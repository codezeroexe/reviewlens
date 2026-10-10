"""Build insights from phase 2-5 outputs. Writes reports/insights.json and reports/insights_run.md."""

import json
import time
from pathlib import Path

import pandas as pd

from batch.loader import load_demo
from contradictions.extract import extract
from insights import generators as G
from insights.models import check_excerpts
from insights.rank import rank

REPORTS = Path("reports")
INPUTS = [REPORTS / "complaint_clusters.json", REPORTS / "complaint_assignments.csv",
          REPORTS / "suspicion_results.csv", REPORTS / "contradictions.json"]
N_ROWS = 20_000


def build() -> dict:
    t0 = time.time()
    df, _ = load_demo(nrows=N_ROWS)
    texts = dict(zip(df["review_id"].astype(str), df["review_text"]))
    clusters = json.loads((REPORTS / "complaint_clusters.json").read_text())["clusters"]
    assign = pd.read_csv(REPORTS / "complaint_assignments.csv", dtype={"review_id": str, "product_id": str})
    susp = pd.read_csv(REPORTS / "suspicion_results.csv", dtype={"review_id": str, "product_id": str}, keep_default_na=False)
    sentences = extract(df)

    gens = {
        "common_problem": G.common_problem(assign, clusters),
        "experience_gap": G.experience_gap(sentences, texts),
        "informative_evidence": G.informative_evidence(),
        "emerging": G.emerging(df),
        "comparison": G.comparison(df),
        "quality_warning": G.quality_warning(df, susp),
    }
    found, omitted = [], {}
    for name, (items, reason) in gens.items():
        for ins in items:
            check_excerpts(ins, texts)
        found += items
        if not items:
            omitted[name] = reason
    ranked = rank(found)
    from insights.rank import overview
    top = overview(ranked)
    out = {"overview": top, "all": ranked, "omitted": omitted,
           "note": None if len(top) >= 3 else f"Only {len(top)} insight(s) qualified. Omitted types: {list(omitted)}",
           "inputs": {str(p): p.stat().st_mtime for p in INPUTS},
           "built_seconds": round(time.time() - t0, 1)}
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "insights.json").write_text(json.dumps(out, indent=2, default=str))

    per_type = pd.Series([i["type"] for i in ranked]).value_counts().to_dict() if ranked else {}
    md = [
        "# Insight engine run", "",
        f"- Runtime: {out['built_seconds']} s",
        f"- Reviews in base: {len(df)} (first {N_ROWS} rows; same subset as phases 3-5)",
        f"- Insights generated per type: {per_type}",
        f"- Overview shown: {len(top)}",
        f"- Omitted types and reasons:",
    ] + [f"  - {k}: {v}" for k, v in omitted.items()] + [
        "", "## Limitations", "",
        "- One week of data (2015-08-25 to 2015-08-31): no meaningful time trend.",
        "- Usefulness is not available (no model output). Not claimed.",
        "- Complaint clusters are preliminary (HDBSCAN found 2 clusters; one is a generic catch-all).",
        "- Quality warnings are similarity signals, not proof of manipulation.",
    ]
    (REPORTS / "insights_run.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return out


if __name__ == "__main__":
    build()
