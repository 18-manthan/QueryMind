#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from backend.utils.database import init_db

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    print("Initializing database schemas...")
    init_db()
    print("Database initialization complete!") 