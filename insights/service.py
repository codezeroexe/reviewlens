"""Overview, drill-down, and evidence. Cache in reports/insights.json; rebuild only when an input file changed."""

import json
import threading

from complaints.service import assignments
from insights.run import INPUTS, REPORTS, build

CACHE = REPORTS / "insights.json"


_build_lock = threading.Lock()


def _fresh() -> dict:
    """Cached insights, rebuilt when an input file changed. One rebuild at a time; others wait and reuse it."""
    def stale():
        if not CACHE.exists():
            return None
        cached = json.loads(CACHE.read_text())
        current = {str(p): p.stat().st_mtime for p in INPUTS if p.exists()}
        return cached if cached.get("inputs") == current else None

    cached = stale()
    if cached:
        return cached
    with _build_lock:
        return stale() or build()


def get_overview() -> dict:
    d = _fresh()
    return {"insights": d["overview"], "note": d["note"], "omitted": d["omitted"],
            "footnotes": ["Suspicion = warning signal, not proof.", "A usefulness prediction is not available in this app."]}


def get_all(type: str | None = None) -> list[dict]:
    items = _fresh()["all"]
    return [i for i in items if type is None or i["type"] == type]


def get_evidence(insight_id: str) -> list[dict]:
    d = _fresh()
    ins = next((i for i in d["all"] if i["id"] == insight_id), None)
    if ins is None:
        raise KeyError(insight_id)
    rows = assignments()
    f = ins["evidence_ref"]["filters"]
    if "cluster_id" in f:
        sel = rows[rows["cluster_id"] == f["cluster_id"]]
    elif "products" in f:
        sel = rows[rows["product_id"].isin(f["products"])]
    elif "product_id" in f:
        sel = rows[rows["product_id"] == f["product_id"]]
    else:
        sel = rows.iloc[0:0]
    return sel[["review_id", "product_id", "rating", "status", "review_text"]].head(200).to_dict(orient="records")
