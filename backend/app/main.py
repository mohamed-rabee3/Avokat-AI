from fastapi import FastAPI
from contextlib import asynccontextmanager

from .core.config import settings
from .db.sqlite import init_db, close_db
from .routers import sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Include routers
app.include_router(sessions.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Avokat AI API",
        "version": settings.api_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}