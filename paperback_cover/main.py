import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination

from paperback_cover.auth.routes import router as auth_router
from paperback_cover.billing.dodopayments.routes import router as dodopayments_router
from paperback_cover.commons.db import test_db_connection
from paperback_cover.config import settings
from paperback_cover.credit.routes import router as credit_router
from paperback_cover.feedback.routes import router as feedback_router
from paperback_cover.imageedit.extend_image.routes import router as extend_image_router
from paperback_cover.imageedit.format_conversion.routes import (
    router as format_conversion_router,
)
from paperback_cover.user.routes import router as user_router

logger = logging.getLogger(__name__)


def register_exception(app: FastAPI):

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTPException: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "message": "Validation error",
                "detail": exc.errors(),
            },
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check database connection on startup
    if not await test_db_connection():
        raise Exception(
            "Failed to connect to database. Please check your database configuration and ensure it's running."
        )
    else:
        logger.info("Database connection successful")
    yield


doc_url = "/api/docs"
redoc_url = "/api/redoc"
if not settings.app.api.docs:
    doc_url = None
    redoc_url = None

app = FastAPI(lifespan=lifespan, docs_url=doc_url, redoc_url=redoc_url)
register_exception(app)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(credit_router)
app.include_router(feedback_router)
app.include_router(dodopayments_router)
app.include_router(extend_image_router)
app.include_router(format_conversion_router)


add_pagination(app)
