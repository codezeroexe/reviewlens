"""Load the local Amazon TSV in chunks. Bad lines are skipped and counted."""

import csv
from pathlib import Path

import pandas as pd

from batch.schema import clean_reviews, dedupe_reviews

# Local copy only. Raw TSVs are gitignored and were not found on disk in phase 1.
DEMO_FILE = Path("data/amazon_reviews_us_Electronics_v1_00.tsv")


def load_reviews(path: Path, nrows: int | None = None, chunksize: int = 50_000) -> tuple[pd.DataFrame, dict]:
    """Read TSV in chunks, clean each chunk, dedupe once at the end."""
    bad_lines = []

    def on_bad(line):
        bad_lines.append(line)
        return None

    reader = pd.read_csv(
        path, sep="\t", quoting=csv.QUOTE_NONE, engine="python",
        on_bad_lines=on_bad, chunksize=chunksize, nrows=nrows, dtype=str,
    )
    parts, totals = [], {"rows_in": 0, "dropped_empty_text": 0, "rating_set_null": 0,
                         "date_set_null": 0, "votes_set_null": 0}
    for chunk in reader:
        clean, rep = clean_reviews(chunk)
        parts.append(clean)
        for key in totals:
            totals[key] += rep[key]

    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    df, dups = dedupe_reviews(df) if "review_id" in df else (df, 0)
    totals["dropped_duplicate_review_id"] = dups
    totals["bad_lines_skipped"] = len(bad_lines)
    totals["rows_kept"] = len(df)
    return df, totals


def load_demo(nrows: int | None = None) -> tuple[pd.DataFrame, dict]:
    if not DEMO_FILE.exists():
        raise FileNotFoundError(
            f"Demo data not found at {DEMO_FILE}. Put the Amazon TSV there. "
            "No fake data is generated."
        )
    return load_reviews(DEMO_FILE, nrows=nrows)
