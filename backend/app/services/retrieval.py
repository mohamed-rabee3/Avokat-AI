"""
Enhanced Retrieval service for multilingual knowledge graph queries
Implements best practices for Neo4j graph traversal and multilingual search
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from .language_detector import LanguageDetector
import re

logger = logging.getLogger(__name__)

class MultilingualRetrievalService:
    """Enhanced service for retrieving information from multilingual knowledge graphs"""
    
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
        Enhanced retrieval using hybrid approach: semantic search + graph traversal
        
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
        
        logger.info(f"Enhanced retrieval for query: '{query}' in session {session_id} (language: {language})")
        
        with self.driver.session(database="neo4j") as session:
            try:
                # Step 1: Semantic search for document chunks
                context_chunks = self._semantic_search_chunks(session, query, session_id, limit)
                
                # Step 2: Extract meaningful search terms
                search_terms = self._extract_meaningful_terms(query, language)
                
                # Step 3: Graph-based entity and relationship retrieval
                entities, relationships = self._graph_traversal_search(
                    session, search_terms, session_id, language, limit
                )
                
                # Step 4: Expand context by following relationships
                expanded_context = self._expand_context_by_relationships(
                    session, entities, relationships, session_id, limit
                )
                
                # Combine all results
                result = {
                    "entities": entities,
                    "relationships": relationships,
                    "context_chunks": context_chunks,
                    "expanded_context": expanded_context,
                    "language": language,
                    "session_id": session_id,
                    "query": query,
                    "search_terms": search_terms
                }
                
                logger.info(f"Enhanced retrieval results: {len(context_chunks)} chunks, {len(entities)} entities, {len(relationships)} relationships, {len(expanded_context)} expanded items")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in enhanced retrieval: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {
                    "entities": [],
                    "relationships": [],
                    "context_chunks": [],
                    "expanded_context": [],
                    "language": language,
                    "session_id": session_id,
                    "query": query,
                    "error": str(e)
                }
    
    def _semantic_search_chunks(self, session, query: str, session_id: int, limit: int) -> List[str]:
        """Always return ALL document chunks for comprehensive context"""
        try:
            # Always get ALL DocumentChunk nodes for this session
            chunks_query = """
            MATCH (n:DocumentChunk)
            WHERE n.session_id = $session_id
            RETURN n.content, n.chunk_index
            ORDER BY n.chunk_index
            """
            
            chunks_result = session.run(chunks_query, {"session_id": str(session_id)})
            chunks_records = list(chunks_result)
            
            if not chunks_records:
                logger.info(f"No DocumentChunk nodes found for session {session_id}")
                return []
            
            # Always return ALL chunks for comprehensive context
            context_chunks = [record['n.content'] for record in chunks_records]
            logger.info(f"Retrieved ALL {len(context_chunks)} document chunks for comprehensive coverage")
            
            return context_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}")
            return []
    
    def _extract_meaningful_terms(self, query: str, language: str) -> List[str]:
        """Extract meaningful search terms with improved multilingual support"""
        # Clean the query
        cleaned_query = query.strip().lower()
        
        # Arabic compound word mapping
        arabic_compound_mapping = {
            'فالملف': 'ملف',
            'فالمستند': 'مستند', 
            'فالمحتوى': 'محتوى',
            'فالمعلومات': 'معلومات',
            'فالتفاصيل': 'تفاصيل',
            'فالعقد': 'عقد',
            'فالعقار': 'عقار',
            'فالشقة': 'شقة',
            'فالمنزل': 'منزل',
            'فالإيجار': 'إيجار',
            'فالدفع': 'دفع',
            'فالمبلغ': 'مبلغ',
            'فالمدة': 'مدة',
            'فالتأمين': 'تأمين',
            'فالغرامة': 'غرامة',
            'فالبند': 'بند',
            'فالمادة': 'مادة',
            'فالقانون': 'قانون',
            'فالمحكمة': 'محكمة',
            'فالاختصاص': 'اختصاص',
            'فالطرف': 'طرف',
            'فالأطراف': 'أطراف',
            'فالمؤجر': 'مؤجر',
            'فالمستأجر': 'مستأجر'
        }
        
        # Replace compound words first
        for compound, simple in arabic_compound_mapping.items():
            cleaned_query = cleaned_query.replace(compound, simple)
        
        # Remove common question words and punctuation
        question_words = {
            'english': ['what', 'is', 'are', 'in', 'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'by', 'how', 'when', 'where', 'why', 'who', 'which', 'tell', 'me', 'about', 'can', 'you', 'please'],
            'arabic': ['ماذا', 'ما', 'هو', 'هي', 'في', 'من', 'إلى', 'على', 'مع', 'ب', 'ل', 'كيف', 'متى', 'أين', 'لماذا', 'من', 'أي', 'أخبر', 'ني', 'عن', 'هل', 'يمكن', 'أن', 'تخبرني', 'يوجد', 'موجود', 'يحتوي', 'يضم']
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', cleaned_query)
        
        # Filter out question words
        meaningful_words = []
        for word in words:
            if word not in question_words['english'] and word not in question_words['arabic']:
                meaningful_words.append(word)
        
        # Special handling for general file/document queries
        if not meaningful_words or len(meaningful_words) == 0:
            # Check if this is a general question about file/document content
            general_indicators = ['ملف', 'مستند', 'محتوى', 'معلومات', 'تفاصيل', 'عقد', 'document', 'file', 'content', 'information', 'details']
            if any(indicator in cleaned_query for indicator in general_indicators):
                meaningful_words = ['عقد']  # Default to contract since that's what we have
                logger.info(f"General file/document query detected, using default search term: 'عقد'")
            else:
                meaningful_words = [cleaned_query]
        
        # Special handling for "what is in the file" type queries
        general_content_queries = ['ماذا يوجد', 'ماذا يحتوي', 'ماذا يضم', 'ما هو المحتوى', 'ما هي المعلومات', 'ماذ يحتوي', 'ماذا في', 'ماذا عن', 'what is in', 'what contains', 'what does it contain', 'what is about']
        if any(query_type in cleaned_query for query_type in general_content_queries):
            meaningful_words = ['عقد', 'مستند', 'محتوى']  # Use multiple terms to catch more content
            logger.info(f"General content query detected, using multiple search terms: {meaningful_words}")
        
        # Special handling for descriptive queries
        descriptive_queries = ['اوصف', 'اشرح', 'وضح', 'تفاصيل', 'describe', 'explain', 'details', 'detail']
        if any(query_type in cleaned_query for query_type in descriptive_queries):
            meaningful_words = ['عقد', 'مستند', 'محتوى', 'تفاصيل']  # Use terms that will match document content
            logger.info(f"Descriptive query detected, using multiple search terms: {meaningful_words}")
        
        logger.info(f"Extracted meaningful terms: {meaningful_words}")
        return meaningful_words
    
    def _graph_traversal_search(self, session, search_terms: List[str], session_id: int, language: str, limit: int) -> Tuple[List[Dict], List[Dict]]:
        """Perform graph traversal search for entities and relationships"""
        try:
            # Build comprehensive Cypher query for graph traversal
            query_parts = []
            params = {"session_id": str(session_id), "limit": limit}
            
            # Create search conditions for each term
            for i, term in enumerate(search_terms):
                param_name = f"term_{i}"
                params[param_name] = term.lower()
                query_parts.append(f"""
                    (n.name IS NOT NULL AND toLower(n.name) CONTAINS ${param_name})
                    OR (n.content IS NOT NULL AND toLower(n.content) CONTAINS ${param_name})
                    OR (n.description IS NOT NULL AND toLower(n.description) CONTAINS ${param_name})
                    OR ANY(prop IN keys(n) WHERE 
                        prop <> 'session_id' AND 
                        prop <> 'created_at' AND 
                        prop <> 'language' AND 
                        prop <> 'id' AND 
                        prop <> 'embedding' AND
                        prop <> 'embedding_dimension' AND
                        prop <> 'metadata' AND
                        prop <> 'chunk_index' AND
                        toLower(toString(n[prop])) CONTAINS ${param_name}
                    )
                """)
            
            # Combine search conditions
            search_condition = " OR ".join(query_parts) if query_parts else "true"
            
            # Enhanced graph traversal query
            cypher_query = f"""
            MATCH (n)
            WHERE n.session_id = $session_id
            AND ({search_condition})
            WITH n, 
                 CASE 
                     WHEN n.content IS NOT NULL THEN 1
                     WHEN n.name IS NOT NULL THEN 2
                     WHEN n.description IS NOT NULL THEN 3
                     ELSE 4
                 END as relevance_score
            ORDER BY relevance_score, n.created_at DESC
            LIMIT $limit
            RETURN n as entity, null as relationship, relevance_score
            """
            
            # Add language filter if specified
            if language and language != "mixed":
                cypher_query = cypher_query.replace(
                    "WHERE n.session_id = $session_id",
                    f"WHERE n.session_id = $session_id AND n.language = '{language}'"
                )
                
            # Initialize variables
            entities = []
            relationships = []
            
            # Execute the query
            result = session.run(cypher_query, params)
            
            for record in result:
                if record.get("entity"):
                    entity = self._format_entity(record["entity"])
                    entity["relevance_score"] = record.get("relevance_score", 0)
                    entities.append(entity)
            
            logger.info(f"Graph traversal found {len(entities)} entities")
            return entities, relationships
            
        except Exception as e:
            logger.error(f"Error in graph traversal search: {e}")
            return [], []
    
    def _expand_context_by_relationships(self, session, entities: List[Dict], relationships: List[Dict], session_id: int, limit: int) -> List[Dict]:
        """Expand context by following relationships from found entities"""
        try:
            if not entities:
                return []
            
            # Get entity IDs from found entities
            entity_ids = [entity.get("id") for entity in entities if entity.get("id")]
            
            if not entity_ids:
                return []
            
            # Query for related entities and relationships
            expansion_query = """
            MATCH (n)-[r]-(related)
            WHERE n.session_id = $session_id 
            AND (n.id IN $entity_ids OR related.id IN $entity_ids)
            AND related.session_id = $session_id
            RETURN DISTINCT related as expanded_entity, r as expanded_relationship, 
                   labels(n)[0] as source_type, labels(related)[0] as target_type,
                   type(r) as relationship_type
            LIMIT $limit
            """
            
            result = session.run(expansion_query, {
                "session_id": str(session_id),
                "entity_ids": entity_ids,
                "limit": limit
            })
            
            expanded_context = []
            for record in result:
                if record.get("expanded_entity"):
                    expanded_item = {
                        "type": "expanded_entity",
                        "entity": self._format_entity(record["expanded_entity"]),
                        "source_type": record.get("source_type"),
                        "target_type": record.get("target_type"),
                        "relationship_type": record.get("relationship_type")
                    }
                    expanded_context.append(expanded_item)
                
                if record.get("expanded_relationship"):
                    expanded_item = {
                        "type": "expanded_relationship",
                        "relationship": self._format_relationship(record["expanded_relationship"]),
                        "source_type": record.get("source_type"),
                        "target_type": record.get("target_type"),
                        "relationship_type": record.get("relationship_type")
                    }
                    expanded_context.append(expanded_item)
            
            logger.info(f"Expanded context with {len(expanded_context)} related items")
            return expanded_context
            
        except Exception as e:
            logger.error(f"Error expanding context: {e}")
            return []
    
    def _build_retrieval_query(self, language: str, limit: int) -> str:
        """Build Cypher query for retrieving relevant entities and relationships"""
        
        # Enhanced query that searches in all relevant fields and handles different node types
        query = """
        MATCH (n)
        WHERE n.session_id = $session_id
        AND (
            // Search in name field (for entities)
            (n.name IS NOT NULL AND toLower(n.name) CONTAINS $query_text)
            OR (n.name IS NOT NULL AND toLower(replace(n.name, '_', ' ')) CONTAINS $query_text)
            OR (n.name IS NOT NULL AND toLower(replace(n.name, ' ', '_')) CONTAINS $query_text)
            // Search in content field (for DocumentChunk nodes)
            OR (n.content IS NOT NULL AND toLower(n.content) CONTAINS $query_text)
            // Search in description field
            OR (n.description IS NOT NULL AND toLower(n.description) CONTAINS $query_text)
            // Search in other common fields
            OR (n.location IS NOT NULL AND toLower(n.location) CONTAINS $query_text)
            OR (n.title IS NOT NULL AND toLower(n.title) CONTAINS $query_text)
            OR (n.email IS NOT NULL AND toLower(n.email) CONTAINS $query_text)
            // Search in all other properties (for extracted entities with Arabic properties)
            OR ANY(prop IN keys(n) WHERE 
                prop <> 'session_id' AND 
                prop <> 'created_at' AND 
                prop <> 'language' AND 
                prop <> 'id' AND 
                prop <> 'name' AND 
                prop <> 'content' AND
                prop <> 'description' AND
                prop <> 'location' AND
                prop <> 'title' AND
                prop <> 'email' AND
                toLower(toString(n[prop])) CONTAINS $query_text
            )
        )
        """
        
        # Add language filter if specified (but allow mixed language to search all)
        if language and language != "mixed":
            query += f" AND n.language = $language"
        
        query += """
        RETURN n as entity, null as relationship, null as related_entity,
               CASE 
                   WHEN n.content IS NOT NULL THEN n.content
                   WHEN n.name IS NOT NULL THEN n.name + " (" + coalesce(n.language, 'unknown') + ")"
                   ELSE labels(n)[0] + " (" + coalesce(n.language, 'unknown') + ")"
               END as context
        ORDER BY 
            CASE 
                WHEN n.content IS NOT NULL AND toLower(n.content) CONTAINS $query_text THEN 1
                WHEN n.name IS NOT NULL AND toLower(n.name) CONTAINS $query_text THEN 2
                WHEN n.description IS NOT NULL AND toLower(n.description) CONTAINS $query_text THEN 3
                WHEN n.location IS NOT NULL AND toLower(n.location) CONTAINS $query_text THEN 4
                WHEN n.title IS NOT NULL AND toLower(n.title) CONTAINS $query_text THEN 5
                ELSE 6
            END
        LIMIT $limit
        """
        
        return query
    
    
    def _format_entity(self, entity_node) -> Dict[str, Any]:
        """Format entity node for response"""
        # Get the primary label as entity_type
        labels = list(entity_node.labels)
        entity_type = labels[0] if labels else "Unknown"
        
        # For DocumentChunk nodes, use content as name if no name exists
        name = entity_node.get("name")
        if not name and entity_type == "DocumentChunk":
            content = entity_node.get("content", "")
            # Use first line or first 50 characters as name
            name = content.split('\n')[0][:50] if content else "Document Chunk"
        
        return {
            "id": entity_node.get("id"),
            "name": name,
            "entity_type": entity_type,
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