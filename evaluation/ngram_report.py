"""N-gram report (phase 8 B). Reuses experiments/tfidf_ngram.py data path and split. Writes reports/ngram_report.{md,json}.

Fit/tune rule (verified in experiments/tfidf_ngram.py): vectorizer + classifier fit on TRAIN; C tuned on VALIDATION; TEST predicted once per config.
"""

import json
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from batch.loader import DEMO_FILE
from experiments.tfidf_ngram import CONFIGS, C_GRID, SEED, build_labelled

REPORTS = Path("reports")


def splits():
    df, info = build_labelled(Path(DEMO_FILE))
    train_val, test = train_test_split(df, test_size=0.15, stratify=df["label"], random_state=SEED)
    train, val = train_test_split(train_val, test_size=0.15 / 0.85, stratify=train_val["label"], random_state=SEED)
    return train, val, test, info


def top_terms(texts, ngram, n=20):
    cv = CountVectorizer(ngram_range=ngram, min_df=2)
    X = cv.fit_transform(texts)
    counts = np.asarray(X.sum(axis=0)).ravel()
    names = cv.get_feature_names_out()
    order = np.argsort(-counts)[:n]
    return [{"term": names[i], "corpus_count": int(counts[i])} for i in order], int(len(names))


def main() -> None:
    train, val, test, info = splits()
    saved = json.loads((REPORTS / "ngram_results.json").read_text())
    assert len(train) == saved["train_count"] and len(test) == saved["test_count"], "split does not match phase 2"

    out = {"source": "experiments/tfidf_ngram.py data path (same split as reports/ngram_results.json)",
           "train_count": len(train), "val_count": len(val), "test_count": len(test),
           "test_used_for_fit_or_tuning": False,
           "fit_policy": "vectorizer+classifier fit on TRAIN; C tuned on VALIDATION macro-F1; TEST predicted once per config",
           "text_cleaning": "none beyond TfidfVectorizer defaults (lowercase, token pattern \\b\\w\\w+\\b); stopwords NOT removed; min_df=2",
           "top_terms": {}, "configs": {}, "errors": {}}

    for name, ngram in CONFIGS.items():
        t0 = time.time()
        top, vocab = top_terms(train["review_text"], ngram)
        out["top_terms"][name] = {"top20": top, "vocab_from_train_counts": vocab}
    # Unigram and bigram top terms reported separately below (uni+bi shares both).

    best_name = saved and max(saved["configs"], key=lambda k: saved["configs"][k]["macro_f1"])
    for name, ngram in CONFIGS.items():
        t0 = time.time()
        pipe = make_pipeline(TfidfVectorizer(ngram_range=ngram, min_df=2), LogisticRegression(C=saved["configs"][name]["C"], max_iter=1000))
        pipe.fit(train["review_text"], train["label"])
        fit_s = round(time.time() - t0, 2)
        pred = pipe.predict(test["review_text"])
        out["configs"][name] = {"ngram_range": list(ngram), "C": saved["configs"][name]["C"], "train_seconds": fit_s,
                                "vocab_size": len(pipe.named_steps["tfidfvectorizer"].vocabulary_),
                                "macro_f1": saved["configs"][name]["macro_f1"], "weighted_f1": saved["configs"][name]["weighted_f1"],
                                "accuracy": saved["configs"][name]["accuracy"]}
        if name == best_name:
            wrong = test.assign(pred=pred)[lambda d: d["pred"] != d["label"]]
            random.seed(SEED)
            sample = wrong.sample(n=min(10, len(wrong)), random_state=SEED)
            out["errors"] = {
                "best_config": name, "misclassified_test_rows": int(len(wrong)), "test_rows": int(len(test)),
                "false_positive_pred_useful_true_not": int(((wrong.pred == 1) & (wrong.label == 0)).sum()),
                "false_negative_pred_not_true_useful": int(((wrong.pred == 0) & (wrong.label == 1)).sum()),
                "median_words_misclassified": float(wrong["review_text"].str.split().str.len().median()),
                "median_words_all_test": float(test["review_text"].str.split().str.len().median()),
                "examples": [{"review_id": r.review_id, "label": int(r.label), "pred": int(r.pred),
                              "text": r.review_text[:300]} for r in sample.itertuples()],
            }
            # Pattern check: review text that starts with a rating label ("Five Stars ...", "One Star ...").
            star = test["review_text"].str.match(r"^(one|two|three|four|five) stars?\b", case=False).to_numpy()
            right = test["label"].to_numpy() == pred
            out["errors"]["title_star_pattern"] = {
                "share_of_test_rows": round(float(star.mean()), 4),
                "accuracy_rows_with_title_star": round(float(right[star].mean()), 4),
                "accuracy_rows_without": round(float(right[~star].mean()), 4),
                "share_of_errors_with_title_star": round(float(star[~right].mean()), 4),
                "errors_false_positive_useful": int(((pred == 1) & (test["label"].to_numpy() == 0)).sum()),
                "errors_false_negative": int(((pred == 0) & (test["label"].to_numpy() == 1)).sum()),
            }

    out["baseline"] = saved["baseline_most_frequent"]
    out["production_model"] = saved["production_model"]
    out["test_class_distribution"] = saved["class_distribution"]["test"]
    out["best_config"] = best_name
    (REPORTS / "ngram_report.json").write_text(json.dumps(out, indent=2, default=str))

    e = out["errors"]
    md = ["# N-gram report", "",
          f"Source: `reports/ngram_results.json` and `experiments/tfidf_ngram.py` (same split: train {len(train):,}, val {len(val):,}, test {len(test):,}).", "",
          "## Fit and tuning policy", "", "- Vectorizer and classifier fit on TRAIN only. C tuned on VALIDATION. TEST scored once per config.",
          "- **Verified in code:** `experiments/tfidf_ngram.py` lines 86-94. Test is not used for fitting or tuning.",
          "- Caveat: the best config (unigram) also had the best validation macro-F1, so selection agrees on both splits.", "",
          "## Test results (from reports/ngram_results.json)", "",
          "| Config | Accuracy | Macro-F1 | Weighted-F1 | Vocab (fit on train) | Train seconds |", "|---|---|---|---|---|---|"]
    md.append(f"| Baseline (majority) | {out['baseline']['accuracy']} | {out['baseline']['macro_f1']} | {out['baseline']['weighted_f1']} | - | - |")
    for name, c in out["configs"].items():
        md.append(f"| {name} | {c['accuracy']} | {c['macro_f1']} | {c['weighted_f1']} | {c['vocab_size']:,} | {c['train_seconds']} |")
    md += ["", f"- Production model on same test set: {out['production_model']}", "",
           "## Top 20 terms (train corpus counts, min_df=2)", ""]
    for name in CONFIGS:
        t = out["top_terms"][name]
        md.append(f"**{name}** (vocab {t['vocab_from_train_counts']:,}): " + ", ".join(f"{x['term']} ({x['corpus_count']:,})" for x in t["top20"]))
        md.append("")
    md += ["## Error analysis (best config, 10 sampled misclassified test rows)", "",
           f"- Misclassified: {e['misclassified_test_rows']} of {e['test_rows']} test rows.",
           f"- False positives (pred useful, label not): {e['false_positive_pred_useful_true_not']}. False negatives: {e['false_negative_pred_not_true_useful']}.",
           f"- Median words: misclassified {e['median_words_misclassified']}, all test {e['median_words_all_test']}.",
           f"- Rating-label titles (e.g. 'Five Stars ...'): {e['title_star_pattern']}", ""]
    md += [f"- [{x['review_id']}] label {x['label']}, pred {x['pred']}: \"{x['text']}\"" for x in e["examples"]]
    md += ["", "## Known limitations", "",
           "- Stopwords are kept (the, and, to ...). They dominate the top-20 lists.",
           "- Usefulness label is derived from votes (helpful/total >= 0.6, total >= 5). Not human-verified.",
           "- Head sample of one file (Electronics). Not random across the file.",
           "- Dedupe is before the split, on normalised text; near-duplicates across splits are not removed.",
           "- Production model has no usefulness output, so no production comparison is possible."]
    (REPORTS / "ngram_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:24]))


if __name__ == "__main__":
    main()
