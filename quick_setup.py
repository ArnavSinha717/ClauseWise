#!/usr/bin/env python3
"""
Quick Setup Script for ClauseWise Legal Document Simplifier
This script sets up the entire environment in one go.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("🏛️  ClauseWise - Legal Document Simplifier")
    print("   AI-Powered Legal Document Analysis & Simplification")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def create_directories():
    """Create all necessary directories"""
    directories = [
        "backend",
        "backend/models", 
        "backend/services",
        "backend/legal_datasets",
        "temp",
        "chroma_db",
        "logs"
    ]
    
    print("\n📁 Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")

def create_init_files():
    """Create __init__.py files for Python packages"""
    init_files = [
        "backend/__init__.py",
        "backend/models/__init__.py",
        "backend/services/__init__.py"
    ]
    
    print("\n📝 Creating package files...")
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Package initialization file\n")
            print(f"   ✅ {init_file}")

def setup_environment():
    """Create environment file"""
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"\n✅ {env_file} already exists")
        return
    
    print(f"\n🔧 Creating {env_file}...")
    
    env_content = """# Gemini API Configuration
GOOGLE_API_KEY=your_gemini_api_key_here

# Server Configuration  
API_HOST=0.0.0.0
API_PORT=8000

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=legal_documents

# Application Settings
MAX_FILE_SIZE_MB=10
RATE_LIMIT_REQUESTS_PER_MINUTE=15
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Legal Knowledge Base
LEGAL_DATASETS_PATH=./backend/legal_datasets
ENABLE_LEGAL_KB=true

# Logging
LOG_LEVEL=INFO
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"   ✅ Created {env_file}")
    print("   ⚠️  IMPORTANT: Update GOOGLE_API_KEY with your actual Gemini API key!")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        return False
    
    try:
        # Upgrade pip first
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Install dependencies
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        
        print("   ✅ All dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error installing dependencies: {e}")
        print("   💡 Try running manually: pip install -r requirements.txt")
        return False

def create_sample_legal_dataset():
    """Create a sample legal dataset for testing"""
    datasets_path = "backend/legal_datasets"
    sample_file = os.path.join(datasets_path, "sample_legal_data.json")
    
    if os.path.exists(sample_file):
        return
    
    print("\n📚 Creating sample legal dataset...")
    
    sample_data = [
        {
            "text": "A contract is a legally binding agreement between two or more parties. For a contract to be valid, it must have offer, acceptance, consideration, and legal capacity of parties.",
            "type": "definition",
            "topic": "contract_law"
        },
        {
            "text": "Indian Contract Act, 1872 governs contracts in India. Section 10 states that all agreements are contracts if made by free consent of parties competent to contract, for lawful consideration and with lawful object.",
            "type": "law",
            "topic": "indian_contract_act"
        },
        {
            "text": "A breach of contract occurs when one party fails to fulfill their obligations under the contract. Remedies include damages, specific performance, or contract rescission.",
            "type": "legal_concept", 
            "topic": "breach_of_contract"
        }
    ]
    
    import json
    with open(sample_file, "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"   ✅ Created sample dataset: {sample_file}")
    print("   💡 Add your own CSV/JSON legal datasets to this directory")

def create_run_scripts():
    """Create convenient run scripts"""
    print("\n🚀 Creating run scripts...")
    
    # Backend run script
    backend_script = """#!/usr/bin/env python3
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
"""
    
    with open("run_backend.py", "w") as f:
        f.write(backend_script)
    
    # Frontend run script  
    frontend_script = """#!/usr/bin/env python3
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
"""
    
    with open("run_frontend.py", "w") as f:
        f.write(frontend_script)
    
    # Make scripts executable on Unix systems
    if os.name != 'nt':  # Not Windows
        os.chmod("run_backend.py", 0o755)
        os.chmod("run_frontend.py", 0o755)
    
    print("   ✅ run_backend.py")
    print("   ✅ run_frontend.py")

def verify_setup():
    """Verify that setup is complete"""
    print("\n🔍 Verifying setup...")
    
    required_files = [
        ".env",
        "requirements.txt", 
        "backend/main.py",
        "backend/models/schemas.py",
        "backend/services/llm_service.py",
        "backend/services/vector_store.py", 
        "backend/services/document_processor.py",
        "streamlit_app.py",
        "run_backend.py",
        "run_frontend.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("   ❌ Missing files:")
        for file in missing_files:
            print(f"      - {file}")
        return False
    
    print("   ✅ All required files present")
    
    # Check directories
    required_dirs = ["backend", "backend/models", "backend/services", "chroma_db", "temp"]
    missing_dirs = []
    for directory in required_dirs:
        if not os.path.exists(directory):
            missing_dirs.append(directory)
    
    if missing_dirs:
        print("   ❌ Missing directories:")
        for directory in missing_dirs:
            print(f"      - {directory}")
        return False
    
    print("   ✅ All required directories present")
    return True

def print_instructions():
    """Print final setup instructions"""
    print("\n" + "=" * 60)
    print("🎉 ClauseWise Setup Complete!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("1. Get a Gemini API key from: https://makersuite.google.com/app/apikey")
    print("2. Update .env file with your API key:")
    print("   GOOGLE_API_KEY=your_actual_api_key_here")
    print()
    print("3. Start the backend:")
    print("   python run_backend.py")
    print()
    print("4. In another terminal, start the frontend:")
    print("   python run_frontend.py")
    print()
    print("5. Access the application:")
    print("   🌐 Frontend: http://localhost:8501")
    print("   📚 API Docs: http://localhost:8000/docs")
    
    print("\n📚 Adding Legal Datasets:")
    print("- Place CSV/JSON legal datasets in: backend/legal_datasets/")
    print("- Supported formats:")
    print("  • CSV with 'text', 'content', or 'judgment' columns")
    print("  • JSON with text content")
    
    print("\n🆘 Need Help?")
    print("- Check the README.md file")
    print("- Ensure you have a stable internet connection for Gemini API")
    print("- For issues, check the logs or API documentation")
    
    print("\n" + "=" * 60)

def main():
    """Main setup function"""
    print_banner()
    
    try:
        # Step 1: Check Python version
        check_python_version()
        
        # Step 2: Create directories
        create_directories()
        
        # Step 3: Create package files
        create_init_files()
        
        # Step 4: Setup environment
        setup_environment()
        
        # Step 5: Install dependencies
        deps_installed = install_dependencies()
        
        # Step 6: Create sample dataset
        create_sample_legal_dataset()
        
        # Step 7: Create run scripts
        create_run_scripts()
        
        # Step 8: Verify setup
        setup_complete = verify_setup()
        
        if setup_complete and deps_installed:
            print_instructions()
        else:
            print("\n❌ Setup incomplete. Please address the issues above.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()