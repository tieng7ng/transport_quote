import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
from app.services.alert_service import alert_check_loop, daily_purge_loop

# Setup Logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Démarre les jobs de fond au lancement, les annule à l'arrêt."""
    task_alerts = asyncio.create_task(alert_check_loop())
    task_purge  = asyncio.create_task(daily_purge_loop())
    logger.info("Jobs de fond démarrés : détection alertes (2 min) + purge quotidienne")
    yield
    task_alerts.cancel()
    task_purge.cancel()
    logger.info("Jobs de fond arrêtés")


app = FastAPI(
    title=settings.app_name,
    description="API de gestion des devis transport",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue. Veuillez réessayer plus tard."},
    )


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes API
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Endpoint racine."""
    return {"app": settings.app_name, "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
