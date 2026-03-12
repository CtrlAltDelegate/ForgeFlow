"""Stage 2.1 — Vision analysis prompt.

All listing images are passed to Claude in a single call as base64 content
blocks. The model returns a single JSON object synthesising all images.
"""

SYSTEM = (
    "You are analyzing product listing images for a 3D printing business. "
    "Your job is to describe what you see precisely and technically — focusing on "
    "geometry, dimensions, visible features, and printability. "
    "Be specific and concrete. Avoid vague adjectives. "
    "If you are uncertain about a value, provide your best estimate and note it as estimated."
)


def build_user_prompt() -> str:
    """Returns the text content block appended after all image blocks."""
    return (
        "Analyze the product shown in these listing images. "
        "Return a single JSON object (no markdown, no code fences) with these fields:\n\n"
        "{\n"
        '  "object_description": "one-sentence description of what this product is",\n'
        '  "primary_geometry": "the dominant 3D shape (e.g. rectangular bar, curved hook, flat plate with holes)",\n'
        '  "visible_features": ["list", "of", "3-8 specific visible features that define this product"],\n'
        '  "estimated_dimensions_mm": {"length": 0.0, "width": 0.0, "height": 0.0},\n'
        '  "aesthetic_style": "surface finish and style cues (e.g. matte, smooth, Apple-like, industrial)",\n'
        '  "material_appearance": "what material this looks like (PLA, silicone, wood, metal, etc.)",\n'
        '  "printability_notes": "is this clearly 3D printable? any overhang or support concerns?",\n'
        '  "confidence": 0.0\n'
        "}\n\n"
        "confidence is a float 0.0–1.0 indicating how certain you are of your analysis overall. "
        "For estimated_dimensions_mm: estimate from context clues (hands, desk, USB ports, etc.). "
        "If you cannot estimate a dimension at all, use 0.0 and explain in printability_notes."
    )
