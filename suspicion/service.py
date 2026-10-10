"""Service: investigate, get_similar, dismiss. Reads saved results; no frontend dependency."""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPORTS = Path("reports")
DISMISS_PATH = Path("data/dismissed_flags.json")
_lock = threading.Lock()


def get_results() -> pd.DataFrame:
    path = REPORTS / "suspicion_results.csv"
    if not path.exists():
        raise FileNotFoundError("Run suspicion/run.py first.")
    return pd.read_csv(path, dtype={"review_id": str, "product_id": str, "similar_review_ids": str})


def get_similar(review_id: str) -> list[dict]:
    df = get_results()
    row = df[df["review_id"] == str(review_id)]
    if row.empty:
        return []
    ids = [i for i in str(row.iloc[0]["similar_review_ids"]).split("; ") if i and i != "nan"]
    return df[df["review_id"].isin(ids)][["review_id", "rating", "review_text"]].to_dict(orient="records")


def list_dismissed() -> dict:
    if not DISMISS_PATH.exists():
        return {}
    return json.loads(DISMISS_PATH.read_text())


def dismiss(review_id: str, note: str = "") -> dict:
    """Mark a flag as dismissed. The flag row stays in the results; only the dismissed marker is added."""
    if not str(review_id).strip():
        raise ValueError("review_id is required.")
    with _lock:  # read-modify-write, then atomic replace so a crash never leaves half a file
        data = list_dismissed()
        data[str(review_id)] = {"note": note, "dismissed_at": datetime.now(timezone.utc).isoformat()}
        DISMISS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = DISMISS_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        os.replace(tmp, DISMISS_PATH)
    return data[str(review_id)]
