# 🚀 Unified Control System - Complete Guide

A professional-grade device management and control system with advanced bot networking capabilities, real-time monitoring, and comprehensive device control features.

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📖 Usage Guide](#-usage-guide)
- [🛠️ Advanced Configuration](#️-advanced-configuration)
- [🤖 Bot Management](#-bot-management)
- [🔧 Command Reference](#-command-reference)
- [📊 Monitoring & Analytics](#-monitoring--analytics)
- [🔒 Security](#-security)
- [🐛 Troubleshooting](#-troubleshooting)

## 🎯 Overview

The Unified Control System is a powerful, web-based device management platform that allows you to:

- **Control multiple devices** from a single web interface
- **Execute commands** across device networks with real-time output
- **Monitor system performance** with comprehensive analytics
- **Deploy and manage bots** for automated tasks
- **Discover and recruit** new devices on your network

## ✨ Features

### 🖥️ **Core Functionality**
- **Real-time Terminal**: Execute commands on local and remote devices with live output
- **Device Discovery**: Automatically find and recruit devices on your network
- **Bot Management**: Create, deploy, and control specialized bots
- **File Management**: Upload, deploy, and execute files across devices
- **System Monitoring**: Real-time CPU, memory, and network monitoring

### 🤖 **Bot Network Features**
- **15+ Bot Templates**: Pre-configured bots for different use cases
- **Custom Bot Creation**: Build specialized bots for specific tasks
- **Centralized Control**: Manage all bots from a single interface
- **Load Balancing**: Distribute commands across 50+ concurrent workers
- **Auto-Optimization**: Dynamic resource allocation based on system capabilities

### 📊 **Advanced Features**
- **Persistent Storage**: SQLite database for logs, sessions, and metrics
- **Session Management**: Track user activity and command history
- **Security Filtering**: Prevent dangerous commands with built-in safeguards
- **Network Scanning**: Discover and analyze devices on local networks
- **Resource Optimization**: Automatic system tuning for optimal performance

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- Linux, macOS, or Termux (Android)
- Network connectivity for multi-device setups

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/MrNova420/unified-control.git
cd unified-control

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x *.sh
```

### 2. Start the Server

```bash
# Quick start (recommended)
./start_unified.sh

# Or manual start
python3 unified_agent_with_ui.py --mode server --auth your_secure_token
```

### 3. Access the Web Interface

Open your browser and navigate to:
```
http://localhost:8766/ui?token=your_secure_token
```

## 📖 Usage Guide

### 🖥️ **Terminal Operations**

The terminal is the heart of the system. It provides real-time command execution with detailed output.

#### Basic Commands
```bash
# System information
uname -a          # System details
whoami           # Current user
free -h          # Memory usage
df -h            # Disk usage
ps aux           # Running processes
```

#### Network Commands
```bash
# Network information
ip addr show     # Network interfaces
netstat -tuln    # Open ports
ping google.com  # Network connectivity
nmap -sn 192.168.1.0/24  # Network scan
```

#### File Operations
```bash
# File management
ls -la           # List files
find / -name "*.log"  # Find files
cat /etc/passwd  # View file contents
tail -f /var/log/syslog  # Monitor logs
```

### 🔍 **Device Discovery**

1. **Click "🔍 DISCOVER DEVICES"** to open the discovery panel
2. **Click "SCAN LOCAL NETWORK"** to start scanning
3. **Review discovered devices** with their IP addresses and services
4. **Click "RECRUIT"** on devices you want to add to your network

### 🤖 **Bot Management**

#### Creating Bots
1. **Select bot type** from the dropdown (Mobile, Server, Scanner, etc.)
2. **Click "CREATE BOT"** and enter a unique bot ID
3. **Review the generated deployment script**
4. **Deploy the script** on target devices

#### Bot Templates Available
- **📱 Mobile Termux Bot**: Android device control with Termux
- **🖥️ Server Bot**: Linux server management
- **🔍 Network Scanner Bot**: Network reconnaissance
- **📊 Monitor Bot**: System monitoring and metrics
- **🌐 Proxy Bot**: Traffic routing and anonymization
- **⛏️ Mining Bot**: Cryptocurrency mining operations
- **🔒 Security Auditor**: System security analysis

#### Managing Existing Bots
- **View bot status** in the Bot Network Fleet panel
- **Execute commands** on specific bot groups using tags
- **Monitor bot performance** through system metrics
- **Remove inactive bots** using the management interface

### 📁 **File Management**

#### Uploading Files
1. **Click the "FILES" tab** in the command center
2. **Drag and drop files** or click to browse
3. **Wait for upload confirmation**
4. **Deploy files** to selected devices using `run_upload:<file_id>`

#### Supported File Types
- **Scripts**: .py, .sh, .bat
- **Configurations**: .conf, .json, .xml
- **Binaries**: .exe, .bin, .app
- **Documents**: .txt, .md, .log

### 🎛️ **System Monitoring**

#### Real-time Metrics
- **CPU Usage**: Current processor utilization
- **Memory Usage**: RAM consumption and availability
- **Disk Usage**: Storage space utilization
- **Network Activity**: Connection counts and traffic
- **Uptime**: System running time

#### Performance Analytics
- **Historical Data**: 24-hour performance graphs
- **Trend Analysis**: Performance patterns over time
- **Resource Alerts**: Notifications for high usage
- **Capacity Planning**: Resource usage projections

## 🛠️ Advanced Configuration

### 🔧 **Server Configuration**

#### Environment Variables
```bash
export UC_AUTH_TOKEN="your_secure_token_here"
export UC_HOST="0.0.0.0"                    # Allow external connections
export UC_WS_PORT="8765"                    # WebSocket port
export UC_HTTP_PORT="8766"                  # HTTP server port
export UC_MAX_DEVICES="1000"                # Maximum connected devices
export UC_MAX_WORKERS="50"                  # Concurrent command workers
```

#### Database Configuration
The system uses SQLite for data storage. Database location:
```bash
./unified_control.sqlite
```

Tables created automatically:
- `audit_logs`: Command execution history
- `user_sessions`: User activity tracking
- `command_history`: Detailed command logs
- `system_metrics`: Performance data
- `recruited_bots`: Bot network information

### ⚙️ **Performance Tuning**

#### Auto-Optimization
The system automatically optimizes based on available hardware:

| RAM | Max Devices | Workers | Memory Limit |
|-----|-------------|---------|--------------|
| < 1GB | 50 | 10 | 256MB |
| 1-2GB | 200 | 20 | 512MB |
| 2-4GB | 500 | 30 | 1GB |
| 4-8GB | 1000 | 40 | 2GB |
| 8-16GB | 2000 | 50 | 3GB |
| 16GB+ | 5000 | 100 | 4GB |

#### Manual Tuning
Override auto-optimization by setting environment variables:
```bash
export UC_MAX_DEVICES="2000"
export UC_MAX_WORKERS="75"
export UC_MEMORY_LIMIT="2048"
```

### 🔌 **Network Configuration**

#### Firewall Settings
Ensure these ports are open:
```bash
# Server ports
8765/tcp  # WebSocket connections
8766/tcp  # HTTP web interface

# Discovery ports
22/tcp    # SSH (optional)
5555/tcp  # ADB (Android, optional)
```

#### Multi-Network Setup
For distributed deployments:
1. **Configure external access** by setting `UC_HOST="0.0.0.0"`
2. **Use proper authentication** tokens for security
3. **Set up port forwarding** if behind NAT
4. **Configure SSL/TLS** for production use

## 🤖 Bot Management

### 📱 **Mobile Bot Setup (Termux)**

#### Installation on Android
1. **Install Termux** from F-Droid (recommended) or Google Play
2. **Update packages**: `pkg update && pkg upgrade`
3. **Install Python**: `pkg install python`
4. **Install dependencies**: `pip install websockets psutil requests`
5. **Deploy bot script** generated by the system

#### Termux-Specific Commands
```bash
# Termux API access
pkg install termux-api
termux-battery-status    # Battery information
termux-location         # GPS coordinates
termux-camera-photo     # Take photos
termux-sms-list        # SMS access
```

### 🖥️ **Server Bot Setup (Linux)**

#### SSH-Based Deployment
```bash
# Copy bot script to target server
scp bot_client.py user@target:/tmp/

# Execute on target
ssh user@target "cd /tmp && python3 bot_client.py --server ws://your_server:8765 --token your_token &"
```

#### Systemd Service (Persistent)
Create `/etc/systemd/system/unified-bot.service`:
```ini
[Unit]
Description=Unified Control Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/unified-bot
ExecStart=/usr/bin/python3 bot_client.py --server ws://your_server:8765 --token your_token
Restart=always

[Install]
WantedBy=multi-user.target
```

### 🔧 **Custom Bot Development**

#### Bot Client Template
```python
#!/usr/bin/env python3
import asyncio
import websockets
import json
import subprocess

class CustomBot:
    def __init__(self, server_url, token, bot_id):
        self.server_url = server_url
        self.token = token
        self.bot_id = bot_id
    
    async def connect(self):
        uri = f"{self.server_url}?token={self.token}&id={self.bot_id}"
        async with websockets.connect(uri) as websocket:
            await self.register()
            await self.message_loop(websocket)
    
    async def register(self):
        # Send registration message
        await websocket.send(json.dumps({
            "type": "register",
            "device_id": self.bot_id,
            "capabilities": ["command_execution", "file_transfer"]
        }))
    
    async def execute_command(self, command):
        # Execute system command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
```

## 🔧 Command Reference

### 📋 **Built-in Commands**

#### System Information
- `SYSTEM INFO` → `uname -a` - System details
- `MEMORY` → `free -h` - Memory usage
- `DISK USAGE` → `df -h` - Disk space
- `PROCESSES` → `ps aux | head -20` - Running processes
- `UPTIME` → `uptime` - System uptime

#### Network Operations
- `NETWORK INFO` → `ip addr show` - Network interfaces
- `OPEN PORTS` → `netstat -tuln` - Listening ports
- `NETWORK SCAN` → `nmap -sn 192.168.1.0/24` - Network discovery
- `PUBLIC IP` → `curl -s ipinfo.io` - External IP address
- `CONNECTIONS` → `ss -tuln` - Active connections

#### Security & Analysis
- `VULN SCAN` → `nmap -sV -sC target_ip` - Vulnerability scan
- `USERS` → `cat /etc/passwd | head -10` - System users
- `LOG FILES` → `find / -name "*.log" | head -10` - Log files
- `CRON JOBS` → `crontab -l` - Scheduled tasks

### 🎯 **Target Selection**

#### Device Targeting
- `all` - Execute on all connected devices
- `id:device-name` - Specific device by ID
- `tag:mobile` - All devices with "mobile" tag
- `tag:servers` - All server-type devices

#### Tag Categories
- `mobile` - Mobile devices (phones, tablets)
- `servers` - Server systems
- `scanners` - Network scanning bots
- `monitors` - System monitoring bots
- `production` - Production environment devices
- `staging` - Staging/test environment devices

### 🔄 **File Operations**

#### Upload Commands
```bash
# Upload file
# 1. Use web interface to upload
# 2. Note the file ID from response
# 3. Deploy using:
run_upload:<file_id>
```

#### File Management
```bash
# File operations
ls -la /path/to/directory
cat /path/to/file
grep "pattern" /path/to/file
chmod +x /path/to/script
./script.sh
```

## 📊 Monitoring & Analytics

### 📈 **Performance Metrics**

#### System Metrics Tracked
- **CPU Usage**: Per-core utilization percentages
- **Memory Usage**: RAM and swap utilization
- **Disk I/O**: Read/write operations and bandwidth
- **Network Traffic**: Incoming/outgoing data rates
- **Process Count**: Active process monitoring
- **Load Average**: System load over time

#### Database Analytics
The system maintains detailed analytics in SQLite:

```sql
-- Command execution statistics
SELECT 
    command,
    COUNT(*) as execution_count,
    AVG(execution_time) as avg_time,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
FROM command_history 
GROUP BY command 
ORDER BY execution_count DESC;

-- Device activity patterns
SELECT 
    device_id,
    COUNT(*) as total_commands,
    MAX(timestamp) as last_activity
FROM command_history 
GROUP BY device_id 
ORDER BY total_commands DESC;
```

### 📊 **Real-time Dashboard**

#### Live Metrics Display
- **CPU Load Graph**: Real-time processor usage
- **Memory Usage Bar**: Current RAM utilization
- **Network Activity**: Live connection counts
- **Command Success Rate**: Execution statistics
- **Device Status**: Connected/disconnected devices

#### Historical Analysis
- **24-hour Performance**: Detailed performance graphs
- **Usage Trends**: Command execution patterns
- **Error Analysis**: Failed command investigation
- **Capacity Planning**: Resource usage projections

## 🔒 Security

### 🛡️ **Security Features**

#### Command Filtering
The system blocks dangerous commands:
- `rm -rf` - Recursive file deletion
- `format` - Disk formatting
- `shutdown` - System shutdown
- `reboot` - System restart
- `halt` - System halt

#### Authentication
- **Token-based auth**: Secure API access
- **Session management**: User activity tracking
- **Request validation**: Input sanitization
- **Rate limiting**: Prevents abuse

#### Audit Logging
All activities are logged:
```sql
-- Audit log structure
CREATE TABLE audit_logs (
    timestamp REAL NOT NULL,
    device_id TEXT NOT NULL,
    action TEXT NOT NULL,
    command TEXT,
    result TEXT,
    user_session TEXT,
    ip_address TEXT
);
```

### 🔐 **Best Practices**

#### Production Deployment
1. **Change default tokens** - Use strong, unique authentication
2. **Enable HTTPS** - Encrypt web traffic
3. **Firewall configuration** - Restrict access to necessary ports
4. **Regular updates** - Keep system dependencies current
5. **Monitor logs** - Regular audit log review

#### Network Security
- **VPN Usage**: Deploy over VPN for remote access
- **Access Control**: Limit IP ranges for connections
- **Certificate Management**: Use valid SSL certificates
- **Network Segmentation**: Isolate bot networks

## 🐛 Troubleshooting

### ❗ **Common Issues**

#### Server Won't Start
```bash
# Check dependencies
pip install -r requirements.txt

# Verify Python version
python3 --version  # Should be 3.7+

# Check port availability
netstat -tuln | grep 8766
```

#### Connection Issues
```bash
# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     ws://localhost:8765/

# Check firewall
sudo ufw status
sudo iptables -L
```

#### Command Execution Fails
1. **Check target selection** - Ensure devices are connected
2. **Verify permissions** - Commands may require elevated privileges
3. **Review command syntax** - Check for typos or invalid commands
4. **Monitor system resources** - High load may cause timeouts

#### Database Issues
```bash
# Check database file
ls -la unified_control.sqlite

# Verify database integrity
sqlite3 unified_control.sqlite ".schema"

# Reset database (caution: loses data)
rm unified_control.sqlite
# Restart server to recreate
```

### 🔧 **Performance Issues**

#### High Memory Usage
1. **Reduce max devices**: Lower `UC_MAX_DEVICES`
2. **Decrease workers**: Lower `UC_MAX_WORKERS`
3. **Clear command history**: Periodic cleanup
4. **Monitor bot count**: Remove inactive bots

#### Slow Response Times
1. **Check network latency**: Test connectivity to devices
2. **Monitor CPU usage**: High load affects performance
3. **Optimize commands**: Use efficient command syntax
4. **Review log files**: Check for errors or warnings

### 📞 **Getting Help**

#### Debug Information
When reporting issues, include:
```bash
# System information
uname -a
python3 --version
pip list | grep -E "(websockets|aiohttp|psutil)"

# Server logs
tail -50 /var/log/unified-control.log

# Configuration
env | grep UC_
```

#### Log Analysis
```bash
# Monitor real-time logs
tail -f unified_control.log

# Search for errors
grep -i error unified_control.log

# Performance analysis
grep -i "execution_time" unified_control.log
```

---

## 🚀 **Getting Started Checklist**

- [ ] Install Python 3.7+ and dependencies
- [ ] Start the server with `./start_unified.sh`
- [ ] Access web interface at `http://localhost:8766/ui?token=your_token`
- [ ] Initialize your local device as control bot (automatic)
- [ ] Test terminal commands (`whoami`, `uname -a`)
- [ ] Discover devices on your network
- [ ] Create your first bot
- [ ] Deploy bot to target device
- [ ] Monitor system performance
- [ ] Review command execution logs

**🎉 Congratulations! You're ready to manage your device network with the Unified Control System.**

---

*For additional support, advanced configurations, or feature requests, please refer to the project documentation or open an issue on GitHub.*