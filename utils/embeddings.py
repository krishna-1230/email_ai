import google.generativeai as genai
import os
from typing import List
import numpy as np
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

def get_embedding(text: str) -> List[float]:
    """Generate embedding for text using Gemini."""
    try:
        # Initialize Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        
        # Generate embedding using the embedding model
        embedding = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document",
        )
        
        # Get the values from the embedding
        if hasattr(embedding, 'embedding'):
            embedding_values = embedding.embedding
        else:
            embedding_values = embedding['embedding']
        
        # Normalize the embedding
        embedding_array = np.array(embedding_values)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
        
        return embedding_array.tolist()
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        # Return a zero vector of appropriate dimension
        return [0.0] * 768  # Default dimension for many embedding models

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    try:
        if not vec1 or not vec2:
            return 0.0
            
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Check if vectors have the same dimension
        if vec1.shape != vec2.shape:
            logging.warning(f"Vectors have different dimensions: {vec1.shape} vs {vec2.shape}")
            # Pad the shorter vector or truncate the longer one
            min_dim = min(len(vec1), len(vec2))
            vec1 = vec1[:min_dim]
            vec2 = vec2[:min_dim]
        
        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        vec1 = vec1 / norm1
        vec2 = vec2 / norm2
        
        # Calculate cosine similarity
        return float(np.dot(vec1, vec2))
    except Exception as e:
        logging.error(f"Error calculating similarity: {e}")
        return 0.0

def get_most_similar(query_embedding: List[float], embeddings: List[List[float]], k: int = 3) -> List[int]:
    """Find k most similar embeddings to the query embedding."""
    try:
        if not query_embedding or not embeddings:
            return []
            
        similarities = [
            cosine_similarity(query_embedding, emb)
            for emb in embeddings
        ]
        
        # Get indices of top k similar embeddings
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        return top_k_indices.tolist()
    except Exception as e:
        logging.error(f"Error finding similar embeddings: {e}")
        return [] 