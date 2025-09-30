#!/usr/bin/env python3
"""
Unified Control System - Management CLI
Command-line interface for system administration
"""

import asyncio
import json
import sqlite3
import sys
import argparse
from pathlib import Path
import requests
import time

class UnifiedControlCLI:
    """Command-line interface for Unified Control System"""
    
    def __init__(self, db_path="./unified_control.sqlite", server_url=None, auth_token=None):
        self.db_path = db_path
        self.server_url = server_url
        self.auth_token = auth_token
    
    def connect_db(self):
        """Connect to database"""
        if not Path(self.db_path).exists():
            print(f"❌ Database not found: {self.db_path}")
            sys.exit(1)
        return sqlite3.connect(self.db_path)
    
    def list_devices(self):
        """List all devices from database"""
        conn = self.connect_db()
        try:
            cursor = conn.execute("""
                SELECT id, tags, exec_allowed, last_seen, created_at, metadata 
                FROM devices ORDER BY last_seen DESC
            """)
            
            devices = cursor.fetchall()
            if not devices:
                print("📱 No devices found")
                return
            
            print(f"📱 Found {len(devices)} devices:\n")
            print(f"{'Device ID':<20} {'Tags':<20} {'Exec':<6} {'Last Seen':<12} {'Status':<8}")
            print("-" * 80)
            
            current_time = int(time.time())
            for device in devices:
                device_id, tags, exec_allowed, last_seen, created_at, metadata = device
                
                # Parse tags
                try:
                    tag_list = json.loads(tags) if tags else []
                    tags_str = ",".join(tag_list[:3])  # Show first 3 tags
                    if len(tag_list) > 3:
                        tags_str += "..."
                except:
                    tags_str = tags or ""
                
                # Calculate status
                age = current_time - (last_seen or 0)
                if age < 60:
                    status = "🟢 Online"
                elif age < 300:
                    status = "🟡 Recent"
                else:
                    status = "🔴 Offline"
                
                # Format last seen
                if last_seen:
                    if age < 60:
                        last_seen_str = f"{age}s ago"
                    elif age < 3600:
                        last_seen_str = f"{age//60}m ago"
                    else:
                        last_seen_str = f"{age//3600}h ago"
                else:
                    last_seen_str = "Never"
                
                exec_str = "✅ Yes" if exec_allowed else "❌ No"
                
                print(f"{device_id:<20} {tags_str:<20} {exec_str:<6} {last_seen_str:<12} {status}")
        
        finally:
            conn.close()
    
    def list_uploads(self):
        """List all uploaded files"""
        conn = self.connect_db()
        try:
            cursor = conn.execute("""
                SELECT id, filename, size, uploader, created_at, sha256 
                FROM uploads ORDER BY created_at DESC
            """)
            
            uploads = cursor.fetchall()
            if not uploads:
                print("📁 No uploads found")
                return
            
            print(f"📁 Found {len(uploads)} uploads:\n")
            print(f"{'File ID':<38} {'Filename':<25} {'Size':<10} {'Uploader':<12} {'Date'}")
            print("-" * 100)
            
            for upload in uploads:
                upload_id, filename, size, uploader, created_at, sha256 = upload
                
                # Format size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/(1024*1024):.1f}MB"
                
                # Format date
                date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(created_at))
                
                print(f"{upload_id:<38} {filename:<25} {size_str:<10} {uploader:<12} {date_str}")
        
        finally:
            conn.close()
    
    def audit_log(self, limit=50):
        """Show audit log"""
        conn = self.connect_db()
        try:
            cursor = conn.execute("""
                SELECT timestamp, device_id, action, command, result, user_agent
                FROM audit_log ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            
            logs = cursor.fetchall()
            if not logs:
                print("📋 No audit logs found")
                return
            
            print(f"📋 Audit Log (last {len(logs)} entries):\n")
            
            for log in logs:
                timestamp, device_id, action, command, result, user_agent = log
                date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                
                print(f"🕒 {date_str}")
                print(f"   Device: {device_id}")
                print(f"   Action: {action}")
                print(f"   Command: {command}")
                if result:
                    try:
                        result_obj = json.loads(result)
                        if isinstance(result_obj, dict) and 'success' in result_obj:
                            status = "✅ Success" if result_obj['success'] else "❌ Failed"
                            print(f"   Result: {status}")
                        else:
                            print(f"   Result: {result[:100]}...")
                    except:
                        print(f"   Result: {result[:100]}...")
                print()
        
        finally:
            conn.close()
    
    def send_command(self, target, command):
        """Send command via HTTP API"""
        if not self.server_url or not self.auth_token:
            print("❌ Server URL and auth token required for API commands")
            sys.exit(1)
        
        try:
            url = f"{self.server_url.replace('ws://', 'http://').replace('wss://', 'https://')}/api/send"
            params = {"token": self.auth_token}
            data = {"target": target, "cmd": command}
            
            print(f"📤 Sending command '{command}' to {target}...")
            
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            print("📥 Response:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Command failed: {e}")
    
    def cleanup_old_data(self, days=7):
        """Clean up old audit logs and disconnected devices"""
        conn = self.connect_db()
        try:
            cutoff_time = int(time.time()) - (days * 24 * 3600)
            
            # Clean old audit logs
            cursor = conn.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff_time,))
            audit_deleted = cursor.rowcount
            
            # Clean old disconnected devices
            cursor = conn.execute("DELETE FROM devices WHERE last_seen < ?", (cutoff_time,))
            devices_deleted = cursor.rowcount
            
            conn.commit()
            
            print(f"🧹 Cleanup completed:")
            print(f"   Deleted {audit_deleted} old audit log entries")
            print(f"   Deleted {devices_deleted} old device records")
        
        finally:
            conn.close()
    
    def stats(self):
        """Show system statistics"""
        conn = self.connect_db()
        try:
            # Device stats
            cursor = conn.execute("SELECT COUNT(*) FROM devices")
            total_devices = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM devices WHERE exec_allowed = 1")
            exec_devices = cursor.fetchone()[0]
            
            current_time = int(time.time())
            cursor = conn.execute("SELECT COUNT(*) FROM devices WHERE last_seen > ?", (current_time - 300,))
            online_devices = cursor.fetchone()[0]
            
            # Upload stats
            cursor = conn.execute("SELECT COUNT(*), COALESCE(SUM(size), 0) FROM uploads")
            upload_count, total_size = cursor.fetchone()
            
            # Audit stats
            cursor = conn.execute("SELECT COUNT(*) FROM audit_log")
            audit_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM audit_log WHERE timestamp > ?", (current_time - 86400,))
            recent_commands = cursor.fetchone()[0]
            
            print("📊 System Statistics")
            print("=" * 40)
            print(f"📱 Devices:")
            print(f"   Total: {total_devices}")
            print(f"   Online (5min): {online_devices}")
            print(f"   Exec allowed: {exec_devices}")
            print()
            print(f"📁 Uploads:")
            print(f"   Files: {upload_count}")
            print(f"   Total size: {total_size / (1024*1024):.1f} MB")
            print()
            print(f"📋 Activity:")
            print(f"   Total commands: {audit_count}")
            print(f"   Last 24h: {recent_commands}")
        
        finally:
            conn.close()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Unified Control System CLI")
    parser.add_argument("--db", default="./unified_control.sqlite", help="Database path")
    parser.add_argument("--server", help="Server URL for API commands")
    parser.add_argument("--token", help="Authentication token")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Device commands
    subparsers.add_parser("devices", help="List all devices")
    subparsers.add_parser("uploads", help="List uploaded files")
    
    # Audit commands
    audit_parser = subparsers.add_parser("audit", help="Show audit log")
    audit_parser.add_argument("--limit", type=int, default=50, help="Number of entries to show")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send command to devices")
    send_parser.add_argument("target", help="Target (all, id:device-1, tag:alpha)")
    send_parser.add_argument("command", help="Command to send")
    
    # Maintenance
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old data")
    cleanup_parser.add_argument("--days", type=int, default=7, help="Days to keep")
    
    subparsers.add_parser("stats", help="Show system statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = UnifiedControlCLI(args.db, args.server, args.token)
    
    try:
        if args.command == "devices":
            cli.list_devices()
        elif args.command == "uploads":
            cli.list_uploads()
        elif args.command == "audit":
            cli.audit_log(args.limit)
        elif args.command == "send":
            cli.send_command(args.target, args.command)
        elif args.command == "cleanup":
            cli.cleanup_old_data(args.days)
        elif args.command == "stats":
            cli.stats()
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()