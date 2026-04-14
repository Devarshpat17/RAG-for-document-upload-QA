"""
Simple test script to debug the API issues.

This script tests the basic API functionality with detailed error output.
"""

import requests
import json
import time
import traceback
from pathlib import Path


def test_api_connection():
    """Test if the API is running."""
    print("=" * 60)
    print("Testing API Connection...")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/api/", timeout=5)
        print(f"✓ API is reachable (status: {response.status_code})")
        print(f"  Response: {response.json()}")
        return True
    except requests.ConnectionError:
        print("✗ Cannot connect to API at http://localhost:8000/api/")
        print("  Make sure the development server is running:")
        print("  python manage.py runserver")
        return False
    except Exception as e:
        print(f"✗ API connection error: {e}")
        traceback.print_exc()
        return False


def test_document_upload():
    """Test document upload."""
    print("\n" + "=" * 60)
    print("Testing Document Upload...")
    print("=" * 60)
    
    # Create a sample text file
    sample_text = """
Artificial Intelligence (AI) is transforming industries worldwide.
Machine Learning (ML) is a key subset of AI that focuses on learning from data.
Deep Learning uses neural networks to process complex information.
Natural Language Processing (NLP) enables computers to understand and generate human language.
Computer Vision allows machines to interpret visual information from images and videos.
"""
    
    sample_file = "test_doc.txt"
    with open(sample_file, 'w') as f:
        f.write(sample_text)
    
    print(f"Created sample file: {sample_file}")
    
    try:
        print("Uploading document (this may take 30-60 seconds on first run)...")
        print("  - Embedding model is being loaded...")
        
        with open(sample_file, 'rb') as f:
            files = {'file': f}
            data = {'title': 'AI and ML Overview'}
            
            # Use longer timeout for first request (model loading)
            response = requests.post(
                "http://localhost:8000/api/documents/",
                files=files,
                data=data,
                timeout=120  # 2 minute timeout
            )
        
        print(f"Upload response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✓ Document uploaded successfully!")
            print(f"  Document ID: {result.get('id')}")
            print(f"  Title: {result.get('title')}")
            print(f"  Processed: {result.get('processed')}")
            print(f"  Chunks: {result.get('chunk_count')}")
            return result
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except requests.Timeout:
        print("✗ Request timed out after 120 seconds")
        print("  This usually means:")
        print("  1. The embedding model is still downloading")
        print("  2. Your system is running out of memory")
        print("  3. The server encountered an error")
        print("\n  Try running: python manage.py warmup_services")
        return None
    except Exception as e:
        print(f"✗ Error during upload: {e}")
        traceback.print_exc()
        return None
    finally:
        # Clean up
        Path(sample_file).unlink(missing_ok=True)
        print(f"\nCleaned up test file: {sample_file}")


def test_document_list():
    """Test listing documents."""
    print("\n" + "=" * 60)
    print("Testing Document List...")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/api/documents/", timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✓ Retrieved {len(documents)} document(s)")
            for doc in documents:
                print(f"  - {doc.get('title')} (ID: {doc.get('id')})")
            return documents
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error listing documents: {e}")
        traceback.print_exc()
        return None


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "AI CHATBOT - API DEBUG TEST SCRIPT" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Test API connection
    if not test_api_connection():
        print("\n⚠️  Cannot proceed without API connection")
        return
    
    # Test warmup (optional but helpful)
    print("\n" + "=" * 60)
    print("Optional: Warming Up Services...")
    print("=" * 60)
    print("Run this command to pre-load the embedding model:")
    print("  python manage.py warmup_services")
    print("\nThis will prevent timeouts on the first document upload.")
    
    # Test document upload
    doc = test_document_upload()
    
    # Test listing
    if doc:
        test_document_list()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
