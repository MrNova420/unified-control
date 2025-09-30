#!/bin/bash
# Quick Start - Server + Device

source ./unified_control_config.sh

echo "🚀 Quick Start - Unified Control System"
echo "======================================="

# Start server in background
echo "Starting server..."
./start_server.sh &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Start a demo device
echo "Starting demo device..."
./start_device.sh "demo-device" "true" &
DEVICE_PID=$!

echo ""
echo "✅ System started!"
echo "📱 Demo device: demo-device (exec allowed)"
echo "🌐 Web UI: http://$UC_HOST:$UC_HTTP_PORT/ui?token=$UC_AUTH_TOKEN"
echo ""
echo "Press Ctrl+C to stop both server and device"

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping..."; kill $SERVER_PID $DEVICE_PID 2>/dev/null; exit' INT
wait
