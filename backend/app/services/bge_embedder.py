"""
Custom BGE M3 embedder for Graphiti integration.
This embedder uses the local BGE M3 model for CPU-based embeddings.
"""

import asyncio
from typing import List, Union
import numpy as np
from FlagEmbedding import BGEM3FlagModel
from graphiti_core.embedder import EmbedderClient


class BGEM3EmbedderConfig:
    """Configuration for BGE M3 embedder."""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        use_fp16: bool = False,
        max_length: int = 8192,
        batch_size: int = 12,
        device: str = "cpu"
    ):
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.max_length = max_length
        self.batch_size = batch_size
        self.device = device


class BGEM3Embedder(EmbedderClient):
    """BGE M3 embedder implementation for Graphiti."""
    
    def __init__(self, config: BGEM3EmbedderConfig):
        self.config = config
        self.model = None
        self._initialized = False
    
    def _initialize_model(self):
        """Initialize the BGE M3 model."""
        if not self._initialized:
            try:
                # Try to load the model with authentication
                self.model = BGEM3FlagModel(
                    self.config.model_name,
                    use_fp16=self.config.use_fp16
                )
                self._initialized = True
            except Exception as e:
                # If authentication fails, try with a different model or fallback
                print(f"Failed to load BGE M3 model: {e}")
                print("Trying with a smaller model...")
                try:
                    # Use a smaller, publicly available model
                    self.model = BGEM3FlagModel(
                        "BAAI/bge-small-en-v1.5",
                        use_fp16=self.config.use_fp16
                    )
                    self._initialized = True
                    print("Successfully loaded BGE small model as fallback")
                except Exception as e2:
                    print(f"Failed to load fallback model: {e2}")
                    raise e2
    
    def create(self, input_data: Union[str, List[str]]) -> List[float]:
        """
        Create embeddings for input data using BGE M3.
        
        Args:
            input_data: Single string or list of strings to embed
            
        Returns:
            List of embedding vectors (list of floats)
        """
        self._initialize_model()
        
        # Handle single string input
        if isinstance(input_data, str):
            texts = [input_data]
        else:
            texts = list(input_data)
        
        if not texts:
            return []
        
        # Encode texts and get dense embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            max_length=self.config.max_length,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False
        )
        
        # Extract dense vectors and convert to list of lists
        dense_vecs = embeddings['dense_vecs']
        
        # If single input, return single embedding
        if isinstance(input_data, str):
            return dense_vecs[0].tolist()
        else:
            return dense_vecs.tolist()
    
    def create_batch(self, input_data: List[str]) -> List[List[float]]:
        """
        Create embeddings for a batch of input data using BGE M3.
        
        Args:
            input_data: List of strings to embed
            
        Returns:
            List of embedding vectors (list of lists of floats)
        """
        return self.create(input_data)
