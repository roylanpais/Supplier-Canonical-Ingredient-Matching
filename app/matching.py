import pandas as pd
from collections import defaultdict
from fuzzywuzzy import fuzz
from .processing import normalize

class Matcher:
    """
    Handles the fuzzy matching logic, including building a
    blocking index for performance and scoring candidates.
    """
    def __init__(self, master_data: pd.DataFrame):
        """
        Initializes the matcher by loading and processing the
        master ingredient list.
        
        Args:
            master_data: DataFrame with 'ingredient_id' and 'name' columns.
        """
        if 'ingredient_id' not in master_data.columns or 'name' not in master_data.columns:
            raise ValueError("master_data must contain 'ingredient_id' and 'name' columns")
            
        self.master_data = master_data.copy()
        
        # Normalize all master names and store them
        self.master_data['normalized_name'] = self.master_data['name'].apply(normalize)
        
        # Create a lookup for normalized name by id
        self.normalized_lookup = self.master_data.set_index('ingredient_id')['normalized_name'].to_dict()
        
        # Build the blocking index for fast candidate retrieval
        self._build_index()

    def _build_index(self):
        """
        Builds an inverted index (token -> set[ingredient_id]) from the
        normalized master names for efficient candidate retrieval (blocking).
        """
        self.index = defaultdict(set)
        for row in self.master_data.itertuples():
            normalized_name = str(row.normalized_name)
            ingredient_id = str(row.ingredient_id)
            
            tokens = set(normalized_name.split())
            if not tokens:
                continue
                
            for token in tokens:
                self.index[token].add(ingredient_id)

    def _get_candidates(self, normalized_query: str) -> set[str]:
        """
        Gets a set of candidate ingredient_ids from the blocking index.
        """
        query_tokens = set(normalized_query.split())
        if not query_tokens:
            return set()

        candidates = set()
        for token in query_tokens:
            candidates.update(self.index.get(token, set()))

        # Fallback: If no tokens match, we must search everything.
        # This is slow but guarantees a match can be found.
        if not candidates:
            return set(self.master_data['ingredient_id'].astype(str))

        return candidates

    def match(self, raw_name: str, threshold: int = 70) -> tuple[str | None, float]:
        """
        Finds the single best match for a raw supplier item name.
        
        Args:
            raw_name: The noisy supplier item name.
            threshold: The confidence threshold (0-100) for evaluation.
                       (Note: this function returns the best match
                       regardless of threshold).
                       
        Returns:
            A tuple of (best_match_ingredient_id, confidence_score [0.0-1.0]).
            Returns (None, 0.0) if no match is possible (e.g., empty query).
        """
        normalized_query = normalize(raw_name)

        if not normalized_query:
            return None, 0.0

        candidate_ids = self._get_candidates(normalized_query)

        if not candidate_ids:
            return None, 0.0

        best_score = -1
        best_match_id = None

        # Iterate through candidates and find the best fuzzy score
        for ing_id in candidate_ids:
            candidate_norm_name = self.normalized_lookup.get(ing_id)
            if not candidate_norm_name:
                continue
            
            # Use token_set_ratio for robustness to word order,
            # subsets, and misspellings.
            score = fuzz.token_set_ratio(normalized_query, candidate_norm_name)

            if score > best_score:
                best_score = score
                best_match_id = ing_id
        
        # Return the single best match and its score normalized to [0, 1]
        if best_match_id is None:
             return None, 0.0

        return best_match_id, best_score / 100.0