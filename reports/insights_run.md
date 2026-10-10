# Insight engine run

- Runtime: 7.1 s
- Reviews in base: 20000 (first 20000 rows; same subset as phases 3-5)
- Insights generated per type: {'quality_warning': 21, 'experience_gap': 11, 'common_problem': 1, 'comparison': 1}
- Overview shown: 4
- Omitted types and reasons:
  - informative_evidence: no usefulness model output exists (phase 2 experiment saved no model; batch/predict has no usefulness column)
  - emerging: all reviews fall in 7 day(s); no two periods can each reach 60 reviews per product

## Limitations

- One week of data (2015-08-25 to 2015-08-31): no meaningful time trend.
- Usefulness is not available (no model output). Not claimed.
- Complaint clusters are preliminary (HDBSCAN found 2 clusters; one is a generic catch-all).
- Quality warnings are similarity signals, not proof of manipulation.
