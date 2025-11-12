from typing import Dict, List, Tuple, Optional
import difflib
import Levenshtein
from sentence_transformers import SentenceTransformer
import logging
import torch

logger = logging.getLogger(__name__)

class TextReconciler:
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        conflict_threshold: float = 0.4,
        use_semantic: bool = True,
        semantic_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize text reconciler for comparing OCR and parsed text.

        Args:
            similarity_threshold: If similarity > this, prefer parsed text
            conflict_threshold: If similarity < this, use heavy reconciliation
            use_semantic: Whether to use semantic similarity
            semantic_model: HuggingFace model for semantic comparison
        """
        self.similarity_threshold = similarity_threshold
        self.conflict_threshold = conflict_threshold
        self.use_semantic = use_semantic

        # Load semantic model if needed
        self.semantic_model = None
        if use_semantic:
            try:
                logger.info(f"Loading semantic model: {semantic_model}")
                self.semantic_model = SentenceTransformer(semantic_model)
                logger.info("Semantic model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load semantic model: {e}")
                self.use_semantic = False

    def reconcile_page(
        self,
        ocr_result: Dict,
        parsed_result: Dict,
        page_number: int
    ) -> Dict[str, any]:
        """
        Reconcile OCR and parsed text for a single page.

        Returns:
            {
                'text': str,
                'source': 'ocr' | 'parsed' | 'reconciled',
                'confidence': float,
                'similarity_score': float
            }
        """
        ocr_text = ocr_result.get('text', '').strip()
        parsed_text = parsed_result.get('text', '').strip()
        ocr_confidence = ocr_result.get('confidence', 0.0)

        # Case 1: Only OCR has content
        if not parsed_text and ocr_text:
            logger.debug(f"Page {page_number}: Only OCR has content")
            return {
                'text': ocr_text,
                'source': 'ocr',
                'confidence': ocr_confidence,
                'similarity_score': 0.0
            }

        # Case 2: Only parsed text has content
        if not ocr_text and parsed_text:
            logger.debug(f"Page {page_number}: Only parsed text has content")
            return {
                'text': parsed_text,
                'source': 'parsed',
                'confidence': 0.95,
                'similarity_score': 0.0
            }

        # Case 3: Neither has content
        if not ocr_text and not parsed_text:
            logger.debug(f"Page {page_number}: No content from either source")
            return {
                'text': '',
                'source': 'none',
                'confidence': 0.0,
                'similarity_score': 0.0
            }

        # Case 4: Both have content - need to reconcile
        logger.debug(f"Page {page_number}: Both sources have content, reconciling...")

        # Calculate string similarity
        string_similarity = self._calculate_string_similarity(ocr_text, parsed_text)
        logger.debug(f"String similarity: {string_similarity:.2f}")

        # High similarity - prefer parsed (usually cleaner)
        if string_similarity >= self.similarity_threshold:
            logger.debug(f"High similarity ({string_similarity:.2f}), using parsed text")
            return {
                'text': parsed_text,
                'source': 'parsed',
                'confidence': 0.95,
                'similarity_score': string_similarity
            }

        # Low similarity - need deeper analysis
        if string_similarity <= self.conflict_threshold:
            logger.debug(f"Low similarity ({string_similarity:.2f}), using semantic analysis")

            # Use semantic similarity if available
            if self.use_semantic and self.semantic_model:
                semantic_sim = self._calculate_semantic_similarity(ocr_text, parsed_text)
                logger.debug(f"Semantic similarity: {semantic_sim:.2f}")

                # If semantically similar, prefer the one with higher confidence
                if semantic_sim > 0.7:
                    if ocr_confidence > 0.8:
                        return {
                            'text': ocr_text,
                            'source': 'ocr',
                            'confidence': ocr_confidence,
                            'similarity_score': semantic_sim
                        }
                    else:
                        return {
                            'text': parsed_text,
                            'source': 'parsed',
                            'confidence': 0.9,
                            'similarity_score': semantic_sim
                        }

            # Heavy reconciliation needed
            reconciled = self._reconcile_with_diff(ocr_text, parsed_text, ocr_confidence)
            return {
                'text': reconciled['text'],
                'source': 'reconciled',
                'confidence': reconciled['confidence'],
                'similarity_score': string_similarity,
                'needs_review': True
            }

        # Medium similarity - choose based on confidence
        if ocr_confidence > 0.85:
            logger.debug(f"Medium similarity, high OCR confidence ({ocr_confidence:.2f})")
            return {
                'text': ocr_text,
                'source': 'ocr',
                'confidence': ocr_confidence,
                'similarity_score': string_similarity
            }
        else:
            logger.debug(f"Medium similarity, preferring parsed text")
            return {
                'text': parsed_text,
                'source': 'parsed',
                'confidence': 0.85,
                'similarity_score': string_similarity
            }

    def _calculate_string_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate string similarity using multiple metrics.
        """
        # Normalize texts
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # Use SequenceMatcher for ratio
        seq_ratio = difflib.SequenceMatcher(None, t1, t2).ratio()

        # Use Levenshtein distance
        lev_ratio = Levenshtein.ratio(t1, t2)

        # Average the two
        return (seq_ratio + lev_ratio) / 2

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity using sentence transformers.
        """
        try:
            # Encode texts
            embeddings = self.semantic_model.encode([text1, text2])

            # Calculate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                torch.tensor(embeddings[0]).unsqueeze(0),
                torch.tensor(embeddings[1]).unsqueeze(0)
            ).item()

            return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0

    def _reconcile_with_diff(
        self,
        ocr_text: str,
        parsed_text: str,
        ocr_confidence: float
    ) -> Dict[str, any]:
        """
        Use diff-based reconciliation to merge texts.

        This is a simple implementation. For production, you might want
        to use Ollama or another LLM here.
        """
        # Split into lines
        ocr_lines = ocr_text.split('\n')
        parsed_lines = parsed_text.split('\n')

        # Use SequenceMatcher to find common subsequences
        matcher = difflib.SequenceMatcher(None, ocr_lines, parsed_lines)

        reconciled_lines = []
        confidence_sum = 0
        count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Both agree - use parsed (usually cleaner)
                reconciled_lines.extend(parsed_lines[j1:j2])
                confidence_sum += 0.95 * (j2 - j1)
                count += (j2 - j1)

            elif tag == 'replace':
                # Disagreement - choose based on length and confidence
                ocr_segment = ocr_lines[i1:i2]
                parsed_segment = parsed_lines[j1:j2]

                if ocr_confidence > 0.8 and len(' '.join(ocr_segment)) > len(' '.join(parsed_segment)):
                    reconciled_lines.extend(ocr_segment)
                    confidence_sum += ocr_confidence * len(ocr_segment)
                else:
                    reconciled_lines.extend(parsed_segment)
                    confidence_sum += 0.8 * len(parsed_segment)

                count += max(len(ocr_segment), len(parsed_segment))

            elif tag == 'delete':
                # OCR has extra content
                if ocr_confidence > 0.7:
                    reconciled_lines.extend(ocr_lines[i1:i2])
                    confidence_sum += ocr_confidence * (i2 - i1)
                    count += (i2 - i1)

            elif tag == 'insert':
                # Parsed has extra content
                reconciled_lines.extend(parsed_lines[j1:j2])
                confidence_sum += 0.8 * (j2 - j1)
                count += (j2 - j1)

        avg_confidence = confidence_sum / count if count > 0 else 0.5

        return {
            'text': '\n'.join(reconciled_lines),
            'confidence': avg_confidence
        }

    def batch_reconcile(
        self,
        ocr_results: List[Dict],
        parsed_results: List[Dict]
    ) -> List[Dict]:
        """
        Reconcile multiple pages.
        """
        results = []

        for i, (ocr_res, parsed_res) in enumerate(zip(ocr_results, parsed_results)):
            page_num = i + 1
            reconciled = self.reconcile_page(ocr_res, parsed_res, page_num)
            reconciled['page_number'] = page_num
            results.append(reconciled)

        return results
