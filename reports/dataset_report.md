# Dataset report

Source: `data/amazon_reviews_us_Electronics_v1_00.tsv` (1,725,988,504 bytes). Sample: first 20,000 rows. Computed by `evaluation/dataset_report.py`.

## Rows

- Read: 20,000
- Retained: 20,000
- Excluded: 0
- Exclusion reasons: dropped_empty_text = 0, rating_set_null = 0, date_set_null = 0, votes_set_null = 0, dropped_duplicate_review_id = 0, bad_lines_skipped = 0

## Unique values

- Products: 10,050 (27 with 30+ reviews)
- Categories: 1
- Review IDs: 20,000
- Reviewers (customer_id): 17380

## Rating distribution (star_rating)

| Stars | Count | % |
|---|---|---|
| 1 | 2,351 | 11.76 |
| 2 | 1,069 | 5.34 |
| 3 | 1,364 | 6.82 |
| 4 | 2,964 | 14.82 |
| 5 | 12,252 | 61.26 |

## Labels

- Usefulness (derived): 723 rows with total_votes >= 5. Rule: helpful_votes/total_votes >= 0.6 with total_votes >= 5.
- Fake/suspicious: none (no labels in dataset)

## Missing values

| Column | Missing | % |
|---|---|---|
| marketplace | 0 | 0.0 |
| customer_id | 0 | 0.0 |
| review_id | 0 | 0.0 |
| product_id | 0 | 0.0 |
| product_parent | 0 | 0.0 |
| product_title | 0 | 0.0 |
| product_category | 0 | 0.0 |
| star_rating | 0 | 0.0 |
| helpful_votes | 0 | 0.0 |
| total_votes | 0 | 0.0 |
| vine | 0 | 0.0 |
| verified_purchase | 0 | 0.0 |
| review_headline | 0 | 0.0 |
| review_body | 1 | 0.005 |
| review_date | 0 | 0.0 |

## Duplicates

- Exact duplicate review IDs: 0
- Exact duplicate texts (normalised): 1761
- Near duplicates: not counted here; method: exact-after-normalisation (lowercase, punctuation removed) within the sample; no fuzzy matching

## Dates

- Min 2015-08-25, max 2015-08-31, distinct months 1

## Metadata present

- verified_purchase: yes
- vine: yes
- helpful_votes: yes
- total_votes: yes
- review_date: yes
- customer_id: yes
