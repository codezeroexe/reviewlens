"""Label clusters from real review text and compute stats from real rows only.

Sentiment rule: rating 4-5 positive, 3 mixed, 1-2 negative (rating proxy, not a sentiment model).
Usefulness / suspicious: the production model has no such output, so these are "not available". Never zero-filled.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS

# Extra filler for labels only (chat-speak, contractions, rating words). Not used for clustering.
LABEL_STOP = set(ENGLISH_STOP_WORDS) | {"br", "didn", "don", "doesn", "isn", "ve", "ll", "star", "stars",
    "just", "like", "really", "product", "item", "use", "used", "got", "bought", "buy", "ok", "okay"}

NOT_AVAILABLE = "not available"
PRELIMINARY = "PRELIMINARY - cluster quality not yet evaluated"


def _sentiment_mix(ratings: pd.Series) -> dict:
    n = len(ratings)
    pos = (ratings >= 4).sum()
    mixed = (ratings == 3).sum()
    neg = (ratings <= 2).sum()
    pct = lambda x: round(100 * x / n, 1) if n else 0.0
    return {"positive_pct": pct(pos), "mixed_pct": pct(mixed), "negative_pct": pct(neg)}


def summarize(assigned: pd.DataFrame, method: str) -> tuple[list[dict], dict]:
    clustered = assigned[assigned["status"] == "clustered"]
    clusters = []
    if clustered.empty:
        return clusters, _meta(assigned, method, 0)
    texts = clustered["review_text"].tolist()
    tfidf = TfidfVectorizer(stop_words=list(LABEL_STOP), min_df=min(2, len(texts)), max_features=20_000,
                            token_pattern=r"(?u)\b[a-z][a-z]+\b")
    try:
        matrix = tfidf.fit_transform(texts)
        terms = np.array(tfidf.get_feature_names_out())
    except ValueError:  # too little text for any term (e.g. only stopwords)
        matrix, terms = None, np.array([])
    positions = {idx: i for i, idx in enumerate(clustered.index)}

    for cid, grp in clustered.groupby("cluster_id"):
        rows = [positions[i] for i in grp.index]
        if matrix is None:
            top = np.array(["n/a (too little text)"])
        else:
            mean_vec = np.asarray(matrix[rows].mean(axis=0)).ravel()
            top = terms[np.argsort(mean_vec)[::-1][:3]]
        reps = grp.sort_values("similarity", ascending=False).head(5)
        clusters.append({
            "cluster_id": int(cid),
            "label": ", ".join(top),
            "size": int(len(grp)),
            "products_covered": int(grp["product_id"].nunique()),
            "categories_covered": int(grp["product_category"].nunique()),
            "sentiment_mix": _sentiment_mix(grp["rating"]),
            "usefulness": NOT_AVAILABLE,
            "suspicious_pct": NOT_AVAILABLE,
            "avg_similarity": round(float(grp["similarity"].mean()), 4),
            "ambiguous_count": int(grp["ambiguous"].sum()),
            "representative_reviews": [
                {"review_id": str(r.review_id), "rating": float(r.rating), "similarity": float(r.similarity),
                 "text": str(r.review_text)[:300]} for r in reps.itertuples()
            ],
        })

    return clusters, _meta(assigned, method, len(clusters))


def _meta(assigned: pd.DataFrame, method: str, cluster_count: int) -> dict:
    meta = {
        "status": PRELIMINARY,
        "embedding_method": method,
        "complaint_rule": "rating <= 3",
        "sentiment_rule": "rating 4-5 positive, 3 mixed, 1-2 negative",
        "rows_total": int(len(assigned)),
        "clustered": int((assigned["status"] == "clustered").sum()),
        "unclustered": int((assigned["status"] == "unclustered").sum()),
        "not_complaint": int((assigned["status"] == "not_complaint").sum()),
        "skipped_small_group": int((assigned["status"] == "skipped_small_group").sum()),
        "cluster_count": cluster_count,
    }
    return meta
