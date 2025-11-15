# **Ingredient Matching API**

A fuzzy matching pipeline and FastAPI service to map supplier items to a canonical ingredient list.

This project provides a complete solution for entity resolution, including a high-performance matching pipeline, a real-time API endpoint, batch processing, and an evaluation suite.

## **Table of Contents**

* How it Works: The Matching Pipeline
* Project Structure
* Running with Docker (Recommended)
* Local Development Setup
* API Endpoints
* How to Use the Scripts
  1. Running the Batch Pipeline
  2. Evaluating Match Accuracy
* Running Tests
* Configuration \& Maintenance
* Design Rationale

## **How it Works: The Matching Pipeline**

The core of this project is a hybrid matching strategy that is both performant and interpretable. The process for matching a string like "gralic peeled 100 g" is as follows:

1. **Normalization (app/processing.py):** The raw string is cleaned and standardized.

2. **Blocking (app/matching.py):** To avoid comparing against all 10,000s of master ingredients, we first find likely candidates.

   * An "inverted index" (a dictionary) is built on startup, mapping normalized tokens.
   * Looking up the token instantly gives the candidate set.
   * This reduces the search space from N*M to N*~1.

3. **Scoring (app/matching.py):** Finally, the normalized query is scored against the normalized candidates.

   * fuzzywuzzy.token\_set\_ratio is used.
   * This ratio is robust to word order and misspellings.
   * The best-scoring candidate is returned as the match.

## **Project Structure**

.  
├── app/  
│   ├── main.py         # FastAPI app (startup logic, /match endpoint)  
│   ├── matching.py     # Core Matcher class (blocking/scoring)  
│   ├── processing.py   # Normalization pipeline (synonyms, regex)  
│   ├── config.py       # File paths, thresholds  
│   └── models.py       # Pydantic request/response models  
├── data/  
│   ├── ingredients\_master.csv  # Canonical list  
│   ├── supplier\_items.csv      # Noisy data to be matched  
│   └── ground\_truth.csv        # Correct matches (for evaluation)  
├── scripts/  
│   ├── run\_pipeline.py # Script to generate matches.csv  
│   └── evaluate.py     # Script to report precision/coverage  
├── tests/  
│   ├── test\_api.py         # Integration tests for the API  
│   ├── test\_matching.py    # Unit tests for the Matcher  
│   └── test\_processing.py  # Unit tests for the normalization  
├── Dockerfile              # Production Docker build  
├── requirements.txt        # Python dependencies  
├── DECISIONS.md            # Critical doc: Why this design was chosen  
└── README.md               # This file

## **Running with Docker (Recommended)**

This is the simplest, most reliable way to run the production application.

1. **Build the Docker Image:**  
   docker build -t ingredient-matcher .
2. **Run the Docker Container:**  
   docker run -p 8000:8000 ingredient-matcher

   The API will be running on http://localhost:8000.

3. Test the Endpoint:  
   Open another terminal and use curl (or any API client) to test:  
   curl -X POST "http://localhost:8000/match" \\  
   -H "Content-Type: application/json" \\  
   -d '{"raw\_name": "gralic peeled 100g"}'

   You should receive a response:  
   {  
   "ingredient\_id": "3",  
   "confidence": 1.0  
   }

   ## **Local Development Setup**

   For actively developing or modifying the code.

1. **Clone the Repository (if you haven't):**  
   git clone <your-repo-url>  
   cd <repo-name>
2. **Create a Virtual Environment:**  
   python -m venv venv  
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
3. **Install Dependencies:**  
   pip install -r requirements.txt
4. **Run the Development Server:**  
   uvicorn app.main:app --reload

   The API will be running on http://localhost:8000. The --reload flag automatically restarts the server when you change code.

   ## **API Endpoints**

   The server provides two main endpoints:

   ### **GET /**

* **Summary:** A simple health check.
* **Response (200 OK):**  
  {  
  "status": "ok",  
  "message": "Ingredient Matching API is running."  
  }

  ### **POST /match**

* **Summary:** Matches a single raw item name to the best canonical ingredient.
* **Request Body:**  
  {  
  "raw\_name": "plain flour 1kg"  
  }
* **Response (200 OK):**  
  {  
  "ingredient\_id": "8",  
  "confidence": 1.0  
  }
* **Response (Empty Query):**  
  {  
  "ingredient\_id": null,  
  "confidence": 0.0  
  }

  ## **How to Use the Scripts**

  These scripts are intended to be run from your local machine (after following the Local Development Setup).

  ### **1. Running the Batch Pipeline**

  This script runs all items from data/supplier\_items.csv through the matcher and produces the matches.csv output file.

  python scripts/run\_pipeline.py

  **Output:**

  Starting batch matching pipeline...  
  Loaded 10 master ingredients.  
  Loaded 10 supplier items.  
  Matching items (with progress bar):  
  Matching: 100%|██████████| 10/10 \[00:00<00:00, 482.90it/s]

  ==============================  
  Matching complete. Results saved to matches.csv  
  Sample results (first 5 rows):  
  item\_id ingredient\_id  confidence  
  0     A01             1         1.0  
  1     A02             2         1.0  
  2     A03             3         1.0  
  3     A04             4         1.0  
  4     A05             5         1.0  
  ==============================

  ### **2. Evaluating Match Accuracy**

  This script compares the matches.csv file (generated above) to the data/ground\_truth.csv file and reports on the pipeline's accuracy.

  python scripts/evaluate.py

  **Output:**

  Running evaluation...

  ==============================  
  --- Evaluation Report ---  
  Matching Threshold (for Coverage): 70%  
  Total Items Evaluated: 10  
  ---  
  Precision@1 (Overall):  100.00%  
  -> 10 / 10 items' top-1 match was correct.  
  ---  
  Coverage (Confidence >= 70%):  100.00%  
  -> 10 / 10 items met the threshold.  
  ---  
  Precision of Covered Items:  100.00%  
  -> 10 / 10 items above threshold were correct.  
  ==============================

  All matches correct!

  ## **Running Tests**

  To ensure the code is working as expected and that new changes don't break existing functionality, run the full test suite.

  pytest

  This will discover and run all tests in the tests/ directory.

  ## **Configuration \& Maintenance**

  The most important part of maintaining and improving this pipeline is the **Synonym Map**.

* **File:** app/processing.py
* **Variable:** SYNONYM\_MAP

  This dictionary is the "human-in-the-loop" brain of the system. It is used to correct common misspellings, abbreviations, and domain-specific synonyms *before* matching.

  \# app/processing.py  
  SYNONYM\_MAP = {  
  # Misspelling  
  "gralic": "garlic",  
  # Synonym  
  "jeera": "cumin",  
  # Abbreviation  
  "unslt": "unsalted",  
  # Domain-specific  
  "plain flour": "all-purpose flour",  
  ...  
  }

  **Workflow for Improvement:**

1. Run the batch pipeline (scripts/run\_pipeline.py).
2. Open matches.csv and sort by confidence (ascending).
3. Look at the low-confidence matches. If you see a supplier item like "caster sugar" that failed to match "Granulated Sugar", you've found a new synonym.
4. Add a new entry to SYNONYM\_MAP: "caster sugar": "granulated sugar".
5. Re-run the pipeline and evaluation to see the score improve.

   ## **Design Rationale**

   For a detailed explanation of *why* this architecture was chosen (e.g., Hybrid Pipeline vs. Embeddings, token\_set\_ratio, trade-offs, and failure modes), please see the full design document: DECISIONS.md

   

