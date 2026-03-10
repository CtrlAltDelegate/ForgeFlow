"""ForgeFlow API entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

from app.core.config import settings
from app.core.database import init_db, fallback_to_sqlite
from app.api.routes import api_router

logger = logging.getLogger("uvicorn.error")


def _log_db_source() -> None:
    """Log which DB URL source is in use (no secrets). Helps debug Postgres auth failures."""
    url = settings.get_database_url()
    if "postgresql" in url:
        # Log host and user only (no password)
        try:
            from urllib.parse import urlparse
            p = urlparse(url)
            user = p.username or "(none)"
            host = p.hostname or "(none)"
            logger.info("Using Postgres: user=%s host=%s (from FORGEFLOW_PG_* or DATABASE_URL)", user, host)
        except Exception:
            logger.info("Using Postgres (from FORGEFLOW_PG_* or DATABASE_URL)")
    else:
        logger.info("Using SQLite (no Postgres credentials set)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup. If Postgres fails (e.g. invalid password), fall back to SQLite so the app still starts."""
    _log_db_source()
    try:
        await init_db()
    except Exception as e:
        err_msg = str(e).lower()
        if "password" in err_msg or "authentication" in err_msg or "connection" in err_msg or "invalid" in err_msg:
            logger.warning(
                "Postgres connection failed (%s). Falling back to SQLite. Data will not persist across redeploys. "
                "Fix: set FORGEFLOW_DATABASE_URL to a fresh URL, or set FORGEFLOW_PG_HOST, FORGEFLOW_PG_PORT, "
                "FORGEFLOW_PG_USER, FORGEFLOW_PG_PASSWORD, FORGEFLOW_PG_DATABASE (or use platform vars DATABASE_URL / PGHOST, etc.). See README.",
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
