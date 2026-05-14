import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.core.config import settings
from src.api.database.session import SessionLocal
from src.api.routers.router import api_router
from src.api.services.inference_engine import get_inference_engine

UTC = UTC


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Then load active models
    logger.info("API Starting: Loading active models into memory...")
    db = SessionLocal()
    try:
        engine = get_inference_engine()
        engine.load_all_active_models(db)
    except Exception as e:
        logger.error(f"Error loading models on startup: {e}")
    finally:
        db.close()
    yield
    # Shutdown (if needed)
    logger.info("API Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Global Exception Handlers


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {
                "status": 400,
                "message": "Validation Error",
                "errors": exc.errors(),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # QA10: Ensure generic messages for 401/403
    message = exc.detail
    if exc.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
        logger.info(f"Auth failure: {exc.detail}")
        # Keep the message from exc if it's already generic or set to generic if needed
        # In our services we already use generic messages.

    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "message": message, "timestamp": datetime.now(UTC).isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": 500, "message": "Internal Server Error", "timestamp": datetime.now(UTC).isoformat()},
    )


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat(), "version": "1.0.1"}


app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
