from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .db.sqlite import init_db, close_db
from .db.neo4j import neo4j_manager, init_neomodel
from .routers import sessions, neo4j

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    
    # Initialize SQLite database
    await init_db()
    logger.info("SQLite database initialized")
    
    # Initialize Neo4j database
    try:
        await neo4j_manager.initialize()
        await init_neomodel()
        logger.info("Neo4j database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {e}")
        # Continue without Neo4j for now
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    await neo4j_manager.close()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Include routers
app.include_router(sessions.router)
app.include_router(neo4j.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Avokat AI API",
        "version": settings.api_version,
        "docs": "/docs",
        "features": ["SQLite Sessions", "Neo4j Knowledge Graph"]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}