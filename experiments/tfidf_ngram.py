"""TF-IDF n-gram experiment for the usefulness task. Compare only; no production change.

LABEL RULE (chosen by user, phase 2):
  usefulness = 1 if helpful_votes / total_votes >= 0.6, else 0.
  Only rows with total_votes >= 5 are labelled (same threshold as notebook cell 16).
  Rows with fewer votes are excluded, not labelled 0.
  NO suspicious/fake label exists. That task is dropped from phase 2.

Split: 70/15/15 stratified, random_state=42. Dedupe on lowercased, stripped text BEFORE split (approximate).
Fit on TRAIN. C tuned on VALIDATION (macro-F1). TEST scored once per config.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from batch.loader import DEMO_FILE, load_reviews

SEED = 42
LABEL_RATIO = 0.6
MIN_TOTAL_VOTES = 5
SAMPLE_N = 100_000
NROWS = 500_000  # read cap; file is not random-ordered, so this is a head sample
CONFIGS = {"unigram": (1, 1), "bigram": (2, 2), "uni_bigram": (1, 2)}
C_GRID = [0.1, 1.0, 10.0]
OUT = Path("reports")


def build_labelled(path: Path) -> tuple[pd.DataFrame, dict]:
    df, load_rep = load_reviews(path, nrows=NROWS)
    df = df[df["total_votes"].fillna(0) >= MIN_TOTAL_VOTES].copy()
    df["label"] = (df["helpful_votes"] / df["total_votes"] >= LABEL_RATIO).astype(int)
    df["norm"] = df["review_text"].str.lower().str.strip()
    before = len(df)
    df = df.drop_duplicates("norm").reset_index(drop=True)
    if len(df) > SAMPLE_N:
        df = df.sample(n=SAMPLE_N, random_state=SEED).reset_index(drop=True)
    return df, {"load": load_rep, "labelled_rows": before, "after_dedupe": len(df)}


def evaluate(y_true, y_pred) -> dict:
    report = classification_report(y_true, y_pred, labels=[0, 1], output_dict=True, zero_division=0)
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "per_class": {k: {m: round(v, 4) for m, v in report[k].items()} for k in ["0", "1"]},
        "macro_f1": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
        "weighted_f1": round(f1_score(y_true, y_pred, average="weighted", zero_division=0), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }


def main() -> None:
    if not Path(DEMO_FILE).exists():
        raise FileNotFoundError(f"Missing {DEMO_FILE}. Phase 2 experiment needs the local TSV.")
    df, info = build_labelled(Path(DEMO_FILE))
    if df["label"].nunique() < 2:
        raise ValueError("Only one class after labelling. Cannot run experiment.")

    train_val, test = train_test_split(df, test_size=0.15, stratify=df["label"], random_state=SEED)
    train, val = train_test_split(train_val, test_size=0.15 / 0.85, stratify=train_val["label"], random_state=SEED)

    results = {"settings": {"seed": SEED, "label_rule": f"helpful/total >= {LABEL_RATIO}, total_votes >= {MIN_TOTAL_VOTES}",
                            "split": "70/15/15 stratified", "sample_n": SAMPLE_N, "nrows_cap": NROWS,
                            "classifier": "LogisticRegression(max_iter=1000)", "C_grid": C_GRID},
               "data": info,
               "class_distribution": {"train": train["label"].value_counts().sort_index().to_dict(),
                                      "test": test["label"].value_counts().sort_index().to_dict()},
               "train_count": len(train), "test_count": len(test), "configs": {}}

    baseline = DummyClassifier(strategy="most_frequent").fit(train["review_text"], train["label"])
    results["baseline_most_frequent"] = evaluate(test["label"], baseline.predict(test["review_text"]))

    for name, ngram in CONFIGS.items():
        best = None
        for c in C_GRID:
            pipe = make_pipeline(TfidfVectorizer(ngram_range=ngram, min_df=2),
                                 LogisticRegression(C=c, max_iter=1000))
            pipe.fit(train["review_text"], train["label"])
            val_f1 = f1_score(val["label"], pipe.predict(val["review_text"]), average="macro")
            if best is None or val_f1 > best[0]:
                best = (val_f1, c, pipe)
        val_f1, c, pipe = best
        test_scores = evaluate(test["label"], pipe.predict(test["review_text"]))
        test_scores.update({"ngram_range": ngram, "C": c, "val_macro_f1": round(val_f1, 4),
                            "vocab_size": len(pipe.named_steps["tfidfvectorizer"].vocabulary_)})
        results["configs"][name] = test_scores

    results["production_model"] = "N/A: ReviewLens is unsupervised (5 clusters). No usefulness output to score."
    OUT.mkdir(exist_ok=True)
    (OUT / "ngram_results.json").write_text(json.dumps(results, indent=2))
    rows = ["| config | ngram | C | accuracy | macro-F1 | weighted-F1 | val macro-F1 | vocab |", "|---|---|---|---|---|---|---|---|"]
    rows.append(f"| baseline | - | - | {results['baseline_most_frequent']['accuracy']} | {results['baseline_most_frequent']['macro_f1']} | {results['baseline_most_frequent']['weighted_f1']} | - | - |")
    for name, r in results["configs"].items():
        rows.append(f"| {name} | {r['ngram_range']} | {r['C']} | {r['accuracy']} | {r['macro_f1']} | {r['weighted_f1']} | {r['val_macro_f1']} | {r['vocab_size']} |")
    (OUT / "ngram_results.md").write_text("# N-gram results (TEST split)\n\n" + "\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
