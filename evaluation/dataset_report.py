"""Dataset report (phase 8 A). Every number is computed here from the raw TSV. Writes reports/dataset_report.{md,json}."""

import json
import os
import re
from pathlib import Path

import pandas as pd

from batch.loader import DEMO_FILE, load_reviews

REPORTS = Path("reports")
N_ROWS = 20_000  # same sample as phases 3-6


def near_dup_note() -> str:
    return "exact-after-normalisation (lowercase, punctuation removed) within the sample; no fuzzy matching"


def main() -> None:
    path = Path(DEMO_FILE)
    raw = pd.read_csv(path, sep="\t", quoting=3, engine="python", on_bad_lines="skip", nrows=N_ROWS, dtype=str)
    rows_read = len(raw)
    clean, rep = load_reviews(path, nrows=N_ROWS)
    rows_retained = len(clean)
    raw_ids = raw["review_id"]
    texts = (raw["review_headline"].fillna("") + " " + raw["review_body"].fillna("")).str.strip()
    norm = texts.str.lower().str.replace(r"[^a-z0-9 ]", " ", regex=True).str.split().str.join(" ")

    rating = pd.to_numeric(raw["star_rating"], errors="coerce")
    dist = {int(k): {"count": int(v), "pct": round(100 * v / rating.notna().sum(), 2)}
            for k, v in rating.dropna().astype(int).value_counts().sort_index().items()}
    dates = pd.to_datetime(raw["review_date"], errors="coerce")
    months = dates.dt.to_period("M").nunique() if dates.notna().any() else "not available"

    missing = {c: {"count": int(raw[c].isna().sum()), "pct": round(100 * raw[c].isna().mean(), 3)} for c in raw.columns}
    counts = raw["product_id"].value_counts()

    out = {
        "file": {"path": str(path), "size_bytes": os.path.getsize(path), "sample_rows": N_ROWS},
        "rows": {"read": rows_read, "retained": rows_retained, "excluded": rows_read - rows_retained,
                 "exclusion_reasons": {k: int(v) for k, v in rep.items() if k.startswith("dropped") or k.endswith("null") or k == "bad_lines_skipped"}},
        "unique": {"products": int(raw["product_id"].nunique()), "categories": int(raw["product_category"].nunique()),
                   "review_ids": int(raw_ids.nunique()), "customers": int(raw["customer_id"].nunique()) if "customer_id" in raw else "not available"},
        "products_with_30plus_reviews": int((counts >= 30).sum()),
        "rating_distribution": dist,
        "labels": {"usefulness": {"status": "derived, see label_notes", "rule": "helpful_votes/total_votes >= 0.6 with total_votes >= 5",
                                  "labelled_rows": int(((raw["total_votes"].astype(float) >= 5)).sum())},
                   "fake_or_suspicious": "none (no labels in dataset)"},
        "missing_values": missing,
        "duplicates": {"exact_duplicate_review_ids": int(raw_ids.duplicated().sum()),
                       "exact_duplicate_texts_normalised": int(norm[norm.str.len() > 0].duplicated().sum()),
                       "near_duplicates": "not counted here; method: " + near_dup_note()},
        "date_coverage": {"min": str(dates.min().date()) if dates.notna().any() else "not available",
                          "max": str(dates.max().date()) if dates.notna().any() else "not available",
                          "distinct_months": months},
        "metadata_columns": {c: (c in raw.columns) for c in ["verified_purchase", "vine", "helpful_votes", "total_votes", "review_date", "customer_id"]},
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "dataset_report.json").write_text(json.dumps(out, indent=2, default=str))
    md = [
        "# Dataset report", "",
        f"Source: `{out['file']['path']}` ({out['file']['size_bytes']:,} bytes). Sample: first {N_ROWS:,} rows. Computed by `evaluation/dataset_report.py`.", "",
        "## Rows", "",
        f"- Read: {out['rows']['read']:,}", f"- Retained: {out['rows']['retained']:,}", f"- Excluded: {out['rows']['excluded']:,}",
        "- Exclusion reasons: " + ", ".join(f"{k} = {v}" for k, v in out["rows"]["exclusion_reasons"].items()), "",
        "## Unique values", "",
        f"- Products: {out['unique']['products']:,} ({out['products_with_30plus_reviews']} with 30+ reviews)",
        f"- Categories: {out['unique']['categories']}",
        f"- Review IDs: {out['unique']['review_ids']:,}", f"- Reviewers (customer_id): {out['unique']['customers']}", "",
        "## Rating distribution (star_rating)", "",
        "| Stars | Count | % |", "|---|---|---|",
    ] + [f"| {k} | {v['count']:,} | {v['pct']} |" for k, v in dist.items()] + [
        "", "## Labels", "",
        f"- Usefulness (derived): {out['labels']['usefulness']['labelled_rows']:,} rows with total_votes >= 5. Rule: {out['labels']['usefulness']['rule']}.",
        f"- Fake/suspicious: {out['labels']['fake_or_suspicious']}", "",
        "## Missing values", "", "| Column | Missing | % |", "|---|---|---|",
    ] + [f"| {c} | {v['count']:,} | {v['pct']} |" for c, v in missing.items()] + [
        "", "## Duplicates", "",
        f"- Exact duplicate review IDs: {out['duplicates']['exact_duplicate_review_ids']}",
        f"- Exact duplicate texts (normalised): {out['duplicates']['exact_duplicate_texts_normalised']}",
        f"- Near duplicates: {out['duplicates']['near_duplicates']}", "",
        "## Dates", "",
        f"- Min {out['date_coverage']['min']}, max {out['date_coverage']['max']}, distinct months {months}", "",
        "## Metadata present", "", "\n".join(f"- {k}: {'yes' if v else 'no'}" for k, v in out["metadata_columns"].items()),
    ]
    (REPORTS / "dataset_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:14]))


if __name__ == "__main__":
    main()
