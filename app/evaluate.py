import pandas as pd
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

try:
    from app.config import OUTPUT_FILE, GROUND_TRUTH_FILE, MATCH_THRESHOLD
except ImportError:
    print("Error: Could not import from 'app'. Make sure the script is run from the project root.")
    sys.exit(1)

def evaluate_matches():
    """
    Evaluates the generated matches.csv file against the ground truth.
    Reports Precision@1 and Coverage.
    """
    print("Running evaluation...")
    
    try:
        results_df = pd.read_csv(OUTPUT_FILE)
        ground_truth_df = pd.read_csv(GROUND_TRUTH_FILE)
    except FileNotFoundError as e:
        print(f"Error: Could not load file. {e}")
        print(f"Please run 'python scripts/run_pipeline.py' first to generate {OUTPUT_FILE}.")
        return

    results_df['item_id'] = results_df['item_id'].astype(str)
    results_df['ingredient_id'] = results_df['ingredient_id'].astype(str)
    ground_truth_df['item_id'] = ground_truth_df['item_id'].astype(str)
    ground_truth_df['ingredient_id'] = ground_truth_df['ingredient_id'].astype(str)

    merged_df = pd.merge(
        ground_truth_df, 
        results_df, 
        on="item_id", 
        suffixes=("_true", "_pred")
    )
    
    if len(merged_df) == 0:
        print("Error: No items matched between results and ground truth. Check item_ids.")
        return

    total_items = len(merged_df)

    correct_top_1 = (merged_df['ingredient_id_pred'] == merged_df['ingredient_id_true']).sum()
    precision_at_1 = correct_top_1 / total_items

    confidence_threshold_normalized = MATCH_THRESHOLD / 100.0
    covered_items_df = merged_df[merged_df['confidence'] >= confidence_threshold_normalized]
    coverage = len(covered_items_df) / total_items

    if len(covered_items_df) > 0:
        correctly_covered = (covered_items_df['ingredient_id_pred'] == covered_items_df['ingredient_id_true']).sum()
        precision_of_covered = correctly_covered / len(covered_items_df)
    else:
        precision_of_covered = 0.0 # Avoid division by zero

    print("\n" + "="*30)
    print("--- Evaluation Report ---")
    print(f"Matching Threshold (for Coverage): {MATCH_THRESHOLD}%")
    print(f"Total Items Evaluated: {total_items}")
    print("---")
    print(f"Precision@1 (Overall): {precision_at_1: .2%}")
    print(f"  -> {correct_top_1} / {total_items} items' top-1 match was correct.")
    print("---")
    print(f"Coverage (Confidence >= {MATCH_THRESHOLD}%): {coverage: .2%}")
    print(f"  -> {len(covered_items_df)} / {total_items} items met the threshold.")
    print("---")
    print(f"Precision of Covered Items: {precision_of_covered: .2%}")
    print(f"  -> {correctly_covered} / {len(covered_items_df)} items above threshold were correct.")
    print("="*30)

    incorrect_matches = merged_df[merged_df['ingredient_id_pred'] != merged_df['ingredient_id_true']]
    if not incorrect_matches.empty:
        print("\nIncorrect Matches:")
        print(incorrect_matches[['item_id', 'ingredient_id_true', 'ingredient_id_pred', 'confidence']].to_string())
    else:
        print("\nAll matches correct!")

if __name__ == "__main__":
    evaluate_matches()