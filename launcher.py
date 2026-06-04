import subprocess
import sys
import webbrowser
import time
import threading
import os

browser_opened = False

def open_browser():
    """Open browser once to ensure Streamlit server is ready."""
    global browser_opened
    if not browser_opened:
        time.sleep(5)
        webbrowser.open('http://localhost:8501')
        browser_opened = True

if __name__ == '__main__':
    print("Starting ASA Trading...")
    print("Please wait while the application initializes...")
    print("The browser will open automatically in a few seconds.")
    print("If it doesn't, open http://localhost:8501 manually.")
    print()
    print("Press Ctrl+C to stop the application.")
    print()
    
    # Start browser in a separate thread (only once)
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Run Streamlit
    try:
        # Check if running from PyInstaller executable
        if getattr(sys, 'frozen', False):
            # Running from PyInstaller executable
            # Use the bundled Python to run streamlit
            subprocess.run(['streamlit', 'run', 'app.py'], shell=True)
        else:
            # Running normally
            subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")
