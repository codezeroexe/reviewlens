"""Batch-run the existing ReviewLens model. No retraining. Errors counted per batch."""

import pandas as pd

from src.reviewlens_inference import ReviewLens


def predict_batch(df: pd.DataFrame, model: ReviewLens, batch_size: int = 500) -> tuple[pd.DataFrame, dict]:
    texts = df["review_text"].tolist()
    rows, failed = [], 0
    for start in range(0, len(texts), batch_size):
        chunk = texts[start:start + batch_size]
        try:
            distances = model.kmeans.transform(model._transform(chunk))
        except Exception as error:  # keep going; report the failure
            failed += len(chunk)
            print(f"batch {start}-{start + len(chunk)} failed: {error}")
            rows += [{"review_pattern": None, "informational_value": None,
                      "closest_cluster": None, "distance_to_closest_cluster": None}] * len(chunk)
            continue
        for row in distances:
            nearest = int(row.argmin())
            profile = model.cluster_profiles[str(nearest)]
            rows.append({
                "review_pattern": profile["label"],
                "informational_value": profile["informational_value"],
                "closest_cluster": nearest,
                "distance_to_closest_cluster": round(float(row[nearest]), 4),
            })
        print(f"processed {start + len(chunk)}/{len(texts)}")
    out = pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    return out, {"rows": len(texts), "failed_in_batches": failed}


if __name__ == "__main__":
    # Self-check on three hand-written reviews through the real model.
    sample = pd.DataFrame({"review_id": ["x1", "x2", "x3"], "review_text": [
        "I have used these headphones for six months. Battery lasts eight hours.",
        "Great product, works well.",
        "Not good. Broke after two days.",
    ]})
    out, rep = predict_batch(sample, ReviewLens("models"), batch_size=2)
    print(out)
    assert rep["failed_in_batches"] == 0
    assert out["review_pattern"].notna().all()
    print("predict self-check OK")
