"""Candidate pairs: one positive and one negative sentence, same product + aspect, different reviews.

Ranked by cosine similarity of the two reviews' phase-3 embeddings, max 20 per (product, aspect).
"""

import numpy as np
import pandas as pd

MAX_PER_GROUP = 20


def candidate_pairs(sentences: pd.DataFrame, emb_by_review: dict[str, np.ndarray]) -> pd.DataFrame:
    out = []
    usable = sentences[sentences["polarity"].isin(["positive", "negative"])]
    for (product, aspect), grp in usable.groupby(["product_id", "aspect"]):
        if grp["review_id"].nunique() < 2:
            continue
        pos = grp[grp["polarity"] == "positive"]
        neg = grp[grp["polarity"] == "negative"]
        cands = []
        for p in pos.itertuples():
            for n in neg.itertuples():
                if p.review_id == n.review_id:
                    continue
                a, b = emb_by_review.get(p.review_id), emb_by_review.get(n.review_id)
                sim = float(a @ b) if a is not None and b is not None else np.nan
                cands.append((sim, p, n))
        cands.sort(key=lambda t: -np.nan_to_num(t[0], nan=-1.0))
        for sim, p, n in cands[:MAX_PER_GROUP]:
            out.append({
                "product_id": product, "aspect": aspect,
                "pos_review_id": p.review_id, "pos_sentence": p.sentence, "pos_rating": p.rating,
                "pos_vader": p.vader, "pos_context": p.context,
                "neg_review_id": n.review_id, "neg_sentence": n.sentence, "neg_rating": n.rating,
                "neg_vader": n.vader, "neg_context": n.context,
                "review_similarity": None if np.isnan(sim) else round(sim, 4),
            })
    return pd.DataFrame(out)
