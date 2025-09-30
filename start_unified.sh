#!/bin/bash
# Simple One-Command Startup for Unified Control System
# This script starts both server and dashboard in one command

set -e

echo "🚀 UNIFIED CONTROL SYSTEM - ONE-COMMAND STARTUP"
echo "================================================="

# Check if config exists, if not run installer
if [ ! -f "unified_control_config.sh" ]; then
    echo "⚙️  Configuration not found, running installer..."
    ./install.sh
fi

# Source configuration
source ./unified_control_config.sh

# Create enhanced startup script that auto-detects optimal settings
cat > start_unified.py << 'EOF'
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
    
    # Calculate optimal settings
    if ram_gb < 1:
        max_devices = 5
        max_workers = 10
        memory_limit = 128
    elif ram_gb < 2:
        max_devices = 25
        max_workers = 25
        memory_limit = 256
    elif ram_gb < 4:
        max_devices = 100
        max_workers = 50
        memory_limit = 512
    else:
        max_devices = 1000
        max_workers = 100
        memory_limit = 1024
    
    print(f"⚙️  Optimized: {max_devices} max devices, {max_workers} workers, {memory_limit}MB memory limit")
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
EOF

chmod +x start_unified.py

echo "🎯 STARTING OPTIMIZED UNIFIED CONTROL SYSTEM"
echo "=============================================="
echo ""
echo "🌐 Web Dashboard: http://$UC_HOST:$UC_HTTP_PORT/ui?token=$UC_AUTH_TOKEN"
echo "📱 Mobile Ready: Works great on Termux!"
echo "⚡ Auto-Optimized: Hardware detection enabled"
echo "🔒 Secure: Full authentication and sandboxing"
echo ""
echo "Starting in 3 seconds... Press Ctrl+C to cancel"
sleep 3

# Start the optimized system
python3 start_unified.py