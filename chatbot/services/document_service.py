"""
Document processing service for text extraction and chunking.

This module handles:
- Text extraction from PDF and TXT files
- Intelligent text chunking with overlap
- Text preprocessing and cleaning
"""

import logging
import re
from typing import List, Tuple
from pathlib import Path

import PyPDF2
import pdfplumber
from django.conf import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for processing documents and extracting text chunks.
    
    This service provides methods for extracting text from various document
    formats and splitting the text into manageable chunks for embedding.
    """
    
    def __init__(self):
        """Initialize the document service with configuration from settings."""
        self.chunk_size = settings.AI_CONFIG['CHUNK_SIZE']
        self.chunk_overlap = settings.AI_CONFIG['CHUNK_OVERLAP']
        self.supported_types = settings.AI_CONFIG['SUPPORTED_DOCUMENT_TYPES']
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from a document file.
        
        Supports PDF and TXT formats with fallback extraction methods.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content as a string
            
        Raises:
            ValueError: If file type is not supported
            Exception: If text extraction fails
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        logger.info(f"Extracting text from {file_path.name} ({file_extension})")
        
        if file_extension == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_extension == '.txt':
            return self._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file using multiple methods.
        
        Tries pdfplumber first (better for complex PDFs), falls back to PyPDF2.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        
        # Try pdfplumber first (better text extraction)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            if text.strip():
                logger.info(f"Successfully extracted {len(text)} characters using pdfplumber")
                return text
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}, trying PyPDF2")
        
        # Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            logger.info(f"Successfully extracted {len(text)} characters using PyPDF2")
            return text
        except Exception as e:
            logger.error(f"All PDF extraction methods failed: {e}")
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    def _extract_from_txt(self, file_path: Path) -> str:
        """
        Extract text from TXT file.
        
        Handles various encodings with fallback options.
        
        Args:
            file_path: Path to the TXT file
            
        Returns:
            Extracted text content
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    text = file.read()
                logger.info(f"Successfully read TXT file with {encoding} encoding")
                return text
            except UnicodeDecodeError:
                continue
        
        raise Exception("Failed to decode TXT file with any supported encoding")
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess extracted text.
        
        Removes excessive whitespace, special characters, and normalizes text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned and preprocessed text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\-\(\)\'\"]+', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, metadata: dict = None) -> List[Tuple[str, dict]]:
        """
        Split text into overlapping chunks for embedding.
        
        Uses a sliding window approach to maintain context across chunks.
        Each chunk is paired with metadata for tracking.
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of tuples containing (chunk_text, chunk_metadata)
        """
        if not text or not text.strip():
            logger.warning("Attempted to chunk empty text")
            return []
        
        # Preprocess the text
        text = self.preprocess_text(text)
        
        # Split into sentences for better chunk boundaries
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunk_metadata = self._create_chunk_metadata(
                    chunk_id, 
                    len(chunks), 
                    metadata
                )
                chunks.append((chunk_text, chunk_metadata))
                
                # Keep overlap: retain last N characters worth of sentences
                overlap_text = chunk_text[-self.chunk_overlap:]
                overlap_sentences = self._split_into_sentences(overlap_text)
                
                current_chunk = overlap_sentences
                current_length = sum(len(s) for s in current_chunk)
                chunk_id += 1
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add the last chunk if it has content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_metadata = self._create_chunk_metadata(
                chunk_id, 
                len(chunks), 
                metadata
            )
            chunks.append((chunk_text, chunk_metadata))
        
        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using basic rules.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be enhanced with NLTK if needed)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_chunk_metadata(self, chunk_id: int, chunk_index: int, 
                              base_metadata: dict = None) -> dict:
        """
        Create metadata dictionary for a text chunk.
        
        Args:
            chunk_id: Unique identifier for this chunk
            chunk_index: Position of this chunk in the sequence
            base_metadata: Base metadata to extend
            
        Returns:
            Complete metadata dictionary
        """
        metadata = base_metadata.copy() if base_metadata else {}
        metadata.update({
            'chunk_id': chunk_id,
            'chunk_index': chunk_index,
        })
        return metadata
    
    def get_document_stats(self, text: str) -> dict:
        """
        Calculate statistics about a document.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with document statistics
        """
        words = text.split()
        sentences = self._split_into_sentences(text)
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
        }
