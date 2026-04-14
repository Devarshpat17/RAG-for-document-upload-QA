"""
Django admin configuration for chatbot models.
"""

from django.contrib import admin
from .models import Document, JSONDatabase, ChatHistory


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""
    
    list_display = [
        'title',
        'file_type',
        'get_file_size_display',
        'uploaded_at',
        'processed',
        'chunk_count',
    ]
    list_filter = ['file_type', 'processed', 'uploaded_at']
    search_fields = ['title', 'id']
    readonly_fields = [
        'id',
        'file_size',
        'file_type',
        'uploaded_at',
        'processed',
        'chunk_count',
        'faiss_index_id',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'file')
        }),
        ('File Details', {
            'fields': ('file_type', 'file_size', 'uploaded_at')
        }),
        ('Processing Status', {
            'fields': ('processed', 'chunk_count', 'faiss_index_id')
        }),
    )


@admin.register(JSONDatabase)
class JSONDatabaseAdmin(admin.ModelAdmin):
    """Admin interface for JSONDatabase model."""
    
    list_display = [
        'name',
        'record_count',
        'created_at',
        'processed',
    ]
    list_filter = ['processed', 'created_at']
    search_fields = ['name', 'description', 'id']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'record_count',
        'processed',
        'faiss_index_id',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description')
        }),
        ('Data', {
            'fields': ('data', 'record_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Processing Status', {
            'fields': ('processed', 'faiss_index_id')
        }),
    )


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ChatHistory model."""
    
    list_display = [
        'get_question_preview',
        'timestamp',
        'processing_time',
        'tokens_used',
    ]
    list_filter = ['timestamp']
    search_fields = ['question', 'answer', 'id']
    readonly_fields = [
        'id',
        'question',
        'answer',
        'context_used',
        'sources',
        'timestamp',
        'processing_time',
        'tokens_used',
    ]
    
    fieldsets = (
        ('Conversation', {
            'fields': ('id', 'question', 'answer')
        }),
        ('Context', {
            'fields': ('context_used', 'sources')
        }),
        ('Metadata', {
            'fields': ('timestamp', 'processing_time', 'tokens_used')
        }),
    )
    
    def get_question_preview(self, obj):
        """Return a preview of the question."""
        return obj.question[:75] + "..." if len(obj.question) > 75 else obj.question
    get_question_preview.short_description = "Question"
