import webview
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
except ImportError:
    print("Error: Could not import 'app' from app.py.")
    print("Please make sure app.py is in the same directory.")
    exit()

def run_server():
    """Run the Dash app's server."""
    # Run on a high port to avoid conflicts
    # debug=False is crucial for running in a thread
    app.run(debug=False, port=8050) 

if __name__ == '__main__':
    # 1. Start the Dash server in a separate thread
    # daemon=True ensures the thread will close when the main window is closed
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    print("Starting standalone application window...")
    
    webview.create_window(
        "Global Flight Network Explorer",
        "http://127.0.0.1:8050/",
        width=1600,
        height=900,
        resizable=True,
        min_size=(1024, 768)
    )
    webview.start()
