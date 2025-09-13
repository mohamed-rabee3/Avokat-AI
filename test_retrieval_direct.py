import asyncio
import sys
sys.path.append('backend')

from app.services.retrieval import retrieval_service
from app.core.config import settings

async def test_retrieval_direct():
    """Test the retrieval service directly"""
    
    # Initialize embedding service first
    from app.services.embedding_service import embedding_service
    embedding_service.initialize()
    print(f"Embedding service initialized with {embedding_service.get_embedding_dimension()} dimensions")
    
    # Initialize retrieval service
    retrieval_service.initialize(
        uri=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
        database=settings.neo4j_database
    )
    
    try:
        # Test retrieval
        result = retrieval_service.retrieve_entities_and_relationships(
            query="tell me about the contract",
            session_id=1,
            language="english",
            limit=5
        )
        
        print("Retrieval result:")
        print(f"  Entities: {len(result['entities'])}")
        print(f"  Relationships: {len(result['relationships'])}")
        print(f"  Context chunks: {len(result['context_chunks'])}")
        print(f"  Language: {result['language']}")
        
        if result['context_chunks']:
            print("\nContext chunks:")
            for i, chunk in enumerate(result['context_chunks']):
                print(f"  {i+1}. {chunk[:100]}...")
        
        if result['entities']:
            print("\nEntities:")
            for i, entity in enumerate(result['entities']):
                print(f"  {i+1}. {entity['name']} ({entity['entity_type']})")
        
    finally:
        retrieval_service.close()

if __name__ == "__main__":
    asyncio.run(test_retrieval_direct())
