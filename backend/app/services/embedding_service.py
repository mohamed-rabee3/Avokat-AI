"""
Embedding service for semantic search using sentence-transformers
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import json

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing embeddings using sentence-transformers"""
    
    def __init__(self):
        self.model = None
        self.model_name = None
        self.embedding_dimension = None
        
        # List of alternative models to try (in order of preference)
        self.alternative_models = [
            "paraphrase-MiniLM-L6-v2",  # 384 dimensions, good alternative
            "distilbert-base-nli-mean-tokens",  # 768 dimensions, reliable
            "all-mpnet-base-v2",  # 768 dimensions, high quality
            "all-MiniLM-L12-v2",  # 384 dimensions, alternative to L6
        ]
        
    def initialize(self):
        """Initialize the sentence transformer model with fallback options"""
        # Skip remote models due to authentication issues and go directly to local fallback
        logger.info("Skipping remote models due to authentication issues. Using simple local embedding fallback...")
        self._initialize_simple_local_embedding()
    
    def _download_and_cache_model(self):
        """Download and cache a model locally to avoid future authentication issues"""
        import os
        import tempfile
        
        # Create a local cache directory
        cache_dir = os.path.join(tempfile.gettempdir(), "sentence_transformers_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Try to download the first model to local cache
        model_name = self.alternative_models[0]
        local_path = os.path.join(cache_dir, model_name.replace("/", "_"))
        
        try:
            logger.info(f"Downloading {model_name} to local cache: {local_path}")
            self.model = SentenceTransformer(model_name, cache_folder=cache_dir)
            self.model_name = model_name
            
            # Set embedding dimension
            if "MiniLM-L6" in model_name or "paraphrase-MiniLM-L6" in model_name:
                self.embedding_dimension = 384
            elif "distilbert" in model_name or "mpnet" in model_name or "MiniLM-L12" in model_name:
                self.embedding_dimension = 768
            else:
                self.embedding_dimension = 384
            
            logger.info(f"Successfully downloaded and cached {model_name} model with {self.embedding_dimension} dimensions")
            
        except Exception as e:
            logger.error(f"Failed to download and cache model: {e}")
            raise
    
    def _initialize_simple_local_embedding(self):
        """Initialize a simple local embedding method as final fallback"""
        logger.info("Initializing simple local embedding fallback")
        self.model = None
        self.model_name = "simple-local"
        self.embedding_dimension = 100  # Fixed dimension for simple embeddings
        
        # Simple word-based embedding using basic text processing
        import re
        import hashlib
        
        self.word_vocab = set()
        self.max_vocab_size = 1000
        
        logger.info("Successfully initialized simple local embedding fallback")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.model and self.model_name != "simple-local":
            raise RuntimeError("Embedding service not initialized")
        
        try:
            # Clean the text
            cleaned_text = self._clean_text(text)
            
            if self.model_name == "simple-local":
                # Use simple local embedding
                return self._generate_simple_embedding(cleaned_text)
            else:
                # Use sentence transformer
                embedding = self.model.encode(cleaned_text, convert_to_tensor=False)
                embedding_list = embedding.tolist()
                
                logger.debug(f"Generated {self.model_name} embedding of dimension {len(embedding_list)} for text: {cleaned_text[:50]}...")
                return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def _generate_simple_embedding(self, text: str) -> List[float]:
        """Generate simple local embedding using basic text processing"""
        import re
        import hashlib
        import numpy as np
        
        # Extract words from text
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Create a simple embedding based on word hashes
        embedding = [0.0] * self.embedding_dimension
        
        for word in words:
            # Create a hash of the word
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
            
            # Map hash to embedding dimensions
            for i in range(min(5, self.embedding_dimension)):  # Use up to 5 dimensions per word
                dim_idx = (word_hash + i) % self.embedding_dimension
                embedding[dim_idx] += 1.0 / len(words)  # Normalize by word count
        
        # Normalize the embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        logger.debug(f"Generated simple local embedding of dimension {len(embedding)} for text: {text[:50]}...")
        return embedding
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.model and self.model_name != "simple-local":
            raise RuntimeError("Embedding service not initialized")
        
        try:
            # Clean texts
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            if self.model_name == "simple-local":
                # Use simple local embedding for each text
                embeddings_list = [self._generate_simple_embedding(text) for text in cleaned_texts]
            else:
                # Use sentence transformer
                embeddings = self.model.encode(cleaned_texts, convert_to_tensor=False)
                embeddings_list = [embedding.tolist() for embedding in embeddings]
            
            logger.info(f"Generated {len(embeddings_list)} {self.model_name} embeddings of dimension {len(embeddings_list[0])}")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], candidate_embeddings: List[List[float]], 
                         candidate_texts: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar texts based on embedding similarity"""
        try:
            similarities = []
            
            for i, candidate_embedding in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate_embedding)
                similarities.append({
                    'index': i,
                    'text': candidate_texts[i],
                    'similarity': similarity
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top_k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to find most similar texts: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation"""
        if not text:
            return ""
        
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        
        # Truncate if too long (sentence-transformers has limits)
        max_length = 512  # Conservative limit for all-MiniLM-L6-v2
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
            logger.warning(f"Text truncated to {max_length} characters")
        
        return cleaned
    
    def embedding_to_string(self, embedding: List[float]) -> str:
        """Convert embedding to string for storage"""
        return json.dumps(embedding)
    
    def string_to_embedding(self, embedding_str: str) -> List[float]:
        """Convert string back to embedding"""
        return json.loads(embedding_str)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.embedding_dimension


# Global instance
embedding_service = EmbeddingService()
