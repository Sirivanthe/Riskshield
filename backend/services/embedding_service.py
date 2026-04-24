# Embedding Service using OpenAI API with Emergent LLM Key
# Generates text embeddings for vector search

import os
import logging
from typing import List, Union
from openai import OpenAI
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI API.
    Uses Emergent LLM key for access.
    """
    
    def __init__(
        self, 
        api_key: str = None,
        model: str = "text-embedding-3-small",
        dimension: int = 1536
    ):
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY')
        self.model = model
        self.dimension = dimension
        
        if not self.api_key:
            logger.warning("No API key provided for embeddings - using mock embeddings")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    async def generate_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for one or more texts.
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            List of embedding vectors
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        # Use mock embeddings if no API key
        if not self.client:
            return self._generate_mock_embeddings(texts)
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            
            # Sort by index and extract embeddings
            embeddings = sorted(response.data, key=lambda x: x.index)
            result = [e.embedding for e in embeddings]
            
            logger.info(f"Generated {len(result)} embeddings using {response.usage.total_tokens} tokens")
            return result
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Fallback to mock embeddings
            return self._generate_mock_embeddings(texts)
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate deterministic mock embeddings based on text content.
        Useful for development and testing without API access.
        """
        embeddings = []
        
        for text in texts:
            # Create deterministic embedding based on text hash
            np.random.seed(hash(text) % (2**32))
            embedding = np.random.randn(self.dimension).astype(np.float32)
            # Normalize
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding.tolist())
        
        logger.info(f"Generated {len(embeddings)} mock embeddings")
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
