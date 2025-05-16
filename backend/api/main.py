import os
import tempfile
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import traceback
import subprocess

# Import local modules
from ..utils.database import init_db, store_document, store_chunk
from ..utils.document_processor import process_pdf, check_poppler_installed
from ..utils.rag import answer_query

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Document Ingestion and RAG API",
    description="API for ingesting PDF documents and answering questions",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    # Check if poppler is installed
    if not check_poppler_installed():
        print("WARNING: Poppler is not installed or not in PATH!")
        print("OCR capabilities will be limited. Install Poppler for full functionality.")
        print("  - macOS: brew install poppler")
        print("  - Ubuntu/Debian: sudo apt-get install poppler-utils")

# Request/Response models
class AnswerRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[dict] = []

class HealthResponse(BaseModel):
    status: str
    version: str
    poppler_installed: bool
    database_connected: bool

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health of the API and its dependencies.
    """
    try:
        # Check if poppler is installed
        poppler_installed = check_poppler_installed()
        
        # Check if database is connected
        init_db()  # This will raise an exception if the database is not available
        database_connected = True
    except Exception:
        database_connected = False
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "poppler_installed": poppler_installed,
        "database_connected": database_connected
    }

@app.post("/ingest", status_code=201)
async def ingest_documents(files: List[UploadFile] = File(...)):
    """
    Ingest multiple PDF documents.
    
    - Extract text
    - Chunk text
    - Generate embeddings
    - Store in database
    """
    if len(files) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Please upload at least 2 PDF files")
    
    # Check file types
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"File {file.filename} is not a PDF")
    
    # Check if poppler is installed first
    if not check_poppler_installed():
        print("WARNING: Poppler is not installed. OCR capabilities will be limited.")
    
    processed_docs = []
    
    for file in files:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        try:
            # Process PDF
            processed_doc = process_pdf(temp_path)
            
            # Store document in database
            document = store_document(
                processed_doc["filename"],
                processed_doc["total_pages"]
            )
            
            # Store chunks and embeddings
            for chunk in processed_doc["chunks"]:
                store_chunk(
                    document_id=document.id,
                    text=chunk["text"],
                    chunk_index=chunk["chunk_index"],
                    page_number=chunk["page_number"],
                    embedding=chunk["embedding"]
                )
            
            processed_docs.append({
                "filename": processed_doc["filename"],
                "total_pages": processed_doc["total_pages"],
                "total_chunks": len(processed_doc["chunks"])
            })
            
        except Exception as e:
            # Print full traceback for debugging
            print(f"Error processing {file.filename}:")
            traceback.print_exc()
            
            error_message = str(e)
            if "poppler" in error_message.lower():
                error_message += ". Is poppler installed and in PATH? Install with 'brew install poppler' on macOS or 'apt-get install poppler-utils' on Linux."
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error processing {file.filename}: {error_message}"
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    return {
        "message": f"Successfully processed {len(processed_docs)} documents",
        "documents": processed_docs
    }

@app.post("/answer", response_model=AnswerResponse)
async def answer_question(request: AnswerRequest):
    """
    Answer a question based on ingested documents.
    
    - Generate question embedding
    - Retrieve relevant document chunks
    - Generate answer using LLM
    """
    if not request.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Question cannot be empty")
    
    try:
        # Process query and generate answer
        result = answer_query(request.question)
        return result
    
    except Exception as e:
        # Print full traceback for debugging
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Error generating answer: {str(e)}")

# Run server directly if this file is executed
if __name__ == "__main__":
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("api.main:app", host=host, port=port, reload=True) 