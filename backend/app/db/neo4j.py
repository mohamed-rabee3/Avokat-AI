import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
# Neomodel imports disabled for Neo4j Aura compatibility
# from neomodel import (
#     StructuredNode, StructuredRel, 
#     StringProperty, IntegerProperty, DateTimeProperty, 
#     RelationshipTo, RelationshipFrom, Relationship,
#     config, install_all_labels, db
# )
# from neomodel.exceptions import DoesNotExist

from ..core.config import settings

# Configure neomodel - DISABLED for Neo4j Aura compatibility
# Neo4j Aura uses neo4j+s:// protocol which neomodel doesn't support well
# We'll use the main Neo4j driver instead for all operations
# config.DATABASE_URL = f"bolt://{settings.neo4j_user}:{settings.neo4j_password}@{neo4j_host}"
# config.DATABASE_NAME = settings.neo4j_database

logger = logging.getLogger(__name__)


# Neomodel model classes disabled for Neo4j Aura compatibility
# We'll use raw Cypher queries with the main Neo4j driver instead

# Base classes for session isolation
# class SessionIsolatedNode(StructuredNode):
#     """Base class for all nodes that need session isolation"""
#     session_id = IntegerProperty(required=True, index=True)
#     created_at = DateTimeProperty(default=lambda: datetime.utcnow())
#     updated_at = DateTimeProperty(default=lambda: datetime.utcnow())
#
#
# class SessionIsolatedRel(StructuredRel):
#     """Base class for all relationships that need session isolation"""
#     session_id = IntegerProperty(required=True, index=True)
#     created_at = DateTimeProperty(default=lambda: datetime.utcnow())
#
#
# # Entity Models
# class Entity(SessionIsolatedNode):
#     """Represents entities in the knowledge graph"""
#     __label__ = "Entity"
#     
#     name = StringProperty(required=True, index=True)
#     entity_type = StringProperty(required=True, index=True)  # PERSON, ORGANIZATION, LOCATION, etc.
#     description = StringProperty()
#     properties = StringProperty()  # JSON string for additional properties
#     
#     # Relationships
#     facts = RelationshipFrom("Fact", "ABOUT", model=SessionIsolatedRel)
#     relationships = Relationship("Entity", "RELATED_TO", model=SessionIsolatedRel)
#
#
# class Fact(SessionIsolatedNode):
#     """Represents facts in the knowledge graph"""
#     __label__ = "Fact"
#     
#     content = StringProperty(required=True, index=True)
#     fact_type = StringProperty(required=True, index=True)  # LEGAL_FACT, EVIDENCE, etc.
#     confidence_score = IntegerProperty(default=100)  # 0-100
#     source = StringProperty()
#     
#     # Relationships
#     entities = RelationshipTo(Entity, "ABOUT", model=SessionIsolatedRel)
#     documents = RelationshipFrom("Document", "CONTAINS", model=SessionIsolatedRel)
#
#
# class Document(SessionIsolatedNode):
#     """Represents documents in the knowledge graph"""
#     __label__ = "Document"
#     
#     title = StringProperty(required=True, index=True)
#     document_type = StringProperty(required=True, index=True)  # CONTRACT, CASE_FILE, etc.
#     content = StringProperty()
#     file_path = StringProperty()
#     file_size = IntegerProperty()
#     upload_date = DateTimeProperty(default=lambda: datetime.utcnow())
#     
#     # Relationships
#     facts = RelationshipTo(Fact, "CONTAINS", model=SessionIsolatedRel)
#     entities = RelationshipTo(Entity, "MENTIONS", model=SessionIsolatedRel)
#
#
# class LegalConcept(SessionIsolatedNode):
#     """Represents legal concepts and terms"""
#     __label__ = "LegalConcept"
#     
#     term = StringProperty(required=True, unique_index=True)
#     definition = StringProperty()
#     category = StringProperty(index=True)  # STATUTE, REGULATION, CASE_LAW, etc.
#     jurisdiction = StringProperty(index=True)
#     
#     # Relationships
#     related_concepts = Relationship("LegalConcept", "RELATED_TO", model=SessionIsolatedRel)
#     applies_to = RelationshipTo(Entity, "APPLIES_TO", model=SessionIsolatedRel)
#
#
# class Case(SessionIsolatedNode):
#     """Represents legal cases"""
#     __label__ = "Case"
#     
#     case_number = StringProperty(required=True, unique_index=True)
#     case_name = StringProperty(required=True, index=True)
#     court = StringProperty(index=True)
#     jurisdiction = StringProperty(index=True)
#     case_date = DateTimeProperty()
#     status = StringProperty(index=True)  # OPEN, CLOSED, PENDING, etc.
#     
#     # Relationships
#     parties = RelationshipTo(Entity, "INVOLVES", model=SessionIsolatedRel)
#     documents = RelationshipTo(Document, "CONTAINS", model=SessionIsolatedRel)
#     legal_concepts = RelationshipTo(LegalConcept, "INVOLVES", model=SessionIsolatedRel)


# Neo4j Driver Management
class Neo4jManager:
    """Manages Neo4j driver and database operations"""
    
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the Neo4j driver and create indexes"""
        if self._initialized:
            return
            
        try:
            # Create async driver
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            
            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info("Neo4j connection established successfully")
            
            # Create indexes and constraints
            await self._create_indexes_and_constraints()
            
            self._initialized = True
            logger.info("Neo4j initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
            raise
    
    async def _create_indexes_and_constraints(self):
        """Create necessary indexes and constraints for session isolation"""
        async with self.driver.session(database=settings.neo4j_database) as session:
            # Create indexes for session_id on all node types
            indexes = [
                "CREATE INDEX session_entity_idx IF NOT EXISTS FOR (n:Entity) ON (n.session_id)",
                "CREATE INDEX session_fact_idx IF NOT EXISTS FOR (n:Fact) ON (n.session_id)",
                "CREATE INDEX session_document_idx IF NOT EXISTS FOR (n:Document) ON (n.session_id)",
                "CREATE INDEX session_legalconcept_idx IF NOT EXISTS FOR (n:LegalConcept) ON (n.session_id)",
                "CREATE INDEX session_case_idx IF NOT EXISTS FOR (n:Case) ON (n.session_id)",
                
                # Create indexes for session_id on relationships
                "CREATE INDEX session_rel_idx IF NOT EXISTS FOR ()-[r:ABOUT]-() ON (r.session_id)",
                "CREATE INDEX session_rel2_idx IF NOT EXISTS FOR ()-[r:CONTAINS]-() ON (r.session_id)",
                "CREATE INDEX session_rel3_idx IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r.session_id)",
                "CREATE INDEX session_rel4_idx IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.session_id)",
                "CREATE INDEX session_rel5_idx IF NOT EXISTS FOR ()-[r:APPLIES_TO]-() ON (r.session_id)",
                "CREATE INDEX session_rel6_idx IF NOT EXISTS FOR ()-[r:INVOLVES]-() ON (r.session_id)",
                
                # Create additional useful indexes
                "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)",
                "CREATE INDEX fact_type_idx IF NOT EXISTS FOR (n:Fact) ON (n.fact_type)",
                "CREATE INDEX document_type_idx IF NOT EXISTS FOR (n:Document) ON (n.document_type)",
                "CREATE INDEX legal_concept_category_idx IF NOT EXISTS FOR (n:LegalConcept) ON (n.category)",
                "CREATE INDEX case_status_idx IF NOT EXISTS FOR (n:Case) ON (n.status)",
                
                # Multilingual support indexes
                "CREATE INDEX entity_language_idx IF NOT EXISTS FOR (n:Entity) ON (n.language)",
                "CREATE INDEX fact_language_idx IF NOT EXISTS FOR (n:Fact) ON (n.language)",
                "CREATE INDEX document_language_idx IF NOT EXISTS FOR (n:Document) ON (n.language)",
                "CREATE INDEX legalconcept_language_idx IF NOT EXISTS FOR (n:LegalConcept) ON (n.language)",
                "CREATE INDEX case_language_idx IF NOT EXISTS FOR (n:Case) ON (n.language)",
            ]
            
            for index_query in indexes:
                try:
                    await session.run(index_query)
                    logger.info(f"Created index: {index_query}")
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
    
    async def close(self):
        """Close the Neo4j driver"""
        if self.driver:
            await self.driver.close()
            self.driver = None
            self._initialized = False
            logger.info("Neo4j driver closed")
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None, session_id: int = None):
        """Execute a Cypher query with session isolation"""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        if parameters is None:
            parameters = {}
        
        # Add session_id to all queries for isolation
        if session_id is not None:
            parameters["session_id"] = session_id
        
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, parameters)
            return await result.data()
    
    async def get_session_stats(self, session_id: int) -> Dict[str, int]:
        """Get statistics for a specific session"""
        stats_query = """
        MATCH (n)
        WHERE n.session_id = $session_id
        RETURN 
            labels(n)[0] as label,
            count(n) as count
        ORDER BY label
        """
        
        results = await self.execute_query(stats_query, {"session_id": str(session_id)})
        
        stats = {}
        for result in results:
            stats[result["label"]] = result["count"]
        
        return stats
    
    async def clear_session_data(self, session_id: int):
        """Clear all data for a specific session"""
        delete_query = """
        MATCH (n)
        WHERE n.session_id = $session_id
        DETACH DELETE n
        """
        
        await self.execute_query(delete_query, {"session_id": str(session_id)})
        logger.info(f"Cleared all data for session {session_id}")


# Global Neo4j manager instance
neo4j_manager = Neo4jManager()


# Database dependency for FastAPI
async def get_neo4j_manager() -> Neo4jManager:
    """Dependency to get Neo4j manager instance"""
    if not neo4j_manager._initialized:
        await neo4j_manager.initialize()
    return neo4j_manager


# Utility functions for session isolation
def add_session_filter(query: str, session_id: int) -> str:
    """Add session_id filter to a Cypher query"""
    if "WHERE" in query.upper():
        # Add to existing WHERE clause
        query = query.replace("WHERE", f"WHERE n.session_id = {session_id} AND")
    else:
        # Add new WHERE clause
        query = query.replace("MATCH", f"MATCH")
        query = query.replace("RETURN", f"WHERE n.session_id = {session_id} RETURN")
    
    return query


# Initialize neomodel labels and constraints
async def init_neomodel():
    """Initialize neomodel labels and constraints - DISABLED for Neo4j Aura"""
    # Neomodel is disabled for Neo4j Aura compatibility
    # The main Neo4j driver handles all operations and index creation
    logger.info("Neomodel initialization skipped - using main Neo4j driver for Neo4j Aura compatibility")