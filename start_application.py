"""
start_application.py

Purpose:
--------
Startup script to verify dependencies and launch the API server.
This is the entry point for the user.
"""

import os
import sys
import subprocess
import time
import webbrowser

def check_dependencies():
    print("Checking dependencies...")
    try:
        import flask
        import flask_cors
        import yaml
        print("✅ Dependencies found.")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_server():
    print("🚀 Starting Drawdown Portfolio Optimizer...")
    print("---------------------------------------------")
    
    server_process = subprocess.Popen(
        [sys.executable, 'api_server.py'],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Wait for server to initialize
    time.sleep(2)
    
    url = "http://localhost:5000"
    print(f"\n✅ Application running at: {url}")
    print("Opening browser...")
    
    webbrowser.open(url)
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\nStopping application...")
        server_process.terminate()

if __name__ == "__main__":
    if check_dependencies():
        start_server()
