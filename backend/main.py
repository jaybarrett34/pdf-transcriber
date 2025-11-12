from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import uuid
import logging
from pathlib import Path
import json
import asyncio

from processor import DocumentProcessor
from config_loader import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PDF Transcriber API", version="1.0.0")

# CORS middleware for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global config and processor
config = get_config()
processor = DocumentProcessor(config)

# Storage for active WebSocket connections
active_connections: dict[str, WebSocket] = {}

# Create necessary directories
os.makedirs(config.get('processing.upload_dir', 'backend/uploads'), exist_ok=True)
os.makedirs(config.get('processing.temp_dir', 'backend/temp'), exist_ok=True)
os.makedirs('backend/output', exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "PDF Transcriber API",
        "version": "1.0.0"
    }


@app.get("/config")
async def get_configuration():
    """Get current configuration."""
    return {
        "ocr_languages": config.get('ocr.languages'),
        "ollama_enabled": config.get('ollama.enabled'),
        "ollama_model": config.get('ollama.default_model'),
        "supported_formats": config.get('supported_formats')
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file for processing.
    Returns a file_id for tracking.
    """
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Save uploaded file
        file_ext = Path(file.filename).suffix
        upload_path = os.path.join(
            config.get('processing.upload_dir'),
            f"{file_id}{file_ext}"
        )

        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"File uploaded: {file.filename} -> {file_id}")

        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/process/{file_id}")
async def process_file(
    file_id: str,
    use_ollama_cleanup: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Process an uploaded file.
    This endpoint returns immediately and processing happens in the background.
    Use WebSocket to get real-time progress updates.
    """
    try:
        # Find the uploaded file
        upload_dir = config.get('processing.upload_dir')
        files = [f for f in os.listdir(upload_dir) if f.startswith(file_id)]

        if not files:
            return {
                "success": False,
                "error": "File not found"
            }

        file_path = os.path.join(upload_dir, files[0])

        # Start processing in background
        background_tasks.add_task(
            process_document_task,
            file_id,
            file_path,
            use_ollama_cleanup
        )

        return {
            "success": True,
            "file_id": file_id,
            "message": "Processing started. Connect to WebSocket for progress updates."
        }

    except Exception as e:
        logger.error(f"Error starting process: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def process_document_task(file_id: str, file_path: str, use_ollama_cleanup: bool):
    """
    Background task to process a document and send progress via WebSocket.
    """
    # Progress callback to send updates via WebSocket
    async def progress_callback(data):
        if file_id in active_connections:
            try:
                await active_connections[file_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending progress update: {e}")

    try:
        # Process the document
        result = await processor.process_document(
            file_path,
            output_format='markdown',
            use_ollama_cleanup=use_ollama_cleanup,
            progress_callback=progress_callback
        )

        # Save output to file
        output_filename = f"{file_id}.md"
        output_path = os.path.join('backend/output', output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['output'])

        # Send completion message
        if file_id in active_connections:
            await active_connections[file_id].send_json({
                'stage': 'complete',
                'progress': 100,
                'message': 'Processing complete!',
                'output_file': output_filename,
                'metadata': result['metadata']
            })

    except Exception as e:
        logger.error(f"Error in processing task: {e}")
        if file_id in active_connections:
            await active_connections[file_id].send_json({
                'stage': 'error',
                'progress': 0,
                'message': f'Error: {str(e)}'
            })


@app.websocket("/ws/{file_id}")
async def websocket_endpoint(websocket: WebSocket, file_id: str):
    """
    WebSocket endpoint for real-time progress updates.
    """
    await websocket.accept()
    active_connections[file_id] = websocket

    try:
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            logger.debug(f"Received from client {file_id}: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {file_id}")
        if file_id in active_connections:
            del active_connections[file_id]


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Download the processed markdown file.
    """
    output_filename = f"{file_id}.md"
    output_path = os.path.join('backend/output', output_filename)

    if not os.path.exists(output_path):
        return {
            "success": False,
            "error": "Output file not found"
        }

    return FileResponse(
        output_path,
        media_type='text/markdown',
        filename=output_filename
    )


@app.post("/process-batch")
async def process_batch(
    files: List[UploadFile] = File(...),
    use_ollama_cleanup: bool = False
):
    """
    Process multiple files in batch.
    Returns a batch_id for tracking.
    """
    try:
        batch_id = str(uuid.uuid4())
        file_ids = []

        # Upload all files first
        for file in files:
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix
            upload_path = os.path.join(
                config.get('processing.upload_dir'),
                f"{file_id}{file_ext}"
            )

            with open(upload_path, "wb") as f:
                content = await file.read()
                f.write(content)

            file_ids.append({
                'file_id': file_id,
                'filename': file.filename,
                'path': upload_path
            })

        logger.info(f"Batch upload complete: {batch_id} with {len(file_ids)} files")

        # Process all files
        # In production, you'd want to process these in a proper queue
        results = []
        for item in file_ids:
            result = await processor.process_document(
                item['path'],
                output_format='markdown',
                use_ollama_cleanup=use_ollama_cleanup
            )

            # Save output
            output_filename = f"{item['file_id']}.md"
            output_path = os.path.join('backend/output', output_filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['output'])

            results.append({
                'file_id': item['file_id'],
                'filename': item['filename'],
                'output_file': output_filename,
                'success': True
            })

        return {
            "success": True,
            "batch_id": batch_id,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn

    host = config.get('server.host', '127.0.0.1')
    port = config.get('server.port', 8000)

    logger.info(f"Starting PDF Transcriber API on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
