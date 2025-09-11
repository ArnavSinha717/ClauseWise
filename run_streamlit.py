#!/usr/bin/env python3
"""
Script to run the Streamlit frontend
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    print("🎨 Starting Legal Document Simplifier Frontend...")
    print("📍 Frontend will be available at: http://localhost:8501")
    print("⚠️  Make sure the backend API is running at http://localhost:8000")
    print("-" * 50)
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "streamlit_app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])