# ASA Trading - Installation Guide

## Compressed Package Information

- **Package Name:** ASA_Trading_Portable.zip
- **Compressed Size:** ~3.3 MB
- **Original Size:** ~808 MB (with venv)
- **Compression Ratio:** ~99.6% reduction

## System Requirements

- Python 3.10 or higher
- 4GB RAM minimum
- 500MB free disk space
- Windows, macOS, or Linux

## Installation Steps

### 1. Extract the Package

Extract `ASA_Trading_Portable.zip` to your desired location:
- Windows: Right-click → Extract All
- macOS: Double-click to extract
- Linux: `unzip ASA_Trading_Portable.zip`

### 2. Create Virtual Environment (Recommended)

```bash
# Navigate to the extracted directory
cd ASA_Trading_Portable

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Quick Start (Without Virtual Environment)

If you prefer not to use a virtual environment:

```bash
# Navigate to the extracted directory
cd ASA_Trading_Portable

# Install dependencies directly
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution:** Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Streamlit not found
**Solution:** Install Streamlit:
```bash
pip install streamlit
```

### Issue: Port 8501 already in use
**Solution:** Run on a different port:
```bash
streamlit run app.py --server.port 8502
```

## Package Contents

The compressed package includes:
- `app.py` - Main application file
- `requirements.txt` - Python dependencies
- `indicators/` - Technical indicator modules
- `market_data/` - Market data and portfolio modules
- `ai/` - AI prediction and analysis modules
- `patterns/` - Candlestick pattern detection
- `icon.png` - Application icon
- `runtime.txt` - Python version specification
- `README.md` - Project documentation
- `DEPLOYMENT.md` - Deployment guide

## Excluded from Package

The following are excluded to reduce size:
- `venv/` - Virtual environment (recreated on installation)
- `__pycache__/` - Python cache files
- `.git/` - Git repository
- `*.pyc` - Compiled Python files
- `.pytest_cache/` - Test cache
- `dist/`, `build/` - Build artifacts
- `*.egg-info/` - Package metadata

## Support

For issues or questions:
- Check the README.md for detailed documentation
- Review DEPLOYMENT.md for deployment options
- Ensure Python 3.10+ is installed
- Verify all dependencies are installed correctly

## Notes

- The compressed package is portable and can be installed on any compatible system
- Dependencies will be downloaded during installation (~200-300 MB)
- First-time installation may take 5-10 minutes depending on internet speed
- The application runs locally and does not require cloud services
