"""
PDF Processing Service using PyMuPDF
Extracts text and metadata from PDF files
"""

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
from typing import List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from langchain.schema import Document

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF processing service using PyMuPDF"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Document]:
        """Extract text from PDF file and return as LangChain documents"""
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is not available. Please install it with: pip install PyMuPDF")
        
        try:
            # Open the PDF file
            doc = fitz.open(pdf_path)
            
            documents = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text from the page
                text = page.get_text()
                
                if text.strip():  # Only add pages with content
                    # Extract metadata
                    metadata = {
                        "page_number": page_num + 1,
                        "file_name": Path(pdf_path).name,
                        "file_path": str(pdf_path),
                        "file_type": "application/pdf",
                        "file_size": Path(pdf_path).stat().st_size,
                        "creation_date": datetime.now().isoformat(),
                        "last_modified_date": datetime.now().isoformat()
                    }
                    
                    # Create LangChain document
                    document = Document(
                        page_content=text,
                        metadata=metadata
                    )
                    
                    documents.append(document)
            
            doc.close()
            
            logger.info(f"Successfully extracted text from {len(documents)} pages of PDF: {pdf_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            raise
    
    def chunk_documents(
        self, 
        documents: List[Document], 
        chunk_size: int = 1000, 
        chunk_overlap: int = 100
    ) -> List[Document]:
        """Chunk documents into smaller pieces"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        try:
            # Create text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Split documents
            chunks = text_splitter.split_documents(documents)
            
            logger.info(f"Successfully chunked {len(documents)} documents into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk documents: {e}")
            raise
    
    def process_pdf(self, pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
        """Complete PDF processing pipeline"""
        try:
            # Extract text from PDF
            documents = self.extract_text_from_pdf(pdf_path)
            
            # Chunk the documents
            chunks = self.chunk_documents(documents, chunk_size, chunk_overlap)
            
            logger.info(f"Successfully processed PDF: {pdf_path} -> {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {e}")
            raise


# Global instance
pdf_processor = PDFProcessor()
