"""Listing schemas."""
from datetime import datetime
from pydantic import BaseModel


class ListingResponse(BaseModel):
    id: int
    product_id: int
    version: int
    title: str | None
    short_pitch: str | None
    bullet_points_json: str | None
    description: str | None
    tags_json: str | None
    suggested_price: float | None
    photo_prompt: str | None
    why_it_could_sell: str | None
    differentiation_angle: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ListingUpdate(BaseModel):
    title: str | None = None
    short_pitch: str | None = None
    bullet_points_json: str | None = None
    description: str | None = None
    tags_json: str | None = None
    suggested_price: float | None = None
    photo_prompt: str | None = None
    why_it_could_sell: str | None = None
    differentiation_angle: str | None = None
