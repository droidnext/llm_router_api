import os
from dotenv import load_dotenv
import phoenix as px
import time

def start_phoenix():
    load_dotenv()

    # Set Phoenix server configuration using environment variables
    os.environ["PHOENIX_HOST"] = os.getenv("PHOENIX_HOST", "0.0.0.0")
    os.environ["PHOENIX_PORT"] = os.getenv("PHOENIX_PORT", "6006")

    # Start Phoenix
    px.launch_app()

    print("✅ Phoenix server is running... Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Server stopped.")

if __name__ == "__main__":
    start_phoenix()
