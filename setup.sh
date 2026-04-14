#!/bin/bash

# AI Chatbot System - Quick Setup Script
# This script automates the initial setup process

set -e  # Exit on error

echo "======================================="
echo "AI Chatbot System - Setup Script"
echo "======================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "Error: Python 3.9 or higher is required. Found: $python_version"
    exit 1
fi
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install requirements
echo ""
echo "Installing Python dependencies..."
echo "This may take several minutes..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Download NLTK data
echo ""
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"
echo "✓ NLTK data downloaded"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate SECRET_KEY
    secret_key=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    # Update .env with generated secret key (for macOS and Linux compatibility)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
    else
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
    fi
    
    echo "✓ .env file created with generated SECRET_KEY"
    echo ""
    echo "IMPORTANT: Please edit .env file to configure:"
    echo "  - LLM_MODEL (default: gpt2 for testing)"
    echo "  - EMBEDDING_MODEL"
    echo "  - Other settings as needed"
else
    echo ".env file already exists. Skipping..."
fi

# Create required directories
echo ""
echo "Creating required directories..."
mkdir -p media/documents
mkdir -p faiss_indices
mkdir -p staticfiles
echo "✓ Directories created"

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate
echo "✓ Database migrations completed"

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput > /dev/null 2>&1
echo "✓ Static files collected"

# Ask if user wants to create superuser
echo ""
read -p "Do you want to create a superuser account? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "======================================="
echo "Setup completed successfully!"
echo "======================================="
echo ""
echo "To start the development server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run server: python manage.py runserver"
echo "  3. Visit: http://localhost:8000/api/"
echo ""
echo "For admin interface:"
echo "  Visit: http://localhost:8000/admin/"
echo ""
echo "For API documentation, see: API_GUIDE.md"
echo ""
