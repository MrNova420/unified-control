#!/bin/bash

# Unified Control System - Automatic Installation Script
# This script sets up the unified control system on Termux or Linux systems

set -e

echo "🚀 Unified Control System - Auto Installer"
echo "============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect system type
detect_system() {
    if [[ -n "$TERMUX_VERSION" ]]; then
        SYSTEM="termux"
        PKG_MANAGER="pkg"
        PYTHON_CMD="python"
        PIP_CMD="pip"
    elif command -v apt-get >/dev/null 2>&1; then
        SYSTEM="debian"
        PKG_MANAGER="apt-get"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    elif command -v yum >/dev/null 2>&1; then
        SYSTEM="redhat"
        PKG_MANAGER="yum"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    elif command -v pacman >/dev/null 2>&1; then
        SYSTEM="arch"
        PKG_MANAGER="pacman"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    else
        SYSTEM="unknown"
    fi
    
    print_status "Detected system: $SYSTEM"
}

# Install system packages
install_system_packages() {
    print_status "Installing system packages..."
    
    case $SYSTEM in
        "termux")
            pkg update -y
            pkg install -y python python-pip git curl wget
            ;;
        "debian")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip git curl wget build-essential
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y python3 python3-pip git curl wget gcc
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip git curl wget base-devel
            ;;
        *)
            print_error "Unsupported system. Please install Python 3.7+ and pip manually."
            exit 1
            ;;
    esac
    
    print_success "System packages installed"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip first
    print_status "Upgrading pip..."
    $PIP_CMD install --upgrade pip --user 2>/dev/null || $PIP_CMD install --upgrade pip
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        print_status "Installing from requirements.txt..."
        $PIP_CMD install -r requirements.txt --user 2>/dev/null || $PIP_CMD install -r requirements.txt
    else
        print_warning "requirements.txt not found, installing core packages..."
        # Install core required packages
        $PIP_CMD install --user websockets aiohttp aiofiles psutil requests cryptography 2>/dev/null || \
        $PIP_CMD install websockets aiohttp aiofiles psutil requests cryptography
    fi
    
    # Verify installation
    print_status "Verifying Python packages..."
    $PYTHON_CMD -c "import websockets, aiohttp, aiofiles, psutil, requests" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "Python dependencies installed and verified"
    else
        print_error "Some dependencies failed to install"
        print_warning "Trying alternative installation method..."
        
        # Try installing without --user flag
        $PIP_CMD install websockets aiohttp aiofiles psutil requests cryptography
        
        # Check again
        $PYTHON_CMD -c "import websockets, aiohttp, aiofiles, psutil, requests" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_success "Dependencies installed successfully (system-wide)"
        else
            print_error "Failed to install dependencies. Please install manually:"
            print_error "  $PIP_CMD install websockets aiohttp aiofiles psutil requests"
            exit 1
        fi
    fi
}

# Generate secure authentication token
generate_auth_token() {
    if command -v openssl >/dev/null 2>&1; then
        AUTH_TOKEN=$(openssl rand -hex 32)
    elif command -v python3 >/dev/null 2>&1; then
        AUTH_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    elif command -v python >/dev/null 2>&1; then
        AUTH_TOKEN=$(python -c "import os; print(os.urandom(32).hex())")
    else
        AUTH_TOKEN="CHANGE_THIS_TOKEN_$(date +%s)"
        print_warning "Could not generate secure token. Using: $AUTH_TOKEN"
        print_warning "Please change this token before use!"
    fi
    
    print_success "Generated authentication token: $AUTH_TOKEN"
}

# Create configuration file
create_config() {
    print_status "Creating configuration file..."
    
    cat > unified_control_config.sh << EOF
#!/bin/bash
# Unified Control System Configuration

# Authentication token (keep this secret!)
export UC_AUTH_TOKEN="$AUTH_TOKEN"

# Server configuration
export UC_HOST="127.0.0.1"
export UC_WS_PORT="8765"
export UC_HTTP_PORT="8766"

# Paths
export UC_DB_PATH="./unified_control.sqlite"
export UC_UPLOAD_DIR="./uploads"

# Device configuration (for device mode)
export UC_DEVICE_ID="device-$(hostname)-$$"
export UC_DEVICE_TAGS="auto-setup,$(hostname)"
export UC_EXEC_ALLOWED="false"  # Set to "true" to allow file execution

# Server URL for device connections
export UC_SERVER_URL="ws://\$UC_HOST:\$UC_WS_PORT"
EOF
    
    chmod +x unified_control_config.sh
    print_success "Configuration created: unified_control_config.sh"
}

# Create startup scripts
create_scripts() {
    print_status "Creating startup scripts..."
    
    # Server startup script
    cat > start_server.sh << 'EOF'
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
EOF

    # Device startup script
    cat > start_device.sh << 'EOF'
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
EOF

    # Quick start script
    cat > quick_start.sh << 'EOF'
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
EOF

    # Make scripts executable
    chmod +x start_server.sh start_device.sh quick_start.sh
    
    print_success "Startup scripts created"
}

# Create systemd service (Linux only)
create_systemd_service() {
    if [[ "$SYSTEM" != "termux" ]] && command -v systemctl >/dev/null 2>&1; then
        print_status "Creating systemd service..."
        
        INSTALL_DIR=$(pwd)
        
        sudo tee /etc/systemd/system/unified-control.service > /dev/null << EOF
[Unit]
Description=Unified Control System Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start_server.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        print_success "Systemd service created. Enable with: sudo systemctl enable unified-control"
    fi
}

# Create documentation
create_docs() {
    print_status "Creating documentation..."
    
    cat > README_USAGE.md << 'EOF'
# Unified Control System - Usage Guide

## Overview
The Unified Control System provides secure, local device management with a web-based dashboard. It's designed for managing multiple devices you own and control.

## ⚠️ Security Notice
**IMPORTANT**: Only use this system on devices you own and control. All activities are logged and audited.

## Quick Start

1. **Start the system** (server + demo device):
   ```bash
   ./quick_start.sh
   ```

2. **Access the web interface**:
   Open your browser and go to the URL shown in the output (includes your auth token)

3. **Upload and deploy files**:
   - Use the web interface to upload files
   - Deploy them to devices with execution permissions
   - Monitor command results in real-time

## Manual Operation

### Start Server Only
```bash
./start_server.sh
```

### Start Device Client
```bash
# Basic device (no execution allowed)
./start_device.sh "my-device-1" "false"

# Device with execution allowed
./start_device.sh "my-device-2" "true"
```

## Configuration

Edit `unified_control_config.sh` to customize:
- Authentication token
- Server ports and host
- Device settings
- File paths

## Web Interface Features

- **Device Management**: View connected devices, their status, and capabilities
- **File Upload**: Securely upload files for deployment
- **Command Console**: Send commands to specific devices or groups
- **Real-time Monitoring**: Live updates of device status and command results
- **Audit Logging**: Complete audit trail of all activities

## Special Commands

- `echo "Hello World"` - Send text command to devices
- `run_upload:<file_id>` - Execute uploaded file on devices with exec_allowed=true

## Safety Features

- Sandboxed execution with CPU, memory, and time limits
- SHA256 file integrity verification
- Comprehensive audit logging
- Per-device execution permissions
- Authentication required for all operations

## Termux Mobile Setup

The system is optimized for Termux on Android devices:

1. Install Termux from F-Droid
2. Run the installation script
3. Start the server and connect devices
4. Use the mobile-friendly web interface

## Production Deployment

For production use:
1. Change the default authentication token
2. Use HTTPS/WSS with proper certificates
3. Set up firewall rules
4. Enable systemd service for auto-start
5. Configure log rotation

## Troubleshooting

- Check `unified_control.log` for detailed logs
- Ensure all devices use the same auth token
- Verify network connectivity between devices
- Check firewall settings for WebSocket connections

## Support

This system includes conservative security safeguards but should be used responsibly. Always verify uploaded files before execution.
EOF

    print_success "Documentation created: README_USAGE.md"
}

# Create .gitignore file
create_gitignore() {
    cat > .gitignore << 'EOF'
# Unified Control System
unified_control.sqlite*
unified_control.log*
uploads/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Sensitive configuration (uncomment if you want to exclude)
# unified_control_config.sh

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db
EOF
}

# Optimize for device capacity
optimize_device_capacity() {
    print_status "Optimizing for device capacity..."
    
    # Get system information
    if command -v free >/dev/null 2>&1; then
        TOTAL_RAM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    else
        TOTAL_RAM=1024  # Default assumption
    fi
    
    CPU_CORES=$(nproc 2>/dev/null || echo "1")
    
    # Calculate optimal device limits based on hardware
    if [[ $TOTAL_RAM -lt 512 ]]; then
        MAX_DEVICES=5
        MEMORY_LIMIT=64
    elif [[ $TOTAL_RAM -lt 1024 ]]; then
        MAX_DEVICES=10
        MEMORY_LIMIT=128
    elif [[ $TOTAL_RAM -lt 2048 ]]; then
        MAX_DEVICES=25
        MEMORY_LIMIT=256
    else
        MAX_DEVICES=100
        MEMORY_LIMIT=512
    fi
    
    print_status "System: ${TOTAL_RAM}MB RAM, ${CPU_CORES} CPU cores"
    print_status "Recommended max devices: $MAX_DEVICES"
    print_status "Memory limit per execution: ${MEMORY_LIMIT}MB"
    
    # Update the Python file with optimized values
    sed -i.bak "s/MAX_DEVICES = 100/MAX_DEVICES = $MAX_DEVICES/" unified_agent_with_ui.py
    sed -i.bak "s/MAX_MEMORY_MB = 256/MAX_MEMORY_MB = $MEMORY_LIMIT/" unified_agent_with_ui.py
    
    print_success "System optimized for current hardware"
}

# Main installation process
main() {
    echo ""
    print_status "Starting installation..."
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]] && [[ "$SYSTEM" != "termux" ]]; then
        print_warning "Running as root is not recommended for security reasons"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    detect_system
    install_system_packages
    install_python_deps
    generate_auth_token
    create_config
    create_scripts
    create_systemd_service
    create_docs
    create_gitignore
    optimize_device_capacity
    
    echo ""
    print_success "Installation completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Review configuration: unified_control_config.sh"
    echo "2. Quick start: ./quick_start.sh"
    echo "3. Read documentation: README_USAGE.md"
    echo ""
    echo "🌐 Web Interface: http://127.0.0.1:8766/ui?token=$AUTH_TOKEN"
    echo ""
    print_warning "Keep your authentication token secure!"
    print_warning "Only use on devices you own and control!"
}

# Run main installation
main "$@"