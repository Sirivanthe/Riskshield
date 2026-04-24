# FAISS Vector Store Service
# Production-ready vector store with persistence and multi-tenancy support

import os
import json
import numpy as np
import faiss
import logging
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Represents a document chunk in the vector store."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding_vector: List[float]
    tenant_id: str = "default"

class FAISSVectorStore:
    """
    Production FAISS vector store with:
    - Multi-tenancy support (database-per-tenant)
    - Persistence to disk
    - Metadata storage
    - Similarity search with filtering
    """
    
    def __init__(
        self, 
        dimension: int = 1536, 
        index_path: str = None,
        tenant_id: str = "default"
    ):
        self.dimension = dimension
        self.tenant_id = tenant_id
        self.base_path = index_path or os.environ.get('FAISS_INDEX_PATH', './data/faiss_index')
        self.index_path = os.path.join(self.base_path, tenant_id)
        
        os.makedirs(self.index_path, exist_ok=True)
        
        self.index = self._load_or_create_index()
        self.docstore = self._load_or_create_docstore()
        self.id_to_index = self._load_or_create_id_mapping()
        
        logger.info(f"Initialized FAISS store for tenant '{tenant_id}' with {self.index.ntotal} vectors")
    
    def _load_or_create_index(self) -> faiss.Index:
        """Load existing index or create new one."""
        index_file = os.path.join(self.index_path, 'index.faiss')
        
        if os.path.exists(index_file):
            logger.info(f"Loading existing FAISS index from {index_file}")
            return faiss.read_index(index_file)
        
        logger.info("Creating new FAISS index (IndexFlatIP for cosine similarity)")
        # Use Inner Product index (works like cosine similarity with normalized vectors)
        index = faiss.IndexFlatIP(self.dimension)
        return index
    
    def _load_or_create_docstore(self) -> Dict:
        """Load document store or create new one."""
        docstore_file = os.path.join(self.index_path, 'docstore.json')
        
        if os.path.exists(docstore_file):
            with open(docstore_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_or_create_id_mapping(self) -> Dict[str, int]:
        """Load ID to index mapping."""
        mapping_file = os.path.join(self.index_path, 'id_mapping.json')
        
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector for cosine similarity."""
        norm = np.linalg.norm(vector)
        if norm > 0:
            return vector / norm
        return vector
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        if not documents:
            return []
        
        added_ids = []
        vectors = []
        
        for doc in documents:
            vector = np.array(doc.embedding_vector, dtype='float32').reshape(1, -1)
            vector = self._normalize_vector(vector)
            vectors.append(vector)
            
            self.docstore[doc.id] = {
                'content': doc.content,
                'metadata': doc.metadata,
                'tenant_id': doc.tenant_id,
                'added_at': datetime.now(timezone.utc).isoformat()
            }
            
            added_ids.append(doc.id)
        
        vectors_array = np.vstack(vectors).astype('float32')
        start_idx = self.index.ntotal
        self.index.add(vectors_array)
        
        for i, doc_id in enumerate(added_ids):
            self.id_to_index[doc_id] = start_idx + i
        
        self.save()
        logger.info(f"Added {len(added_ids)} documents to vector store")
        return added_ids
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        threshold: float = 0.0,
        metadata_filter: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar documents.
        
        Returns: List of (document_id, similarity_score, document_data) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        query_vector = np.array(query_embedding, dtype='float32').reshape(1, -1)
        query_vector = self._normalize_vector(query_vector)
        
        # Search more than k to allow for filtering
        search_k = min(k * 3, self.index.ntotal)
        similarities, indices = self.index.search(query_vector, search_k)
        
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if idx == -1:
                continue
            
            doc_id = self._find_doc_id_by_index(int(idx))
            if not doc_id:
                continue
            
            doc = self.docstore.get(doc_id)
            if not doc or doc.get('deleted', False):
                continue
            
            # Apply metadata filter
            if metadata_filter:
                match = all(
                    doc.get('metadata', {}).get(key) == value
                    for key, value in metadata_filter.items()
                )
                if not match:
                    continue
            
            if similarity >= threshold:
                results.append((doc_id, float(similarity), doc))
            
            if len(results) >= k:
                break
        
        return results
    
    def _find_doc_id_by_index(self, index: int) -> Optional[str]:
        """Find document ID from index position."""
        for doc_id, idx in self.id_to_index.items():
            if idx == index:
                return doc_id
        return None
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID."""
        return self.docstore.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Soft delete a document."""
        if doc_id not in self.docstore:
            return False
        
        self.docstore[doc_id]['deleted'] = True
        self.id_to_index.pop(doc_id, None)
        self.save()
        return True
    
    def save(self):
        """Persist index and metadata to disk."""
        os.makedirs(self.index_path, exist_ok=True)
        
        faiss.write_index(self.index, os.path.join(self.index_path, 'index.faiss'))
        
        with open(os.path.join(self.index_path, 'docstore.json'), 'w') as f:
            json.dump(self.docstore, f)
        
        with open(os.path.join(self.index_path, 'id_mapping.json'), 'w') as f:
            json.dump(self.id_to_index, f)
    
    def get_stats(self) -> Dict:
        """Get vector store statistics."""
        return {
            'tenant_id': self.tenant_id,
            'total_vectors': self.index.ntotal,
            'total_documents': len([d for d in self.docstore.values() if not d.get('deleted')]),
            'dimension': self.dimension,
            'index_type': type(self.index).__name__
        }
    
    def clear(self):
        """Clear all data (for testing)."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.docstore = {}
        self.id_to_index = {}
        self.save()


class MultiTenantVectorStoreManager:
    """Manages vector stores for multiple tenants (database-per-tenant)."""
    
    _instances: Dict[str, FAISSVectorStore] = {}
    
    @classmethod
    def get_store(cls, tenant_id: str, dimension: int = 1536) -> FAISSVectorStore:
        """Get or create a vector store for a tenant."""
        if tenant_id not in cls._instances:
            cls._instances[tenant_id] = FAISSVectorStore(
                dimension=dimension,
                tenant_id=tenant_id
            )
        return cls._instances[tenant_id]
    
    @classmethod
    def delete_tenant(cls, tenant_id: str) -> bool:
        """Delete a tenant's vector store."""
        if tenant_id in cls._instances:
            store = cls._instances[tenant_id]
            store.clear()
            del cls._instances[tenant_id]
            return True
        return False
    
    @classmethod
    def list_tenants(cls) -> List[str]:
        """List all active tenants."""
        return list(cls._instances.keys())
