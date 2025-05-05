#!/usr/bin/env python3
import os
import argparse
import subprocess
from pathlib import Path

def create_data_directory():
    """Create data directory for Phoenix if it doesn't exist"""
    data_dir = Path.home() / ".phoenix" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def start_phoenix_server(host: str = "0.0.0.0", port: int = 6006):
    """Start the Phoenix server with the specified configuration"""
    data_dir = create_data_directory()
    
    # Set environment variables if needed
    os.environ["PHOENIX_DATA_PATH"] = str(data_dir)
    
    print(f"Starting Phoenix server on {host}:{port}")
    print(f"Data directory: {data_dir}")
    
    try:
        subprocess.run([
            "phoenix",
            "serve",
            "--host", host,
            "--port", str(port)
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Phoenix server: {e}")
        raise
    except KeyboardInterrupt:
        print("\nShutting down Phoenix server...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Phoenix server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=6006, help="Port to listen on")
    
    args = parser.parse_args()
    start_phoenix_server(args.host, args.port) 