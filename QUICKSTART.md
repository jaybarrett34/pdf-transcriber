# Quick Start Guide

Get PDF Transcriber running in 5 minutes!

## Prerequisites Check

Before starting, make sure you have:

- ✅ Python 3.8 or higher: `python3 --version`
- ✅ Node.js 16 or higher: `node --version`
- ✅ npm: `npm --version`
- ⚠️ Ollama (optional): `ollama --version`

## Installation

### Step 1: Setup
```bash
./setup.sh
```

This will:
- Create Python virtual environment
- Install all Python dependencies
- Install Node.js dependencies
- Create necessary directories

**Expected time:** 5-10 minutes (depending on internet speed)

### Step 2: Start the App
```bash
./start.sh
```

Or manually in two terminals:

**Terminal 1:**
```bash
source venv/bin/activate
python backend/main.py
```

**Terminal 2:**
```bash
cd frontend
npm run electron:dev
```

## First Use

1. **Wait for the app to open** (takes 10-20 seconds on first run)

2. **Check Settings tab**
   - Verify backend is online (green dot)
   - Check OCR languages are loaded
   - Optionally configure Ollama

3. **Upload a test file**
   - Switch to Upload tab
   - Drag & drop a PDF or click Browse
   - Click "Process 1 File"

4. **Download result**
   - Wait for processing to complete
   - Click "Download" button
   - Find file in Downloads folder

## Common Issues

### "Backend Offline"
- Make sure backend is running: `python backend/main.py`
- Check port 8000 isn't in use: `lsof -i :8000`

### "Module not found" errors
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r backend/requirements.txt`

### Electron won't start
- Reinstall: `cd frontend && npm install`
- Check port 5173: `lsof -i :5173`

### Slow processing
- First run downloads ML models (1-2 GB)
- Subsequent runs are much faster
- Disable Ollama cleanup for speed

## Optional: Ollama Setup

For AI-powered markdown cleanup:

```bash
# Install Ollama
brew install ollama  # macOS
# or visit https://ollama.ai

# Pull a model
ollama pull llama2:7b

# Verify
ollama list
```

## Tips

- **Start small**: Test with 1-2 page PDFs first
- **Monitor logs**: Watch terminal output for errors
- **Check config**: Edit `config/default_config.yaml` for customization
- **Bulk processing**: Upload multiple files at once

## Next Steps

- Read full [README.md](README.md) for advanced features
- Configure settings in `config/default_config.yaml`
- Try different file formats (PPTX, images)
- Enable Ollama for better markdown formatting

## Need Help?

1. Check [README.md](README.md) troubleshooting section
2. Review logs in terminal output
3. Open an issue on GitHub

Happy transcribing! 🚀
