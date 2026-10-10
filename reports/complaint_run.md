# Complaint Discovery run

**PRELIMINARY - cluster quality not yet evaluated**

- Input: first 20000 rows of `data/amazon_reviews_us_Electronics_v1_00.tsv` (head sample, not random)
- Rows read after cleaning: 20000 (load report: {'rows_in': 20000, 'dropped_empty_text': 0, 'rating_set_null': 0, 'date_set_null': 0, 'votes_set_null': 0, 'dropped_duplicate_review_id': 0, 'bad_lines_skipped': 0, 'rows_kept': 20000})
- Runtime: 11.9 s
- Embedding method: sentence-transformers all-MiniLM-L6-v2; clustering: HDBSCAN min_cluster_size=10
- Complaint rule: rating <= 3
- Clusters: 2
- Clustered rows: 819
- Unclustered rows (HDBSCAN noise or far from centroid): 3965
- Not complaint (rating 4-5, out of scope): 15216
- In skipped small groups (<30 reviews): 0

## Limitations

- Embedding: sentence-transformers all-MiniLM-L6-v2; clustering: HDBSCAN min_cluster_size=10. Model is small (MiniLM-L6); quality not checked.
- Head sample of one file, not a random sample.
- Sentiment is a rating proxy. Complaint rule is rating <= 3, so the 'positive' share is 0 by design.
- Usefulness and suspicious stats are not available (no model output).
- No cluster quality evaluation yet (no labels, no silhouette run).
- All products are one category (Electronics), so one group.
