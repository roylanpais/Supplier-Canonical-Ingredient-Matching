"""Fuzzy matching engine with blocking and similarity scoring."""
from typing import Tuple, List, Dict
from difflib import SequenceMatcher
import sys
from pathlib import Path

# Import preprocessing from same package
sys.path.insert(0, str(Path(__file__).parent))
from preprocessing import TextPreprocessor


class BlockingIndex:
    """Efficient blocking to reduce candidate set."""
    
    def __init__(self, ingredients: List[Dict]):
        self.ingredients = ingredients
        self.prefix_index = self._build_prefix_index()
        self.token_index = self._build_token_index()
    
    def _build_prefix_index(self) -> Dict[str, List[int]]:
        """Index ingredients by 2-3 char prefix."""
        prefix_index = {}
        for idx, ingredient in enumerate(self.ingredients):
            name = TextPreprocessor.preprocess(ingredient['name'])
            for prefix_len in [2, 3]:
                if len(name) >= prefix_len:
                    prefix = name[:prefix_len]
                    if prefix not in prefix_index:
                        prefix_index[prefix] = []
                    prefix_index[prefix].append(idx)
        return prefix_index
    
    def _build_token_index(self) -> Dict[str, List[int]]:
        """Index ingredients by tokens."""
        token_index = {}
        for idx, ingredient in enumerate(self.ingredients):
            tokens = TextPreprocessor.get_tokens(ingredient['name'])
            for token in tokens:
                if token not in token_index:
                    token_index[token] = []
                token_index[token].append(idx)
        return token_index
    
    def get_candidates(self, query: str, max_candidates: int = 50) -> List[int]:
        """Get candidate ingredients using multi-strategy blocking."""
        candidates_set = set()
        
        # Strategy 1: Prefix matching
        normalized_query = TextPreprocessor.preprocess(query)
        for prefix_len in [2, 3]:
            if len(normalized_query) >= prefix_len:
                prefix = normalized_query[:prefix_len]
                if prefix in self.prefix_index:
                    candidates_set.update(self.prefix_index[prefix])
        
        # Strategy 2: Token-based matching
        query_tokens = TextPreprocessor.get_tokens(query)
        for token in query_tokens:
            if token in self.token_index:
                candidates_set.update(self.token_index[token])
        
        # Fallback: return all
        if not candidates_set:
            candidates_set = set(range(len(self.ingredients)))
        
        return list(candidates_set)[:max_candidates]


class FuzzyMatcher:
    """Fuzzy matching engine with multiple strategies."""
    
    EXACT_THRESHOLD = 0.95
    STRONG_THRESHOLD = 0.75
    WEAK_THRESHOLD = 0.50
    
    def __init__(self, ingredients: List[Dict]):
        """Initialize matcher with ingredient list."""
        self.ingredients = ingredients
        self.blocking = BlockingIndex(ingredients)
    
    @staticmethod
    def token_set_similarity(text1: str, text2: str) -> float:
        """Token-set Jaccard similarity."""
        tokens1 = TextPreprocessor.get_tokens(text1)
        tokens2 = TextPreprocessor.get_tokens(text2)
        
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def string_similarity(text1: str, text2: str) -> float:
        """Sequence matching similarity."""
        norm1 = TextPreprocessor.preprocess(text1)
        norm2 = TextPreprocessor.preprocess(text2)
        
        if norm1 == norm2:
            return 1.0
        if not norm1 or not norm2:
            return 0.0
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    @staticmethod
    def combined_similarity(query: str, candidate: str) -> float:
        """Weighted combination of similarity metrics."""
        token_sim = FuzzyMatcher.token_set_similarity(query, candidate)
        string_sim = FuzzyMatcher.string_similarity(query, candidate)
        
        # 60% token, 40% string for robustness
        combined = (0.6 * token_sim) + (0.4 * string_sim)
        return combined
    
    def match_single(self, query: str) -> Tuple[int, float]:
        """Match a single query to best ingredient."""
        if not query or not query.strip():
            return -1, 0.0
        
        candidate_indices = self.blocking.get_candidates(query)
        
        best_score = 0.0
        best_ingredient_id = -1
        
        for idx in candidate_indices:
            ingredient = self.ingredients[idx]
            score = self.combined_similarity(query, ingredient['name'])
            
            if score > best_score:
                best_score = score
                best_ingredient_id = ingredient['ingredient_id']
        
        return best_ingredient_id, best_score
    
    def match_batch(self, queries: List[str]) -> List[Tuple[int, float]]:
        """Match multiple queries."""
        return [self.match_single(q) for q in queries]
