#!/bin/bash
# Unified Control System Configuration

# Authentication token (keep this secret!)
export UC_AUTH_TOKEN="957f31748962a73bd03bc897d2c843ac3950eb8a58a8f283ec8339cb3e78fee9"

# Server configuration
export UC_HOST="127.0.0.1"
export UC_WS_PORT="8765"
export UC_HTTP_PORT="8766"

# Paths
export UC_DB_PATH="./unified_control.sqlite"
export UC_UPLOAD_DIR="./uploads"

# Device configuration (for device mode)
export UC_DEVICE_ID="device-runnervm3ublj-3494"
export UC_DEVICE_TAGS="auto-setup,runnervm3ublj"
export UC_EXEC_ALLOWED="false"  # Set to "true" to allow file execution

# Server URL for device connections
export UC_SERVER_URL="ws://$UC_HOST:$UC_WS_PORT"
