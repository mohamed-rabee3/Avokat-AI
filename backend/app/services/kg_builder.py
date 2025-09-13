"""
Neo4j Knowledge Graph Builder Service
Uses LangChain and Neo4j LLM Graph Builder to create knowledge graphs from text
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from langchain_community.graphs.graph_document import (
    Node as BaseNode,
    Relationship as BaseRelationship,
    GraphDocument,
)
from langchain.schema import Document
from pydantic import Field, BaseModel
from langchain_community.graphs import Neo4jGraph
from langchain.chains import create_extraction_chain
from langchain.prompts import ChatPromptTemplate
import google.generativeai as genai

from ..core.config import settings
from .language_detector import language_detector

logger = logging.getLogger(__name__)


class Property(BaseModel):
    """A single property consisting of key and value"""
    key: str = Field(..., description="key")
    value: str = Field(..., description="value")


class Node(BaseNode):
    properties: Optional[List[Property]] = Field(
        None, description="List of node properties")


class Relationship(BaseRelationship):
    properties: Optional[List[Property]] = Field(
        None, description="List of relationship properties"
    )


class KnowledgeGraph(BaseModel):
    """Generate a knowledge graph with entities and relationships."""
    nodes: List[Node] = Field(
        ..., description="List of nodes in the knowledge graph")
    rels: List[Relationship] = Field(
        ..., description="List of relationships in the knowledge graph"
    )


class Neo4jKnowledgeGraphBuilder:
    """Neo4j Knowledge Graph Builder using LangChain and Gemini"""
    
    def __init__(self):
        self.llm = None
        self.graph = None
        self.extraction_chain = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the knowledge graph builder"""
        if self._initialized:
            return
            
        try:
            # Initialize Gemini LLM
            genai.configure(api_key=settings.gemini_api_key)
            self.llm = genai.GenerativeModel("gemini-1.5-flash")
            
            # Initialize Neo4j graph connection
            self.graph = Neo4jGraph(
                url=settings.neo4j_uri,
                username=settings.neo4j_user,
                password=settings.neo4j_password,
                database=settings.neo4j_database
            )
            
            # Create extraction chain
            self.extraction_chain = self._create_extraction_chain()
            
            self._initialized = True
            logger.info("Neo4j Knowledge Graph Builder initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j Knowledge Graph Builder: {e}")
            raise
    
    def _create_extraction_chain(self):
        """Create the extraction chain for knowledge graph building"""
        
        # Define the prompt for entity and relationship extraction
        self.prompt_template = """
        You are a knowledge graph extraction expert. Extract entities and relationships from the given text.
        
        Focus on extracting:
        - Legal entities (persons, organizations, contracts, cases, laws, regulations)
        - Legal relationships (agreements, obligations, rights, responsibilities)
        - Key legal concepts and terms
        - Dates, amounts, and other important details
        
        For each entity, provide:
        - A clear, unique identifier
        - Entity type (PERSON, ORGANIZATION, CONTRACT, CASE, LAW, etc.)
        - Relevant properties (name, date, amount, description, etc.)
        
        For each relationship, provide:
        - Source and target entities
        - Relationship type (AGREES_TO, OBLIGATED_BY, INVOLVES, etc.)
        - Relevant properties
        
        Be precise and avoid duplicates.
        
        Return the result in JSON format matching this schema:
        {{
            "nodes": [
                {{
                    "id": "entity_id",
                    "type": "ENTITY_TYPE",
                    "properties": [
                        {{"key": "property_name", "value": "property_value"}}
                    ]
                }}
            ],
            "rels": [
                {{
                    "source": {{"id": "source_id", "type": "SOURCE_TYPE"}},
                    "target": {{"id": "target_id", "type": "TARGET_TYPE"}},
                    "type": "RELATIONSHIP_TYPE",
                    "properties": [
                        {{"key": "property_name", "value": "property_value"}}
                    ]
                }}
            ]
        }}
        
        Text to extract from: {input}
        """
        
        return None  # We'll use direct LLM calls instead of chains
    
    def _format_property_key(self, s: str) -> str:
        """Format property key to camelCase"""
        words = s.split()
        if not words:
            return s
        first_word = words[0].lower()
        capitalized_words = [word.capitalize() for word in words[1:]]
        return "".join([first_word] + capitalized_words)
    
    def _props_to_dict(self, props) -> dict:
        """Convert properties to a dictionary"""
        properties = {}
        if not props:
            return properties
        for p in props:
            properties[self._format_property_key(p.key)] = p.value
        return properties
    
    def _map_to_base_node(self, node: Node) -> BaseNode:
        """Map the KnowledgeGraph Node to the base Node"""
        properties = self._props_to_dict(node.properties) if node.properties else {}
        # Add name property for better Cypher statement generation
        properties["name"] = node.id.title()
        return BaseNode(
            id=node.id.title(), 
            type=node.type.capitalize(), 
            properties=properties
        )
    
    def _map_to_base_relationship(self, rel: Relationship) -> BaseRelationship:
        """Map the KnowledgeGraph Relationship to the base Relationship"""
        source = self._map_to_base_node(rel.source)
        target = self._map_to_base_node(rel.target)
        properties = self._props_to_dict(rel.properties) if rel.properties else {}
        return BaseRelationship(
            source=source, 
            target=target, 
            type=rel.type, 
            properties=properties
        )
    
    async def extract_and_store_graph(
        self, 
        document: Document, 
        session_id: int,
        nodes: Optional[List[str]] = None,
        rels: Optional[List[str]] = None
    ) -> GraphDocument:
        """Extract and store graph data from a document"""
        
        if not self._initialized:
            await self.initialize()
        
        try:
            # Detect language and enhance prompt accordingly
            detected_language = language_detector.detect_language(document.page_content)
            enhanced_prompt = language_detector.get_language_specific_prompt(
                detected_language, 
                self.prompt_template
            )
            
            # Extract graph data using Gemini directly
            prompt = enhanced_prompt.format(input=document.page_content)
            
            logger.info(f"Processing document in {detected_language} language")
            
            # Generate response from Gemini
            response = self.llm.generate_content(prompt)
            
            # Clean and parse the JSON response
            import json
            import re
            
            # Extract JSON from the response (in case there's extra text)
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                json_text = response_text
            
            # Parse the JSON
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response_text}")
                logger.error(f"Extracted JSON: {json_text}")
                raise
            
            # Parse the extracted data
            kg_data = KnowledgeGraph(**data)
            
            # Construct a graph document
            graph_document = GraphDocument(
                nodes=[self._map_to_base_node(node) for node in kg_data.nodes],
                relationships=[self._map_to_base_relationship(rel) for rel in kg_data.rels],
                source=document
            )
            
            # Add session_id and language to all nodes and relationships
            for node in graph_document.nodes:
                node.properties = node.properties or {}
                node.properties["session_id"] = str(session_id)
                node.properties["language"] = detected_language
                node.properties["created_at"] = datetime.now(timezone.utc).isoformat()
            
            for rel in graph_document.relationships:
                rel.properties = rel.properties or {}
                rel.properties["session_id"] = str(session_id)
                rel.properties["language"] = detected_language
                rel.properties["created_at"] = datetime.now(timezone.utc).isoformat()
            
            # Store information into Neo4j graph
            self.graph.add_graph_documents([graph_document])
            
            logger.info(f"Successfully extracted and stored graph with {len(graph_document.nodes)} nodes and {len(graph_document.relationships)} relationships")
            
            return graph_document
            
        except Exception as e:
            logger.error(f"Failed to extract and store graph: {e}")
            raise
    
    async def get_session_stats(self, session_id: int) -> Dict[str, int]:
        """Get statistics for a specific session"""
        try:
            query = """
            MATCH (n)
            WHERE n.session_id = $session_id
            RETURN 
                labels(n)[0] as label,
                count(n) as count
            ORDER BY label
            """
            
            result = self.graph.query(query, {"session_id": str(session_id)})
            
            stats = {}
            for record in result:
                stats[record["label"]] = record["count"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
    
    async def store_document_chunk(self, document: Document, session_id: int, chunk_index: int):
        """Store document chunk for retrieval with embeddings"""
        try:
            # Detect language
            detected_language = language_detector.detect_language(document.page_content)
            
            # Generate embedding for the document content
            from .embedding_service import embedding_service
            embedding = embedding_service.generate_embedding(document.page_content)
            embedding_str = embedding_service.embedding_to_string(embedding)
            
            # Create document chunk node with embedding
            chunk_query = """
            CREATE (c:DocumentChunk {
                session_id: $session_id,
                chunk_index: $chunk_index,
                content: $content,
                language: $language,
                embedding: $embedding,
                embedding_dimension: $embedding_dimension,
                created_at: datetime(),
                metadata: $metadata
            })
            """
            
            metadata = {}
            if hasattr(document, 'metadata') and document.metadata:
                metadata = document.metadata
            
            # Convert metadata to JSON string (Neo4j doesn't support complex objects)
            import json
            metadata_json = json.dumps(metadata) if metadata else "{}"
            
            # Execute the query
            result = self.graph.query(chunk_query, {
                "session_id": str(session_id),
                "chunk_index": chunk_index,
                "content": document.page_content,
                "language": detected_language,
                "embedding": embedding_str,
                "embedding_dimension": embedding_service.get_embedding_dimension(),
                "metadata": metadata_json
            })
            
            logger.info(f"Stored document chunk {chunk_index} for session {session_id} with embedding (content length: {len(document.page_content)})")
            
        except Exception as e:
            logger.error(f"Failed to store document chunk: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def clear_session_data(self, session_id: int):
        """Clear all data for a specific session"""
        try:
            query = """
            MATCH (n)
            WHERE n.session_id = $session_id
            DETACH DELETE n
            """
            
            self.graph.query(query, {"session_id": str(session_id)})
            logger.info(f"Cleared all data for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear session data: {e}")
            raise


# Global instance
kg_builder = Neo4jKnowledgeGraphBuilder()
