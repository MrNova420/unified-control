#!/bin/bash

# Unified Control System - One-Click Auto Setup
# This script automatically installs all dependencies and sets up the system

echo "🚀 Unified Control System - One-Click Auto Setup"
echo "=================================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "📋 Please install Python 3.7 or higher first:"
    echo ""
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Termux:        pkg install python python-pip"
    echo "  macOS:         brew install python3"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $PYTHON_VERSION"

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed!"
    echo "📋 Installing pip..."
    
    # Try to install pip
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-pip
    elif [[ -n "$TERMUX_VERSION" ]]; then
        pkg install -y python-pip
    else
        python3 -m ensurepip --default-pip
    fi
fi

# Use pip3 if available, otherwise pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

echo "✅ Using pip command: $PIP_CMD"
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
echo "   This may take a few minutes..."
echo ""

# Upgrade pip first
echo "   Upgrading pip..."
python3 -m pip install --upgrade pip --user 2>/dev/null || python3 -m pip install --upgrade pip

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "   Installing from requirements.txt..."
    python3 -m pip install -r requirements.txt --user 2>/dev/null || python3 -m pip install -r requirements.txt
else
    echo "   Installing core packages..."
    python3 -m pip install --user websockets aiohttp aiofiles psutil requests cryptography 2>/dev/null || \
    python3 -m pip install websockets aiohttp aiofiles psutil requests cryptography
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."

python3 -c "
import sys
missing = []
required = ['websockets', 'aiohttp', 'aiofiles', 'psutil', 'requests']

for module in required:
    try:
        __import__(module)
        print(f'   ✅ {module}')
    except ImportError:
        print(f'   ❌ {module} - MISSING')
        missing.append(module)

if missing:
    print(f'\n❌ Some dependencies are still missing: {missing}')
    print('📋 Try manual installation:')
    print(f'   python3 -m pip install {\" \".join(missing)}')
    sys.exit(1)
else:
    print('\n✅ All dependencies installed successfully!')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Setup failed. Please install dependencies manually:"
    echo "   python3 -m pip install websockets aiohttp aiofiles psutil requests"
    exit 1
fi

# Make scripts executable
echo ""
echo "🔧 Setting up scripts..."
chmod +x *.sh 2>/dev/null
chmod +x *.py 2>/dev/null
echo "✅ Scripts are now executable"

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p uploads logs
echo "✅ Directories created"

# Generate auth token if config doesn't exist
if [ ! -f "unified_control_config.sh" ]; then
    echo ""
    echo "🔐 Generating authentication token..."
    
    if command -v openssl &> /dev/null; then
        AUTH_TOKEN=$(openssl rand -hex 32)
    else
        AUTH_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    fi
    
    cat > unified_control_config.sh << EOF
#!/bin/bash
# Unified Control System Configuration
export UC_AUTH_TOKEN="$AUTH_TOKEN"
export UC_HOST="127.0.0.1"
export UC_WS_PORT="8765"
export UC_HTTP_PORT="8766"
export UC_DB_PATH="./unified_control.sqlite"
export UC_UPLOAD_DIR="./uploads"
EOF
    
    chmod +x unified_control_config.sh
    echo "✅ Configuration file created"
else
    source ./unified_control_config.sh
    echo "✅ Using existing configuration"
fi

# Done
echo ""
echo "=================================================="
echo "🎉 Setup completed successfully!"
echo "=================================================="
echo ""
echo "📋 Quick Start Options:"
echo ""
echo "  1. Start server with auto-optimization:"
echo "     python3 start_unified.py"
echo ""
echo "  2. Start server manually:"
echo "     python3 unified_agent_with_ui.py --mode server --auth test_token"
echo ""
echo "  3. Use the installer for full setup:"
echo "     ./install.sh"
echo ""
echo "🌐 Web Interface will be at:"
echo "   http://127.0.0.1:8766/ui?token=${UC_AUTH_TOKEN:-test_token}"
echo ""
echo "⚠️  Keep your authentication token secure!"
echo ""
