"""
Evaluation Script for Matching Pipeline
Runs the pipeline and reports comprehensive metrics.
"""

import csv
from pathlib import Path
from collections import defaultdict
import statistics

from matcher import (
    run_pipeline,
    load_master_ingredients,
    load_supplier_items,
    MatchingEngine,
    MIN_CONFIDENCE_THRESHOLD,
    MASTER_FILE,
    SUPPLIER_FILE,
    OUTPUT_FILE,
)


def load_matches(filepath: Path) -> dict:
    """Load matches from CSV."""
    matches = {}
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches[row['item_id']] = {
                'ingredient_id': row['ingredient_id'] if row['ingredient_id'] else None,
                'confidence': float(row['confidence'])
            }
    return matches


def generate_detailed_report():
    """Generate detailed evaluation report."""
    
    print("\n" + "="*80)
    print("FUZZY ENTITY MATCHING PIPELINE - EVALUATION REPORT")
    print("="*80 + "\n")
    
    # Run pipeline
    print("[1/3] Running matching pipeline...")
    eval_metrics = run_pipeline(MASTER_FILE, SUPPLIER_FILE, OUTPUT_FILE)
    
    print("\n[2/3] Loading results...")
    matches = load_matches(OUTPUT_FILE)
    ingredients = load_master_ingredients(MASTER_FILE)
    supplier_items = load_supplier_items(SUPPLIER_FILE)
    
    print(f"\n[3/3] Generating report...\n")
    
    # Basic metrics
    print("-" * 80)
    print("BASIC METRICS")
    print("-" * 80)
    print(f"Total supplier items: {eval_metrics['total_items']}")
    print(f"High-confidence matches (≥{MIN_CONFIDENCE_THRESHOLD}): {eval_metrics['high_confidence_matches']}")
    print(f"Coverage: {eval_metrics['coverage']:.2%}")
    print(f"Avg confidence: {eval_metrics['avg_confidence']:.4f}")
    
    # Confidence distribution
    print("\n" + "-" * 80)
    print("CONFIDENCE DISTRIBUTION")
    print("-" * 80)
    for bin_range, count in eval_metrics['confidence_distribution'].items():
        pct = (count / eval_metrics['total_items'] * 100) if eval_metrics['total_items'] > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"{bin_range:>10}: {count:>3} ({pct:>5.1f}%) {bar}")
    
    # Match details
    print("\n" + "-" * 80)
    print("MATCH DETAILS (ALL ITEMS)")
    print("-" * 80)
    print(f"{'Item ID':<10} {'Raw Name':<40} {'Ingredient':<20} {'Confidence':>10}")
    print("-" * 80)
    
    for item in supplier_items:
        match = matches.get(item.item_id, {})
        ingredient_id = match.get('ingredient_id')
        confidence = match.get('confidence', 0.0)
        
        # Find ingredient name
        ingredient_name = "UNMATCHED"
        if ingredient_id:
            ing = next((i for i in ingredients if i.ingredient_id == int(ingredient_id)), None)
            if ing:
                ingredient_name = ing.name
        
        # Format confidence with color coding
        conf_str = f"{confidence:.4f}"
        if confidence >= 0.8:
            conf_str = "✓ " + conf_str  # High confidence
        elif confidence >= 0.6:
            conf_str = "~ " + conf_str  # Medium confidence
        else:
            conf_str = "✗ " + conf_str  # Low confidence
        
        print(f"{item.item_id:<10} {item.raw_name:<40} {ingredient_name:<20} {conf_str:>10}")
    
    # Summary
    print("\n" + "-" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("-" * 80)
    
    high_conf_pct = eval_metrics['coverage']
    if high_conf_pct >= 0.95:
        print("✓ Excellent coverage! Pipeline is ready for production.")
    elif high_conf_pct >= 0.80:
        print("✓ Good coverage. Consider reviewing low-confidence matches (~20%).")
    elif high_conf_pct >= 0.60:
        print("⚠ Moderate coverage. Recommend expanding abbreviations dictionary or")
        print("  adjusting confidence threshold.")
    else:
        print("✗ Low coverage. Review data quality and consider retraining.")
    
    print("\nKey insights:")
    if eval_metrics['avg_confidence'] >= 0.85:
        print("  • High average confidence: Most matches are reliable.")
    elif eval_metrics['avg_confidence'] >= 0.70:
        print("  • Moderate average confidence: Mix of strong and weak matches.")
    else:
        print("  • Low average confidence: Many weak matches; investigate data quality.")
    
    # Tie-breaker policy
    print("\nMatching pipeline configuration:")
    print(f"  • Minimum confidence threshold: {MIN_CONFIDENCE_THRESHOLD}")
    print(f"  • Blocking strategy: Token-set similarity (≥2 tokens)")
    print(f"  • Similarity metrics: Levenshtein, Jaro-Winkler, TF-IDF (max)")
    print(f"  • Tie-breaking: By ingredient_id (deterministic)")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    generate_detailed_report()
