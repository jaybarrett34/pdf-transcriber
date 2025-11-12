from typing import Dict, List, Optional, Callable
import os
import logging
from pathlib import Path

from ocr_engine import OCREngine
from parser import DocumentParser
from converter import DocumentConverter
from reconciler import TextReconciler
from formatter import MarkdownFormatter
from config_loader import get_config

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, config=None):
        """
        Main document processing pipeline.
        """
        self.config = config or get_config()

        # Initialize components
        logger.info("Initializing DocumentProcessor components...")

        self.converter = DocumentConverter(
            temp_dir=self.config.get('processing.temp_dir', 'backend/temp')
        )

        self.parser = DocumentParser(
            preserve_layout=self.config.get('parser.preserve_layout', True)
        )

        self.ocr = OCREngine(
            languages=self.config.get('ocr.languages', ['en']),
            use_gpu=self.config.get('ocr.use_gpu', False)
        )

        self.reconciler = TextReconciler(
            similarity_threshold=self.config.get('reconciliation.similarity_threshold', 0.85),
            conflict_threshold=self.config.get('reconciliation.conflict_threshold', 0.4),
            use_semantic=self.config.get('reconciliation.use_semantic_check', True),
            semantic_model=self.config.get('reconciliation.semantic_model',
                                          'sentence-transformers/all-MiniLM-L6-v2')
        )

        self.formatter = MarkdownFormatter(
            ollama_enabled=self.config.get('ollama.enabled', True),
            base_url=self.config.get('ollama.base_url', 'http://localhost:11434'),
            model=self.config.get('ollama.cleanup_model', 'llama2:7b'),
            temperature=self.config.get('ollama.temperature', 0.3)
        )

        logger.info("DocumentProcessor initialized successfully")

    async def process_document(
        self,
        file_path: str,
        output_format: str = 'markdown',
        use_ollama_cleanup: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, any]:
        """
        Process a document through the full pipeline.

        Args:
            file_path: Path to the document
            output_format: Output format (currently only 'markdown' supported)
            use_ollama_cleanup: Whether to use Ollama for markdown cleanup
            progress_callback: Optional callback for progress updates

        Returns:
            {
                'filename': str,
                'output': str (formatted text),
                'metadata': Dict,
                'pages': List[Dict] with per-page details
            }
        """
        try:
            filename = Path(file_path).name
            logger.info(f"Processing document: {filename}")

            if progress_callback:
                await progress_callback({'stage': 'start', 'progress': 0, 'message': 'Starting processing...'})

            # Step 1: Convert to images
            if progress_callback:
                await progress_callback({'stage': 'convert', 'progress': 10, 'message': 'Converting document...'})

            file_type = self.converter.identify_file_type(file_path)
            image_paths = self.converter.convert_to_images(file_path, file_type)

            if not image_paths:
                raise ValueError(f"Failed to convert document to images: {filename}")

            total_pages = len(image_paths)
            logger.info(f"Converted to {total_pages} images")

            # Step 2: Extract text with parser (for PDFs)
            parsed_results = []
            if file_type == 'pdf':
                if progress_callback:
                    await progress_callback({'stage': 'parse', 'progress': 20, 'message': 'Parsing document text...'})

                parsed_data = self.parser.parse_pdf(file_path)
                parsed_results = parsed_data.get('pages', [])

            # Ensure parsed_results has entries for all pages
            while len(parsed_results) < total_pages:
                parsed_results.append({'text': '', 'confidence': 0.0, 'page_number': len(parsed_results) + 1})

            # Step 3: OCR extraction
            if progress_callback:
                await progress_callback({'stage': 'ocr', 'progress': 40, 'message': 'Running OCR...'})

            ocr_results = []
            for i, img_path in enumerate(image_paths):
                logger.info(f"OCR processing page {i+1}/{total_pages}")

                result = self.ocr.process_image(img_path)
                result['page_number'] = i + 1
                ocr_results.append(result)

                if progress_callback:
                    progress = 40 + int((i + 1) / total_pages * 30)
                    await progress_callback({
                        'stage': 'ocr',
                        'progress': progress,
                        'message': f'OCR: Page {i+1}/{total_pages}'
                    })

            # Step 4: Reconciliation
            if progress_callback:
                await progress_callback({'stage': 'reconcile', 'progress': 70, 'message': 'Reconciling text...'})

            reconciled_results = self.reconciler.batch_reconcile(ocr_results, parsed_results)
            logger.info("Text reconciliation completed")

            # Step 5: Format output
            if progress_callback:
                await progress_callback({'stage': 'format', 'progress': 85, 'message': 'Formatting output...'})

            if output_format == 'markdown':
                if use_ollama_cleanup:
                    output = self.formatter.format_with_cleanup(
                        reconciled_results,
                        filename,
                        include_metadata=self.config.get('output.include_metadata', True)
                    )
                else:
                    output = self.formatter.format_basic(
                        reconciled_results,
                        filename,
                        include_metadata=self.config.get('output.include_metadata', True),
                        include_confidence=self.config.get('output.include_confidence_scores', False)
                    )
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

            # Step 6: Cleanup temp files
            if progress_callback:
                await progress_callback({'stage': 'cleanup', 'progress': 95, 'message': 'Cleaning up...'})

            self.converter.cleanup_temp_files(image_paths)

            if progress_callback:
                await progress_callback({'stage': 'complete', 'progress': 100, 'message': 'Processing complete!'})

            logger.info(f"Document processing completed: {filename}")

            return {
                'filename': filename,
                'output': output,
                'metadata': {
                    'original_filename': filename,
                    'total_pages': total_pages,
                    'file_type': file_type
                },
                'pages': reconciled_results
            }

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            if progress_callback:
                await progress_callback({
                    'stage': 'error',
                    'progress': 0,
                    'message': f'Error: {str(e)}'
                })
            raise

    async def process_batch(
        self,
        file_paths: List[str],
        output_format: str = 'markdown',
        use_ollama_cleanup: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, any]]:
        """
        Process multiple documents.

        Returns list of processing results.
        """
        results = []

        for i, file_path in enumerate(file_paths):
            logger.info(f"Processing file {i+1}/{len(file_paths)}: {file_path}")

            try:
                # Create a scoped progress callback for this file
                if progress_callback:
                    async def file_progress(data):
                        data['file_index'] = i
                        data['total_files'] = len(file_paths)
                        await progress_callback(data)

                    result = await self.process_document(
                        file_path,
                        output_format,
                        use_ollama_cleanup,
                        file_progress
                    )
                else:
                    result = await self.process_document(
                        file_path,
                        output_format,
                        use_ollama_cleanup
                    )

                results.append(result)

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results.append({
                    'filename': Path(file_path).name,
                    'error': str(e),
                    'success': False
                })

        return results
