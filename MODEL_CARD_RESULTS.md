# Model card: Review Intelligence (ReviewLens prototype)

Numbers below are read from `model_card_metrics.json`, which is built from files in `reports/`. Source file given per section.

## 1. Model name, purpose, version, intended use
- Name: Review Intelligence (ReviewLens prototype). Snapshot: phase-8 snapshot.
- Purpose: help a reader see what Amazon product reviews say. Parts: a supervised usefulness experiment (TF-IDF + logistic regression, research only), an unsupervised review-pattern model (5 clusters), and heuristic modules (complaint groups, contradictions, suspicion signals, insights).
- Intended use: research and demonstration on the sample described below. Not for decisions about sellers, reviewers, or products.

## 2. Dataset description and provenance
- Source: `data/amazon_reviews_us_Electronics_v1_00.tsv` (1,725,988,504 bytes), Amazon US Customer Reviews (Electronics). Licence: academic research only (per the Kaggle dataset page; the local file was downloaded by the user).
- Pipeline sample (phases 3-6, dashboard): first 20,000 rows. Read 20,000, retained 20,000, excluded 0.
- Usefulness experiment sample: first 500,000 rows (head cap), 17,333 labelled, 17,241 after dedupe (`reports/ngram_results.json`).
- Products: 10,050. Categories: 1. Dates: 2015-08-25 to 2015-08-31 (1 month).
- Source: `reports/dataset_report.md`.

## 3. How labels were obtained + label limitations
- Usefulness: NOT human-labelled. Derived: helpful_votes / total_votes >= 0.6, only where total_votes >= 5. Experiment: 17,333 labelled rows in the 500,000-row head sample.
- Limitations: votes are noisy, new reviews have few votes, popularity affects votes, the threshold 0.6 was chosen by the user, not tuned on data. See `reports/label_notes.md`.
- Suspicious / fake: NO labels exist. The suspicion module is heuristic only.
- Complaint, contradiction, and insight outputs have no labels. Their quality has not been measured against ground truth.

## 4. Preprocessing and model architecture
- Supervised (experiment): TF-IDF (min_df=2, default tokenizer, stopwords kept) + LogisticRegression. Configs: unigram, bigram, uni+bigram. Source: `experiments/tfidf_ngram.py`.
- Unsupervised (existing, unchanged): text cleaning -> TF-IDF (category-filtered) + 9 style features -> TruncatedSVD (100) -> Normalizer -> MiniBatchKMeans (k=5). Source: `src/reviewlens_inference.py`, `models/`.
- Heuristic (new): complaint clustering (rating <= 3, HDBSCAN min_cluster_size=10 on all-MiniLM-L6-v2 embeddings), contradiction check (VADER polarity + NLI model `cross-encoder/nli-deberta-v3-small`), suspicion signals (duplicates, similarity, promo phrases, reviewer activity, bursts), insight rules.
- Supervised: only the experiment in section 6. Everything else is heuristic or unsupervised.

## 5. Evaluation methodology
- Split: 70/15/15 stratified, seed 42. Train 12,068, validation 2,586, test 2,587.
- Leakage control: vectorizer and classifier fit on TRAIN only. C tuned on VALIDATION. TEST predicted once per config. Verified in `experiments/tfidf_ngram.py` (fit lines and single test prediction).
- Known leakage risk: exact-duplicate removal is done before the split, on normalised text. Near-duplicates across splits are not removed.

## 6. Test results (`reports/ngram_results.json`)
- Best config (unigram, C=10.0, vocab 16,688):
  - accuracy 0.8179, macro-F1 0.6863, weighted-F1 0.8023.
- Majority-class baseline: accuracy 0.7855, macro-F1 0.4399.
- Production model on the same test set: N/A: ReviewLens is unsupervised (5 clusters). No usefulness output to score.
- Confusion matrix and per-class scores: `reports/ngram_results.json`.

## 7. Unigram/bigram experiment results
- See `reports/ngram_report.md` for all three configs, top-20 terms, and training time.
- Macro-F1: unigram 0.6863, bigram 0.618, uni+bigram 0.6566.

## 8. Error analysis (best config)
- Misclassified test rows: 471 of 2587. False positives (predicted useful, labelled not): 335. False negatives: 136.
- Misclassified reviews are shorter: median 58.0 words vs 94.0 for all test rows.
- Rating-label titles ("Five Stars ...", "One Star ..."): 8.3% of test rows. Accuracy on these rows 0.6977 vs 0.8288 on other rows. They make up 13.8% of errors.
- Examples: 10 sampled misclassified rows in `reports/ngram_report.md`.

## 9. Class imbalance
- Test: {'0': 555, '1': 2032} (label 0 = not useful, 1 = useful). The majority baseline already reaches accuracy 0.7855, so accuracy alone overstates the model. Use macro-F1.

## 10. Limitations, fairness, and generalisation
- One marketplace (US), English only, one category (Electronics) in the sample, one week of dates.
- Head samples of the file, not random: 20,000 rows for the pipeline, 500,000 rows for the experiment. Results may not hold for the full file or other categories.
- Helpful-vote bias: products and reviewers with more visibility get more votes.
- Complaint clusters: preliminary. HDBSCAN found 2 clusters; one is a generic catch-all.
- Contradictions: 567 shown after filter. Sample checks show many pairs are real opposing sentences, but not all. The NLI label is a model output.
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
- Python 3.11.15, Darwin 27.0.0, arm64.
- Packages: scikit-learn 1.6.1, numpy 2.4.6, pandas 3.0.6, scipy 1.17.1, joblib 1.6.0, sentence-transformers 6.1.0, hdbscan 0.8.44, transformers 5.19.0, torch 2.14.1, vaderSentiment 3.3.2, openpyxl 3.1.5.
- Embedding model: all-MiniLM-L6-v2 (sentence-transformers). NLI model: cross-encoder/nli-deberta-v3-small. Random seed: 42.
- Runtime: insights build 3.5 s. Full analysis run: see `reports/quality_check.md` (check 1).

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
- Counts: {'PASS': 10, 'NOT VERIFIED': 2}. Full list with failures first: `reports/quality_check.md`.
