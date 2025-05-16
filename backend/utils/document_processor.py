import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import sys
import subprocess

# PDF processing
from pypdf import PdfReader
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except (ImportError, RuntimeError):
    PDF2IMAGE_AVAILABLE = False
import pytesseract

# LangChain components
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set OpenAI API key in environment
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
# Initialize OpenAI embeddings with minimal parameters
embeddings = OpenAIEmbeddings()

def check_poppler_installed():
    """Check if Poppler is installed and in PATH."""
    try:
        # Try to execute pdftoppm to see if it's in the PATH
        subprocess.run(["pdftoppm", "-v"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=False)
        return True
    except FileNotFoundError:
        return False

def extract_text_from_pdf(pdf_path: str) -> Tuple[List[str], int]:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (list of page texts, total pages)
    """
    pdf_reader = PdfReader(pdf_path)
    total_pages = len(pdf_reader.pages)
    page_texts = []
    
    # Check if poppler is installed if we need OCR
    poppler_available = check_poppler_installed() and PDF2IMAGE_AVAILABLE
    
    for page_num, page in enumerate(pdf_reader.pages):
        # First try to extract text directly
        text = page.extract_text()
        
        # If no text extracted and poppler is available, try OCR
        if not text.strip() and poppler_available:
            # Convert page to image
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
                    if images:
                        image = images[0]
                        # Use OCR to extract text
                        text = pytesseract.image_to_string(image)
            except Exception as e:
                print(f"OCR failed for page {page_num+1}: {str(e)}")
                # Fall back to empty text if OCR fails
                text = f"[Failed to extract text from page {page_num+1}]"
        elif not text.strip() and not poppler_available:
            # If poppler is not available, warn but continue with empty text
            text = f"[Text extraction failed for page {page_num+1}. Poppler not available for OCR.]"
        
        page_texts.append(text)
    
    return page_texts, total_pages

def chunk_text(texts: List[str], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks for better retrieval.
    
    Args:
        texts: List of texts to chunk (one per page)
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunk dictionaries with text, metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = []
    for page_num, page_text in enumerate(texts):
        if not page_text:
            continue
            
        # Modified for older langchain version
        page_chunks = text_splitter.split_text(page_text)
        
        for i, chunk_text in enumerate(page_chunks):
            chunks.append({
                "text": chunk_text,
                "page_number": page_num + 1,
                "chunk_index": i,
            })
    
    return chunks

def create_embeddings(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create embeddings for each text chunk.
    
    Args:
        chunks: List of chunk dictionaries
        
    Returns:
        List of chunks with embeddings added
    """
    texts = [chunk["text"] for chunk in chunks]
    chunk_embeddings = embeddings.embed_documents(texts)
    
    for i, embedding in enumerate(chunk_embeddings):
        chunks[i]["embedding"] = embedding
    
    return chunks

def process_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Process a PDF document: extract text, chunk it, create embeddings.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with filename, total_pages, and chunks
    """
    # Check if Poppler is installed first
    if not check_poppler_installed():
        print("Warning: Poppler is not installed or not in PATH. OCR capabilities will be limited.")
        print("Install Poppler with:")
        print("  - macOS: brew install poppler")
        print("  - Ubuntu/Debian: sudo apt-get install poppler-utils")
    
    # Extract text from PDF
    page_texts, total_pages = extract_text_from_pdf(pdf_path)
    
    # Split text into chunks
    chunks = chunk_text(page_texts)
    
    # Create embeddings for chunks
    chunks = create_embeddings(chunks)
    
    # Get filename from path
    filename = Path(pdf_path).name
    
    return {
        "filename": filename,
        "total_pages": total_pages,
        "chunks": chunks
    } 