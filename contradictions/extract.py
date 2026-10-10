"""Split reviews into sentences, keep those naming an aspect, score polarity with VADER."""

import re

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from contradictions.aspects import ASPECTS, CONTEXT

SPLIT = re.compile(r"(?<=[.!?])\s+")
_vader = SentimentIntensityAnalyzer()


def _pattern(words: list[str]) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r")\b", re.I)


ASPECT_RE = {aspect: _pattern(words) for aspect, words in ASPECTS.items()}
CONTEXT_RE = {w: _pattern([w]) for words in CONTEXT.values() for w in words}


def polarity_label(score: float) -> str:
    return "positive" if score > 0.3 else "negative" if score < -0.3 else "neutral"


def extract(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rec in df.itertuples():
        text = str(rec.review_text)
        for sentence in SPLIT.split(text):
            hits = [a for a, rx in ASPECT_RE.items() if rx.search(sentence)]
            if not hits:
                continue
            score = _vader.polarity_scores(sentence)["compound"]
            context = sorted({w for w, rx in CONTEXT_RE.items() if rx.search(sentence)})
            for aspect in hits:
                rows.append({
                    "review_id": str(rec.review_id), "product_id": str(rec.product_id), "aspect": aspect,
                    "sentence": sentence, "rating": float(rec.rating), "vader": round(score, 4),
                    "polarity": polarity_label(score), "context": "; ".join(context),
                })
    return pd.DataFrame(rows)
