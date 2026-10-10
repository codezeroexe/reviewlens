"""Active dataset for the dashboard: demo sample or an uploaded file. Upload uses the phase-2 cleaner.

Analysis steps (phases 3-6) still read the demo file. Uploads are browsable (metrics + filters), not analysed.
"""

import io
import re
from pathlib import Path

import pandas as pd

from batch.schema import clean_reviews, dedupe_reviews

UPLOAD_DIR = Path("data/uploads")
MAX_BYTES = 200 * 1024 * 1024
ALLOWED = {".csv", ".tsv", ".txt", ".xlsx"}
MIN_PRODUCT_REVIEWS = 30  # product filter lists only products with at least this many reviews

FRAME = {"df": None, "kind": None, "name": None}


class UploadError(ValueError):
    pass


def _read(name: str, data: bytes) -> pd.DataFrame:
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED:
        raise UploadError(f"Unsupported file type '{suffix}'. Use CSV, TSV, TXT, or XLSX.")
    if not data:
        raise UploadError("The file is empty.")
    try:
        if suffix == ".xlsx":
            return pd.read_excel(io.BytesIO(data), dtype=str)
        text = data.decode("utf-8-sig", errors="strict")
        first = text.split("\n", 1)[0]
        sep = "\t" if first.count("\t") > first.count(",") else ","
        return pd.read_csv(io.StringIO(text), sep=sep, dtype=str, on_bad_lines="skip")
    except UnicodeDecodeError:
        raise UploadError("The file is not UTF-8 text. Save it as UTF-8 CSV and try again.")
    except Exception as error:
        raise UploadError(f"Could not read the file: {error}")


def _adapt(raw: pd.DataFrame) -> pd.DataFrame:
    """Map common alternative column names onto the phase-2 schema. Missing text is an error."""
    cols = {c: re.sub(r"\s+", "_", str(c).strip().lower()) for c in raw.columns}
    raw = raw.rename(columns=cols)
    if "review_text" in raw and "review_body" not in raw:
        raw = raw.rename(columns={"review_text": "review_body"})
    if "rating" in raw and "star_rating" not in raw:
        raw = raw.rename(columns={"rating": "star_rating"})
    if "review_body" not in raw:
        raise UploadError("Missing a text column. Add 'review_body' or 'review_text'.")
    if "review_id" not in raw:
        raw = raw.assign(review_id=[f"row{i}" for i in range(len(raw))])
    return raw


def load_upload(name: str, data: bytes) -> dict:
    if len(data) > MAX_BYTES:
        raise UploadError("File is larger than 200 MB.")
    raw = _adapt(_read(name, data))
    if raw.empty:
        raise UploadError("The file has no rows.")
    df, report = clean_reviews(raw)
    df, dups = dedupe_reviews(df)
    report["dropped_duplicate_review_id"] = dups
    if df.empty:
        raise UploadError(f"No usable reviews after cleaning: {report}")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)
    (UPLOAD_DIR / safe).write_bytes(data)
    FRAME.update(df=df, kind="upload", name=safe)
    return {"name": safe, "report": report, "rows_kept": int(len(df))}


def set_demo(df: pd.DataFrame, name: str) -> None:
    FRAME.update(df=df, kind="demo", name=name)


def apply_filters(df: pd.DataFrame, product=None, rating=None, date_from=None, date_to=None) -> pd.DataFrame:
    out = df
    if product:
        out = out[out["product_id"].astype(str) == str(product)]
    if rating:
        out = out[out["rating"] == float(rating)]
    if date_from:
        out = out[out["date"] >= pd.Timestamp(date_from)]
    if date_to:
        out = out[out["date"] <= pd.Timestamp(date_to)]
    return out


def metrics(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"reviews": 0, "products": 0, "date_span": [None, None], "complaint_reviews": 0}
    return {
        "reviews": int(len(df)),
        "products": int(df["product_id"].nunique()),
        "date_span": [str(df["date"].min().date()) if df["date"].notna().any() else None,
                      str(df["date"].max().date()) if df["date"].notna().any() else None],
        "complaint_reviews": int((df["rating"] <= 3).sum()),
    }


def filter_options(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"products": [], "date_min": None, "date_max": None, "categories": []}
    counts = df["product_id"].value_counts()
    products = sorted(counts[counts >= MIN_PRODUCT_REVIEWS].index.astype(str).tolist())
    cats = sorted(df["product_category"].dropna().unique().tolist()) if "product_category" in df else []
    return {
        "products": products,
        "date_min": str(df["date"].min().date()) if df["date"].notna().any() else None,
        "date_max": str(df["date"].max().date()) if df["date"].notna().any() else None,
        "categories": cats,
    }
