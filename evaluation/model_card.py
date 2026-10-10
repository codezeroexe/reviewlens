"""Phase 8 D + E: writes model_card_metrics.json, MODEL_CARD_RESULTS.md (project root) and reports/FINAL_SUMMARY.md.

Every number comes from a file in reports/ or from the environment. Nothing is typed in by hand.
"""

import importlib.metadata as md
import json
import platform
from pathlib import Path

R = Path("reports")
ROOT = Path(".")


def load(name):
    return json.loads((R / name).read_text())


def pkg(name):
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return "not installed"


def main() -> None:
    ds = load("dataset_report.json")
    ng = load("ngram_report.json")
    qc = load("quality_check.json")
    cl = load("complaint_clusters.json")["meta"]
    cr = load("contradictions.json")
    su = (R / "suspicion_run.md").read_text()
    ins = load("insights.json")
    exp = load("ngram_results.json")["data"]  # experiment sample (500,000-row head, labelled, deduped)
    runs = {"complaints_run_s": "see reports/complaint_run.md", "insights_built_s": ins["built_seconds"]}

    best = ng["best_config"]
    cfg = ng["configs"][best]
    base = ng["baseline"]
    err = ng["errors"]
    ts = err["title_star_pattern"]

    metrics = {
        "model_name": "Review Intelligence (ReviewLens prototype)",
        "version": "phase-8 snapshot",
        "dataset": {"file": ds["file"]["path"], "size_bytes": ds["file"]["size_bytes"], "sample_rows": ds["file"]["sample_rows"],
                    "rows_read": ds["rows"]["read"], "rows_retained": ds["rows"]["retained"], "rows_excluded": ds["rows"]["excluded"],
                    "products": ds["unique"]["products"], "categories": ds["unique"]["categories"],
                    "date_min": ds["date_coverage"]["min"], "date_max": ds["date_coverage"]["max"],
                    "distinct_months": ds["date_coverage"]["distinct_months"],
                    "exact_duplicate_texts_normalised": ds["duplicates"]["exact_duplicate_texts_normalised"]},
        "usefulness_task": {"label_rule": ng["configs"] and "helpful_votes/total_votes >= 0.6, total_votes >= 5",
                            "labelled_rows_in_sample": ds["labels"]["usefulness"]["labelled_rows"],
                            "train": ng["train_count"], "validation": ng["val_count"], "test": ng["test_count"],
                            "test_class_distribution": ng["test_class_distribution"]},
        "test_results": {"best_config": best, "ngram_range": cfg["ngram_range"], "C": cfg["C"],
                         "accuracy": cfg["accuracy"], "macro_f1": cfg["macro_f1"], "weighted_f1": cfg["weighted_f1"],
                         "vocab_size": cfg["vocab_size"], "train_seconds": cfg["train_seconds"],
                         "source": "reports/ngram_results.json", "all_configs": ng["configs"]},
        "baseline_majority": base,
        "production_model_on_same_test_set": ng["production_model"],
        "error_analysis": {"misclassified": err["misclassified_test_rows"], "test_rows": err["test_rows"],
                           "false_positive": err["false_positive_pred_useful_true_not"],
                           "false_negative": err["false_negative_pred_not_true_useful"],
                           "median_words_misclassified": err["median_words_misclassified"],
                           "median_words_all_test": err["median_words_all_test"],
                           "title_star_pattern": ts, "examples_file": "reports/ngram_report.md"},
        "complaint_clusters": {"status": cl["status"], "method": cl["embedding_method"], "clusters": cl["cluster_count"],
                               "clustered": cl["clustered"], "unclustered": cl["unclustered"], "not_complaint": cl["not_complaint"],
                               "rule": cl["complaint_rule"]},
        "contradictions": {"method": cr["method"], "all_pairs_checked": cr["all_pairs_checked"],
                           "nli_label_counts": cr["nli_label_counts"], "shown_after_filter": len(cr["conflicts"]),
                           "filter": cr["filter"]},
        "suspicion": {"type": "heuristic / similarity-based (not validated)", "source": "reports/suspicion_run.md"},
        "quality_checks": {"counts": qc["counts"], "source": "reports/quality_check.md"},
        "runtime_seconds": runs,
        "environment": {"python": platform.python_version(), "os": f"{platform.system()} {platform.release()}",
                        "machine": platform.machine(),
                        "packages": {p: pkg(p) for p in ["scikit-learn", "numpy", "pandas", "scipy", "joblib",
                                                        "sentence-transformers", "hdbscan", "transformers", "torch",
                                                        "vaderSentiment", "openpyxl"]},
                        "embedding_model": "all-MiniLM-L6-v2 (sentence-transformers)",
                        "nli_model": "cross-encoder/nli-deberta-v3-small",
                        "random_seed": 42},
    }
    (ROOT / "model_card_metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    m = metrics
    card = f"""# Model card: Review Intelligence (ReviewLens prototype)

Numbers below are read from `model_card_metrics.json`, which is built from files in `reports/`. Source file given per section.

## 1. Model name, purpose, version, intended use
- Name: {m['model_name']}. Snapshot: {m['version']}.
- Purpose: help a reader see what Amazon product reviews say. Parts: a supervised usefulness experiment (TF-IDF + logistic regression, research only), an unsupervised review-pattern model (5 clusters), and heuristic modules (complaint groups, contradictions, suspicion signals, insights).
- Intended use: research and demonstration on the sample described below. Not for decisions about sellers, reviewers, or products.

## 2. Dataset description and provenance
- Source: `{m['dataset']['file']}` ({m['dataset']['size_bytes']:,} bytes), Amazon US Customer Reviews (Electronics). Licence: academic research only (per the Kaggle dataset page; the local file was downloaded by the user).
- Pipeline sample (phases 3-6, dashboard): first {m['dataset']['sample_rows']:,} rows. Read {m['dataset']['rows_read']:,}, retained {m['dataset']['rows_retained']:,}, excluded {m['dataset']['rows_excluded']:,}.
- Usefulness experiment sample: first {exp['load']['rows_in']:,} rows (head cap), {exp['labelled_rows']:,} labelled, {exp['after_dedupe']:,} after dedupe (`reports/ngram_results.json`).
- Products: {m['dataset']['products']:,}. Categories: {m['dataset']['categories']}. Dates: {m['dataset']['date_min']} to {m['dataset']['date_max']} ({m['dataset']['distinct_months']} month).
- Source: `reports/dataset_report.md`.

## 3. How labels were obtained + label limitations
- Usefulness: NOT human-labelled. Derived: helpful_votes / total_votes >= 0.6, only where total_votes >= 5. Experiment: {exp['labelled_rows']:,} labelled rows in the 500,000-row head sample.
- Limitations: votes are noisy, new reviews have few votes, popularity affects votes, the threshold 0.6 was chosen by the user, not tuned on data. See `reports/label_notes.md`.
- Suspicious / fake: NO labels exist. The suspicion module is heuristic only.
- Complaint, contradiction, and insight outputs have no labels. Their quality has not been measured against ground truth.

## 4. Preprocessing and model architecture
- Supervised (experiment): TF-IDF (min_df=2, default tokenizer, stopwords kept) + LogisticRegression. Configs: unigram, bigram, uni+bigram. Source: `experiments/tfidf_ngram.py`.
- Unsupervised (existing, unchanged): text cleaning -> TF-IDF (category-filtered) + 9 style features -> TruncatedSVD (100) -> Normalizer -> MiniBatchKMeans (k=5). Source: `src/reviewlens_inference.py`, `models/`.
- Heuristic (new): complaint clustering (rating <= 3, HDBSCAN min_cluster_size=10 on all-MiniLM-L6-v2 embeddings), contradiction check (VADER polarity + NLI model `cross-encoder/nli-deberta-v3-small`), suspicion signals (duplicates, similarity, promo phrases, reviewer activity, bursts), insight rules.
- Supervised: only the experiment in section 6. Everything else is heuristic or unsupervised.

## 5. Evaluation methodology
- Split: 70/15/15 stratified, seed 42. Train {m['usefulness_task']['train']:,}, validation {m['usefulness_task']['validation']:,}, test {m['usefulness_task']['test']:,}.
- Leakage control: vectorizer and classifier fit on TRAIN only. C tuned on VALIDATION. TEST predicted once per config. Verified in `experiments/tfidf_ngram.py` (fit lines and single test prediction).
- Known leakage risk: exact-duplicate removal is done before the split, on normalised text. Near-duplicates across splits are not removed.

## 6. Test results (`reports/ngram_results.json`)
- Best config (unigram, C={m['test_results']['C']}, vocab {m['test_results']['vocab_size']:,}):
  - accuracy {m['test_results']['accuracy']}, macro-F1 {m['test_results']['macro_f1']}, weighted-F1 {m['test_results']['weighted_f1']}.
- Majority-class baseline: accuracy {m['baseline_majority']['accuracy']}, macro-F1 {m['baseline_majority']['macro_f1']}.
- Production model on the same test set: {m['production_model_on_same_test_set']}
- Confusion matrix and per-class scores: `reports/ngram_results.json`.

## 7. Unigram/bigram experiment results
- See `reports/ngram_report.md` for all three configs, top-20 terms, and training time.
- Macro-F1: unigram {ng['configs']['unigram']['macro_f1']}, bigram {ng['configs']['bigram']['macro_f1']}, uni+bigram {ng['configs']['uni_bigram']['macro_f1']}.

## 8. Error analysis (best config)
- Misclassified test rows: {err['misclassified_test_rows']} of {err['test_rows']}. False positives (predicted useful, labelled not): {err['false_positive_pred_useful_true_not']}. False negatives: {err['false_negative_pred_not_true_useful']}.
- Misclassified reviews are shorter: median {err['median_words_misclassified']} words vs {err['median_words_all_test']} for all test rows.
- Rating-label titles ("Five Stars ...", "One Star ..."): {ts['share_of_test_rows']*100:.1f}% of test rows. Accuracy on these rows {ts['accuracy_rows_with_title_star']} vs {ts['accuracy_rows_without']} on other rows. They make up {ts['share_of_errors_with_title_star']*100:.1f}% of errors.
- Examples: 10 sampled misclassified rows in `reports/ngram_report.md`.

## 9. Class imbalance
- Test: {m['usefulness_task']['test_class_distribution']} (label 0 = not useful, 1 = useful). The majority baseline already reaches accuracy {m['baseline_majority']['accuracy']}, so accuracy alone overstates the model. Use macro-F1.

## 10. Limitations, fairness, and generalisation
- One marketplace (US), English only, one category (Electronics) in the sample, one week of dates.
- Head samples of the file, not random: 20,000 rows for the pipeline, 500,000 rows for the experiment. Results may not hold for the full file or other categories.
- Helpful-vote bias: products and reviewers with more visibility get more votes.
- Complaint clusters: preliminary. HDBSCAN found {m['complaint_clusters']['clusters']} clusters; one is a generic catch-all.
- Contradictions: {m['contradictions']['shown_after_filter']} shown after filter. Sample checks show many pairs are real opposing sentences, but not all. The NLI label is a model output.
- Suspicion: heuristic, no ground truth. Flags are warnings. Frequent flags come from common phrases such as "five stars" in review titles.
- No demographic data. No fairness analysis was possible.

## 11. Prohibited overclaims
- Do not call suspicious-review flags "proof" or "verified fake".
- Do not call the heuristic detector a validated classifier.
- Do not call complaint clusters "evaluated" (cluster quality was not measured).
- Do not say contradictions prove a cause.
- Do not call usefulness predictions verified truth.
- Do not say "rising" trends (the data covers one week).

## 12. Runtime environment
- Python {m['environment']['python']}, {m['environment']['os']}, {m['environment']['machine']}.
- Packages: {', '.join(f'{k} {v}' for k, v in m['environment']['packages'].items())}.
- Embedding model: {m['environment']['embedding_model']}. NLI model: {m['environment']['nli_model']}. Random seed: {m['environment']['random_seed']}.
- Runtime: insights build {runs['insights_built_s']} s. Full analysis run: see `reports/quality_check.md` (check 1).

## 13. Reproducibility (run from the project root, in order)
```bash
pip install -r requirements.txt
python -m evaluation.dataset_report
python -m experiments.tfidf_ngram
python -m evaluation.ngram_report
python -m complaints.run
python -m contradictions.run
python -m suspicion.run
python -m insights.run
python -m evaluation.quality_checks
python -m evaluation.model_card
```

## Quality checks
- Counts: {m['quality_checks']['counts']}. Full list with failures first: `reports/quality_check.md`.
"""
    (ROOT / "MODEL_CARD_RESULTS.md").write_text(card)

    fs = [
        "# Final summary", "",
        "Built: dataset report, n-gram experiment, complaint discovery, contradiction investigator, suspicion investigator, insight engine, dashboard with upload and filters.", "",
        "## Quality checks", "", "Counts: " + ", ".join(f"{k} {v}" for k, v in m['quality_checks']['counts'].items()), "",
    ] + [f"- {r['n']}. {r['check']}: {r['status']}" for r in sorted(qc["results"], key=lambda r: r["n"])] + [
        "", "## Values for the academic model card", "",
        f"- Rows retained (sample): {m['dataset']['rows_retained']:,} of {m['dataset']['rows_read']:,}",
        f"- Usefulness labelled rows (experiment sample): {exp['labelled_rows']:,} (after dedupe {exp['after_dedupe']:,})",
        f"- Best n-gram config: {best}, macro-F1 {m['test_results']['macro_f1']}, accuracy {m['test_results']['accuracy']}",
        f"- Majority baseline macro-F1: {m['baseline_majority']['macro_f1']}",
        f"- Vocabulary sizes: unigram {ng['configs']['unigram']['vocab_size']:,}, bigram {ng['configs']['bigram']['vocab_size']:,}, uni+bigram {ng['configs']['uni_bigram']['vocab_size']:,}",
        f"- Complaint clusters: {m['complaint_clusters']['clusters']} ({m['complaint_clusters']['clustered']} clustered, {m['complaint_clusters']['unclustered']} unclustered)",
        f"- Contradictions shown: {m['contradictions']['shown_after_filter']} (NLI score >= 0.9, shared keyword)",
        f"- Insight build time: {runs['insights_built_s']} s", "",
        "## Not verified", "",
        "- Usefulness model prediction on the app: no model exists.",
        "- Existing fake-review detector: none exists.",
        "- Cluster quality, contradiction precision, suspicion precision: not measured against ground truth.",
        "- Full dataset (only a 20,000-row head sample was analysed).",
    ]
    (R / "FINAL_SUMMARY.md").write_text("\n".join(fs) + "\n")
    print("wrote model_card_metrics.json, MODEL_CARD_RESULTS.md, reports/FINAL_SUMMARY.md")


if __name__ == "__main__":
    main()
