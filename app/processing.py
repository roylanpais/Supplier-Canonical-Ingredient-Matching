import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# One-time downloads for NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


# --- Constants ---

# Regex to remove size/weight/volume/pack information
SIZE_REGEX = re.compile(
    r'\b\d+[\.,]?\d*\s*(kg|g|mg|l|ml|cl|oz|lb|pack|can|bottle|bunch|ea|pc|tbl|tsp)\b',
    re.IGNORECASE
)

# Regex to remove punctuation
PUNCT_REGEX = re.compile(r'[^\w\s]')

# Synonym map: noisy/alternate -> canonical token
# This is a critical, domain-specific list that should be maintained.
SYNONYM_MAP = {
    # From supplier_items.csv
    "tomatoes": "tomato",
    "onion": "onion",
    "gralic": "garlic",  # Misspelling
    "milk full cream": "whole milk",
    "extra virgin olive oil": "olive oil",
    "jeera": "cumin",  # Synonym
    "jeera seeds": "cumin seeds",
    "white sugar": "granulated sugar",
    "plain flour": "all-purpose flour",
    "unslt": "unsalted",  # Abbreviation
    "butter unslt": "unsalted butter",
    "rice long grain": "white rice"
}

# Custom stopwords to remove, in addition to NLTK's list
CUSTOM_STOP_WORDS = {
    'extra', 'virgin', 'peeled', 'red', 'full', 'cream', 'plain', 'white',
    'long', 'grain', 'unsl', 'unslt', 'pack', 'g', 'kg', 'l', 'ml'
}

STOP_WORDS = set(stopwords.words('english')).union(CUSTOM_STOP_WORDS)
LEMMATIZER = WordNetLemmatizer()


def normalize(text: str) -> str:
    """
    Converts a raw item string into a normalized, canonical form
    for matching.
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()

    # Apply synonym replacements
    for k, v in SYNONYM_MAP.items():
        if k in text:
            text = text.replace(k, v)

    # Remove size/pack info
    text = SIZE_REGEX.sub(' ', text)
    
    # Remove punctuation
    text = PUNCT_REGEX.sub(' ', text)

    # Tokenize
    tokens = word_tokenize(text)

    # Lemmatize, remove stopwords and short tokens
    lemmatized_tokens = []
    for t in tokens:
        if t not in STOP_WORDS and len(t) > 1 and not t.isdigit():
            lemmatized_tokens.append(LEMMATIZER.lemmatize(t))

    # De-duplicate and sort to create a stable, order-independent string
    # "olive oil" and "oil olive" both become "olive oil"
    final_tokens = sorted(list(set(lemmatized_tokens)))

    return " ".join(final_tokens)