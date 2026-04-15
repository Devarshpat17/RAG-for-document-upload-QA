# AI Chatbot System - Complete Documentation

**AI-Powered Chatbot System with RAG** - A Django-based AI chatbot that answers questions from uploaded documents and structured JSON databases using open-source LLMs and Retrieval-Augmented Generation.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [System Architecture](#system-architecture)
4. [Configuration](#configuration)
5. [API Endpoints](#api-endpoints)
6. [Frontend/UI Guide](#frontendu-guide)
7. [Troubleshooting](#troubleshooting)
8. [Deployment](#deployment)
9. [Quick Restart Commands](#quick-restart-commands)

---

## Quick Start

### Prerequisites
- Python 3.9+
- pip & virtualenv
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

### 5-Minute Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# 4. Set up environment
cp .env.example .env

# 5. Initialize database
python manage.py makemigrations
python manage.py migrate

# 6. Warm up services (optional but recommended)
python manage.py warmup_services

# 7. Run server
python manage.py runserver
```

Visit: **http://localhost:8000** for the UI or **http://localhost:8000/api/** for the API.

---

## Installation

### Option 1: Automated Setup (Recommended)

```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
python manage.py runserver
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run server
python manage.py runserver
```

---

## System Architecture

### Overview

```
┌─────────────────────────────────────────────────┐
│  Frontend UI (Web Interface)                    │
│  Dashboard • Chat • Documents • JSON DB • History│
└────────────────────┬────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────┐
│  Django REST Framework                          │
│  ├─ Document ViewSet                            │
│  ├─ JSON Database ViewSet                       │
│  └─ Chat ViewSet                                │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  Service Layer                                  │
│  ├─ DocumentService (text extraction)           │
│  ├─ EmbeddingService (sentence-transformers)   │
│  ├─ RetrievalService (FAISS search)            │
│  ├─ LLMService (HuggingFace models)            │
│  └─ JSONService (structured data)              │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  Data Layer                                     │
│  ├─ SQLite DB (metadata, history)              │
│  ├─ FAISS (vector embeddings)                  │
│  └─ File System (documents)                    │
└─────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Django 4.2+, Django REST Framework
- **Vector DB**: FAISS
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: HuggingFace Transformers (gpt2, Mistral, LLaMA support)
- **Document Processing**: PyPDF2, pdfplumber, python-docx
- **Text Processing**: NLTK, spaCy
- **Frontend**: Vanilla JavaScript, HTML5, CSS3 (Dark theme)

### RAG Pipeline Flow

1. **Document Upload** → Text extraction & chunking
2. **Embedding Generation** → Convert chunks to vectors
3. **FAISS Indexing** → Store vectors for fast search
4. **Query Processing** → Embed user question
5. **Similarity Retrieval** → Find relevant chunks
6. **Context Aggregation** → Combine top chunks
7. **LLM Answer Generation** → Generate response with context

---

## Configuration

### Environment Variables (.env)

```bash
# Django Settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# LLM Configuration
LLM_MODEL=gpt2                              # or mistralai/Mistral-7B-Instruct-v0.2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=512
TEMPERATURE=0.7

# FAISS Configuration
FAISS_INDEX_TYPE=Flat  # Options: Flat, IVFFlat, HNSW
SIMILARITY_TOP_K=5

# Document Processing
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_FILE_SIZE_MB=10
```

### Model Selection

**For Testing (Fast):**
```env
LLM_MODEL=gpt2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=256
```

**For Production (Better Quality):**
```env
LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
MAX_TOKENS=512
```

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/
```

### Document Management

#### Upload Document
```bash
POST /api/documents/
Content-Type: multipart/form-data

curl -X POST http://localhost:8000/api/documents/ \
  -F "file=@document.pdf" \
  -F "title=My Document"
```

#### List Documents
```bash
GET /api/documents/

curl http://localhost:8000/api/documents/
```

#### Get Document Details
```bash
GET /api/documents/{id}/

curl http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/
```

#### Delete Document
```bash
DELETE /api/documents/{id}/

curl -X DELETE http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/
```

### JSON Database

#### Upload JSON Data
```bash
POST /api/json-database/
Content-Type: application/json

curl -X POST http://localhost:8000/api/json-database/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Data",
    "description": "Customer records",
    "data": [
      {"name": "John", "age": 30, "city": "NYC"},
      {"name": "Jane", "age": 28, "city": "LA"}
    ]
  }'
```

#### List Databases
```bash
GET /api/json-database/

curl http://localhost:8000/api/json-database/
```

#### Delete Database
```bash
DELETE /api/json-database/{id}/

curl -X DELETE http://localhost:8000/api/json-database/{id}/
```

### Chat

#### Ask Question
```bash
POST /api/chat/ask/
Content-Type: application/json

curl -X POST http://localhost:8000/api/chat/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is mentioned in the documents?",
    "max_context_chunks": 5,
    "include_sources": true
  }'
```

**Response:**
```json
{
  "question": "What is mentioned in the documents?",
  "answer": "The documents discuss...",
  "sources": [
    {"document": "doc_id", "title": "Document Title"}
  ],
  "processing_time": 2.345
}
```

#### Get Chat History
```bash
GET /api/chat/history/

curl http://localhost:8000/api/chat/history/
```

#### Clear Chat History
```bash
DELETE /api/chat/clear_history/

curl -X DELETE http://localhost:8000/api/chat/clear_history/
```

---

## Frontend/UI Guide

### Features

✅ **Modern Dark Theme** - Orange (#ff8c00) primary, Purple (#7c3aed) secondary  
✅ **Responsive Dashboard** - Real-time statistics and system info  
✅ **Document Upload** - Drag & drop PDF/TXT files  
✅ **Chat Interface** - Ask questions with context retrieval  
✅ **JSON Database Management** - Upload and query structured data  
✅ **Chat History** - Track all interactions  

### UI Testing

#### 1. Dashboard
- Navigate to Dashboard page
- See statistics: Documents Uploaded, JSON Databases, Chat Messages
- View recent documents with processing status

#### 2. Document Upload
1. Go to Documents page
2. Enter title
3. Upload PDF or TXT file (max 10MB)
4. File shows as "Processing" then "Ready"
5. Can delete documents

**Expected Result**: Document appears in list with chunk count and size

#### 3. JSON Database
1. Go to JSON Database page
2. Enter name and description
3. Paste JSON data (array of objects or single object)
4. Database shows record count

**Expected Result**: Database appears with processing status

#### 4. Chat
1. Go to Chat page
2. Ask a question about documents/data
3. System retrieves relevant context
4. LLM generates answer with sources
5. Message appears in history

**Expected Result**: Quick response with accurate context

#### 5. Chat History
1. View all previous conversations
2. See question, answer, date, processing time
3. Clear all history with confirmation

---

## Troubleshooting

### Issue: "Out of Memory" Error

**Cause**: Model too large for available RAM

**Solutions**:
```bash
# Use smaller model
LLM_MODEL=gpt2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Or enable GPU acceleration
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Issue: First Request Timeout (>60s)

**Cause**: Embedding model downloading/loading

**Solution**:
```bash
# Pre-warm services before testing
python manage.py warmup_services
python example_usage.py
```

### Issue: "Port already in use"

**Solution**:
```bash
# Use different port
python manage.py runserver 8001
```

### Issue: "ModuleNotFoundError"

**Cause**: Missing virtual environment activation

**Solution**:
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Issue: Document Upload Fails with 500 Error

**Cause**: 
- Embedding model not loaded
- File too large
- Invalid file format

**Solution**:
```bash
# Check file size (max 10MB)
# Use PDF or TXT only
# Pre-warm services
python manage.py warmup_services
```

### Issue: Slow Chat Responses

**Solutions**:
1. Use smaller model (gpt2 instead of Mistral)
2. Reduce MAX_TOKENS in .env
3. Enable GPU acceleration
4. Reduce SIMILARITY_TOP_K

---

## Deployment

### Production Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Set DEBUG=False
- [ ] Configure PostgreSQL instead of SQLite
- [ ] Set up Nginx as reverse proxy
- [ ] Use Gunicorn/uWSGI as application server
- [ ] Enable HTTPS with SSL certificate
- [ ] Set up logging and monitoring
- [ ] Create backup strategy for FAISS indices
- [ ] Configure allowed hosts

### Production Deployment Steps

```bash
# 1. Install system dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv postgresql nginx supervisor

# 2. Set up application directory
sudo mkdir -p /var/www/ai_chatbot
cd /var/www/ai_chatbot

# 3. Clone and setup
git clone <repo> .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure PostgreSQL
sudo -u postgres psql
CREATE DATABASE ai_chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_chatbot_db TO chatbot_user;

# 5. Update .env for production
cp .env.example .env
# Edit: DEBUG=False, SECRET_KEY, DATABASE settings, ALLOWED_HOSTS

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Run migrations
python manage.py migrate

# 8. Set up Gunicorn service with Supervisor
# See supervisor configuration below
```

### Supervisor Configuration

Create `/etc/supervisor/conf.d/ai_chatbot.conf`:
```ini
[program:ai_chatbot]
directory=/var/www/ai_chatbot
command=/var/www/ai_chatbot/venv/bin/gunicorn ai_chatbot.wsgi:application --bind 127.0.0.1:8000 --workers 4
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/ai_chatbot/access.log
stderr_logfile=/var/log/ai_chatbot/error.log
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /static/ {
        alias /var/www/ai_chatbot/staticfiles/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Quick Restart Commands

### Activate & Run Server

```bash
# Windows PowerShell
cd d:\NIRMA\ai_chatbot_system
.\venv\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000

# Mac/Linux
cd ai_chatbot_system
source venv/bin/activate
python manage.py runserver
```

### Full Reset

```bash
# Remove database
rm db.sqlite3

# Clear indices
rm -r faiss_indices
mkdir faiss_indices

# Fresh migrations
rm chatbot/migrations/0*.py

# Restart
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test chatbot

# With verbose output
python manage.py test -v 2
```

### Create Superuser

```bash
python manage.py createsuperuser
# Then visit: http://localhost:8000/admin/
```

---

## Common Workflows

### Upload Document & Ask Question

```bash
# 1. Start server
python manage.py runserver

# 2. Upload document
curl -X POST http://localhost:8000/api/documents/ \
  -F "file=@myfile.pdf" \
  -F "title=My PDF"

# 3. Wait for processing (status changes to "Ready")
curl http://localhost:8000/api/documents/

# 4. Ask question
curl -X POST http://localhost:8000/api/chat/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is in this document?"}'
```

### Use Example Script

```bash
# Run comprehensive example
python example_usage.py

# Run simple API tests
python test_api.py
```

---

## File Structure

```
ai_chatbot_system/
├── README.md                      # Main readme
├── DOCUMENTATION.md               # This file
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── manage.py                      # Django management
├── setup.sh                       # Automated setup script
├── example_usage.py               # Complete example
├── test_api.py                    # API tests
│
├── ai_chatbot/                    # Main Django project
│   ├── settings.py                # Configuration
│   ├── urls.py                    # URL routing
│   ├── wsgi.py                    # WSGI app
│   └── asgi.py                    # ASGI app
│
├── chatbot/                       # Chatbot app
│   ├── models.py                  # Database models
│   ├── views.py                   # API views
│   ├── serializers.py             # DRF serializers
│   ├── urls.py                    # App URLs
│   ├── admin.py                   # Admin config
│   ├── tests.py                   # Unit tests
│   ├── services/                  # Business logic
│   │   ├── document_service.py
│   │   ├── embedding_service.py
│   │   ├── retrieval_service.py
│   │   ├── llm_service.py
│   │   └── json_service.py
│   └── management/
│       └── commands/
│           └── warmup_services.py # Warmup command
│
├── templates/
│   └── base.html                  # Main UI template
│
├── static/
│   ├── css/
│   │   └── main.css               # Dark theme styles
│   └── js/
│       └── app.js                 # Frontend logic
│
├── media/                         # Uploaded documents
├── faiss_indices/                 # Vector indices
└── db.sqlite3                     # Development database
```

---

**For additional help or issues, check the troubleshooting section or review the source code documentation in each module.**
