"""
API views for the chatbot application.

This module defines all REST API endpoints for:
- Document management
- JSON database management
- Chat interactions
"""

import logging
import time
from pathlib import Path

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings

from .models import Document, JSONDatabase, ChatHistory
from .serializers import (
    DocumentSerializer, DocumentListSerializer,
    JSONDatabaseSerializer, JSONDatabaseListSerializer,
    ChatHistorySerializer, ChatQuerySerializer, ChatResponseSerializer
)
from .services import (
    DocumentService, EmbeddingService, RetrievalService,
    LLMService, JSONService
)

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents.
    
    Provides endpoints for uploading, listing, retrieving, and deleting documents.
    Automatically processes documents and creates embeddings.
    """
    
    queryset = Document.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DocumentListSerializer
        return DocumentSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Upload and process a new document.
        
        Extracts text, generates embeddings, and stores in FAISS index.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the uploaded file
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract file metadata
        file_type = Path(uploaded_file.name).suffix[1:].lower()
        file_size = uploaded_file.size
        
        # Create document instance
        document = serializer.save(
            file_type=file_type,
            file_size=file_size
        )
        
        # Process the document asynchronously (in production, use Celery)
        try:
            self._process_document(document)
            logger.info(f"Successfully processed document {document.id}")
        except Exception as e:
            logger.error(f"Failed to process document {document.id}: {e}")
            document.delete()
            return Response(
                {'error': f'Failed to process document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
    
    def _process_document(self, document: Document):
        """
        Process a document: extract text, create embeddings, and index.
        
        Args:
            document: Document instance to process
        """
        try:
            # Initialize services
            logger.info(f"Initializing services for document {document.id}")
            doc_service = DocumentService()
            logger.info("DocumentService initialized")
            
            embed_service = EmbeddingService()
            logger.info(f"EmbeddingService initialized with model: {settings.AI_CONFIG['EMBEDDING_MODEL']}")
            
            retrieval_service = RetrievalService()
            logger.info("RetrievalService initialized")
            
            # Extract text from document
            logger.info(f"Extracting text from {document.title}")
            file_path = document.file.path
            text = doc_service.extract_text_from_file(file_path)
            logger.info(f"Extracted {len(text)} characters from document")
            
            # Create chunks with metadata
            logger.info("Creating text chunks")
            base_metadata = {
                'document_id': str(document.id),
                'document_title': document.title,
                'file_type': document.file_type,
            }
            chunks = doc_service.chunk_text(text, metadata=base_metadata)
            logger.info(f"Created {len(chunks)} chunks")
            
            if not chunks:
                raise Exception("No text chunks extracted from document")
            
            # Generate embeddings for chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk[0] for chunk in chunks]
            chunk_metadata = [chunk[1] for chunk in chunks]
            
            embeddings = embed_service.encode_batch(chunk_texts)
            logger.info(f"Generated embeddings with shape {embeddings.shape}")
            
            # Create or update FAISS index
            logger.info(f"Adding embeddings to FAISS index")
            index_id = f"doc_{document.id}"
            retrieval_service.add_embeddings(index_id, embeddings, chunk_metadata)
            logger.info(f"Saving FAISS index {index_id}")
            retrieval_service.save_index(index_id)
            logger.info(f"FAISS index saved successfully")
            
            # Update document
            document.processed = True
            document.chunk_count = len(chunks)
            document.faiss_index_id = index_id
            document.save()
            logger.info(f"Document {document.id} processing completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {e}", exc_info=True)
            raise
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a document and its associated FAISS index.
        """
        document = self.get_object()
        
        # Delete FAISS index if exists
        if document.faiss_index_id:
            retrieval_service = RetrievalService()
            retrieval_service.delete_index(document.faiss_index_id)
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """
        Reprocess a document to update its embeddings.
        """
        document = self.get_object()
        
        try:
            self._process_document(document)
            return Response({
                'message': 'Document reprocessed successfully',
                'document': DocumentSerializer(document).data
            })
        except Exception as e:
            logger.error(f"Failed to reprocess document {document.id}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JSONDatabaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing JSON databases.
    
    Provides endpoints for uploading, listing, retrieving, and deleting
    structured JSON data.
    """
    
    queryset = JSONDatabase.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return JSONDatabaseListSerializer
        return JSONDatabaseSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Upload and process JSON data.
        
        Converts JSON records to embeddings and stores in FAISS index.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Calculate record count
        data = serializer.validated_data['data']
        if isinstance(data, list):
            record_count = len(data)
        else:
            record_count = 1
        
        # Create database instance
        json_db = serializer.save(record_count=record_count)
        
        # Process the JSON data
        try:
            self._process_json_database(json_db)
            logger.info(f"Successfully processed JSON database {json_db.id}")
        except Exception as e:
            logger.error(f"Failed to process JSON database {json_db.id}: {e}")
            json_db.delete()
            return Response(
                {'error': f'Failed to process JSON data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            JSONDatabaseSerializer(json_db).data,
            status=status.HTTP_201_CREATED
        )
    
    def _process_json_database(self, json_db: JSONDatabase):
        """
        Process JSON database: convert to text, create embeddings, and index.
        
        Args:
            json_db: JSONDatabase instance to process
        """
        # Initialize services
        json_service = JSONService()
        embed_service = EmbeddingService()
        retrieval_service = RetrievalService()
        
        # Convert JSON to text chunks
        chunks = json_service.process_json_data(json_db.data)
        
        if not chunks:
            raise Exception("No searchable content extracted from JSON data")
        
        # Generate embeddings
        chunk_texts = [chunk[0] for chunk in chunks]
        chunk_metadata = [chunk[1] for chunk in chunks]
        
        # Add database metadata
        for metadata in chunk_metadata:
            metadata['database_id'] = str(json_db.id)
            metadata['database_name'] = json_db.name
        
        embeddings = embed_service.encode_batch(chunk_texts)
        
        # Create or update FAISS index
        index_id = f"json_{json_db.id}"
        retrieval_service.add_embeddings(index_id, embeddings, chunk_metadata)
        retrieval_service.save_index(index_id)
        
        # Update database
        json_db.processed = True
        json_db.faiss_index_id = index_id
        json_db.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a JSON database and its associated FAISS index.
        """
        json_db = self.get_object()
        
        # Delete FAISS index if exists
        if json_db.faiss_index_id:
            retrieval_service = RetrievalService()
            retrieval_service.delete_index(json_db.faiss_index_id)
        
        return super().destroy(request, *args, **kwargs)


class ChatViewSet(viewsets.ViewSet):
    """
    ViewSet for chat interactions.
    
    Provides endpoints for asking questions and managing chat history.
    """
    
    @action(detail=False, methods=['post'])
    def ask(self, request):
        """
        Process a question and generate an answer using RAG.
        
        This is the main chatbot endpoint that:
        1. Encodes the question
        2. Retrieves relevant context from all indices
        3. Generates an answer using the LLM
        4. Saves the interaction to history
        """
        serializer = ChatQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question']
        max_context_chunks = serializer.validated_data['max_context_chunks']
        include_sources = serializer.validated_data['include_sources']
        
        start_time = time.time()
        
        try:
            # Initialize services
            embed_service = EmbeddingService()
            retrieval_service = RetrievalService()
            llm_service = LLMService()
            
            # Generate query embedding
            query_embedding = embed_service.encode_query(question)
            
            # Retrieve context from all available indices
            all_results = []
            
            # Search document indices
            documents = Document.objects.filter(processed=True)
            for doc in documents:
                if doc.faiss_index_id:
                    results = retrieval_service.search(
                        doc.faiss_index_id,
                        query_embedding,
                        top_k=max_context_chunks
                    )
                    all_results.append(results)
            
            # Search JSON database indices
            json_dbs = JSONDatabase.objects.filter(processed=True)
            for json_db in json_dbs:
                if json_db.faiss_index_id:
                    results = retrieval_service.search(
                        json_db.faiss_index_id,
                        query_embedding,
                        top_k=max_context_chunks
                    )
                    all_results.append(results)
            
            # Merge and rank results
            if all_results:
                merged_results = retrieval_service.merge_search_results(all_results)
                top_results = merged_results[:max_context_chunks]
            else:
                top_results = []
            
            # Extract context chunks and sources
            context_chunks = []
            sources = []
            
            for metadata, score in top_results:
                # Get the actual text from metadata
                if 'chunk_text' in metadata:
                    # For documents, use the stored chunk text
                    text = metadata.get('chunk_text', '')
                elif 'original_record' in metadata:
                    # For JSON databases, use the record text
                    json_service = JSONService()
                    text = json_service._record_to_text(metadata['original_record'])
                else:
                    text = ''
                
                context_chunks.append(text) if text else None
                
                # Build source info
                source_info = {
                    'type': metadata.get('source_type', 'document'),
                    'score': score,
                }
                
                if 'document_title' in metadata:
                    source_info['title'] = metadata['document_title']
                    source_info['id'] = metadata['document_id']
                elif 'database_name' in metadata:
                    source_info['name'] = metadata['database_name']
                    source_info['id'] = metadata['database_id']
                
                sources.append(source_info)
            
            # Generate answer using LLM
            llm_response = llm_service.generate_response(
                question,
                context_chunks
            )
            
            answer = llm_response['answer']
            tokens_used = llm_response.get('tokens_used', 0)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save to chat history
            chat_history = ChatHistory.objects.create(
                question=question,
                answer=answer,
                context_used=context_chunks,
                sources=sources,
                processing_time=processing_time,
                tokens_used=tokens_used
            )
            
            # Build response
            response_data = {
                'question': question,
                'answer': answer,
                'processing_time': processing_time,
                'chat_history_id': chat_history.id,
            }
            
            if include_sources:
                response_data['sources'] = sources
                response_data['context_chunks'] = context_chunks
            
            response_serializer = ChatResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Failed to process question: {e}")
            return Response(
                {'error': f'Failed to generate answer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Retrieve chat history.
        """
        history = ChatHistory.objects.all()[:50]  # Last 50 interactions
        serializer = ChatHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def clear_history(self, request):
        """
        Clear all chat history.
        """
        count = ChatHistory.objects.all().delete()[0]
        return Response({
            'message': f'Deleted {count} chat history entries'
        })
