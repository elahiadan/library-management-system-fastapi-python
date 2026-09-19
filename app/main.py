import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.core.responses import error, success
from app.routers import auth, authors, books, borrowings, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A production-style Library Management REST API.\n\n"
        "Features:\n"
        "- JWT authentication with role-based access control (ADMIN / MEMBER)\n"
        "- Authors, Books and Borrowings management\n"
        "- Borrow / return flow with stock validation\n"
        "- Overdue detection\n"
        "- Consistent envelope responses\n\n"
        "Use the lock icon on the right and paste a token returned by `POST /api/auth/login`."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc = err.get("loc", ())
        field = ".".join(str(part) for part in loc if part not in ("body", "query", "path"))
        errors[field or "body"] = err.get("msg", "Invalid value")
    return JSONResponse(
        status_code=422,
        content=error("Validation failed", errors),
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error(exc.message, exc.errors),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Error"
    return JSONResponse(
        status_code=exc.status_code or 500,
        content=error(detail),
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Integrity error: %s", exc)
    return JSONResponse(
        status_code=409,
        content=error("Resource already exists or violates a database constraint"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error("Internal server error"),
    )


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(authors.router, prefix=settings.api_prefix)
app.include_router(books.router, prefix=settings.api_prefix)
app.include_router(borrowings.router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
def root() -> dict[str, Any]:
    return success(
        f"Welcome to {settings.app_name}",
        {"docs": "/docs", "redoc": "/redoc", "health": "/health"},
    )


@app.get("/health", tags=["System"])
def health_check() -> dict[str, Any]:
    database = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        database = "unavailable"
    return success(
        "Health check",
        {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "database": database,
        },
    )