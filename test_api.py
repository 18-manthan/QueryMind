#!/usr/bin/env python3
"""
Test script for the Document Ingestion and RAG API.
This script demonstrates how to use the API for ingesting documents and asking questions.
"""

import os
import requests
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default settings
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}"

def ingest_documents(pdf_files):
    """Ingest PDF documents through the API."""
    if len(pdf_files) < 2:
        print("Error: Please provide at least 2 PDF files")
        return False
    
    # Prepare files for upload
    files = []
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            print(f"Error: File not found: {pdf_file}")
            return False
        
        if not pdf_file.lower().endswith('.pdf'):
            print(f"Error: File is not a PDF: {pdf_file}")
            return False
        
        files.append(("files", (os.path.basename(pdf_file), open(pdf_file, "rb"), "application/pdf")))
    
    print(f"Ingesting {len(files)} documents...")
    
    # Make API request
    try:
        response = requests.post(f"{API_URL}/ingest", files=files)
        
        # Close file handles
        for _, (_, file_handle, _) in enumerate(files):
            file_handle.close()
            
        if response.status_code == 201:
            result = response.json()
            print(f"Success! {len(result['documents'])} documents processed")
            for doc in result["documents"]:
                print(f"  - {doc['filename']}: {doc['total_pages']} pages, {doc['total_chunks']} chunks")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        
        # Close file handles in case of exception
        for _, (_, file_handle, _) in enumerate(files):
            file_handle.close()
            
        return False


def ask_question(question):
    """Ask a question through the API."""
    if not question.strip():
        print("Error: Question cannot be empty")
        return False
    
    print(f"Question: {question}")
    print("Generating answer...")
    
    # Make API request
    try:
        response = requests.post(
            f"{API_URL}/answer",
            json={"question": question}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\nAnswer:")
            print(result["answer"])
            
            if result["sources"]:
                print("\nSources:")
                for i, source in enumerate(result["sources"]):
                    print(f"  - Document {source['document_id']}, Page {source['page_number']}")
                    
            return True
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test the Document Ingestion and RAG API")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest PDF documents")
    ingest_parser.add_argument("pdfs", nargs="+", help="PDF files to ingest (minimum 2)")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("question", help="Question to ask")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        ingest_documents(args.pdfs)
    elif args.command == "ask":
        ask_question(args.question)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 