from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums for type validation
class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    LEGAL_ENTITY = "LEGAL_ENTITY"
    COURT = "COURT"
    OTHER = "OTHER"


class FactType(str, Enum):
    LEGAL_FACT = "LEGAL_FACT"
    EVIDENCE = "EVIDENCE"
    TESTIMONY = "TESTIMONY"
    DOCUMENT_FACT = "DOCUMENT_FACT"
    CASE_FACT = "CASE_FACT"
    OTHER = "OTHER"


class DocumentType(str, Enum):
    CONTRACT = "CONTRACT"
    CASE_FILE = "CASE_FILE"
    LEGAL_BRIEF = "LEGAL_BRIEF"
    EVIDENCE = "EVIDENCE"
    CORRESPONDENCE = "CORRESPONDENCE"
    OTHER = "OTHER"


class LegalConceptCategory(str, Enum):
    STATUTE = "STATUTE"
    REGULATION = "REGULATION"
    CASE_LAW = "CASE_LAW"
    LEGAL_DOCTRINE = "LEGAL_DOCTRINE"
    PROCEDURAL_RULE = "PROCEDURAL_RULE"
    OTHER = "OTHER"


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"
    APPEALED = "APPEALED"
    SETTLED = "SETTLED"
    OTHER = "OTHER"


# Base schemas
class SessionIsolatedBase(BaseModel):
    session_id: int = Field(..., description="Session ID for isolation")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


# Entity schemas
class EntityCreate(SessionIsolatedBase):
    name: str = Field(..., min_length=1, max_length=255, description="Entity name")
    entity_type: EntityType = Field(..., description="Type of entity")
    description: Optional[str] = Field(None, description="Entity description")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional properties")


class EntityResponse(EntityCreate):
    id: int = Field(..., description="Entity ID")
    
    class Config:
        from_attributes = True


# Fact schemas
class FactCreate(SessionIsolatedBase):
    content: str = Field(..., min_length=1, description="Fact content")
    fact_type: FactType = Field(..., description="Type of fact")
    confidence_score: int = Field(100, ge=0, le=100, description="Confidence score (0-100)")
    source: Optional[str] = Field(None, description="Fact source")
    entity_ids: Optional[List[int]] = Field(None, description="Related entity IDs")


class FactResponse(FactCreate):
    id: int = Field(..., description="Fact ID")
    
    class Config:
        from_attributes = True


# Document schemas
class DocumentCreate(SessionIsolatedBase):
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    document_type: DocumentType = Field(..., description="Type of document")
    content: Optional[str] = Field(None, description="Document content")
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    upload_date: Optional[datetime] = Field(None, description="Upload date")


class DocumentResponse(DocumentCreate):
    id: int = Field(..., description="Document ID")
    
    class Config:
        from_attributes = True


# Legal Concept schemas
class LegalConceptCreate(SessionIsolatedBase):
    term: str = Field(..., min_length=1, max_length=255, description="Legal term")
    definition: Optional[str] = Field(None, description="Term definition")
    category: LegalConceptCategory = Field(..., description="Concept category")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction")


class LegalConceptResponse(LegalConceptCreate):
    id: int = Field(..., description="Legal concept ID")
    
    class Config:
        from_attributes = True


# Case schemas
class CaseCreate(SessionIsolatedBase):
    case_number: str = Field(..., min_length=1, max_length=100, description="Case number")
    case_name: str = Field(..., min_length=1, max_length=255, description="Case name")
    court: Optional[str] = Field(None, description="Court name")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction")
    case_date: Optional[datetime] = Field(None, description="Case date")
    status: CaseStatus = Field(..., description="Case status")


class CaseResponse(CaseCreate):
    id: int = Field(..., description="Case ID")
    
    class Config:
        from_attributes = True


# Relationship schemas
class RelationshipCreate(BaseModel):
    session_id: int = Field(..., description="Session ID for isolation")
    source_id: int = Field(..., description="Source node ID")
    target_id: int = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Type of relationship")
    properties: Optional[Dict[str, Any]] = Field(None, description="Relationship properties")


class RelationshipResponse(RelationshipCreate):
    id: int = Field(..., description="Relationship ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# Query schemas
class GraphQuery(BaseModel):
    session_id: int = Field(..., description="Session ID for isolation")
    query: str = Field(..., min_length=1, description="Cypher query")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class GraphQueryResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    execution_time: float = Field(..., description="Query execution time in seconds")


# Statistics schemas
class SessionStats(BaseModel):
    session_id: int = Field(..., description="Session ID")
    entity_count: int = Field(0, description="Number of entities")
    fact_count: int = Field(0, description="Number of facts")
    document_count: int = Field(0, description="Number of documents")
    legal_concept_count: int = Field(0, description="Number of legal concepts")
    case_count: int = Field(0, description="Number of cases")
    relationship_count: int = Field(0, description="Number of relationships")


# Search schemas
class GraphSearch(BaseModel):
    session_id: int = Field(..., description="Session ID for isolation")
    search_term: str = Field(..., min_length=1, description="Search term")
    node_types: Optional[List[str]] = Field(None, description="Node types to search")
    limit: int = Field(50, ge=1, le=1000, description="Maximum results")


class GraphSearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")


# Bulk operations
class BulkEntityCreate(BaseModel):
    session_id: int = Field(..., description="Session ID for isolation")
    entities: List[EntityCreate] = Field(..., min_items=1, max_items=1000)


class BulkFactCreate(BaseModel):
    session_id: int = Field(..., description="Session ID for isolation")
    facts: List[FactCreate] = Field(..., min_items=1, max_items=1000)


class BulkDocumentCreate(BaseModel):
    session_id: int = Field(..., description="Session ID for isolation")
    documents: List[DocumentCreate] = Field(..., min_items=1, max_items=1000)
