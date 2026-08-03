from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .api import router
from .auth import AuthService
from .core import HibikiError, Settings, VERSION, setup_logging
from .database import Database
from .media import MediaService
from .scanner import LibraryScanner

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "media-src 'self'; "
        "font-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "connect-src 'self'; "
        # The Teacher Mode reading page is a user-configured iframe that may
        # point at any http(s) URL; keep frames allowed accordingly.
        "frame-src http: https:"
    ),
}

STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = Settings.load()
    logs = setup_logging(settings)
    database = Database(settings.database_path)
    database.initialize()
    auth = AuthService(database, settings)
    created = auth.ensure_password()
    if created:
        logs["application"].info(
            "Generated the initial local password and wrote it to config/initial-admin.txt"
        )
    scanner = LibraryScanner(settings, logs["scanner"])
    media = MediaService(settings, scanner)
    application.state.settings = settings
    application.state.database = database
    application.state.auth = auth
    application.state.scanner = scanner
    application.state.media = media
    if not settings.library_path.exists():
        logs["application"].info("No library cache yet; starting a background scan")
        media.scan_async()
    if (settings.config_path.with_name("initial-admin.txt")).exists():
        logs["application"].warning(
            "config/initial-admin.txt still exists; delete it after unlocking to avoid exposing the bootstrap password"
        )
    logs["application"].info("Hibiki started")
    yield
    logs["application"].info("Hibiki stopped")


app = FastAPI(title="Hibiki", version=VERSION, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


@app.middleware("http")
async def enforce_same_origin(request: Request, call_next):
    """Reject cross-origin state-changing requests (CSRF defense-in-depth).

    The session cookie is already SameSite=Strict; this adds an Origin check
    for requests that carry one. Requests without an Origin header (curl,
    non-browser clients) are unaffected.
    """
    if request.method in STATE_CHANGING_METHODS:
        origin = request.headers.get("origin")
        if origin:
            parsed = urlparse(origin)
            if parsed.netloc != request.headers.get("host", ""):
                return JSONResponse(
                    status_code=403,
                    content={"success": False, "error": {"code": "CROSS_ORIGIN_DENIED", "message": "Cross-origin requests are not allowed"}},
                )
    return await call_next(request)


@app.exception_handler(HibikiError)
async def hibiki_error(_: Request, error: HibikiError):
    code = "AUTHENTICATION_REQUIRED" if error.__class__.__name__ == "AuthenticationError" else "REQUEST_FAILED"
    return JSONResponse(status_code=401, content={"success": False, "error": {"code": code, "message": str(error)}})


@app.exception_handler(HTTPException)
async def http_error(_: Request, error: HTTPException):
    detail = error.detail if isinstance(error.detail, str) else "Request failed"
    code = {401: "AUTHENTICATION_REQUIRED", 403: "AUTHORIZATION_FAILED", 404: "NOT_FOUND", 409: "CONFLICT", 429: "RATE_LIMITED"}.get(error.status_code, "REQUEST_FAILED")
    return JSONResponse(status_code=error.status_code, content={"success": False, "error": {"code": code, "message": detail}})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, error: RequestValidationError):
    details = "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
        for item in error.errors()
    )
    return JSONResponse(status_code=422, content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": details or "Invalid request"}})


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@app.get("/", include_in_schema=False)
async def frontend_index():
    return FileResponse(PROJECT_ROOT / "frontend" / "index.html")


@app.get("/LICENSE", include_in_schema=False)
async def project_license():
    return FileResponse(PROJECT_ROOT / "LICENSE", media_type="text/plain")


@app.get("/docs/ATTRIBUTION.md", include_in_schema=False)
async def project_attribution():
    return FileResponse(PROJECT_ROOT / "docs" / "ATTRIBUTION.md", media_type="text/markdown")


@app.head("/", include_in_schema=False)
async def frontend_head():
    return Response(status_code=200)


app.mount("/frontend", StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend"), name="frontend")
app.mount("/assets", StaticFiles(directory=Path(__file__).resolve().parents[2] / "assets"), name="assets")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
