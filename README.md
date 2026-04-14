# AI-Powered Chatbot System with RAG

A Django-based AI chatbot system that answers natural language questions from uploaded documents (PDF, TXT) and structured JSON databases using open-source Large Language Models and Retrieval-Augmented Generation (RAG).

## Features

- **Document Processing**: Upload and process PDF and TXT documents
- **Text Extraction**: Automatic text extraction from various document formats
- **Intelligent Chunking**: Smart text chunking with overlap for context preservation
- **Vector Embeddings**: Generate embeddings using HuggingFace models (sentence-transformers)
- **FAISS Indexing**: Efficient vector similarity search with FAISS
- **JSON Database Support**: Convert JSON records to searchable embeddings
- **RAG Pipeline**: Retrieve relevant context and generate answers using open-source LLMs
- **RESTful API**: Complete API for document management and chat interactions
- **Modular Architecture**: Clean separation of concerns for easy maintenance and extension

## Architecture Overview

```
┌─────────────────┐
│   Django REST   │
│   Framework     │
└────────┬────────┘
         │
    ┌────┴────────────────────────────────┐
    │                                     │
┌───▼──────────┐                  ┌──────▼─────┐
│  Document    │                  │   Chat     │
│  Management  │                  │   Service  │
└───┬──────────┘                  └──────┬─────┘
    │                                    │
    │  ┌─────────────────────────────────┤
    │  │                                 │
┌───▼──▼─────────┐  ┌──────────────┐  ┌─▼────────────┐
│  Embedding     │  │   FAISS      │  │  LLM         │
│  Service       │─>│   Index      │<─│  Service     │
└────────────────┘  └──────────────┘  └──────────────┘
```

## Technology Stack

- **Backend**: Django 4.2+
- **API**: Django REST Framework
- **Vector Database**: FAISS
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: HuggingFace Transformers (Mistral, LLaMA, Phi support)
- **Document Processing**: PyPDF2, python-docx
- **Text Processing**: NLTK, spaCy

## Installation

### Prerequisites

- Python 3.9+
- pip
- virtualenv (recommended)

### Setup

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Initialize NLTK data**:
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

4. **Run migrations**:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser** (optional):
```bash
python manage.py createsuperuser
```

6. **Run development server**:
```bash
python manage.py runserver
```

## API Endpoints

### Document Management

- `POST /api/documents/upload/` - Upload a document (PDF, TXT)
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}/` - Get document details
- `DELETE /api/documents/{id}/` - Delete a document

### JSON Database

- `POST /api/json-database/upload/` - Upload JSON data
- `GET /api/json-database/` - List all JSON databases
- `DELETE /api/json-database/{id}/` - Delete a JSON database

### Chat

- `POST /api/chat/ask/` - Ask a question
- `GET /api/chat/history/` - Get chat history
- `DELETE /api/chat/history/` - Clear chat history

## Usage Examples

### 1. Upload a Document

```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -F "file=@document.pdf" \
  -F "title=My Document"
```

### 2. Upload JSON Database

```bash
curl -X POST http://localhost:8000/api/json-database/upload/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Products Database",
    "data": [
      {"id": 1, "name": "Product A", "description": "High-quality widget"},
      {"id": 2, "name": "Product B", "description": "Premium gadget"}
    ]
  }'
```

### 3. Ask a Question

```bash
curl -X POST http://localhost:8000/api/chat/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What products are available?",
    "max_context_chunks": 5
  }'
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# LLM Configuration
LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=512
TEMPERATURE=0.7

# FAISS Configuration
FAISS_INDEX_TYPE=Flat
SIMILARITY_TOP_K=5

# Document Processing
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Supported LLM Models

The system supports various open-source models from HuggingFace:

- **Mistral**: `mistralai/Mistral-7B-Instruct-v0.2`
- **LLaMA**: `meta-llama/Llama-2-7b-chat-hf` (requires approval)
- **Phi**: `microsoft/phi-2`
- **GPT-2**: `gpt2` (smaller, for testing)

## Project Structure

```
ai_chatbot_system/
├── ai_chatbot/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── chatbot/                    # Main application
│   ├── models.py              # Database models
│   ├── serializers.py         # DRF serializers
│   ├── views.py               # API views
│   ├── urls.py                # URL routing
│   └── services/              # Business logic layer
│       ├── document_service.py    # Document processing
│       ├── embedding_service.py   # Embedding generation
│       ├── retrieval_service.py   # FAISS-based retrieval
│       ├── llm_service.py         # LLM interaction
│       └── json_service.py        # JSON database handling
├── media/                      # Uploaded files
├── faiss_indices/             # FAISS index storage
├── requirements.txt           # Python dependencies
└── manage.py                  # Django management script
```

## Key Components

### 1. Document Service
Handles document upload, text extraction, and preprocessing. Supports PDF and TXT formats with intelligent text cleaning and validation.

### 2. Embedding Service
Generates vector embeddings using sentence-transformers. Implements batching for efficiency and caching for frequently accessed embeddings.

### 3. Retrieval Service
Manages FAISS indices for fast similarity search. Supports multiple index types and automatic index persistence.

### 4. LLM Service
Interfaces with HuggingFace models for text generation. Implements prompt engineering, context management, and response formatting.

### 5. JSON Service
Converts structured JSON data into searchable text embeddings. Supports nested structures and custom field mapping.

## Development Notes

### Code Quality
- All code follows PEP 8 style guidelines
- Comprehensive docstrings for all classes and methods
- Type hints for better IDE support
- Extensive inline comments explaining complex logic

### Testing
Run tests with:
```bash
python manage.py test
```

### Performance Optimization
- Batch processing for embeddings
- Index caching to reduce disk I/O
- Lazy loading of LLM models
- Efficient chunking algorithms

### Future Enhancements
- Support for more document formats (DOCX, CSV, etc.)
- Multi-language support
- Fine-tuning capabilities
- User authentication and authorization
- Real-time chat interface
- Advanced analytics and monitoring

## Troubleshooting

### Memory Issues
If you encounter out-of-memory errors:
- Reduce `CHUNK_SIZE` in settings
- Use a smaller embedding model
- Enable GPU acceleration if available

### Slow Response Times
- Decrease `max_context_chunks` in queries
- Use a lighter LLM model (e.g., GPT-2 for testing)
- Pre-compute and cache embeddings

### Model Download Issues
Models are downloaded from HuggingFace on first use. Ensure:
- Stable internet connection
- Sufficient disk space (~5GB for Mistral-7B)
- HuggingFace credentials for gated models

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Contact

For questions or support, please open an issue on GitHub.
