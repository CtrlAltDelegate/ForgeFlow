"""Stage 2.3 — Brief assembly service.

Calls Claude Sonnet to synthesise visual_summary + text_extraction into a
complete draft product brief conforming to the ProductBrief schema.
Uses the same Anthropic client pattern as cad_service.py.
"""
import json
import logging

import anthropic

from app.core.config import settings
from app.prompts.brief_assembly import SYSTEM, build_user_prompt

logger = logging.getLogger(__name__)


def assemble_brief(
    visual_summary: dict,
    text_extraction: dict,
    raw_title: str | None = None,
    raw_description: str | None = None,
    reviewer_notes: str | None = None,
) -> dict | None:
    """Call Claude Sonnet to assemble a complete draft product brief.

    Args:
        visual_summary: Output from Stage 2.1 vision analysis.
        text_extraction: Output from Stage 2.2 text extraction.
        raw_title: Original listing title (optional context).
        raw_description: Listing description excerpt (optional context).
        reviewer_notes: Correction guidance from a previous failed enrichment.

    Returns:
        Parsed brief dict on success, None on failure.
    """
    if not settings.cad_llm_api_key:
        logger.warning("cad_llm_api_key not set — brief assembly skipped")
        return None

    user_prompt = build_user_prompt(
        visual_summary=visual_summary,
        text_extraction=text_extraction,
        raw_title=raw_title,
        raw_description=raw_description,
        reviewer_notes=reviewer_notes,
    )

    try:
        client = anthropic.Anthropic(api_key=settings.cad_llm_api_key)
        msg = client.messages.create(
            model=settings.intake_vision_model,  # Sonnet for assembly quality
            max_tokens=4096,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = (msg.content[0].text if msg.content else "").strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()

        return json.loads(text)

    except json.JSONDecodeError as exc:
        logger.warning("brief_assembler: Claude returned invalid JSON: %s", exc)
        return None
    except anthropic.APIError as exc:
        logger.warning("brief_assembler: Anthropic API error: %s", exc)
        return None
    except Exception as exc:
        logger.warning("brief_assembler: unexpected error: %s", exc)
        return None


def regenerate_openscad_prompt(brief_fields: dict) -> str | None:
    """Regenerate just the openscad_prompt field from current brief state.

    Used by POST /api/intake/{id}/regenerate-prompt.
    Returns the new prompt string, or None on failure.
    """
    from app.prompts.prompt_regeneration import SYSTEM as REGEN_SYSTEM, build_user_prompt as regen_prompt

    if not settings.cad_llm_api_key:
        return None

    try:
        client = anthropic.Anthropic(api_key=settings.cad_llm_api_key)
        msg = client.messages.create(
            model=settings.intake_vision_model,
            max_tokens=1024,
            system=REGEN_SYSTEM,
            messages=[{"role": "user", "content": regen_prompt(brief_fields)}],
        )
        return (msg.content[0].text if msg.content else "").strip() or None
    except Exception as exc:
        logger.warning("regenerate_openscad_prompt: error: %s", exc)
        return None
