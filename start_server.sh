#!/bin/bash
# Start Unified Control Server

source ./unified_control_config.sh

echo "🚀 Starting Unified Control Server..."
echo "📡 WebSocket: ws://$UC_HOST:$UC_WS_PORT"
echo "🌐 Web UI: http://$UC_HOST:$UC_HTTP_PORT/ui?token=$UC_AUTH_TOKEN"
echo ""
echo "⚠️  Keep your auth token secure: $UC_AUTH_TOKEN"
echo ""

python3 unified_agent_with_ui.py \
    --mode server \
    --auth "$UC_AUTH_TOKEN" \
    --host "$UC_HOST" \
    --ws-port "$UC_WS_PORT" \
    --http-port "$UC_HTTP_PORT" \
    --db "$UC_DB_PATH" \
    --upload-dir "$UC_UPLOAD_DIR"
