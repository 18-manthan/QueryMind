# Installation Guide

This guide provides detailed instructions for setting up the Document Ingestion and Retrieval System.

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose (if using the containerized PostgreSQL approach)
- PostgreSQL with PGVector extension (if not using Docker)
- OpenAI API key
- Poppler (required for PDF processing)

## Step 1: Clone Repository

If you received this as a ZIP file, extract it. Otherwise, navigate to the project directory.

## Step 2: Install Poppler (Required for PDF processing)

Poppler is necessary for proper PDF text extraction and OCR.

### macOS
```
brew install poppler
```

### Ubuntu/Debian
```
sudo apt-get install poppler-utils
```

### Windows
Download and install from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows)
- Add the bin folder to your PATH environment variable

## Step 3: Set Up the Database

### Option A: Using Docker (Recommended)

1. Navigate to the project directory:
   ```
   cd DocIngestApp
   ```

2. Start PostgreSQL with PGVector using Docker Compose:
   ```
   docker-compose up -d
   ```

3. Verify the container is running:
   ```
   docker ps
   ```
   You should see `docapp-postgres` running.

4. Enable PGVector extension in the database:
   ```
   docker exec -it docapp-postgres psql -U postgres -d docapp -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

### Option B: Using an Existing PostgreSQL Installation

1. Install PostgreSQL if not already installed.

2. Install the PGVector extension:
   ```
   # For Ubuntu/Debian
   sudo apt-get install postgresql-14-pgvector
   
   # For other systems, see: https://github.com/pgvector/pgvector
   ```

3. Create a database for the application:
   ```
   createdb docapp
   ```

4. Enable the PGVector extension for the database:
   ```
   psql -d docapp -c "CREATE EXTENSION vector;"
   ```

## Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```
   cp config.env .env
   ```

2. Edit the `.env` file with your settings:
   ```
   # If using Docker setup
   DATABASE_URL=postgresql://postgres:postgres@localhost/docapp
   
   # If using custom PostgreSQL setup
   DATABASE_URL=postgresql://username:password@localhost/docapp
   
   # Replace with your actual OpenAI API key
   OPENAI_API_KEY=your_openai_api_key
   ```

## Step 5: Install Dependencies

Install the required Python packages:

```
pip install -r requirements.txt
```

## Step 6: Initialize the Database

Run the database initialization script:

```
python init_db.py
```

## Step 7: Run the Application

1. Start both the backend API and Streamlit frontend with a single command:
   ```
   python run.py
   ```

2. The application will automatically open in your default web browser. If not, open:
   - Streamlit UI: [http://localhost:8501](http://localhost:8501)
   - FastAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Step 8: Using the Application

1. Upload at least 2 PDF documents using the sidebar.
2. Click "Process Documents" to extract text, create embeddings, and store in the database.
3. Ask questions in the chat interface to retrieve information from the documents.

## Alternative Setup (Using setup.sh)

For convenience, we've provided a setup script that checks dependencies and sets up the environment:

```
chmod +x setup.sh
./setup.sh
```

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running:
  ```
  docker ps  # If using Docker
  # or
  sudo systemctl status postgresql  # If using system install
  ```

- Check the connection string in the `.env` file.

### PDF Processing Issues

- Ensure your PDFs are not password-protected.
- If OCR is not working, ensure you have Poppler and Tesseract OCR installed:
  ```
  # Ubuntu/Debian
  sudo apt-get install tesseract-ocr poppler-utils
  # macOS
  brew install tesseract poppler
  ```

### API Key Issues

- Verify your OpenAI API key is correct and has available credits.
- Ensure the OPENAI_API_KEY variable is set in your `.env` file.

### Port Conflicts

If you have services already running on ports 8000 or 8501:
1. Stop those services or change the ports in the `.env` file.
2. Update API_PORT to a free port number. 