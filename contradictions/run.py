"""Run Contradiction Investigator on the same 20k-row subset as phase 3 (reuses its embedding cache)."""

import json
import time
from collections import Counter
from pathlib import Path

import pandas as pd

from batch.loader import load_demo
from complaints.embed import embed
from contradictions.aspects import ASPECTS
from contradictions.extract import _pattern, extract
from contradictions.pairs import candidate_pairs
from contradictions.report import build
from contradictions.verify import verify

N_ROWS = 20_000
NLI_MIN_SCORE = 0.9  # strict rule: NLI contradiction score >= 0.9 AND both quotes contain the same aspect keyword
REPORTS = Path("reports")


def _shared_keywords(row) -> set[str]:
    """Aspect keywords found in BOTH sentences (same word, not just same aspect group)."""
    found = []
    for kw in ASPECTS[row["aspect"]]:
        rx = _pattern([kw])
        if rx.search(row["pos_sentence"]) and rx.search(row["neg_sentence"]):
            found.append(kw)
    return set(found)


def main() -> None:
    t0 = time.time()
    df, _ = load_demo(nrows=N_ROWS)
    sentences = extract(df)
    emb, emb_method = embed(df)  # cached from phase 3 when the same subset is used
    emb_by_review = {str(r): emb[i] for i, r in enumerate(df["review_id"].astype(str))}
    pairs = candidate_pairs(sentences, emb_by_review)
    verified, method = verify(pairs)

    if method == "nli":
        nli_contra = verified[verified["nli_label"] == "contradiction"]
        shared = nli_contra.apply(lambda r: bool(_shared_keywords(r)), axis=1)
        strict_mask = nli_contra["nli_score"].ge(NLI_MIN_SCORE) & shared
        conflicts = nli_contra[strict_mask]
        loose_count = len(nli_contra)
    else:
        conflicts = verified
        loose_count = len(verified)
    reports = [build(r) for r in conflicts.to_dict(orient="records")]
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "contradictions.json").write_text(json.dumps({
        "method": method, "embedding_method": emb_method, "conflicts": reports,
        "all_pairs_checked": int(len(verified)),
        "nli_label_counts": verified["nli_label"].value_counts().to_dict() if method == "nli" else {},
        "filter": f"NLI contradiction, score >= {NLI_MIN_SCORE}, both quotes contain the same aspect keyword",
        "conflicts_before_strict_filter": loose_count,
    }, indent=2, default=str))
    pd.DataFrame(reports).drop(columns=["observed_evidence", "unknown_or_missing_context"], errors="ignore").to_csv(
        REPORTS / "contradictions.csv", index=False)

    elapsed = round(time.time() - t0, 1)
    md = [
        "# Contradiction Investigator run", "",
        "**Preliminary: no evaluation of contradiction quality yet.**", "",
        f"- Reviews: first {N_ROWS} rows of Electronics TSV (same subset as phase 3)",
        f"- Products scanned: {df['product_id'].nunique()}",
        f"- Sentences naming an aspect: {len(sentences)}",
        f"- Candidate pairs (pos vs neg, same product+aspect, different reviews): {len(pairs)}",
        f"- Verification method: {method}",
        f"- NLI label counts: {verified['nli_label'].value_counts().to_dict() if method == 'nli' else 'n/a'}",
        f"- NLI contradictions before strict filter: {loose_count}",
        f"- Filter: NLI contradiction, score >= {NLI_MIN_SCORE}, both quotes contain the same aspect keyword",
        f"- Conflicts shown after strict filter: {len(reports)}",
        f"- Runtime: {elapsed} s",
        f"- Polarity: VADER compound, positive > 0.3, negative < -0.3",
        f"- Embeddings for ranking: {emb_method}",
        "", "## Limitations", "",
        "- Aspects are keyword matches. They miss paraphrases and can match the wrong sense.",
        "- Polarity from VADER is a rough lexicon score. It can misread sarcasm and negation.",
        "- NLI model labels a sentence pair, not the product. A 'contradiction' label is a model output, not proof.",
        "- Context words are literal keyword matches inside the sentence only.",
        "- Head sample of one file. Most products have few reviews, so few pairs.",
    ]
    (REPORTS / "contradiction_run.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
