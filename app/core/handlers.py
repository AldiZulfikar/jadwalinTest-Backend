from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.logging import logger


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handler for domain specific AppExceptions."""
    logger.warning(f"AppException handling [{request.method} {request.url.path}]: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": exc.data,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for Pydantic validation errors."""
    errors = exc.errors()
    error_messages = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []) if l != "body")
        msg = err.get("msg", "Invalid input")
        error_messages.append(f"{loc}: {msg}" if loc else msg)
    
    combined_message = "; ".join(error_messages) or "Validation error"
    logger.warning(f"Validation error [{request.method} {request.url.path}]: {combined_message}")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": combined_message,
            "data": {"details": jsonable_encoder(errors)},
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for standard FastAPI HTTP exceptions."""
    logger.warning(f"HTTPException [{request.method} {request.url.path}]: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "data": None,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unexpected internal server errors."""
    logger.error(f"Unhandled Exception [{request.method} {request.url.path}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred.",
            "data": None,
        },
    )
