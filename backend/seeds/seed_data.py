"""Seed demo data for ForgeFlow."""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models import Product, ResearchData, OpportunityScore
from app.models.product import ProductStatus, slugify


DEMO_PRODUCTS = [
    {
        "name": "Desk Cable Organizer Clip",
        "category": "cable organizers",
        "source": "seed",
        "source_keyword": "desk cable management",
        "research": {
            "listed_price": 12.99,
            "review_count": 2847,
            "rating": 4.3,
            "estimated_sales": 850,
            "competitor_count": 45,
            "listing_count": 120,
            "listing_age_days": 180,
        },
        "scores": {"demand": 78, "competition": 52, "manufacturing": 88, "margin": 72, "differentiation": 65},
    },
    {
        "name": "Vacuum Hose Adapter 1.25 to 2.5",
        "category": "vacuum adapters",
        "source": "seed",
        "source_keyword": "vacuum adapter",
        "research": {
            "listed_price": 8.99,
            "review_count": 1523,
            "rating": 4.5,
            "estimated_sales": 420,
            "competitor_count": 18,
            "listing_count": 35,
            "listing_age_days": 90,
        },
        "scores": {"demand": 72, "competition": 68, "manufacturing": 92, "margin": 80, "differentiation": 70},
    },
    {
        "name": "Pegboard Tool Holder",
        "category": "pegboard mounts",
        "source": "seed",
        "source_keyword": "pegboard organizer",
        "research": {
            "listed_price": 14.99,
            "review_count": 892,
            "rating": 4.1,
            "estimated_sales": 280,
            "competitor_count": 62,
            "listing_count": 95,
            "listing_age_days": 365,
        },
        "scores": {"demand": 65, "competition": 45, "manufacturing": 85, "margin": 68, "differentiation": 58},
    },
    {
        "name": "Monitor Riser with Cable Cutout",
        "category": "desk accessories",
        "source": "seed",
        "source_keyword": "monitor stand",
        "research": {
            "listed_price": 24.99,
            "review_count": 3421,
            "rating": 4.4,
            "estimated_sales": 620,
            "competitor_count": 88,
            "listing_count": 200,
            "listing_age_days": 120,
        },
        "scores": {"demand": 82, "competition": 38, "manufacturing": 75, "margin": 65, "differentiation": 72},
    },
    {
        "name": "Controller Wall Mount",
        "category": "gaming accessories",
        "source": "seed",
        "source_keyword": "game controller holder",
        "research": {
            "listed_price": 11.99,
            "review_count": 567,
            "rating": 4.6,
            "estimated_sales": 190,
            "competitor_count": 22,
            "listing_count": 40,
            "listing_age_days": 60,
        },
        "scores": {"demand": 68, "competition": 72, "manufacturing": 90, "margin": 78, "differentiation": 75},
    },
    {
        "name": "Dishwasher Rack Clip Replacement",
        "category": "appliance replacement parts",
        "source": "seed",
        "source_keyword": "dishwasher rack clip",
        "research": {
            "listed_price": 9.99,
            "review_count": 2103,
            "rating": 4.2,
            "estimated_sales": 510,
            "competitor_count": 12,
            "listing_count": 28,
            "listing_age_days": 200,
        },
        "scores": {"demand": 85, "competition": 82, "manufacturing": 88, "margin": 85, "differentiation": 60},
    },
    {
        "name": "USB Hub Desk Mount Bracket",
        "category": "desk accessories",
        "source": "seed",
        "source_keyword": "usb hub mount",
        "research": {
            "listed_price": 15.99,
            "review_count": 434,
            "rating": 4.0,
            "estimated_sales": 140,
            "competitor_count": 28,
            "listing_count": 55,
            "listing_age_days": 45,
        },
        "scores": {"demand": 58, "competition": 62, "manufacturing": 82, "margin": 70, "differentiation": 68},
    },
    {
        "name": "Headphone Stand with Base",
        "category": "desk accessories",
        "source": "seed",
        "source_keyword": "headphone stand",
        "research": {
            "listed_price": 18.99,
            "review_count": 1892,
            "rating": 4.5,
            "estimated_sales": 380,
            "competitor_count": 55,
            "listing_count": 110,
            "listing_age_days": 150,
        },
        "scores": {"demand": 75, "competition": 48, "manufacturing": 80, "margin": 72, "differentiation": 65},
    },
    {
        "name": "Router Shelf Bracket",
        "category": "mounts",
        "source": "seed",
        "source_keyword": "router shelf",
        "research": {
            "listed_price": 13.99,
            "review_count": 756,
            "rating": 4.3,
            "estimated_sales": 220,
            "competitor_count": 35,
            "listing_count": 68,
            "listing_age_days": 100,
        },
        "scores": {"demand": 70, "competition": 58, "manufacturing": 86, "margin": 74, "differentiation": 62},
    },
    {
        "name": "Drawer Divider Tray",
        "category": "organizers",
        "source": "seed",
        "source_keyword": "drawer organizer",
        "research": {
            "listed_price": 10.99,
            "review_count": 3201,
            "rating": 4.2,
            "estimated_sales": 720,
            "competitor_count": 95,
            "listing_count": 180,
            "listing_age_days": 220,
        },
        "scores": {"demand": 80, "competition": 35, "manufacturing": 78, "margin": 62, "differentiation": 55},
    },
    {
        "name": "GoPro Camera Mount Adapter",
        "category": "adapters",
        "source": "seed",
        "source_keyword": "gopro mount",
        "research": {
            "listed_price": 7.99,
            "review_count": 987,
            "rating": 4.4,
            "estimated_sales": 310,
            "competitor_count": 42,
            "listing_count": 75,
            "listing_age_days": 80,
        },
        "scores": {"demand": 72, "competition": 55, "manufacturing": 92, "margin": 82, "differentiation": 70},
    },
    {
        "name": "Spice Jar Lid Spacer",
        "category": "organizers",
        "source": "seed",
        "source_keyword": "spice rack",
        "research": {
            "listed_price": 6.99,
            "review_count": 445,
            "rating": 4.1,
            "estimated_sales": 165,
            "competitor_count": 25,
            "listing_count": 48,
            "listing_age_days": 130,
        },
        "scores": {"demand": 62, "competition": 65, "manufacturing": 95, "margin": 88, "differentiation": 58},
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

        for i, data in enumerate(DEMO_PRODUCTS):
            slug = slugify(data["name"])
            # Ensure unique slug
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
            await db.flush()

            r = data["research"]
            research = ResearchData(
                product_id=product.id,
                source_type="seed",
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
                scoring_notes="Seeded demo data",
            )
            db.add(score)

        await db.commit()
        print(f"Seeded {len(DEMO_PRODUCTS)} products with research and opportunity scores.")


if __name__ == "__main__":
    asyncio.run(run_seed())
