from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..db.sqlite import get_db, Session, Message, Upload
from ..models.schemas import SessionCreate, SessionResponse, SessionWithMessages, SessionWithUploads, SessionWithAll

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
    Delete a session and all its associated messages and uploads.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    await db.delete(session)
    await db.commit()
    
    return None