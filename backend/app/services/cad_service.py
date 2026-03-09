"""
CAD generation service: template-based OpenSCAD code and file export.

Supports: bracket, clip, holder, spacer, mount, tray, cable_organizer.
OpenSCAD CLI is used for STL export when available.
"""

import json
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
