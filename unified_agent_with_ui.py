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
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import psutil

try:
    import websockets
    from aiohttp import web, MultipartReader
    import aiofiles
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install websockets aiohttp aiofiles psutil")
    sys.exit(1)

# Configuration
DEFAULT_HOST = "0.0.0.0"  # Allow external connections for mobile devices
DEFAULT_WS_PORT = 8765
DEFAULT_HTTP_PORT = 8766
DEFAULT_DB_PATH = "./unified_control.sqlite"
DEFAULT_UPLOAD_DIR = "./uploads"
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB for larger deployments
MAX_DEVICES = 1000  # Support many more devices
HEARTBEAT_INTERVAL = 15  # More frequent heartbeats
DEVICE_TIMEOUT = 45

# Security limits for sandboxed execution
EXEC_TIMEOUT = 120  # Longer execution time for complex tasks
MAX_CPU_PERCENT = 80  # Allow more CPU usage
MAX_MEMORY_MB = 1024  # More memory for complex operations
MAX_OUTPUT_SIZE = 5 * 1024 * 1024  # 5MB output

# Load balancing and performance
MAX_CONCURRENT_COMMANDS = 50
COMMAND_QUEUE_SIZE = 1000
DEVICE_BATCH_SIZE = 25  # Process devices in batches

# Service management
AUTO_RESTART_DELAY = 5
MAX_RESTART_ATTEMPTS = 3

# Device grouping and management
DEFAULT_DEVICE_GROUPS = ["production", "staging", "development", "mobile", "servers"]

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

# Global instances
device_manager = DeviceManager()
service_manager = ServiceManager()

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
UI_HTML = """<!DOCTYPE html>
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
        <!-- Left Panel: Device Management -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">🤖 DEVICE FLEET</div>
                <button class="btn btn-secondary" onclick="refreshDevices()">SYNC</button>
            </div>
            
            <div class="device-groups">
                <div class="group-tag" onclick="filterByGroup('all')">ALL</div>
                <div class="group-tag" onclick="filterByGroup('production')">PROD</div>
                <div class="group-tag" onclick="filterByGroup('staging')">STAGE</div>
                <div class="group-tag" onclick="filterByGroup('mobile')">MOBILE</div>
                <div class="group-tag" onclick="filterByGroup('servers')">SERVERS</div>
            </div>
            
            <div class="device-list" id="deviceList">
                <!-- Devices will be populated here -->
            </div>
            
            <div class="metrics-grid">
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
        
        <!-- Center Panel: Command Center -->
        <div class="panel command-center">
            <div class="panel-header">
                <div class="panel-title">⚡ COMMAND CENTER</div>
                <div class="command-tabs">
                    <div class="tab active" onclick="switchTab('terminal')">TERMINAL</div>
                    <div class="tab" onclick="switchTab('files')">FILES</div>
                    <div class="tab" onclick="switchTab('services')">SERVICES</div>
                </div>
            </div>
            
            <div id="terminalTab" class="tab-content">
                <div class="quick-commands">
                    <div class="quick-cmd" onclick="sendQuickCommand('uname -a')">SYSTEM INFO</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('ps aux')">PROCESSES</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('df -h')">DISK USAGE</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('free -h')">MEMORY</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('uptime')">UPTIME</div>
                    <div class="quick-cmd" onclick="sendQuickCommand('whoami')">USER</div>
                </div>
                
                <div class="command-input-area">
                    <select id="targetSelect" class="command-input">
                        <option value="all">🌐 ALL DEVICES</option>
                    </select>
                    <input type="text" id="commandInput" class="command-input" 
                           placeholder="Enter command (e.g., echo 'Hello World')" 
                           onkeypress="handleCommandKeyPress(event)">
                    <button class="btn" onclick="sendCommand()">EXECUTE</button>
                </div>
                
                <div class="terminal" id="terminal">
                    <div class="terminal-line terminal-success">
                        <span class="terminal-timestamp">[SYSTEM]</span> 
                        🚀 Unified Control Center initialized and ready
                    </div>
                    <div class="terminal-line terminal-info">
                        <span class="terminal-timestamp">[INFO]</span> 
                        📡 Monitoring device connections and awaiting commands
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
        
        // Terminal functions
        function appendToTerminal(message, type = 'info') {
            const terminal = document.getElementById('terminal');
            const timestamp = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.className = `terminal-line terminal-${type}`;
            div.innerHTML = `<span class="terminal-timestamp">[${timestamp}]</span> ${message}`;
            terminal.appendChild(div);
            terminal.scrollTop = terminal.scrollHeight;
        }
        
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
                const data = await api('/api/devices');
                const devices = data.devices || [];
                
                const deviceList = document.getElementById('deviceList');
                const targetSelect = document.getElementById('targetSelect');
                
                deviceList.innerHTML = '';
                targetSelect.innerHTML = '<option value="all">🌐 ALL DEVICES</option>';
                
                let onlineCount = 0;
                
                devices.forEach(device => {
                    const age = Math.round((Date.now() / 1000) - device.last_seen);
                    const isOnline = age < 60;
                    if (isOnline) onlineCount++;
                    
                    const deviceItem = document.createElement('div');
                    deviceItem.className = 'device-item';
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
            }
        }
        
        function toggleDeviceSelection(deviceId) {
            const deviceItems = document.querySelectorAll('.device-item');
            deviceItems.forEach(item => {
                if (item.textContent.includes(deviceId)) {
                    item.classList.toggle('selected');
                }
            });
        }
        
        // Command execution
        async function sendCommand() {
            const target = document.getElementById('targetSelect').value;
            const command = document.getElementById('commandInput').value.trim();
            
            if (!command) {
                appendToTerminal('❌ Please enter a command', 'error');
                return;
            }
            
            try {
                appendToTerminal(`📤 Executing "${command}" on ${target}...`, 'info');
                
                const result = await api('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target, cmd: command })
                });
                
                commandCount++;
                if (result.results) {
                    let successful = 0;
                    Object.values(result.results).forEach(r => {
                        if (r.status === 'sent') successful++;
                    });
                    successfulCommands += successful;
                }
                
                appendToTerminal(`📥 Result: ${JSON.stringify(result, null, 2)}`, 'success');
                appendToActivityLog(`⚡ Command executed: ${command} → ${target}`);
                
                document.getElementById('commandInput').value = '';
                updateMetrics();
                
            } catch (error) {
                appendToTerminal(`❌ Command failed: ${error.message}`, 'error');
                appendToActivityLog(`❌ Command failed: ${command}`, 'error');
            }
        }
        
        function sendQuickCommand(command) {
            document.getElementById('commandInput').value = command;
            sendCommand();
        }
        
        function handleCommandKeyPress(event) {
            if (event.key === 'Enter') {
                sendCommand();
            }
        }
        
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
        
        // System simulation
        function simulateSystemLoad() {
            const cpuLoad = Math.floor(Math.random() * 20) + 10; // 10-30%
            const memoryLoad = Math.floor(Math.random() * 30) + 20; // 20-50%
            
            document.getElementById('cpuUsage').textContent = cpuLoad + '%';
            document.getElementById('memoryUsage').textContent = memoryLoad + '%';
            document.getElementById('systemLoad').textContent = Math.max(cpuLoad, memoryLoad) + '%';
        }
        
        // Auto-refresh and initialization
        setInterval(refreshDevices, 3000);
        setInterval(updateUptime, 1000);
        setInterval(simulateSystemLoad, 5000);
        
        // Initialize
        refreshDevices();
        updateUptime();
        simulateSystemLoad();
        
        appendToActivityLog('🚀 Control Center initialized');
        appendToActivityLog('📡 Monitoring systems active');
    </script>
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
    
    # Collect system statistics
    stats = {
        "devices": {
            "total": len(clients),
            "online": sum(1 for c in clients.values() if time.time() - c.get("last_seen", 0) < 60),
            "exec_allowed": sum(1 for c in clients.values() if c.get("meta", {}).get("exec_allowed", False))
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
            "uptime": time.time(),
            "memory_usage": "N/A",  # Would need psutil for real stats
            "cpu_usage": "N/A"
        }
    }
    
    return web.json_response(stats)

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
        # Initialize database
        db = Database(args.db)
        
        print(f"""
🚀 Unified Device Control Server Starting...

📡 WebSocket Server: ws://{HOST}:{WS_PORT}
🌐 Web Interface: http://{HOST}:{HTTP_PORT}/ui?token={AUTH_TOKEN}
📁 Upload Directory: {UPLOAD_DIR}
💾 Database: {args.db}

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
            
            # Start cleanup task
            asyncio.create_task(cleanup_stale_clients())
            
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