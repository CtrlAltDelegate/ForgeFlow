from fastapi import APIRouter
from app.api.routes import (
    products,
    dashboard,
    imports as imports_routes,
    cad as cad_routes,
    simulation as simulation_routes,
    listings as listings_routes,
)

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
# More specific /products routes first
api_router.include_router(cad_routes.router, prefix="/products", tags=["cad"])
api_router.include_router(simulation_routes.router, prefix="/products", tags=["simulation"])
api_router.include_router(listings_routes.router, prefix="/products", tags=["listings"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(imports_routes.router, prefix="/imports", tags=["imports"])
