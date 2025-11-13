"""Text preprocessing and normalization for ingredient matching."""
import re
from typing import List, Set
import unicodedata


class TextPreprocessor:
    """Handles text normalization and tokenization for matching."""
    
    # Common stop words in ingredient contexts
    STOP_WORDS = {
        'pack', 'g', 'kg', 'ml', 'l', 'liter', 'gram',
        'and', 'or', 'the', 'a', 'an', 'is', 'in', 'of',
        'full', 'extra', 'virgin', 'unsalted', 'unslt',
        'plain', 'long', 'grain', 'red', 'white', 'peeled'
    }
    
    # Common unit patterns to remove
    UNIT_PATTERNS = [
        r'\d+\s*(kg|g|ml|l|liter|litre|pound|oz|pcs|piece)',
        r'\(.*?\)',  # Remove parenthetical content
    ]
    
    # Common misspelling corrections
    CORRECTIONS = {
        'gralic': 'garlic',
        'garic': 'garlic',
        'jeera': 'cumin',
        'jira': 'cumin',
    }
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize: lowercase, remove accents, clean whitespace."""
        if not text:
            return ""
        
        text = text.lower().strip()
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        for pattern in TextPreprocessor.UNIT_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Split text and remove stop words."""
        tokens = text.split()
        return [t for t in tokens 
                if t not in TextPreprocessor.STOP_WORDS and len(t) > 1]
    
    @staticmethod
    def correct_misspellings(text: str) -> str:
        """Apply misspelling corrections."""
        normalized = text
        for misspelling, correction in TextPreprocessor.CORRECTIONS.items():
            normalized = re.sub(rf'\b{misspelling}\b', correction, normalized)
        return normalized
    
    @staticmethod
    def preprocess(text: str) -> str:
        """Full preprocessing pipeline."""
        text = TextPreprocessor.normalize_text(text)
        text = TextPreprocessor.correct_misspellings(text)
        return text
    
    @staticmethod
    def get_tokens(text: str) -> Set[str]:
        """Get set of tokens for a text."""
        text = TextPreprocessor.preprocess(text)
        return set(TextPreprocessor.tokenize(text))
