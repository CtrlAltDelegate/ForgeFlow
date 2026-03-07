from fastapi import APIRouter
from app.api.routes import products, dashboard

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
