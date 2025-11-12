import fitz  # PyMuPDF
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self, preserve_layout: bool = True):
        """
        Initialize document parser using PyMuPDF.

        Args:
            preserve_layout: Whether to try preserving text layout
        """
        self.preserve_layout = preserve_layout
        logger.info("Document Parser initialized")

    def parse_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Parse PDF and extract text page by page.

        Returns:
            {
                'pages': List[Dict] with per-page content,
                'total_pages': int,
                'metadata': Dict with PDF metadata
            }
        """
        try:
            doc = fitz.open(pdf_path)
            pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extract text
                if self.preserve_layout:
                    # Try to preserve layout with blocks
                    text = page.get_text("text")
                else:
                    text = page.get_text()

                # Calculate confidence based on text extraction
                # If we got text, confidence is high; otherwise, low
                confidence = 0.95 if text.strip() else 0.0

                pages.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'confidence': confidence,
                    'char_count': len(text)
                })

            # Extract metadata
            metadata = doc.metadata

            doc.close()

            return {
                'pages': pages,
                'total_pages': len(pages),
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}")
            return {
                'pages': [],
                'total_pages': 0,
                'metadata': {},
                'error': str(e)
            }

    def extract_page(self, pdf_path: str, page_num: int) -> Optional[str]:
        """
        Extract text from a specific page (1-indexed).
        """
        try:
            doc = fitz.open(pdf_path)

            if page_num < 1 or page_num > len(doc):
                logger.warning(f"Page {page_num} out of range for {pdf_path}")
                return None

            page = doc[page_num - 1]
            text = page.get_text("text") if self.preserve_layout else page.get_text()

            doc.close()
            return text

        except Exception as e:
            logger.error(f"Error extracting page {page_num} from {pdf_path}: {e}")
            return None

    def check_if_text_extractable(self, pdf_path: str) -> bool:
        """
        Quick check to see if PDF has extractable text or is image-based.
        """
        try:
            doc = fitz.open(pdf_path)

            # Check first 3 pages or all pages if fewer
            pages_to_check = min(3, len(doc))

            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()

                # If we find any substantial text, it's extractable
                if len(text) > 50:
                    doc.close()
                    return True

            doc.close()
            return False

        except Exception as e:
            logger.error(f"Error checking PDF {pdf_path}: {e}")
            return False

    def get_page_images(self, pdf_path: str, output_dir: str, dpi: int = 300) -> List[str]:
        """
        Convert PDF pages to images for OCR processing.

        Returns list of image paths.
        """
        try:
            doc = fitz.open(pdf_path)
            image_paths = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Render page to image
                mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is default DPI
                pix = page.get_pixmap(matrix=mat)

                # Save image
                image_path = f"{output_dir}/page_{page_num + 1}.png"
                pix.save(image_path)
                image_paths.append(image_path)

            doc.close()
            return image_paths

        except Exception as e:
            logger.error(f"Error converting PDF to images {pdf_path}: {e}")
            return []
