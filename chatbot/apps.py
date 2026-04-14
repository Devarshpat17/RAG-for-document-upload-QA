"""
Configuration for the chatbot application.
"""

import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ChatbotConfig(AppConfig):
    """Configuration class for the chatbot app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    verbose_name = 'AI Chatbot'
    
    def ready(self):
        """
        Perform initialization when Django starts.
        
        This is where you can register signals, perform startup tasks, etc.
        """
        # Optionally pre-load the embedding model to avoid first-request timeout
        # Commented out by default - uncomment if you want auto-warmup
        # try:
        #     logger.info("Pre-loading embedding model...")
        #     from chatbot.services import EmbeddingService
        #     embedding_service = EmbeddingService()
        #     test_embedding = embedding_service.encode("warmup test")
        #     logger.info(f"Embedding model loaded successfully (dimension: {embedding_service.dimension})")
        # except Exception as e:
        #     logger.error(f"Failed to pre-load embedding model: {e}")

