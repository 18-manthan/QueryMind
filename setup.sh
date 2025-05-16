#!/bin/bash

echo "===== DocIngestApp Setup Script ====="
echo "This script will set up the environment for DocIngestApp"
echo

# Check Python version
python_version=$(python3 -V 2>&1 | awk '{print $2}')
if [[ -z "$python_version" ]]; then
  echo "❌ Python 3 not found. Please install Python 3.8 or higher."
  exit 1
else
  echo "✅ Found Python $python_version"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. It's recommended for running PostgreSQL with PGVector."
  echo "   You can still use a local PostgreSQL installation."
else
  echo "✅ Docker is installed"
  
  # Check if Docker Compose is installed
  if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. It's recommended for running PostgreSQL with PGVector."
  else
    echo "✅ Docker Compose is installed"
  fi
fi

# Check if Poppler is installed (needed for pdf2image)
if ! command -v pdftoppm &> /dev/null; then
  echo "❌ Poppler not found. It's required for PDF processing."
  echo "   Install with:"
  echo "   - macOS: brew install poppler"
  echo "   - Ubuntu/Debian: sudo apt-get install poppler-utils"
  echo "   - Windows: Follow instructions at https://github.com/oschwartz10612/poppler-windows"
  echo ""
  echo "   After installing Poppler, run this setup script again."
  exit 1
else
  echo "✅ Poppler is installed"
fi

# Check if PostgreSQL is running if not using Docker
if ! docker ps | grep docapp-postgres &> /dev/null; then
  echo "⚠️ DocApp PostgreSQL container not running. You may need to start it with:"
  echo "   docker-compose up -d"
fi

# Setup environment file
if [ ! -f .env ]; then
  echo "ℹ️ Creating .env file from config.env"
  cp config.env .env
  echo "⚠️ Please edit .env file to add your OpenAI API key"
else
  echo "✅ .env file exists"
  
  # Check if API key is set
  if grep -q "your_openai_api_key" .env; then
    echo "⚠️ OpenAI API key needs to be set in .env file"
  fi
fi

# Install Python dependencies
echo "ℹ️ Installing Python dependencies..."
python3 -m pip install -r requirements.txt

# Initialize database
echo "ℹ️ Checking Docker container status..."
if docker ps | grep docapp-postgres &> /dev/null; then
  echo "ℹ️ Initializing database schema..."
  python3 init_db.py
else
  echo "⚠️ PostgreSQL container not running. Start it with 'docker-compose up -d'"
  echo "   After starting the container, run 'python3 init_db.py' to initialize the database."
fi

echo
echo "===== Setup Complete ====="
echo
echo "To run the application:"
echo "1. Ensure PostgreSQL with PGVector is running"
echo "2. Run: python3 run.py"
echo
echo "If you encounter any issues:"
echo "- Check the README.md and INSTALL.md files for troubleshooting"
echo "- Verify your OpenAI API key is correctly set in .env"
echo "- Ensure PostgreSQL is running and PGVector extension is enabled"
echo
echo "If you encounter PDF processing errors:"
echo "- Make sure Poppler is correctly installed and in your PATH"
echo 