from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..db.sqlite import get_db, Session, Message, Upload
from ..db.neo4j import neo4j_manager
from ..models.schemas import SessionCreate, SessionUpdate, SessionResponse, SessionWithMessages, SessionWithUploads, SessionWithAll

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new session.
    
    - **name**: Optional session name (max 255 characters)
    """
    # Create new session
    db_session = Session(name=session_data.name)
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    
    return db_session


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all sessions with pagination.
    
    - **skip**: Number of sessions to skip (default: 0)
    - **limit**: Maximum number of sessions to return (default: 100)
    """
    result = await db.execute(
        select(Session)
        .order_by(Session.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific session by ID.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a session's name.
    
    - **name**: New session name (max 255 characters)
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Update session name if provided
    if session_data.name is not None:
        session.name = session_data.name
    
    await db.commit()
    await db.refresh(session)
    
    return session


@router.get("/{session_id}/messages", response_model=SessionWithMessages)
async def get_session_with_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a session with all its messages.
    """
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@router.get("/{session_id}/uploads", response_model=SessionWithUploads)
async def get_session_with_uploads(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a session with all its uploads.
    """
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@router.get("/{session_id}/full", response_model=SessionWithAll)
async def get_session_full(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a session with all its messages and uploads.
    """
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a session and all its associated messages, uploads, and Neo4j knowledge graph data.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    try:
        # Clear Neo4j knowledge graph data for this session
        await neo4j_manager.clear_session_data(session_id)
        
        # Delete SQLite session (messages and uploads will be cascade deleted)
        await db.delete(session)
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )
    
    return None