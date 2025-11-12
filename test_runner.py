#!/usr/bin/env python3
"""
Test runner for the PDF transcriber backend.
Tests confidence scoring and accuracy without Ollama.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
import json
from datetime import datetime
import difflib

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from processor import DocumentProcessor
from config_loader import reload_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestResults:
    """Store and analyze test results."""

    def __init__(self):
        self.results = []

    def add_result(self, filename, result, original_text):
        """Add a processing result."""
        self.results.append({
            'filename': filename,
            'result': result,
            'original_text': original_text,
            'timestamp': datetime.now().isoformat()
        })

    def analyze_accuracy(self):
        """Analyze accuracy of extraction."""
        print("\n" + "="*80)
        print("TEST RESULTS ANALYSIS")
        print("="*80)

        for item in self.results:
            filename = item['filename']
            result = item['result']
            original = item['original_text']

            print(f"\n{'='*80}")
            print(f"FILE: {filename}")
            print(f"{'='*80}")

            # Metadata
            metadata = result.get('metadata', {})
            print(f"\nMetadata:")
            print(f"  Total Pages: {metadata.get('total_pages', 'N/A')}")
            print(f"  File Type: {metadata.get('file_type', 'N/A')}")

            # Analyze pages
            pages = result.get('pages', [])
            if pages:
                print(f"\nPer-Page Analysis:")
                print(f"{'Page':<6} {'Source':<12} {'Confidence':<12} {'Characters':<12}")
                print("-" * 50)

                for page in pages:
                    page_num = page.get('page_number', '?')
                    source = page.get('source', 'unknown')
                    confidence = page.get('confidence', 0.0)
                    text_len = len(page.get('text', ''))

                    print(f"{page_num:<6} {source:<12} {confidence:>6.2%}    {text_len:>8} chars")

                # Calculate averages
                avg_confidence = sum(p.get('confidence', 0) for p in pages) / len(pages)
                sources = [p.get('source', 'unknown') for p in pages]
                source_counts = {s: sources.count(s) for s in set(sources)}

                print(f"\nSummary Statistics:")
                print(f"  Average Confidence: {avg_confidence:.2%}")
                print(f"  Source Distribution:")
                for source, count in source_counts.items():
                    percentage = (count / len(pages)) * 100
                    print(f"    - {source}: {count} pages ({percentage:.1f}%)")

            # Text accuracy comparison
            extracted_text = result.get('output', '')

            # Remove markdown formatting for comparison
            cleaned_extracted = self._clean_text(extracted_text)
            cleaned_original = self._clean_text(original)

            # Calculate similarity
            similarity = difflib.SequenceMatcher(None, cleaned_original, cleaned_extracted).ratio()

            print(f"\nText Accuracy:")
            print(f"  Original Length: {len(original)} chars")
            print(f"  Extracted Length: {len(cleaned_extracted)} chars")
            print(f"  Similarity Score: {similarity:.2%}")

            # Character-level accuracy
            if len(cleaned_original) > 0:
                char_accuracy = 1 - (abs(len(cleaned_original) - len(cleaned_extracted)) / len(cleaned_original))
                print(f"  Length Accuracy: {char_accuracy:.2%}")

            # Show sample differences
            if similarity < 0.99:
                print(f"\nSample Differences:")
                self._show_differences(cleaned_original[:1000], cleaned_extracted[:1000])

            # Confidence vs Accuracy analysis
            if pages:
                print(f"\nConfidence vs Accuracy Correlation:")
                for page in pages[:3]:  # Show first 3 pages
                    page_text = page.get('text', '')
                    page_conf = page.get('confidence', 0)
                    page_num = page.get('page_number', 0)

                    # Try to find this section in original
                    # This is approximate since we don't have page boundaries in original
                    print(f"  Page {page_num}: Confidence {page_conf:.2%}, "
                          f"Length {len(page_text)} chars, Source: {page.get('source', 'unknown')}")

    def _clean_text(self, text):
        """Remove markdown and extra whitespace for comparison."""
        import re
        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        # Remove page markers
        text = re.sub(r'---+', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common markdown artifacts
        text = re.sub(r'\*\*|__|\*|_', '', text)
        return text.strip()

    def _show_differences(self, original, extracted, context=50):
        """Show sample differences between texts."""
        matcher = difflib.SequenceMatcher(None, original, extracted)
        differences = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                diff = {
                    'type': tag,
                    'original': original[max(0, i1-context):min(len(original), i2+context)],
                    'extracted': extracted[max(0, j1-context):min(len(extracted), j2+context)]
                }
                differences.append(diff)

                if len(differences) >= 3:  # Show max 3 differences
                    break

        for i, diff in enumerate(differences, 1):
            print(f"\n  Difference {i} ({diff['type']}):")
            print(f"    Original:  ...{diff['original'][:100]}...")
            print(f"    Extracted: ...{diff['extracted'][:100]}...")

    def save_results(self, output_file="test_results.json"):
        """Save results to JSON file."""
        # Prepare serializable results
        serializable_results = []
        for item in self.results:
            serializable_results.append({
                'filename': item['filename'],
                'timestamp': item['timestamp'],
                'metadata': item['result'].get('metadata', {}),
                'output_preview': item['result'].get('output', '')[:500],
                'pages_summary': [
                    {
                        'page_number': p.get('page_number'),
                        'source': p.get('source'),
                        'confidence': p.get('confidence'),
                        'char_count': len(p.get('text', ''))
                    }
                    for p in item['result'].get('pages', [])
                ]
            })

        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"\n\nResults saved to: {output_file}")


async def test_processing(pdf_path, original_text_path):
    """Test processing a single PDF."""
    # Disable Ollama for this test
    config = reload_config()
    config.config['ollama']['enabled'] = False

    # Create processor
    processor = DocumentProcessor(config)

    # Read original text
    with open(original_text_path, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # Progress callback
    async def progress_callback(data):
        stage = data.get('stage', 'unknown')
        progress = data.get('progress', 0)
        message = data.get('message', '')
        print(f"  [{progress:3d}%] {stage}: {message}")

    # Process document
    print(f"\nProcessing: {pdf_path}")
    print("-" * 80)

    try:
        result = await processor.process_document(
            pdf_path,
            output_format='markdown',
            use_ollama_cleanup=False,
            progress_callback=progress_callback
        )

        return result, original_text

    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}", exc_info=True)
        return None, original_text


async def main():
    """Main test runner."""
    print("\n" + "="*80)
    print("PDF TRANSCRIBER TEST SUITE")
    print("Testing confidence scoring and accuracy without Ollama")
    print("="*80)

    # Check if test PDFs exist
    test_files = [
        ('test_data/test_pdfs/modern_english.pdf', 'test_data/modern_english.txt'),
        ('test_data/test_pdfs/old_english.pdf', 'test_data/old_english.txt')
    ]

    # Create test results tracker
    test_results = TestResults()

    for pdf_path, text_path in test_files:
        if not os.path.exists(pdf_path):
            print(f"\nWarning: {pdf_path} not found. Skipping...")
            print("Run: cd test_data && python create_test_pdfs.py")
            continue

        result, original = await test_processing(pdf_path, text_path)

        if result:
            test_results.add_result(
                filename=os.path.basename(pdf_path),
                result=result,
                original_text=original
            )

    # Analyze results
    if test_results.results:
        test_results.analyze_accuracy()
        test_results.save_results()
    else:
        print("\nNo test results to analyze. Please create test PDFs first.")
        print("Run: cd test_data && python create_test_pdfs.py")


if __name__ == "__main__":
    asyncio.run(main())
