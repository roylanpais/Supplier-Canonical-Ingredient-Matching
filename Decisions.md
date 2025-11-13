# **Design Decisions: Supplier-Ingredient Matching Pipeline**

This document outlines the technical decisions, trade-offs, and architecture for the fuzzy matching pipeline.

## **1\. Core Matching Strategy**

The core problem is to match noisy, multi-token strings (supplier items) against a clean, canonical list (master ingredients). The chosen strategy is a **Hybrid Pipeline** combining **Normalization**, **Token-based Blocking**, and **Fuzzy Scoring**.

This approach was chosen over a pure embedding-based (e.g., SBERT) or a simple fuzzy search (e.g., fuzzywuzzy alone) for the following reasons:

* **Interpretability & Control (Pro):** The hybrid approach is transparent. We can see *why* a match failed (e.g., normalization, synonym missing). An embedding model is a black box.  
* **Domain-Specific Noise (Pro):** Our pipeline excels at removing specific, non-semantic noise like "1kg", "500ml", "pack". This noise would pollute a text embedding, pushing "Tomato 1kg" and "Tomato 500g" apart in vector space.  
* **Performance (Pro):** The blocking step drastically reduces the N\*M comparison problem, making it far faster than a brute-force search.  
* **Lightweight (Pro):** It relies on lighter libraries (nltk, fuzzywuzzy) compared to heavy-duty transformers (sentence-transformers).

### **1.1. Step 1: Normalization (app/processing.py)**

This is the most critical step. The goal is to create a "canonical" representation for both supplier and master items.

1. **Lowercase:** Converts all text to a single case.  
2. **Synonym Replacement:** A manually curated SYNONYM\_MAP (e.g., {"jeera": "cumin", "plain flour": "all-purpose flour"}) is applied. This is a powerful, high-precision way to handle domain-specific synonyms.  
3. **Regex-based Noise Removal:** A regex (SIZE\_REGEX) removes all package size and unit information (e.g., "1kg", "500 ml", "2.5oz", "pack").  
4. **Punctuation Removal:** All non-alphanumeric characters are removed.  
5. **Tokenization & Stopword Removal:** The string is tokenized. Common English stopwords (from nltk) and a CUSTOM\_STOP\_WORDS set (e.g., "extra", "virgin", "peeled") are removed.  
6. **Lemmatization:** Tokens are reduced to their dictionary form (e.g., "tomatoes" \-\> "tomato") using WordNetLemmatizer.  
7. **Final Form:** Tokens are de-duplicated and sorted alphabetically (e.g., "oil olive" \-\> "olive oil") to create a stable, order-independent string.

Trade-off: No Automated Spell-Correction:  
I explicitly avoided using a library like TextBlob for automated spelling correction.

* **Reason:** fuzzywuzzy itself is highly robust to misspellings. More importantly, automated correctors are slow and can be *incorrect* (e.g., it might "correct" a valid brand name or an abbreviation like "unslt" to "insult").  
* **Solution:** We handle common misspellings/abbreviations in the SYNONYM\_MAP (e.g., {"unslt": "unsalted", "gralic": "garlic"}), which is safer and more precise.

### **1.2. Step 2: Blocking (app/matching.py)**

To avoid comparing every supplier item to every master item (N\*M), we use a blocking strategy.

* **Method:** An **inverted index** (dict\[str, set\[str\]\]) is built from the *normalized* master list. Each normalized token maps to the set of ingredient\_ids that contain it.  
  * {"tomato": {"1"}, "onion": {"2"}, ...}  
* **Process:** When a new raw\_name comes in, it's normalized (e.g., "gralic peeled 100g" \-\> "garlic"). We look up its tokens ("garlic") in the index to get a small set of candidates (just {"3"}).  
* **Fallback:** If no tokens produce any candidates (a very noisy item), we fall back to searching the *entire* master list. This ensures we always find a match, but it is slower.

### **1.3. Step 3: Scoring (app/matching.py)**

Once we have a small set of candidates, we use a more precise (and expensive) scoring function.

* **Algorithm:** fuzzywuzzy.token\_set\_ratio.  
* **Why:** This function is perfect for our use case. It tokenizes, sorts, and finds the ratio of common tokens.  
  * It's robust to word order: score("red onion", "onion red") \= 100\.  
  * It's robust to subset/superset strings: score("olive oil", "extra virgin olive oil") \= 100\.  
  * It's robust to misspellings: score("garlic", "gralic") is high.

## **2\. API Design (app/main.py)**

* **Endpoint:** POST /match  
* **Request:** {"raw\_name": "..."}  
* **Response:** {"ingredient\_id": "...", "confidence": ...}  
* **Behavior:** The endpoint returns the **single best match** found, along with its confidence score \[0, 1\]. It does *not* filter by a threshold. This design choice puts the power in the hands of the client, which can then decide if the confidence score is high enough for its own business logic.  
* **On-Startup Loading:** The Matcher class and all master data are loaded into memory once on application startup. This ensures that all /match requests are extremely fast, as they only perform normalization and scoring, not data loading.

## **3\. Evaluation (scripts/evaluate.py)**

* **Ground Truth:** A data/ground\_truth.csv file was created to enable evaluation.  
* **Metrics:**  
  * **Precision@1:** What percentage of *all* supplier items were correctly mapped to their single best match? This is the primary measure of accuracy.  
  * **Coverage:** What percentage of items received a confidence score *above* the defined MATCH\_THRESHOLD? This measures how many matches the pipeline "trusts".  
  * **Precision of Covered:** Of the items that met the confidence threshold, what percentage were correct? This tells us how reliable the MATCH\_THRESHOLD is.

## **4\. Failure Modes & Future Improvements**

* **Unknown Synonyms:** The pipeline's accuracy for synonyms (e.g., "caster sugar" vs. "granulated sugar") is 100% dependent on the SYNONYM\_MAP.  
  * **Mitigation:** This map is the most important piece of "human-in-the-loop" maintenance. A process should be built to review low-confidence matches to discover new synonyms.  
* **Ambiguity:** The model has no way to distinguish between "Chicken Breast (Raw)" and "Chicken (Cooked)". If both were in the master list, it might match ambiguously.  
  * **Mitigation:** The master list must be well-defined. For more complex cases, the model would need to be expanded to consider other features, or the master list would need more specific names.  
* **Performance Fallback:** If many queries are extremely noisy and fail to match any tokens in the blocking index, they will trigger the "search all" fallback, which is slow.  
  * **Mitigation:** Monitor logs for this fallback. It indicates that the normalization or synonym map needs improvement.