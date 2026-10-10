"""Map raw Amazon review columns to one internal schema. Count every drop; never crash."""

import pandas as pd

RAW_TO_INTERNAL = {
    "review_id": "review_id",
    "product_id": "product_id",
    "product_title": "product_title",
    "product_category": "product_category",
    "star_rating": "rating",
    "review_date": "date",
    "helpful_votes": "helpful_votes",
    "total_votes": "total_votes",
    "verified_purchase": "verified_purchase",
}


def _text_col(raw: pd.DataFrame, name: str) -> pd.Series:
    if name not in raw.columns:
        return pd.Series("", index=raw.index)
    return raw[name].fillna("").astype(str)


def clean_reviews(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return cleaned rows plus a report of what was dropped or nulled."""
    df = pd.DataFrame(index=raw.index)
    for src, dst in RAW_TO_INTERNAL.items():
        if src in raw.columns:
            df[dst] = raw[src]
    df["review_text"] = (_text_col(raw, "review_headline") + " " + _text_col(raw, "review_body")).str.strip()

    report = {"rows_in": len(raw), "dropped_empty_text": 0, "rating_set_null": 0,
              "date_set_null": 0, "votes_set_null": 0}

    empty = df["review_text"] == ""
    report["dropped_empty_text"] = int(empty.sum())
    df = df[~empty]

    if "rating" in df:
        raw_r = pd.to_numeric(df["rating"], errors="coerce")
        ok = raw_r.between(1, 5)
        report["rating_set_null"] = int((df["rating"].notna() & ~ok).sum())
        df["rating"] = raw_r.where(ok)

    if "date" in df:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        report["date_set_null"] = int((df["date"].notna() & parsed.isna()).sum())
        df["date"] = parsed

    for col in ("helpful_votes", "total_votes"):
        if col in df:
            num = pd.to_numeric(df[col], errors="coerce")
            report["votes_set_null"] += int((df[col].notna() & num.isna()).sum())
            df[col] = num.astype("Int64")

    if "verified_purchase" in df:
        df["verified_purchase"] = df["verified_purchase"].map({"Y": True, "N": False})

    report["rows_kept"] = len(df)
    return df.reset_index(drop=True), report


def dedupe_reviews(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Keep first row per review_id. Returns (df, dropped_count)."""
    dup = df["review_id"].duplicated(keep="first")
    return df[~dup].reset_index(drop=True), int(dup.sum())


if __name__ == "__main__":
    # Self-check on hand-written test rows (not dataset numbers).
    raw = pd.DataFrame({
        "review_id": ["a", "b", "c", "d", "a", "e"],
        "review_headline": ["ok", "", "", "bad", "ok", "fine"],
        "review_body": ["good item", "", "", "x", "good item", "works"],
        "star_rating": [5, 4, 3, 9, 5, "abc"],
        "review_date": ["2020-01-02", "2020-01-02", "2020-01-02", "not a date", "2020-01-02", "2021-05-05"],
        "helpful_votes": [1, 0, 0, 0, 1, "x"],
        "total_votes": [2, 0, 0, 0, 2, 3],
        "verified_purchase": ["Y", "N", "N", "N", "Y", "Y"],
    })
    clean, rep = clean_reviews(raw)
    clean, dups = dedupe_reviews(clean)
    rep["dropped_duplicate_review_id"] = dups
    print(rep)
    assert rep["dropped_empty_text"] == 2
    assert rep["rating_set_null"] == 2  # 9 and "abc"
    assert rep["date_set_null"] == 1
    assert rep["votes_set_null"] == 1  # "x"
    assert rep["dropped_duplicate_review_id"] == 1  # second 'a' dropped, first kept
    print("schema self-check OK")
