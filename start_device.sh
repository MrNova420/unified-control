#!/bin/bash
# Start Unified Control Device Client

source ./unified_control_config.sh

# Allow overriding device ID via command line
DEVICE_ID="${1:-$UC_DEVICE_ID}"
EXEC_ALLOWED="${2:-$UC_EXEC_ALLOWED}"

echo "📱 Starting Device Client..."
echo "🆔 Device ID: $DEVICE_ID"
echo "📡 Server: $UC_SERVER_URL"
echo "🔧 Exec Allowed: $EXEC_ALLOWED"
echo ""

python3 unified_agent_with_ui.py \
    --mode device \
    --auth "$UC_AUTH_TOKEN" \
    --id "$DEVICE_ID" \
    --server "$UC_SERVER_URL" \
    --tags $UC_DEVICE_TAGS \
    $([ "$EXEC_ALLOWED" = "true" ] && echo "--exec-allowed")
