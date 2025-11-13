"""Batch matching script for supplier items."""
import csv
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.matcher import FuzzyMatcher


def load_ingredients(filepath):
    """Load ingredients from CSV."""
    ingredients = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ingredients.append({
                'ingredient_id': int(row['ingredient_id']),
                'name': row['name']
            })
    return ingredients


def load_supplier_items(filepath):
    """Load supplier items from CSV."""
    items = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({
                'item_id': row['item_id'],
                'raw_name': row['raw_name']
            })
    return items


def save_matches(matches, output_filepath):
    """Save matches to CSV."""
    with open(output_filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['item_id', 'ingredient_id', 'confidence'])
        writer.writeheader()
        writer.writerows(matches)


def main():
    """Run batch matching."""
    # File paths
    ingredients_file = 'data/ingredients_master.csv'
    supplier_file = 'data/supplier_items.csv'
    output_file = 'data/matches.csv'
    
    print("Loading data...")
    ingredients = load_ingredients(ingredients_file)
    supplier_items = load_supplier_items(supplier_file)
    
    print(f"Loaded {len(ingredients)} canonical ingredients")
    print(f"Loaded {len(supplier_items)} supplier items")
    
    # Initialize matcher
    print("\nInitializing matcher...")
    matcher = FuzzyMatcher(ingredients)
    
    # Match all items
    print("\nMatching items...")
    matches = []
    for item in supplier_items:
        ingredient_id, confidence = matcher.match_single(item['raw_name'])
        matches.append({
            'item_id': item['item_id'],
            'ingredient_id': ingredient_id,
            'confidence': f"{confidence:.4f}"
        })
        status = "✓" if ingredient_id > 0 else "✗"
        print(f"  {status} {item['item_id']}: '{item['raw_name']}' → ID {ingredient_id} ({confidence:.4f})")
    
    # Save matches
    save_matches(matches, output_file)
    print(f"\n✓ Matches saved to {output_file}")
    
    # Summary
    valid_matches = sum(1 for m in matches if m['ingredient_id'] > 0)
    print(f"\nSummary:")
    print(f"  Total items: {len(matches)}")
    print(f"  Valid matches: {valid_matches} ({100*valid_matches/len(matches):.1f}%)")
    print(f"  Unmatched: {len(matches) - valid_matches}")
    
    return matches


if __name__ == '__main__':
    main()
