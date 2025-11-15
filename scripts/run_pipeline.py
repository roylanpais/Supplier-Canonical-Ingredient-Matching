import pandas as pd
from tqdm import tqdm
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.matching import Matcher
from app.config import MASTER_FILE, SUPPLIER_FILE, OUTPUT_FILE, MATCH_THRESHOLD

def run_batch_matching():
    """
    Loads the supplier and master files, runs the matching pipeline
    on all supplier items, and saves the results to matches.csv.
    """
    print("Starting batch matching pipeline...")
    
    try:
        master_df = pd.read_csv(MASTER_FILE)
        master_df['ingredient_id'] = master_df['ingredient_id'].astype(str)
        supplier_df = pd.read_csv(SUPPLIER_FILE)
        supplier_df['item_id'] = supplier_df['item_id'].astype(str)
    except FileNotFoundError as e:
        print(f"Error: Data file not found. {e}")
        return
    
    print(f"Loaded {len(master_df)} master ingredients.")
    print(f"Loaded {len(supplier_df)} supplier items.")

    matcher = Matcher(master_df)
    
    results = []
    
    print("Matching items (with progress bar):")
    for row in tqdm(supplier_df.itertuples(), total=len(supplier_df), desc="Matching"):
        try:
            item_id = str(row.item_id)
            raw_name = str(row.raw_name)
        except AttributeError:
            print(f"Skipping row with missing data: {row}")
            continue

        ingredient_id, confidence = matcher.match(raw_name, threshold=MATCH_THRESHOLD)
        
        results.append({
            "item_id": item_id,
            "ingredient_id": ingredient_id,
            "confidence": confidence
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "="*30)
    print(f"Matching complete. Results saved to {OUTPUT_FILE}")
    print(f"Sample results (first 5 rows):")
    print(results_df.head().to_string())
    print("="*30)

if __name__ == "__main__":

    run_batch_matching()
