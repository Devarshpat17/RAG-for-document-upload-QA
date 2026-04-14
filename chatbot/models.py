"""
Database models for the AI chatbot system.

This module defines the core data structures for:
- Document storage and metadata
- JSON database records
- Chat interaction history
"""

from django.db import models
from django.core.validators import FileExtensionValidator
import uuid


class Document(models.Model):
    """
    Model for storing uploaded documents and their metadata.
    
    Attributes:
        id: Unique UUID for the document
        title: Human-readable title for the document
        file: The uploaded document file
        file_type: Type of document (pdf, txt, etc.)
        file_size: Size of the file in bytes
        uploaded_at: Timestamp when the document was uploaded
        processed: Whether the document has been processed for indexing
        chunk_count: Number of text chunks extracted from the document
        faiss_index_id: Reference to the FAISS index storing this document's embeddings
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the document"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Title or name of the document"
    )
    
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'txt'])],
        help_text="The uploaded document file"
    )
    
    file_type = models.CharField(
        max_length=10,
        help_text="File extension (pdf, txt, etc.)"
    )
    
    file_size = models.BigIntegerField(
        help_text="File size in bytes"
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of upload"
    )
    
    processed = models.BooleanField(
        default=False,
        help_text="Whether the document has been processed and indexed"
    )
    
    chunk_count = models.IntegerField(
        default=0,
        help_text="Number of text chunks extracted from this document"
    )
    
    faiss_index_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Identifier for the FAISS index containing this document's embeddings"
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Document"
        verbose_name_plural = "Documents"
    
    def __str__(self):
        return f"{self.title} ({self.file_type})"
    
    def get_file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


class JSONDatabase(models.Model):
    """
    Model for storing JSON databases and their metadata.
    
    This model allows users to upload structured JSON data that will be
    converted to searchable text embeddings for semantic search.
    
    Attributes:
        id: Unique UUID for the JSON database
        name: Human-readable name for the database
        description: Optional description of the data
        data: The actual JSON data (stored as JSONField)
        created_at: Timestamp when the database was created
        updated_at: Timestamp of last update
        record_count: Number of records in the JSON data
        processed: Whether the data has been processed for indexing
        faiss_index_id: Reference to the FAISS index storing this database's embeddings
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the JSON database"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Name of the JSON database"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of the database contents"
    )
    
    data = models.JSONField(
        help_text="The JSON data to be indexed"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of creation"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of last update"
    )
    
    record_count = models.IntegerField(
        default=0,
        help_text="Number of records in the JSON data"
    )
    
    processed = models.BooleanField(
        default=False,
        help_text="Whether the data has been processed and indexed"
    )
    
    faiss_index_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Identifier for the FAISS index containing this database's embeddings"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "JSON Database"
        verbose_name_plural = "JSON Databases"
    
    def __str__(self):
        return f"{self.name} ({self.record_count} records)"


class ChatHistory(models.Model):
    """
    Model for storing chat interactions.
    
    Attributes:
        id: Unique UUID for the chat entry
        question: The user's question
        answer: The system's generated answer
        context_used: The context chunks used to generate the answer
        sources: List of source documents/databases used
        timestamp: When the interaction occurred
        processing_time: Time taken to generate the response (in seconds)
        tokens_used: Approximate number of tokens used in the LLM call
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the chat entry"
    )
    
    question = models.TextField(
        help_text="The user's question"
    )
    
    answer = models.TextField(
        help_text="The generated answer"
    )
    
    context_used = models.JSONField(
        default=list,
        help_text="List of context chunks used for answering"
    )
    
    sources = models.JSONField(
        default=list,
        help_text="List of source documents/databases referenced"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the interaction occurred"
    )
    
    processing_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Time taken to generate response (seconds)"
    )
    
    tokens_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Approximate tokens used in LLM call"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Chat History"
        verbose_name_plural = "Chat Histories"
    
    def __str__(self):
        question_preview = self.question[:50] + "..." if len(self.question) > 50 else self.question
        return f"Q: {question_preview}"
