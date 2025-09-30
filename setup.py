#!/usr/bin/env python3
"""
Unified Control System - Setup Script
Auto-installs all dependencies and sets up the system
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install all required dependencies"""
    print("🚀 Unified Control System - Auto Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Upgrade pip first
    print("\n📦 Upgrading pip...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        print("✅ pip upgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to upgrade pip: {e}")
    
    # Install from requirements.txt if it exists
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    
    if os.path.exists(requirements_file):
        print(f"\n📦 Installing dependencies from requirements.txt...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '-r', requirements_file, 
                '--user'
            ])
            print("✅ All dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            print("\n📋 Manual installation command:")
            print(f"   {sys.executable} -m pip install -r requirements.txt")
            sys.exit(1)
    else:
        # Install core dependencies directly if no requirements.txt
        print("\n📦 Installing core dependencies...")
        core_packages = [
            'websockets>=13.0.1',
            'aiohttp>=3.9.1',
            'aiofiles>=24.1.0',
            'psutil>=6.0.0',
            'requests>=2.32.0',
            'cryptography>=42.0.0',
        ]
        
        for package in core_packages:
            print(f"   Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', 
                    package, '--user'
                ])
            except subprocess.CalledProcessError:
                print(f"   ⚠️  Warning: Failed to install {package}")
    
    # Verify installation
    print("\n✅ Verifying installation...")
    required_modules = ['websockets', 'aiohttp', 'aiofiles', 'psutil', 'requests']
    all_installed = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - NOT INSTALLED")
            all_installed = False
    
    if all_installed:
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Run the server: python3 unified_agent_with_ui.py --mode server")
        print("   2. Or use quick start: ./quick_start.sh")
        print("   3. Or run the installer: ./install.sh")
    else:
        print("\n⚠️  Some dependencies failed to install")
        print("   Try manual installation: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == '__main__':
    install_dependencies()
