# PDF Parser Service using PyMuPDF
# Extracts text from PDF documents for RAG ingestion

import fitz  # PyMuPDF
import os
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import tempfile

logger = logging.getLogger(__name__)

@dataclass
class PDFPage:
    """Represents a parsed PDF page."""
    page_number: int
    text: str
    metadata: Dict[str, Any]

@dataclass
class ParsedPDF:
    """Represents a fully parsed PDF document."""
    filename: str
    title: str
    author: str
    total_pages: int
    pages: List[PDFPage]
    metadata: Dict[str, Any]
    text_content: str
    
class PDFParserService:
    """
    PDF parsing service using PyMuPDF (fitz).
    Extracts text, metadata, and structure from PDF documents.
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def parse_pdf_file(self, file_path: str) -> ParsedPDF:
        """Parse a PDF file from disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        doc = fitz.open(file_path)
        return self._parse_document(doc, os.path.basename(file_path))
    
    def parse_pdf_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> ParsedPDF:
        """Parse PDF from bytes."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        return self._parse_document(doc, filename)
    
    def _parse_document(self, doc: fitz.Document, filename: str) -> ParsedPDF:
        """Internal method to parse a PyMuPDF document."""
        pages = []
        all_text = []
        
        # Extract metadata
        metadata = doc.metadata or {}
        title = metadata.get('title', '') or filename.replace('.pdf', '')
        author = metadata.get('author', 'Unknown')
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            # Clean up text
            text = self._clean_text(text)
            
            if text.strip():
                pages.append(PDFPage(
                    page_number=page_num + 1,
                    text=text,
                    metadata={
                        'width': page.rect.width,
                        'height': page.rect.height
                    }
                ))
                all_text.append(text)

        total_pages = len(doc)
        doc.close()

        full_text = "\n\n".join(all_text)

        return ParsedPDF(
            filename=filename,
            title=title,
            author=author,
            total_pages=total_pages,
            pages=pages,
            metadata={
                **metadata,
                'parsed_at': datetime.now(timezone.utc).isoformat(),
                'file_hash': hashlib.md5(full_text.encode()).hexdigest()
            },
            text_content=full_text
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers (common patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        # Remove headers/footers (lines that are very short at start/end)
        lines = text.split('\n')
        if lines and len(lines[0]) < 20:
            lines = lines[1:]
        if lines and len(lines[-1]) < 20:
            lines = lines[:-1]
        return '\n'.join(lines).strip()
    
    def chunk_document(
        self, 
        parsed_pdf: ParsedPDF,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Split parsed PDF into chunks for embedding.
        
        Returns list of chunks with content and metadata.
        """
        text = parsed_pdf.text_content
        chunks = []
        
        # Split into words
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) < 50:  # Skip very short chunks
                continue
            
            chunk_data = {
                'content': chunk_text,
                'chunk_index': len(chunks),
                'word_count': len(chunk_words),
                'char_count': len(chunk_text)
            }
            
            if include_metadata:
                chunk_data['metadata'] = {
                    'source': parsed_pdf.filename,
                    'title': parsed_pdf.title,
                    'author': parsed_pdf.author,
                    'total_pages': parsed_pdf.total_pages,
                    'document_hash': parsed_pdf.metadata.get('file_hash', '')
                }
            
            chunks.append(chunk_data)
        
        logger.info(f"Created {len(chunks)} chunks from PDF '{parsed_pdf.filename}'")
        return chunks
    
    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF (basic implementation)."""
        doc = fitz.open(file_path)
        tables = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Use blocks to identify potential table structures
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block.get("type") == 0:  # Text block
                    lines = block.get("lines", [])
                    if len(lines) > 2:  # Potential table
                        table_text = []
                        for line in lines:
                            spans = line.get("spans", [])
                            row = [span.get("text", "") for span in spans]
                            if row:
                                table_text.append(row)
                        
                        if table_text:
                            tables.append({
                                'page': page_num + 1,
                                'data': table_text
                            })
        
        doc.close()
        return tables


class DocumentIngestionService:
    """Service for ingesting documents into the vector store."""
    
    def __init__(self, pdf_parser: PDFParserService = None):
        self.pdf_parser = pdf_parser or PDFParserService()
    
    async def ingest_pdf(
        self,
        file_path: str = None,
        file_bytes: bytes = None,
        filename: str = "document.pdf",
        embedding_service = None,
        vector_store = None,
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Ingest a PDF document into the vector store.
        
        Args:
            file_path: Path to PDF file
            file_bytes: PDF content as bytes
            filename: Name of the file
            embedding_service: Service to generate embeddings
            vector_store: Vector store to save documents
            tenant_id: Tenant identifier for multi-tenancy
            
        Returns:
            Ingestion result with stats
        """
        # Parse PDF
        if file_bytes:
            parsed_pdf = self.pdf_parser.parse_pdf_bytes(file_bytes, filename)
        elif file_path:
            parsed_pdf = self.pdf_parser.parse_pdf_file(file_path)
        else:
            raise ValueError("Either file_path or file_bytes must be provided")
        
        # Create chunks
        chunks = self.pdf_parser.chunk_document(parsed_pdf)
        
        if not chunks:
            return {
                'success': False,
                'message': 'No text content extracted from PDF',
                'chunks_created': 0
            }
        
        # Generate embeddings
        if embedding_service:
            chunk_texts = [c['content'] for c in chunks]
            embeddings = await embedding_service.generate_embeddings(chunk_texts)
        else:
            # Return chunks without embeddings if no service provided
            return {
                'success': True,
                'message': 'PDF parsed successfully (no embeddings generated)',
                'chunks': chunks,
                'document_title': parsed_pdf.title,
                'total_pages': parsed_pdf.total_pages
            }
        
        # Store in vector store
        if vector_store:
            from services.vector_store import Document
            
            documents = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc_id = f"{parsed_pdf.metadata.get('file_hash', 'doc')}_{i}"
                documents.append(Document(
                    id=doc_id,
                    content=chunk['content'],
                    metadata=chunk.get('metadata', {}),
                    embedding_vector=embedding,
                    tenant_id=tenant_id
                ))
            
            added_ids = vector_store.add_documents(documents)
            
            return {
                'success': True,
                'message': f'PDF ingested successfully',
                'document_id': parsed_pdf.metadata.get('file_hash'),
                'document_title': parsed_pdf.title,
                'total_pages': parsed_pdf.total_pages,
                'chunks_created': len(added_ids),
                'chunk_ids': added_ids
            }
        
        return {
            'success': True,
            'message': 'PDF parsed and embedded (not stored)',
            'chunks_created': len(chunks),
            'embeddings_generated': len(embeddings)
        }
