# RAG and Document API Routes
# Endpoints for PDF ingestion, vector search, and document management

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)
api_router = APIRouter()

# Request/Response Models
class DocumentSearchRequest(BaseModel):
    query: str
    k: int = 5
    threshold: float = 0.0
    framework: Optional[str] = None

class DocumentSearchResult(BaseModel):
    document_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]

class DocumentSearchResponse(BaseModel):
    query: str
    results: List[DocumentSearchResult]
    total_results: int

class IngestResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    chunks_created: int = 0
    text: Optional[str] = None  # full extracted text so callers can re-use it

class VectorStoreStats(BaseModel):
    tenant_id: str
    total_vectors: int
    total_documents: int
    dimension: int
    index_type: str

# Initialize services lazily
_embedding_service = None
_vector_store_manager = None
_pdf_parser = None

def get_embedding_service():
    global _embedding_service
    if _embedding_service is None:
        from services.embedding_service import EmbeddingService
        api_key = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-8976aDc2b88Bc80C41')
        _embedding_service = EmbeddingService(api_key=api_key)
    return _embedding_service

def get_vector_store(tenant_id: str = "default"):
    global _vector_store_manager
    if _vector_store_manager is None:
        from services.vector_store import MultiTenantVectorStoreManager
        _vector_store_manager = MultiTenantVectorStoreManager
    return _vector_store_manager.get_store(tenant_id)

def get_pdf_parser():
    global _pdf_parser
    if _pdf_parser is None:
        from services.pdf_parser import PDFParserService
        _pdf_parser = PDFParserService()
    return _pdf_parser


@api_router.post("/documents/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Query(default="default")
):
    """
    Upload and ingest a PDF document into the RAG system.
    
    The document will be:
    1. Parsed for text content
    2. Split into chunks
    3. Embedded using OpenAI
    4. Stored in FAISS vector store
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        pdf_parser = get_pdf_parser()
        embedding_service = get_embedding_service()
        vector_store = get_vector_store(tenant_id)
        
        # Parse PDF
        parsed_pdf = pdf_parser.parse_pdf_bytes(content, file.filename)
        chunks = pdf_parser.chunk_document(parsed_pdf)
        
        if not chunks:
            return IngestResponse(
                success=False,
                message="No text content extracted from PDF",
                chunks_created=0
            )
        
        # Generate embeddings
        chunk_texts = [c['content'] for c in chunks]
        embeddings = await embedding_service.generate_embeddings(chunk_texts)
        
        # Store in vector store
        from services.vector_store import Document
        
        documents = []
        doc_hash = parsed_pdf.metadata.get('file_hash', 'doc')
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_id = f"{doc_hash}_{i}"
            documents.append(Document(
                id=doc_id,
                content=chunk['content'],
                metadata={
                    **chunk.get('metadata', {}),
                    'chunk_index': i,
                    'filename': file.filename
                },
                embedding_vector=embedding,
                tenant_id=tenant_id
            ))
        
        added_ids = vector_store.add_documents(documents)
        
        logger.info(f"Ingested PDF '{file.filename}' with {len(added_ids)} chunks")
        
        return IngestResponse(
            success=True,
            message=f"Document '{file.filename}' ingested successfully",
            document_id=doc_hash,
            chunks_created=len(added_ids),
            text=(parsed_pdf.text_content or "")[:200000],  # expose extracted text for downstream flows
        )
        
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@api_router.post("/documents/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    tenant_id: str = Query(default="default")
):
    """
    Semantic search across ingested documents.
    
    Returns the most relevant document chunks based on the query.
    """
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
    
    try:
        embedding_service = get_embedding_service()
        vector_store = get_vector_store(tenant_id)
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_single_embedding(request.query)
        
        # Build metadata filter
        metadata_filter = None
        if request.framework:
            metadata_filter = {"framework": request.framework}
        
        # Search vector store
        results = vector_store.search(
            query_embedding=query_embedding,
            k=request.k,
            threshold=request.threshold,
            metadata_filter=metadata_filter
        )
        
        formatted_results = []
        for doc_id, similarity, doc_data in results:
            formatted_results.append(DocumentSearchResult(
                document_id=doc_id,
                content=doc_data.get('content', ''),
                similarity_score=similarity,
                metadata=doc_data.get('metadata', {})
            ))
        
        return DocumentSearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results)
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@api_router.get("/documents/stats", response_model=VectorStoreStats)
async def get_vector_store_stats(tenant_id: str = Query(default="default")):
    """Get statistics about the vector store."""
    try:
        vector_store = get_vector_store(tenant_id)
        stats = vector_store.get_stats()
        return VectorStoreStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    tenant_id: str = Query(default="default")
):
    """Delete a document from the vector store."""
    try:
        vector_store = get_vector_store(tenant_id)
        success = vector_store.delete_document(document_id)
        
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/documents/rag-query")
async def rag_query(
    request: DocumentSearchRequest,
    tenant_id: str = Query(default="default")
):
    """
    RAG query endpoint - retrieves relevant context for LLM generation.
    
    Returns:
    - Retrieved document chunks as context
    - Source document metadata
    - Total context length
    """
    search_response = await search_documents(request, tenant_id)
    
    # Combine content for LLM context
    context_chunks = [r.content for r in search_response.results]
    combined_context = "\n\n---\n\n".join(context_chunks)
    
    return {
        "query": request.query,
        "context": combined_context,
        "context_length": len(combined_context),
        "sources": [
            {
                "document_id": r.document_id,
                "similarity": r.similarity_score,
                "metadata": r.metadata
            }
            for r in search_response.results
        ],
        "total_sources": len(search_response.results)
    }
