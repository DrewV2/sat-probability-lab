"""Transparent teaching vectors; no pretrained model or remote service required."""
from math import sqrt, isfinite
import re

FEATURES = ("algebra", "geometry", "probability", "grammar", "evidence", "data")
VOCABULARY = (
    {"algebra", "linear", "equation", "equations", "slope"},
    {"geometry", "triangle", "circle", "area", "angle"},
    {"probability", "chance", "guessing", "bernoulli", "distribution"},
    {"grammar", "punctuation", "comma", "sentence", "verb"},
    {"evidence", "reading", "inference", "passage", "claim"},
    {"data", "sql", "database", "duckdb", "query"},
)


def embed(text):
    """Six-dimensional keyword-count representation, NOT an AI embedding model."""
    words = re.findall(r"[a-z]+", text.lower())
    return [float(sum(word in vocabulary for word in words)) for vocabulary in VOCABULARY]


def cosine_similarity(a, b):
    if not a or len(a) != len(b) or any(not isfinite(v) for v in (*a, *b)):
        raise ValueError("Vectors must be nonempty, finite, and have matching dimensions.")
    norm = sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    if norm == 0:
        raise ValueError("Cosine similarity is undefined for a zero vector.")
    return sum(x*y for x,y in zip(a,b))/norm


TOPICS = [
    ("linear", "Linear equations", "algebra equation slope linear"),
    ("circles", "Circles and areas", "geometry circle area angle"),
    ("guessing", "Guessing uncertainty", "probability guessing bernoulli distribution"),
    ("commas", "Sentence boundaries", "grammar punctuation comma sentence"),
    ("claims", "Supporting claims", "reading evidence inference claim"),
    ("storage", "Analyzing attempts", "data sql database duckdb query probability"),
]
