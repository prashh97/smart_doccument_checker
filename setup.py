#!/usr/bin/env python3
"""
Smart Doc Checker Setup Script
Automates the initial setup process
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    
    directories = [
        "src",
        "components", 
        "config",
        "data/uploads",
        "data/reports",
        "data/cache",
        "tests",
        "docs",
        "deployment",
        ".streamlit"
    ]
    
    print("📁 Creating project directories...")
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}/")
    
    # Create __init__.py files
    init_files = [
        "src/__init__.py",
        "components/__init__.py", 
        "config/__init__.py",
        "tests/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()

def create_gitignore():
    """Create .gitignore file"""
    
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Streamlit
.streamlit/secrets.toml
.streamlit/credentials.toml

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Data files
data/uploads/*
data/cache/*
data/reports/*
!data/uploads/.gitkeep
!data/cache/.gitkeep
!data/reports/.gitkeep

# Logs
*.log
logs/

# API Keys and Secrets
config/secrets.json
api_keys.txt
secrets.txt

# Temporary files
tmp/
temp/
*.tmp

# Documentation build
docs/_build/
site/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Deployment
deployment/.env
deployment/secrets/
"""
    
    print("📄 Creating .gitignore...")
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("  ✓ Created .gitignore")

def create_secrets_template():
    """Create secrets template file"""
    
    secrets_template = """# Smart Doc Checker - API Keys Template
# Copy this file to .streamlit/secrets.toml and add your actual keys
# DO NOT COMMIT secrets.toml TO VERSION CONTROL

[api_keys]
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = "your-gemini-api-key-here"

# Optional: OpenAI API key for future integration
OPENAI_API_KEY = "your-openai-api-key-here"

# Optional: Grok API key when available
GROK_API_KEY = "your-grok-api-key-here"

# Flexprice API key for billing integration
FLEXPRICE_API_KEY = "your-flexprice-api-key-here"
FLEXPRICE_BASE_URL = "https://api.flexprice.com/v1"

[app_settings]
DEBUG = false
MAX_FILE_SIZE = 50  # MB
MAX_FILES_PER_ANALYSIS = 5
DEFAULT_MODEL = "gemini-2.5-flash"

[pathway_settings]
# Pathway license key for real-time monitoring
PATHWAY_LICENSE_KEY = "your-pathway-license-key"
EXTERNAL_MONITOR_URL = "https://example.com/policy-updates"
MONITOR_INTERVAL = 30  # seconds

[ui_settings]
APP_TITLE = "Smart Doc Checker Agent"
COMPANY_NAME = "Your Company"
SUPPORT_EMAIL = "support@yourcompany.com"
"""
    
    print("🔐 Creating secrets template...")
    template_path = ".streamlit/secrets_template.toml"
    with open(template_path, "w") as f:
        f.write(secrets_template)
    print(f"  ✓ Created {template_path}")
    print("  ⚠️  Copy this to .streamlit/secrets.toml and add your API keys!")

def install_dependencies():
    """Install Python dependencies"""
    
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("  ✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("  ❌ Failed to install dependencies")
        print("  💡 Try running: pip install -r requirements.txt manually")
        return False

def create_empty_files():
    """Create empty placeholder files"""
    
    placeholder_files = [
        "data/uploads/.gitkeep",
        "data/reports/.gitkeep", 
        "data/cache/.gitkeep",
        "tests/.gitkeep",
        "docs/.gitkeep"
    ]
    
    print("📝 Creating placeholder files...")
    
    for file_path in placeholder_files:
        Path(file_path).touch()
        print(f"  ✓ Created {file_path}")

def validate_setup():
    """Validate the setup"""
    
    print("🔍 Validating setup...")
    
    required_files = [
        "streamlit_app.py",
        "requirements.txt",
        "README.md",
        ".gitignore",
        ".streamlit/secrets_template.toml"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✓ {file_path} exists")
    
    if missing_files:
        print(f"  ❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("  ✅ Setup validation passed!")
    return True

def print_next_steps():
    """Print next steps for the user"""
    
    print("\n🎉 Setup complete! Next steps:")
    print()
    print("1. 🔑 Configure API Keys:")
    print("   cp .streamlit/secrets_template.toml .streamlit/secrets.toml")
    print("   # Edit .streamlit/secrets.toml with your actual API keys")
    print()
    print("2. 🏃 Run the application:")
    print("   streamlit run streamlit_app.py")
    print()
    print("3. 🌐 Open in browser:")
    print("   http://localhost:8501")
    print()
    print("4. 📚 API Keys needed:")
    print("   • Gemini API: https://makersuite.google.com/app/apikey")
    print("   • Flexprice API: https://flexprice.com/api")
    print("   • Pathway License: https://pathway.com (optional)")
    print()
    print("5. 📖 Documentation:")
    print("   • README.md - Project overview")
    print("   • docs/ - Detailed documentation")
    print()
    print("Happy document checking! 📄✨")

def main():
    """Main setup function"""
    
    print("🚀 Setting up Smart Doc Checker Agent...")
    print("=" * 50)
    
    # Create directory structure
    create_directories()
    
    # Create configuration files
    create_gitignore()
    create_secrets_template()
    create_empty_files()
    
    # Install dependencies if requirements.txt exists
    if Path("requirements.txt").exists():
        success = install_dependencies()
        if not success:
            print("⚠️  Continue with manual dependency installation")
    else:
        print("📦 requirements.txt not found - skipping dependency installation")
    
    # Validate setup
    if validate_setup():
        print_next_steps()
    else:
        print("❌ Setup validation failed - please check missing files")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)