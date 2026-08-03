from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .api import router
from .auth import AuthService
from .core import HibikiError, Settings, setup_logging
from .database import Database
from .media import MediaService
from .scanner import LibraryScanner


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = Settings.load()
    logs = setup_logging(settings)
    database = Database(settings.database_path)
    database.initialize()
    auth = AuthService(database, settings)
    auth.ensure_initial_admin()
    scanner = LibraryScanner(settings, logs["scanner"])
    media = MediaService(settings, scanner)
    application.state.settings = settings
    application.state.database = database
    application.state.auth = auth
    application.state.scanner = scanner
    application.state.media = media
    logs["application"].info("Hibiki started")
    yield
    logs["application"].info("Hibiki stopped")


app = FastAPI(title="Hibiki", version="0.2.0", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(HibikiError)
async def hibiki_error(_: Request, error: HibikiError):
    status_code = 403 if error.__class__.__name__ == "AuthorizationError" else 401
    return JSONResponse(status_code=status_code, content={"success": False, "error": {"code": error.__class__.__name__.upper(), "message": str(error)}})


@app.exception_handler(HTTPException)
async def http_error(_: Request, error: HTTPException):
    detail = error.detail if isinstance(error.detail, str) else "Request failed"
    code = {401: "AUTHENTICATION_REQUIRED", 403: "AUTHORIZATION_FAILED", 404: "NOT_FOUND", 409: "CONFLICT"}.get(error.status_code, "REQUEST_FAILED")
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
app.mount("/localization", StaticFiles(directory=Path(__file__).resolve().parents[2] / "data" / "localization"), name="localization")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
