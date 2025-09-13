"""
Chat router for conversation endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime

from ..db.sqlite import get_db, Session as DbSession, Message as DbMessage
from ..services.retrieval import retrieval_service
from ..services.llm import get_llm_service
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat endpoint for conversation with the legal assistant
    
    Args:
        request: Request object containing JSON body with session_id and message
        db: Database session
        
    Returns:
        Streaming response with assistant's reply
    """
    
    # Parse request body
    body = await request.json()
    session_id = body.get("session_id")
    message = body.get("message")
    
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_id is required")
    
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message is required")
    
    # Validate session exists
    result = await db.execute(select(DbSession).where(DbSession.id == session_id))
    existing_session = result.scalar_one_or_none()
    if existing_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Validate message
    if not message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")
    
    try:
        # Store user message
        user_message = DbMessage(
            session_id=session_id,
            role="user",
            content=message.strip(),
            token_count=len(message.split())  # Rough token estimation
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)
        
        # Get recent chat history (last 10 messages)
        history_result = await db.execute(
            select(DbMessage)
            .where(DbMessage.session_id == session_id)
            .order_by(desc(DbMessage.created_at))
            .limit(10)
        )
        chat_history = history_result.scalars().all()
        
        # Convert to dict format for LLM service
        history_messages = []
        for msg in reversed(chat_history):  # Reverse to get chronological order
            history_messages.append({
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            })
        
        # Retrieve relevant information from knowledge graph
        # Use "mixed" language to search across all languages
        retrieval_result = retrieval_service.retrieve_entities_and_relationships(
            query=message,
            session_id=str(session_id),  # Convert to string for Neo4j compatibility
            language="mixed",  # Search across all languages
            limit=15
        )
        
        # Debug logging
        logger.info(f"Retrieval result for query '{message}': entities={len(retrieval_result.get('entities', []))}, relationships={len(retrieval_result.get('relationships', []))}, context_chunks={len(retrieval_result.get('context_chunks', []))}")
        
        # Always proceed with LLM generation, even without context
        # The LLM can provide general legal assistance even without specific documents
        
        # Generate response using LLM
        llm_service = get_llm_service()
        
        # Create streaming response
        async def generate_response():
            response_chunks = []
            
            try:
                async for chunk in llm_service.generate_response(
                    user_message=message,
                    retrieval_result=retrieval_result,
                    chat_history=history_messages,
                    stream=True
                ):
                    response_chunks.append(chunk)
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Complete response
                full_response = "".join(response_chunks)
                
                # Store assistant response
                assistant_message = DbMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    token_count=len(full_response.split())
                )
                db.add(assistant_message)
                await db.commit()
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True, 'sources': _extract_sources(retrieval_result)})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in chat generation: {e}")
                error_response = f"I apologize, but I encountered an error while processing your request. Please try again."
                
                # Store error response
                assistant_message = DbMessage(
                    session_id=session_id,
                    role="assistant",
                    content=error_response,
                    token_count=len(error_response.split())
                )
                db.add(assistant_message)
                await db.commit()
                
                yield f"data: {json.dumps({'error': error_response})}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/non-streaming")
async def chat_non_streaming(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Non-streaming chat endpoint for simple request/response
    
    Args:
        request: Request object containing JSON body with session_id and message
        db: Database session
        
    Returns:
        Complete response with sources
    """
    
    # Parse request body
    body = await request.json()
    session_id = body.get("session_id")
    message = body.get("message")
    
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_id is required")
    
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message is required")
    
    # Validate session exists
    result = await db.execute(select(DbSession).where(DbSession.id == session_id))
    existing_session = result.scalar_one_or_none()
    if existing_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Validate message
    if not message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")
    
    try:
        # Store user message
        user_message = DbMessage(
            session_id=session_id,
            role="user",
            content=message.strip(),
            token_count=len(message.split())
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)
        
        # Get recent chat history
        history_result = await db.execute(
            select(DbMessage)
            .where(DbMessage.session_id == session_id)
            .order_by(desc(DbMessage.created_at))
            .limit(10)
        )
        chat_history = history_result.scalars().all()
        
        # Convert to dict format
        history_messages = []
        for msg in reversed(chat_history):
            history_messages.append({
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            })
        
        # Retrieve relevant information
        # Use "mixed" language to search across all languages
        retrieval_result = retrieval_service.retrieve_entities_and_relationships(
            query=message,
            session_id=str(session_id),  # Convert to string for Neo4j compatibility
            language="mixed",  # Search across all languages
            limit=15
        )
        
        # Debug logging
        logger.info(f"Retrieval result for query '{message}': entities={len(retrieval_result.get('entities', []))}, relationships={len(retrieval_result.get('relationships', []))}, context_chunks={len(retrieval_result.get('context_chunks', []))}")
        
        # Always use LLM - with or without document context
        # If no specific context found, LLM will still respond with general knowledge
        if not retrieval_result.get("entities") and not retrieval_result.get("relationships"):
            logger.info(f"No specific document context found for query '{message}' in session {session_id}. Using LLM with general knowledge.")
            # Keep retrieval_result empty - LLM will handle general questions
        
        # Generate response
        llm_service = get_llm_service()
        response = await llm_service.generate_response_sync(
            user_message=message,
            retrieval_result=retrieval_result,
            chat_history=history_messages
        )
        
        # Store assistant response
        assistant_message = DbMessage(
            session_id=session_id,
            role="assistant",
            content=response,
            token_count=len(response.split())
        )
        db.add(assistant_message)
        await db.commit()
        
        return {
            "response": response,
            "sources": _extract_sources(retrieval_result)
        }
        
    except Exception as e:
        logger.error(f"Error in non-streaming chat: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat history for a session
    
    Args:
        session_id: Session ID
        limit: Maximum number of messages to return
        db: Database session
        
    Returns:
        List of messages in chronological order
    """
    
    # Validate session exists
    result = await db.execute(select(DbSession).where(DbSession.id == session_id))
    existing_session = result.scalar_one_or_none()
    if existing_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    try:
        # Get messages
        messages_result = await db.execute(
            select(DbMessage)
            .where(DbMessage.session_id == session_id)
            .order_by(DbMessage.created_at)
            .limit(limit)
        )
        messages = messages_result.scalars().all()
        
        # Convert to response format
        response_messages = []
        for msg in messages:
            response_messages.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "token_count": msg.token_count,
                "created_at": msg.created_at.isoformat()
            })
        
        return {
            "session_id": session_id,
            "messages": response_messages,
            "total_count": len(response_messages)
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def _extract_sources(retrieval_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract sources from enhanced retrieval result for citations"""
    sources = []
    
    # Add entity sources
    for entity in retrieval_result.get("entities", []):
        sources.append({
            "type": "entity",
            "name": entity.get("name"),
            "entity_type": entity.get("entity_type"),
            "language": entity.get("language"),
            "relevance_score": entity.get("relevance_score")
        })
    
    # Add relationship sources
    for rel in retrieval_result.get("relationships", []):
        sources.append({
            "type": "relationship",
            "relationship_type": rel.get("type"),
            "language": rel.get("language")
        })
    
    # Add expanded context sources
    for item in retrieval_result.get("expanded_context", []):
        if item["type"] == "expanded_entity":
            entity = item["entity"]
            sources.append({
                "type": "related_entity",
                "name": entity.get("name"),
                "entity_type": entity.get("entity_type"),
                "relationship_type": item.get("relationship_type"),
                "language": entity.get("language")
            })
        elif item["type"] == "expanded_relationship":
            rel = item["relationship"]
            sources.append({
                "type": "related_relationship",
                "relationship_type": rel.get("type"),
                "connection_type": item.get("relationship_type"),
                "language": rel.get("language")
            })
    
    # Add context chunk sources (document content)
    for i, chunk in enumerate(retrieval_result.get("context_chunks", [])):
        sources.append({
            "type": "document_chunk",
            "content_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
            "language": retrieval_result.get("language", "unknown"),
            "chunk_index": i
        })
    
    # Add search terms for transparency
    if retrieval_result.get("search_terms"):
        sources.append({
            "type": "search_info",
            "search_terms": retrieval_result["search_terms"],
            "language": retrieval_result.get("language", "unknown")
        })
    
    return sources