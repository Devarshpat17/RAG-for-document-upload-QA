# System Architecture Documentation

## Overview

The AI Chatbot System is a Django-based application that implements Retrieval-Augmented Generation (RAG) for question-answering from documents and structured data. The system uses open-source models from HuggingFace and FAISS for efficient vector search.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  (API Consumers, Frontend Apps, CLI Tools, Example Scripts)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Django REST Framework                      │
│                        (API Layer)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Document    │  │  JSON DB     │  │    Chat      │         │
│  │  ViewSet     │  │  ViewSet     │  │  ViewSet     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Business Logic
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Document    │  │  Embedding   │  │  Retrieval   │         │
│  │  Service     │  │  Service     │  │  Service     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │    LLM       │  │    JSON      │                           │
│  │  Service     │  │  Service     │                           │
│  └──────────────┘  └──────────────┘                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Data Access
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │    FAISS     │  │  File System │         │
│  │  (Metadata)  │  │  (Vectors)   │  │  (Documents) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ External Services
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   HuggingFace Models                            │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │  Embedding Models    │  │    LLM Models        │           │
│  │  (sentence-trans.)   │  │  (Mistral, LLaMA)    │           │
│  └──────────────────────┘  └──────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer (Django REST Framework)

#### Document ViewSet
- **Responsibility**: Handle document upload, processing, and management
- **Endpoints**:
  - `POST /api/documents/` - Upload document
  - `GET /api/documents/` - List documents
  - `GET /api/documents/{id}/` - Get document details
  - `DELETE /api/documents/{id}/` - Delete document
  - `POST /api/documents/{id}/reprocess/` - Reprocess document
- **Key Features**:
  - Multipart file upload
  - Automatic text extraction
  - Async processing (ready for Celery integration)

#### JSON Database ViewSet
- **Responsibility**: Handle structured data upload and indexing
- **Endpoints**:
  - `POST /api/json-database/` - Upload JSON data
  - `GET /api/json-database/` - List databases
  - `GET /api/json-database/{id}/` - Get database details
  - `DELETE /api/json-database/{id}/` - Delete database
- **Key Features**:
  - JSON validation
  - Automatic text conversion
  - Nested structure support

#### Chat ViewSet
- **Responsibility**: Handle question-answering interactions
- **Endpoints**:
  - `POST /api/chat/ask/` - Ask a question
  - `GET /api/chat/history/` - Get chat history
  - `DELETE /api/chat/history/` - Clear history
- **Key Features**:
  - Multi-source retrieval
  - Context aggregation
  - Answer generation

### 2. Service Layer

#### Document Service
**File**: `chatbot/services/document_service.py`

**Responsibilities**:
- Text extraction from PDF and TXT files
- Text preprocessing and cleaning
- Intelligent text chunking with overlap
- Document statistics calculation

**Key Methods**:
- `extract_text_from_file()` - Extract text from various formats
- `chunk_text()` - Split text into overlapping chunks
- `preprocess_text()` - Clean and normalize text
- `get_document_stats()` - Calculate document metrics

**Design Decisions**:
- Uses both PyPDF2 and pdfplumber for robust PDF extraction
- Implements sliding window chunking for context preservation
- Configurable chunk size and overlap via settings

#### Embedding Service
**File**: `chatbot/services/embedding_service.py`

**Responsibilities**:
- Load and manage embedding models
- Generate vector embeddings for text
- Batch processing for efficiency
- Similarity calculation

**Key Methods**:
- `encode()` - Generate embeddings for text(s)
- `encode_query()` - Encode search queries
- `encode_batch()` - Batch processing
- `similarity()` - Calculate cosine similarity

**Design Decisions**:
- Singleton pattern to avoid multiple model loads
- Automatic GPU detection and utilization
- Normalized embeddings for cosine similarity
- Lazy loading of models

#### Retrieval Service
**File**: `chatbot/services/retrieval_service.py`

**Responsibilities**:
- Create and manage FAISS indices
- Add embeddings to indices
- Perform similarity search
- Index persistence and loading

**Key Methods**:
- `create_index()` - Initialize FAISS index
- `add_embeddings()` - Add vectors to index
- `search()` - Find similar vectors
- `save_index()` / `load_index()` - Persistence
- `merge_search_results()` - Combine multi-index results

**Design Decisions**:
- Support for multiple FAISS index types (Flat, IVF, HNSW)
- Separate metadata storage with pickle
- Index caching for performance
- Automatic index training for IVF indices

#### LLM Service
**File**: `chatbot/services/llm_service.py`

**Responsibilities**:
- Load and manage LLM models
- Generate responses with context
- Prompt engineering
- Token management

**Key Methods**:
- `generate_response()` - Generate answer with context
- `_build_prompt()` - Format prompts for different models
- `_extract_answer()` - Clean model output
- `estimate_tokens()` - Token counting

**Design Decisions**:
- Model-specific prompt templates (Mistral, LLaMA, Phi, GPT-2)
- Singleton pattern for model reuse
- Configurable generation parameters
- Support for both CPU and GPU inference

#### JSON Service
**File**: `chatbot/services/json_service.py`

**Responsibilities**:
- Convert JSON to searchable text
- Handle nested structures
- Extract key fields
- Data validation

**Key Methods**:
- `process_json_data()` - Convert JSON to chunks
- `_record_to_text()` - Flatten JSON structure
- `validate_json_data()` - Data validation
- `extract_searchable_fields()` - Prioritize fields

**Design Decisions**:
- Recursive flattening of nested objects
- Readable key name conversion
- Preserves original records in metadata
- Flexible field prioritization

### 3. Data Layer

#### PostgreSQL (or SQLite)
**Models**: `chatbot/models.py`

**Document Model**:
- Stores document metadata
- Tracks processing status
- Links to FAISS index

**JSONDatabase Model**:
- Stores JSON data
- Tracks record count
- Links to FAISS index

**ChatHistory Model**:
- Records all interactions
- Stores context and sources
- Tracks performance metrics

#### FAISS Indices
**Storage**: `faiss_indices/`

**Index Files**:
- `{index_id}.index` - FAISS index binary
- `{index_id}.metadata` - Associated metadata (pickle)

**Index Types Supported**:
- **Flat**: Exact search, best for small datasets
- **FlatIP**: Inner product (cosine similarity)
- **IVFFlat**: Inverted file, faster for large datasets
- **HNSW**: Hierarchical graph, fastest approximate search

#### File System
**Storage**: `media/documents/`

**Organization**:
```
media/
└── documents/
    └── YYYY/
        └── MM/
            └── DD/
                └── filename.ext
```

## Data Flow

### Document Upload Flow

```
1. Client uploads document
   ↓
2. DocumentViewSet validates file
   ↓
3. Django saves file to media storage
   ↓
4. DocumentService extracts text
   ↓
5. DocumentService chunks text
   ↓
6. EmbeddingService generates embeddings
   ↓
7. RetrievalService creates/updates FAISS index
   ↓
8. Index saved to disk
   ↓
9. Document marked as processed
   ↓
10. Response returned to client
```

### Question-Answering Flow

```
1. Client asks question
   ↓
2. ChatViewSet receives request
   ↓
3. EmbeddingService encodes query
   ↓
4. RetrievalService searches all indices
   ↓
5. Top results merged and ranked
   ↓
6. Context chunks extracted
   ↓
7. LLMService builds prompt with context
   ↓
8. LLM generates answer
   ↓
9. ChatHistory record created
   ↓
10. Response returned with answer and sources
```

## Scalability Considerations

### Current Architecture (Single Server)
- **Concurrent Users**: ~10-50
- **Documents**: Up to 10,000
- **Response Time**: 2-5 seconds per query

### Scaling Strategies

#### Horizontal Scaling
1. **Load Balancer** (Nginx/HAProxy)
2. **Multiple Application Servers**
3. **Shared Storage** (NFS/S3 for media files)
4. **Centralized Database** (PostgreSQL with replication)
5. **Distributed Cache** (Redis/Memcached)

#### Vertical Scaling
1. **GPU Acceleration** (NVIDIA GPUs for model inference)
2. **More RAM** (for larger models and indices)
3. **SSD Storage** (faster index access)

#### Async Processing
1. **Celery** for background tasks
2. **RabbitMQ/Redis** as message broker
3. **Separate workers** for document processing
4. **Task queue** for high-volume ingestion

#### Caching Strategy
1. **Embedding Cache** (Redis)
   - Cache frequently accessed embeddings
   - TTL-based expiration
2. **Model Cache** (Memory)
   - Keep models loaded in memory
   - LRU eviction for multiple models
3. **Query Cache** (Redis)
   - Cache common queries
   - Invalidate on data updates

## Security

### Authentication & Authorization
- Token-based auth (DRF TokenAuthentication)
- JWT for stateless auth
- Role-based access control (future)

### Data Security
- HTTPS/TLS for all communications
- Encrypted database connections
- Secure file upload validation
- Rate limiting per user/IP

### API Security
- CSRF protection
- CORS configuration
- Input validation
- SQL injection prevention (Django ORM)

## Monitoring & Observability

### Metrics to Track
1. **Performance**:
   - Query response time
   - Document processing time
   - Model inference time
   - FAISS search latency

2. **Resource Usage**:
   - CPU utilization
   - Memory usage
   - GPU utilization
   - Disk I/O

3. **Business Metrics**:
   - Questions per day
   - Documents processed
   - Average answer quality (user feedback)
   - Cache hit rate

### Logging
- **Application Logs**: Django logging framework
- **Access Logs**: Nginx/Apache logs
- **Error Tracking**: Sentry integration
- **Audit Logs**: User actions, data changes

## Future Enhancements

### Planned Features
1. **Multi-language Support**
   - Language detection
   - Multilingual embeddings
   - Translation integration

2. **Advanced Document Types**
   - DOCX, XLSX, PPT support
   - Image OCR
   - Audio transcription

3. **Fine-tuning**
   - Domain-specific model fine-tuning
   - Custom embedding models
   - Feedback-based improvement

4. **Analytics Dashboard**
   - Usage statistics
   - Popular queries
   - Answer quality metrics

5. **Real-time Features**
   - WebSocket chat interface
   - Streaming responses
   - Live document updates

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Web Framework | Django 4.2 | Backend framework |
| API | Django REST Framework | RESTful APIs |
| Database | PostgreSQL / SQLite | Metadata storage |
| Vector DB | FAISS | Similarity search |
| Embeddings | sentence-transformers | Text embeddings |
| LLM | HuggingFace Transformers | Response generation |
| Document Processing | PyPDF2, pdfplumber | Text extraction |
| NLP | NLTK | Text processing |
| Deployment | Gunicorn, Nginx | WSGI server, reverse proxy |

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Comprehensive docstrings
- Meaningful variable names

### Testing
- Unit tests for services
- Integration tests for APIs
- Test coverage > 80%

### Documentation
- Inline comments for complex logic
- API documentation (OpenAPI/Swagger)
- Architecture updates with changes
- Deployment runbooks

### Version Control
- Feature branches
- Pull request reviews
- Semantic versioning
- Changelog maintenance
