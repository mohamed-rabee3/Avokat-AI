#!/usr/bin/env python3
"""
Comprehensive test to verify that the LLM can now see uploaded documents
"""

import requests
import json
import time
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.retrieval import retrieval_service
from backend.app.core.config import settings

def test_server_connection():
    """Test if the server is running and accessible"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def test_retrieval_service_directly():
    """Test the retrieval service directly to verify it finds documents"""
    print("\n" + "="*60)
    print("TESTING RETRIEVAL SERVICE DIRECTLY")
    print("="*60)
    
    try:
        # Initialize retrieval service
        retrieval_service.initialize(
            uri=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )
        print("✅ Retrieval service initialized")
        
        session_id = 60
        
        # Test queries that should find documents
        test_queries = [
            ("contract", "English query for contract"),
            ("عقد", "Arabic query for contract"),
            ("المؤجر", "Arabic query for landlord"),
            ("المستأجر", "Arabic query for tenant"),
            ("إيجار", "Arabic query for rental"),
        ]
        
        all_tests_passed = True
        
        for query, description in test_queries:
            print(f"\n--- Testing: {description} ---")
            print(f"Query: '{query}'")
            
            result = retrieval_service.retrieve_entities_and_relationships(
                query=query,
                session_id=session_id,
                language="mixed",
                limit=10
            )
            
            entities_count = len(result.get('entities', []))
            context_count = len(result.get('context_chunks', []))
            
            print(f"Entities found: {entities_count}")
            print(f"Context chunks: {context_count}")
            
            if entities_count > 0 or context_count > 0:
                print("✅ SUCCESS: Found relevant documents!")
                
                # Show some context
                if context_count > 0:
                    print("Context preview:")
                    for i, chunk in enumerate(result['context_chunks'][:2]):
                        preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
                        print(f"  {i+1}. {preview}")
            else:
                print("❌ FAILED: No documents found")
                all_tests_passed = False
        
        retrieval_service.close()
        return all_tests_passed
        
    except Exception as e:
        print(f"❌ Error testing retrieval service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_endpoint():
    """Test the chat endpoint to verify LLM can see documents"""
    print("\n" + "="*60)
    print("TESTING CHAT ENDPOINT")
    print("="*60)
    
    url = "http://127.0.0.1:8000/chat/non-streaming"
    session_id = 60
    
    # Test cases that should trigger document retrieval
    test_cases = [
        {
            "query": "What is this contract about?",
            "description": "English query about contract content",
            "should_find_docs": True
        },
        {
            "query": "ما هو هذا العقد؟",
            "description": "Arabic query about contract content", 
            "should_find_docs": True
        },
        {
            "query": "Who are the parties in this contract?",
            "description": "English query about contract parties",
            "should_find_docs": True
        },
        {
            "query": "من هم أطراف هذا العقد؟",
            "description": "Arabic query about contract parties",
            "should_find_docs": True
        },
        {
            "query": "What are the rental terms?",
            "description": "English query about rental terms",
            "should_find_docs": True
        },
        {
            "query": "ما هي شروط الإيجار؟",
            "description": "Arabic query about rental terms",
            "should_find_docs": True
        },
        {
            "query": "Tell me about the weather today",
            "description": "Unrelated query (should not find docs)",
            "should_find_docs": False
        }
    ]
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['description']} ---")
        print(f"Query: '{test_case['query']}'")
        
        payload = {
            "session_id": session_id,
            "message": test_case['query']
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                sources = result.get('sources', [])
                response_text = result.get('response', '')
                
                print(f"✅ Response received (Status: {response.status_code})")
                print(f"Sources found: {len(sources)}")
                
                # Check if we found documents when we expected to
                found_docs = len(sources) > 0
                expected_docs = test_case['should_find_docs']
                
                if found_docs == expected_docs:
                    if found_docs:
                        print("🎉 SUCCESS: LLM can see documents!")
                        print("Sources:")
                        for source in sources[:3]:
                            print(f"  - {source}")
                    else:
                        print("✅ SUCCESS: No documents found (as expected for unrelated query)")
                else:
                    print(f"❌ FAILED: Expected {'documents' if expected_docs else 'no documents'}, but got {len(sources)} sources")
                    all_tests_passed = False
                
                # Show response preview
                response_preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
                print(f"Response: {response_preview}")
                
            else:
                print(f"❌ FAILED: HTTP {response.status_code} - {response.text}")
                all_tests_passed = False
                
        except requests.exceptions.ConnectionError:
            print("❌ FAILED: Could not connect to server")
            all_tests_passed = False
            break
        except Exception as e:
            print(f"❌ FAILED: Error - {e}")
            all_tests_passed = False
    
    return all_tests_passed

def main():
    """Run all tests"""
    print("🔍 TESTING DOCUMENT VISIBILITY FIX")
    print("="*60)
    
    # Test 1: Server connection
    print("\n1. Testing server connection...")
    if not test_server_connection():
        print("\n❌ CRITICAL: Server is not running!")
        print("Please start the server with:")
        print("  venv\\Scripts\\Activate.ps1")
        print("  python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000")
        return False
    
    # Test 2: Retrieval service directly
    print("\n2. Testing retrieval service directly...")
    retrieval_success = test_retrieval_service_directly()
    
    # Test 3: Chat endpoint
    print("\n3. Testing chat endpoint...")
    chat_success = test_chat_endpoint()
    
    # Final results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    if retrieval_success and chat_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The LLM can now see uploaded documents!")
        print("✅ Document retrieval is working correctly!")
        print("✅ Chat endpoint is functioning properly!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        if not retrieval_success:
            print("❌ Retrieval service has issues")
        if not chat_success:
            print("❌ Chat endpoint has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
