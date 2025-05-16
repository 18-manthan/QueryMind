import os
import streamlit as st
import requests
from datetime import datetime
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define API URL
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}"

# Set page configuration
st.set_page_config(
    page_title="Document RAG System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "documents" not in st.session_state:
    st.session_state.documents = []

if "api_status" not in st.session_state:
    st.session_state.api_status = "unknown"

if "poppler_installed" not in st.session_state:
    st.session_state.poppler_installed = False

if "database_connected" not in st.session_state:
    st.session_state.database_connected = False


# Functions
def check_api_health():
    """Check if the backend API is available and get health status."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            st.session_state.api_status = "connected"
            st.session_state.poppler_installed = health_data.get("poppler_installed", False)
            st.session_state.database_connected = health_data.get("database_connected", False)
            return True
        else:
            st.session_state.api_status = "error"
            return False
    except requests.exceptions.RequestException:
        st.session_state.api_status = "error"
        return False


def upload_documents(files):
    """Upload PDF files to the backend API."""
    if len(files) < 2:
        st.error("Please upload at least 2 PDF files")
        return False
    
    # Verify API connection first
    if not check_api_health():
        st.error(f"Cannot connect to backend API at {API_URL}. Please ensure the backend server is running.")
        return False
    
    # Create file data
    files_data = [("files", (file.name, file.getvalue(), "application/pdf")) for file in files]
    
    with st.spinner("Uploading and processing documents..."):
        try:
            response = requests.post(f"{API_URL}/ingest", files=files_data, timeout=120)
            
            if response.status_code == 201:
                result = response.json()
                st.session_state.documents.extend(result["documents"])
                return True
            else:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Unknown error")
                except:
                    error_msg = response.text
                
                st.error(f"Error: {response.status_code} - {error_msg}")
                
                # If poppler error, show installation instructions
                if "poppler" in error_msg.lower():
                    st.warning("""
                    Poppler is required for PDF processing.
                    
                    Install with:
                    - macOS: `brew install poppler`
                    - Ubuntu/Debian: `sudo apt-get install poppler-utils`
                    - Windows: Download from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows)
                    """)
                return False
        except requests.exceptions.ConnectionError:
            st.error(f"Connection error: Unable to connect to backend at {API_URL}. Please ensure the backend server is running.")
            return False
        except requests.exceptions.Timeout:
            st.error("Timeout: The document processing is taking too long. Try with smaller documents or check the backend server.")
            return False
        except Exception as e:
            st.error(f"Error uploading documents: {str(e)}")
            return False


def ask_question(question):
    """Send a question to the backend API and get the answer."""
    if not question.strip():
        return None
    
    # Verify API connection first
    if not check_api_health():
        st.error(f"Cannot connect to backend API at {API_URL}. Please ensure the backend server is running.")
        return None
    
    with st.spinner("Generating answer..."):
        try:
            response = requests.post(
                f"{API_URL}/answer",
                json={"question": question},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Unknown error")
                except:
                    error_msg = response.text
                
                st.error(f"Error: {response.status_code} - {error_msg}")
                return None
        except requests.exceptions.ConnectionError:
            st.error(f"Connection error: Unable to connect to backend at {API_URL}. Please ensure the backend server is running.")
            return None
        except requests.exceptions.Timeout:
            st.error("Timeout: The answer generation is taking too long. Try a simpler question or check the backend server.")
            return None
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return None


def display_chat_history():
    """Display the chat history."""
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.chat_message("user").write(chat["content"])
        else:
            with st.chat_message("assistant"):
                st.write(chat["content"])
                if "sources" in chat and chat["sources"]:
                    with st.expander("View Sources"):
                        for i, source in enumerate(chat["sources"]):
                            st.markdown(f"**Source {i+1}** (Document {source['document_id']}, Page {source['page_number']})")
                            st.text(source['text_snippet'])


# Main application
def main():
    # Sidebar
    with st.sidebar:
        st.title("Document RAG System 📚")
        st.markdown("---")
        
        # API status indicator
        if st.session_state.api_status == "unknown":
            check_api_health()
            
        if st.session_state.api_status == "connected":
            st.success("✅ Connected to backend API")
            
            # Show dependency status
            with st.expander("System Status"):
                if st.session_state.database_connected:
                    st.success("✅ Database connection successful")
                else:
                    st.error("❌ Database connection failed")
                    
                if st.session_state.poppler_installed:
                    st.success("✅ Poppler is installed (PDF processing works)")
                else:
                    st.warning("⚠️ Poppler is not installed. PDF processing may be limited.")
                    st.markdown("""
                    **Install Poppler for full PDF processing:**
                    - macOS: `brew install poppler`
                    - Ubuntu/Debian: `sudo apt-get install poppler-utils`
                    - Windows: [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows)
                    """)
        else:
            st.error("❌ Not connected to backend API")
            if st.button("Retry Connection"):
                check_api_health()
        
        # Document upload section
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload PDF files (minimum 2 files)", 
            type=["pdf"], 
            accept_multiple_files=True
        )
        
        if st.button("Process Documents") and uploaded_files:
            success = upload_documents(uploaded_files)
            if success:
                st.success(f"Successfully processed {len(uploaded_files)} documents")
        
        # Ingested documents display
        if st.session_state.documents:
            st.subheader("Ingested Documents")
            for i, doc in enumerate(st.session_state.documents):
                st.markdown(f"**{i+1}. {doc['filename']}**")
                st.text(f"Pages: {doc['total_pages']}, Chunks: {doc['total_chunks']}")
        
        st.markdown("---")
        
        # Settings and About
        with st.expander("About"):
            st.markdown("""
            This application allows you to upload PDF documents and ask questions about their content.
            
            Built with:
            - Streamlit
            - FastAPI
            - PostgreSQL + PGVector
            - OpenAI API
            """)
        
        with st.expander("Troubleshooting"):
            st.markdown("""
            **If you're having issues:**
            
            1. Ensure the backend server is running
            2. Check that PostgreSQL with PGVector extension is running
            3. Verify your OpenAI API key is correct in the .env file
            4. Check the terminal for error messages
            
            **PDF Processing Issues:**
            
            If you're seeing "Poppler not installed" errors:
            - macOS: `brew install poppler`
            - Ubuntu/Debian: `sudo apt-get install poppler-utils`
            - Windows: [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows)
            """)
    
    # Main content area
    st.title("Document Q&A")
    
    # Check if backend is connected
    if st.session_state.api_status != "connected":
        st.warning("⚠️ Not connected to the backend API. Please check if the backend server is running.")
        
        if st.button("Check Connection"):
            if check_api_health():
                st.success("✅ Successfully connected to backend API!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Could not connect to the backend API. Please check if the server is running.")
        return
    
    # Check if documents are uploaded
    if not st.session_state.documents:
        st.info("Please upload at least 2 PDF documents using the sidebar to get started.")
        return
    
    # Display chat history
    display_chat_history()
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents"):
        # Add user question to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Display user message
        st.chat_message("user").write(prompt)
        
        # Get answer from API
        response = ask_question(prompt)
        
        if response:
            # Add assistant response to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["sources"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response["answer"])
                
                # Display sources if available
                if response["sources"]:
                    with st.expander("View Sources"):
                        for i, source in enumerate(response["sources"]):
                            st.markdown(f"**Source {i+1}** (Document {source['document_id']}, Page {source['page_number']})")
                            st.text(source['text_snippet'])
        
if __name__ == "__main__":
    main() 