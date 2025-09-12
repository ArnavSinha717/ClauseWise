#!/usr/bin/env python3
"""
Backend Environment Debug Script
Save this as: backend/env_debug.py
Run from: backend/ directory
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check .env file in backend directory"""
    print("🔍 Backend Environment Diagnostics")
    print("=" * 40)
    
    # Get current working directory
    cwd = os.getcwd()
    print(f"Current Working Directory: {cwd}")
    
    # Get script directory (should be backend/)
    script_dir = Path(__file__).parent.absolute()
    print(f"Script Directory (backend/): {script_dir}")
    
    # Check for .env file in backend directory
    env_file = script_dir / ".env"
    print(f"\n📁 Looking for .env at: {env_file}")
    
    if env_file.exists():
        print(f"✅ Found .env file")
        
        # Check file permissions
        try:
            with open(env_file, 'r') as f:
                content = f.read()
            print(f"   📄 Size: {len(content)} characters")
            print(f"   🔐 Readable: Yes")
            
            # Check for required keys (without showing values)
            lines = content.split('\n')
            keys_found = []
            for line in lines:
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=')[0].strip()
                    value = line.split('=', 1)[1].strip()
                    keys_found.append(key)
                    
                    # Check if key has a real value
                    if value and not value.startswith('your_'):
                        print(f"   ✅ {key}: Has value")
                    else:
                        print(f"   ❌ {key}: Needs real value")
            
            print(f"   🗝️  All keys found: {', '.join(keys_found)}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            return False
    else:
        print(f"❌ .env file not found")
        return False

def test_dotenv_loading():
    """Test loading .env file"""
    print(f"\n🧪 Testing .env Loading:")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv package is installed")
        
        # Method 1: Default loading (should find .env in current directory)
        result1 = load_dotenv()
        print(f"📍 load_dotenv() result: {result1}")
        
        # Method 2: Explicit path loading
        env_file = Path(".env")
        if env_file.exists():
            result2 = load_dotenv(env_file)
            print(f"📍 load_dotenv('.env') result: {result2}")
        
        # Method 3: Absolute path loading
        abs_env_file = Path(__file__).parent / ".env"
        if abs_env_file.exists():
            result3 = load_dotenv(abs_env_file)
            print(f"📍 load_dotenv(absolute path) result: {result3}")
        
        # Check if environment variables are actually loaded
        print(f"\n🔐 Environment Variables Check:")
        important_vars = ['GOOGLE_API_KEY', 'ELEVENLABS_API_KEY']
        
        for var in important_vars:
            value = os.getenv(var)
            if value:
                if len(value) > 12:
                    masked_value = value[:8] + "..." + value[-4:]
                else:
                    masked_value = "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"❌ {var}: Not found in environment")
        
        return True
        
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Install with: pip install python-dotenv")
        return False

def test_import_main():
    """Test importing main.py to see if it loads environment correctly"""
    print(f"\n🔬 Testing Main.py Import:")
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        print("📦 Attempting to import main.py...")
        
        # Try importing main - this will show if environment loading works
        import main
        print("✅ main.py imported successfully")
        
        # Check if services are initialized
        if hasattr(main, 'llm_service'):
            print("✅ LLM service initialized")
        else:
            print("❌ LLM service not initialized")
            
        if hasattr(main, 'voice_service'):
            print("✅ Voice service initialized")
        else:
            print("❌ Voice service not initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import main.py: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def create_env_file():
    """Create a .env file in backend directory"""
    print(f"\n📝 Creating .env file in backend/...")
    
    env_content = """# ClauseWise Backend Environment Configuration
# Place your actual API keys here (no quotes needed)

# Required: Google Gemini API Key for LLM
GOOGLE_API_KEY=your_actual_gemini_api_key_here

# Required: ElevenLabs API Key for Voice Services (TTS + STT)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Voice Service Configuration
ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM
TTS_MAX_CHARACTERS=5000
STT_MAX_FILE_SIZE_MB=3000
STT_MAX_DURATION_HOURS=10

# Application Settings
RATE_LIMIT_REQUESTS_PER_MINUTE=15
MAX_FILE_SIZE_MB=10
CHUNK_SIZE=1000
ENABLE_LEGAL_KB=true

# Database Paths
CHROMA_DB_PATH=./chroma_db
LEGAL_DATASETS_PATH=./legal_datasets
CHROMA_COLLECTION_NAME=legal_documents
"""
    
    env_file = Path(".env")
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created .env file at: {env_file.absolute()}")
        
        # Set proper permissions on Mac
        os.chmod(env_file, 0o600)
        print(f"✅ Set file permissions to 600")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def print_mac_specific_fixes():
    """Print Mac-specific troubleshooting steps"""
    print(f"\n🍎 Mac-Specific Fixes:")
    print("-" * 30)
    
    print("1. **Check file permissions:**")
    print("   ls -la .env")
    print("   chmod 600 .env")
    print("")
    
    print("2. **Check for hidden characters:**")
    print("   cat -A .env")
    print("   # Look for ^M or other weird characters")
    print("")
    
    print("3. **Recreate .env file:**")
    print("   rm .env")
    print("   touch .env")
    print("   nano .env")
    print("   # Add your keys without quotes")
    print("")
    
    print("4. **Check Python path:**")
    print("   which python3")
    print("   python3 --version")
    print("")
    
    print("5. **Run from correct directory:**")
    print("   cd backend/")
    print("   python3 -m uvicorn main:app --reload --port 8000")
    print("")

def main():
    """Main function"""
    print("🍎 ClauseWise Backend .env Diagnostics for Mac")
    print("=" * 55)
    
    # Step 1: Check for .env file
    env_exists = check_env_file()
    
    # Step 2: Test loading
    if env_exists:
        load_success = test_dotenv_loading()
    else:
        load_success = False
    
    # Step 3: Test main.py import
    if load_success:
        import_success = test_import_main()
    else:
        import_success = False
    
    # Step 4: Create .env if needed
    if not env_exists:
        print(f"\n❌ No .env file found in backend/")
        response = input("Create a new .env file? (y/n): ").strip().lower()
        if response == 'y':
            create_env_file()
    
    # Step 5: Print Mac-specific fixes
    print_mac_specific_fixes()
    
    # Summary
    print(f"\n📊 Diagnostic Summary:")
    print(f"   .env file exists: {'✅' if env_exists else '❌'}")
    print(f"   .env loads successfully: {'✅' if load_success else '❌'}")
    print(f"   main.py imports correctly: {'✅' if import_success else '❌'}")
    
    if all([env_exists, load_success, import_success]):
        print(f"\n🎉 Everything looks good! Try starting your backend now:")
        print(f"   cd backend/")
        print(f"   python3 -m uvicorn main:app --reload --port 8000")
    else:
        print(f"\n⚠️  Issues found. Follow the Mac-specific fixes above.")

if __name__ == "__main__":
    main()