"""
Test suite for chatbot services.

This module contains unit tests for all service classes.
"""

import os
import tempfile
from pathlib import Path
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
import numpy as np

from chatbot.models import Document, JSONDatabase, ChatHistory
from chatbot.services import (
    DocumentService,
    EmbeddingService,
    RetrievalService,
    LLMService,
    JSONService
)


class DocumentServiceTest(TestCase):
    """Tests for DocumentService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = DocumentService()
    
    def test_chunk_text(self):
        """Test text chunking functionality."""
        text = "This is a test. " * 100  # Create a longer text
        chunks = self.service.chunk_text(text)
        
        self.assertGreater(len(chunks), 0)
        self.assertIsInstance(chunks[0], tuple)
        self.assertIsInstance(chunks[0][0], str)  # Chunk text
        self.assertIsInstance(chunks[0][1], dict)  # Chunk metadata
    
    def test_preprocess_text(self):
        """Test text preprocessing."""
        text = "This   is  a    test\n\n\nwith    whitespace"
        processed = self.service.preprocess_text(text)
        
        self.assertNotIn("   ", processed)  # Multiple spaces removed
        self.assertIn("test", processed)
    
    def test_split_into_sentences(self):
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = self.service._split_into_sentences(text)
        
        self.assertEqual(len(sentences), 3)
    
    def test_get_document_stats(self):
        """Test document statistics calculation."""
        text = "This is a test document. It has two sentences."
        stats = self.service.get_document_stats(text)
        
        self.assertIn('word_count', stats)
        self.assertIn('sentence_count', stats)
        self.assertGreater(stats['word_count'], 0)


class EmbeddingServiceTest(TestCase):
    """Tests for EmbeddingService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = EmbeddingService()
    
    def test_encode_single_text(self):
        """Test encoding a single text."""
        text = "This is a test sentence."
        embedding = self.service.encode(text)
        
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding), self.service.dimension)
    
    def test_encode_batch(self):
        """Test encoding multiple texts."""
        texts = ["First text.", "Second text.", "Third text."]
        embeddings = self.service.encode(texts)
        
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape[0], len(texts))
        self.assertEqual(embeddings.shape[1], self.service.dimension)
    
    def test_encode_query(self):
        """Test encoding a search query."""
        query = "What is machine learning?"
        embedding = self.service.encode_query(query)
        
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(len(embedding), self.service.dimension)
    
    def test_similarity(self):
        """Test similarity calculation."""
        text1 = "Machine learning is a subset of AI."
        text2 = "AI includes machine learning."
        text3 = "Pizza is delicious."
        
        emb1 = self.service.encode(text1)
        emb2 = self.service.encode(text2)
        emb3 = self.service.encode(text3)
        
        sim_12 = self.service.similarity(emb1, emb2)
        sim_13 = self.service.similarity(emb1, emb3)
        
        # Related texts should be more similar
        self.assertGreater(sim_12, sim_13)


class RetrievalServiceTest(TestCase):
    """Tests for RetrievalService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = RetrievalService()
        self.embed_service = EmbeddingService()
    
    def test_create_index(self):
        """Test index creation."""
        index_id = "test_index"
        index = self.service.create_index(index_id)
        
        self.assertIsNotNone(index)
        self.assertEqual(index.ntotal, 0)  # Empty index
    
    def test_add_and_search_embeddings(self):
        """Test adding embeddings and searching."""
        index_id = "test_search"
        
        # Create some test embeddings
        texts = [
            "Machine learning is great",
            "Deep learning is powerful",
            "Pizza is tasty"
        ]
        embeddings = self.embed_service.encode(texts)
        metadata = [{'text': text, 'id': i} for i, text in enumerate(texts)]
        
        # Add to index
        self.service.add_embeddings(index_id, embeddings, metadata)
        
        # Search
        query = "What is machine learning?"
        query_emb = self.embed_service.encode_query(query)
        results = self.service.search(index_id, query_emb, top_k=2)
        
        self.assertGreater(len(results), 0)
        self.assertIsInstance(results[0], tuple)
        
        # Clean up
        self.service.delete_index(index_id)
    
    def test_save_and_load_index(self):
        """Test index persistence."""
        index_id = "test_persist"
        
        # Create and populate index
        texts = ["Test text 1", "Test text 2"]
        embeddings = self.embed_service.encode(texts)
        self.service.add_embeddings(index_id, embeddings)
        
        # Save
        saved = self.service.save_index(index_id)
        self.assertTrue(saved)
        
        # Clear cache
        self.service._index_cache.clear()
        
        # Load
        loaded_index = self.service.load_index(index_id)
        self.assertIsNotNone(loaded_index)
        self.assertEqual(loaded_index.ntotal, len(texts))
        
        # Clean up
        self.service.delete_index(index_id)


class JSONServiceTest(TestCase):
    """Tests for JSONService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = JSONService()
    
    def test_process_json_data_list(self):
        """Test processing a list of JSON records."""
        data = [
            {'id': 1, 'name': 'Product A', 'price': 10.99},
            {'id': 2, 'name': 'Product B', 'price': 20.99}
        ]
        
        chunks = self.service.process_json_data(data)
        
        self.assertEqual(len(chunks), 2)
        self.assertIsInstance(chunks[0], tuple)
        self.assertIn('Product A', chunks[0][0])
    
    def test_process_json_data_dict(self):
        """Test processing a single JSON record."""
        data = {'id': 1, 'name': 'Product A', 'price': 10.99}
        
        chunks = self.service.process_json_data(data)
        
        self.assertEqual(len(chunks), 1)
        self.assertIn('Product A', chunks[0][0])
    
    def test_record_to_text(self):
        """Test converting a record to text."""
        record = {
            'id': 1,
            'name': 'Test Product',
            'description': 'A great product',
            'price': 29.99
        }
        
        text = self.service._record_to_text(record)
        
        self.assertIn('Test Product', text)
        self.assertIn('29.99', text)
    
    def test_nested_record_to_text(self):
        """Test converting a nested record to text."""
        record = {
            'id': 1,
            'product': {
                'name': 'Widget',
                'specs': {
                    'color': 'blue',
                    'size': 'large'
                }
            }
        }
        
        text = self.service._record_to_text(record)
        
        self.assertIn('Widget', text)
        self.assertIn('blue', text)
    
    def test_validate_json_data(self):
        """Test JSON data validation."""
        # Valid list
        valid, msg = self.service.validate_json_data([{'id': 1}])
        self.assertTrue(valid)
        
        # Valid dict
        valid, msg = self.service.validate_json_data({'id': 1})
        self.assertTrue(valid)
        
        # Invalid: None
        valid, msg = self.service.validate_json_data(None)
        self.assertFalse(valid)
        
        # Invalid: string
        valid, msg = self.service.validate_json_data("invalid")
        self.assertFalse(valid)


class ModelTest(TestCase):
    """Tests for Django models."""
    
    def test_document_creation(self):
        """Test creating a Document instance."""
        # Create a test file
        file_content = b"Test document content"
        test_file = SimpleUploadedFile(
            "test.txt",
            file_content,
            content_type="text/plain"
        )
        
        document = Document.objects.create(
            title="Test Document",
            file=test_file,
            file_type="txt",
            file_size=len(file_content)
        )
        
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.file_type, "txt")
        self.assertFalse(document.processed)
    
    def test_json_database_creation(self):
        """Test creating a JSONDatabase instance."""
        data = [{'id': 1, 'name': 'Test'}]
        
        json_db = JSONDatabase.objects.create(
            name="Test DB",
            description="A test database",
            data=data,
            record_count=1
        )
        
        self.assertEqual(json_db.name, "Test DB")
        self.assertEqual(json_db.record_count, 1)
        self.assertFalse(json_db.processed)
    
    def test_chat_history_creation(self):
        """Test creating a ChatHistory instance."""
        chat = ChatHistory.objects.create(
            question="What is AI?",
            answer="AI stands for Artificial Intelligence.",
            context_used=["Context 1", "Context 2"],
            sources=[{'type': 'document', 'id': '123'}],
            processing_time=1.5,
            tokens_used=50
        )
        
        self.assertEqual(chat.question, "What is AI?")
        self.assertEqual(len(chat.context_used), 2)
        self.assertEqual(chat.processing_time, 1.5)
