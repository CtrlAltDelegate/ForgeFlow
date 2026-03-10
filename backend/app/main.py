"""ForgeFlow API entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

from app.core.config import settings
from app.core.database import init_db, fallback_to_sqlite
from app.api.routes import api_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup. If Postgres fails (e.g. invalid password), fall back to SQLite so the app still starts."""
    try:
        await init_db()
    except Exception as e:
        err_msg = str(e).lower()
        if "password" in err_msg or "authentication" in err_msg or "connection" in err_msg or "invalid" in err_msg:
            logger.warning(
                "Postgres connection failed (%s). Falling back to SQLite. Data will not persist across redeploys. "
                "Update FORGEFLOW_DATABASE_URL with a fresh URL from Postgres → Variables.",
                e,
            )
            fallback_to_sqlite()
            await init_db()
        else:
            raise
    yield
    # shutdown if needed


app = FastAPI(
    title=settings.app_name,
    description="Product discovery engine for 3D-printable products",
    version="0.1.0",
    lifespan=lifespan,
)

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
# Fallback: ensure our known frontend(s) are in the list (e.g. if Railway env is empty)
_netlify_origins = ["https://forgeflowdashboard.netlify.app"]
for origin in _netlify_origins:
    if origin not in _origins:
        _origins.append(origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
