#!/usr/bin/env python3
\"\"\"OceanScope Setup Script

Helps users quickly set up the OceanScope environment with proper configuration.
\"\"\"

import os
import shutil
import subprocess
import sys
from pathlib import Path

def check_python_version():
    \"\"\"Check if Python version is compatible.\"\"\"
    if sys.version_info < (3, 8):
        print(\"❌ Python 3.8 or higher is required\")
        return False
    print(f\"✅ Python {sys.version.split()[0]} detected\")
    return True

def install_dependencies():
    \"\"\"Install required Python packages.\"\"\"
    print(\"\n📦 Installing dependencies...\")
    try:
        subprocess.check_call([sys.executable, \"-m\", \"pip\", \"install\", \"-r\", \"requirements.txt\"])
        print(\"✅ Dependencies installed successfully\")
        return True
    except subprocess.CalledProcessError as e:
        print(f\"❌ Failed to install dependencies: {e}\")
        return False

def setup_env_file():
    \"\"\"Set up environment file if it doesn't exist.\"\"\"
    print(\"\n🔧 Setting up environment configuration...\")
    
    env_file = Path(\".env\")
    env_example = Path(\".env.example\")
    
    if env_file.exists():
        print(\"✅ .env file already exists\")
        return True
    
    if env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print(\"✅ Created .env file from template\")
            print(\"⚠️  Please edit .env file and add your Gemini API key\")
            return True
        except Exception as e:
            print(f\"❌ Failed to create .env file: {e}\")
            return False
    else:
        print(\"❌ .env.example template not found\")
        return False

def check_data_file():
    \"\"\"Check if the data file exists.\"\"\"
    print(\"\n📊 Checking data file...\")
    
    data_file = Path(\"data/20250101_prof.nc\")
    if data_file.exists():
        size_mb = data_file.stat().st_size / (1024 * 1024)
        print(f\"✅ Data file found ({size_mb:.1f} MB)\")
        return True
    else:
        print(\"❌ Data file not found: data/20250101_prof.nc\")
        print(\"   Please ensure the NetCDF data file is in the data/ directory\")
        return False

def run_configuration_test():
    \"\"\"Run the configuration validation test.\"\"\"
    print(\"\n🧪 Running configuration test...\")
    
    try:
        # Import and test configuration
        sys.path.insert(0, '.')
        from utils.config import config
        
        is_valid, issues = config.validate_configuration()
        env_info = config.get_env_info()
        
        print(f\"Configuration Status: {'✅ Valid' if is_valid else '⚠️ Issues Found'}\")
        print(f\"API Configured: {'✅' if env_info['gemini_api_configured'] else '❌'}\")
        print(f\"Data File: {'✅' if 'data/20250101_prof.nc' in env_info['data_file_path'] else '❌'}\")
        
        if issues:
            print(\"\nConfiguration Issues:\")
            for issue in issues:
                print(f\"  • {issue}\")
        
        return len(issues) <= 1  # Allow API key to be missing
        
    except Exception as e:
        print(f\"❌ Configuration test failed: {e}\")
        return False

def main():
    \"\"\"Main setup function.\"\"\"
    print(\"🌊 OceanScope Setup Script\n\")
    print(\"This script will help you set up the OceanScope environment.\n\")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Setup environment file
    if not setup_env_file():
        return False
    
    # Check data file
    data_ok = check_data_file()
    
    # Run configuration test
    config_ok = run_configuration_test()
    
    # Final summary
    print(\"\n\" + \"=\"*50)
    print(\"🎯 Setup Summary\")
    print(\"=\"*50)
    
    if data_ok and config_ok:
        print(\"✅ Setup completed successfully!\")
        print(\"\n🚀 Next Steps:\")
        print(\"1. Edit .env file and add your Gemini API key (optional but recommended)\")
        print(\"2. Run: streamlit run app.py\")
        print(\"3. Open your browser to the displayed URL\")
        return True
    else:
        print(\"⚠️ Setup completed with issues\")
        print(\"\n🔧 Required Actions:\")
        if not data_ok:
            print(\"• Add NetCDF data file to data/ directory\")
        if not config_ok:
            print(\"• Check configuration and resolve any issues\")
        print(\"• Edit .env file and add your Gemini API key\")
        return False

if __name__ == \"__main__\":
    success = main()
    sys.exit(0 if success else 1)