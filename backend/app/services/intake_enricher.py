"""Stage 2 — AI enrichment orchestrator.

Runs three sequential AI passes on a ProductIntake record:
  2.1  Vision analysis  — Claude Sonnet with base64 image content blocks
  2.2  Text extraction  — Claude Haiku with tool calling (structured JSON)
  2.3  Brief assembly   — Claude Sonnet synthesises both passes into a full brief

Then scores confidence and updates the ProductIntake record.

This function is async and creates its own DB session so it can safely run
as a FastAPI BackgroundTask after the originating request session closes.
"""
import base64
import json
import logging
from pathlib import Path

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.intake import IntakeImage, IntakeStatus, ProductIntake
from app.prompts.text_extraction import SYSTEM as TEXT_SYSTEM, TOOL_DEFINITION, build_user_prompt as text_prompt
from app.prompts.vision_analysis import SYSTEM as VISION_SYSTEM, build_user_prompt as vision_prompt
from app.services.brief_assembler import assemble_brief
from app.services.brief_validator import compute_confidence

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def run_enrichment(intake_id: str, reviewer_notes: str | None = None) -> None:
    """Full Stage 2 enrichment pipeline.

    Creates its own AsyncSession — safe to call as a BackgroundTask.
    Status transitions:
      raw_collected → enriching → brief_drafted  (success)
      raw_collected → enriching → raw_collected   (failure — allows retry)
    """
    async with AsyncSessionLocal() as db:
        intake = await db.get(ProductIntake, intake_id)
        if intake is None:
            logger.error("run_enrichment: intake %s not found", intake_id)
            return

        # Mark as enriching
        intake.status = IntakeStatus.ENRICHING
        intake.enrichment_attempt_count = (intake.enrichment_attempt_count or 0) + 1
        await db.commit()
        await db.refresh(intake)

        try:
            await _do_enrichment(intake, db, reviewer_notes)
        except Exception as exc:
            logger.exception("run_enrichment: enrichment failed for %s: %s", intake_id, exc)
            # Reset to raw_collected so the user can retry
            intake.status = IntakeStatus.RAW_COLLECTED
            await db.commit()
            raise


# ---------------------------------------------------------------------------
# Internal enrichment logic
# ---------------------------------------------------------------------------


async def _do_enrichment(
    intake: ProductIntake,
    db: AsyncSession,
    reviewer_notes: str | None,
) -> None:
    """Runs all three AI passes and updates the intake record."""

    # --- Stage 2.1: Vision analysis ----------------------------------------
    image_records = await _load_images(intake.id, db)
    visual_summary: dict = {}

    if image_records and settings.cad_llm_api_key:
        visual_summary = _run_vision_pass(image_records) or {}
    else:
        logger.info("enricher: skipping vision pass (no images or no API key)")

    intake.visual_summary_json = visual_summary
    await db.commit()

    # --- Stage 2.2: Text extraction ----------------------------------------
    text_extraction: dict = {}

    if (intake.raw_title or intake.raw_description) and settings.cad_llm_api_key:
        text_extraction = _run_text_extraction(
            title=intake.raw_title or "",
            description=intake.raw_description or "",
            tags=intake.raw_tags or [],
        ) or {}
    else:
        logger.info("enricher: skipping text extraction (no text content or no API key)")

    intake.text_extraction_json = text_extraction
    await db.commit()

    # --- Stage 2.3: Brief assembly -----------------------------------------
    draft_brief = assemble_brief(
        visual_summary=visual_summary,
        text_extraction=text_extraction,
        raw_title=intake.raw_title,
        raw_description=intake.raw_description,
        reviewer_notes=reviewer_notes,
    )

    if draft_brief is None:
        raise RuntimeError("Brief assembly returned None — check API key and logs")

    intake.draft_brief_json = draft_brief

    # --- Confidence scoring ------------------------------------------------
    conf = compute_confidence(draft_brief)
    intake.confidence_score = conf.overall
    intake.confidence_detail_json = {
        "per_field": conf.per_field,
        "low_confidence_fields": conf.low_confidence_fields,
        "warning_level": conf.warning_level,
    }

    intake.status = IntakeStatus.BRIEF_DRAFTED
    if reviewer_notes:
        intake.reviewer_notes = reviewer_notes

    await db.commit()
    logger.info(
        "enricher: intake %s → brief_drafted (confidence %.2f, level=%s)",
        intake.id,
        conf.overall,
        conf.warning_level,
    )


# ---------------------------------------------------------------------------
# Stage 2.1 — Vision pass
# ---------------------------------------------------------------------------


def _run_vision_pass(image_records: list[IntakeImage]) -> dict | None:
    """Call Claude Sonnet with all images as base64 content blocks.

    Returns parsed visual_summary dict, or None on failure.
    """
    content_blocks = _build_image_content_blocks(image_records)
    if not content_blocks:
        return None

    # Append the text prompt after all image blocks
    content_blocks.append({"type": "text", "text": vision_prompt()})

    try:
        client = anthropic.Anthropic(api_key=settings.cad_llm_api_key)
        msg = client.messages.create(
            model=settings.intake_vision_model,
            max_tokens=2048,
            system=VISION_SYSTEM,
            messages=[{"role": "user", "content": content_blocks}],
        )
        text = (msg.content[0].text if msg.content else "").strip()

        # Strip markdown code fences
        if text.startswith("```"):
            text = "\n".join(
                line for line in text.splitlines() if not line.startswith("```")
            ).strip()

        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("vision_pass: invalid JSON from Claude: %s", exc)
        return None
    except anthropic.APIError as exc:
        logger.warning("vision_pass: API error: %s", exc)
        return None
    except Exception as exc:
        logger.warning("vision_pass: unexpected error: %s", exc)
        return None


def _build_image_content_blocks(images: list[IntakeImage]) -> list[dict]:
    """Base64-encode each image file and return Anthropic content blocks.

    Skips images whose local_path doesn't exist on disk.
    """
    blocks = []
    for img in images:
        path = Path(img.local_path)
        if not path.exists():
            logger.debug("image %s not found on disk, skipping", img.local_path)
            continue
        try:
            data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
            # Infer media type from extension
            ext = path.suffix.lower()
            media_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            media_type = media_type_map.get(ext, "image/jpeg")
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data,
                    },
                }
            )
        except OSError as exc:
            logger.warning("could not read image %s: %s", img.local_path, exc)

    return blocks


# ---------------------------------------------------------------------------
# Stage 2.2 — Text extraction pass
# ---------------------------------------------------------------------------


def _run_text_extraction(title: str, description: str, tags: list) -> dict | None:
    """Call Claude Haiku with tool calling to extract structured product info.

    tool_choice="required" forces Claude to call the tool rather than
    returning free text, ensuring schema compliance.
    Returns the tool input dict, or None on failure.
    """
    try:
        client = anthropic.Anthropic(api_key=settings.cad_llm_api_key)
        msg = client.messages.create(
            model=settings.intake_text_model,  # Haiku — fast + cheap
            max_tokens=1024,
            system=TEXT_SYSTEM,
            tools=[TOOL_DEFINITION],
            tool_choice={"type": "required"},  # must call the tool
            messages=[
                {
                    "role": "user",
                    "content": text_prompt(
                        title=title,
                        description=description,
                        tags=list(tags) if tags else [],
                    ),
                }
            ],
        )

        # Extract tool use block
        for block in msg.content:
            if hasattr(block, "type") and block.type == "tool_use":
                return dict(block.input)

        logger.warning("text_extraction: no tool_use block in response")
        return None

    except anthropic.APIError as exc:
        logger.warning("text_extraction: API error: %s", exc)
        return None
    except Exception as exc:
        logger.warning("text_extraction: unexpected error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _load_images(intake_id: str, db: AsyncSession) -> list[IntakeImage]:
    """Load IntakeImage records for an intake, ordered by image_index."""
    result = await db.execute(
        select(IntakeImage)
        .where(IntakeImage.intake_id == intake_id)
        .order_by(IntakeImage.image_index)
    )
    return list(result.scalars().all())
