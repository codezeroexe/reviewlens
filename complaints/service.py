"""Two functions the frontend calls (through server.py). Reads saved report files; no model load."""

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from complaints.cluster import cluster
from complaints.embed import embed
from complaints.summarize import summarize

REPORTS = Path("reports")


@lru_cache(maxsize=2)
def _read_assignments(path: str, mtime: float) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"review_id": str, "product_id": str})


def assignments() -> pd.DataFrame:
    """The per-review cluster table. Cached until the file changes, so each click does not re-parse 20k rows."""
    path = REPORTS / "complaint_assignments.csv"
    if not path.exists():
        raise FileNotFoundError("Run complaints/run.py first.")
    return _read_assignments(str(path), path.stat().st_mtime)


def discover(df: pd.DataFrame) -> tuple[list[dict], pd.DataFrame, dict]:
    emb, method = embed(df)
    assigned, cluster_method = cluster(df, emb)
    clusters, meta = summarize(assigned, f"{method}; clustering: {cluster_method}")
    return clusters, assigned, meta


def get_cluster_reviews(cluster_id: int) -> list[dict]:
    df = assignments()
    rows = df[df["cluster_id"] == int(cluster_id)]
    return rows.to_dict(orient="records")


def get_clusters() -> dict:
    path = REPORTS / "complaint_clusters.json"
    if not path.exists():
        raise FileNotFoundError("Run complaints/run.py first.")
    return json.loads(path.read_text())


def get_unclustered_reviews(limit: int = 200) -> list[dict]:
    df = assignments()
    rows = df[df["status"] == "unclustered"]
    return rows.head(limit).to_dict(orient="records")
