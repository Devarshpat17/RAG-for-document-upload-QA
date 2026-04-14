"""
Django REST Framework serializers for API endpoints.

This module defines serializers for converting model instances to/from JSON,
with validation and custom field handling.
"""

from rest_framework import serializers
from .models import Document, JSONDatabase, ChatHistory


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for Document model.
    
    Provides read/write serialization for document uploads and retrieval.
    Includes computed fields for human-readable file size.
    """
    
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'file',
            'file_type',
            'file_size',
            'file_size_display',
            'uploaded_at',
            'processed',
            'chunk_count',
            'faiss_index_id',
        ]
        read_only_fields = [
            'id',
            'uploaded_at',
            'processed',
            'chunk_count',
            'faiss_index_id',
            'file_size',
            'file_type',
        ]
    
    def get_file_size_display(self, obj):
        """Return human-readable file size."""
        return obj.get_file_size_display()
    
    def validate_file(self, value):
        """
        Validate uploaded file size and type.
        
        Args:
            value: The uploaded file object
            
        Returns:
            The validated file object
            
        Raises:
            ValidationError: If file is too large or wrong type
        """
        from django.conf import settings
        
        max_size = settings.AI_CONFIG['MAX_FILE_SIZE_MB'] * 1024 * 1024
        
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of "
                f"{settings.AI_CONFIG['MAX_FILE_SIZE_MB']} MB"
            )
        
        return value


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing documents.
    Excludes file data for better performance.
    """
    
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'file_type',
            'file_size_display',
            'uploaded_at',
            'processed',
            'chunk_count',
        ]
    
    def get_file_size_display(self, obj):
        """Return human-readable file size."""
        return obj.get_file_size_display()


class JSONDatabaseSerializer(serializers.ModelSerializer):
    """
    Serializer for JSONDatabase model.
    
    Handles JSON data validation and storage.
    """
    
    class Meta:
        model = JSONDatabase
        fields = [
            'id',
            'name',
            'description',
            'data',
            'created_at',
            'updated_at',
            'record_count',
            'processed',
            'faiss_index_id',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'record_count',
            'processed',
            'faiss_index_id',
        ]
    
    def validate_data(self, value):
        """
        Validate that the JSON data is a list or dict.
        
        Args:
            value: The JSON data
            
        Returns:
            The validated JSON data
            
        Raises:
            ValidationError: If data is not a list or dict
        """
        if not isinstance(value, (list, dict)):
            raise serializers.ValidationError(
                "JSON data must be a list of records or a dictionary"
            )
        
        # If it's a dict, convert to list with single item
        if isinstance(value, dict):
            value = [value]
        
        return value


class JSONDatabaseListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing JSON databases.
    Excludes actual data for better performance.
    """
    
    class Meta:
        model = JSONDatabase
        fields = [
            'id',
            'name',
            'description',
            'record_count',
            'created_at',
            'processed',
        ]


class ChatHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for ChatHistory model.
    
    Handles chat interaction records.
    """
    
    class Meta:
        model = ChatHistory
        fields = [
            'id',
            'question',
            'answer',
            'context_used',
            'sources',
            'timestamp',
            'processing_time',
            'tokens_used',
        ]
        read_only_fields = [
            'id',
            'timestamp',
            'answer',
            'context_used',
            'sources',
            'processing_time',
            'tokens_used',
        ]


class ChatQuerySerializer(serializers.Serializer):
    """
    Serializer for chat query requests.
    
    Validates and processes incoming chat questions.
    """
    
    question = serializers.CharField(
        required=True,
        max_length=2000,
        help_text="The question to ask the chatbot"
    )
    
    max_context_chunks = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
        help_text="Maximum number of context chunks to retrieve"
    )
    
    include_sources = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Whether to include source information in the response"
    )
    
    def validate_question(self, value):
        """
        Validate that the question is not empty or just whitespace.
        
        Args:
            value: The question text
            
        Returns:
            The validated and cleaned question
            
        Raises:
            ValidationError: If question is empty
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Question cannot be empty")
        return value


class ChatResponseSerializer(serializers.Serializer):
    """
    Serializer for chat response data.
    
    Formats the chatbot's response for API output.
    """
    
    question = serializers.CharField()
    answer = serializers.CharField()
    sources = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    context_chunks = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    processing_time = serializers.FloatField(required=False)
    chat_history_id = serializers.UUIDField(required=False)
