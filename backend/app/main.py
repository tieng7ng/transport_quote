from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API de gestion des devis transport",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes API
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Endpoint racine."""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
