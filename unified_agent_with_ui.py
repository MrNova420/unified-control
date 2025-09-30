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
DEFAULT_HOST = "127.0.0.1"
DEFAULT_WS_PORT = 8765
DEFAULT_HTTP_PORT = 8766
DEFAULT_DB_PATH = "./unified_control.sqlite"
DEFAULT_UPLOAD_DIR = "./uploads"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DEVICES = 100
HEARTBEAT_INTERVAL = 30
DEVICE_TIMEOUT = 60

# Security limits for sandboxed execution
EXEC_TIMEOUT = 30
MAX_CPU_PERCENT = 50
MAX_MEMORY_MB = 512
MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB

# Global state
clients: Dict[str, Dict] = {}
clients_lock = asyncio.Lock()
db = None
AUTH_TOKEN = None
HOST = DEFAULT_HOST
WS_PORT = DEFAULT_WS_PORT
HTTP_PORT = DEFAULT_HTTP_PORT
UPLOAD_DIR = DEFAULT_UPLOAD_DIR

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
    <title>Unified Device Control Console</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; overflow-x: hidden; }
        header { background: #161b22; padding: 1rem; border-bottom: 1px solid #30363d; }
        .wrap { display: flex; height: calc(100vh - 60px); }
        .left, .right { padding: 1rem; overflow-y: auto; }
        .left { width: 40%; border-right: 1px solid #30363d; background: #0d1117; }
        .right { width: 60%; background: #161b22; }
        h2 { color: #58a6ff; margin-bottom: 1rem; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
        th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #30363d; }
        th { background: #21262d; color: #58a6ff; }
        .btn { background: #238636; color: white; border: none; padding: 0.5rem 1rem; border-radius: 3px; cursor: pointer; }
        .btn:hover { background: #2ea043; }
        .btn-danger { background: #da3633; }
        .btn-danger:hover { background: #f85149; }
        .upload-list { margin-bottom: 1rem; }
        .upload-item { background: #21262d; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 3px; border: 1px solid #30363d; }
        .upload-item strong { color: #58a6ff; }
        .chat { height: 400px; background: #0d1117; border: 1px solid #30363d; padding: 1rem; overflow-y: auto; margin-bottom: 1rem; font-family: monospace; }
        .chat-msg { margin-bottom: 0.5rem; }
        .chat-timestamp { color: #7d8590; font-size: 0.8em; }
        .chat-content { color: #c9d1d9; }
        .chat-error { color: #f85149; }
        .chat-success { color: #3fb950; }
        .row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
        input, select { background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 0.5rem; border-radius: 3px; }
        input[type="file"] { padding: 0.25rem; }
        .status-online { color: #3fb950; }
        .status-offline { color: #f85149; }
        .warning { background: #422b19; border: 1px solid #d29922; color: #f0d050; padding: 1rem; margin-bottom: 1rem; border-radius: 3px; }
        .code { background: #161b22; padding: 0.25rem; border-radius: 2px; font-family: monospace; }
    </style>
</head>
<body>
    <header>
        <strong>🔧 Unified Device Control Console</strong> — Secure Local Management System
    </header>
    
    <div class="warning">
        ⚠️ <strong>Security Notice:</strong> Only use this system on devices you own and control. All commands are logged and audited.
    </div>
    
    <div class="wrap">
        <div class="left">
            <h2>📱 Connected Devices</h2>
            <table id="devices">
                <thead>
                    <tr>
                        <th>Device ID</th>
                        <th>Tags</th>
                        <th>Exec Allowed</th>
                        <th>Last Seen</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
            
            <h2>📁 File Uploads</h2>
            <div class="upload-list" id="uploads"></div>
            <form id="uploadForm">
                <div class="row">
                    <input type="file" id="file" required>
                    <button type="submit" class="btn">Upload File</button>
                </div>
            </form>
        </div>
        
        <div class="right">
            <h2>💬 Command Console</h2>
            <div class="chat" id="chat"></div>
            <div class="row">
                <select id="target">
                    <option value="all">All Devices</option>
                </select>
                <input id="cmd" placeholder="Enter command (e.g., echo hello, run_upload:file_id)" style="flex: 1;">
                <button class="btn" id="sendBtn">Send Command</button>
            </div>
            <p style="color:#7d8590; font-size: 0.9em; margin-top: 0.5rem;">
                Special commands: <span class="code">run_upload:&lt;file_id&gt;</span> executes uploaded file on devices with exec_allowed=true
            </p>
        </div>
    </div>

    <script>
        const token = new URLSearchParams(window.location.search).get('token');
        if (!token) {
            document.body.innerHTML = '<div style="padding:2rem;text-align:center;color:#f85149;">❌ Access token required in URL: ?token=YOUR_TOKEN</div>';
        }
        
        async function api(endpoint, options = {}) {
            const url = `${endpoint}${endpoint.includes('?') ? '&' : '?'}token=${token}`;
            const response = await fetch(url, options);
            return await response.json();
        }
        
        function appendChat(message, type = 'info') {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = 'chat-msg';
            
            const timestamp = new Date().toLocaleTimeString();
            const typeClass = type === 'error' ? 'chat-error' : type === 'success' ? 'chat-success' : 'chat-content';
            
            div.innerHTML = `
                <div class="chat-timestamp">[${timestamp}]</div>
                <div class="${typeClass}">${typeof message === 'object' ? JSON.stringify(message, null, 2) : message}</div>
            `;
            
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
        
        async function refresh() {
            try {
                // Update devices
                const devices = await api('/api/devices');
                const tbody = document.querySelector('#devices tbody');
                tbody.innerHTML = '';
                
                const targetSelect = document.getElementById('target');
                const currentTarget = targetSelect.value;
                targetSelect.innerHTML = '<option value="all">All Devices</option>';
                
                (devices.devices || []).forEach(dev => {
                    const tr = document.createElement('tr');
                    const age = Math.round((Date.now() / 1000) - dev.last_seen);
                    const status = age < 60 ? 'online' : 'offline';
                    const statusClass = status === 'online' ? 'status-online' : 'status-offline';
                    
                    tr.innerHTML = `
                        <td>${dev.id}</td>
                        <td>${(dev.tags || []).join(', ')}</td>
                        <td>${dev.exec_allowed ? '✅ Yes' : '❌ No'}</td>
                        <td>${age}s ago</td>
                        <td class="${statusClass}">●</td>
                    `;
                    tbody.appendChild(tr);
                    
                    // Add to target selector
                    const option = document.createElement('option');
                    option.value = `id:${dev.id}`;
                    option.textContent = dev.id;
                    targetSelect.appendChild(option);
                });
                
                targetSelect.value = currentTarget;
                
                // Update uploads
                const uploads = await api('/api/uploads');
                const uploadsDiv = document.getElementById('uploads');
                uploadsDiv.innerHTML = '';
                
                (uploads.uploads || []).forEach(upload => {
                    const div = document.createElement('div');
                    div.className = 'upload-item';
                    div.innerHTML = `
                        <div><strong>${upload.filename}</strong> (${(upload.size / 1024).toFixed(1)} KB)</div>
                        <div style="color:#7d8590; font-size:0.8em;">ID: ${upload.id} | SHA256: ${upload.sha256.substring(0, 16)}...</div>
                        <div style="margin-top:0.5rem;">
                            <button class="btn" onclick="deployUpload('${upload.id}')">Deploy to Devices</button>
                        </div>
                    `;
                    uploadsDiv.appendChild(div);
                });
                
            } catch (error) {
                appendChat(`Refresh error: ${error.message}`, 'error');
            }
        }
        
        async function deployUpload(fileId) {
            const target = document.getElementById('target').value || 'all';
            
            if (!confirm(`Deploy file ${fileId} to ${target}?\\n\\nThis will execute the file on devices that have exec_allowed=true.\\nOnly proceed if you trust the file and target devices.`)) {
                return;
            }
            
            try {
                appendChat(`🚀 Deploying ${fileId} to ${target}...`);
                const result = await api('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        target: target,
                        cmd: `run_upload:${fileId}`
                    })
                });
                
                appendChat(`📤 Deploy result: ${JSON.stringify(result, null, 2)}`, 'success');
            } catch (error) {
                appendChat(`❌ Deploy failed: ${error.message}`, 'error');
            }
        }
        
        document.getElementById('sendBtn').onclick = async () => {
            const target = document.getElementById('target').value;
            const cmd = document.getElementById('cmd').value.trim();
            
            if (!cmd) {
                appendChat('❌ Please enter a command', 'error');
                return;
            }
            
            try {
                appendChat(`📤 Sending "${cmd}" to ${target}...`);
                const result = await api('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target, cmd: cmd })
                });
                
                appendChat(`📥 Command result: ${JSON.stringify(result, null, 2)}`, 'success');
                document.getElementById('cmd').value = '';
            } catch (error) {
                appendChat(`❌ Command failed: ${error.message}`, 'error');
            }
        };
        
        document.getElementById('cmd').onkeypress = (e) => {
            if (e.key === 'Enter') {
                document.getElementById('sendBtn').click();
            }
        };
        
        document.getElementById('uploadForm').onsubmit = async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('file');
            const file = fileInput.files[0];
            
            if (!file) {
                appendChat('❌ Please select a file', 'error');
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) {
                appendChat('❌ File too large (max 10MB)', 'error');
                return;
            }
            
            try {
                appendChat(`📤 Uploading ${file.name}...`);
                
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch(`/api/upload?token=${token}`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    appendChat(`✅ Upload successful: ${result.filename} (ID: ${result.id})`, 'success');
                    fileInput.value = '';
                    refresh();
                } else {
                    appendChat(`❌ Upload failed: ${result.error}`, 'error');
                }
            } catch (error) {
                appendChat(`❌ Upload error: ${error.message}`, 'error');
            }
        };
        
        // Auto-refresh every 3 seconds
        setInterval(refresh, 3000);
        refresh();
        
        // Initial welcome message
        appendChat('🚀 Unified Device Control Console initialized', 'success');
        appendChat('📡 Monitoring device connections and ready for commands', 'info');
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
            
            logging.info("Server started successfully")
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