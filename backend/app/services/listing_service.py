"""
Listing generation: template-based or LLM-generated marketplace content.

Produces title, pitch, bullets, description, tags, suggested price,
photo prompt, why it could sell, differentiation angle.
When FORGEFLOW_LISTING_LLM_API_KEY is set, uses OpenAI to generate copy; otherwise uses templates.
"""

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import settings


@dataclass
class ListingInputs:
    product_name: str
    category: str
    listed_price: float | None = None
    competitor_count: int | None = None
    review_count: int | None = None
    rating: float | None = None
    source_keyword: str | None = None
    notes: str | None = None


@dataclass
class GeneratedListing:
    title: str
    short_pitch: str
    bullet_points: list[str]
    description: str
    tags: list[str]
    suggested_price: float
    photo_prompt: str
    why_it_could_sell: str
    differentiation_angle: str


def _title(name: str, category: str) -> str:
    """Etsy-style: name + category hint, under 60 chars."""
    base = f"{name} | {category.replace('_', ' ').title()}"
    return base[:60] if len(base) > 60 else base


def _pitch(name: str, category: str, keyword: str | None) -> str:
    return f"Quality {category.replace('_', ' ')}. {name}. {f'Perfect for {keyword}.' if keyword else 'Ready to ship.'}"[:500]


def _bullets(name: str, category: str, keyword: str | None) -> list[str]:
    return [
        f"Designed for durability and everyday use.",
        f"Fits standard {category.replace('_', ' ')} applications.",
        f"Clean finish, consistent quality.",
        f"{name} – as described, ready to use.",
        "Ships securely; contact for custom options.",
    ][:5]


def _description(name: str, category: str, keyword: str | None) -> str:
    return (
        f"This {name} is made for {category.replace('_', ' ')} use. "
        f"{f'Ideal for {keyword}.' if keyword else ''} "
        "Designed for a balance of strength and simplicity. "
        "Ships carefully packaged. If you have questions or need a variation, message before ordering."
    )


def _tags(category: str, name: str, keyword: str | None) -> list[str]:
    words = category.replace("_", " ").split() + name.split()[:3]
    if keyword:
        words.extend(keyword.split())
    base = list(dict.fromkeys(w.lower() for w in words if len(w) > 2))[:12]
    extra = ["3d printed", "functional", "practical", "custom", "durable"]
    combined = (base + extra)[:15]
    return combined[:15]


def _suggested_price(listed: float | None) -> float:
    if listed is not None and listed > 0:
        return round(listed, 2)
    return 12.99


def _photo_prompt(name: str, category: str) -> str:
    return f"Product photography of {name}, {category.replace('_', ' ')}, white background, soft shadow, high resolution, e-commerce style."


def _why_sell(price: float, competitor_count: int | None, rating: float | None) -> str:
    low_comp = competitor_count is not None and competitor_count < 30
    high_rating = rating is not None and rating >= 4.3
    parts = []
    if low_comp:
        parts.append("Niche demand without oversaturation.")
    if high_rating:
        parts.append("Similar products have strong reviews.")
    parts.append(f"Room for margin at ${price:.2f} with controlled material and time.")
    return " ".join(parts)[:500]


def _differentiation(competitor_count: int | None, rating: float | None) -> str:
    if competitor_count is not None and competitor_count > 50:
        return "Stand out with clear photos, accurate dimensions, and responsive messaging. Many listings are generic."
    if rating is not None and rating < 4.0:
        return "Competitors get complaints about fit or finish – emphasize quality control and consistency."
    return "Focus on clear listing, fast shipping, and optional customization to differentiate."


def _generate_listing_template(inputs: ListingInputs) -> GeneratedListing:
    """Template-based listing (used when no LLM key or on LLM failure)."""
    price = _suggested_price(inputs.listed_price)
    return GeneratedListing(
        title=_title(inputs.product_name, inputs.category),
        short_pitch=_pitch(inputs.product_name, inputs.category, inputs.source_keyword),
        bullet_points=_bullets(inputs.product_name, inputs.category, inputs.source_keyword),
        description=_description(inputs.product_name, inputs.category, inputs.source_keyword),
        tags=_tags(inputs.category, inputs.product_name, inputs.source_keyword),
        suggested_price=price,
        photo_prompt=_photo_prompt(inputs.product_name, inputs.category),
        why_it_could_sell=_why_sell(price, inputs.competitor_count, inputs.rating),
        differentiation_angle=_differentiation(inputs.competitor_count, inputs.rating),
    )


def _generate_listing_llm(inputs: ListingInputs) -> GeneratedListing | None:
    """Call OpenAI to generate listing copy. Returns None on failure or missing key."""
    if not (settings.listing_llm_api_key and settings.listing_llm_provider == "openai"):
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.listing_llm_api_key)
        notes = f" Notes: {inputs.notes}" if inputs.notes else ""
        prompt = (
            f"Generate a marketplace listing (Etsy-style) for this 3D-printed product.\n"
            f"Product name: {inputs.product_name}\n"
            f"Category: {inputs.category}\n"
            f"Optional context: listed_price={inputs.listed_price}, competitor_count={inputs.competitor_count}, "
            f"rating={inputs.rating}, keyword={inputs.source_keyword}.{notes}\n\n"
            "Respond with a single JSON object with these exact keys (strings unless noted): "
            "title (max 60 chars), short_pitch (max 500), bullet_points (array of 3-5 strings), "
            "description (max 1000), tags (array of 10-15 strings), suggested_price (number), "
            "photo_prompt (product photography prompt), why_it_could_sell (1-2 sentences), "
            "differentiation_angle (1-2 sentences). No markdown, only JSON."
        )
        resp = client.chat.completions.create(
            model=settings.listing_llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return None
        # Strip markdown code block if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        return GeneratedListing(
            title=str(data.get("title", ""))[:60] or _title(inputs.product_name, inputs.category),
            short_pitch=str(data.get("short_pitch", ""))[:500] or _pitch(inputs.product_name, inputs.category, inputs.source_keyword),
            bullet_points=[str(x) for x in data.get("bullet_points", [])][:5] or _bullets(inputs.product_name, inputs.category, inputs.source_keyword),
            description=str(data.get("description", ""))[:2000] or _description(inputs.product_name, inputs.category, inputs.source_keyword),
            tags=[str(x) for x in data.get("tags", [])][:15] or _tags(inputs.category, inputs.product_name, inputs.source_keyword),
            suggested_price=float(data.get("suggested_price", 0)) or _suggested_price(inputs.listed_price),
            photo_prompt=str(data.get("photo_prompt", ""))[:500] or _photo_prompt(inputs.product_name, inputs.category),
            why_it_could_sell=str(data.get("why_it_could_sell", ""))[:500] or _why_sell(_suggested_price(inputs.listed_price), inputs.competitor_count, inputs.rating),
            differentiation_angle=str(data.get("differentiation_angle", ""))[:500] or _differentiation(inputs.competitor_count, inputs.rating),
        )
    except Exception:
        return None


def generate_listing(inputs: ListingInputs) -> GeneratedListing:
    """Generate full marketplace listing: LLM if configured, else template."""
    llm_result = _generate_listing_llm(inputs)
    if llm_result is not None:
        return llm_result
    return _generate_listing_template(inputs)
