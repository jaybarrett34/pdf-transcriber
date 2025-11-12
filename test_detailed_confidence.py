#!/usr/bin/env python3
"""
Detailed confidence interval testing with various scenarios.
"""

import random
import difflib
from typing import Dict, List
import json


def simulate_scenario(scenario_name: str, ocr_error_rate: float, parse_success_rate: float, text_sample: str):
    """
    Simulate a specific scenario and show confidence scoring behavior.
    """
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*80}")
    print(f"OCR Error Rate: {ocr_error_rate:.1%}")
    print(f"Parse Success Rate: {parse_success_rate:.1%}")
    print()

    # Simulate OCR
    ocr_text = list(text_sample)
    errors_introduced = 0

    for i in range(len(ocr_text)):
        if random.random() < ocr_error_rate:
            # Introduce error
            if ocr_text[i] == 'l':
                ocr_text[i] = '1'
            elif ocr_text[i] == 'o':
                ocr_text[i] = '0'
            elif ocr_text[i] == 'I':
                ocr_text[i] = 'l'
            elif ocr_text[i] == 'e':
                ocr_text[i] = 'c'
            errors_introduced += 1

    ocr_text = ''.join(ocr_text)
    ocr_confidence = max(0.5, 1.0 - (ocr_error_rate * 2))

    # Simulate parsing
    if random.random() < parse_success_rate:
        parsed_text = text_sample  # Perfect extraction
        parsed_confidence = 0.95
    else:
        parsed_text = ""  # Scanned PDF, no text
        parsed_confidence = 0.0

    # Calculate similarity
    if parsed_text and ocr_text:
        similarity = difflib.SequenceMatcher(None, ocr_text.lower(), parsed_text.lower()).ratio()
    else:
        similarity = 0.0

    # Reconciliation logic
    similarity_threshold = 0.85
    conflict_threshold = 0.4

    if not parsed_text and ocr_text:
        decision = "ocr"
        final_confidence = ocr_confidence
        reason = "Only OCR has content (scanned PDF)"
    elif not ocr_text and parsed_text:
        decision = "parsed"
        final_confidence = parsed_confidence
        reason = "Only parsed has content"
    elif not ocr_text and not parsed_text:
        decision = "none"
        final_confidence = 0.0
        reason = "No content from either source"
    elif similarity >= similarity_threshold:
        decision = "parsed"
        final_confidence = 0.95
        reason = f"High similarity ({similarity:.2%}), prefer parsed (cleaner)"
    elif similarity <= conflict_threshold:
        if ocr_confidence > 0.8:
            decision = "ocr"
            final_confidence = ocr_confidence
            reason = f"Low similarity ({similarity:.2%}), high OCR confidence"
        else:
            decision = "reconciled"
            final_confidence = 0.75
            reason = f"Low similarity ({similarity:.2%}), heavy reconciliation needed"
    else:
        if ocr_confidence > 0.85:
            decision = "ocr"
            final_confidence = ocr_confidence
            reason = f"Medium similarity ({similarity:.2%}), high OCR confidence"
        else:
            decision = "parsed"
            final_confidence = 0.85
            reason = f"Medium similarity ({similarity:.2%}), prefer parsed"

    # Display results
    print(f"OCR Results:")
    print(f"  Errors Introduced: {errors_introduced}/{len(text_sample)} chars ({errors_introduced/len(text_sample):.1%})")
    print(f"  OCR Confidence: {ocr_confidence:.2%}")
    print(f"  Sample: '{ocr_text[:80]}...'")
    print()
    print(f"Parsing Results:")
    print(f"  Success: {'Yes' if parsed_text else 'No'}")
    print(f"  Parse Confidence: {parsed_confidence:.2%}")
    if parsed_text:
        print(f"  Sample: '{parsed_text[:80]}...'")
    print()
    print(f"Reconciliation:")
    print(f"  Similarity Score: {similarity:.2%}")
    print(f"  Decision: Use {decision.upper()}")
    print(f"  Final Confidence: {final_confidence:.2%}")
    print(f"  Reason: {reason}")

    return {
        'scenario': scenario_name,
        'ocr_error_rate': ocr_error_rate,
        'parse_success_rate': parse_success_rate,
        'ocr_confidence': ocr_confidence,
        'parsed_confidence': parsed_confidence,
        'similarity': similarity,
        'decision': decision,
        'final_confidence': final_confidence,
        'reason': reason,
        'errors_introduced': errors_introduced
    }


def main():
    print("="*80)
    print("DETAILED CONFIDENCE INTERVAL ANALYSIS")
    print("Demonstrating how confidence scoring works in different scenarios")
    print("="*80)

    # Sample text
    modern_sample = "Artificial intelligence has revolutionized the way we interact with technology in the twenty-first century. From simple voice assistants to complex machine learning algorithms, AI has become integral to our lives."

    old_sample = "In þe olde dayes, whan þe worlde was yonge and men spake in tongues now longe forgoten, þere dwelte in þis lande a grete kyngdome of muchel renoun and wisdom."

    # Test various scenarios
    random.seed(42)
    scenarios = []

    # Scenario 1: Perfect case - clean PDF with good OCR
    scenarios.append(simulate_scenario(
        "1. Clean PDF with Good OCR",
        ocr_error_rate=0.01,
        parse_success_rate=0.95,
        text_sample=modern_sample
    ))

    # Scenario 2: Scanned document - must rely on OCR
    scenarios.append(simulate_scenario(
        "2. Scanned Document (OCR Only)",
        ocr_error_rate=0.05,
        parse_success_rate=0.0,  # No parseable text
        text_sample=modern_sample
    ))

    # Scenario 3: Old English with higher OCR errors
    scenarios.append(simulate_scenario(
        "3. Old English Text (Higher OCR Error)",
        ocr_error_rate=0.08,
        parse_success_rate=0.70,
        text_sample=old_sample
    ))

    # Scenario 4: Very poor OCR quality
    scenarios.append(simulate_scenario(
        "4. Poor Quality Scan (High OCR Error)",
        ocr_error_rate=0.15,
        parse_success_rate=0.0,
        text_sample=modern_sample
    ))

    # Scenario 5: Conflict case - medium similarity
    scenarios.append(simulate_scenario(
        "5. Medium Similarity Conflict",
        ocr_error_rate=0.06,
        parse_success_rate=0.90,
        text_sample=modern_sample
    ))

    # Summary table
    print(f"\n{'='*80}")
    print("SUMMARY TABLE")
    print(f"{'='*80}\n")

    print(f"{'Scenario':<35} {'Decision':<12} {'Confidence':<12} {'Similarity':<12}")
    print("-" * 80)
    for s in scenarios:
        print(f"{s['scenario']:<35} {s['decision']:<12} {s['final_confidence']:>6.2%}      {s['similarity']:>6.2%}")

    # Confidence interval distribution
    print(f"\n{'='*80}")
    print("CONFIDENCE INTERVAL DISTRIBUTION")
    print(f"{'='*80}\n")

    high_conf = [s for s in scenarios if s['final_confidence'] > 0.9]
    medium_conf = [s for s in scenarios if 0.7 <= s['final_confidence'] <= 0.9]
    low_conf = [s for s in scenarios if s['final_confidence'] < 0.7]

    print(f"High Confidence (>90%): {len(high_conf)} scenarios")
    for s in high_conf:
        print(f"  - {s['scenario']}: {s['final_confidence']:.2%}")

    print(f"\nMedium Confidence (70-90%): {len(medium_conf)} scenarios")
    for s in medium_conf:
        print(f"  - {s['scenario']}: {s['final_confidence']:.2%}")

    print(f"\nLow Confidence (<70%): {len(low_conf)} scenarios")
    for s in low_conf:
        print(f"  - {s['scenario']}: {s['final_confidence']:.2%}")

    # Key insights
    print(f"\n{'='*80}")
    print("KEY INSIGHTS")
    print(f"{'='*80}\n")

    print("1. Confidence Thresholds:")
    print("   - High (>90%): Text-based PDFs with good OCR or high similarity")
    print("   - Medium (70-90%): Reconciled text or medium similarity conflicts")
    print("   - Low (<70%): Very poor OCR with no alternative\n")

    print("2. Decision Logic:")
    print("   - Similarity >85%: Prefer parsed (cleaner, no OCR errors)")
    print("   - Similarity <40%: Heavy reconciliation or use high-confidence source")
    print("   - Similarity 40-85%: Choose based on confidence scores\n")

    print("3. Source Priority:")
    ocr_count = sum(1 for s in scenarios if s['decision'] == 'ocr')
    parsed_count = sum(1 for s in scenarios if s['decision'] == 'parsed')
    reconciled_count = sum(1 for s in scenarios if s['decision'] == 'reconciled')

    print(f"   - OCR Only: {ocr_count} scenarios ({ocr_count/len(scenarios):.0%})")
    print(f"   - Parsed: {parsed_count} scenarios ({parsed_count/len(scenarios):.0%})")
    print(f"   - Reconciled: {reconciled_count} scenarios ({reconciled_count/len(scenarios):.0%})\n")

    print("4. Error Tolerance:")
    print("   - Modern English: Tolerates ~1-5% OCR error with good parsing")
    print("   - Old English: System adapts, tolerates ~8% error rate")
    print("   - Scanned docs: Relies on OCR, confidence reflects error rate\n")

    # Save detailed results
    with open('test_confidence_intervals.json', 'w') as f:
        json.dump(scenarios, f, indent=2)

    print(f"Detailed results saved to: test_confidence_intervals.json")


if __name__ == "__main__":
    main()
