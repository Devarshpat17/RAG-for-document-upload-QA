# API Usage Guide

Complete guide for using the AI Chatbot API endpoints.

## Base URL

```
http://localhost:8000/api/
```

## Authentication

Currently, the API does not require authentication. For production deployments, implement Django REST Framework authentication (Token, JWT, OAuth2).

## Endpoints

### 1. Document Management

#### Upload a Document

**Endpoint:** `POST /api/documents/`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): The document file (PDF or TXT)
- `title` (required): Document title

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/documents/ \
  -F "file=@/path/to/document.pdf" \
  -F "title=My Research Paper"
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/api/documents/"
files = {'file': open('document.pdf', 'rb')}
data = {'title': 'My Research Paper'}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My Research Paper",
  "file": "/media/documents/2024/01/15/document.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "file_size_display": "1.00 MB",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "processed": true,
  "chunk_count": 25,
  "faiss_index_id": "doc_550e8400-e29b-41d4-a716-446655440000"
}
```

#### List All Documents

**Endpoint:** `GET /api/documents/`

**Example:**
```bash
curl http://localhost:8000/api/documents/
```

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "My Research Paper",
      "file_type": "pdf",
      "file_size_display": "1.00 MB",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "processed": true,
      "chunk_count": 25
    }
  ]
}
```

#### Get Document Details

**Endpoint:** `GET /api/documents/{id}/`

**Example:**
```bash
curl http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/
```

#### Delete a Document

**Endpoint:** `DELETE /api/documents/{id}/`

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/
```

#### Reprocess a Document

**Endpoint:** `POST /api/documents/{id}/reprocess/`

**Example:**
```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/reprocess/
```

---

### 2. JSON Database Management

#### Upload JSON Data

**Endpoint:** `POST /api/json-database/`

**Content-Type:** `application/json`

**Parameters:**
- `name` (required): Database name
- `description` (optional): Database description
- `data` (required): JSON data (list or dict)

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/json-database/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Catalog",
    "description": "Our product inventory",
    "data": [
      {
        "id": 1,
        "name": "Laptop",
        "category": "Electronics",
        "price": 999.99,
        "specs": {
          "ram": "16GB",
          "storage": "512GB SSD"
        }
      },
      {
        "id": 2,
        "name": "Mouse",
        "category": "Accessories",
        "price": 29.99
      }
    ]
  }'
```

**Example (Python):**
```python
import requests
import json

url = "http://localhost:8000/api/json-database/"
data = {
    "name": "Product Catalog",
    "description": "Our product inventory",
    "data": [
        {
            "id": 1,
            "name": "Laptop",
            "category": "Electronics",
            "price": 999.99,
            "specs": {"ram": "16GB", "storage": "512GB SSD"}
        },
        {
            "id": 2,
            "name": "Mouse",
            "category": "Accessories",
            "price": 29.99
        }
    ]
}

response = requests.post(url, json=data)
print(response.json())
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Product Catalog",
  "description": "Our product inventory",
  "data": [...],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "record_count": 2,
  "processed": true,
  "faiss_index_id": "json_660e8400-e29b-41d4-a716-446655440001"
}
```

#### List All JSON Databases

**Endpoint:** `GET /api/json-database/`

#### Get JSON Database Details

**Endpoint:** `GET /api/json-database/{id}/`

#### Delete a JSON Database

**Endpoint:** `DELETE /api/json-database/{id}/`

---

### 3. Chat Interface

#### Ask a Question

**Endpoint:** `POST /api/chat/ask/`

**Content-Type:** `application/json`

**Parameters:**
- `question` (required): The question to ask
- `max_context_chunks` (optional): Maximum context chunks to retrieve (default: 5)
- `include_sources` (optional): Include source information (default: true)

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/chat/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What laptops are available and what are their specs?",
    "max_context_chunks": 5,
    "include_sources": true
  }'
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/api/chat/ask/"
data = {
    "question": "What laptops are available and what are their specs?",
    "max_context_chunks": 5,
    "include_sources": True
}

response = requests.post(url, json=data)
result = response.json()

print("Question:", result['question'])
print("Answer:", result['answer'])
print("Processing Time:", result['processing_time'], "seconds")

if 'sources' in result:
    print("\nSources:")
    for source in result['sources']:
        print(f"  - {source['type']}: {source.get('name', source.get('title'))}")
```

**Response:**
```json
{
  "question": "What laptops are available and what are their specs?",
  "answer": "Based on the product catalog, there is one laptop available. It is priced at $999.99 and comes with the following specifications: 16GB of RAM and 512GB SSD storage.",
  "processing_time": 2.34,
  "chat_history_id": "770e8400-e29b-41d4-a716-446655440002",
  "sources": [
    {
      "type": "json_database",
      "name": "Product Catalog",
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "score": 0.89
    }
  ],
  "context_chunks": [
    "Id: 1. Name: Laptop. Category: Electronics. Price: 999.99. Specs Ram: 16GB. Specs Storage: 512GB SSD"
  ]
}
```

#### Get Chat History

**Endpoint:** `GET /api/chat/history/`

**Example:**
```bash
curl http://localhost:8000/api/chat/history/
```

**Response:**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "question": "What laptops are available?",
    "answer": "There is one laptop available...",
    "context_used": [...],
    "sources": [...],
    "timestamp": "2024-01-15T10:35:00Z",
    "processing_time": 2.34,
    "tokens_used": 150
  }
]
```

#### Clear Chat History

**Endpoint:** `DELETE /api/chat/history/`

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/chat/history/
```

---

## Complete Workflow Example

### Python Script for Complete Workflow

```python
import requests
import time

BASE_URL = "http://localhost:8000/api"

def upload_document(file_path, title):
    """Upload a document."""
    url = f"{BASE_URL}/documents/"
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'title': title}
        response = requests.post(url, files=files, data=data)
    return response.json()

def upload_json_database(name, data):
    """Upload JSON database."""
    url = f"{BASE_URL}/json-database/"
    payload = {
        "name": name,
        "data": data
    }
    response = requests.post(url, json=payload)
    return response.json()

def ask_question(question, max_chunks=5):
    """Ask a question to the chatbot."""
    url = f"{BASE_URL}/chat/ask/"
    payload = {
        "question": question,
        "max_context_chunks": max_chunks,
        "include_sources": True
    }
    response = requests.post(url, json=payload)
    return response.json()

# Example usage
if __name__ == "__main__":
    # 1. Upload a document
    print("Uploading document...")
    doc_result = upload_document("research_paper.pdf", "AI Research Paper")
    print(f"Document uploaded: {doc_result['id']}")
    
    # Wait for processing
    time.sleep(2)
    
    # 2. Upload JSON database
    print("\nUploading JSON database...")
    products = [
        {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
        {"id": 2, "name": "Mouse", "price": 29.99, "category": "Accessories"}
    ]
    json_result = upload_json_database("Products", products)
    print(f"JSON database uploaded: {json_result['id']}")
    
    # Wait for processing
    time.sleep(2)
    
    # 3. Ask questions
    questions = [
        "What does the research paper say about AI?",
        "What products are available?",
        "How much does the laptop cost?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        result = ask_question(question)
        print(f"Answer: {result['answer']}")
        print(f"Processing time: {result['processing_time']:.2f}s")
        
        if result.get('sources'):
            print("Sources:")
            for source in result['sources']:
                print(f"  - {source['type']}: {source.get('name', source.get('title'))}")
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request (resource created)
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "error": "Description of the error"
}
```

**Validation Error Format:**
```json
{
  "field_name": [
    "Error message for this field"
  ]
}
```

---

## Rate Limiting

Currently, there are no rate limits. For production, implement rate limiting using:
- Django REST Framework throttling
- Django Ratelimit
- API Gateway rate limiting

---

## Best Practices

1. **Document Processing**: Upload documents during off-peak hours if processing large files
2. **Question Optimization**: Be specific in questions for better answers
3. **Context Chunks**: Start with 5 chunks, adjust based on answer quality
4. **Error Handling**: Always implement retry logic for network errors
5. **Pagination**: Use pagination parameters for large result sets

---

## Next Steps

1. Implement user authentication
2. Add WebSocket support for real-time chat
3. Create a web frontend
4. Set up background task processing with Celery
5. Deploy to production with Gunicorn/uWSGI
