"""ForgeFlow API entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging
import os
from urllib.parse import urlparse

from app.core.config import settings
from app.core.database import init_db, fallback_to_sqlite
from app.api.routes import api_router

logger = logging.getLogger("uvicorn.error")


def _log_db_source() -> None:
    """Log which DB URL source is in use (no secrets). Helps debug Postgres auth failures on Railway."""
    # Inspect which env vars are actually present
    raw_db_url = os.environ.get("DATABASE_URL", "")
    pg_host_present = bool((settings.pg_host or "").strip() or os.environ.get("PGHOST", ""))
    forgeflow_db_url_present = bool(os.environ.get("FORGEFLOW_DATABASE_URL", ""))

    # Check for FORGEFLOW_PG_* overrides (these take precedence over auto-injected PG vars)
    forgeflow_pg_overrides = {
        k: "set" for k in ("FORGEFLOW_PG_HOST", "FORGEFLOW_PG_PORT", "FORGEFLOW_PG_USER",
                           "FORGEFLOW_PG_PASSWORD", "FORGEFLOW_PG_DATABASE")
        if os.environ.get(k, "").strip()
    }

    logger.info(
        "DB env vars present: DATABASE_URL=%s  PGHOST=%s  FORGEFLOW_DATABASE_URL=%s  FORGEFLOW_PG_*=%s",
        "set" if raw_db_url else "not set",
        "set" if pg_host_present else "not set",
        "set" if forgeflow_db_url_present else "not set",
        ",".join(forgeflow_pg_overrides) if forgeflow_pg_overrides else "none",
    )
    if forgeflow_pg_overrides:
        logger.warning(
            "FORGEFLOW_PG_* overrides are set (%s) and will take precedence over Railway-injected "
            "PGHOST/PGPASSWORD etc. If these contain stale credentials, delete them from Railway Variables.",
            ", ".join(forgeflow_pg_overrides),
        )

    # Detect unresolved Railway reference variables (e.g. ${{Postgres.DATABASE_URL}})
    if raw_db_url and "${{" in raw_db_url:
        logger.warning(
            "DATABASE_URL contains an unresolved Railway reference (%r). "
            "The variable was not expanded before the process started -- "
            "check that the ForgeFlow service references the correct Postgres service name in Railway. "
            "The app will attempt to use PGHOST/PGPASSWORD etc. instead.",
            raw_db_url,
        )

    # Determine which source get_database_url() is using (mirrors its own selection logic)
    if raw_db_url and "postgres" in raw_db_url.lower() and "${{" not in raw_db_url:
        source = "DATABASE_URL env var"
    elif pg_host_present:
        source = "PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE (or FORGEFLOW_PG_* equivalents)"
    elif forgeflow_db_url_present:
        source = "FORGEFLOW_DATABASE_URL env var"
    else:
        source = "SQLite default (no Postgres credentials found)"

    url = settings.get_database_url()
    if "postgresql" in url:
        try:
            p = urlparse(url)
            logger.info(
                "Using Postgres [source=%s]: user=%s  host=%s  port=%s  db=%s",
                source,
                p.username or "(none)",
                p.hostname or "(none)",
                p.port or "(none)",
                (p.path or "").lstrip("/") or "(none)",
            )
        except Exception:
            logger.info("Using Postgres [source=%s] (URL parse error)", source)
    else:
        logger.info("Using SQLite [source=%s]", source)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup. If Postgres fails (e.g. invalid password), fall back to SQLite so the app still starts."""
    _log_db_source()
    try:
        await init_db()
    except Exception as e:
        err_msg = str(e).lower()
        if "password" in err_msg or "authentication" in err_msg or "connection" in err_msg or "invalid" in err_msg:
            # Build a Railway-specific hint based on which source was being tried
            raw_db_url = os.environ.get("DATABASE_URL", "")
            pg_host_present = bool((settings.pg_host or "").strip() or os.environ.get("PGHOST", ""))
            if raw_db_url and "postgres" in raw_db_url.lower() and "${{" not in raw_db_url:
                fix_hint = (
                    "DATABASE_URL is set but authentication failed. "
                    "On Railway: redeploy to pick up fresh credentials, or confirm the Postgres service "
                    "is in the same project and DATABASE_URL references it (not DATABASE_PUBLIC_URL)."
                )
            elif raw_db_url and "${{" in raw_db_url:
                fix_hint = (
                    "DATABASE_URL contains an unresolved reference. "
                    "On Railway: verify the variable reference name matches your Postgres service name "
                    "and that the ForgeFlow service is linked to the Postgres service."
                )
            elif pg_host_present:
                fix_hint = (
                    "PGHOST/PGPASSWORD (or FORGEFLOW_PG_*) are set but authentication failed. "
                    "On Railway: redeploy to refresh injected PG credentials, or set DATABASE_URL "
                    "as a reference to ${{<PostgresServiceName>.DATABASE_URL}}."
                )
            else:
                fix_hint = (
                    "No Postgres credentials found. "
                    "On Railway: set DATABASE_URL as a reference to ${{<PostgresServiceName>.DATABASE_URL}}, "
                    "or set FORGEFLOW_DATABASE_URL to a fresh URL copied from Postgres -> Variables."
                )
            logger.warning(
                "Postgres connection failed (%s). Falling back to SQLite. "
                "Data will not persist across redeploys. %s",
                e,
                fix_hint,
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
