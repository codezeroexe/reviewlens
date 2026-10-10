# Final summary

Built: dataset report, n-gram experiment, complaint discovery, contradiction investigator, suspicion investigator, insight engine, dashboard with upload and filters.

## Quality checks

Counts: PASS 10, NOT VERIFIED 2

- 1. Batch pipeline completes (phases 3-6 steps + phase 2 predict on 2,000 rows): PASS
- 2. Cluster links: 5 random clustered reviews match raw ID and text: PASS
- 3. Contradiction quotes: 3 pairs are real substrings of cited reviews: PASS
- 4. Suspicious explanations: 3 flagged reviews, listed signals reproduced from raw: PASS
- 5. Dashboard vs backend: 4 numbers (UI reads these endpoints): PASS
- 6. Empty file -> clear error: PASS
- 7. Malformed file (bad dates, text in numeric, wrong range) -> counted, no crash: PASS
- 7. Wrong columns -> clear error: PASS
- 8. Tiny dataset (10 rows): no crash, no fake clusters: PASS
- 9. Second upload: old clusters, insights, flags hidden (no mixing): PASS
- 10. Original usefulness prediction works (one example): NOT VERIFIED
- 11. Original suspicious/fake detection works (one example): NOT VERIFIED

## Values for the academic model card

- Rows retained (sample): 20,000 of 20,000
- Usefulness labelled rows (experiment sample): 17,333 (after dedupe 17,241)
- Best n-gram config: unigram, macro-F1 0.6863, accuracy 0.8179
- Majority baseline macro-F1: 0.4399
- Vocabulary sizes: unigram 16,688, bigram 146,417, uni+bigram 163,105
- Complaint clusters: 2 (819 clustered, 3965 unclustered)
- Contradictions shown: 567 (NLI score >= 0.9, shared keyword)
- Insight build time: 3.5 s

## Not verified

- Usefulness model prediction on the app: no model exists.
- Existing fake-review detector: none exists.
- Cluster quality, contradiction precision, suspicion precision: not measured against ground truth.
- Full dataset (only a 20,000-row head sample was analysed).
