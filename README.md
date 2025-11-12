# PDF Transcriber

A self-hosted, AI-powered PDF OCR and transcription application with a beautiful macOS-style interface. Transform PDFs, images, and presentations into clean, accurate markdown with advanced OCR and intelligent text reconciliation.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Node](https://img.shields.io/badge/node-16+-green.svg)

## Features

### 🎯 Core Capabilities
- **Multi-Format Support**: PDF, PNG, JPG, JPEG, PPTX, TIFF, BMP
- **Dual Extraction Pipeline**: Combines OCR and native text parsing for maximum accuracy
- **Intelligent Reconciliation**: Uses confidence scoring and semantic analysis to choose the best extraction
- **Multi-Language Support**: English, Spanish, Chinese, code, and Old English formatting
- **AI-Powered Cleanup**: Optional Ollama integration for markdown beautification

### 🧠 Advanced Processing
- **PaddleOCR Engine**: 80+ languages, high accuracy, confidence scores
- **Smart Confidence Scoring**: Lightweight NLP for basic comparison, transformers for semantic analysis
- **Conflict Resolution**: Automatic reconciliation when OCR and parsing disagree
- **Layout Preservation**: Maintains document structure and formatting

### 💻 Modern Interface
- **Apple-Style UI**: Clean, modern design inspired by macOS
- **Drag & Drop**: Easy file upload with visual feedback
- **Bulk Processing**: Handle multiple files simultaneously
- **Real-Time Progress**: WebSocket-powered progress tracking
- **Chromium-Style Downloads**: Save directly to Downloads folder

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Electron Frontend (React)              │
│  • Drag & Drop Upload                           │
│  • Progress Tracking                            │
│  • Settings Management                          │
└─────────────────┬───────────────────────────────┘
                  │ WebSocket + REST API
┌─────────────────▼───────────────────────────────┐
│          FastAPI Backend (Python)                │
│  ┌───────────────────────────────────────────┐  │
│  │     Document Processor Pipeline           │  │
│  ├───────────────────────────────────────────┤  │
│  │ 1. Converter (PDF/PPTX → Images)         │  │
│  │ 2. OCR Engine (PaddleOCR)                │  │
│  │ 3. Parser (PyMuPDF text extraction)      │  │
│  │ 4. Reconciler (Confidence + Semantic)    │  │
│  │ 5. Formatter (Markdown + Ollama)         │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- **Python 3.8+**
- **Node.js 16+** and npm
- **Ollama** (optional, for markdown cleanup)

### Quick Start

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd pdf-transcriber
```

2. **Run setup script**
```bash
chmod +x setup.sh
./setup.sh
```

3. **Start the application**
```bash
chmod +x start.sh
./start.sh
```

Or manually:

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python backend/main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run electron:dev
```

### Optional: Install Ollama

For AI-powered markdown cleanup:

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai

# Pull a model
ollama pull llama2:7b
# or
ollama pull mistral:7b
```

## Configuration

Edit `config/default_config.yaml` to customize:

```yaml
# OCR settings
ocr:
  languages: ["en", "spanish", "chinese_cht", "ch"]
  confidence_threshold: 0.6

# Reconciliation thresholds
reconciliation:
  similarity_threshold: 0.85  # Prefer parsed if above
  conflict_threshold: 0.4     # Heavy reconciliation if below

# Ollama settings
ollama:
  enabled: true
  default_model: "llama2:7b"
  temperature: 0.3

# Output settings
output:
  default_format: "markdown"
  include_metadata: true
```

## Usage

### Basic Workflow

1. **Upload Files**
   - Drag and drop files into the upload area
   - Or click "Browse Files" / "Select Files"
   - Supports bulk upload

2. **Configure Options**
   - Toggle "Use Ollama for Markdown Cleanup" if desired
   - View settings in the Settings tab

3. **Process**
   - Click "Process N Files"
   - Watch real-time progress for each file

4. **Download**
   - Click "Download" on completed files
   - Files saved to your Downloads folder

### API Usage

The backend can also be used programmatically:

```python
from processor import DocumentProcessor

processor = DocumentProcessor()

result = await processor.process_document(
    file_path="path/to/document.pdf",
    output_format="markdown",
    use_ollama_cleanup=True
)

print(result['output'])
```

### REST API Endpoints

- `GET /` - Health check
- `GET /config` - Get configuration
- `POST /upload` - Upload file
- `POST /process/{file_id}` - Start processing
- `WS /ws/{file_id}` - WebSocket for progress
- `GET /download/{file_id}` - Download result
- `POST /process-batch` - Batch processing

## Processing Pipeline

### 1. Document Conversion
- PDFs → High-resolution images (300 DPI)
- PPTX → Slide images
- Images → Preprocessed for OCR

### 2. Dual Extraction
- **Path A**: OCR with PaddleOCR
  - Multi-language support
  - Per-character confidence scores
  - Layout-aware extraction

- **Path B**: Text parsing with PyMuPDF
  - Fast, accurate for text-based PDFs
  - Preserves layout
  - High confidence for extractable text

### 3. Intelligent Reconciliation

```
High Similarity (>85%) → Use Parsed Text (cleaner)
Medium Similarity → Choose based on confidence
Low Similarity (<40%) → Deep analysis:
  ├─ Semantic similarity (sentence-transformers)
  ├─ Confidence scoring
  └─ Optional: Ollama for context-aware decision
```

### 4. Output Formatting
- Generate markdown with page numbers
- Include metadata (filename, pages, file type)
- Optional: AI cleanup with Ollama for polished output

## File Support

| Format | Method | Notes |
|--------|--------|-------|
| PDF | OCR + Parse | Best quality |
| PNG, JPG | OCR | High accuracy |
| PPTX | OCR | Slide-by-slide |
| TIFF, BMP | OCR | Converted to PNG first |

## Development

### Project Structure

```
pdf-transcriber/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── processor.py         # Main pipeline
│   ├── ocr_engine.py        # PaddleOCR wrapper
│   ├── parser.py            # PyMuPDF parser
│   ├── converter.py         # Format converter
│   ├── reconciler.py        # Text reconciliation
│   ├── formatter.py         # Markdown formatter
│   ├── config_loader.py     # Config management
│   └── requirements.txt     # Python deps
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   └── components/
│   │       ├── FileUploader.jsx
│   │       ├── ProcessingQueue.jsx
│   │       ├── ProgressBar.jsx
│   │       └── Settings.jsx
│   ├── electron.js          # Electron main
│   ├── preload.js          # IPC bridge
│   └── package.json
├── config/
│   └── default_config.yaml  # Configuration
└── setup.sh                # Setup script
```

### Running Tests

```bash
# Backend tests (if implemented)
pytest backend/tests/

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
cd frontend
npm run electron:build
```

Builds will be in `frontend/dist-electron/`:
- macOS: `.dmg` and `.zip`
- Windows: `.exe`
- Linux: `.AppImage` and `.deb`

## Performance

### Typical Processing Times (M4 Pro)

| Document | Pages | Time |
|----------|-------|------|
| Text PDF | 10 | ~15s |
| Scanned PDF | 10 | ~45s |
| Mixed PDF | 50 | ~3m |
| PPTX | 30 slides | ~2m |

*Without Ollama cleanup. Add 30-60s for AI cleanup on full documents.*

### Optimization Tips

1. **GPU Acceleration**: Set `ocr.use_gpu: true` in config (requires CUDA)
2. **Disable Ollama**: Skip cleanup for faster processing
3. **Adjust DPI**: Lower DPI in converter for faster but less accurate OCR
4. **Batch Processing**: Process multiple files simultaneously

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
pip install -r backend/requirements.txt

# Check port availability
lsof -i :8000
```

### OCR not working
- Verify PaddleOCR installation: `pip list | grep paddle`
- Check language packs: some languages require additional downloads
- Increase timeout in config if processing large images

### Ollama not connecting
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Pull a model if needed
ollama pull llama2:7b
```

### Electron app won't start
```bash
# Reinstall Node modules
cd frontend
rm -rf node_modules
npm install

# Check for port conflicts
lsof -i :5173
```

## Roadmap

- [ ] Batch export options (ZIP download)
- [ ] Custom output templates
- [ ] OCR quality assessment
- [ ] Support for more languages
- [ ] Document comparison mode
- [ ] Cloud storage integration
- [ ] Docker containerization
- [ ] REST API authentication
- [ ] Job queue with Redis
- [ ] Export to DOCX, HTML

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **PaddleOCR** - Excellent OCR engine
- **PyMuPDF** - Fast PDF processing
- **Ollama** - Local AI models
- **FastAPI** - Modern Python web framework
- **Electron** - Cross-platform desktop apps
- **React** - UI framework
- **TailwindCSS** - Utility-first CSS

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Read the docs in `config/default_config.yaml`

---

Built with ❤️ for efficient document processing
