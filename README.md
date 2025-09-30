# 🚀 Unified Control System

A secure, local-first device management system with web dashboard, designed for Termux and Linux environments.

## ⚠️ Security Notice

**IMPORTANT**: This system is designed for managing devices you own and control. It includes conservative security safeguards and comprehensive audit logging. Use responsibly and only on your own devices.

## 🌟 Features

- **🔒 Secure by Design**: Authentication required, sandboxed execution, comprehensive audit logging
- **📱 Mobile Ready**: Optimized for Termux on Android devices
- **🌐 Web Dashboard**: Modern, responsive interface with real-time updates
- **📁 File Management**: Secure upload, SHA256 verification, controlled deployment
- **🤖 Multi-Device**: Support for hundreds of devices with automatic scaling
- **📊 Real-time Monitoring**: Live device status, command results, and system metrics
- **🔧 Flexible Targeting**: Send commands to specific devices, groups, or all devices
- **🛡️ Sandboxed Execution**: CPU, memory, and time limits for safety
- **📋 Complete Audit Trail**: All activities logged and queryable

## 🚀 Quick Start

### 1. Automated Installation

```bash
# Download and run the installer
curl -sSL https://raw.githubusercontent.com/MrNova420/unified-control/main/install.sh | bash

# Or clone and install manually
git clone https://github.com/MrNova420/unified-control.git
cd unified-control
chmod +x install.sh
./install.sh
```

### 2. Start the System

```bash
# Quick start (server + demo device)
./quick_start.sh

# Or start components separately
./start_server.sh          # Start server only
./start_device.sh my-device # Start device client
```

### 3. Access Web Interface

Open your browser to the URL shown in the terminal output (includes your secure auth token).

## 📖 Documentation

- **[Complete Usage Guide](README_USAGE.md)** - Detailed documentation
- **[Installation Guide](#installation)** - Platform-specific setup
- **[Security Guide](#security)** - Important security considerations
- **[API Reference](#api)** - HTTP API documentation

## 🖥️ System Requirements

### Server
- Python 3.7+
- 512MB+ RAM (recommended 1GB+)
- Network connectivity
- Linux, macOS, or Termux

### Devices
- Python 3.7+
- WebSocket connectivity to server
- 128MB+ RAM for basic operation

## 🔧 Installation

### Termux (Android)
```bash
pkg update -y
pkg install python git curl
git clone https://github.com/MrNova420/unified-control.git
cd unified-control
./install.sh
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip git
git clone https://github.com/MrNova420/unified-control.git
cd unified-control
./install.sh
```

### Manual Installation
```bash
pip install -r requirements.txt
python unified_agent_with_ui.py --help
```

## 🎮 Usage Examples

### Start Server
```bash
python unified_agent_with_ui.py \
  --mode server \
  --auth YOUR_SECRET_TOKEN \
  --ws-port 8765 \
  --http-port 8766
```

### Connect Device
```bash
python unified_agent_with_ui.py \
  --mode device \
  --id my-device-1 \
  --server ws://127.0.0.1:8765 \
  --auth YOUR_SECRET_TOKEN \
  --exec-allowed \
  --tags production mobile
```

### Send Commands (CLI)
```bash
# List connected devices
python control_cli.py devices

# Send command to all devices
python control_cli.py send all "echo Hello World"

# Send to specific device
python control_cli.py send id:my-device-1 "uptime"

# Deploy file to devices with execution allowed
python control_cli.py send tag:production "run_upload:file-id-here"
```

### Web Interface Commands
- `echo "Hello World"` - Send text command
- `run_upload:file_id` - Execute uploaded file
- `uptime` - Show device uptime
- `df -h` - Show disk usage

## 🛠️ Advanced Configuration

### Environment Variables
```bash
export UC_AUTH_TOKEN="your-secure-token"
export UC_HOST="0.0.0.0"
export UC_WS_PORT="8765"
export UC_HTTP_PORT="8766"
```

### Production Deployment
1. Generate strong authentication token
2. Configure firewall rules
3. Set up HTTPS/WSS with certificates
4. Enable systemd service
5. Configure log rotation

### Device Auto-Detection
The system automatically optimizes for your hardware:
- Detects RAM and CPU capacity
- Sets appropriate device limits
- Configures memory restrictions
- Adjusts execution timeouts

## 🔒 Security Features

- **Authentication Required**: All connections require valid token
- **Sandboxed Execution**: Files run in isolated environment with limits
- **File Integrity**: SHA256 verification for all uploads
- **Audit Logging**: Complete trail of all activities
- **Per-Device Permissions**: Granular execution control
- **Resource Limits**: CPU, memory, and time constraints
- **Safe Defaults**: Conservative security settings

## 📊 Management Tools

### Command Line Interface
```bash
python control_cli.py devices           # List devices
python control_cli.py uploads          # List files
python control_cli.py audit            # Show logs
python control_cli.py stats            # System stats
python control_cli.py cleanup --days 7 # Clean old data
```

### Device Simulator
```bash
python device_simulator.py 10  # Simulate 10 devices
```

### Web Dashboard
- Real-time device monitoring
- File upload and deployment
- Command execution
- Audit log viewing
- System statistics

## 🔄 API Reference

### WebSocket (Device Communication)
- Authentication handshake
- Heartbeat mechanism
- Command execution
- Result reporting

### HTTP API (Web Interface)
- `GET /ui?token=TOKEN` - Web interface
- `POST /api/upload` - File upload
- `GET /api/devices` - Device list
- `POST /api/send` - Send command
- `GET /api/uploads` - File list

## 🧪 Testing

```bash
# Start test environment
./quick_start.sh

# Run device simulator
python device_simulator.py 5

# Test CLI commands
python control_cli.py stats
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Read the security guidelines
2. Test on multiple platforms
3. Update documentation
4. Add appropriate safeguards

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is provided for legitimate device management purposes. Users are responsible for:
- Only using on devices they own
- Complying with applicable laws
- Implementing appropriate security measures
- Understanding the risks involved

## 🆘 Support

- Check `unified_control.log` for detailed logs
- Review `README_USAGE.md` for common solutions
- Ensure all devices use the same auth token
- Verify network connectivity and firewall settings

## 🎯 Roadmap

- [ ] HTTPS/WSS support with certificates
- [ ] Role-based access control
- [ ] Plugin system for custom commands
- [ ] Mobile app for management
- [ ] Docker containerization
- [ ] Kubernetes deployment options