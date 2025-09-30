#!/bin/bash
# Simple One-Command Startup for Unified Control System
# This script is a wrapper around start_unified.py

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

# Ensure start_unified.py exists and is executable
if [ ! -f "start_unified.py" ]; then
    echo "❌ Error: start_unified.py not found!"
    echo "Please ensure the repository is complete."
    exit 1
fi

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

# Start the optimized system using the existing start_unified.py
python3 start_unified.py