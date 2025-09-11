#!/usr/bin/env python3
"""
Setup script to initialize the Legal Document Simplifier project
"""

import os
import subprocess
import sys

def create_directories():
    """Create necessary directories"""
    directories = [
        "backend",
        "backend/models",
        "backend/services",
        "vector_stores",
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies. Please install manually using:")
        print("pip install -r requirements.txt")
        return False
    return True

def setup_environment():
    """Set up environment file if it doesn't exist"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"\n🔧 Creating {env_file} file...")
        with open(env_file, "w") as f:
            f.write("GOOGLE_API_KEY=your_gemini_api_key_here\n")
        print(f"✅ Created {env_file}")
        print("⚠️  Please update the .env file with your actual Gemini API key!")
    else:
        print(f"✅ {env_file} already exists")

def create_init_files():
    """Create __init__.py files for Python packages"""
    init_files = [
        "backend/__init__.py",
        "backend/models/__init__.py", 
        "backend/services/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Package initialization file\n")
            print(f"✅ Created {init_file}")

def main():
    print("🚀 Setting up Legal Document Simplifier...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Create __init__.py files
    create_init_files()
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Setup environment
    setup_environment()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!") 
    print("\n📋 Next steps:")
    print("1. Add your Gemini API key to the .env file")
    print("2. Run the backend: python run_backend.py")
    print("3. Run the frontend: python run_streamlit.py")
    print("4. Access the app at http://localhost:8501")
    print("\n📚 Need help? Check the README.md file")

if __name__ == "__main__":
    main()