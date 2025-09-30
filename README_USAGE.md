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
