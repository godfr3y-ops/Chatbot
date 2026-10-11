"""BUSE Bot intent matching and response generation.

Uses TF-IDF over training patterns for reliable matching without a
Keras model. The legacy .h5 model is optional if present.
"""

from __future__ import annotations

import json
import logging
import pickle
import random
import re
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
INTENTS_PATH = BASE_DIR / "job_intents.json"
ERROR_THRESHOLD = 0.22
KERAS_THRESHOLD = 0.50

FALLBACK_RESPONSE = (
    "I am not sure about that yet. Try asking about admissions, fees, "
    "faculties, accommodation, library services, or campus contacts — "
    "or visit https://www.buse.ac.zw for official information."
)


def _load_intents() -> dict[str, Any]:
    with INTENTS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


intents = _load_intents()
intent_by_tag = {item["tag"]: item for item in intents["intents"]}

training_corpus: list[str] = []
training_tags: list[str] = []
for item in intents["intents"]:
    if item["tag"] == "unknown":
        continue
    for pattern in item["patterns"]:
        training_corpus.append(_normalize(pattern))
        training_tags.append(item["tag"])

vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
pattern_matrix = vectorizer.fit_transform(training_corpus)

# Optional legacy Keras model (used only when available and confident)
keras_model = None
keras_words = None
keras_classes = None
try:
    model_path = BASE_DIR / "chatbot_model.h5"
    words_path = BASE_DIR / "words.pkl"
    classes_path = BASE_DIR / "classes.pkl"
    if model_path.exists() and words_path.exists() and classes_path.exists():
        from keras.models import load_model  # type: ignore
        from nltk.stem import WordNetLemmatizer
        import nltk
        import numpy as np

        nltk.download("punkt", quiet=True)
        nltk.download("wordnet", quiet=True)
        keras_model = load_model(str(model_path))
        keras_words = pickle.load(words_path.open("rb"))
        keras_classes = pickle.load(classes_path.open("rb"))
        lemmatizer = WordNetLemmatizer()
        logger.info("Loaded optional Keras model for hybrid scoring")
except Exception as exc:  # noqa: BLE001 - optional path
    logger.info("Keras model unavailable; using TF-IDF matcher only (%s)", exc)
    keras_model = None


def _keras_predict(sentence: str) -> list[dict[str, str]]:
    if keras_model is None or keras_words is None or keras_classes is None:
        return []
    import numpy as np
    from nltk.stem import WordNetLemmatizer
    import nltk

    lemmatizer = WordNetLemmatizer()
    tokens = nltk.word_tokenize(sentence)
    tokens = [lemmatizer.lemmatize(word.lower()) for word in tokens]
    bag = [0] * len(keras_words)
    for token in tokens:
        for index, word in enumerate(keras_words):
            if word == token:
                bag[index] = 1
    result = keras_model.predict(np.array([bag]), verbose=0)[0]
    ranked = [[i, score] for i, score in enumerate(result) if score > KERAS_THRESHOLD]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return [
        {"intent": keras_classes[i], "probability": str(score), "source": "keras"}
        for i, score in ranked
    ]


_STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "to", "of", "and",
    "or", "in", "on", "for", "at", "by", "with", "about", "me", "my", "your",
    "you", "i", "we", "what", "where", "when", "who", "how", "tell", "please",
    "can", "do", "does", "did", "like", "from", "this", "that", "it",
}


def _content_tokens(text: str) -> set[str]:
    return {token for token in text.split() if token not in _STOPWORDS and len(token) > 2}


def predict_class(sentence: str) -> list[dict[str, str]]:
    """Return ranked intent predictions for a user message."""
    normalized = _normalize(sentence)
    if not normalized:
        return [{"intent": "unknown", "probability": "0.0", "source": "empty"}]

    query_vec = vectorizer.transform([normalized])
    scores = cosine_similarity(query_vec, pattern_matrix)[0]
    query_tokens = _content_tokens(normalized)

    # Aggregate best score per tag, with a content-token overlap boost so
    # distinctive words like "accommodation" or "library" win over generic phrasing.
    tag_scores: dict[str, float] = {}
    for index, (tag, score) in enumerate(zip(training_tags, scores)):
        pattern_tokens = _content_tokens(training_corpus[index])
        overlap = len(query_tokens & pattern_tokens)
        boosted = float(score) + (0.18 * overlap)
        if query_tokens and pattern_tokens and query_tokens.issubset(pattern_tokens):
            boosted += 0.12
        if boosted > tag_scores.get(tag, 0.0):
            tag_scores[tag] = boosted

    ranked_tfidf = sorted(tag_scores.items(), key=lambda item: item[1], reverse=True)
    best_score = ranked_tfidf[0][1] if ranked_tfidf else 0.0
    tfidf_predictions = [
        {"intent": tag, "probability": f"{score:.4f}", "source": "tfidf"}
        for tag, score in ranked_tfidf[:3]
        if score >= ERROR_THRESHOLD
    ]

    keras_predictions = _keras_predict(sentence)

    if tfidf_predictions:
        primary = tfidf_predictions
    else:
        primary = [{"intent": "unknown", "probability": f"{best_score:.4f}", "source": "tfidf"}]

    # Prefer Keras only when it is more confident than TF-IDF and the tag still exists
    if keras_predictions:
        keras_best = float(keras_predictions[0]["probability"])
        tfidf_best = float(primary[0]["probability"])
        keras_tag = keras_predictions[0]["intent"]
        if keras_tag in intent_by_tag and keras_best >= max(KERAS_THRESHOLD, tfidf_best):
            return keras_predictions

    return primary


def get_response(predictions: list[dict[str, str]], intents_json: dict[str, Any] | None = None) -> str:
    """Pick a response for the top predicted intent."""
    intents_json = intents_json or intents
    if not predictions:
        return FALLBACK_RESPONSE

    tag = predictions[0]["intent"]
    for item in intents_json["intents"]:
        if item["tag"] == tag:
            return random.choice(item["responses"])
    return FALLBACK_RESPONSE


def chatbot_response(msg: str) -> str:
    """Public API used by the Flask app."""
    try:
        predictions = predict_class(msg)
        if predictions[0]["intent"] == "unknown":
            return FALLBACK_RESPONSE
        return get_response(predictions, intents)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to generate response: %s", exc)
        return "Sorry, an error occurred. Please try again."


def list_topics(limit: int = 8) -> list[dict[str, str]]:
    """Return quick-reply chips with display labels and askable questions."""
    preferred = [
        ("howtoapply", "How to apply", "How to apply to BUSE"),
        ("feesstructure", "Fees", "What is the fees structure"),
        ("faculty", "Faculties", "What faculties are available at BUSE"),
        ("accommodation", "Accommodation", "Tell me about accommodation"),
        ("entryrequirements", "Entry requirements", "What are the entry requirements for BUSE"),
        ("campuslife", "Campus life", "What is campus life like"),
        ("librarylocation", "Library", "Where is the library"),
        ("contact", "Contact", "How can I contact BUSE"),
        ("backgroundhistory", "About BUSE", "Tell me about BUSE"),
        ("internationalstudents", "International students", "Information for international students"),
    ]
    topics: list[dict[str, str]] = []
    for tag, label, question in preferred:
        if tag in intent_by_tag:
            topics.append({"label": label, "question": question})
        if len(topics) >= limit:
            break
    return topics
