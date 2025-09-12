from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
import time
import logging

from ..db.neo4j import (
    neo4j_manager, get_neo4j_manager, Neo4jManager,
    Entity, Fact, Document, LegalConcept, Case
)
from ..models.neo4j_schemas import (
    EntityCreate, EntityResponse, FactCreate, FactResponse,
    DocumentCreate, DocumentResponse, LegalConceptCreate, LegalConceptResponse,
    CaseCreate, CaseResponse, RelationshipCreate, RelationshipResponse,
    GraphQuery, GraphQueryResponse, SessionStats, GraphSearch, GraphSearchResponse,
    BulkEntityCreate, BulkFactCreate, BulkDocumentCreate
)

router = APIRouter(prefix="/neo4j", tags=["neo4j"])
logger = logging.getLogger(__name__)


# Health check
@router.get("/health")
async def neo4j_health():
    """Check Neo4j connection health"""
    try:
        # Try to get manager without dependency injection to avoid initialization issues
        if not neo4j_manager._initialized:
            await neo4j_manager.initialize()
        
        # Test basic connectivity
        result = await neo4j_manager.execute_query("RETURN 1 as test")
        return {"status": "healthy", "message": "Neo4j connection is working"}
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        return {
            "status": "unavailable", 
            "message": "Neo4j connection failed", 
            "error": str(e),
            "note": "Neo4j server is not running or not accessible"
        }


# Session statistics
@router.get("/sessions/{session_id}/stats")
async def get_session_stats(session_id: int):
    """Get statistics for a specific session"""
    try:
        if not neo4j_manager._initialized:
            await neo4j_manager.initialize()
        
        stats = await neo4j_manager.get_session_stats(session_id)
        
        return SessionStats(
            session_id=session_id,
            entity_count=stats.get("Entity", 0),
            fact_count=stats.get("Fact", 0),
            document_count=stats.get("Document", 0),
            legal_concept_count=stats.get("LegalConcept", 0),
            case_count=stats.get("Case", 0),
            relationship_count=0  # Would need separate query for relationships
        )
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        return {
            "session_id": session_id,
            "entity_count": 0,
            "fact_count": 0,
            "document_count": 0,
            "legal_concept_count": 0,
            "case_count": 0,
            "relationship_count": 0,
            "error": "Neo4j unavailable",
            "message": str(e)
        }


# Clear session data
@router.delete("/sessions/{session_id}/clear")
async def clear_session_data(session_id: int):
    """Clear all data for a specific session"""
    try:
        if not neo4j_manager._initialized:
            await neo4j_manager.initialize()
        
        await neo4j_manager.clear_session_data(session_id)
        return {"message": f"All data cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Failed to clear session data: {e}")
        return {
            "message": f"Failed to clear session data for session {session_id}",
            "error": "Neo4j unavailable",
            "details": str(e)
        }


# Entity operations
@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity_data: EntityCreate,
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """Create a new entity"""
    try:
        entity = Entity(
            session_id=entity_data.session_id,
            name=entity_data.name,
            entity_type=entity_data.entity_type.value,
            description=entity_data.description,
            properties=str(entity_data.properties) if entity_data.properties else None
        )
        entity.save()
        
        return EntityResponse(
            id=entity.id,
            session_id=entity.session_id,
            name=entity.name,
            entity_type=entity.entity_type,
            description=entity.description,
            properties=entity_data.properties,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    except Exception as e:
        logger.error(f"Failed to create entity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entity: {str(e)}"
        )


@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    session_id: int = Query(..., description="Session ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of entities"),
    skip: int = Query(0, ge=0, description="Number of entities to skip"),
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """List entities for a session"""
    try:
        entities = Entity.nodes.filter(session_id=session_id).skip(skip).limit(limit)
        
        return [
            EntityResponse(
                id=entity.id,
                session_id=entity.session_id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
                properties=eval(entity.properties) if entity.properties else None,
                created_at=entity.created_at,
                updated_at=entity.updated_at
            )
            for entity in entities
        ]
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list entities: {str(e)}"
        )


# Fact operations
@router.post("/facts", response_model=FactResponse)
async def create_fact(
    fact_data: FactCreate,
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """Create a new fact"""
    try:
        fact = Fact(
            session_id=fact_data.session_id,
            content=fact_data.content,
            fact_type=fact_data.fact_type.value,
            confidence_score=fact_data.confidence_score,
            source=fact_data.source
        )
        fact.save()
        
        # Create relationships to entities if provided
        if fact_data.entity_ids:
            for entity_id in fact_data.entity_ids:
                try:
                    entity = Entity.nodes.get(id=entity_id, session_id=fact_data.session_id)
                    fact.entities.connect(entity)
                except Entity.DoesNotExist:
                    logger.warning(f"Entity {entity_id} not found for session {fact_data.session_id}")
        
        return FactResponse(
            id=fact.id,
            session_id=fact.session_id,
            content=fact.content,
            fact_type=fact.fact_type,
            confidence_score=fact.confidence_score,
            source=fact.source,
            entity_ids=fact_data.entity_ids,
            created_at=fact.created_at,
            updated_at=fact.updated_at
        )
    except Exception as e:
        logger.error(f"Failed to create fact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create fact: {str(e)}"
        )


@router.get("/facts", response_model=List[FactResponse])
async def list_facts(
    session_id: int = Query(..., description="Session ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of facts"),
    skip: int = Query(0, ge=0, description="Number of facts to skip"),
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """List facts for a session"""
    try:
        facts = Fact.nodes.filter(session_id=session_id).skip(skip).limit(limit)
        
        return [
            FactResponse(
                id=fact.id,
                session_id=fact.session_id,
                content=fact.content,
                fact_type=fact.fact_type,
                confidence_score=fact.confidence_score,
                source=fact.source,
                entity_ids=[],  # Would need to query relationships
                created_at=fact.created_at,
                updated_at=fact.updated_at
            )
            for fact in facts
        ]
    except Exception as e:
        logger.error(f"Failed to list facts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list facts: {str(e)}"
        )


# Document operations
@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    document_data: DocumentCreate,
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """Create a new document"""
    try:
        document = Document(
            session_id=document_data.session_id,
            title=document_data.title,
            document_type=document_data.document_type.value,
            content=document_data.content,
            file_path=document_data.file_path,
            file_size=document_data.file_size,
            upload_date=document_data.upload_date or document.created_at
        )
        document.save()
        
        return DocumentResponse(
            id=document.id,
            session_id=document.session_id,
            title=document.title,
            document_type=document.document_type,
            content=document.content,
            file_path=document.file_path,
            file_size=document.file_size,
            upload_date=document.upload_date,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


# Custom Cypher query execution
@router.post("/query", response_model=GraphQueryResponse)
async def execute_query(
    query_data: GraphQuery,
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """Execute a custom Cypher query with session isolation"""
    try:
        start_time = time.time()
        
        # Add session isolation to the query
        if "WHERE" in query_data.query.upper():
            # Add session_id filter to existing WHERE clause
            modified_query = query_data.query.replace(
                "WHERE", f"WHERE n.session_id = {query_data.session_id} AND"
            )
        else:
            # Add session_id filter
            modified_query = query_data.query.replace(
                "MATCH", f"MATCH"
            ).replace(
                "RETURN", f"WHERE n.session_id = {query_data.session_id} RETURN"
            )
        
        results = await manager.execute_query(
            modified_query, 
            query_data.parameters or {},
            query_data.session_id
        )
        
        execution_time = time.time() - start_time
        
        return GraphQueryResponse(
            results=results,
            execution_time=execution_time
        )
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute query: {str(e)}"
        )


# Graph search
@router.post("/search", response_model=GraphSearchResponse)
async def search_graph(
    search_data: GraphSearch,
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """Search across the knowledge graph"""
    try:
        # Build search query based on node types
        if search_data.node_types:
            node_types = "|".join(search_data.node_types)
            match_clause = f"MATCH (n:{node_types})"
        else:
            match_clause = "MATCH (n)"
        
        search_query = f"""
        {match_clause}
        WHERE n.session_id = $session_id
        AND (
            toLower(n.name) CONTAINS toLower($search_term) OR
            toLower(n.content) CONTAINS toLower($search_term) OR
            toLower(n.title) CONTAINS toLower($search_term) OR
            toLower(n.term) CONTAINS toLower($search_term) OR
            toLower(n.case_name) CONTAINS toLower($search_term)
        )
        RETURN n, labels(n) as node_type
        ORDER BY n.name
        LIMIT $limit
        """
        
        results = await manager.execute_query(
            search_query,
            {
                "session_id": search_data.session_id,
                "search_term": search_data.search_term,
                "limit": search_data.limit
            }
        )
        
        return GraphSearchResponse(
            results=results,
            total_count=len(results)
        )
    except Exception as e:
        logger.error(f"Failed to search graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search graph: {str(e)}"
        )


# Bulk operations
@router.post("/entities/bulk", response_model=List[EntityResponse])
async def create_entities_bulk(
    bulk_data: BulkEntityCreate,
    manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """Create multiple entities in bulk"""
    try:
        created_entities = []
        
        for entity_data in bulk_data.entities:
            entity = Entity(
                session_id=bulk_data.session_id,
                name=entity_data.name,
                entity_type=entity_data.entity_type.value,
                description=entity_data.description,
                properties=str(entity_data.properties) if entity_data.properties else None
            )
            entity.save()
            
            created_entities.append(EntityResponse(
                id=entity.id,
                session_id=entity.session_id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
                properties=entity_data.properties,
                created_at=entity.created_at,
                updated_at=entity.updated_at
            ))
        
        return created_entities
    except Exception as e:
        logger.error(f"Failed to create entities in bulk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entities in bulk: {str(e)}"
        )
