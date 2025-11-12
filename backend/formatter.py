import ollama
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class MarkdownFormatter:
    def __init__(
        self,
        ollama_enabled: bool = True,
        base_url: str = "http://localhost:11434",
        model: str = "llama2:7b",
        temperature: float = 0.3
    ):
        """
        Initialize Markdown formatter with optional Ollama integration.

        Args:
            ollama_enabled: Whether to use Ollama for cleanup
            base_url: Ollama server URL
            model: Ollama model to use
            temperature: Model temperature for generation
        """
        self.ollama_enabled = ollama_enabled
        self.base_url = base_url
        self.model = model
        self.temperature = temperature

        if ollama_enabled:
            self._check_ollama_connection()

    def _check_ollama_connection(self):
        """Check if Ollama is available."""
        try:
            # Try to list models to verify connection
            models = ollama.list()
            logger.info(f"Connected to Ollama. Available models: {len(models.get('models', []))}")
        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}. Cleanup will be disabled.")
            self.ollama_enabled = False

    def format_basic(
        self,
        pages: List[Dict],
        filename: str,
        include_metadata: bool = True,
        include_confidence: bool = False
    ) -> str:
        """
        Format extracted text as basic markdown without Ollama cleanup.

        Args:
            pages: List of page dictionaries with 'text', 'page_number', etc.
            filename: Original filename
            include_metadata: Whether to include metadata header
            include_confidence: Whether to include confidence scores

        Returns:
            Formatted markdown string
        """
        lines = []

        # Add metadata header
        if include_metadata:
            lines.append(f"# {filename}\n")
            lines.append(f"**Total Pages:** {len(pages)}\n")
            lines.append("---\n")

        # Add content page by page
        for page in pages:
            page_num = page.get('page_number', 0)
            text = page.get('text', '').strip()
            source = page.get('source', 'unknown')
            confidence = page.get('confidence', 0.0)

            if not text:
                continue

            # Page header
            lines.append(f"\n## Page {page_num}\n")

            if include_confidence:
                lines.append(f"*Source: {source} | Confidence: {confidence:.2%}*\n")

            # Content
            lines.append(text)
            lines.append("\n---\n")

        return '\n'.join(lines)

    def format_with_cleanup(
        self,
        pages: List[Dict],
        filename: str,
        include_metadata: bool = True
    ) -> str:
        """
        Format and cleanup text using Ollama for better markdown.

        This processes the entire document through Ollama to improve
        formatting, fix OCR errors, and create cleaner markdown.
        """
        if not self.ollama_enabled:
            logger.warning("Ollama not enabled, falling back to basic formatting")
            return self.format_basic(pages, filename, include_metadata)

        # First create basic markdown
        basic_md = self.format_basic(pages, filename, include_metadata, include_confidence=False)

        # Prepare prompt for Ollama
        prompt = self._create_cleanup_prompt(basic_md, filename)

        try:
            logger.info(f"Cleaning up markdown with Ollama model: {self.model}")

            # Call Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': self.temperature,
                }
            )

            cleaned_text = response['response']
            logger.info("Markdown cleanup completed successfully")

            return cleaned_text

        except Exception as e:
            logger.error(f"Error during Ollama cleanup: {e}")
            logger.info("Falling back to basic formatting")
            return basic_md

    def _create_cleanup_prompt(self, raw_markdown: str, filename: str) -> str:
        """
        Create prompt for Ollama to cleanup and improve markdown.
        """
        prompt = f"""You are a document formatting assistant. Your task is to clean up and improve the following markdown document that was extracted from a PDF using OCR and text parsing.

Original filename: {filename}

Instructions:
1. Fix any obvious OCR errors (common character substitutions like 'l' for '1', 'O' for '0')
2. Improve markdown formatting (proper headers, lists, code blocks, etc.)
3. Preserve the original content and meaning - DO NOT add or remove information
4. Maintain page numbers and structure
5. Fix broken words or sentences from OCR artifacts
6. Ensure proper spacing and line breaks
7. If you see code, format it with proper code blocks and syntax
8. Keep the document structure (pages, sections) intact

Here is the raw markdown to clean up:

{raw_markdown}

Please provide the cleaned up markdown document:"""

        return prompt

    def format_pages_individually(
        self,
        pages: List[Dict],
        filename: str,
        use_ollama: bool = False
    ) -> List[str]:
        """
        Format each page individually, optionally using Ollama.

        Returns list of formatted markdown strings, one per page.
        """
        formatted_pages = []

        for page in pages:
            page_num = page.get('page_number', 0)
            text = page.get('text', '').strip()

            if not text:
                formatted_pages.append(f"## Page {page_num}\n\n*[Empty page]*\n")
                continue

            if use_ollama and self.ollama_enabled:
                # Cleanup this page with Ollama
                cleaned = self._cleanup_page(text, page_num)
                formatted_pages.append(f"## Page {page_num}\n\n{cleaned}\n")
            else:
                formatted_pages.append(f"## Page {page_num}\n\n{text}\n")

        return formatted_pages

    def _cleanup_page(self, text: str, page_num: int) -> str:
        """
        Cleanup a single page with Ollama.
        """
        prompt = f"""Clean up the following text from page {page_num} of a document. Fix OCR errors, improve formatting, but preserve all content:

{text}

Cleaned version:"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': self.temperature}
            )
            return response['response']

        except Exception as e:
            logger.error(f"Error cleaning page {page_num}: {e}")
            return text
