"""
Django management command to pre-load embedding model.

This command pre-loads the sentence-transformers model to avoid
timeout issues on first API request.
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from chatbot.services import EmbeddingService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to warm up the embedding service."""
    
    help = 'Pre-load embedding model to avoid timeout on first request'
    
    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(
            self.style.SUCCESS('Initializing AI services...')
        )
        
        try:
            # Initialize the embedding service
            self.stdout.write('Loading embedding model...')
            
            embedding_service = EmbeddingService()
            model_name = settings.AI_CONFIG['EMBEDDING_MODEL']
            
            self.stdout.write(f'Using model: {model_name}')
            
            # Pre-encode a test string to warm up the model
            test_text = "This is a test sentence for warming up the embedding model."
            embedding = embedding_service.encode(test_text)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Embedding service initialized successfully!\n'
                    f'  Model: {model_name}\n'
                    f'  Embedding dimension: {embedding_service.dimension}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to initialize services: {e}')
            )
            raise
