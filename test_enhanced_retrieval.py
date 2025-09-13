#!/usr/bin/env python3
"""
Test script for the enhanced retrieval system
Tests both Arabic and English queries with improved graph traversal
"""

import asyncio
import sys
import os
sys.path.append('backend')

from app.services.retrieval import retrieval_service
from app.services.embedding_service import embedding_service
from app.core.config import settings

async def test_enhanced_retrieval():
    """Test the enhanced retrieval system with various queries"""
    
    print("🚀 Testing Enhanced Retrieval System")
    print("=" * 50)
    
    # Initialize services
    print("📋 Initializing services...")
    embedding_service.initialize()
    print(f"✅ Embedding service initialized with {embedding_service.get_embedding_dimension()} dimensions")
    
    retrieval_service.initialize(
        uri=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
        database=settings.neo4j_database
    )
    print("✅ Retrieval service initialized")
    
    # Test queries in both languages
    test_queries = [
        # English queries
        {
            "query": "tell me about the contract",
            "language": "english",
            "session_id": 1,
            "description": "General contract query in English"
        },
        {
            "query": "what are the rental terms",
            "language": "english", 
            "session_id": 1,
            "description": "Specific rental terms query in English"
        },
        {
            "query": "who are the parties involved",
            "language": "english",
            "session_id": 1,
            "description": "Parties query in English"
        },
        # Arabic queries
        {
            "query": "أخبرني عن العقد",
            "language": "arabic",
            "session_id": 1,
            "description": "General contract query in Arabic"
        },
        {
            "query": "ما هي شروط الإيجار",
            "language": "arabic",
            "session_id": 1,
            "description": "Rental terms query in Arabic"
        },
        {
            "query": "من هم الأطراف في العقد",
            "language": "arabic",
            "session_id": 1,
            "description": "Parties query in Arabic"
        },
        # Mixed language queries
        {
            "query": "tell me about العقد",
            "language": "mixed",
            "session_id": 1,
            "description": "Mixed language query"
        }
    ]
    
    try:
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {test_case['description']}")
            print(f"Query: '{test_case['query']}'")
            print(f"Language: {test_case['language']}")
            print("-" * 40)
            
            # Perform retrieval
            result = retrieval_service.retrieve_entities_and_relationships(
                query=test_case['query'],
                session_id=test_case['session_id'],
                language=test_case['language'],
                limit=10
            )
            
            # Display results
            print(f"📊 Results Summary:")
            print(f"  • Entities found: {len(result.get('entities', []))}")
            print(f"  • Relationships found: {len(result.get('relationships', []))}")
            print(f"  • Context chunks: {len(result.get('context_chunks', []))}")
            print(f"  • Expanded context items: {len(result.get('expanded_context', []))}")
            print(f"  • Search terms used: {result.get('search_terms', [])}")
            print(f"  • Detected language: {result.get('language', 'unknown')}")
            
            # Show top entities
            if result.get('entities'):
                print(f"\n🏷️  Top Entities:")
                for j, entity in enumerate(result['entities'][:3], 1):
                    relevance = entity.get('relevance_score', 'N/A')
                    print(f"  {j}. {entity.get('name', 'Unknown')} ({entity.get('entity_type', 'Unknown')}) [Relevance: {relevance}]")
            
            # Show context chunks
            if result.get('context_chunks'):
                print(f"\n📄 Relevant Document Content:")
                for j, chunk in enumerate(result['context_chunks'][:2], 1):
                    preview = chunk[:150] + "..." if len(chunk) > 150 else chunk
                    print(f"  {j}. {preview}")
            
            # Show expanded context
            if result.get('expanded_context'):
                print(f"\n🔗 Related Information:")
                for j, item in enumerate(result['expanded_context'][:3], 1):
                    if item['type'] == 'expanded_entity':
                        entity = item['entity']
                        rel_type = item.get('relationship_type', 'unknown')
                        print(f"  {j}. Related entity: {entity.get('name', 'Unknown')} via {rel_type}")
                    elif item['type'] == 'expanded_relationship':
                        rel = item['relationship']
                        print(f"  {j}. Related relationship: {rel.get('type', 'Unknown')}")
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
            
            print("\n" + "="*50)
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        retrieval_service.close()
        print("🔒 Services closed")

def test_session_statistics():
    """Test session statistics functionality"""
    print("\n📈 Testing Session Statistics")
    print("=" * 30)
    
    try:
        retrieval_service.initialize(
            uri=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )
        
        stats = retrieval_service.get_session_statistics(1)
        print(f"Session 1 Statistics:")
        print(f"  • Total entities: {stats.get('total_entities', 0)}")
        print(f"  • Total relationships: {stats.get('total_relationships', 0)}")
        print(f"  • Entities by type: {stats.get('entities_by_type', {})}")
        print(f"  • Entities by language: {stats.get('entities_by_language', {})}")
        
    except Exception as e:
        print(f"❌ Statistics test failed: {e}")
    finally:
        retrieval_service.close()

if __name__ == "__main__":
    print("🧪 Enhanced Retrieval System Test Suite")
    print("This script tests the improved retrieval system with:")
    print("• Better semantic search with higher threshold")
    print("• Improved graph traversal")
    print("• Enhanced multilingual support")
    print("• Context expansion through relationships")
    print("• Better search term extraction")
    print()
    
    # Run the main test
    asyncio.run(test_enhanced_retrieval())
    
    # Run statistics test
    test_session_statistics()
    
    print("\n✅ All tests completed!")
    print("\n💡 Key Improvements:")
    print("• Higher similarity threshold (0.5) for better relevance")
    print("• Graph traversal with relationship following")
    print("• Simplified search term extraction")
    print("• Enhanced context expansion")
    print("• Better multilingual query handling")
    print("• Improved relevance scoring")
