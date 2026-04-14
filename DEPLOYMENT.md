# Deployment Guide

Complete guide for deploying the AI Chatbot system to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Performance Optimization](#performance-optimization)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ / Debian 10+ / macOS / Windows WSL2
- **Python**: 3.9 or higher
- **RAM**: Minimum 8GB (16GB+ recommended for larger models)
- **Storage**: 10GB+ free space (for models and indices)
- **GPU**: Optional but recommended for faster processing

### Software Dependencies

- Python 3.9+
- pip
- virtualenv or conda
- Git
- PostgreSQL (for production) or SQLite (for development)
- Nginx (for production)
- Supervisor or systemd (for process management)

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai_chatbot_system
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download NLTK Data

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 5. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

**Important .env settings for development:**
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
LLM_MODEL=gpt2  # Use smaller model for testing
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 6. Initialize Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000/api/` to see the API.

---

## Production Deployment

### Option 1: Traditional Server Deployment

#### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib supervisor
```

#### 2. Set Up PostgreSQL

```bash
# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE ai_chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'secure_password';
ALTER ROLE chatbot_user SET client_encoding TO 'utf8';
ALTER ROLE chatbot_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE chatbot_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ai_chatbot_db TO chatbot_user;
\q
```

#### 3. Deploy Application

```bash
# Create app directory
sudo mkdir -p /var/www/ai_chatbot
sudo chown $USER:$USER /var/www/ai_chatbot
cd /var/www/ai_chatbot

# Clone repository
git clone <repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### 4. Configure Environment

```bash
# Create production .env file
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=ai_chatbot_db
DATABASE_USER=chatbot_user
DATABASE_PASSWORD=secure_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EOF
```

#### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### 6. Run Migrations

```bash
python manage.py migrate
```

#### 7. Create Gunicorn Configuration

```bash
# Create Gunicorn systemd service
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=Gunicorn daemon for AI Chatbot
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai_chatbot
Environment="PATH=/var/www/ai_chatbot/venv/bin"
ExecStart=/var/www/ai_chatbot/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/ai_chatbot/gunicorn.sock \
          --timeout 300 \
          ai_chatbot.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable Gunicorn
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

#### 8. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/ai_chatbot
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/ai_chatbot/staticfiles/;
    }

    location /media/ {
        alias /var/www/ai_chatbot/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/ai_chatbot/gunicorn.sock;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ai_chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 9. Set Up SSL (with Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "300", "ai_chatbot.wsgi:application"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=ai_chatbot_db
      - POSTGRES_USER=chatbot_user
      - POSTGRES_PASSWORD=secure_password

  web:
    build: .
    command: gunicorn ai_chatbot.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 300
    volumes:
      - ./media:/app/media
      - ./faiss_indices:/app/faiss_indices
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./staticfiles:/var/www/static
      - ./media:/var/www/media
    depends_on:
      - web

volumes:
  postgres_data:
```

#### 3. Deploy

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## Performance Optimization

### 1. Model Selection

**For Limited Resources:**
- LLM: `gpt2` or `microsoft/phi-2`
- Embedding: `sentence-transformers/all-MiniLM-L6-v2`

**For Better Performance:**
- LLM: `mistralai/Mistral-7B-Instruct-v0.2`
- Embedding: `sentence-transformers/all-mpnet-base-v2`

### 2. GPU Acceleration

```python
# In settings.py, models will auto-detect GPU
# Ensure PyTorch CUDA is installed:
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 3. Model Quantization

```python
# For reduced memory usage, use 8-bit quantization
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_8bit=True,
    device_map="auto"
)
```

### 4. Caching Strategy

```python
# Implement Redis caching for embeddings
# Install: pip install django-redis

# In settings.py:
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 5. Background Task Processing

```bash
# Install Celery for async processing
pip install celery redis

# Configure in settings.py:
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### 6. Database Optimization

```python
# Add database indices
class Migration:
    operations = [
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['processed', '-uploaded_at']),
        ),
        migrations.AddIndex(
            model_name='chathistory',
            index=models.Index(fields=['-timestamp']),
        ),
    ]
```

---

## Monitoring and Maintenance

### 1. Logging

```python
# Configure production logging in settings.py
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ai_chatbot/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
    },
}
```

### 2. Health Checks

```bash
# Create health check endpoint
# In views.py:
@api_view(['GET'])
def health_check(request):
    return Response({'status': 'healthy'})
```

### 3. Monitoring Tools

- **Application**: Sentry for error tracking
- **Server**: Prometheus + Grafana
- **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana)

### 4. Backup Strategy

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR=/backups/postgresql
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U chatbot_user ai_chatbot_db > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -mtime +7 -delete  # Keep 7 days
```

### 5. Update Procedure

```bash
# Pull latest code
cd /var/www/ai_chatbot
git pull origin main

# Activate venv and update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up HTTPS/SSL
- [ ] Enable CSRF protection
- [ ] Implement rate limiting
- [ ] Set up firewall (UFW)
- [ ] Regular security updates
- [ ] Secure database credentials
- [ ] Implement user authentication
- [ ] Set up backup system
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets

---

## Troubleshooting

### Common Issues

**Issue: Out of Memory**
- Use smaller models (gpt2, phi-2)
- Enable model quantization
- Reduce batch sizes
- Add swap space

**Issue: Slow Response Times**
- Use GPU acceleration
- Reduce max_tokens
- Implement caching
- Use smaller embedding model

**Issue: FAISS Index Errors**
- Check file permissions
- Verify index directory exists
- Ensure sufficient disk space

**Issue: Database Connection Errors**
- Verify PostgreSQL is running
- Check database credentials
- Ensure database exists

---

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
- Email: support@yourdomain.com
