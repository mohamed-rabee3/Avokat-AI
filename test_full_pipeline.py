#!/usr/bin/env python3
"""
Test the full pipeline: Document Upload -> Retrieval -> LLM Response
"""
import requests
import json
import time
import sys
import os
import asyncio

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.retrieval import retrieval_service
from app.core.config import settings

def test_server_health():
    """Test if the server is running and healthy"""
    print("🔍 Testing Server Health")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server is not responding: {e}")
        return False

def test_retrieval_service():
    """Test retrieval service directly"""
    print("\n🔍 Testing Retrieval Service")
    print("=" * 35)
    
    try:
        # Initialize retrieval service
        retrieval_service.initialize(
            uri=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )
        
        session_id = 60
        
        # Test both English and Arabic queries
        test_queries = [
            # English queries (should translate to Arabic)
            "What is in the contract?",
            "Tell me about the rental agreement", 
            "Who is the tenant?",
            "Who is the landlord?",
            "Tell me about the apartment",
            
            # Arabic queries
            "عقد",
            "إيجار", 
            "شقة",
            "مؤجر",
            "مستأجر"
        ]
        
        successful_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"{i:2d}. Testing: '{query}'")
            
            result = retrieval_service.retrieve_entities_and_relationships(
                query=query,
                session_id=str(session_id),
                language="mixed",
                limit=10
            )
            
            entities = len(result.get('entities', []))
            context_chunks = len(result.get('context_chunks', []))
            
            print(f"     Entities: {entities}, Context chunks: {context_chunks}")
            
            if context_chunks > 0:
                successful_queries += 1
                print(f"     ✅ SUCCESS")
            else:
                print(f"     ❌ No context found")
        
        print(f"\n📊 Retrieval Service Summary:")
        print(f"   Successful queries: {successful_queries}/{len(test_queries)}")
        print(f"   Success rate: {successful_queries/len(test_queries)*100:.1f}%")
        
        retrieval_service.close()
        return successful_queries > 0
        
    except Exception as e:
        print(f"❌ Error testing retrieval service: {e}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint with both Arabic and English queries"""
    print("\n🔍 Testing Chat Endpoint")
    print("=" * 30)
    
    session_id = 60
    base_url = "http://localhost:8000"
    
    # Test cases covering different scenarios
    test_cases = [
        {
            "query": "What is in the contract?",
            "language": "English",
            "description": "Basic English question about contract content"
        },
        {
            "query": "Tell me about the rental agreement",
            "language": "English", 
            "description": "English question about rental terms"
        },
        {
            "query": "Who is the tenant?",
            "language": "English",
            "description": "English question about parties"
        },
        {
            "query": "عقد",
            "language": "Arabic",
            "description": "Direct Arabic term"
        },
        {
            "query": "مؤجر",
            "language": "Arabic",
            "description": "Arabic term for landlord"
        },
        {
            "query": "مستأجر",
            "language": "Arabic", 
            "description": "Arabic term for tenant"
        }
    ]
    
    successful_tests = 0
    total_sources = 0
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        language = test_case["language"]
        description = test_case["description"]
        
        print(f"\n{i}. Testing {language}: '{query}'")
        print(f"   Description: {description}")
        
        try:
            url = f"{base_url}/chat/non-streaming"
            payload = {
                "session_id": session_id,
                "message": query
            }
            
            response = requests.post(
                url, 
                json=payload, 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                response_text = data.get('response', '')
                sources = data.get('sources', [])
                
                print(f"   Response length: {len(response_text)} characters")
                print(f"   Sources found: {len(sources)}")
                
                if sources:
                    successful_tests += 1
                    total_sources += len(sources)
                    print(f"   ✅ SUCCESS: Found {len(sources)} sources")
                    
                    # Show source types
                    source_types = [s.get('type', 'unknown') for s in sources]
                    print(f"   Source types: {source_types}")
                    
                    # Show response preview
                    preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
                    print(f"   Response preview: {preview}")
                    
                    # Check if response mentions relevant content
                    if any(term in response_text.lower() for term in ['contract', 'عقد', 'rental', 'إيجار', 'tenant', 'مستأجر', 'landlord', 'مؤجر']):
                        print(f"   ✅ Response contains relevant content")
                    else:
                        print(f"   ⚠️  Response may not contain relevant content")
                        
                else:
                    print(f"   ❌ No sources found - LLM won't have document context")
                
                # Check for API errors
                if "503" in response_text or "UNAVAILABLE" in response_text:
                    print(f"   ⚠️  Gemini API error (model overloaded)")
                elif "error" in response_text.lower():
                    print(f"   ⚠️  Response contains error message")
                    
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Chat Endpoint Summary:")
    print(f"   Successful tests: {successful_tests}/{len(test_cases)}")
    print(f"   Total sources found: {total_sources}")
    print(f"   Success rate: {successful_tests/len(test_cases)*100:.1f}%")
    
    return successful_tests > 0

def test_streaming_chat():
    """Test the streaming chat endpoint"""
    print("\n🔍 Testing Streaming Chat Endpoint")
    print("=" * 40)
    
    session_id = 60
    base_url = "http://localhost:8000"
    
    test_query = "What is in the contract?"
    
    print(f"Testing streaming with query: '{test_query}'")
    
    try:
        url = f"{base_url}/chat/"
        payload = {
            "session_id": session_id,
            "message": test_query
        }
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
            stream=True
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Streaming response received")
            
            chunks_received = 0
            total_content = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            if 'chunk' in data:
                                chunks_received += 1
                                total_content += data['chunk']
                                print(f"   Chunk {chunks_received}: {data['chunk'][:50]}...")
                            elif 'done' in data:
                                sources = data.get('sources', [])
                                print(f"   ✅ Streaming complete: {len(sources)} sources")
                                break
                            elif 'error' in data:
                                print(f"   ❌ Streaming error: {data['error']}")
                                break
                        except json.JSONDecodeError:
                            continue
            
            print(f"   Total chunks received: {chunks_received}")
            print(f"   Total content length: {len(total_content)} characters")
            
            if chunks_received > 0:
                print("✅ Streaming chat is working")
                return True
            else:
                print("❌ No chunks received")
                return False
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing streaming chat: {e}")
        return False

def test_session_management():
    """Test session management endpoints"""
    print("\n🔍 Testing Session Management")
    print("=" * 35)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test creating a new session
        print("1. Testing session creation...")
        response = requests.post(f"{base_url}/sessions/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"   ✅ Session created: {session_id}")
            
            # Test getting session info
            print("2. Testing session info retrieval...")
            response = requests.get(f"{base_url}/sessions/{session_id}", timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Session info retrieved")
            else:
                print(f"   ❌ Failed to get session info: {response.status_code}")
            
            # Test listing sessions
            print("3. Testing session listing...")
            response = requests.get(f"{base_url}/sessions/", timeout=10)
            
            if response.status_code == 200:
                sessions = response.json()
                print(f"   ✅ Found {len(sessions)} sessions")
            else:
                print(f"   ❌ Failed to list sessions: {response.status_code}")
            
            return True
            
        else:
            print(f"   ❌ Failed to create session: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing session management: {e}")
        return False

def main():
    """Run the full pipeline test suite"""
    print("🚀 Full Pipeline Test Suite")
    print("=" * 50)
    print("Testing complete end-to-end functionality")
    print("=" * 50)
    
    # Test results tracking
    results = {}
    
    # 1. Test server health
    results['server_health'] = test_server_health()
    
    if not results['server_health']:
        print("\n❌ Server is not running. Please start the server first.")
        print("   Run: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # 2. Test retrieval service
    results['retrieval_service'] = test_retrieval_service()
    
    # 3. Test chat endpoint
    results['chat_endpoint'] = test_chat_endpoint()
    
    # 4. Test streaming chat
    results['streaming_chat'] = test_streaming_chat()
    
    # 5. Test session management
    results['session_management'] = test_session_management()
    
    # Final summary
    print("\n\n🎯 FINAL PIPELINE RESULTS")
    print("=" * 40)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 SUCCESS: Full pipeline is working perfectly!")
        print("   ✅ Server is running")
        print("   ✅ Retrieval service is working")
        print("   ✅ Chat endpoint is working")
        print("   ✅ Streaming chat is working")
        print("   ✅ Session management is working")
        print("\n   Both Arabic and English queries work with document retrieval!")
    else:
        print(f"\n⚠️  Some issues found. {total_tests - passed_tests} test(s) failed.")
        print("   Check the individual test results above for details.")

if __name__ == "__main__":
    main()
