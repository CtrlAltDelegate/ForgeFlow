"""Stage 2.3 — Brief assembly prompt.

Claude Sonnet assembles visual_summary + text_extraction into a complete
draft product brief conforming to the ProductBrief schema.

The USB cable organizer (rank 1) is used as a few-shot example because it is
the highest-quality brief in the seed set and calibrates output quality.
"""
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Load few-shot example once at import time
# ---------------------------------------------------------------------------
_SEEDS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "seeds" / "product_briefs.json"
)

_USB_EXAMPLE: str = ""
try:
    _data = json.loads(_SEEDS_PATH.read_text(encoding="utf-8"))
    _usb = next(p for p in _data["products"] if p["product_id"] == "usb_cable_desk_organizer")
    # Flatten into the canonical brief format expected by ProductBrief schema
    _flat = {
        "product_id": _usb["product_id"],
        "product_name": _usb["product_name"],
        "material": _usb["material"],
        "estimated_print_time_hrs": _usb["estimated_print_time_hrs"],
        "estimated_filament_g": _usb["estimated_filament_g"],
        "phase": _usb.get("phase"),
        "forgescore_demand": _usb.get("forgescore_demand"),
        "price_range_usd": _usb.get("price_range_usd"),
        "sku_expansion_strategy": _usb.get("sku_expansion_strategy"),
        "openscad_prompt": _usb["openscad_prompt"],
        "parametric_variables": [
            {
                "name": pv["name"],
                "controls": pv.get("drives", ""),
                "min": pv.get("range", [0, 1])[0],
                "max": pv.get("range", [0, 1])[-1],
            }
            for pv in _usb.get("parametric_variables", [])
        ],
        **_usb["design_brief"],
    }
    _USB_EXAMPLE = json.dumps(_flat, indent=2)
except Exception:
    _USB_EXAMPLE = "{}"  # graceful fallback if seeds file missing


# ---------------------------------------------------------------------------
# Brief schema template (placeholder values for Claude to fill)
# ---------------------------------------------------------------------------
_BRIEF_TEMPLATE = """{
  "product_id": "snake_case_slug",
  "product_name": "Human-readable name",
  "schema_version": "1.0",
  "product_type": "short category label",
  "primary_use_case": "one sentence describing what it does",
  "primary_geometry": "shape archetype (e.g. rectangular bar, curved hook)",
  "dominant_features": ["feature 1", "feature 2", "feature 3"],
  "approximate_dimensions_mm": {"length": 0, "width": 0, "height": 0},
  "edge_treatment": "fillet radius and locations",
  "aesthetic": "style goal + reference brand",
  "print_orientation": "how it sits on the print bed",
  "support_required": false,
  "avoid": ["anti-pattern 1", "anti-pattern 2", "anti-pattern 3"],
  "resemblance_goal": "commercial reference point",
  "parametric_variables": [
    {"name": "variable_name", "controls": "what it drives", "min": 0, "max": 10, "default": 5}
  ],
  "openscad_prompt": "Full OpenSCAD generation prompt (≥150 chars)",
  "material": "PLA",
  "estimated_print_time_hrs": 1.0,
  "estimated_filament_g": 30.0,
  "sku_expansion_strategy": null,
  "commercial_differentiators": null
}"""

SYSTEM = f"""You are a product design expert generating structured product briefs for a 3D printing business.
Your briefs are the direct input to an OpenSCAD CAD generation pipeline.
Brief quality directly determines whether the generated CAD file looks like a commercial product or a generic box.

Here is an example of a high-quality brief for reference:
{_USB_EXAMPLE}

Rules for generating a good brief:
1. Fill every required field. If evidence is insufficient, make a reasonable inference and note it.
2. dominant_features must have AT LEAST 3 items; avoid must have AT LEAST 3 items.
3. approximate_dimensions_mm must have length, width, and height — estimate if not given.
4. Write openscad_prompt LAST, after all other fields are set, so it can reference accurate values.
5. The openscad_prompt must follow this structure:
   - Opening: "Create a 3D-printable [product_type] in OpenSCAD."
   - Geometry block: dimensions and primary shape
   - Feature enumeration: each feature with measurements where possible
   - Treatment block: edge_treatment, surface finish, print_orientation
   - Parametric block: variable name, what it drives, range
   - Avoid block: list all avoid items
   - Resemblance goal and material
   The prompt must be AT LEAST 150 characters.
6. Cross-check openscad_prompt against avoid list — none of the avoided anti-patterns should appear in the prompt.
7. product_id should be a snake_case slug derived from the product name.
8. material must be one of: PLA, PETG, TPU, ABS.
9. Return ONLY valid JSON matching the schema below. No markdown, no code fences, no commentary.

Schema to fill:
{_BRIEF_TEMPLATE}"""


def build_user_prompt(
    visual_summary: dict,
    text_extraction: dict,
    raw_title: str | None,
    raw_description: str | None,
    reviewer_notes: str | None = None,
) -> str:
    parts = []

    if raw_title:
        parts.append(f"Product title: {raw_title}")
    if raw_description:
        parts.append(f"Listing description (excerpt):\n{raw_description[:800]}")

    parts.append(
        f"Vision analysis (from product images):\n{json.dumps(visual_summary, indent=2)}"
    )
    parts.append(
        f"Text extraction (from listing text):\n{json.dumps(text_extraction, indent=2)}"
    )

    if reviewer_notes:
        parts.append(
            f"Reviewer correction notes (from a previous enrichment attempt — address these):\n{reviewer_notes}"
        )

    parts.append(
        "Using the evidence above, generate the complete product brief JSON. "
        "Synthesise visual and text evidence — do not choose one over the other. "
        "Where you must infer a value, provide your best estimate."
    )

    return "\n\n".join(parts)
