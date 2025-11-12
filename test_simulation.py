#!/usr/bin/env python3
"""
Simulation of the PDF transcriber backend for testing confidence scoring.
This simulates OCR and parsing results without needing heavy dependencies.
"""

import difflib
import random
from typing import Dict, List
import json


class SimulatedOCR:
    """Simulate OCR with controlled error rates."""

    def __init__(self, error_rate=0.02):
        """
        error_rate: Probability of character-level OCR error (0.0 to 1.0)
        """
        self.error_rate = error_rate
        # Common OCR confusion pairs
        self.confusions = {
            'l': ['I', '1', '|'],
            'I': ['l', '1', '|'],
            '1': ['l', 'I', '|'],
            '0': ['O', 'o'],
            'O': ['0', 'o'],
            'o': ['0', 'O'],
            'rn': ['m'],
            'vv': ['w'],
            'cl': ['d'],
            '5': ['S'],
            'S': ['5'],
            'þ': ['p', 'th'],  # Old English thorn
            'Þ': ['P', 'Th'],
            'ð': ['d', 'th'],  # Old English eth
        }

    def process_text(self, text: str, confidence_boost: float = 0.0) -> Dict:
        """
        Simulate OCR processing with errors.

        confidence_boost: Additional confidence for easier texts (0.0 to 1.0)
        """
        result_text = []
        char_confidences = []

        i = 0
        while i < len(text):
            char = text[i]

            # Check for multi-char patterns
            if i < len(text) - 1:
                two_char = text[i:i+2]
                if two_char in self.confusions and random.random() < self.error_rate:
                    # Introduce OCR error
                    result_text.append(random.choice(self.confusions[two_char]))
                    char_confidences.append(random.uniform(0.5, 0.8))
                    i += 2
                    continue

            # Single character processing
            if char in self.confusions and random.random() < self.error_rate:
                # Introduce OCR error
                result_text.append(random.choice(self.confusions[char]))
                char_confidences.append(random.uniform(0.5, 0.8))
            else:
                # Correct recognition
                result_text.append(char)
                char_confidences.append(random.uniform(0.85 + confidence_boost, 0.98 + confidence_boost))

            i += 1

        # Calculate overall confidence
        avg_confidence = sum(char_confidences) / len(char_confidences) if char_confidences else 0.0

        return {
            'text': ''.join(result_text),
            'confidence': min(1.0, avg_confidence),
            'lines': []  # Simplified
        }


class SimulatedParser:
    """Simulate PDF text parsing."""

    def __init__(self, extractable_rate=0.8):
        """
        extractable_rate: Probability that text can be extracted (0.0 to 1.0)
        """
        self.extractable_rate = extractable_rate

    def parse_text(self, text: str, is_scanned: bool = False) -> Dict:
        """
        Simulate PDF text extraction.

        is_scanned: If True, simulate scanned PDF (no extractable text)
        """
        if is_scanned or random.random() > self.extractable_rate:
            # Scanned PDF - no extractable text
            return {
                'text': '',
                'confidence': 0.0
            }
        else:
            # Text-based PDF - clean extraction
            # Sometimes introduce minor artifacts
            result_text = text
            if random.random() < 0.1:  # 10% chance of minor issues
                # Remove some line breaks (common PDF artifact)
                result_text = result_text.replace('\n\n', '\n')

            return {
                'text': result_text,
                'confidence': 0.95
            }


class SimulatedReconciler:
    """Simulate text reconciliation logic."""

    def __init__(self, similarity_threshold=0.85, conflict_threshold=0.4):
        self.similarity_threshold = similarity_threshold
        self.conflict_threshold = conflict_threshold

    def reconcile(self, ocr_result: Dict, parsed_result: Dict) -> Dict:
        """
        Reconcile OCR and parsed text using confidence scoring.
        """
        ocr_text = ocr_result.get('text', '').strip()
        parsed_text = parsed_result.get('text', '').strip()
        ocr_confidence = ocr_result.get('confidence', 0.0)

        # Case 1: Only OCR has content
        if not parsed_text and ocr_text:
            return {
                'text': ocr_text,
                'source': 'ocr',
                'confidence': ocr_confidence,
                'similarity_score': 0.0
            }

        # Case 2: Only parsed text has content
        if not ocr_text and parsed_text:
            return {
                'text': parsed_text,
                'source': 'parsed',
                'confidence': 0.95,
                'similarity_score': 0.0
            }

        # Case 3: Neither has content
        if not ocr_text and not parsed_text:
            return {
                'text': '',
                'source': 'none',
                'confidence': 0.0,
                'similarity_score': 0.0
            }

        # Case 4: Both have content - calculate similarity
        similarity = difflib.SequenceMatcher(None, ocr_text.lower(), parsed_text.lower()).ratio()

        # High similarity - prefer parsed (cleaner)
        if similarity >= self.similarity_threshold:
            return {
                'text': parsed_text,
                'source': 'parsed',
                'confidence': 0.95,
                'similarity_score': similarity,
                'reason': f'High similarity ({similarity:.2%})'
            }

        # Low similarity - need deeper analysis
        if similarity <= self.conflict_threshold:
            # Use confidence to decide
            if ocr_confidence > 0.8:
                return {
                    'text': ocr_text,
                    'source': 'ocr',
                    'confidence': ocr_confidence,
                    'similarity_score': similarity,
                    'reason': f'Low similarity ({similarity:.2%}), high OCR confidence'
                }
            else:
                return {
                    'text': parsed_text,
                    'source': 'reconciled',
                    'confidence': 0.75,
                    'similarity_score': similarity,
                    'reason': f'Low similarity ({similarity:.2%}), low OCR confidence',
                    'needs_review': True
                }

        # Medium similarity - choose based on confidence
        if ocr_confidence > 0.85:
            return {
                'text': ocr_text,
                'source': 'ocr',
                'confidence': ocr_confidence,
                'similarity_score': similarity,
                'reason': f'Medium similarity ({similarity:.2%}), high OCR confidence'
            }
        else:
            return {
                'text': parsed_text,
                'source': 'parsed',
                'confidence': 0.85,
                'similarity_score': similarity,
                'reason': f'Medium similarity ({similarity:.2%}), preferring parsed'
            }


def simulate_processing(text: str, doc_name: str, is_old_english: bool = False):
    """
    Simulate processing a document through the pipeline.
    """
    print(f"\n{'='*80}")
    print(f"SIMULATING: {doc_name}")
    print(f"{'='*80}")

    # Split into pages (approximate)
    words = text.split()
    words_per_page = 500
    pages = []

    for i in range(0, len(words), words_per_page):
        page_words = words[i:i+words_per_page]
        pages.append(' '.join(page_words))

    print(f"Document split into {len(pages)} pages\n")

    # Initialize components
    # Old English has higher OCR error rate due to unusual characters
    ocr = SimulatedOCR(error_rate=0.05 if is_old_english else 0.02)

    # Old English might be scanned more often, lower extractable rate
    parser = SimulatedParser(extractable_rate=0.6 if is_old_english else 0.9)

    reconciler = SimulatedReconciler()

    # Process each page
    results = []
    for page_num, page_text in enumerate(pages, 1):
        print(f"Processing Page {page_num}/{len(pages)}...")

        # Simulate OCR
        # Old English gets lower confidence boost
        confidence_boost = 0.0 if is_old_english else 0.05
        ocr_result = ocr.process_text(page_text, confidence_boost)

        # Simulate parsing
        # Randomly some pages are scanned
        is_scanned = random.random() < 0.2 if is_old_english else random.random() < 0.05
        parsed_result = parser.parse_text(page_text, is_scanned)

        # Reconcile
        final_result = reconciler.reconcile(ocr_result, parsed_result)
        final_result['page_number'] = page_num
        final_result['original_length'] = len(page_text)
        final_result['extracted_length'] = len(final_result['text'])

        # Calculate accuracy
        similarity = difflib.SequenceMatcher(
            None,
            page_text.lower(),
            final_result['text'].lower()
        ).ratio()
        final_result['accuracy'] = similarity

        results.append(final_result)

        # Print page summary
        print(f"  Source: {final_result['source']:<12} "
              f"Confidence: {final_result['confidence']:>6.2%}  "
              f"Accuracy: {final_result['accuracy']:>6.2%}  "
              f"Similarity: {final_result.get('similarity_score', 0):>6.2%}")
        if 'reason' in final_result:
            print(f"  Reason: {final_result['reason']}")

    return results


def analyze_results(results: List[Dict], doc_name: str):
    """Analyze and display results."""
    print(f"\n{'='*80}")
    print(f"ANALYSIS: {doc_name}")
    print(f"{'='*80}\n")

    # Overall statistics
    total_pages = len(results)
    avg_confidence = sum(r['confidence'] for r in results) / total_pages
    avg_accuracy = sum(r['accuracy'] for r in results) / total_pages

    sources = [r['source'] for r in results]
    source_counts = {s: sources.count(s) for s in set(sources)}

    print(f"Overall Statistics:")
    print(f"  Total Pages: {total_pages}")
    print(f"  Average Confidence: {avg_confidence:.2%}")
    print(f"  Average Accuracy: {avg_accuracy:.2%}")
    print(f"\nSource Distribution:")
    for source, count in sorted(source_counts.items()):
        percentage = (count / total_pages) * 100
        print(f"  {source:>12}: {count:>3} pages ({percentage:>5.1f}%)")

    # Confidence intervals
    print(f"\nConfidence Intervals:")
    intervals = {
        'High (>90%)': [r for r in results if r['confidence'] > 0.9],
        'Medium (70-90%)': [r for r in results if 0.7 <= r['confidence'] <= 0.9],
        'Low (<70%)': [r for r in results if r['confidence'] < 0.7]
    }

    for interval, pages in intervals.items():
        count = len(pages)
        percentage = (count / total_pages) * 100
        avg_acc = sum(p['accuracy'] for p in pages) / count if count > 0 else 0
        print(f"  {interval:>15}: {count:>3} pages ({percentage:>5.1f}%) - Avg Accuracy: {avg_acc:.2%}")

    # Pages needing review
    needs_review = [r for r in results if r.get('needs_review', False)]
    if needs_review:
        print(f"\nPages Needing Review: {len(needs_review)}")
        for page in needs_review:
            print(f"  Page {page['page_number']}: {page.get('reason', 'Unknown')}")

    return {
        'doc_name': doc_name,
        'total_pages': total_pages,
        'avg_confidence': avg_confidence,
        'avg_accuracy': avg_accuracy,
        'source_distribution': source_counts,
        'confidence_intervals': {k: len(v) for k, v in intervals.items()}
    }


def main():
    """Main test function."""
    print("\n" + "="*80)
    print("PDF TRANSCRIBER CONFIDENCE SCORING SIMULATION")
    print("Testing without Ollama - Pure OCR + Parsing + Reconciliation")
    print("="*80)

    # Load test documents
    with open('test_data/modern_english.txt', 'r') as f:
        modern_text = f.read()

    with open('test_data/old_english.txt', 'r') as f:
        old_text = f.read()

    # Set random seed for reproducibility
    random.seed(42)

    # Process both documents
    modern_results = simulate_processing(modern_text, "Modern English", is_old_english=False)
    old_results = simulate_processing(old_text, "Old English", is_old_english=True)

    # Analyze results
    modern_analysis = analyze_results(modern_results, "Modern English")
    old_analysis = analyze_results(old_results, "Old English")

    # Comparative analysis
    print(f"\n{'='*80}")
    print("COMPARATIVE ANALYSIS")
    print(f"{'='*80}\n")

    print(f"{'Metric':<30} {'Modern English':>20} {'Old English':>20}")
    print("-" * 72)
    print(f"{'Average Confidence':<30} {modern_analysis['avg_confidence']:>19.2%} {old_analysis['avg_confidence']:>19.2%}")
    print(f"{'Average Accuracy':<30} {modern_analysis['avg_accuracy']:>19.2%} {old_analysis['avg_accuracy']:>19.2%}")
    print(f"{'Total Pages':<30} {modern_analysis['total_pages']:>20} {old_analysis['total_pages']:>20}")

    print("\nSource Distribution Comparison:")
    all_sources = set(modern_analysis['source_distribution'].keys()) | set(old_analysis['source_distribution'].keys())
    for source in sorted(all_sources):
        modern_count = modern_analysis['source_distribution'].get(source, 0)
        old_count = old_analysis['source_distribution'].get(source, 0)
        print(f"  {source:>12}: {modern_count:>3} pages (modern), {old_count:>3} pages (old)")

    # Save results
    summary = {
        'modern_english': modern_analysis,
        'old_english': old_analysis,
        'comparison': {
            'confidence_difference': modern_analysis['avg_confidence'] - old_analysis['avg_confidence'],
            'accuracy_difference': modern_analysis['avg_accuracy'] - old_analysis['avg_accuracy']
        }
    }

    with open('test_results_simulation.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n\n{'='*80}")
    print("KEY FINDINGS")
    print(f"{'='*80}\n")

    conf_diff = summary['comparison']['confidence_difference']
    acc_diff = summary['comparison']['accuracy_difference']

    print(f"1. Confidence Scoring Performance:")
    print(f"   - Modern English: {modern_analysis['avg_confidence']:.2%} average confidence")
    print(f"   - Old English: {old_analysis['avg_confidence']:.2%} average confidence")
    print(f"   - Difference: {abs(conf_diff):.2%} {'higher' if conf_diff > 0 else 'lower'} for modern English")

    print(f"\n2. Accuracy Performance:")
    print(f"   - Modern English: {modern_analysis['avg_accuracy']:.2%} accuracy")
    print(f"   - Old English: {old_analysis['avg_accuracy']:.2%} accuracy")
    print(f"   - Difference: {abs(acc_diff):.2%} {'higher' if acc_diff > 0 else 'lower'} for modern English")

    print(f"\n3. Reconciliation Strategy:")
    modern_parsed_pct = (modern_analysis['source_distribution'].get('parsed', 0) / modern_analysis['total_pages']) * 100
    old_parsed_pct = (old_analysis['source_distribution'].get('parsed', 0) / old_analysis['total_pages']) * 100
    print(f"   - Modern English: {modern_parsed_pct:.1f}% from parsing (cleaner extraction)")
    print(f"   - Old English: {old_parsed_pct:.1f}% from parsing")
    print(f"   - System adapts to document difficulty by choosing optimal source")

    print(f"\nResults saved to: test_results_simulation.json")


if __name__ == "__main__":
    main()
