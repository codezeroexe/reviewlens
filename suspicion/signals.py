"""Heuristic, similarity-based signals. NOT a validated fake-review classifier.

Signals only use text, product, and date fields. Short reviews (< 5 tokens) never trigger duplicate/similarity signals.
Customer and vine columns are read from the raw TSV (same subset) and used for reviewer activity and context only.
"""

import re
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

MIN_TOKENS = 5
NEAR_DUP = 0.9
SEMANTIC = 0.9
# Plan list, kept in full (user decision). Note: "five stars" is often a headline rating label in this data.
PROMO_PHRASES = ["highly recommend", "best product ever", "must buy", "five stars", "buy now", "amazing product"]
PROMO_RE = {p: re.compile(r"\b" + re.escape(p) + r"\b") for p in PROMO_PHRASES}
TOP_WORD_RATIO = 0.25
MIN_TOKENS_REPEAT = 15
REVIEWER_DAY_MIN = 5
BURST_MIN_REVIEWS = 20
BURST_MIN_DAYS = 10
BURST_MIN_COUNT = 5
BURST_SIGMA = 3


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", str(text).lower()).split())


def exact_duplicates(df: pd.DataFrame) -> dict:
    norm = df["review_text"].map(normalize)
    tokens = norm.str.split().str.len().fillna(0)
    out = {}
    eligible = df[tokens >= MIN_TOKENS].assign(norm=norm)
    for gid, (text, grp) in enumerate(eligible.groupby("norm")):
        if len(grp) < 2:
            continue
        ids = grp["review_id"].astype(str).tolist()
        for rid in ids:
            out[rid] = {"group": gid, "similar": [i for i in ids if i != rid]}
    return out


def near_duplicates(df: pd.DataFrame) -> dict:
    norm = df["review_text"].map(normalize)
    eligible = df[norm.str.split().str.len().fillna(0) >= MIN_TOKENS].reset_index(drop=True)
    tfidf = TfidfVectorizer(min_df=1).fit_transform(norm[eligible.index].tolist())
    out = {}
    for _, grp in eligible.groupby("product_id"):
        if len(grp) < 2:
            continue
        rows = grp.index.to_numpy()
        sims = (tfidf[rows] @ tfidf[rows].T).toarray()
        np.fill_diagonal(sims, 0)
        for a, rid in enumerate(eligible.loc[rows, "review_id"].astype(str)):
            hits = [(str(eligible.loc[rows[b], "review_id"]), round(float(sims[a, b]), 4))
                    for b in np.where(sims[a] >= NEAR_DUP)[0]]
            if hits:
                out[rid] = {"similar": hits}
    return out


def semantic_similar(df: pd.DataFrame, emb: np.ndarray, chunk: int = 2000) -> dict:
    ids = df["review_id"].astype(str).to_numpy()
    tokens = df["review_text"].map(normalize).str.split().str.len().fillna(0).to_numpy()
    out = {}
    for start in range(0, len(df), chunk):
        block = emb[start:start + chunk] @ emb.T
        for offset, row in enumerate(block):
            i = start + offset
            if tokens[i] < MIN_TOKENS:
                continue
            row[i] = 0
            row[tokens < MIN_TOKENS] = 0
            hits = np.where(row >= SEMANTIC)[0]
            if len(hits):
                out[ids[i]] = {"similar": [(ids[j], round(float(row[j]), 4)) for j in hits[:20]],
                               "count": int(len(hits))}
    return out


def promo_repetition(df: pd.DataFrame) -> dict:
    out = {}
    for rid, text in zip(df["review_id"].astype(str), df["review_text"].map(normalize)):
        words = text.split()
        reasons = {}
        if len(words) >= MIN_TOKENS_REPEAT:
            content = [w for w in words if w not in ENGLISH_STOP_WORDS]  # ignore "the", "and", etc.
            if content:
                word, n = Counter(content).most_common(1)[0]
                if n / len(words) > TOP_WORD_RATIO:
                    reasons["top_word"] = {"word": word, "ratio": round(n / len(words), 3)}
        phrases = [p for p, rx in PROMO_RE.items() if rx.search(text)]
        if phrases:
            reasons["promo_phrases"] = phrases
        if reasons:
            out[rid] = reasons
    return out


def reviewer_activity(df: pd.DataFrame) -> dict:
    if "customer_id" not in df or df["customer_id"].isna().all():
        return {"__skipped__": "customer_id not available"}
    day = df["date"].dt.date.astype(str)
    counts = df.assign(day=day).groupby(["customer_id", "day"]).size()
    busy = counts[counts >= REVIEWER_DAY_MIN]
    out = {}
    for (cust, d), n in busy.items():
        for rid in df.loc[(df["customer_id"] == cust) & (day == d), "review_id"].astype(str):
            out[rid] = {"customer_id": str(cust), "day": d, "reviews_that_day": int(n)}
    return out


def bursts(df: pd.DataFrame) -> dict:
    out = {}
    for product, grp in df.dropna(subset=["date"]).groupby("product_id"):
        if len(grp) < BURST_MIN_REVIEWS or grp["date"].dt.date.nunique() < BURST_MIN_DAYS:
            continue
        daily = grp.groupby(grp["date"].dt.date).size()
        mean, std = daily.mean(), daily.std(ddof=0)
        for d, n in daily.items():
            if n >= BURST_MIN_COUNT and n > mean + BURST_SIGMA * std:
                for rid in grp.loc[grp["date"].dt.date == d, "review_id"].astype(str):
                    out[rid] = {"product_id": product, "date": str(d), "count": int(n),
                                "baseline_mean": round(float(mean), 3), "baseline_std": round(float(std), 3)}
    return out
