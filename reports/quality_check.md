# Quality check

Failures first. Evidence is from code run in `evaluation/quality_checks.py`.

Counts: {'PASS': 10, 'NOT VERIFIED': 2}

| # | Check | Status | Evidence |
|---|---|---|---|
| 10 | Original usefulness prediction works (one example) | NOT VERIFIED | No usefulness model in the project. batch/predict returns cluster patterns only (phase 2 checked, see phase1-findings). |
| 11 | Original suspicious/fake detection works (one example) | NOT VERIFIED | No existing fake-review detector in the project (reports/suspicion_audit.md). New heuristic example runs: see check 4. |
| 1 | Batch pipeline completes (phases 3-6 steps + phase 2 predict on 2,000 rows) | PASS | job status=ready, steps=['Complaint clusters', 'Contradictions', 'Suspicious signals', 'Insights'], total runtime 79.2s, predict rows=2000, failed=0 |
| 2 | Cluster links: 5 random clustered reviews match raw ID and text | PASS | checked ['R3IZUC3GFQGGUD', 'R2OH0OL4IRVAFA', 'RIZ7XB1HPV3C7', 'R1H00C0S8Z7CQ8', 'RYXA2WLC50U2U']; mismatches: none |
| 3 | Contradiction quotes: 3 pairs are real substrings of cited reviews | PASS | checked 3 pairs (6 quotes); not substring: none |
| 4 | Suspicious explanations: 3 flagged reviews, listed signals reproduced from raw | PASS | R3KU7RE4F9WR5E: signals [semantic similarity; promotional/repetitive wording] -> promo phrases=['five stars'] | R20D506TK57P7T: signals [promotional/repetitive wording] -> promo phrases=['five stars'] | RQRGLK0F30669: signals [promotional/repetitive wording] -> promo phrases=['five stars'] |
| 5 | Dashboard vs backend: 4 numbers (UI reads these endpoints) | PASS | reviews: dashboard=20000, report=20000; complaint_clusters: dashboard=2, report=2; flagged: dashboard=5880, report=5880; top_discovery_numerator: dashboard=49, report=49. Note: 'reviews' dashboard=20,000 sample; report=retained rows. |
| 6 | Empty file -> clear error | PASS | message: 'The file is empty.' |
| 7 | Malformed file (bad dates, text in numeric, wrong range) -> counted, no crash | PASS | report: rating_set_null=2, date_set_null=2, kept=3 |
| 7 | Wrong columns -> clear error | PASS | message: 'Missing a text column. Add 'review_body' or 'review_text'.' |
| 8 | Tiny dataset (10 rows): no crash, no fake clusters | PASS | clusters=0, clustered=0, statuses={'not_complaint': 9, 'skipped_small_group': 1} |
| 9 | Second upload: old clusters, insights, flags hidden (no mixing) | PASS | after upload, status=Loaded, analysis_on=demo sample only, overview available=False, demo clusters shown=0. Analysis is not re-run for uploads; phase-3 cache key is hashed on review IDs, so a new file gets a new cache key. |
