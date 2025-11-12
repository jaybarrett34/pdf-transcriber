from paddleocr import PaddleOCR
from typing import List, Dict, Tuple
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class OCREngine:
    def __init__(self, languages: List[str] = None, use_gpu: bool = False):
        """
        Initialize PaddleOCR engine with support for multiple languages.

        Args:
            languages: List of language codes (en, ch, spanish, etc.)
            use_gpu: Whether to use GPU acceleration
        """
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu

        # Initialize PaddleOCR with multilingual support
        # For multilingual, we'll use 'en' as base and it handles most languages
        lang = "en" if "en" in self.languages else self.languages[0]

        self.ocr = PaddleOCR(
            use_angle_cls=True,  # Enable angle classification for rotated text
            lang=lang,
            use_gpu=use_gpu,
            show_log=False
        )

        logger.info(f"OCR Engine initialized with languages: {self.languages}, GPU: {use_gpu}")

    def process_image(self, image_path: str) -> Dict[str, any]:
        """
        Process a single image and extract text with confidence scores.

        Returns:
            {
                'text': str,
                'confidence': float,
                'lines': List[Dict] with per-line details
            }
        """
        try:
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'lines': []
                }

            lines = []
            all_text = []
            confidences = []

            for line in result[0]:
                # line[0] contains bbox coordinates
                # line[1] contains (text, confidence)
                text, confidence = line[1]

                lines.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': line[0]
                })

                all_text.append(text)
                confidences.append(confidence)

            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                'text': '\n'.join(all_text),
                'confidence': avg_confidence,
                'lines': lines
            }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'lines': [],
                'error': str(e)
            }

    def process_multiple_images(self, image_paths: List[str]) -> List[Dict[str, any]]:
        """
        Process multiple images (e.g., pages of a PDF converted to images).

        Returns list of results, one per image.
        """
        results = []

        for i, image_path in enumerate(image_paths):
            logger.info(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
            result = self.process_image(image_path)
            result['page_number'] = i + 1
            results.append(result)

        return results

    def get_text_with_layout(self, image_path: str) -> str:
        """
        Extract text while trying to preserve layout based on bounding boxes.
        """
        result = self.process_image(image_path)

        if not result['lines']:
            return result['text']

        # Sort lines by vertical position (top to bottom)
        sorted_lines = sorted(result['lines'], key=lambda x: x['bbox'][0][1])

        # Group lines that are approximately on the same horizontal level
        grouped_lines = []
        current_group = []
        last_y = None
        y_threshold = 10  # pixels

        for line in sorted_lines:
            y_pos = line['bbox'][0][1]

            if last_y is None or abs(y_pos - last_y) <= y_threshold:
                current_group.append(line)
            else:
                if current_group:
                    # Sort current group by x position (left to right)
                    current_group.sort(key=lambda x: x['bbox'][0][0])
                    grouped_lines.append(current_group)
                current_group = [line]

            last_y = y_pos

        # Don't forget the last group
        if current_group:
            current_group.sort(key=lambda x: x['bbox'][0][0])
            grouped_lines.append(current_group)

        # Reconstruct text with proper spacing
        reconstructed = []
        for group in grouped_lines:
            line_text = ' '.join([item['text'] for item in group])
            reconstructed.append(line_text)

        return '\n'.join(reconstructed)
