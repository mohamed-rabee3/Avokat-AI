from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .db.sqlite import init_db, close_db
from .db.neo4j import neo4j_manager, init_neomodel
from .routers import sessions, neo4j, chat, ingest
# from .services.bge_embedder import BGEM3Embedder, BGEM3EmbedderConfig  # Not used in current implementation
from .services.retrieval import retrieval_service
from .services.llm import initialize_llm_service
from .services.kg_builder import kg_builder
from .services.embedding_service import embedding_service

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
        
        # Initialize retrieval service
        retrieval_service.initialize(
            uri=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )
        logger.info("Retrieval service initialized")
        
        # Initialize embedding service
        embedding_service.initialize()
        logger.info("Embedding service initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {e}")
        # Continue without Neo4j for now
    
    # Initialize LLM service
    try:
        if settings.gemini_api_key:
            await initialize_llm_service(settings.gemini_api_key)
            logger.info("LLM service initialized")
        else:
            logger.warning("Gemini API key not provided - LLM service not initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LLM service: {e}")
        # Continue without LLM service
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    await neo4j_manager.close()
    retrieval_service.close()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware - Comprehensive configuration for all development scenarios
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Localhost variations
        "http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "http://localhost:8080", 
        "http://localhost:8081", "http://localhost:8082", "http://localhost:8083", "http://localhost:8084",
        # 127.0.0.1 variations  
        "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8080",
        "http://127.0.0.1:8081", "http://127.0.0.1:8082", "http://127.0.0.1:8083", "http://127.0.0.1:8084",
        # Network IP variations (for different network interfaces)
        "http://26.249.156.137:8080", "http://192.168.1.2:8080", "http://192.168.56.1:8080",
        "http://192.168.154.1:8080", "http://192.168.75.1:8080", "http://172.25.32.1:8080",
        # Additional common development ports
        "http://localhost:3001", "http://localhost:4000", "http://localhost:5000",
        "http://127.0.0.1:3001", "http://127.0.0.1:4000", "http://127.0.0.1:5000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept", "Accept-Language", "Content-Language", "Content-Type",
        "Authorization", "X-Requested-With", "Origin", "Access-Control-Request-Method",
        "Access-Control-Request-Headers", "Cache-Control", "Pragma"
    ],
)

# Include routers
app.include_router(sessions.router)
app.include_router(neo4j.router)
app.include_router(chat.router)
app.include_router(ingest.router)


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

