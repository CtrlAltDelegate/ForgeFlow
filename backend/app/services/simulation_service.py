"""
Manufacturing simulation: heuristic engine.

Estimates print time, material usage, cost, supports, orientation, difficulty
from part dimensions (from CAD parameters or default volume). Designed so that
Layer 2 (slicer CLI) can replace the heuristic without changing callers.
"""

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import settings


# Material density g/cm³ (for volume -> grams)
DENSITY_PLA = 1.24
DENSITY_ABS = 1.04
DENSITY_PETG = 1.27
DENSITY_TPU = 1.21
DENSITY = {"PLA": DENSITY_PLA, "ABS": DENSITY_ABS, "PETG": DENSITY_PETG, "TPU": DENSITY_TPU}

# Heuristic: minutes per cm³ by material (rough)
MIN_PER_CM3 = {"PLA": 1.8, "ABS": 2.0, "PETG": 1.9, "TPU": 2.2}


@dataclass
class SimulationInputs:
    material_type: str = "PLA"
    layer_height: float = 0.2
    infill: float = 20.0
    nozzle_size: float = 0.4
    # Optional: from CAD model parameters for volume estimate
    cad_model_type: str | None = None
    cad_parameters_json: str | None = None


@dataclass
class SimulationResult:
    estimated_print_time_minutes: float
    estimated_material_grams: float
    estimated_filament_cost: float
    supports_required: bool
    recommended_orientation: str
    difficulty_score: float
    notes: str
    warnings: list[str]


def _estimate_volume_cm3(model_type: str | None, parameters_json: str | None) -> float:
    """Rough volume in cm³ from CAD type + params, or default."""
    if not parameters_json or not model_type:
        return 50.0  # default medium part
    try:
        p = json.loads(parameters_json)
    except (json.JSONDecodeError, TypeError):
        return 50.0
    # Approximate volume from template dimensions (mm -> cm)
    w = (p.get("width") or 40) / 10.0
    h = (p.get("height") or 30) / 10.0
    d = (p.get("depth") or (p.get("length") or 20)) / 10.0
    t = (p.get("thickness") or (p.get("wall_thickness") or 3)) / 10.0
    if model_type == "bracket":
        return w * t * h * 0.5 + t * (h / 10) * (t / 10)  # L-shape approx
    if model_type == "spacer":
        od = (p.get("outer_diameter") or 10) / 10.0
        id_ = (p.get("inner_diameter") or 5) / 10.0
        height = (p.get("height") or 5) / 10.0
        return 3.14159 * (od**2 - id_**2) / 4 * height
    if model_type in ("holder", "tray"):
        return w * d * h - (w - 2 * t) * (d - 2 * t) * (h - t)  # hollow box
    if model_type == "clip":
        return w * (h / 10) * (t / 10) * 1.5
    if model_type == "mount":
        return w * (t / 10) * h
    if model_type == "cable_organizer":
        length = (p.get("length") or 60) / 10.0
        width = (p.get("width") or 20) / 10.0
        height = (p.get("height") or 15) / 10.0
        return length * width * height * 0.6
    return w * h * d * 0.3  # generic


def _needs_support(model_type: str | None) -> bool:
    """Heuristic: does this part type typically need supports?"""
    if not model_type:
        return False
    # Clips and brackets often have overhangs; trays/mounts often don't
    return model_type in ("clip", "bracket", "cable_organizer")


def _orientation(model_type: str | None) -> str:
    if not model_type:
        return "Largest flat face down"
    if model_type in ("tray", "holder", "mount"):
        return "Open side up, base on bed"
    if model_type == "spacer":
        return "Cylinder axis vertical"
    return "Largest flat face down"


def run_simulation(inputs: SimulationInputs) -> SimulationResult:
    """
    Run heuristic manufacturing simulation. Returns estimates and warnings.
    """
    vol = _estimate_volume_cm3(inputs.cad_model_type, inputs.cad_parameters_json)
    material = inputs.material_type.upper() if inputs.material_type else "PLA"
    density = DENSITY.get(material, DENSITY_PLA)
    rate = MIN_PER_CM3.get(material, MIN_PER_CM3["PLA"])

    # Layer height factor: finer = longer
    lh_factor = 0.2 / max(0.1, inputs.layer_height)
    infill_factor = 0.5 + (inputs.infill / 100.0) * 0.5  # 20% -> 0.6, 100% -> 1.0

    print_time = vol * rate * lh_factor * infill_factor
    if _needs_support(inputs.cad_model_type):
        print_time *= 1.35
        supports = True
    else:
        supports = False

    # Grams: volume * density * (shell + infill contribution)
    material_grams = vol * density * (0.3 + 0.7 * (inputs.infill / 100.0))
    cost = material_grams * settings.default_material_cost_per_gram

    # Difficulty 0-100: higher time and support = harder
    difficulty = min(100.0, 20.0 + (print_time / 60.0) * 15.0 + (30.0 if supports else 0.0))

    notes = (
        f"Heuristic simulation. Volume approx {vol:.1f} cm³. "
        f"Material={material}, layer={inputs.layer_height}mm, infill={inputs.infill}%. "
        "Replace with slicer CLI for production estimates."
    )

    warnings = []
    if print_time > 240:
        warnings.append("Long print time (>4 h) – consider batch size and machine availability.")
    if supports:
        warnings.append("Supports likely required – may increase time and post-processing.")
    if vol > 500:
        warnings.append("Large part – verify build volume (e.g. 200×200×200 mm).")
    if cost > 5.0:
        warnings.append("Higher material cost – review margin vs. selling price.")

    return SimulationResult(
        estimated_print_time_minutes=round(print_time, 1),
        estimated_material_grams=round(material_grams, 1),
        estimated_filament_cost=round(cost, 2),
        supports_required=supports,
        recommended_orientation=_orientation(inputs.cad_model_type),
        difficulty_score=round(difficulty, 1),
        notes=notes,
        warnings=warnings,
    )
