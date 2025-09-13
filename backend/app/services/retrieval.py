"""
Retrieval service for multilingual knowledge graph queries
"""
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from .language_detector import LanguageDetector

logger = logging.getLogger(__name__)

class MultilingualRetrievalService:
    """Service for retrieving information from multilingual knowledge graphs"""
    
    def __init__(self):
        self.driver = None
        self.language_detector = LanguageDetector()
        
    def initialize(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
            logger.info("Retrieval service connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Retrieval service connection closed")
    
    def retrieve_entities_and_relationships(
        self, 
        query: str, 
        session_id: int, 
        language: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve entities and relationships relevant to the query
        
        Args:
            query: User's question or query
            session_id: Session ID for isolation
            language: Optional language filter (arabic, english, mixed)
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing entities, relationships, and context
        """
        if not self.driver:
            raise RuntimeError("Retrieval service not initialized")
        
        # Detect language if not provided
        if not language:
            language = self.language_detector.detect_language(query)
        
        with self.driver.session(database="neo4j") as session:
            try:
                # Build Cypher query for multilingual retrieval
                cypher_query = self._build_retrieval_query(language, limit)
                
                # Execute query with parameters (convert session_id to string)
                result = session.run(cypher_query, {
                    "session_id": str(session_id),
                    "query_text": query.lower(),
                    "language": language,
                    "limit": limit
                })
                
                # Process results
                entities = []
                relationships = []
                context_chunks = []
                
                for record in result:
                    if record.get("entity"):
                        entities.append(self._format_entity(record["entity"]))
                    if record.get("relationship"):
                        relationships.append(self._format_relationship(record["relationship"]))
                    if record.get("context"):
                        context_chunks.append(record["context"])
                
                return {
                    "entities": entities,
                    "relationships": relationships,
                    "context_chunks": context_chunks,
                    "language": language,
                    "session_id": session_id,
                    "query": query
                }
                
            except Exception as e:
                logger.error(f"Error retrieving from knowledge graph: {e}")
                return {
                    "entities": [],
                    "relationships": [],
                    "context_chunks": [],
                    "language": language,
                    "session_id": session_id,
                    "query": query,
                    "error": str(e)
                }
    
    def _build_retrieval_query(self, language: str, limit: int) -> str:
        """Build Cypher query for retrieving relevant entities and relationships"""
        
        # Query that searches both standalone nodes and relationships
        # Handle both space and underscore variations and search in all properties
        query = """
        MATCH (n)
        WHERE n.session_id = $session_id
        AND (
            toLower(n.name) CONTAINS $query_text 
            OR toLower(replace(n.name, '_', ' ')) CONTAINS $query_text
            OR toLower(replace(n.name, ' ', '_')) CONTAINS $query_text
            OR toLower(coalesce(n.description, '')) CONTAINS $query_text
            OR toLower(coalesce(n.content, '')) CONTAINS $query_text
            OR toLower(coalesce(n.location, '')) CONTAINS $query_text
            OR toLower(coalesce(n.title, '')) CONTAINS $query_text
            OR toLower(coalesce(n.email, '')) CONTAINS $query_text
            OR ANY(prop IN keys(n) WHERE prop <> 'session_id' AND prop <> 'created_at' AND prop <> 'language' AND prop <> 'id' AND prop <> 'name' AND toLower(toString(n[prop])) CONTAINS $query_text)
        )
        """
        
        # Add language filter if specified
        if language and language != "mixed":
            query += f" AND n.language = $language"
        
        query += """
        RETURN n as entity, null as relationship, null as related_entity,
               CASE 
                   WHEN n.content IS NOT NULL THEN n.content
                   WHEN n.text IS NOT NULL THEN n.text
                   WHEN n.page_content IS NOT NULL THEN n.page_content
                   ELSE n.name + " (" + coalesce(n.language, 'unknown') + ")"
               END as context
        ORDER BY 
            CASE 
                WHEN toLower(n.name) CONTAINS $query_text THEN 1
                WHEN toLower(coalesce(n.description, '')) CONTAINS $query_text THEN 2
                WHEN toLower(coalesce(n.location, '')) CONTAINS $query_text THEN 3
                WHEN toLower(coalesce(n.title, '')) CONTAINS $query_text THEN 4
                ELSE 5
            END
        LIMIT $limit
        """
        
        return query
    
    def _format_entity(self, entity_node) -> Dict[str, Any]:
        """Format entity node for response"""
        return {
            "id": entity_node.get("id"),
            "name": entity_node.get("name"),
            "entity_type": entity_node.get("entity_type"),
            "description": entity_node.get("description"),
            "language": entity_node.get("language"),
            "properties": dict(entity_node)
        }
    
    def _format_relationship(self, relationship) -> Dict[str, Any]:
        """Format relationship for response"""
        return {
            "type": relationship.get("type"),
            "properties": dict(relationship),
            "language": relationship.get("language")
        }
    
    def get_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """Get statistics for a session's knowledge graph"""
        if not self.driver:
            raise RuntimeError("Retrieval service not initialized")
        
        with self.driver.session(database="neo4j") as session:
            try:
                # Count entities by type and language
                entity_stats_query = """
                MATCH (n)
                WHERE n.session_id = $session_id
                RETURN 
                    labels(n)[0] as node_type,
                    n.language as language,
                    count(n) as count
                ORDER BY count DESC
                """
                
                # Count relationships by type and language
                relationship_stats_query = """
                MATCH ()-[r]->()
                WHERE r.session_id = $session_id
                RETURN 
                    r.type as relationship_type,
                    r.language as language,
                    count(r) as count
                ORDER BY count DESC
                """
                
                entity_result = session.run(entity_stats_query, {"session_id": str(session_id)})
                relationship_result = session.run(relationship_stats_query, {"session_id": str(session_id)})
                
                entities_by_type = {}
                entities_by_language = {}
                relationships_by_type = {}
                relationships_by_language = {}
                
                for record in entity_result:
                    node_type = record["node_type"]
                    language = record["language"] or "unknown"
                    count = record["count"]
                    
                    entities_by_type[node_type] = entities_by_type.get(node_type, 0) + count
                    entities_by_language[language] = entities_by_language.get(language, 0) + count
                
                for record in relationship_result:
                    rel_type = record["relationship_type"]
                    language = record["language"] or "unknown"
                    count = record["count"]
                    
                    relationships_by_type[rel_type] = relationships_by_type.get(rel_type, 0) + count
                    relationships_by_language[language] = relationships_by_language.get(language, 0) + count
                
                return {
                    "session_id": session_id,
                    "entities_by_type": entities_by_type,
                    "entities_by_language": entities_by_language,
                    "relationships_by_type": relationships_by_type,
                    "relationships_by_language": relationships_by_language,
                    "total_entities": sum(entities_by_type.values()),
                    "total_relationships": sum(relationships_by_type.values())
                }
                
            except Exception as e:
                logger.error(f"Error getting session statistics: {e}")
                return {
                    "session_id": session_id,
                    "error": str(e)
                }
    
    def search_similar_entities(
        self, 
        entity_name: str, 
        session_id: int, 
        language: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for entities similar to the given name"""
        if not self.driver:
            raise RuntimeError("Retrieval service not initialized")
        
        with self.driver.session(database="neo4j") as session:
            try:
                query = """
                MATCH (n)
                WHERE n.session_id = $session_id
                AND toLower(n.name) CONTAINS toLower($entity_name)
                """
                
                if language and language != "mixed":
                    query += " AND n.language = $language"
                
                query += """
                RETURN n
                ORDER BY 
                    CASE 
                        WHEN toLower(n.name) = toLower($entity_name) THEN 1
                        WHEN toLower(n.name) STARTS WITH toLower($entity_name) THEN 2
                        ELSE 3
                    END
                LIMIT $limit
                """
                
                result = session.run(query, {
                    "session_id": str(session_id),
                    "entity_name": entity_name,
                    "language": language,
                    "limit": limit
                })
                
                entities = []
                for record in result:
                    entities.append(self._format_entity(record["n"]))
                
                return entities
                
            except Exception as e:
                logger.error(f"Error searching similar entities: {e}")
                return []


# Global instance
retrieval_service = MultilingualRetrievalService()