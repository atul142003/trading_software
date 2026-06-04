# ASA Trading - Executable Build Guide

## Overview

This guide explains how to build an executable version of the ASA Trading application that can be distributed and run on any desktop device without requiring Python installation.

## Prerequisites

- Python 3.10 or higher installed
- All dependencies installed (run `pip install -r requirements.txt`)
- PyInstaller installed (included in requirements.txt)

## Building the Executable

### Windows

1. Open Command Prompt or PowerShell in the project directory
2. Run the build script:
   ```bash
   build_executable.bat
   ```
   Or manually:
   ```bash
   pyinstaller app.spec
   ```

### Linux/macOS

1. Open Terminal in the project directory
2. Make the build script executable:
   ```bash
   chmod +x build_executable.sh
   ```
3. Run the build script:
   ```bash
   ./build_executable.sh
   ```
   Or manually:
   ```bash
   pyinstaller app.spec
   ```

## Output

After building, the executable will be located in the `dist` folder:
- **Windows:** `dist/ASA_Trading.exe`
- **Linux/macOS:** `dist/ASA_Trading`

## Distribution

### For Distribution

1. Navigate to the `dist` folder
2. The executable file is standalone and can be distributed
3. Users can simply double-click/run the executable to launch the application

### Executable Size

The executable will be approximately 150-200 MB due to bundled Python interpreter and all dependencies.

## Running the Executable

### Windows
- Double-click `ASA_Trading.exe`
- Or run from Command Prompt: `ASA_Trading.exe`

### Linux/macOS
- Run from Terminal: `./ASA_Trading`
- Or make executable: `chmod +x ASA_Trading` then double-click

## What Happens When Running

1. The executable launches
2. Streamlit server starts automatically
3. Default browser opens to `http://localhost:8501`
4. Application is ready to use

## Important Notes

- **First launch may be slow** (10-30 seconds) as the application initializes
- **Antivirus warnings** may appear due to unsigned executable - this is normal for PyInstaller executables
- **Firewall prompts** may appear when the application tries to open a browser
- **No Python required** - the executable includes everything needed
- **Internet connection required** for fetching market data

## Troubleshooting

### Executable won't run
- Ensure you have proper permissions
- On Linux/macOS: `chmod +x ASA_Trading`
- Check antivirus software isn't blocking it

### Application doesn't open in browser
- Manually open browser to `http://localhost:8501`
- Check if port 8501 is already in use

### Missing dependencies errors
- Rebuild the executable after updating requirements.txt
- Ensure all dependencies are installed before building

### Large file size
- This is normal - PyInstaller bundles the entire Python runtime
- Cannot be significantly reduced without losing functionality

## Building for Different Platforms

PyInstaller creates executables for the platform it's run on:
- Build on Windows for Windows executables
- Build on Linux for Linux executables
- Build on macOS for macOS executables

To create executables for multiple platforms, you need to build on each platform separately.

## Advanced Options

### Customizing the Build

Edit `app.spec` to customize:
- Include additional data files
- Add more hidden imports
- Change executable name
- Add icon (already configured)

### One-File Mode

The current spec uses one-file mode (everything in single executable). For one-directory mode (faster startup), modify the spec file.

## Support

For issues with the executable:
1. Check that all dependencies are installed
2. Rebuild the executable
3. Verify Python version compatibility
4. Check the PyInstaller documentation: https://pyinstaller.org

## License

The executable includes all open-source dependencies used in the project. Ensure compliance with their licenses when distributing.
