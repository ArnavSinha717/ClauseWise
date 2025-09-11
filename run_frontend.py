#!/usr/bin/env python3
import subprocess
import sys

if __name__ == "__main__":
    print("🎨 Starting ClauseWise Frontend...")
    print("📍 Frontend: http://localhost:8501") 
    print("⚠️  Ensure backend is running at http://localhost:8000")
    print("-" * 50)
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "streamlit_app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])
