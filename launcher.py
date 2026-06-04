import subprocess
import sys
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser after a delay to ensure Streamlit server is ready."""
    time.sleep(3)
    webbrowser.open('http://localhost:8501')

if __name__ == '__main__':
    print("Starting ASA Trading...")
    print("Please wait while the application initializes...")
    print("The browser will open automatically in a few seconds.")
    print("If it doesn't, open http://localhost:8501 manually.")
    print()
    print("Press Ctrl+C to stop the application.")
    print()
    
    # Start browser in a separate thread
    Timer(2, open_browser).start()
    
    # Run Streamlit
    try:
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")
