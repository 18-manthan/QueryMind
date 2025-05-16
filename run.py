#!/usr/bin/env python3
import os
import subprocess
import time
import signal
import sys
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default settings
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")

# Find the Python executable
PYTHON_PATH = shutil.which('python3') or shutil.which('python')
if not PYTHON_PATH:
    # Try using the virtual environment Python if we can find it
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'venv', 'bin', 'python')
    if os.path.exists(venv_python):
        PYTHON_PATH = venv_python
    else:
        print("Error: Python executable not found. Please activate your virtual environment.")
        sys.exit(1)

def run_backend():
    """Run the FastAPI backend server."""
    print(f"Starting backend server using {PYTHON_PATH}...")
    try:
        return subprocess.Popen(
            [PYTHON_PATH, "-m", "uvicorn", "backend.api.main:app", "--host", "127.0.0.1", "--port", API_PORT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
    except Exception as e:
        print(f"Error starting backend: {e}")
        sys.exit(1)

def run_frontend():
    """Run the Streamlit frontend."""
    print("Starting Streamlit frontend...")
    try:
        streamlit_cmd = shutil.which('streamlit')
        if not streamlit_cmd:
            # Try using the virtual environment streamlit if available
            venv_streamlit = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'venv', 'bin', 'streamlit')
            if os.path.exists(venv_streamlit):
                streamlit_cmd = venv_streamlit
            else:
                print("Error: streamlit command not found. Please ensure it's installed.")
                sys.exit(1)
                
        return subprocess.Popen(
            [streamlit_cmd, "run", "frontend/app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
    except Exception as e:
        print(f"Error starting frontend: {e}")
        sys.exit(1)

def show_process_output(process, prefix):
    """Show output from a subprocess."""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"{prefix}: {output.strip()}")

def main():
    """Run both backend and frontend services."""
    print("Starting Document RAG System...")
    
    # Start backend
    backend_process = run_backend()
    
    # Wait for backend to start
    time.sleep(2)
    
    # Start frontend
    frontend_process = run_frontend()
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        print("\nShutting down...")
        frontend_process.terminate()
        backend_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Display output from processes
    try:
        # Show some initial information
        print("\n" + "="*50)
        print(f"Backend API running at: http://{API_HOST}:{API_PORT}")
        print(f"Streamlit UI will open in your browser automatically")
        print("="*50 + "\n")
        
        # Wait for processes to complete (they won't unless terminated)
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        frontend_process.terminate()
        backend_process.terminate()
    
if __name__ == "__main__":
    main() 