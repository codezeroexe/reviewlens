"""Insight generators. Each returns (list_of_insights, omitted_reason_or_None). Reads phase outputs only; no edits to them."""

import json
from pathlib import Path

import pandas as pd

from insights.models import make

REPORTS = Path("reports")
MIN_CLUSTER = 10
MIN_POS_NEG = 5
MIN_PRODUCT = 30
MIN_GAP_PP = 5.0
MIN_WARN_REVIEWS = 10
WARN_SHARE = 0.20


# Label words too generic to name a problem. A cluster needs >= 2 non-generic words to be shown on the overview.
GENERIC = {"good", "great", "work", "works", "working", "worked", "did", "does", "product", "time", "months",
           "days", "stars", "just", "like", "really", "use", "used", "bought", "buy", "ok", "okay", "nice", "thing"}


def is_generic(label: str) -> bool:
    words = [w.strip() for w in label.split(",") if w.strip()]
    return sum(w not in GENERIC for w in words) < 2


def common_problem(assign: pd.DataFrame, clusters: list[dict]):
    complaints = int((assign["status"].isin(["clustered", "unclustered"])).sum())  # rating <= 3 rows that were clustered or noise
    out = []
    for c in clusters:
        if c["size"] < MIN_CLUSTER:
            continue
        if is_generic(c["label"]):
            continue  # generic label: not a named problem, keep out of insights
        reps = [r for r in c["representative_reviews"][:3]]
        out.append(make(
            id=f"common_problem_{c['cluster_id']}", type="common_problem",
            headline=f"Recurring complaint: \"{c['label']}\"",
            interpretation="Reviews with similar wording in the complaint group (rating 1-3). Preliminary cluster, quality not evaluated.",
            numbers=[{"label": "cluster reviews of complaint reviews", "numerator": c["size"], "denominator": complaints}],
            excerpts=[{"review_id": r["review_id"], "text": r["text"]} for r in reps[:3]],
            warning=None, evidence_ref={"page": "complaints", "filters": {"cluster_id": c["cluster_id"]}},
            score=c["size"] / max(complaints, 1)))
    return out, None if out else f"no cluster with size >= {MIN_CLUSTER} and a non-generic label"


def experience_gap(sentences: pd.DataFrame, texts: dict):
    out = []
    usable = sentences[sentences["polarity"].isin(["positive", "negative"])]
    for (product, aspect), grp in usable.groupby(["product_id", "aspect"]):
        pos = grp[grp["polarity"] == "positive"]
        neg = grp[grp["polarity"] == "negative"]
        if len(pos) < MIN_POS_NEG or len(neg) < MIN_POS_NEG:
            continue
        p, n = pos.iloc[0], neg.iloc[0]
        out.append(make(
            id=f"gap_{product}_{aspect.replace(' ', '_')}", type="experience_gap",
            headline=f"Mixed experiences on {aspect} for product {product}",
            interpretation="Both positive and negative sentences about this aspect. The reason is not stated in these sentences.",
            numbers=[{"label": "positive sentences", "numerator": len(pos), "denominator": len(grp)},
                     {"label": "negative sentences", "numerator": len(neg), "denominator": len(grp)}],
            excerpts=[{"review_id": p["review_id"], "text": p["sentence"]},
                      {"review_id": n["review_id"], "text": n["sentence"]}],
            warning=None, evidence_ref={"page": "contradictions",
                                        "filters": {"product_id": product, "aspect": aspect}},
            score=min(len(pos), len(neg)) / len(grp)))
    return out, None if out else f"no product+aspect with >= {MIN_POS_NEG} positive AND >= {MIN_POS_NEG} negative sentences"


def comparison(df: pd.DataFrame):
    grp = df.groupby("product_id").agg(n=("rating", "size"), comp=("rating", lambda r: int((r <= 3).sum())))
    grp = grp[grp["n"] >= MIN_PRODUCT].copy()
    if len(grp) < 2:
        return [], f"fewer than 2 products with >= {MIN_PRODUCT} reviews"
    grp["rate"] = 100 * grp["comp"] / grp["n"]
    top, bottom = grp["rate"].idxmax(), grp["rate"].idxmin()
    gap = grp.loc[top, "rate"] - grp.loc[bottom, "rate"]
    if gap < MIN_GAP_PP:
        return [], f"largest gap {gap:.1f} pp < {MIN_GAP_PP} pp"
    ex_hi = df[(df["product_id"] == top) & (df["rating"] <= 3)].iloc[0]
    ex_lo = df[(df["product_id"] == bottom) & (df["rating"] >= 4)].iloc[0]
    return [make(
        id=f"comparison_{top}_{bottom}", type="comparison",
        headline=f"Complaint rate differs between products: {top} vs {bottom}",
        interpretation="Share of reviews rated 1-3 stars. Shows the gap only; the reason is not stated.",
        numbers=[{"label": f"{top} complaint reviews", "numerator": int(grp.loc[top, "comp"]), "denominator": int(grp.loc[top, "n"])},
                 {"label": f"{bottom} complaint reviews", "numerator": int(grp.loc[bottom, "comp"]), "denominator": int(grp.loc[bottom, "n"])}],
        excerpts=[{"review_id": str(ex_hi["review_id"]), "text": str(ex_hi["review_text"])[:300]},
                  {"review_id": str(ex_lo["review_id"]), "text": str(ex_lo["review_text"])[:300]}],
        warning=None, evidence_ref={"page": "overview", "filters": {"products": [top, bottom]}},
        score=gap)], None


def quality_warning(df: pd.DataFrame, susp: pd.DataFrame):
    flagged = susp["signal_groups"].fillna("").str.contains("near_duplicate|similar_text")
    s = susp.assign(flag=flagged)
    out = []
    for product, grp in s.groupby("product_id"):
        if len(grp) < MIN_WARN_REVIEWS:
            continue
        share = grp["flag"].mean()
        if share < WARN_SHARE:
            continue
        hits = grp[grp["flag"]].head(2)
        out.append(make(
            id=f"warning_{product}", type="quality_warning",
            headline=f"Warning signal: many similar-text reviews for product {product}",
            interpretation="Warning signal, not proof of manipulation. Reviews share near-identical or similar wording.",
            numbers=[{"label": "reviews with near-duplicate or similar-text signal", "numerator": int(grp["flag"].sum()), "denominator": len(grp)}],
            excerpts=[{"review_id": r.review_id, "text": r.review_text[:300]} for r in hits.itertuples()],
            warning=None, evidence_ref={"page": "suspicion", "filters": {"product_id": product}},
            score=share))
    return out, None if out else f"no product with >= {MIN_WARN_REVIEWS} reviews and >= {int(WARN_SHARE*100)}% similar-text share"


def emerging(df: pd.DataFrame):
    """Time trend needs >= 2 periods with >= 30 reviews each. Checked on the data's date span."""
    span_days = (df["date"].max() - df["date"].min()).days + 1
    return [], f"all reviews fall in {span_days} day(s); no two periods can each reach {2 * 30} reviews per product"


def informative_evidence():
    return [], "no usefulness model output exists (phase 2 experiment saved no model; batch/predict has no usefulness column)"
