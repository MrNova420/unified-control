#!/usr/bin/env python3
"""
Unified Control System - Device Simulator
Creates multiple simulated device clients for testing
"""

import asyncio
import sys
import logging
from unified_agent_with_ui import DeviceClient
import random
import string

# Configuration
DEFAULT_SERVER = "ws://127.0.0.1:8765"
DEFAULT_TOKEN = "your_auth_token_here"

def generate_device_id():
    """Generate a random device ID"""
    return f"sim-{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"

def generate_tags():
    """Generate random tags for device"""
    tag_options = ["alpha", "beta", "production", "testing", "mobile", "server", "edge"]
    return random.sample(tag_options, random.randint(1, 3))

async def run_simulated_device(device_id, server_url, auth_token, exec_allowed=False):
    """Run a single simulated device"""
    try:
        client = DeviceClient(
            device_id=device_id,
            server_url=server_url,
            auth_token=auth_token,
            tags=generate_tags(),
            exec_allowed=exec_allowed
        )
        
        print(f"🤖 Starting simulated device: {device_id} (exec: {exec_allowed})")
        await client.run()
        
    except Exception as e:
        logging.error(f"Device {device_id} error: {e}")

async def main():
    """Main simulator entry point"""
    if len(sys.argv) < 2:
        print("""
🤖 Unified Control Device Simulator

Usage:
    python device_simulator.py <num_devices> [server_url] [auth_token] [exec_ratio]

Arguments:
    num_devices : Number of devices to simulate (1-50)
    server_url  : WebSocket server URL (default: ws://127.0.0.1:8765)
    auth_token  : Authentication token (default: your_auth_token_here)
    exec_ratio  : Fraction of devices with exec_allowed (default: 0.3)

Examples:
    python device_simulator.py 5
    python device_simulator.py 10 ws://192.168.1.100:8765 mytoken123 0.5
""")
        sys.exit(1)
    
    num_devices = int(sys.argv[1])
    server_url = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SERVER
    auth_token = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_TOKEN
    exec_ratio = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
    
    if num_devices < 1 or num_devices > 50:
        print("❌ Number of devices must be between 1 and 50")
        sys.exit(1)
    
    print(f"""
🚀 Starting Device Simulator
============================
📱 Devices: {num_devices}
📡 Server: {server_url}
🔧 Exec ratio: {exec_ratio:.1%}
""")
    
    # Create device tasks
    tasks = []
    for i in range(num_devices):
        device_id = generate_device_id()
        exec_allowed = random.random() < exec_ratio
        
        task = asyncio.create_task(
            run_simulated_device(device_id, server_url, auth_token, exec_allowed)
        )
        tasks.append(task)
        
        # Stagger device connections
        await asyncio.sleep(0.5)
    
    print(f"✅ All {num_devices} devices started")
    print("Press Ctrl+C to stop all devices")
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all simulated devices...")
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to cleanup
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())