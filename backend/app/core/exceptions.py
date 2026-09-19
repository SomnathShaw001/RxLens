"""
Global error handling middleware and structured error responses.
Ensures all exceptions return RFC 7807-compliant Problem Detail JSON.
"""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Returns structured 422 responses for request validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg"),
            "type": error.get("type"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": errors,
            "status": 422,
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Converts SQLAlchemy errors into 503 responses without leaking stack traces."""
    logger.error(f"Database error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Database Error",
            "detail": "A database error occurred. Please try again shortly.",
            "status": 503,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unexpected internal errors."""
    logger.exception(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Our team has been notified.",
            "status": 500,
        },
    )
