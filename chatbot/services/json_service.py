"""
JSON service for handling structured data and converting it to searchable format.

This module handles:
- JSON data validation and processing
- Converting JSON records to text for embedding
- Extracting searchable content from nested structures
"""

import logging
import json
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class JSONService:
    """
    Service for processing JSON data and converting it to searchable text.
    
    This service provides methods for flattening JSON structures and
    creating text representations suitable for embedding.
    """
    
    def __init__(self):
        """Initialize the JSON service."""
        pass
    
    def process_json_data(self, data: Any) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Process JSON data and convert to text chunks with metadata.
        
        Args:
            data: JSON data (list of dicts, or single dict)
            
        Returns:
            List of tuples containing (text_representation, metadata)
        """
        # Ensure data is a list
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            logger.error(f"Invalid JSON data type: {type(data)}")
            return []
        
        chunks = []
        for idx, record in enumerate(data):
            if not isinstance(record, dict):
                logger.warning(f"Skipping non-dict record at index {idx}")
                continue
            
            # Convert record to searchable text
            text = self._record_to_text(record)
            
            # Create metadata
            metadata = {
                'record_index': idx,
                'record_id': record.get('id', idx),
                'source_type': 'json_database',
                'original_record': record,
            }
            
            chunks.append((text, metadata))
        
        logger.info(f"Processed {len(chunks)} JSON records")
        return chunks
    
    def _record_to_text(self, record: Dict[str, Any], prefix: str = "") -> str:
        """
        Convert a JSON record to a searchable text representation.
        
        Flattens nested structures and creates a natural language description.
        
        Args:
            record: Dictionary representing a JSON record
            prefix: Prefix for nested keys
            
        Returns:
            Text representation of the record
        """
        text_parts = []
        
        for key, value in record.items():
            # Create readable key name
            readable_key = self._make_readable_key(key)
            full_key = f"{prefix}{readable_key}" if prefix else readable_key
            
            if isinstance(value, dict):
                # Recursively process nested dict
                nested_text = self._record_to_text(value, prefix=f"{full_key} ")
                text_parts.append(nested_text)
            
            elif isinstance(value, list):
                # Process list items
                list_text = self._list_to_text(full_key, value)
                if list_text:
                    text_parts.append(list_text)
            
            elif value is not None:
                # Add simple key-value pair
                text_parts.append(f"{full_key}: {value}")
        
        return ". ".join(text_parts)
    
    def _list_to_text(self, key: str, items: List[Any]) -> str:
        """
        Convert a list to text representation.
        
        Args:
            key: Key name for the list
            items: List items
            
        Returns:
            Text representation
        """
        if not items:
            return ""
        
        # Handle list of primitives
        if all(isinstance(item, (str, int, float, bool)) for item in items):
            items_str = ", ".join(str(item) for item in items)
            return f"{key}: {items_str}"
        
        # Handle list of dicts
        elif all(isinstance(item, dict) for item in items):
            text_parts = []
            for idx, item in enumerate(items):
                item_text = self._record_to_text(item, prefix=f"{key} {idx+1} ")
                text_parts.append(item_text)
            return ". ".join(text_parts)
        
        # Mixed types - convert all to string
        else:
            items_str = ", ".join(str(item) for item in items)
            return f"{key}: {items_str}"
    
    def _make_readable_key(self, key: str) -> str:
        """
        Convert a key name to a more readable format.
        
        Converts snake_case and camelCase to spaces.
        
        Args:
            key: Original key name
            
        Returns:
            Readable key name
        """
        # Convert snake_case to spaces
        readable = key.replace('_', ' ')
        
        # Convert camelCase to spaces
        import re
        readable = re.sub(r'([a-z])([A-Z])', r'\1 \2', readable)
        
        # Capitalize first letter of each word
        readable = ' '.join(word.capitalize() for word in readable.split())
        
        return readable
    
    def validate_json_data(self, data: Any) -> Tuple[bool, str]:
        """
        Validate JSON data format.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if data is None:
            return False, "Data cannot be None"
        
        if not isinstance(data, (list, dict)):
            return False, "Data must be a list or dictionary"
        
        # If it's a dict, ensure it's not empty
        if isinstance(data, dict) and not data:
            return False, "Dictionary cannot be empty"
        
        # If it's a list, ensure it contains dicts
        if isinstance(data, list):
            if not data:
                return False, "List cannot be empty"
            
            # Check first few items
            sample_size = min(5, len(data))
            for i in range(sample_size):
                if not isinstance(data[i], dict):
                    return False, f"List item {i} is not a dictionary"
        
        return True, ""
    
    def extract_searchable_fields(self, record: Dict[str, Any],
                                  field_priorities: List[str] = None) -> str:
        """
        Extract and prioritize specific fields for searching.
        
        Useful when you want certain fields to be more prominent in search.
        
        Args:
            record: JSON record
            field_priorities: List of field names to prioritize
            
        Returns:
            Text with prioritized fields
        """
        if field_priorities is None:
            field_priorities = ['name', 'title', 'description', 'summary']
        
        text_parts = []
        
        # Add prioritized fields first
        for field in field_priorities:
            if field in record:
                value = record[field]
                if value:
                    readable_key = self._make_readable_key(field)
                    text_parts.append(f"{readable_key}: {value}")
        
        # Add remaining fields
        for key, value in record.items():
            if key not in field_priorities and value is not None:
                readable_key = self._make_readable_key(key)
                if isinstance(value, (str, int, float, bool)):
                    text_parts.append(f"{readable_key}: {value}")
        
        return ". ".join(text_parts)
    
    def search_json_records(self, records: List[Dict[str, Any]],
                           query: str) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search through JSON records.
        
        This is a fallback for when vector search is not available.
        
        Args:
            records: List of JSON records
            query: Search query
            
        Returns:
            List of matching records
        """
        query_lower = query.lower()
        matching_records = []
        
        for record in records:
            # Convert record to text and search
            text = self._record_to_text(record).lower()
            
            # Simple keyword matching
            if query_lower in text:
                matching_records.append(record)
        
        return matching_records
    
    def get_record_summary(self, record: Dict[str, Any],
                          max_length: int = 200) -> str:
        """
        Create a brief summary of a JSON record.
        
        Args:
            record: JSON record
            max_length: Maximum length of summary
            
        Returns:
            Summary text
        """
        # Try to get key fields for summary
        summary_fields = ['id', 'name', 'title', 'description']
        summary_parts = []
        
        for field in summary_fields:
            if field in record and record[field]:
                value = str(record[field])
                if len(value) > 50:
                    value = value[:47] + "..."
                summary_parts.append(f"{field}: {value}")
        
        summary = ", ".join(summary_parts)
        
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
