"""
FAISS-based retrieval service for semantic search.

This module handles:
- FAISS index creation and management
- Vector storage and retrieval
- Similarity search operations
- Index persistence
"""

import logging
import os
import pickle
from typing import List, Tuple, Dict, Any
import numpy as np
import faiss
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for managing FAISS indices and performing semantic search.
    
    This service provides methods for creating, updating, and querying
    FAISS vector indices for efficient similarity search.
    """
    
    def __init__(self):
        """Initialize the retrieval service with configuration."""
        self.index_dir = Path(settings.AI_CONFIG['FAISS_INDEX_DIR'])
        self.index_type = settings.AI_CONFIG['FAISS_INDEX_TYPE']
        self.dimension = settings.AI_CONFIG['EMBEDDING_DIMENSION']
        self.top_k = settings.AI_CONFIG['SIMILARITY_TOP_K']
        
        # Ensure index directory exists
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for loaded indices
        self._index_cache = {}
        self._metadata_cache = {}
    
    def create_index(self, index_id: str, dimension: int = None) -> faiss.Index:
        """
        Create a new FAISS index.
        
        Args:
            index_id: Unique identifier for the index
            dimension: Embedding dimension (uses config default if not provided)
            
        Returns:
            Initialized FAISS index
        """
        if dimension is None:
            dimension = self.dimension
        
        logger.info(f"Creating new FAISS index: {index_id} (dimension: {dimension})")
        
        # Create index based on type
        if self.index_type == 'Flat':
            # L2 (Euclidean) distance - good for small datasets
            index = faiss.IndexFlatL2(dimension)
        elif self.index_type == 'FlatIP':
            # Inner product (cosine similarity with normalized vectors)
            index = faiss.IndexFlatIP(dimension)
        elif self.index_type == 'IVFFlat':
            # Inverted file index - good for larger datasets
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        elif self.index_type == 'HNSW':
            # Hierarchical Navigable Small World - fast approximate search
            index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            logger.warning(f"Unknown index type {self.index_type}, using Flat")
            index = faiss.IndexFlatL2(dimension)
        
        # Cache the index
        self._index_cache[index_id] = index
        self._metadata_cache[index_id] = []
        
        return index
    
    def add_embeddings(self, index_id: str, embeddings: np.ndarray, 
                      metadata: List[Dict[str, Any]] = None) -> int:
        """
        Add embeddings to an index.
        
        Args:
            index_id: ID of the index to add to
            embeddings: Array of embeddings to add (shape: [n, dimension])
            metadata: Optional list of metadata dicts for each embedding
            
        Returns:
            Number of embeddings added
        """
        # Get or create index
        if index_id not in self._index_cache:
            index = self.load_index(index_id)
            if index is None:
                index = self.create_index(index_id)
        else:
            index = self._index_cache[index_id]
        
        # Ensure embeddings are 2D
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Validate dimension
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embeddings.shape[1]} does not match "
                f"index dimension {self.dimension}"
            )
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Train index if needed (for IVF indices)
        if hasattr(index, 'is_trained') and not index.is_trained:
            logger.info(f"Training index {index_id}")
            index.train(embeddings)
        
        # Add to index
        start_id = index.ntotal
        index.add(embeddings)
        
        # Store metadata
        if index_id not in self._metadata_cache:
            self._metadata_cache[index_id] = []
        
        if metadata:
            self._metadata_cache[index_id].extend(metadata)
        else:
            # Create default metadata
            default_metadata = [
                {'id': start_id + i} for i in range(len(embeddings))
            ]
            self._metadata_cache[index_id].extend(default_metadata)
        
        logger.info(
            f"Added {len(embeddings)} embeddings to index {index_id}. "
            f"Total: {index.ntotal}"
        )
        
        return len(embeddings)
    
    def search(self, index_id: str, query_embedding: np.ndarray, 
               top_k: int = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar embeddings in the index.
        
        Args:
            index_id: ID of the index to search
            query_embedding: Query embedding vector
            top_k: Number of results to return (uses config default if not provided)
            
        Returns:
            List of tuples (metadata, similarity_score) for top results
        """
        if top_k is None:
            top_k = self.top_k
        
        # Load index if not cached
        if index_id not in self._index_cache:
            index = self.load_index(index_id)
            if index is None:
                logger.warning(f"Index {index_id} not found")
                return []
        else:
            index = self._index_cache[index_id]
        
        # Check if index is empty
        if index.ntotal == 0:
            logger.warning(f"Index {index_id} is empty")
            return []
        
        # Reshape query if needed
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query embedding
        faiss.normalize_L2(query_embedding)
        
        # Limit top_k to available embeddings
        k = min(top_k, index.ntotal)
        
        # Search
        distances, indices = index.search(query_embedding, k)
        
        # Get metadata for results
        results = []
        metadata_list = self._metadata_cache.get(index_id, [])
        
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(metadata_list):
                # Convert distance to similarity score (for L2 distance)
                # Higher score = more similar
                similarity = 1 / (1 + distance)
                results.append((metadata_list[idx], float(similarity)))
        
        logger.info(f"Found {len(results)} results for query in index {index_id}")
        return results
    
    def save_index(self, index_id: str) -> bool:
        """
        Save index and metadata to disk.
        
        Args:
            index_id: ID of the index to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if index_id not in self._index_cache:
            logger.warning(f"Index {index_id} not found in cache")
            return False
        
        try:
            index = self._index_cache[index_id]
            metadata = self._metadata_cache.get(index_id, [])
            
            # Save FAISS index
            index_path = self.index_dir / f"{index_id}.index"
            faiss.write_index(index, str(index_path))
            
            # Save metadata
            metadata_path = self.index_dir / f"{index_id}.metadata"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Saved index {index_id} to {index_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index {index_id}: {e}")
            return False
    
    def load_index(self, index_id: str) -> faiss.Index:
        """
        Load index and metadata from disk.
        
        Args:
            index_id: ID of the index to load
            
        Returns:
            Loaded FAISS index, or None if not found
        """
        index_path = self.index_dir / f"{index_id}.index"
        metadata_path = self.index_dir / f"{index_id}.metadata"
        
        if not index_path.exists():
            logger.warning(f"Index file not found: {index_path}")
            return None
        
        try:
            # Load FAISS index
            index = faiss.read_index(str(index_path))
            
            # Load metadata
            metadata = []
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
            
            # Cache the loaded index
            self._index_cache[index_id] = index
            self._metadata_cache[index_id] = metadata
            
            logger.info(
                f"Loaded index {index_id} with {index.ntotal} embeddings"
            )
            return index
            
        except Exception as e:
            logger.error(f"Failed to load index {index_id}: {e}")
            return None
    
    def delete_index(self, index_id: str) -> bool:
        """
        Delete an index from disk and cache.
        
        Args:
            index_id: ID of the index to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Remove from cache
            if index_id in self._index_cache:
                del self._index_cache[index_id]
            if index_id in self._metadata_cache:
                del self._metadata_cache[index_id]
            
            # Delete files
            index_path = self.index_dir / f"{index_id}.index"
            metadata_path = self.index_dir / f"{index_id}.metadata"
            
            if index_path.exists():
                index_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Deleted index {index_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete index {index_id}: {e}")
            return False
    
    def get_index_stats(self, index_id: str) -> Dict[str, Any]:
        """
        Get statistics about an index.
        
        Args:
            index_id: ID of the index
            
        Returns:
            Dictionary with index statistics
        """
        if index_id not in self._index_cache:
            index = self.load_index(index_id)
            if index is None:
                return {'error': 'Index not found'}
        else:
            index = self._index_cache[index_id]
        
        return {
            'index_id': index_id,
            'total_embeddings': index.ntotal,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'is_trained': getattr(index, 'is_trained', True),
        }
    
    def merge_search_results(self, 
                           results_list: List[List[Tuple[Dict, float]]]) -> List[Tuple[Dict, float]]:
        """
        Merge and deduplicate results from multiple index searches.
        
        Args:
            results_list: List of result lists from different indices
            
        Returns:
            Merged and sorted results
        """
        # Flatten all results
        all_results = []
        seen_ids = set()
        
        for results in results_list:
            for metadata, score in results:
                # Use a unique key for deduplication
                result_id = metadata.get('chunk_id', id(metadata))
                
                if result_id not in seen_ids:
                    all_results.append((metadata, score))
                    seen_ids.add(result_id)
        
        # Sort by score (descending)
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        return all_results[:self.top_k]
