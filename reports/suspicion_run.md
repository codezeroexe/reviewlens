# Suspicious Review Investigator run

**Heuristic / similarity-based signals. Not a validated fake-review classifier.**

- Rows processed: 20000 (first 20000 rows of Electronics TSV, same subset as phase 3)
- Load report: {'rows_in': 20000, 'dropped_empty_text': 0, 'rating_set_null': 0, 'date_set_null': 0, 'votes_set_null': 0, 'dropped_duplicate_review_id': 0, 'bad_lines_skipped': 0, 'rows_kept': 20000}
- Runtime: 6.4 s
- Embedding for semantic signal: sentence-transformers all-MiniLM-L6-v2
- Category counts: {'No signals': 14120, 'Low': 4454, 'Medium': 1359, 'High': 67}
- Reviews with each signal: {'exact_duplicate': 533, 'near_duplicate': 26, 'semantic_similar': 1756, 'promo_repetition': 5065, 'reviewer_activity': 519, 'review_burst': 0}
- Signals skipped: none
- Legacy model prediction: not available (no existing detector in the project)

## Limitations

- No ground-truth fake labels. Signals are patterns, not proof.
- Short reviews (< 5 tokens) excluded from duplicate and similarity signals.
- Head sample of one file. Few products have 20+ reviews, so burst checks are rare.
- Semantic threshold 0.9 on MiniLM embeddings is my choice, not tuned.
- Exact duplicates and semantic matches are counted as ONE 'similar text' signal (they overlap).
- Promo list is the full plan list, including 'five stars'. In this data it often appears as a headline rating label, so it can flag normal reviews.
- Reviewer signal: 5+ reviews by one customer on one day in this subset.
