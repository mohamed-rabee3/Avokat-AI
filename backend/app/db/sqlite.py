import aiosqlite
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import AsyncGenerator
import os

from ..core.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="messages")


class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="uploads")


# Database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Database initialization
async def init_db():
    """Initialize the database and create tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Enable WAL mode for better concurrency
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        
        # Create indexes for better performance
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_uploads_session_id ON uploads(session_id)"))


# Database cleanup
async def close_db():
    """Close database connections"""
    await engine.dispose()