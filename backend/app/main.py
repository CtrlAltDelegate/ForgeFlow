"""ForgeFlow API entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    await init_db()
    yield
    # shutdown if needed


app = FastAPI(
    title=settings.app_name,
    description="Product discovery engine for 3D-printable products",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
