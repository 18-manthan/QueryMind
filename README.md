# Document Ingestion and Retrieval System

A RAG-based system for ingesting PDF documents and answering questions using the content.

## Features

- PDF document ingestion and text extraction
- Vector-based document retrieval with PostgreSQL + PGVector
- Question answering with LLM integration
- Streamlit UI for document upload and querying

## Setup Instructions

### Option 1: Using Docker for PostgreSQL

1. Make sure you have Docker and Docker Compose installed.

2. Start the PostgreSQL database with PGVector:
   ```
   cd DocIngestApp
   docker-compose up -d
   ```

3. Rename `config.env` to `.env` and add your OpenAI API key:
   ```
   mv config.env .env
   # Edit .env and add your OpenAI API key
   ```

4. Install required packages:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python run.py
   ```

### Option 2: Using Your Own PostgreSQL Installation

1. Install PostgreSQL and the PGVector extension:
   - Follow instructions at https://github.com/pgvector/pgvector

2. Create a database for the application:
   ```
   createdb docapp
   ```

3. Install the PGVector extension in your database:
   ```
   psql -d docapp -c "CREATE EXTENSION vector;"
   ```

4. Rename `config.env` to `.env` and update the database connection string:
   ```
   mv config.env .env
   # Edit .env with your database connection details and OpenAI API key
   ```

5. Install required packages:
   ```
   pip install -r requirements.txt
   ```

6. Run the application:
   ```
   python run.py
   ```

## Usage

1. The application will start both the backend API and the Streamlit frontend
2. Open the Streamlit UI in your browser (usually at http://localhost:8501)
3. Upload at least 2 PDF documents using the sidebar
4. Use the chat interface to ask questions about the document content

## Architecture

- **Backend**: FastAPI-based API with endpoints for document ingestion and question answering
- **Database**: PostgreSQL with PGVector extension for vector embeddings
- **Frontend**: Streamlit UI for user interaction
- **RAG Pipeline**: Document chunking, embedding, retrieval, and LLM integration

## API Endpoints

- **POST /ingest**: Upload and process PDF documents
- **POST /answer**: Ask questions about ingested documents

## Implementation Details

### Document Processing

The system processes PDFs through the following steps:
1. Text extraction using PyPDF (with OCR fallback)
2. Chunking with RecursiveCharacterTextSplitter (1000 token chunks with 200 token overlap)
3. Embedding generation using OpenAI's text-embedding model
4. Storage in PostgreSQL with PGVector for efficient vector search

### Retrieval Augmented Generation (RAG)

When answering questions:
1. The question is embedded using the same model
2. The most similar document chunks are retrieved via cosine similarity
3. These chunks are used as context for the LLM
4. The LLM generates an answer based on the retrieved context

### Accuracy Improvements

The system includes several techniques to improve retrieval accuracy:
- Optimal chunk sizing with overlap to maintain context across chunks
- Cosine similarity search for semantic matching
- Page and chunk metadata to maintain document provenance
- Source attribution in responses to increase transparency

## Extending the System

- Add authentication and user management
- Support more document types (Word, HTML, etc.)
- Implement document-level filtering
- Add text highlights and PDF viewers
- Implement response streaming 