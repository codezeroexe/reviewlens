"""Run the Suspicious Review Investigator on the phase-3 20k subset. Writes reports/."""

import time
from pathlib import Path

import pandas as pd

from batch.loader import DEMO_FILE, load_demo
from complaints.embed import embed
from suspicion import signals as S
from suspicion.score import score

N_ROWS = 20_000
REPORTS = Path("reports")


def load_context() -> pd.DataFrame:
    """customer_id and vine are not in the phase-2 schema. Read them from the same raw rows and join by review_id."""
    raw = pd.read_csv(DEMO_FILE, sep="\t", quoting=3, engine="python", on_bad_lines="skip",
                      nrows=N_ROWS, dtype=str, usecols=["review_id", "customer_id", "vine"])
    return raw.drop_duplicates("review_id")


def main() -> None:
    t0 = time.time()
    df, load_rep = load_demo(nrows=N_ROWS)
    ctx = load_context()
    df = df.assign(review_id=df["review_id"].astype(str)).merge(
        ctx.assign(review_id=ctx["review_id"].astype(str)), on="review_id", how="left")
    emb, emb_method = embed(df)

    sig = {
        "exact": S.exact_duplicates(df),
        "near": S.near_duplicates(df),
        "semantic": S.semantic_similar(df, emb),
        "promo": S.promo_repetition(df),
        "reviewer": S.reviewer_activity(df),
        "burst": S.bursts(df),
    }
    skipped = {}
    for name in ("reviewer",):
        if "__skipped__" in sig[name]:
            skipped[name] = sig[name].pop("__skipped__")
    results = score(df, sig)
    REPORTS.mkdir(exist_ok=True)
    results.to_csv(REPORTS / "suspicion_results.csv", index=False)

    counts = results["category"].value_counts().to_dict()
    per_signal = {
        "exact_duplicate": len(sig["exact"]), "near_duplicate": len(sig["near"]),
        "semantic_similar": len(sig["semantic"]), "promo_repetition": len(sig["promo"]),
        "reviewer_activity": len(sig["reviewer"]), "review_burst": len(sig["burst"]),
    }
    elapsed = round(time.time() - t0, 1)
    md = [
        "# Suspicious Review Investigator run", "",
        "**Heuristic / similarity-based signals. Not a validated fake-review classifier.**", "",
        f"- Rows processed: {len(df)} (first {N_ROWS} rows of Electronics TSV, same subset as phase 3)",
        f"- Load report: {load_rep}",
        f"- Runtime: {elapsed} s",
        f"- Embedding for semantic signal: {emb_method}",
        f"- Category counts: {counts}",
        f"- Reviews with each signal: {per_signal}",
        f"- Signals skipped: {skipped if skipped else 'none'}",
        f"- Legacy model prediction: not available (no existing detector in the project)",
        "", "## Limitations", "",
        "- No ground-truth fake labels. Signals are patterns, not proof.",
        f"- Short reviews (< {S.MIN_TOKENS} tokens) excluded from duplicate and similarity signals.",
        "- Head sample of one file. Few products have 20+ reviews, so burst checks are rare.",
        "- Semantic threshold 0.9 on MiniLM embeddings is my choice, not tuned.",
        "- Exact duplicates and semantic matches are counted as ONE 'similar text' signal (they overlap).",
        "- Promo list is the full plan list, including 'five stars'. In this data it often appears as a headline rating label, so it can flag normal reviews.",
        "- Reviewer signal: 5+ reviews by one customer on one day in this subset.",
    ]
    (REPORTS / "suspicion_run.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
