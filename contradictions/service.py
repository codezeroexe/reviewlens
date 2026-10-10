"""Service interface. Reads saved reports and the phase-3 assignments file. No frontend dependency."""

import json
from pathlib import Path

REPORTS = Path("reports")


def find_contradictions(product_id: str | None = None, aspect: str | None = None) -> list[dict]:
    path = REPORTS / "contradictions.json"
    if not path.exists():
        raise FileNotFoundError("Run contradictions/run.py first.")
    items = json.loads(path.read_text())["conflicts"]
    if product_id:
        items = [i for i in items if i["product_id"] == product_id]
    if aspect:
        items = [i for i in items if i["aspect"] == aspect]
    return items


def get_review(review_id: str) -> dict | None:
    from complaints.service import assignments
    df = assignments()
    rows = df[df["review_id"] == str(review_id)]
    return None if rows.empty else rows.iloc[0].to_dict()


def pair_count(items: list[dict]) -> int:
    """Unique review pairs. One pair can appear under two aspects."""
    return len({(i["observed_evidence"]["positive"]["review_id"], i["observed_evidence"]["negative"]["review_id"]) for i in items})
