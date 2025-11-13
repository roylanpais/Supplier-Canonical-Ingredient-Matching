"""Evaluation metrics: precision@1, coverage, and statistics."""
import csv
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_matches(filepath):
    """Load matches from CSV."""
    matches = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append({
                'item_id': row['item_id'],
                'ingredient_id': int(row['ingredient_id']),
                'confidence': float(row['confidence'])
            })
    return matches


def evaluate_matches(matches, confidence_threshold=0.5):
    """
    Calculate precision@1 and coverage metrics.
    
    Args:
        matches: List of match dictionaries
        confidence_threshold: Minimum confidence to count as valid match
    
    Returns:
        Dictionary with metrics
    """
    total_items = len(matches)
    
    # Coverage: items with valid ingredient_id (> 0)
    coverage_count = sum(1 for m in matches if m['ingredient_id'] > 0)
    coverage = (coverage_count / total_items * 100) if total_items > 0 else 0
    
    # Precision@1: items with confidence >= threshold
    precision_count = sum(
        1 for m in matches 
        if m['ingredient_id'] > 0 and m['confidence'] >= confidence_threshold
    )
    precision_at_1 = (precision_count / total_items * 100) if total_items > 0 else 0
    
    # Confidence statistics
    valid_confidences = [m['confidence'] for m in matches if m['ingredient_id'] > 0]
    avg_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0
    min_confidence = min(valid_confidences) if valid_confidences else 0
    max_confidence = max(valid_confidences) if valid_confidences else 0
    
    # Distribution bins
    confidence_bins = defaultdict(int)
    for m in matches:
        if m['ingredient_id'] > 0:
            bin_label = f"{int(m['confidence']*10)/10:.1f}"
            confidence_bins[bin_label] += 1
    
    return {
        'total_items': total_items,
        'valid_matches': coverage_count,
        'coverage': coverage,
        'precision_at_1': precision_at_1,
        'avg_confidence': avg_confidence,
        'min_confidence': min_confidence,
        'max_confidence': max_confidence,
        'confidence_distribution': dict(sorted(confidence_bins.items()))
    }


def main():
    """Run evaluation."""
    matches_file = 'data/matches.csv'
    
    print("Loading matches...")
    matches = load_matches(matches_file)
    
    print("\n" + "="*70)
    print("EVALUATION REPORT".center(70))
    print("="*70)
    
    metrics = evaluate_matches(matches, confidence_threshold=0.5)
    
    print(f"\nDataset:")
    print(f"  Total Items:           {metrics['total_items']}")
    print(f"  Valid Matches:         {metrics['valid_matches']}")
    
    print(f"\nMetrics:")
    print(f"  Coverage:              {metrics['coverage']:.2f}%")
    print(f"  Precision@1 (≥0.50):   {metrics['precision_at_1']:.2f}%")
    
    print(f"\nConfidence Statistics:")
    print(f"  Average:               {metrics['avg_confidence']:.4f}")
    print(f"  Minimum:               {metrics['min_confidence']:.4f}")
    print(f"  Maximum:               {metrics['max_confidence']:.4f}")
    
    print(f"\nConfidence Distribution:")
    for bin_label in sorted(metrics['confidence_distribution'].keys()):
        count = metrics['confidence_distribution'][bin_label]
        percentage = 100 * count / metrics['valid_matches'] if metrics['valid_matches'] > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"  {bin_label}: {count:3d} items ({percentage:5.1f}%) {bar}")
    
    print("\n" + "="*70)
    
    # Recommendations
    print("\nRecommendations:")
    if metrics['coverage'] < 95:
        print(f"  ⚠ Coverage ({metrics['coverage']:.1f}%) below 95% target")
        print(f"    → Expand misspellings dict or review unmatched items")
    else:
        print(f"  ✓ Coverage ({metrics['coverage']:.1f}%) good")
    
    if metrics['precision_at_1'] < 85:
        print(f"  ⚠ Precision ({metrics['precision_at_1']:.1f}%) below 85% target")
        print(f"    → Review false positives, consider stricter threshold")
    else:
        print(f"  ✓ Precision ({metrics['precision_at_1']:.1f}%) good")
    
    print("\n" + "="*70)
    
    return metrics


if __name__ == '__main__':
    main()
