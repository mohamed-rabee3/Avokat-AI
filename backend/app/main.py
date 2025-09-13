from fastapi import FastAPI
from fastapi import UploadFile, File, Form, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from uuid import uuid4
import shutil
import os
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

from .core.config import settings
from .db.sqlite import init_db, close_db
from .db.sqlite import get_db, Session as DbSession, Upload as DbUpload
from .db.neo4j import neo4j_manager, init_neomodel
from .routers import sessions, neo4j, chat
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


# Ingestion endpoint: PDF -> LlamaIndex chunks -> Graphiti episodes -> Neo4j (session-scoped)
@app.post("/ingest")
async def ingest(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Validate session exists
    result = await db.execute(select(DbSession).where(DbSession.id == session_id))
    existing_session = result.scalar_one_or_none()
    if existing_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Validate file
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only PDF is supported.")

    # Persist file to uploads directory
    uploads_dir = Path("uploads") / str(session_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload.pdf").name
    target_path = uploads_dir / safe_name

    size_bytes = 0
    with target_path.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            size_bytes += len(chunk)

    # Record upload in SQLite
    db_upload = DbUpload(session_id=session_id, file_name=str(target_path), size_bytes=size_bytes)
    db.add(db_upload)
    await db.commit()
    await db.refresh(db_upload)

    # PyMuPDF: load + chunk
    try:
        from .services.pdf_processor import pdf_processor
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF processor not available: {e}")

    try:
        # Process PDF and create chunks
        documents = pdf_processor.process_pdf(str(target_path), chunk_size=1000, chunk_overlap=100)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to parse PDF: {e}")

    # Neo4j Knowledge Graph Builder: extract and store knowledge graph
    try:
        from .services.kg_builder import kg_builder
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Knowledge Graph Builder not available: {e}")

    # Check for Gemini API key (required for knowledge graph creation)
    gemini_api_key = settings.gemini_api_key
    if not gemini_api_key:
        logger.warning("Gemini API key not provided - required for knowledge graph creation")
        return {
            "status": "success",
            "session_id": session_id,
            "file_name": safe_name,
            "size_bytes": size_bytes,
            "chunks": len(documents),
            "nodes_created": 0,
            "relationships_created": 0,
            "batch_id": f"ingest_sess{session_id}_{uuid4()}_{Path(safe_name).stem}",
            "note": "Gemini API key required for knowledge graph creation"
        }

    try:
        # Initialize the knowledge graph builder
        await kg_builder.initialize()
        logger.info(f"Successfully connected to Neo4j Cloud: {settings.neo4j_uri}")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j Knowledge Graph Builder: {e}")
        return {
            "status": "success",
            "session_id": session_id,
            "file_name": safe_name,
            "size_bytes": size_bytes,
            "chunks": len(documents),
            "nodes_created": 0,
            "relationships_created": 0,
            "batch_id": f"ingest_sess{session_id}_{uuid4()}_{Path(safe_name).stem}",
            "note": f"Neo4j Knowledge Graph Builder connection failed: {str(e)}"
        }

    batch_id = f"ingest_sess{session_id}_{uuid4()}_{Path(safe_name).stem}"

    total_nodes = 0
    total_relationships = 0
    
    # Process documents to extract knowledge graph
    max_chunks = len(documents)
    
    # Rate limiting for Gemini LLM calls (15 requests per minute)
    import asyncio
    
    for idx, document in enumerate(documents[:max_chunks]):
        # Rate limiting: wait 4 seconds between LLM requests
        if idx > 0:  # Don't delay the first request
            logger.info(f"Rate limiting: waiting 4 seconds before processing chunk {idx + 1}/{max_chunks}")
            await asyncio.sleep(4)
        
        try:
            # Extract and store knowledge graph from document
            graph_document = await kg_builder.extract_and_store_graph(
                document=document,
                session_id=session_id
            )
            
            total_nodes += len(graph_document.nodes)
            total_relationships += len(graph_document.relationships)
            
            # Store document chunk for retrieval
            await kg_builder.store_document_chunk(
                document=document,
                session_id=session_id,
                chunk_index=idx
            )
            
            logger.info(f"Successfully processed chunk {idx + 1}/{max_chunks}: {len(graph_document.nodes)} nodes, {len(graph_document.relationships)} relationships")
            
        except Exception as e:
            logger.warning(f"Failed to process chunk {idx + 1}: {e}")

    # Get final session statistics
    try:
        session_stats = await kg_builder.get_session_stats(session_id)
        logger.info(f"Session {session_id} statistics: {session_stats}")
    except Exception as e:
        logger.warning(f"Failed to get session statistics: {e}")
        session_stats = {}

    return {
        "status": "success",
        "session_id": session_id,
        "file_name": safe_name,
        "size_bytes": size_bytes,
        "chunks": len(documents),
        "nodes_created": total_nodes,
        "relationships_created": total_relationships,
        "batch_id": batch_id,
        "session_stats": session_stats
    }