import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import AppException
from app.core.handlers import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.api.v1.endpoints import bookings, environments, health
from app.api.v1.router import api_router, root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' mode on port {settings.PORT}...")

    # Validate production JWT secret
    if settings.APP_ENV == "production" and "supersecret" in settings.JWT_SECRET_KEY:
        logger.warning(
            "CRITICAL SECURITY WARNING: Default JWT_SECRET_KEY is being used in production environment! Please set a secure JWT_SECRET_KEY environment variable."
        )

    yield
    # Shutdown tasks
    logger.info(f"Shutting down {settings.APP_NAME} gracefully...")


app = FastAPI(
    title="JadwalinTest API",
    description=(
        "**JadwalinTest API** - *Jadwal Terkendali, Aplikasi Siap Berlari!*\n\n"
        "Internal QA Portal backend providing RESTful APIs to manage performance testing schedules, "
        "enforce schedule overlap prevention, soft delete support, normalized environment master table, and notification alerts."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Liveness & Readiness health probe endpoints for system monitoring and container orchestrators (OpenShift / Kubernetes)."
        },
        {
            "name": "Environments",
            "description": "Read-only master list of active performance testing environments."
        },
        {
            "name": "Bookings",
            "description": "CRUD operations for managing performance test reservations and schedule availability."
        },
        {
            "name": "User Management",
            "description": "QA administrative operations for creating, updating, resetting passwords, and deactivating user accounts."
        }
    ]
)

# Configurable CORS origins
origins = settings.get_cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request correlation ID & Security headers middleware
@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    # 1. Resolve or generate Request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    # 2. Attach X-Request-ID to response headers
    response.headers["X-Request-ID"] = request_id

    # 3. Attach Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # 4. Structured HTTP Request Logging
    if not request.url.path.startswith("/health"):
        logger.info(
            f"HTTP {request.method} {request.url.path} [req_id={request_id}] -> Status {response.status_code} ({process_time:.2f}ms)"
        )

    return response


# Register Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# Register Routers
# Directly exposed paths: /health, /environments, /bookings
app.include_router(root_router)
app.include_router(bookings.router)

# Versioned API routes: /api/v1/...
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
