#!/usr/bin/env python3
import uvicorn
import os
import sys

# Add backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    print("🚀 Starting ClauseWise Backend API...")
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("-" * 50)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        reload_dirs=["backend"]
    )
