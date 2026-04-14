# Quick Start Guide

Get the AI Chatbot system running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Start the server
source venv/bin/activate
python manage.py runserver
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Set up environment
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

## First Steps

### 1. Access the API

Open your browser and visit:
- API Root: http://localhost:8000/api/
- Admin Panel: http://localhost:8000/admin/ (if you created a superuser)

### 2. Upload a Document

```bash
# Create a test document
echo "Artificial Intelligence is transforming the world." > test.txt

# Upload it
curl -X POST http://localhost:8000/api/documents/ \
  -F "file=@test.txt" \
  -F "title=Test Document"
```

### 3. Upload JSON Data

```bash
curl -X POST http://localhost:8000/api/json-database/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Products",
    "data": [
      {"id": 1, "name": "Widget", "price": 19.99},
      {"id": 2, "name": "Gadget", "price": 29.99}
    ]
  }'
```

### 4. Ask a Question

```bash
curl -X POST http://localhost:8000/api/chat/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is AI?",
    "max_context_chunks": 5
  }'
```

## Run Example Script

The included example script demonstrates the complete workflow:

```bash
# Make sure the server is running in another terminal
python example_usage.py
```

## Configuration Tips

### For Testing (Faster, Less Accurate)
```env
LLM_MODEL=gpt2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=256
```

### For Production (Slower, More Accurate)
```env
LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
MAX_TOKENS=512
```

### For GPU Acceleration
```bash
# Install CUDA-enabled PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## Common Issues

### Issue: "Out of memory"
**Solution**: Use a smaller model (gpt2 or phi-2)

### Issue: "Module not found"
**Solution**: Make sure you're in the virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Port already in use"
**Solution**: Use a different port
```bash
python manage.py runserver 8001
```

### Issue: Slow responses
**Solution**: 
1. Use GPU acceleration
2. Reduce max_tokens in .env
3. Use a smaller model

## Next Steps

1. **Read the Documentation**:
   - [README.md](README.md) - Full overview
   - [API_GUIDE.md](API_GUIDE.md) - API usage examples
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment

2. **Explore the Admin Interface**:
   - View uploaded documents
   - Manage JSON databases
   - Review chat history

3. **Try Different Models**:
   - Experiment with different LLM models
   - Compare embedding models
   - Tune generation parameters

4. **Build a Frontend**:
   - Create a web interface
   - Add real-time chat
   - Implement user authentication

## Support

For help:
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system details
- Review [API_GUIDE.md](API_GUIDE.md) for API examples
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup

## Project Structure

```
ai_chatbot_system/
├── README.md              # Project overview
├── QUICKSTART.md          # This file
├── API_GUIDE.md          # API documentation
├── ARCHITECTURE.md       # Technical details
├── DEPLOYMENT.md         # Production guide
├── requirements.txt      # Dependencies
├── manage.py            # Django management
├── setup.sh             # Setup script
├── example_usage.py     # Example code
├── ai_chatbot/          # Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── chatbot/             # Main app
    ├── models.py        # Database models
    ├── views.py         # API endpoints
    ├── serializers.py   # Data serialization
    ├── services/        # Business logic
    │   ├── document_service.py
    │   ├── embedding_service.py
    │   ├── retrieval_service.py
    │   ├── llm_service.py
    │   └── json_service.py
    └── tests.py         # Unit tests
```

Happy coding! 🚀
