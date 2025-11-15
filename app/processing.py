import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

SIZE_REGEX = re.compile(
    r'\b\d+[\.,]?\d*\s*(kg|g|mg|l|ml|cl|oz|lb|pack|can|bottle|bunch|ea|pc|tbl|tsp)\b',
    re.IGNORECASE
)

PUNCT_REGEX = re.compile(r'[^\w\s]')

SYNONYM_MAP = {
    "milk full cream": "whole milk",
    "extra virgin olive oil": "olive oil",
    "jeera seeds": "cumin seeds",
    "white sugar": "granulated sugar",
    "plain flour": "all-purpose flour",
    "unslt": "unsalted",  # Abbreviation
    "butter unslt": "unsalted butter",
    "rice long grain": "white rice",
    "jeera": "cumin",  # Synonym
    "tomatoes": "tomato",
    "onion": "onion",
    "gralic": "garlic",  # Misspelling
}

CUSTOM_STOP_WORDS = {
    'extra', 'virgin', 'peeled', 'red', 'full', 'cream', 'plain', 'white',
    'long', 'grain', 'unsl', 'unslt', 'pack', 'g', 'kg', 'l', 'ml', 'bottle'
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

    for k, v in SYNONYM_MAP.items():
        if k in text:
            text = text.replace(k, v)

    text = SIZE_REGEX.sub(' ', text)
    text = PUNCT_REGEX.sub(' ', text)

    tokens = word_tokenize(text)

    lemmatized_tokens = []
    for t in tokens:
        if t not in STOP_WORDS and len(t) > 1 and not t.isdigit():
            lemmatized_tokens.append(LEMMATIZER.lemmatize(t))

    final_tokens = sorted(list(set(lemmatized_tokens)))

    return " ".join(final_tokens)
