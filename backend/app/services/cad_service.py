"""
CAD generation service: template-based OpenSCAD code and file export.

Supports: bracket, clip, holder, spacer, mount, tray, cable_organizer.
When FORGEFLOW_CAD_LLM_API_KEY is set (Anthropic), can suggest template + parameters
from product/category to match Etsy best-seller style. OpenSCAD CLI for STL export.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.core.config import settings


def check_openscad_available() -> tuple[bool, str]:
    """
    Check if OpenSCAD CLI is available. Returns (available, message).
    """
    path = shutil.which(settings.openscad_path)
    if path:
        return True, ""
    try:
        subprocess.run(
            [settings.openscad_path, "--version"],
            capture_output=True,
            timeout=5,
        )
        return True, ""
    except FileNotFoundError:
        return False, (
            f"OpenSCAD is not installed or not on PATH. "
            f"Set FORGEFLOW_OPENSCAD_PATH to the executable path. "
            f"CAD generation and .scad saving still work; only STL export is affected."
        )
    except Exception:
        return False, "OpenSCAD could not be run. STL export is unavailable."


MODEL_TYPES = [
    "bracket",
    "clip",
    "holder",
    "spacer",
    "mount",
    "tray",
    "cable_organizer",
]


def _ensure_dirs() -> None:
    """Ensure scad and stl directories exist."""
    settings.scad_dir.mkdir(parents=True, exist_ok=True)
    settings.stl_dir.mkdir(parents=True, exist_ok=True)


def _bracket_code(params: dict[str, Any]) -> str:
    w = float(params.get("width", 40))
    h = float(params.get("height", 30))
    t = float(params.get("thickness", 4))
    hole_d = float(params.get("hole_diameter", 4))
    return f"""
// L-bracket
w = {w};
h = {h};
t = {t};
hole_d = {hole_d};

difference() {{
    union() {{
        cube([w, t, h]);
        cube([t, h, t]);
    }}
    translate([t/2, t + h/2, -1]) cylinder(d=hole_d, h=t+2, $fn=24);
    translate([w - t/2, t + h/2, -1]) cylinder(d=hole_d, h=t+2, $fn=24);
}}
"""


def _clip_code(params: dict[str, Any]) -> str:
    w = float(params.get("width", 25))
    h = float(params.get("height", 15))
    t = float(params.get("thickness", 3))
    inner_r = float(params.get("inner_radius", 5))
    return f"""
// Cable clip
w = {w};
h = {h};
t = {t};
r = {inner_r};

difference() {{
    union() {{
        cube([w, t, h]);
        translate([w/2, t + r, 0]) cylinder(r=r+t, h=h, $fn=32);
    }}
    translate([w/2, t + r, -1]) cylinder(r=r, h=h+2, $fn=32);
}}
"""


def _holder_code(params: dict[str, Any]) -> str:
    w = float(params.get("width", 50))
    d = float(params.get("depth", 40))
    h = float(params.get("height", 20))
    wall = float(params.get("wall_thickness", 3))
    return f"""
// Simple holder base
w = {w};
d = {d};
h = {h};
wall = {wall};

difference() {{
    cube([w, d, h]);
    translate([wall, wall, wall]) cube([w-2*wall, d-2*wall, h-wall+0.1]);
}}
"""


def _spacer_code(params: dict[str, Any]) -> str:
    od = float(params.get("outer_diameter", 10))
    id_ = float(params.get("inner_diameter", 5))
    height = float(params.get("height", 5))
    return f"""
// Cylinder spacer
od = {od};
id = {id_};
h = {height};

difference() {{
    cylinder(d=od, h=h, $fn=48);
    translate([0, 0, -0.5]) cylinder(d=id_, h=h+1, $fn=32);
}}
"""


def _mount_code(params: dict[str, Any]) -> str:
    w = float(params.get("width", 60))
    h = float(params.get("height", 40))
    t = float(params.get("thickness", 4))
    hole_d = float(params.get("hole_diameter", 4))
    return f"""
// Wall mount plate
w = {w};
h = {h};
t = {t};
hole_d = {hole_d};

difference() {{
    cube([w, t, h]);
    translate([10, -1, 10]) cylinder(d=hole_d, h=t+2, $fn=24);
    translate([w-10, -1, 10]) cylinder(d=hole_d, h=t+2, $fn=24);
    translate([10, -1, h-10]) cylinder(d=hole_d, h=t+2, $fn=24);
    translate([w-10, -1, h-10]) cylinder(d=hole_d, h=t+2, $fn=24);
}}
"""


def _tray_code(params: dict[str, Any]) -> str:
    w = float(params.get("width", 80))
    d = float(params.get("depth", 60))
    h = float(params.get("height", 25))
    wall = float(params.get("wall_thickness", 3))
    return f"""
// Rectangular tray
w = {w};
d = {d};
h = {h};
wall = {wall};

difference() {{
    cube([w, d, h]);
    translate([wall, wall, wall]) cube([w-2*wall, d-2*wall, h-wall+0.1]);
}}
"""


def _cable_organizer_code(params: dict[str, Any]) -> str:
    length = float(params.get("length", 60))
    width = float(params.get("width", 20))
    height = float(params.get("height", 15))
    channel_r = float(params.get("channel_radius", 4))
    return f"""
// Cable channel
length = {length};
width = {width};
height = {height};
r = {channel_r};

difference() {{
    cube([length, width, height]);
    translate([length/4, width/2, height]) cylinder(r=r, h=2, $fn=24);
    translate([length*3/4, width/2, height]) cylinder(r=r, h=2, $fn=24);
}}
"""


_GENERATORS: dict[str, callable] = {
    "bracket": _bracket_code,
    "clip": _clip_code,
    "holder": _holder_code,
    "spacer": _spacer_code,
    "mount": _mount_code,
    "tray": _tray_code,
    "cable_organizer": _cable_organizer_code,
}

# Parameter keys per template (for LLM prompt)
_TEMPLATE_PARAMS: dict[str, list[str]] = {
    "bracket": ["width", "height", "thickness", "hole_diameter"],
    "clip": ["width", "height", "thickness", "inner_radius"],
    "holder": ["width", "depth", "height", "wall_thickness"],
    "spacer": ["outer_diameter", "inner_diameter", "height"],
    "mount": ["width", "height", "thickness", "hole_diameter"],
    "tray": ["width", "depth", "height", "wall_thickness"],
    "cable_organizer": ["length", "width", "height", "channel_radius"],
}


def suggest_cad_from_product(
    product_name: str,
    category: str,
    notes: str | None = None,
) -> tuple[str, dict[str, Any]] | None:
    """
    Use Claude to suggest a template type and parameters suited to this product/category,
    aiming for designs that match popular/Etsy best-seller style 3D-printed products.
    Returns (model_type, parameters) or None if LLM is not configured or fails.
    """
    if not settings.cad_llm_api_key or settings.cad_llm_provider != "anthropic":
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.cad_llm_api_key)
        templates_desc = "\n".join(
            f"- {t}: params {_TEMPLATE_PARAMS.get(t, [])}"
            for t in MODEL_TYPES
        )
        prompt = f"""You are helping design 3D-printable products that match best sellers on Etsy for a given category.

Available template types and their parameters (all dimensions in mm):
{templates_desc}

Product name: {product_name}
Category: {category}
{f'Research/notes: {notes}' if notes else ''}

Choose the single best template type and concrete parameter values (in mm) so the result looks like a popular, functional product in this category—e.g. desk organizers should have useful compartments/channels, trays should have sensible proportions, clips/holders should fit common items. Avoid a plain box; prefer the template that adds clear value (holes, channels, dividers, etc.).

Respond with only a JSON object, no markdown, with exactly two keys:
- "model_type": one of {json.dumps(MODEL_TYPES)}
- "parameters": an object with the parameter names and numeric values for that template (e.g. "width": 80, "height": 25)

Example for a cable desk organizer: {{"model_type": "cable_organizer", "parameters": {{"length": 120, "width": 35, "height": 25, "channel_radius": 6}}}}
Example for a desk tray: {{"model_type": "tray", "parameters": {{"width": 200, "depth": 100, "height": 40, "wall_thickness": 3}}}}"""

        msg = client.messages.create(
            model=settings.cad_llm_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (msg.content[0].text if msg.content else "").strip() if isinstance(msg.content, list) else ""
        if not text:
            return None
        # Strip markdown code block if present
        if "```" in text:
            text = re.sub(r"^```(?:json)?\s*", "", text).strip()
            text = re.sub(r"\s*```$", "", text).strip()
        data = json.loads(text)
        model_type = str(data.get("model_type", "")).strip().lower()
        params = data.get("parameters")
        if model_type not in _GENERATORS or not isinstance(params, dict):
            return None
        # Ensure all parameter values are numbers
        parameters = {k: float(v) for k, v in params.items() if isinstance(v, (int, float))}
        return (model_type, parameters)
    except Exception:
        return None


def generate_scad_code(model_type: str, parameters: dict[str, Any]) -> str:
    """
    Generate OpenSCAD source code for the given model type and parameters.
    Raises ValueError if model_type is unknown.
    """
    if model_type not in _GENERATORS:
        raise ValueError(f"Unknown model type: {model_type}. Choose from: {MODEL_TYPES}")
    return _GENERATORS[model_type](parameters or {}).strip()


def save_scad_file(product_id: int, version: int, code: str, slug: str) -> Path:
    """Write SCAD code to disk. Returns path to saved file."""
    _ensure_dirs()
    safe_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in slug)[:50]
    name = f"product_{product_id}_{safe_slug}_v{version}.scad"
    path = settings.scad_dir / name
    path.write_text(code, encoding="utf-8")
    return path


def export_stl(scad_path: Path, stl_path: Path) -> tuple[bool, str]:
    """
    Run OpenSCAD CLI to export STL. Returns (success, message).
    """
    _ensure_dirs()
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [
                settings.openscad_path,
                "-o", str(stl_path),
                str(scad_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return False, result.stderr or result.stdout or f"Exit code {result.returncode}"
        return True, "OK"
    except FileNotFoundError:
        return False, (
            "STL export is not available on this server (OpenSCAD not installed). "
            "You can still generate and save .scad files and export to STL locally."
        )
    except subprocess.TimeoutExpired:
        return False, "OpenSCAD timed out."
    except Exception as e:
        return False, str(e)
