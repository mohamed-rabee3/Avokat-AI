"""
Ingest router for file upload and processing
Handles PDF upload, processing, and knowledge graph creation
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from uuid import uuid4
import logging
import asyncio

from ..db.sqlite import get_db, Session as DbSession, Upload as DbUpload
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest")
async def ingest(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingestion endpoint: PDF -> LlamaIndex chunks -> Graphiti episodes -> Neo4j (session-scoped)
    
    Args:
        session_id: ID of the session to associate the upload with
        file: PDF file to upload and process
        db: Database session
        
    Returns:
        Dictionary with ingestion status and statistics
    """
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
        from ..services.pdf_processor import pdf_processor
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF processor not available: {e}")

    try:
        # Process PDF and create chunks
        documents = pdf_processor.process_pdf(str(target_path), chunk_size=1000, chunk_overlap=100)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to parse PDF: {e}")

    # Neo4j Knowledge Graph Builder: extract and store knowledge graph
    try:
        from ..services.kg_builder import kg_builder
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