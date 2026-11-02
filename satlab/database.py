"""DuckDB metadata, input, prediction, and vector tables for the notebooks."""
from dataclasses import asdict
import json
from pathlib import Path
import duckdb

from .model import Counts, Settings, predict_test
from .examples import example_modules
from .similarity import TOPICS, embed

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    attempt_id VARCHAR PRIMARY KEY,
    student_id VARCHAR NOT NULL,
    test_form_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    is_synthetic BOOLEAN NOT NULL,
    actual_rw INTEGER CHECK (actual_rw BETWEEN 200 AND 800 AND actual_rw % 10 = 0),
    actual_math INTEGER CHECK (actual_math BETWEEN 200 AND 800 AND actual_math % 10 = 0)
);
CREATE TABLE IF NOT EXISTS module_inputs (
    attempt_id VARCHAR REFERENCES attempts(attempt_id),
    section VARCHAR CHECK (section IN ('rw', 'math')),
    module INTEGER CHECK (module IN (1, 2)),
    confident INTEGER NOT NULL CHECK (confident >= 0),
    guess2 INTEGER NOT NULL CHECK (guess2 >= 0),
    guess3 INTEGER NOT NULL CHECK (guess3 >= 0),
    guess4 INTEGER NOT NULL CHECK (guess4 >= 0),
    fill_right INTEGER NOT NULL CHECK (fill_right >= 0),
    fill_wrong INTEGER NOT NULL CHECK (fill_wrong >= 0),
    fill_uncertain INTEGER NOT NULL CHECK (fill_uncertain >= 0),
    wrong INTEGER NOT NULL CHECK (wrong >= 0),
    route VARCHAR NOT NULL CHECK (route IN ('unknown', 'hard', 'easy')),
    PRIMARY KEY (attempt_id, section, module),
    CHECK (confident+guess2+guess3+guess4+fill_right+fill_wrong+fill_uncertain+wrong
           = CASE WHEN section='rw' THEN 27 ELSE 22 END),
    CHECK (section='math' OR fill_right+fill_wrong+fill_uncertain=0)
);
CREATE TABLE IF NOT EXISTS predictions (
    attempt_id VARCHAR REFERENCES attempts(attempt_id),
    model_version VARCHAR,
    score_status VARCHAR NOT NULL,
    low INTEGER NOT NULL, median INTEGER NOT NULL, high INTEGER NOT NULL,
    coverage DOUBLE NOT NULL,
    settings_json VARCHAR NOT NULL,
    PRIMARY KEY (attempt_id, model_version),
    CHECK (low <= median AND median <= high)
);
CREATE TABLE IF NOT EXISTS topics (
    topic_id VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, description VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS topic_embeddings (
    topic_id VARCHAR REFERENCES topics(topic_id),
    embedding_model VARCHAR,
    embedding DOUBLE[] NOT NULL,
    PRIMARY KEY (topic_id, embedding_model),
    CHECK (len(embedding)=6)
);
"""


def connect(path=":memory:"):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(path))
    connection.execute(SCHEMA)
    return connection


def seed_demo(connection):
    """Idempotent inserts of synthetic records. No actual score labels invented."""
    modules = example_modules()
    for i in range(6):
        attempt_id = f"demo-{i+1}"
        connection.execute("INSERT INTO attempts VALUES (?, ?, ?, ?, ?, NULL, NULL) ON CONFLICT DO NOTHING",
                           [attempt_id, f"synthetic-student-{i//2+1}", f"demo-form-{i%2+1}", "teaching fixture", True])
        for section, pair in modules.items():
            for module, counts in enumerate(pair, 1):
                values = asdict(counts)
                # Move confident answers into two-choice guesses to vary examples.
                values["confident"] -= i
                values["guess2"] += i
                connection.execute("INSERT INTO module_inputs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                                   [attempt_id, section, module, *values.values(), "unknown"])
    for topic_id, title, description in TOPICS:
        connection.execute("INSERT INTO topics VALUES (?, ?, ?) ON CONFLICT DO NOTHING", [topic_id, title, description])
        connection.execute("INSERT INTO topic_embeddings VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                           [topic_id, "keyword-count-v1", embed(description)])


def predict_attempt(connection, attempt_id, settings=None):
    settings = settings or Settings()
    rows = connection.execute("""
        SELECT section, module, confident, guess2, guess3, guess4,
               fill_right, fill_wrong, fill_uncertain, wrong, route
        FROM module_inputs WHERE attempt_id = ? ORDER BY section, module
    """, [attempt_id]).fetchall()
    if len(rows) != 4:
        raise ValueError("An attempt must have four complete modules.")
    modules, routes = {"rw": [], "math": []}, {}
    for section, module, *values in rows:
        modules[section].append(Counts(*values[:8]))
        if module == 2:
            routes[section] = values[8]
    result = predict_test(**modules, routes=routes, settings=settings, include_illustrative_scores=True)
    scores = result["total_score_summary"]
    connection.execute("""
        INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (attempt_id, model_version) DO UPDATE SET
        score_status=excluded.score_status, low=excluded.low, median=excluded.median,
        high=excluded.high, coverage=excluded.coverage, settings_json=excluded.settings_json
    """, [attempt_id, "illustrative-v1", result["score_status"], scores["low"], scores["median"],
          scores["high"], settings.coverage, json.dumps(asdict(settings), sort_keys=True)])
    return result


def search_topics(connection, query_vector, limit=3):
    from .similarity import cosine_similarity
    cosine_similarity(query_vector, query_vector)  # Reject zero/nonfinite vectors.
    if len(query_vector) != 6:
        raise ValueError("keyword-count-v1 requires six features.")
    if type(limit) is not int or limit <= 0:
        raise ValueError("limit must be a positive integer")
    return connection.execute("""
        SELECT t.topic_id, t.title, t.description,
               list_cosine_similarity(e.embedding, ?::DOUBLE[]) AS similarity
        FROM topics AS t JOIN topic_embeddings AS e USING (topic_id)
        WHERE e.embedding_model = 'keyword-count-v1'
        ORDER BY similarity DESC, t.topic_id LIMIT ?
    """, [query_vector, limit]).df()
