"""Run Complaint Discovery on the first N rows of the local Electronics TSV. Writes reports/."""

import time
from pathlib import Path

import pandas as pd

from batch.loader import load_demo
from complaints.service import discover

N_ROWS = 20_000
REPORTS = Path("reports")


def main() -> None:
    t0 = time.time()
    df, load_rep = load_demo(nrows=N_ROWS)
    clusters, assigned, meta = discover(df)
    REPORTS.mkdir(exist_ok=True)

    import json
    (REPORTS / "complaint_clusters.json").write_text(json.dumps({"meta": meta, "clusters": clusters}, indent=2))
    pd.DataFrame([{k: v for k, v in c.items() if k != "representative_reviews"} | {
        "sentiment_pos_pct": c["sentiment_mix"]["positive_pct"],
        "sentiment_mixed_pct": c["sentiment_mix"]["mixed_pct"],
        "sentiment_neg_pct": c["sentiment_mix"]["negative_pct"]} for c in clusters]
    ).drop(columns=["sentiment_mix"]).to_csv(REPORTS / "complaint_clusters.csv", index=False)
    assigned[["review_id", "product_id", "product_category", "rating", "review_text",
              "status", "cluster_id", "similarity", "ambiguous"]].to_csv(
        REPORTS / "complaint_assignments.csv", index=False)

    elapsed = round(time.time() - t0, 1)
    md = [
        "# Complaint Discovery run", "",
        "**PRELIMINARY - cluster quality not yet evaluated**", "",
        f"- Input: first {N_ROWS} rows of `data/amazon_reviews_us_Electronics_v1_00.tsv` (head sample, not random)",
        f"- Rows read after cleaning: {len(df)} (load report: {load_rep})",
        f"- Runtime: {elapsed} s",
        f"- Embedding method: {meta['embedding_method']}",
        f"- Complaint rule: {meta['complaint_rule']}",
        f"- Clusters: {meta['cluster_count']}",
        f"- Clustered rows: {meta['clustered']}",
        f"- Unclustered rows (HDBSCAN noise or far from centroid): {meta['unclustered']}",
        f"- Not complaint (rating 4-5, out of scope): {meta['not_complaint']}",
        f"- In skipped small groups (<30 reviews): {meta['skipped_small_group']}",
        "", "## Limitations", "",
        f"- Embedding: {meta['embedding_method']}. " + ("Fallback matches words, not meaning." if "fallback" in meta["embedding_method"] else "Model is small (MiniLM-L6); quality not checked."),
        "- Head sample of one file, not a random sample.",
        "- Sentiment is a rating proxy. Complaint rule is rating <= 3, so the 'positive' share is 0 by design.",
        "- Usefulness and suspicious stats are not available (no model output).",
        "- No cluster quality evaluation yet (no labels, no silhouette run).",
        "- All products are one category (Electronics), so one group.",
    ]
    (REPORTS / "complaint_run.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
