"""
Example script demonstrating the AI Chatbot API usage.

This script shows a complete workflow:
1. Upload a text document
2. Upload JSON data
3. Ask questions and get answers
"""

import requests
import json
import time
from pathlib import Path 


class ChatbotAPIClient:
    """Client for interacting with the AI Chatbot API."""
    
    def __init__(self, base_url="http://localhost:8000/api"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url.rstrip('/')
    
    def upload_document(self, file_path, title):
        """
        Upload a document to the system.
        
        Args:
            file_path: Path to the document file
            title: Title for the document
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/documents/"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'title': title}
            # Use longer timeout for document upload (first request may load models)
            response = requests.post(url, files=files, data=data, timeout=120)
        
        response.raise_for_status()
        return response.json()
    
    def list_documents(self):
        """
        List all documents.
        
        Returns:
            List of documents
        """
        url = f"{self.base_url}/documents/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def delete_document(self, document_id):
        """
        Delete a document.
        
        Args:
            document_id: ID of the document to delete
        """
        url = f"{self.base_url}/documents/{document_id}/"
        response = requests.delete(url)
        response.raise_for_status()
    
    def upload_json_database(self, name, data, description=None):
        """
        Upload JSON data to the system.
        
        Args:
            name: Name for the database
            data: JSON data (list or dict)
            description: Optional description
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/json-database/"
        
        payload = {
            'name': name,
            'data': data
        }
        
        if description:
            payload['description'] = description
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_json_databases(self):
        """
        List all JSON databases.
        
        Returns:
            List of databases
        """
        url = f"{self.base_url}/json-database/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def ask_question(self, question, max_context_chunks=5, include_sources=True):
        """
        Ask a question to the chatbot.
        
        Args:
            question: The question to ask
            max_context_chunks: Maximum context chunks to retrieve
            include_sources: Whether to include source information
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/chat/ask/"
        
        payload = {
            'question': question,
            'max_context_chunks': max_context_chunks,
            'include_sources': include_sources
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_chat_history(self):
        """
        Get chat history.
        
        Returns:
            List of chat interactions
        """
        url = f"{self.base_url}/chat/history/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def clear_chat_history(self):
        """Clear all chat history."""
        url = f"{self.base_url}/chat/history/"
        response = requests.delete(url)
        response.raise_for_status()
        return response.json()


def create_sample_text_file():
    """Create a sample text file for testing."""
    content = """
    Artificial Intelligence and Machine Learning
    
    Artificial Intelligence (AI) is the simulation of human intelligence by machines.
    Machine Learning (ML) is a subset of AI that enables systems to learn from data.
    
    Deep Learning is a subset of ML that uses neural networks with multiple layers.
    These technologies are transforming industries including healthcare, finance, and transportation.
    
    Common AI applications include:
    - Natural Language Processing (NLP) for understanding text
    - Computer Vision for image recognition
    - Robotics for automation
    - Recommendation systems for personalized content
    
    AI models require large amounts of data and computational power for training.
    """
    
    file_path = "sample_ai_document.txt"
    with open(file_path, 'w') as f:
        f.write(content.strip())
    
    return file_path


def main():
    """Main function demonstrating API usage."""
    
    print("=" * 60)
    print("AI Chatbot API - Example Usage")
    print("=" * 60)
    print()
    
    # Initialize client
    client = ChatbotAPIClient()
    
    # Step 1: Create and upload a sample document
    print("Step 1: Creating and uploading a sample document...")
    sample_file = create_sample_text_file()
    
    try:
        doc_result = client.upload_document(sample_file, "AI and ML Overview")
        print(f"✓ Document uploaded successfully!")
        print(f"  Document ID: {doc_result['id']}")
        print(f"  Title: {doc_result['title']}")
        print(f"  Processed: {doc_result['processed']}")
        print(f"  Chunks: {doc_result['chunk_count']}")
        print()
        
        # Wait for processing
        print("Waiting for document processing...")
        time.sleep(3)
        
    finally:
        # Clean up sample file
        Path(sample_file).unlink(missing_ok=True)
    
    # Step 2: Upload JSON database
    print("\nStep 2: Uploading JSON database...")
    
    products = [
        {
            "id": 1,
            "name": "AI-Powered Robot",
            "category": "Robotics",
            "price": 4999.99,
            "description": "Advanced robot with computer vision and NLP capabilities",
            "features": ["Object Recognition", "Voice Commands", "Autonomous Navigation"]
        },
        {
            "id": 2,
            "name": "ML Training Platform",
            "category": "Software",
            "price": 299.99,
            "description": "Cloud-based platform for training machine learning models",
            "features": ["GPU Support", "AutoML", "Model Deployment"]
        },
        {
            "id": 3,
            "name": "Computer Vision Camera",
            "category": "Hardware",
            "price": 799.99,
            "description": "High-resolution camera with built-in AI processing",
            "features": ["Real-time Object Detection", "Facial Recognition", "4K Video"]
        }
    ]
    
    json_result = client.upload_json_database(
        "AI Products Catalog",
        products,
        "Catalog of AI and ML related products"
    )
    
    print(f"✓ JSON database uploaded successfully!")
    print(f"  Database ID: {json_result['id']}")
    print(f"  Name: {json_result['name']}")
    print(f"  Records: {json_result['record_count']}")
    print(f"  Processed: {json_result['processed']}")
    print()
    
    # Wait for processing
    print("Waiting for JSON database processing...")
    time.sleep(3)
    
    # Step 3: Ask questions
    print("\nStep 3: Asking questions...")
    print("-" * 60)
    
    questions = [
        "What is the difference between AI and Machine Learning?",
        "What AI products are available?",
        "How much does the ML Training Platform cost?",
        "What features does the AI-Powered Robot have?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        print()
        
        try:
            result = client.ask_question(question)
            
            print(f"Answer: {result['answer']}")
            print(f"\nProcessing time: {result['processing_time']:.2f} seconds")
            
            if result.get('sources'):
                print(f"\nSources used:")
                for source in result['sources']:
                    source_type = source['type']
                    source_name = source.get('name') or source.get('title')
                    source_score = source['score']
                    print(f"  - {source_type}: {source_name} (score: {source_score:.2f})")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 60)
        
        # Small delay between questions
        time.sleep(1)
    
    # Step 4: View chat history
    print("\nStep 4: Viewing chat history...")
    history = client.get_chat_history()
    print(f"Total chat interactions: {len(history)}")
    print()
    
    # Step 5: List all resources
    print("Step 5: Listing all resources...")
    
    docs = client.list_documents()
    print(f"Documents: {docs['count']}")
    
    databases = client.list_json_databases()
    print(f"JSON Databases: {databases['count']}")
    print()
    
    # Cleanup (optional)
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print()
    print("Note: Documents and databases created during this example")
    print("are still in the system. You can view or delete them via:")
    print("  - Admin interface: http://localhost:8000/admin/")
    print("  - API endpoints (see API_GUIDE.md)")
    print()


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Make sure the server is running:")
        print("  python manage.py runserver")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
