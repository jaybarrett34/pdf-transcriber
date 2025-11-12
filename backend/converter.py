from pptx import Presentation
from PIL import Image
import os
from pathlib import Path
from typing import List, Dict
import logging
import fitz  # PyMuPDF for PDF to image conversion

logger = logging.getLogger(__name__)

class DocumentConverter:
    def __init__(self, temp_dir: str = "backend/temp"):
        """
        Initialize document converter for various file formats.
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Document Converter initialized with temp dir: {temp_dir}")

    def identify_file_type(self, file_path: str) -> str:
        """
        Identify file type from extension.
        """
        ext = Path(file_path).suffix.lower()
        return ext.lstrip('.')

    def convert_to_images(self, file_path: str, file_type: str = None) -> List[str]:
        """
        Convert document to images based on file type.

        Returns list of image paths.
        """
        if file_type is None:
            file_type = self.identify_file_type(file_path)

        logger.info(f"Converting {file_type} file to images: {file_path}")

        if file_type == 'pdf':
            return self._convert_pdf_to_images(file_path)
        elif file_type in ['pptx', 'ppt']:
            return self._convert_pptx_to_images(file_path)
        elif file_type in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
            return self._handle_image(file_path)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return []

    def _convert_pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[str]:
        """
        Convert PDF pages to images.
        """
        try:
            doc = fitz.open(pdf_path)
            image_paths = []

            # Create subdirectory for this PDF
            pdf_name = Path(pdf_path).stem
            output_dir = os.path.join(self.temp_dir, pdf_name)
            os.makedirs(output_dir, exist_ok=True)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Render page to image at high DPI for better OCR
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)

                # Save as PNG
                image_path = os.path.join(output_dir, f"page_{page_num + 1:04d}.png")
                pix.save(image_path)
                image_paths.append(image_path)

                logger.debug(f"Converted page {page_num + 1} to {image_path}")

            doc.close()
            logger.info(f"Converted {len(image_paths)} pages from PDF")
            return image_paths

        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []

    def _convert_pptx_to_images(self, pptx_path: str) -> List[str]:
        """
        Convert PPTX slides to images.

        Note: This extracts text and creates images of slides.
        For better results, we render slides to images.
        """
        try:
            prs = Presentation(pptx_path)
            image_paths = []

            # Create subdirectory for this PPTX
            pptx_name = Path(pptx_path).stem
            output_dir = os.path.join(self.temp_dir, pptx_name)
            os.makedirs(output_dir, exist_ok=True)

            # PPTX to image conversion requires LibreOffice or similar
            # For now, we'll extract images and text from slides
            # In production, you might want to use libreoffice --headless --convert-to pdf

            # Alternative approach: Extract embedded images and text
            for slide_num, slide in enumerate(prs.slides):
                # Create a simple text representation for now
                # In a full implementation, you'd use LibreOffice to render slides

                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        slide_text.append(shape.text)

                # Save as text file temporarily
                # This is a fallback; ideally use LibreOffice rendering
                text_path = os.path.join(output_dir, f"slide_{slide_num + 1:04d}.txt")
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(slide_text))

                # For images in the slide
                for shape in slide.shapes:
                    if hasattr(shape, "image"):
                        image = shape.image
                        image_bytes = image.blob
                        image_path = os.path.join(output_dir, f"slide_{slide_num + 1:04d}_img.png")

                        with open(image_path, 'wb') as f:
                            f.write(image_bytes)

                        image_paths.append(image_path)

            logger.info(f"Extracted content from {len(prs.slides)} slides")

            # Return text files as "images" for processing
            # In full implementation, return rendered slide images
            text_files = [os.path.join(output_dir, f"slide_{i + 1:04d}.txt")
                          for i in range(len(prs.slides))]

            return text_files if not image_paths else image_paths

        except Exception as e:
            logger.error(f"Error converting PPTX to images: {e}")
            return []

    def _handle_image(self, image_path: str) -> List[str]:
        """
        Handle single image files. Optionally preprocess.
        """
        try:
            # Optionally preprocess image (resize, enhance contrast, etc.)
            img = Image.open(image_path)

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save preprocessed image
            output_path = os.path.join(self.temp_dir, Path(image_path).name)
            img.save(output_path)

            logger.info(f"Processed image: {image_path}")
            return [output_path]

        except Exception as e:
            logger.error(f"Error handling image {image_path}: {e}")
            return []

    def cleanup_temp_files(self, file_paths: List[str]):
        """
        Clean up temporary files after processing.
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {file_path}: {e}")
