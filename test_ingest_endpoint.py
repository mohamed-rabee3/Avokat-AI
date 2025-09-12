#!/usr/bin/env python3
"""
Test file for the /ingest endpoint
"""
import asyncio
import os
import sys
import requests
import json
from pathlib import Path
from io import BytesIO

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings

class IngestEndpointTester:
    """Test class for the /ingest endpoint"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        
    def load_real_pdf(self):
        """Load the real contract.pdf file"""
        pdf_path = Path("contract.pdf")
        if not pdf_path.exists():
            raise FileNotFoundError(f"contract.pdf not found at {pdf_path.absolute()}")
        
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
        
        print(f"📄 Loaded contract.pdf ({len(pdf_content)} bytes)")
        return pdf_content
    
    def create_session(self):
        """Create a new session"""
        try:
            response = requests.post(f"{self.base_url}/sessions", json={"name": "Test Session"})
            if response.status_code == 201:  # Changed from 200 to 201 (Created)
                data = response.json()
                self.session_id = data.get("id")  # Changed from "session_id" to "id"
                print(f"✅ Created session with ID: {self.session_id}")
                return True
            else:
                print(f"❌ Failed to create session: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return False
    
    def test_ingest_endpoint(self):
        """Test the /ingest endpoint with a PDF file"""
        if not self.session_id:
            print("❌ No session ID available. Create a session first.")
            return False
            
        try:
            # Load real PDF content
            pdf_content = self.load_real_pdf()
            
            # Prepare multipart form data
            files = {
                'file': ('contract.pdf', BytesIO(pdf_content), 'application/pdf')
            }
            data = {
                'session_id': self.session_id
            }
            
            print(f"📤 Uploading PDF to session {self.session_id}...")
            
            # Make the request
            response = requests.post(
                f"{self.base_url}/ingest",
                files=files,
                data=data,
                timeout=300  # 5 minutes timeout for processing
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Ingestion successful!")
                print(f"   Status: {result.get('status')}")
                print(f"   Session ID: {result.get('session_id')}")
                print(f"   File: {result.get('file_name')}")
                print(f"   Size: {result.get('size_bytes')} bytes")
                print(f"   Chunks: {result.get('chunks')}")
                print(f"   Nodes created: {result.get('nodes_created')}")
                print(f"   Relationships created: {result.get('relationships_created')}")
                print(f"   Batch ID: {result.get('batch_id')}")
                
                if 'session_stats' in result:
                    print(f"   Session stats: {result.get('session_stats')}")
                
                if 'note' in result:
                    print(f"   Note: {result.get('note')}")
                
                return True
            else:
                print(f"❌ Ingestion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out. The ingestion process might be taking longer than expected.")
            return False
        except Exception as e:
            print(f"❌ Error during ingestion: {e}")
            return False
    
    def test_invalid_file_type(self):
        """Test with invalid file type"""
        if not self.session_id:
            print("❌ No session ID available. Create a session first.")
            return False
            
        try:
            # Create a text file instead of PDF
            text_content = b"This is a text file, not a PDF"
            
            files = {
                'file': ('test.txt', BytesIO(text_content), 'text/plain')
            }
            data = {
                'session_id': self.session_id
            }
            
            print("📤 Testing with invalid file type (text file)...")
            
            response = requests.post(
                f"{self.base_url}/ingest",
                files=files,
                data=data
            )
            
            if response.status_code == 400:
                print("✅ Correctly rejected invalid file type")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Expected 400 error, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing invalid file type: {e}")
            return False
    
    def test_nonexistent_session(self):
        """Test with non-existent session ID"""
        try:
            pdf_content = self.load_real_pdf()
            
            files = {
                'file': ('contract.pdf', BytesIO(pdf_content), 'application/pdf')
            }
            data = {
                'session_id': 99999  # Non-existent session ID
            }
            
            print("📤 Testing with non-existent session ID...")
            
            response = requests.post(
                f"{self.base_url}/ingest",
                files=files,
                data=data
            )
            
            if response.status_code == 404:
                print("✅ Correctly rejected non-existent session")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Expected 404 error, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing non-existent session: {e}")
            return False
    
    def test_missing_parameters(self):
        """Test with missing parameters"""
        try:
            print("📤 Testing with missing session_id...")
            
            response = requests.post(f"{self.base_url}/ingest")
            
            if response.status_code == 422:  # FastAPI validation error
                print("✅ Correctly rejected missing parameters")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Expected 422 error, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing missing parameters: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting /ingest endpoint tests with contract.pdf...")
        print("=" * 50)
        
        # Check if contract.pdf exists
        pdf_path = Path("contract.pdf")
        if not pdf_path.exists():
            print(f"❌ contract.pdf not found at {pdf_path.absolute()}")
            print("   Please ensure contract.pdf is in the current directory")
            return False
        
        # Test 1: Create session
        print("\n1. Creating test session...")
        if not self.create_session():
            print("❌ Cannot proceed without a session")
            return False
        
        # Test 2: Valid ingestion
        print("\n2. Testing valid PDF ingestion with contract.pdf...")
        success1 = self.test_ingest_endpoint()
        
        # Test 3: Invalid file type
        print("\n3. Testing invalid file type...")
        success2 = self.test_invalid_file_type()
        
        # Test 4: Non-existent session
        print("\n4. Testing non-existent session...")
        success3 = self.test_nonexistent_session()
        
        # Test 5: Missing parameters
        print("\n5. Testing missing parameters...")
        success4 = self.test_missing_parameters()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"   Valid ingestion (contract.pdf): {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"   Invalid file type: {'✅ PASS' if success2 else '❌ FAIL'}")
        print(f"   Non-existent session: {'✅ PASS' if success3 else '❌ FAIL'}")
        print(f"   Missing parameters: {'✅ PASS' if success4 else '❌ FAIL'}")
        
        all_passed = success1 and success2 and success3 and success4
        print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return all_passed

def main():
    """Main function"""
    print("🧪 Ingest Endpoint Tester")
    print("=" * 50)
    
    # Check if server is running
    tester = IngestEndpointTester()
    
    try:
        # Test server connectivity
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the FastAPI server is running on http://localhost:8000")
        print("   Start the server with: uvicorn backend.app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False
    
    # Run tests
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
c