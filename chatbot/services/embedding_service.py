"""
Embedding generation service using HuggingFace sentence-transformers.

This module handles:
- Loading and managing embedding models
- Generating vector embeddings for text
- Batch processing for efficiency
- Embedding dimension management
"""

import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using sentence-transformers.
    
    This service provides a singleton instance of the embedding model
    and methods for generating embeddings from text efficiently.
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Implement singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding service and load the model."""
        if self._model is None:
            self.model_name = settings.AI_CONFIG['EMBEDDING_MODEL']
            self.dimension = settings.AI_CONFIG['EMBEDDING_DIMENSION']
            self._load_model()
    
    def _load_model(self):
        """
        Load the sentence-transformer model.
        
        This method loads the model on first use and caches it for subsequent calls.
        """
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            
            # Verify embedding dimension
            test_embedding = self._model.encode("test")
            actual_dimension = len(test_embedding)
            
            if actual_dimension != self.dimension:
                logger.warning(
                    f"Expected embedding dimension {self.dimension}, "
                    f"but model produces {actual_dimension}. Updating config."
                )
                self.dimension = actual_dimension
            
            logger.info(
                f"Successfully loaded embedding model. "
                f"Embedding dimension: {self.dimension}"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise Exception(f"Could not load embedding model {self.model_name}: {e}")
    
    def get_model(self) -> SentenceTransformer:
        """
        Get the loaded embedding model.
        
        Returns:
            The sentence-transformer model instance
        """
        if self._model is None:
            self._load_model()
        return self._model
    
    def encode(self, texts: Union[str, List[str]], 
               batch_size: int = 32,
               show_progress: bool = False,
               normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text string or list of texts
            batch_size: Number of texts to process at once
            show_progress: Whether to show progress bar
            normalize: Whether to normalize embeddings to unit length
            
        Returns:
            Numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        # Validate inputs
        if not texts:
            logger.warning("Attempted to encode empty text list")
            return np.array([])
        
        # Filter out empty strings
        valid_texts = [t for t in texts if t and t.strip()]
        if len(valid_texts) < len(texts):
            logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} empty texts"
            )
        
        if not valid_texts:
            return np.array([])
        
        try:
            logger.info(f"Generating embeddings for {len(valid_texts)} text(s)")
            
            # Generate embeddings
            embeddings = self._model.encode(
                valid_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=normalize,
                convert_to_numpy=True
            )
            
            logger.info(
                f"Successfully generated embeddings with shape {embeddings.shape}"
            )
            
            # Return single embedding if input was single string
            if single_input:
                return embeddings[0]
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise Exception(f"Embedding generation failed: {e}")
    
    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a search query.
        
        This is a convenience method for encoding single queries.
        
        Args:
            query: The search query text
            normalize: Whether to normalize the embedding
            
        Returns:
            Numpy array of the query embedding
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        logger.info(f"Encoding query: {query[:50]}...")
        return self.encode(query, normalize=normalize)
    
    def encode_batch(self, texts: List[str], 
                    batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        This method is optimized for processing large numbers of texts.
        
        Args:
            texts: List of text strings
            batch_size: Number of texts to process at once
            
        Returns:
            Numpy array of embeddings
        """
        return self.encode(texts, batch_size=batch_size, show_progress=True)
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Integer dimension of embeddings
        """
        return self.dimension
    
    def similarity(self, embedding1: np.ndarray, 
                  embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        # Ensure embeddings are normalized
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
    
    def batch_similarity(self, query_embedding: np.ndarray,
                        document_embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate similarities between a query and multiple documents.
        
        Args:
            query_embedding: Single query embedding
            document_embeddings: Array of document embeddings
            
        Returns:
            Array of similarity scores
        """
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = document_embeddings / np.linalg.norm(
            document_embeddings, axis=1, keepdims=True
        )
        
        # Calculate cosine similarities
        similarities = np.dot(doc_norms, query_norm)
        return similarities
    
    def clear_cache(self):
        """
        Clear the model cache to free up memory.
        
        Use this method if you need to free GPU/CPU memory.
        The model will be reloaded on next use.
        """
        logger.info("Clearing embedding model cache")
        self._model = None
        import gc
        gc.collect()
