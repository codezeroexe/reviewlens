"""Cluster complaint-like reviews inside each product group.

Preferred: HDBSCAN (min_cluster_size=10). Noise (-1) -> "unclustered".
Fallback: MiniBatchKMeans, then bottom-10% similarity to centroid -> "unclustered".

Complaint rule: rating <= 3 (no sentiment model in the app).
Rows outside the rule keep status "not_complaint" and are not clustered.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans

MAX_RATING = 3
MIN_GROUP = 30
MAX_K = 15
HDBSCAN_MIN_SIZE = 10


def _hdbscan_available() -> bool:
    try:
        import hdbscan  # noqa: F401
        return True
    except ImportError:
        return False


def _labels(emb_group: np.ndarray, use_hdbscan: bool) -> tuple[np.ndarray, np.ndarray]:
    """Return (cluster label per row, bool keep mask). Label -1 = noise, always 'unclustered'."""
    if use_hdbscan:
        import hdbscan
        labels = hdbscan.HDBSCAN(min_cluster_size=HDBSCAN_MIN_SIZE, metric="euclidean").fit_predict(emb_group)
        return labels, labels >= 0
    k = min(MAX_K, max(2, round(np.sqrt(len(emb_group) / 2))))
    labels = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=10, batch_size=1024).fit_predict(emb_group)
    return labels, np.ones(len(labels), bool)


def cluster(df: pd.DataFrame, emb: np.ndarray) -> tuple[pd.DataFrame, str]:
    use_hdbscan = _hdbscan_available()
    n = len(df)
    complaint = df["rating"].le(MAX_RATING).fillna(False).to_numpy(bool)
    group = df["product_category"].fillna(df["product_id"]).astype(str).to_numpy()

    status = np.array(["not_complaint"] * n, dtype=object)
    cluster_id = np.full(n, -1)
    sim = np.full(n, np.nan)
    ambiguous = np.zeros(n, bool)
    next_id = 0

    for g in np.unique(group[complaint]):
        idx = np.where(complaint & (group == g))[0]
        if len(idx) < MIN_GROUP:
            status[idx] = "skipped_small_group"
            continue
        labels, keep = _labels(emb[idx], use_hdbscan)
        for c in np.unique(labels[keep]):
            members = idx[labels == c]
            centroid = emb[members].mean(axis=0)
            centroid = centroid / (np.linalg.norm(centroid) or 1.0)
            cos = emb[members] @ centroid
            sim[members] = cos
            if use_hdbscan:
                too_far = np.zeros(len(members), bool)
            else:
                too_far = cos < np.percentile(cos, 10)
            status[members[too_far]] = "unclustered"
            kept = members[~too_far]
            status[kept] = "clustered"
            cluster_id[kept] = next_id
            if len(kept):
                ambiguous[kept] = sim[kept] < np.percentile(sim[kept], 25)
            next_id += 1
        noise = idx[labels == -1] if use_hdbscan else np.array([], int)
        status[noise] = "unclustered"

    out = df.copy()
    out["status"] = status
    out["cluster_id"] = cluster_id
    out["similarity"] = np.round(sim, 4)
    out["ambiguous"] = ambiguous
    return out, ("HDBSCAN min_cluster_size=10" if use_hdbscan else "MiniBatchKMeans + 10% distance cut")
