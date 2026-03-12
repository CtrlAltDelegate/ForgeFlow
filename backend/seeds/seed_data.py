"""Seed real ForgeFlow top-10 product data, including design briefs for CAD generation."""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models import Product, ResearchData, OpportunityScore
from app.models.product import ProductStatus, slugify
from app.models.cad_model import CadModel

# ---------------------------------------------------------------------------
# Load design briefs from product_briefs.json (same directory as this script)
# ---------------------------------------------------------------------------
BRIEFS_PATH = Path(__file__).resolve().parent / "product_briefs.json"
with open(BRIEFS_PATH, "r") as f:
    _briefs_data = json.load(f)

# Build a lookup dict keyed by product_id for fast access
DESIGN_BRIEFS: dict[str, dict] = {
    p["product_id"]: p for p in _briefs_data["products"]
}

# ---------------------------------------------------------------------------
# Top 10 ForgeFlow products — real market data from Master Rankings (March 2026)
# Scores are on a 0–100 scale:
#   demand        — eRank search volume signal (higher = more buyers searching)
#   competition   — inverse of seller density (higher = less competition = better)
#   manufacturing — ease and cost of printing (higher = faster/cheaper)
#   margin        — profit margin attractiveness
#   differentiation — parametric SKU expansion potential
# ---------------------------------------------------------------------------
DEMO_PRODUCTS = [
    {
        "product_id": "usb_cable_desk_organizer",
        "name": "USB / Cable Desk Organizer",
        "category": "cable organizers",
        "source": "forgescore",
        "source_keyword": "desk cable management",
        "phase": "launch_month_1",
        "research": {
            "listed_price": 16.00,
            "review_count": 2847,
            "rating": 4.4,
            "estimated_sales": 850,
            "competitor_count": 85,
            "listing_count": 200,
            "listing_age_days": 180,
        },
        # demand 1488 | margin 35.8% | parametric 5/5 | 168 units/mo
        "scores": {
            "demand": 78,
            "competition": 42,
            "manufacturing": 95,
            "margin": 75,
            "differentiation": 85,
        },
    },
    {
        "product_id": "universal_headset_wall_mount",
        "name": "Universal Headset Wall Mount",
        "category": "gaming accessories",
        "source": "forgescore",
        "source_keyword": "headset wall mount",
        "phase": "launch_month_1",
        "research": {
            "listed_price": 20.00,
            "review_count": 1245,
            "rating": 4.6,
            "estimated_sales": 620,
            "competitor_count": 55,
            "listing_count": 130,
            "listing_age_days": 120,
        },
        # demand 2058 (highest of all 14) | margin 26–34% | parametric 3/5
        "scores": {
            "demand": 92,
            "competition": 55,
            "manufacturing": 82,
            "margin": 68,
            "differentiation": 72,
        },
    },
    {
        "product_id": "french_cleat_tool_holder_series",
        "name": "French Cleat Tool Holder Series",
        "category": "workshop storage",
        "source": "forgescore",
        "source_keyword": "french cleat tool holder",
        "phase": "launch_month_2",
        "research": {
            "listed_price": 20.50,
            "review_count": 892,
            "rating": 4.5,
            "estimated_sales": 480,
            "competitor_count": 38,
            "listing_count": 85,
            "listing_age_days": 210,
        },
        # demand 1470 | margin 33.2% | parametric 5/5 | 36+ SKUs from one file
        "scores": {
            "demand": 76,
            "competition": 72,
            "manufacturing": 80,
            "margin": 78,
            "differentiation": 95,
        },
    },
    {
        "product_id": "controller_stand_universal",
        "name": "Controller Stand (PS5 / Xbox / Switch)",
        "category": "gaming accessories",
        "source": "forgescore",
        "source_keyword": "ps5 controller stand",
        "phase": "launch_month_2",
        "research": {
            "listed_price": 23.00,
            "review_count": 3200,
            "rating": 4.4,
            "estimated_sales": 740,
            "competitor_count": 120,
            "listing_count": 380,
            "listing_age_days": 90,
        },
        # demand 1680 | margin 30.1% | parametric 4/5 | 3000+ active listings = proven market
        "scores": {
            "demand": 84,
            "competition": 38,
            "manufacturing": 82,
            "margin": 72,
            "differentiation": 82,
        },
    },
    {
        "product_id": "compact_cable_organizer_clips",
        "name": "Compact Cable Organizer / Clips",
        "category": "cable organizers",
        "source": "forgescore",
        "source_keyword": "cable management clips desk",
        "phase": "launch_month_1",
        "research": {
            "listed_price": 15.00,
            "review_count": 1580,
            "rating": 4.3,
            "estimated_sales": 950,
            "competitor_count": 72,
            "listing_count": 165,
            "listing_age_days": 140,
        },
        # demand 980 | margin 33.7% | parametric 4/5 | 192 units/mo = highest throughput
        "scores": {
            "demand": 65,
            "competition": 48,
            "manufacturing": 98,
            "margin": 76,
            "differentiation": 80,
        },
    },
    {
        "product_id": "plant_propagation_station",
        "name": "Plant Propagation Station",
        "category": "home decor",
        "source": "forgescore",
        "source_keyword": "plant propagation station 3d printed",
        "phase": "month_3",
        "research": {
            "listed_price": 23.00,
            "review_count": 756,
            "rating": 4.7,
            "estimated_sales": 420,
            "competitor_count": 48,
            "listing_count": 110,
            "listing_age_days": 95,
        },
        # demand 1100 | margin 31.5% | parametric 3/5 | 4-pack bundle = best AOV play
        "scores": {
            "demand": 68,
            "competition": 62,
            "manufacturing": 85,
            "margin": 74,
            "differentiation": 72,
        },
    },
    {
        "product_id": "under_shelf_drill_impact_holder",
        "name": "Under-Shelf Drill / Impact Holder",
        "category": "workshop storage",
        "source": "forgescore",
        "source_keyword": "under shelf drill holder",
        "phase": "month_3",
        "research": {
            "listed_price": 21.00,
            "review_count": 445,
            "rating": 4.5,
            "estimated_sales": 310,
            "competitor_count": 32,
            "listing_count": 68,
            "listing_age_days": 160,
        },
        # demand 1225 | margin 34.9% (highest of workshop tools) | parametric 4/5
        "scores": {
            "demand": 72,
            "competition": 70,
            "manufacturing": 78,
            "margin": 82,
            "differentiation": 80,
        },
    },
    {
        "product_id": "gridfinity_drawer_organizer_kit",
        "name": "Gridfinity Drawer Organizer Kit",
        "category": "storage organizers",
        "source": "forgescore",
        "source_keyword": "gridfinity drawer organizer",
        "phase": "month_3",
        "research": {
            "listed_price": 31.50,
            "review_count": 2100,
            "rating": 4.6,
            "estimated_sales": 380,
            "competitor_count": 65,
            "listing_count": 145,
            "listing_age_days": 200,
        },
        # demand 1715 | margin 25.5% | parametric 5/5 | Gridfinity community = built-in traffic
        "scores": {
            "demand": 85,
            "competition": 45,
            "manufacturing": 72,
            "margin": 62,
            "differentiation": 95,
        },
    },
    {
        "product_id": "dual_controller_headset_stand",
        "name": "Dual Controller + Headset Stand",
        "category": "gaming accessories",
        "source": "forgescore",
        "source_keyword": "dual controller headset stand",
        "phase": "month_4",
        "research": {
            "listed_price": 33.00,
            "review_count": 620,
            "rating": 4.5,
            "estimated_sales": 280,
            "competitor_count": 42,
            "listing_count": 90,
            "listing_age_days": 75,
        },
        # demand 1340 | margin 32.9% | $10.53/unit = highest profit in gaming category
        "scores": {
            "demand": 74,
            "competition": 60,
            "manufacturing": 70,
            "margin": 76,
            "differentiation": 70,
        },
    },
    {
        "product_id": "board_game_organizer_insert",
        "name": "Board Game Organizer Insert",
        "category": "gaming accessories",
        "source": "forgescore",
        "source_keyword": "wingspan board game insert 3d printed",
        "phase": "phase_2",
        "research": {
            "listed_price": 46.50,
            "review_count": 890,
            "rating": 4.8,
            "estimated_sales": 185,
            "competitor_count": 28,
            "listing_count": 60,
            "listing_age_days": 180,
        },
        # demand 1200 | margin 25.5% | $13.17/unit = highest absolute profit | parametric 5/5
        "scores": {
            "demand": 70,
            "competition": 65,
            "manufacturing": 55,
            "margin": 62,
            "differentiation": 95,
        },
    },
]


def weighted_total(scores: dict) -> float:
    """ForgeFlow opportunity score formula."""
    return (
        scores["demand"] * 0.30
        + scores["competition"] * 0.20
        + scores["manufacturing"] * 0.20
        + scores["margin"] * 0.20
        + scores["differentiation"] * 0.10
    )


async def run_seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Product).limit(1))
        if existing.scalar_one_or_none() is not None:
            print("Database already has products. Skip seeding or delete data first.")
            return

        seeded_products = 0
        seeded_briefs = 0

        for i, data in enumerate(DEMO_PRODUCTS):
            # ------------------------------------------------------------------
            # 1. Product record
            # ------------------------------------------------------------------
            slug = slugify(data["name"])
            check = await db.execute(select(Product).where(Product.slug == slug))
            if check.scalar_one_or_none():
                slug = f"{slug}-{i}"

            product = Product(
                name=data["name"],
                slug=slug,
                category=data["category"],
                source=data["source"],
                source_keyword=data.get("source_keyword"),
                status=ProductStatus.SCORED,
            )
            db.add(product)
            await db.flush()  # get product.id before creating children

            # ------------------------------------------------------------------
            # 2. Research data record
            # ------------------------------------------------------------------
            r = data["research"]
            research = ResearchData(
                product_id=product.id,
                source_type="forgescore",
                keyword=data.get("source_keyword"),
                listed_price=r.get("listed_price"),
                review_count=r.get("review_count"),
                rating=r.get("rating"),
                estimated_sales=r.get("estimated_sales"),
                competitor_count=r.get("competitor_count"),
                listing_count=r.get("listing_count"),
                listing_age_days=r.get("listing_age_days"),
            )
            db.add(research)

            # ------------------------------------------------------------------
            # 3. Opportunity score record
            # ------------------------------------------------------------------
            s = data["scores"]
            total = weighted_total(s)
            score = OpportunityScore(
                product_id=product.id,
                demand_score=s["demand"],
                competition_score=s["competition"],
                manufacturing_score=s["manufacturing"],
                margin_score=s["margin"],
                differentiation_score=s["differentiation"],
                total_score=round(total, 1),
                scoring_notes=f"ForgeFlow Master Rankings March 2026 — Phase: {data.get('phase', 'unknown')}",
            )
            db.add(score)
            seeded_products += 1

            # ------------------------------------------------------------------
            # 4. CadModel record — pre-load design brief into parameters_json
            #    scad_code is null here; the CAD generation pipeline populates it
            #    by reading parameters_json and passing openscad_prompt to Claude
            # ------------------------------------------------------------------
            product_id_key = data.get("product_id")
            brief = DESIGN_BRIEFS.get(product_id_key)

            if brief:
                # Store the full brief so the CAD generation step has everything:
                # geometry, dimensions, parametric variables, avoid list, and
                # the ready-to-use openscad_prompt field.
                cad_model = CadModel(
                    product_id=product.id,
                    version=1,
                    model_type="parametric_brief",
                    parameters_json=json.dumps(brief, indent=2),
                    scad_code=None,          # populated by CAD generation pipeline
                    scad_file_path=None,     # populated after generation
                    stl_file_path=None,      # populated after slicing
                    generation_method="brief_pending",  # updated to "claude" after generation
                )
                db.add(cad_model)
                seeded_briefs += 1
            else:
                print(f"  WARNING: No design brief found for product_id '{product_id_key}' — CadModel not created")

        await db.commit()
        print(f"Seeded {seeded_products} products with research data and opportunity scores.")
        print(f"Seeded {seeded_briefs} CadModel records with design briefs loaded into parameters_json.")
        print()
        print("Next step: run the CAD generation pipeline.")
        print("  For each CadModel where generation_method='brief_pending':")
        print("  1. Read parameters_json -> extract ['design_brief']['openscad_prompt']")
        print("  2. Pass openscad_prompt to Claude for OpenSCAD generation")
        print("  3. Write result to scad_code, update generation_method to 'claude'")


if __name__ == "__main__":
    asyncio.run(run_seed())
