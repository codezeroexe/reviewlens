"""Text -> normalized vectors. Preferred: all-MiniLM-L6-v2. Fallback: TF-IDF + TruncatedSVD (word overlap only)."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

CACHE_DIR = Path("cache")
ST_MODEL = "all-MiniLM-L6-v2"
FALLBACK = "tfidf-svd fallback (100 dims)"
DIMS = 100
BATCH = 64


def _sentence_transformers_ok() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


def embed(df: pd.DataFrame) -> tuple[np.ndarray, str]:
    """Return L2-normalized embeddings (one row per df row) and the method name."""
    use_st = _sentence_transformers_ok()
    method = f"sentence-transformers {ST_MODEL}" if use_st else FALLBACK
    if not use_st:
        print("WARNING: sentence-transformers missing. Using TF-IDF+SVD fallback (weaker, word-overlap based).")

    key = hashlib.sha256((method + "|" + "|".join(df["review_id"].astype(str))).encode()).hexdigest()[:16]
    path = CACHE_DIR / f"embeddings_{key}.npy"
    if path.exists():
        print(f"loaded cached embeddings: {path}")
        return np.load(path), method

    texts = df["review_text"].tolist()
    if use_st:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(ST_MODEL, device="cpu")
        emb = model.encode(texts, batch_size=BATCH, normalize_embeddings=True, show_progress_bar=True)
    else:
        tfidf = TfidfVectorizer(min_df=2, max_features=50_000, stop_words="english")
        matrix = tfidf.fit_transform(texts)
        svd = TruncatedSVD(n_components=DIMS, random_state=42).fit(matrix)
        parts = []
        for start in range(0, matrix.shape[0], BATCH):
            parts.append(svd.transform(matrix[start:start + BATCH]))
            print(f"embedded {min(start + BATCH, len(texts))}/{len(texts)}")
        emb = normalize(np.vstack(parts))

    CACHE_DIR.mkdir(exist_ok=True)
    np.save(path, emb)
    return emb, method
