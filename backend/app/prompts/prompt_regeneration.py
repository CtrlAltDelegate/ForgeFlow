"""Prompt for regenerating only the openscad_prompt field.

Used by POST /api/intake/{id}/regenerate-prompt when a reviewer has edited
geometry fields and wants a fresh prompt without re-running full enrichment.
"""
import json

SYSTEM = (
    "You are generating an OpenSCAD generation prompt for a 3D-printable product. "
    "The prompt will be passed directly to Claude for OpenSCAD code generation. "
    "It must be precise, technical, and structured — not a vague description. "
    "A good prompt produces a commercially correct CAD file; a vague prompt produces a generic box."
)

_PROMPT_STRUCTURE = """A good openscad_prompt has this structure:
1. Opening: "Create a 3D-printable [product_type] in OpenSCAD."
2. Geometry block: primary shape and key dimensions in mm
3. Feature enumeration: each dominant feature with measurements where possible
4. Treatment: edge_treatment, surface finish, print_orientation
5. Parametric: variable name, what it drives, range (min–max)
6. Avoid: each item in the avoid list
7. Resemblance goal
8. Closing: material, support requirements

The prompt must be at least 150 characters. Return only the prompt string — no JSON, no explanation."""


def build_user_prompt(brief_fields: dict) -> str:
    return (
        f"Generate an openscad_prompt for this product brief:\n\n"
        f"{json.dumps(brief_fields, indent=2)}\n\n"
        f"{_PROMPT_STRUCTURE}"
    )
