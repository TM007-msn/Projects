"""FastAPI application.

Public:     /  (the app shell and its static files), /api/health, /api/login
Protected:  /api/* (everything else) and /content/* (revision content JSON)

Run locally (env vars from .env, see .env.example):
    uvicorn --factory app.main:create_app --reload
"""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import auth, db
from app.config import Settings, load_settings
from app.events import EventBatch, insert_events, list_events

STATIC_DIR = Path(__file__).resolve().parent / "static"


class LoginBody(BaseModel):
    password: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    conn = db.connect(settings.db_path)
    limiter = auth.LoginRateLimiter()
    app = FastAPI(title="H446 Revision", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings, app.state.conn, app.state.limiter = settings, conn, limiter

    # ---- security helpers --------------------------------------------------

    def require_login(request: Request) -> None:
        token = request.cookies.get(auth.COOKIE_NAME)
        if not auth.check_session_token(token, settings.secret_key):
            raise HTTPException(status_code=401, detail="Not logged in")

    @app.middleware("http")
    async def json_only_posts(request: Request, call_next):
        # Basic CSRF defence: browsers won't send a cross-site POST with a JSON
        # content type without a CORS preflight, and CORS isn't enabled.
        if request.method in ("POST", "PUT", "DELETE") and request.url.path.startswith("/api/"):
            ctype = request.headers.get("content-type", "")
            if not ctype.startswith("application/json"):
                return JSONResponse({"detail": "JSON required"}, status_code=415)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        return response

    # ---- public routes -----------------------------------------------------

    @app.get("/api/health")
    def health():
        return {"ok": True}

    @app.post("/api/login")
    def login(body: LoginBody, request: Request, response: Response):
        ip = request.client.host if request.client else "unknown"
        if limiter.blocked(ip):
            raise HTTPException(status_code=429, detail="Too many attempts. Try again in 15 minutes.")
        if not auth.verify_password(body.password, settings.password_hash):
            limiter.record_failure(ip)
            raise HTTPException(status_code=401, detail="Wrong password")
        limiter.reset(ip)
        response.set_cookie(
            auth.COOKIE_NAME,
            auth.make_session_token(settings.secret_key, settings.session_days),
            max_age=settings.session_days * 86400,
            httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
        )
        return {"ok": True}

    @app.post("/api/logout")
    def logout(response: Response):
        response.delete_cookie(auth.COOKIE_NAME, path="/")
        return {"ok": True}

    @app.get("/api/session")
    def session(request: Request):
        token = request.cookies.get(auth.COOKIE_NAME)
        return {"authenticated": auth.check_session_token(token, settings.secret_key)}

    # ---- protected routes --------------------------------------------------

    @app.get("/api/events", dependencies=[Depends(require_login)])
    def get_events():
        return {"events": list_events(conn)}

    @app.post("/api/events", dependencies=[Depends(require_login)])
    def post_events(batch: EventBatch):
        return insert_events(conn, batch.events)

    @app.get("/content/{path:path}", dependencies=[Depends(require_login)])
    def content(path: str):
        base = settings.content_dir.resolve()
        target = (base / path).resolve()
        # Refuse anything outside the content folder (e.g. ../../etc/passwd)
        # and anything that isn't JSON.
        if base not in target.parents or target.suffix != ".json" or not target.is_file():
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(target, media_type="application/json",
                            headers={"Cache-Control": "no-cache"})

    # The app shell. Mounted last so the API routes above take priority.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app
