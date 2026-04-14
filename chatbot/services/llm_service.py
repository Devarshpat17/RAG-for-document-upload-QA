"""
LLM service for generating responses using HuggingFace transformers.

This module handles:
- Loading and managing LLM models
- Prompt engineering and formatting
- Response generation with context
- Token management
"""

import logging
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for generating responses using open-source LLMs.
    
    This service provides methods for loading models and generating
    context-aware responses to user queries.
    """
    
    _instance = None
    _model = None
    _tokenizer = None
    _pipeline = None
    
    def __new__(cls):
        """Implement singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the LLM service and load the model."""
        if self._model is None:
            self.model_name = settings.AI_CONFIG['LLM_MODEL']
            self.max_tokens = settings.AI_CONFIG['MAX_TOKENS']
            self.temperature = settings.AI_CONFIG['TEMPERATURE']
            self._load_model()
    
    def _load_model(self):
        """
        Load the LLM model and tokenizer.
        
        This method loads the model on first use and caches it.
        For production, consider using smaller models or model quantization.
        """
        try:
            logger.info(f"Loading LLM model: {self.model_name}")
            
            # Determine device (GPU if available, else CPU)
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {self.device}")
            
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Set padding token if not exists
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
            
            # Load model
            # For production, consider using quantization:
            # load_in_8bit=True, device_map="auto"
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
            )
            
            # Move model to device
            if self.device == 'cuda':
                self._model = self._model.to(self.device)
            
            # Create text generation pipeline
            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                device=0 if self.device == 'cuda' else -1,
            )
            
            logger.info("Successfully loaded LLM model")
            
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            raise Exception(f"Could not load LLM model {self.model_name}: {e}")
    
    def generate_response(self, 
                         question: str,
                         context_chunks: List[str],
                         max_tokens: Optional[int] = None,
                         temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a response to a question using retrieved context.
        
        Args:
            question: The user's question
            context_chunks: List of relevant context chunks
            max_tokens: Maximum tokens to generate (uses config default if not provided)
            temperature: Sampling temperature (uses config default if not provided)
            
        Returns:
            Dictionary containing the generated answer and metadata
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        if temperature is None:
            temperature = self.temperature
        
        # Build the prompt with context
        prompt = self._build_prompt(question, context_chunks)
        
        logger.info(f"Generating response for question: {question[:50]}...")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        
        try:
            # Generate response
            outputs = self._pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                top_p=0.9,
                top_k=50,
                num_return_sequences=1,
                pad_token_id=self._tokenizer.eos_token_id,
            )
            
            # Extract generated text
            full_response = outputs[0]['generated_text']
            
            # Extract just the answer (remove the prompt)
            answer = self._extract_answer(full_response, prompt)
            
            # Calculate approximate token usage
            tokens_used = len(self._tokenizer.encode(full_response))
            
            logger.info(f"Generated response ({tokens_used} tokens)")
            
            return {
                'answer': answer,
                'tokens_used': tokens_used,
                'model': self.model_name,
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                'answer': "I apologize, but I encountered an error generating a response.",
                'tokens_used': 0,
                'error': str(e),
            }
    
    def _build_prompt(self, question: str, context_chunks: List[str]) -> str:
        """
        Build a prompt with context for the LLM.
        
        Uses a structured format to guide the model to generate accurate,
        context-based responses.
        
        Args:
            question: The user's question
            context_chunks: List of relevant context chunks
            
        Returns:
            Formatted prompt string
        """
        # Combine context chunks
        if context_chunks:
            context = "\n\n".join([
                f"[Context {i+1}]\n{chunk}"
                for i, chunk in enumerate(context_chunks)
            ])
        else:
            context = "No specific context available."
        
        # Build prompt based on model type
        if "mistral" in self.model_name.lower():
            # Mistral-specific format
            prompt = f"""<s>[INST] You are a helpful AI assistant. Answer the question based on the provided context. If the context doesn't contain enough information to answer the question, say so clearly.

Context:
{context}

Question: {question}

Please provide a clear, concise answer based on the context above. [/INST]"""
        
        elif "llama" in self.model_name.lower():
            # LLaMA-specific format
            prompt = f"""<s>[INST] <<SYS>>
You are a helpful AI assistant. Answer questions based on the provided context. If the context doesn't contain enough information, acknowledge this limitation.
<</SYS>>

Context:
{context}

Question: {question} [/INST]"""
        
        elif "phi" in self.model_name.lower():
            # Phi-specific format
            prompt = f"""Instruct: You are a helpful assistant. Use the following context to answer the question.

Context:
{context}

Question: {question}

Output:"""
        
        else:
            # Generic format (works with GPT-2 and similar models)
            prompt = f"""Answer the following question based on the provided context.

Context:
{context}

Question: {question}

Answer:"""
        
        return prompt
    
    def _extract_answer(self, full_response: str, prompt: str) -> str:
        """
        Extract the answer from the full model response.
        
        Args:
            full_response: Complete generated text including prompt
            prompt: The original prompt
            
        Returns:
            Extracted answer text
        """
        # Remove the prompt to get just the answer
        if full_response.startswith(prompt):
            answer = full_response[len(prompt):].strip()
        else:
            answer = full_response.strip()
        
        # Clean up common artifacts
        answer = answer.replace("</s>", "").replace("<s>", "")
        answer = answer.replace("[/INST]", "").replace("[INST]", "")
        
        # Remove excess whitespace
        answer = " ".join(answer.split())
        
        return answer
    
    def generate_simple_response(self, question: str) -> str:
        """
        Generate a simple response without context.
        
        Useful for general questions that don't require document context.
        
        Args:
            question: The user's question
            
        Returns:
            Generated answer
        """
        result = self.generate_response(question, context_chunks=[])
        return result.get('answer', '')
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Approximate number of tokens
        """
        if self._tokenizer is None:
            # Rough estimate: ~4 characters per token
            return len(text) // 4
        
        return len(self._tokenizer.encode(text))
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'device': self.device,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'model_loaded': self._model is not None,
        }
    
    def clear_cache(self):
        """
        Clear the model cache to free up memory.
        
        Use this method if you need to free GPU/CPU memory.
        The model will be reloaded on next use.
        """
        logger.info("Clearing LLM model cache")
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        import gc
        gc.collect()
