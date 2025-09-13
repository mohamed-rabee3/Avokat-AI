from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Session schemas
class SessionCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Optional session name")


class SessionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="New session name")


class SessionResponse(BaseModel):
    id: int
    name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Message schemas
class MessageCreate(BaseModel):
    session_id: int
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    token_count: Optional[int] = Field(None, ge=0, description="Token count for the message")


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    token_count: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Upload schemas
class UploadCreate(BaseModel):
    session_id: int
    file_name: str = Field(..., max_length=255, description="Name of the uploaded file")
    size_bytes: int = Field(..., ge=0, description="Size of the file in bytes")


class UploadResponse(BaseModel):
    id: int
    session_id: int
    file_name: str
    size_bytes: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Session with related data
class SessionWithMessages(SessionResponse):
    messages: List[MessageResponse] = []


class SessionWithUploads(SessionResponse):
    uploads: List[UploadResponse] = []


class SessionWithAll(SessionResponse):
    messages: List[MessageResponse] = []
    uploads: List[UploadResponse] = []