import asyncio
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the embedding service
import sys
sys.path.append('backend')
from app.services.embedding_service import embedding_service

load_dotenv()

async def add_embeddings_to_existing_chunks():
    """Add embeddings to existing DocumentChunk nodes that don't have them"""
    
    # Initialize embedding service
    embedding_service.initialize()
    logger.info(f"Embedding service initialized with {embedding_service.get_embedding_dimension()} dimensions")
    
    driver = AsyncGraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    try:
        async with driver.session(database='neo4j') as session:
            # Find DocumentChunk nodes without embeddings
            result = await session.run('MATCH (n:DocumentChunk) WHERE n.embedding IS NULL RETURN n LIMIT 10')
            
            count = 0
            async for record in result:
                node = record["n"]
                chunk_id = node.get("chunk_index")
                session_id = node.get("session_id")
                content = node.get("content", "")
                
                if not content:
                    logger.warning(f"Skipping chunk {chunk_id} in session {session_id} - no content")
                    continue
                
                try:
                    # Generate embedding
                    logger.info(f"Generating embedding for chunk {chunk_id} in session {session_id}")
                    embedding = embedding_service.generate_embedding(content)
                    embedding_str = embedding_service.embedding_to_string(embedding)
                    
                    # Update the node with embedding
                    update_query = """
                    MATCH (n:DocumentChunk)
                    WHERE n.chunk_index = $chunk_index AND n.session_id = $session_id
                    SET n.embedding = $embedding,
                        n.embedding_dimension = $embedding_dimension
                    RETURN n
                    """
                    
                    await session.run(update_query, {
                        "chunk_index": chunk_id,
                        "session_id": session_id,
                        "embedding": embedding_str,
                        "embedding_dimension": embedding_service.get_embedding_dimension()
                    })
                    
                    count += 1
                    logger.info(f"Added embedding to chunk {chunk_id} in session {session_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to add embedding to chunk {chunk_id}: {e}")
            
            logger.info(f"Successfully added embeddings to {count} DocumentChunk nodes")
            
            # Verify embeddings were added
            result = await session.run('MATCH (n:DocumentChunk) WHERE n.embedding IS NOT NULL RETURN count(n) as count')
            record = await result.single()
            logger.info(f"Total DocumentChunk nodes with embeddings: {record['count']}")
                
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(add_embeddings_to_existing_chunks())
