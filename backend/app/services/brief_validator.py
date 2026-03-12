"""Gate condition checks and confidence scoring for product briefs.

Gate conditions (Section 3.3.3): block approval if any fail.
Confidence scoring (Section 3.2.4): weighted 0.0–1.0 score per brief field.
"""
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    passes: bool
    failed_conditions: list[str] = field(default_factory=list)


@dataclass
class ConfidenceResult:
    overall: float
    per_field: dict[str, float] = field(default_factory=dict)
    low_confidence_fields: list[str] = field(default_factory=list)

    @property
    def warning_level(self) -> str:
        """Return 'red', 'yellow', or 'green' per spec thresholds."""
        if self.overall < 0.35:
            return "red"
        if self.overall < 0.55:
            return "yellow"
        return "green"


# ---------------------------------------------------------------------------
# Gate conditions (spec Section 3.3.3)
# ---------------------------------------------------------------------------

# Each entry: (field_name, predicate, failure_message)
_GATE_CONDITIONS: list[tuple[str, object, str]] = [
    (
        "primary_geometry",
        lambda b: bool((b.get("primary_geometry") or "").strip()),
        "primary_geometry must be set",
    ),
    (
        "dominant_features",
        lambda b: len(b.get("dominant_features") or []) >= 3,
        "dominant_features needs ≥3 items",
    ),
    (
        "approximate_dimensions_mm",
        lambda b: all(
            b.get("approximate_dimensions_mm", {}).get(k)
            for k in ("length", "width", "height")
        ),
        "approximate_dimensions_mm must have length, width, and height",
    ),
    (
        "avoid",
        lambda b: len(b.get("avoid") or []) >= 3,
        "avoid list needs ≥3 items",
    ),
    (
        "openscad_prompt",
        lambda b: len(b.get("openscad_prompt") or "") >= 150,
        "openscad_prompt must be ≥150 characters",
    ),
    (
        "parametric_variables",
        lambda b: len(b.get("parametric_variables") or []) >= 1,
        "needs ≥1 parametric_variable defined",
    ),
    (
        "material",
        lambda b: (b.get("material") or "").upper() in {"PLA", "PETG", "TPU", "ABS"},
        "material must be one of: PLA, PETG, TPU, ABS",
    ),
]


def check_gate_conditions(brief: dict) -> GateResult:
    """Check all Stage 3 gate conditions. Returns GateResult."""
    failures = []
    for _field_name, predicate, message in _GATE_CONDITIONS:
        try:
            if not predicate(brief):
                failures.append(message)
        except Exception:
            failures.append(message)
    return GateResult(passes=len(failures) == 0, failed_conditions=failures)


# ---------------------------------------------------------------------------
# Confidence scoring (spec Section 3.2.4)
# ---------------------------------------------------------------------------

# Weight map: field -> weight (must sum to 1.0)
_FIELD_WEIGHTS: dict[str, float] = {
    "primary_geometry": 0.25,
    "dominant_features": 0.20,
    "approximate_dimensions_mm": 0.20,
    "aesthetic": 0.15,
    "avoid": 0.10,
    "openscad_prompt": 0.10,
}


def _field_score(brief: dict, field_name: str) -> float:
    """Return 0.0 (missing), 0.5 (inferred/thin), or 1.0 (well-evidenced)."""
    value = brief.get(field_name)

    if field_name == "primary_geometry":
        if not value:
            return 0.0
        return 1.0 if len(str(value)) > 10 else 0.5

    if field_name == "dominant_features":
        if not value or len(value) == 0:
            return 0.0
        if len(value) >= 3:
            return 1.0
        return 0.5

    if field_name == "approximate_dimensions_mm":
        if not isinstance(value, dict):
            return 0.0
        present = [value.get(k) for k in ("length", "width", "height") if value.get(k)]
        if len(present) == 3:
            # Check if all three are non-zero (0.0 means unestimated)
            if all(float(v) > 0 for v in present):
                return 1.0
            return 0.5
        if len(present) > 0:
            return 0.5
        return 0.0

    if field_name == "aesthetic":
        if not value:
            return 0.0
        return 1.0 if len(str(value)) > 15 else 0.5

    if field_name == "avoid":
        if not value or len(value) == 0:
            return 0.0
        if len(value) >= 3:
            return 1.0
        return 0.5

    if field_name == "openscad_prompt":
        if not value:
            return 0.0
        length = len(str(value))
        if length >= 300:
            return 1.0
        if length >= 150:
            return 0.5
        return 0.0

    return 0.0


def compute_confidence(brief: dict) -> ConfidenceResult:
    """Compute per-field and weighted overall confidence score.

    Weights per spec Section 3.2.4:
      primary_geometry: 0.25, dominant_features: 0.20,
      approximate_dimensions_mm: 0.20, aesthetic: 0.15,
      avoid: 0.10, openscad_prompt: 0.10
    """
    per_field: dict[str, float] = {}
    overall = 0.0

    for field_name, weight in _FIELD_WEIGHTS.items():
        score = _field_score(brief, field_name)
        per_field[field_name] = score
        overall += score * weight

    low_confidence = [f for f, s in per_field.items() if s < 0.6]

    return ConfidenceResult(
        overall=round(overall, 3),
        per_field=per_field,
        low_confidence_fields=low_confidence,
    )
