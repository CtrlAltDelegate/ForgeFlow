"""Stage 2.2 — Text extraction prompt + Claude tool definition.

Claude Haiku is used with tool_choice="required" to force structured JSON
output via tool calling, rather than free-form text.
"""

SYSTEM = (
    "You are a product analyst extracting structured information from Etsy listing text. "
    "Your job is to infer product characteristics from the title, description, and tags. "
    "Extract only what is evidenced by the text — do not invent features. "
    "For fields you cannot determine from the text, leave them as null."
)

# Tool definition — input_schema mirrors the text_extraction_json column structure
TOOL_DEFINITION: dict = {
    "name": "extract_product_info",
    "description": (
        "Extract structured product information from an Etsy listing's title, "
        "description, and tags. Populate each field based on evidence in the text."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "product_type": {
                "type": "string",
                "description": "One short phrase category label (e.g. 'desktop cable management strip')",
            },
            "primary_use_case": {
                "type": "string",
                "description": "One sentence: what the product does and for whom",
            },
            "primary_geometry": {
                "type": "string",
                "description": "Shape archetype (e.g. 'rectangular bar', 'curved hook', 'flat plate')",
            },
            "dominant_features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3–8 key functional or visual features mentioned in the listing",
            },
            "style_cues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Aesthetic descriptors from the listing text (e.g. 'minimalist', 'matte black')",
            },
            "likely_dimensions_mm": {
                "type": "object",
                "description": "Dimensions if mentioned or inferrable from the text",
                "properties": {
                    "length": {"type": "number"},
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                },
            },
            "material_hints": {
                "type": "string",
                "description": "Material type if mentioned (e.g. 'PLA', 'PETG', 'wood filament')",
            },
            "print_constraints": {
                "type": "string",
                "description": "Any manufacturing or print constraints mentioned in the listing",
            },
            "what_makes_it_sellable": {
                "type": "string",
                "description": "2–3 sentences on the commercial appeal based on listing language",
            },
        },
        "required": [
            "product_type",
            "primary_use_case",
            "primary_geometry",
            "dominant_features",
        ],
    },
}


def build_user_prompt(title: str, description: str, tags: list[str]) -> str:
    tags_str = ", ".join(tags) if tags else "(none)"
    desc_excerpt = (description or "")[:1500]
    return (
        f"Listing Title: {title}\n\n"
        f"Tags: {tags_str}\n\n"
        f"Description:\n{desc_excerpt}"
    )
