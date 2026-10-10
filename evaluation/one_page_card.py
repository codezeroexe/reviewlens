"""One-page model card (sample format). Every number is computed here from the phase-2 split and the best config."""

import json
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.pipeline import make_pipeline

from evaluation.ngram_report import splits

OUT = Path(".")
C = 10.0


def subgroup(test, pred, mask, name, how):
    y = test["label"].to_numpy()
    m = np.asarray(mask)
    return {"name": name, "how": how, "n": int(m.sum()),
            "accuracy": round(float(accuracy_score(y[m], pred[m])), 4),
            "macro_f1": round(float(f1_score(y[m], pred[m], average="macro")), 4)}


def main() -> None:
    train, val, test, info = splits()
    pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 1), min_df=2), LogisticRegression(C=C, max_iter=1000))
    pipe.fit(train["review_text"], train["label"])
    pred = pipe.predict(test["review_text"])
    y = test["label"].to_numpy()
    p, r, f, _ = precision_recall_fscore_support(y, pred, labels=[0, 1], zero_division=0)
    maj = int(train["label"].mode()[0])
    base_acc = float(accuracy_score(y, np.full_like(y, maj)))
    base_f1 = float(f1_score(y, np.full_like(y, maj), average="macro"))

    words = test["review_text"].str.split().str.len().to_numpy()
    title_star = test["review_text"].str.match(r"^(one|two|three|four|five) stars?\b", case=False).to_numpy()
    negation = test["review_text"].str.contains(r"\b(not|never|no|n't)\b", case=False, regex=True).to_numpy()
    groups = [
        subgroup(test, pred, words < 20, "Short reviews", "fewer than 20 words"),
        subgroup(test, pred, words >= 20, "Long reviews", "20 words or more"),
        subgroup(test, pred, title_star, "Rating-title reviews", "start with 'One..Five Star(s)'"),
        subgroup(test, pred, ~title_star, "Other reviews", "no rating title"),
        subgroup(test, pred, negation, "Negation words", "contains not / never / no / n't"),
        subgroup(test, pred, ~negation, "No negation", "none of the above"),
    ]

    vec = pipe.named_steps["tfidfvectorizer"]
    coef = pipe.named_steps["logisticregression"].coef_[0]
    names = vec.get_feature_names_out()
    order = np.argsort(coef)
    top_neg = [(names[i], round(float(coef[i]), 2)) for i in order[:5]]
    top_pos = [(names[i], round(float(coef[i]), 2)) for i in order[::-1][:5]]

    card = {
        "model": "Review usefulness classifier (ReviewLens experiment, unigram config)",
        "task": "Binary: useful (1) vs not useful (0), derived label", "algorithm": "TF-IDF (unigrams, min_df=2) + Logistic Regression (C=10)",
        "training_data": f"Electronics reviews, first 500,000 rows, {info['after_dedupe']:,} labelled after dedupe (total_votes >= 5)",
        "split": f"70/15/15 stratified, seed 42. Train {len(train):,}, validation {len(val):,}, test {len(test):,}",
        "labels": "helpful_votes / total_votes >= 0.6 (not human-labelled; votes are noisy)",
        "overall": {"accuracy": round(float(accuracy_score(y, pred)), 4), "macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
                    "baseline_accuracy": round(base_acc, 4), "baseline_macro_f1": round(base_f1, 4), "baseline_name": "majority class"},
        "per_class": {"not_useful": {"precision": round(float(p[0]), 3), "recall": round(float(r[0]), 3), "f1": round(float(f[0]), 3)},
                      "useful": {"precision": round(float(p[1]), 3), "recall": round(float(r[1]), 3), "f1": round(float(f[1]), 3)}},
        "subgroups": groups,
        "top_features": {"useful": top_pos, "not_useful": top_neg},
        "lime": "NOT RUN (lime not installed)",
        "errors": {"misclassified": int((pred != y).sum()), "of": len(y)},
    }
    (OUT / "model_card_one_page.json").write_text(json.dumps(card, indent=2))
    print(json.dumps(card, indent=2))


if __name__ == "__main__":
    main()
