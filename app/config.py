from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory
DATA_DIR = BASE_DIR / "data"

# Input and Output files
MASTER_FILE = DATA_DIR / "ingredients_master.csv"
SUPPLIER_FILE = DATA_DIR / "supplier_items.csv"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.csv"
OUTPUT_FILE = BASE_DIR / "matches.csv"

# Confidence threshold for evaluation (score 0-100)
# A match is "covered" if its confidence is >= this value.
MATCH_THRESHOLD = 70