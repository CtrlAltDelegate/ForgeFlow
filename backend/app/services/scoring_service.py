"""
ForgeFlow Opportunity Score engine.

Computes 0-100 scores from research data (and optional manufacturing data).
Weights: demand 30%, competition 20%, manufacturing 20%, margin 20%, differentiation 10%.
"""

from dataclasses import dataclass

from app.core.config import settings


# Weights (tunable)
WEIGHT_DEMAND = 0.30
WEIGHT_COMPETITION = 0.20
WEIGHT_MANUFACTURING = 0.20
WEIGHT_MARGIN = 0.20
WEIGHT_DIFFERENTIATION = 0.10


@dataclass
class ScoreInputs:
    """Inputs used to compute opportunity score."""
    listed_price: float | None = None
    review_count: int | None = None
    rating: float | None = None
    estimated_sales: int | None = None
    competitor_count: int | None = None
    listing_count: int | None = None
    listing_age_days: int | None = None
    # Optional: from manufacturing_simulation when available
    estimated_print_time_minutes: float | None = None
    estimated_material_grams: float | None = None
    supports_required: bool = False


@dataclass
class ScoreResult:
    """Computed scores (0-100 each) and total."""
    demand_score: float
    competition_score: float
    manufacturing_score: float
    margin_score: float
    differentiation_score: float
    total_score: float
    scoring_notes: str


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _demand_score(inp: ScoreInputs) -> float:
    """Demand: higher estimated_sales, review_count, rating => higher score."""
    score = 50.0  # baseline
    if inp.estimated_sales is not None:
        # Rough scale: 100+ sales => +20, 500+ => +30, 1000+ => +40
        if inp.estimated_sales >= 1000:
            score += 40
        elif inp.estimated_sales >= 500:
            score += 30
        elif inp.estimated_sales >= 200:
            score += 20
        elif inp.estimated_sales >= 50:
            score += 10
    if inp.review_count is not None:
        if inp.review_count >= 1000:
            score += 15
        elif inp.review_count >= 200:
            score += 10
        elif inp.review_count >= 50:
            score += 5
    if inp.rating is not None and inp.rating >= 4.0:
        score += 10
    return _clamp(score)


def _competition_score(inp: ScoreInputs) -> float:
    """Competition: fewer competitors => higher score (less saturated)."""
    score = 50.0
    comp = inp.competitor_count if inp.competitor_count is not None else 30
    listing = inp.listing_count if inp.listing_count is not None else 50
    # Lower competition = higher score
    if comp <= 10 and listing <= 25:
        score = 85
    elif comp <= 25 and listing <= 60:
        score = 70
    elif comp <= 50 and listing <= 120:
        score = 55
    elif comp <= 100:
        score = 40
    else:
        score = 25
    return _clamp(score)


def _manufacturing_score(inp: ScoreInputs) -> float:
    """Manufacturing: simple/fast prints => higher score. Uses heuristics until we have slicer data."""
    score = 60.0  # default when no data
    if inp.estimated_print_time_minutes is not None:
        if inp.estimated_print_time_minutes <= 60:
            score = 90
        elif inp.estimated_print_time_minutes <= 180:
            score = 75
        elif inp.estimated_print_time_minutes <= 360:
            score = 55
        else:
            score = 35
    if inp.supports_required:
        score -= 15
    return _clamp(score)


def _margin_score(inp: ScoreInputs) -> float:
    """Margin: higher (price - fees - material - shipping) => higher score."""
    score = 50.0
    price = inp.listed_price
    if price is not None and price > 0:
        fee = price * (settings.default_platform_fee_percent / 100)
        material = (inp.estimated_material_grams or 50) * settings.default_material_cost_per_gram
        shipping = settings.default_shipping_estimate
        margin = price - fee - material - shipping
        if margin >= 8:
            score = 85
        elif margin >= 5:
            score = 72
        elif margin >= 2:
            score = 55
        elif margin >= 0:
            score = 40
        else:
            score = 20
    return _clamp(score)


def _differentiation_score(inp: ScoreInputs) -> float:
    """Differentiation: hard to infer from research alone; use rating/competition as proxy."""
    # Higher rating + moderate competition => room to differentiate
    score = 50.0
    rating = inp.rating or 4.0
    comp = inp.competitor_count or 40
    if rating < 4.0 and comp > 30:
        score = 65  # poor incumbents, room to improve
    elif rating >= 4.3 and comp <= 25:
        score = 55  # good niche
    elif comp <= 15:
        score = 60
    return _clamp(score)


def compute_opportunity_score(inputs: ScoreInputs) -> ScoreResult:
    """
    Compute ForgeFlow Opportunity Score from research (and optional manufacturing) inputs.
    Returns all component scores and weighted total.
    """
    demand = _demand_score(inputs)
    competition = _competition_score(inputs)
    manufacturing = _manufacturing_score(inputs)
    margin = _margin_score(inputs)
    differentiation = _differentiation_score(inputs)

    total = (
        demand * WEIGHT_DEMAND
        + competition * WEIGHT_COMPETITION
        + manufacturing * WEIGHT_MANUFACTURING
        + margin * WEIGHT_MARGIN
        + differentiation * WEIGHT_DIFFERENTIATION
    )
    total = round(total, 1)

    notes = (
        f"Weights: demand={WEIGHT_DEMAND}, competition={WEIGHT_COMPETITION}, "
        f"manufacturing={WEIGHT_MANUFACTURING}, margin={WEIGHT_MARGIN}, differentiation={WEIGHT_DIFFERENTIATION}"
    )

    return ScoreResult(
        demand_score=round(demand, 1),
        competition_score=round(competition, 1),
        manufacturing_score=round(manufacturing, 1),
        margin_score=round(margin, 1),
        differentiation_score=round(differentiation, 1),
        total_score=total,
        scoring_notes=notes,
    )
