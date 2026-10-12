"""App entry point: REST API at /api, MCP at /mcp, dashboard at /.

Run locally:  uvicorn app.main:app --reload
"""

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from mcp.server.transport_security import TransportSecuritySettings

from app import db, scheduler
from app.api.routes import router
from app.config import settings
from app.mcp_server import mcp
from app.services import Conflict, NotFound

logging.basicConfig(level=logging.INFO)
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def mcp_routes():
    """The MCP endpoint at exactly /mcp. Hosts not listed are rejected (DNS-rebinding protection)."""
    local_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*", "127.0.0.1", "localhost"]
    public_hosts = [h for host in settings.public_hosts for h in (host, f"{host}:*")]
    mcp_app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=local_hosts + public_hosts,
            allowed_origins=[f"https://{host}" for host in settings.public_hosts]
            + ["http://127.0.0.1:*", "http://localhost:*"],
        ),
    )
    # Reuse the route rather than mounting the sub-app, which would turn the URL into /mcp/.
    return mcp_app.routes


def check_settings() -> None:
    """Refuse to run publicly without a token: PUBLIC_HOSTS means the internet can reach /api and /mcp."""
    if settings.public_hosts and not settings.token:
        raise RuntimeError("PUBLIC_HOSTS is set, so PLANNER_TOKEN is required. Add a long random token to .env.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    check_settings()
    db.configure(settings.database_url)
    jobs = scheduler.start() if settings.scheduler_enabled else None
    async with mcp.session_manager.run():
        yield
    if jobs:
        jobs.shutdown()


async def require_token(request: Request, call_next):
    """If PLANNER_TOKEN is set, /api and /mcp need it as 'Authorization: Bearer <token>' or '?token=<token>'."""
    protected = request.url.path.startswith(("/api", "/mcp")) and request.url.path != "/api/health"
    if settings.token and protected:
        header = request.headers.get("authorization", "")
        given = header.removeprefix("Bearer ").strip() or request.query_params.get("token", "")
        if not secrets.compare_digest(given, settings.token):
            return JSONResponse({"detail": "Missing or wrong token"}, status_code=401)
    return await call_next(request)


async def not_found(_: Request, exc: NotFound):
    return JSONResponse({"detail": str(exc)}, status_code=404)


async def conflict(_: Request, exc: Conflict):
    return JSONResponse({"detail": str(exc)}, status_code=409)


def create_app() -> FastAPI:
    """A fresh app each call (the MCP session manager can only be started once per app)."""
    app = FastAPI(title="Student Life Planner", lifespan=lifespan)
    app.include_router(router)
    app.router.routes.extend(mcp_routes())
    app.middleware("http")(require_token)
    app.add_exception_handler(NotFound, not_found)
    app.add_exception_handler(Conflict, conflict)
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


app = create_app()
