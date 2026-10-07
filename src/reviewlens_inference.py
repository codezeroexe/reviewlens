"""Load trained ReviewLens artifacts and analyze a new product review."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import normalize


STYLE_FEATURE_NAMES = [
    "log_word_count",
    "sentence_count",
    "vocabulary_diversity",
    "numeric_detail_rate",
    "first_person_rate",
    "long_term_experience_rate",
    "comparison_rate",
    "contrast_pros_cons_rate",
    "exclamation_count",
]


def clean_review_text(headline: str, body: str) -> str:
    """Apply the same text cleaning used by the training notebook."""
    headline = "" if pd.isna(headline) else str(headline)
    body = "" if pd.isna(body) else str(body)

    text = html.unescape(f"{headline} {body}")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def build_style_features(texts: Sequence[str]) -> pd.DataFrame:
    """Create the category-independent review-writing features."""
    text_series = pd.Series(texts, dtype="string").fillna("").str.lower()
    tokens = text_series.str.findall(r"[a-z]+")
    word_count = tokens.str.len().clip(lower=1)
    vocabulary_diversity = tokens.apply(
        lambda words: len(set(words)) / max(len(words), 1)
    )

    return pd.DataFrame({
        "log_word_count": np.log1p(word_count),
        "sentence_count": text_series.str.count(r"[.!?]+").clip(lower=1),
        "vocabulary_diversity": vocabulary_diversity,
        "numeric_detail_rate": text_series.str.count(r"\d+") / word_count,
        "first_person_rate": text_series.str.count(r"\b(i|my|mine|we|our|ours)\b") / word_count,
        "long_term_experience_rate": (
            text_series.str.count(r"\b(after|since|days?|weeks?|months?|years?|used|using)\b")
            / word_count
        ),
        "comparison_rate": (
            text_series.str.count(r"\b(better|worse|than|compared|comparison|instead)\b")
            / word_count
        ),
        "contrast_pros_cons_rate": (
            text_series.str.count(r"\b(but|however|although|pros|cons|despite|except)\b")
            / word_count
        ),
        "exclamation_count": text_series.str.count(r"!"),
    }).astype(np.float32)


class ReviewLens:
    """Reusable inference wrapper for the trained ReviewLens model."""

    def __init__(self, model_dir: str | Path = "models") -> None:
        self.model_dir = Path(model_dir)
        self.vectorizer = joblib.load(self.model_dir / "tfidf_vectorizer.joblib")
        self.svd = joblib.load(self.model_dir / "svd_model.joblib")
        self.normalizer = joblib.load(self.model_dir / "normalizer.joblib")
        self.kmeans = joblib.load(self.model_dir / "clustering_model.joblib")
        self.style_scaler = joblib.load(self.model_dir / "style_scaler.joblib")

        with (self.model_dir / "cluster_profiles.json").open(encoding="utf-8") as file:
            self.cluster_profiles = json.load(file)
        with (self.model_dir / "model_metadata.json").open(encoding="utf-8") as file:
            self.metadata = json.load(file)

        self.style_weight = float(self.metadata.get("style_weight", 0.8))

    def _transform(self, review_texts: Sequence[str]):
        cleaned_texts = [clean_review_text("", text) for text in review_texts]
        text_features = self.vectorizer.transform(cleaned_texts)
        style_features = build_style_features(cleaned_texts)
        scaled_style_features = self.style_scaler.transform(style_features)
        scaled_style_features = normalize(scaled_style_features) * self.style_weight

        combined_features = hstack(
            [text_features, csr_matrix(scaled_style_features)],
            format="csr",
        )
        return self.normalizer.transform(self.svd.transform(combined_features))

    def analyze(self, review_text: str) -> dict[str, Any]:
        """Return the closest learned review pattern for a non-empty review."""
        if not isinstance(review_text, str) or not review_text.strip():
            raise ValueError("Please enter a non-empty review.")

        transformed_review = self._transform([review_text])
        distances = self.kmeans.transform(transformed_review)[0]
        ranked_clusters = np.argsort(distances)
        nearest_cluster = int(ranked_clusters[0])
        alternative_cluster = int(ranked_clusters[1])
        profile = self.cluster_profiles[str(nearest_cluster)]

        return {
            "review_pattern": profile["label"],
            "description": profile["description"],
            "informational_value": profile["informational_value"],
            "closest_cluster": nearest_cluster,
            "alternative_pattern": self.cluster_profiles[str(alternative_cluster)]["label"],
            "distance_to_closest_cluster": round(float(distances[nearest_cluster]), 4),
            "note": (
                "This is the closest learned review pattern, not an objective "
                "or guaranteed usefulness judgement."
            ),
        }
