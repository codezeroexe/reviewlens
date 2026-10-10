"""Combine signals into a transparent category. Count of DIFFERENT strong signals, not a probability.

Rule: 0 signals -> No signals; 1 -> Low; 2 -> Medium; 3+ -> High.
Exact-duplicate and semantic-similarity both count as one "similar text" signal (they overlap).
Legacy model: none exists in this project (see reports/suspicion_audit.md). Field is "not available".
"""

import pandas as pd

CATEGORY = {0: "No signals", 1: "Low", 2: "Medium"}
DISCLAIMER = "This is a heuristic signal, not proof of fake activity."
LABELS = {"exact_duplicate": "exact duplicate", "near_duplicate": "near-duplicate",
          "semantic_similar": "semantic similarity", "promo_repetition": "promotional/repetitive wording",
          "reviewer_activity": "reviewer activity", "review_burst": "review burst"}


def category_for(n: int) -> str:
    return CATEGORY.get(n, "High")


def score(df: pd.DataFrame, sig: dict) -> pd.DataFrame:
    rows = []
    for rec in df.itertuples():
        rid = str(rec.review_id)
        fired = {}
        if rid in sig["exact"]:
            fired["exact_duplicate"] = sig["exact"][rid]
        if rid in sig["near"]:
            fired["near_duplicate"] = sig["near"][rid]
        if rid in sig["semantic"]:
            fired["semantic_similar"] = sig["semantic"][rid]
        if rid in sig["promo"]:
            fired["promo_repetition"] = sig["promo"][rid]
        if rid in sig["reviewer"]:
            fired["reviewer_activity"] = sig["reviewer"][rid]
        if rid in sig["burst"]:
            fired["review_burst"] = sig["burst"][rid]
        # Exact copies are also semantic matches at 1.0. Count "copied/similar text" once, not twice.
        groups = set()
        for key in fired:
            groups.add("similar_text" if key in ("exact_duplicate", "semantic_similar") else key)
        n = len(groups)
        cat = category_for(n)
        meta = (f"rating={rec.rating}; verified_purchase={rec.verified_purchase}; vine={getattr(rec, 'vine', 'n/a')}; "
                f"words={len(str(rec.review_text).split())}")
        if fired:
            parts = [f"{LABELS[k]}" for k in fired]
            explanation = (f"Flagged {cat}: " + ", ".join(parts) + ". Metadata: " + meta + ". " + DISCLAIMER)
        else:
            explanation = "No heuristic signals fired. " + DISCLAIMER
        rows.append({
            "review_id": rid, "product_id": str(rec.product_id), "category": cat, "signal_count": n,
            "signal_groups": "; ".join(sorted(groups)),
            "signals": "; ".join(LABELS[k] for k in fired), "details": str(fired) if fired else "",
            "similar_review_ids": "; ".join(_similar_ids(fired)),
            "legacy_model_prediction": "not available", "explanation": explanation,
            "rating": rec.rating, "verified_purchase": rec.verified_purchase,
            "vine": getattr(rec, "vine", None), "review_text": rec.review_text,
        })
    return pd.DataFrame(rows)


def _similar_ids(fired: dict) -> list[str]:
    ids = []
    for key in ("exact_duplicate", "near_duplicate", "semantic_similar"):
        if key in fired:
            for item in fired[key].get("similar", []):
                ids.append(item[0] if isinstance(item, tuple) else item)
    return sorted(set(ids))[:20]
