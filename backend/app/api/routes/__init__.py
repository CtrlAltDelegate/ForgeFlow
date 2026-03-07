from fastapi import APIRouter
from app.api.routes import products, dashboard, imports as imports_routes

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(imports_routes.router, prefix="/imports", tags=["imports"])
