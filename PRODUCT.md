# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + Vite frontend. Calls the existing Python backend (`POST /analyze` in `src/server.py`). User chose this over plain HTML, Next.js, after reviewing pros and cons.

## Users

Analysts and researchers studying review-writing patterns across many product reviews. Not shoppers or review writers at this stage (not confirmed; ask before adding).

## Product Purpose

ReviewLens is an unsupervised NLP prototype. It analyzes how a product review is written and assigns it to the closest of five learned review-writing patterns. It does not judge usefulness, truthfulness, or quality. Success means a researcher can submit review text and understand which pattern it matches, why, and what the nearest alternative is.

*Confirmed by user.*

## Positioning

Unsupervised pattern discovery. No usefulness label is used for training. Outputs are interpretable cluster profiles, not a predicted score.

*Confirmed by user.*

## Operating Context

Researchers paste or enter single reviews and inspect results. Backend loads trained artifacts once at startup. Training runs only in the Colab notebook, never from the frontend.

*Confirmed by user.*

## Deployment

Local only for now. Public hosting is an open decision; revisit before any deploy (CORS, build output).

## Capabilities and Constraints

- Input: one review text, non-empty.
- Output: `review_pattern`, `description`, `informational_value`, `alternative_pattern`, `closest_cluster`, `distance_to_closest_cluster`, `note`.
- Must not show the distance as a confidence score or accuracy percentage.
- Must not show raw cluster numbers (`closest_cluster`). Show the pattern label only.
- Cluster labels confirmed by teammate handoff: 0 Balanced Evaluative Review, 1 Extended Analytical Review, 2 Concise General Opinion, 3 Long-Term Usage Experience, 4 Personal Experience and Recommendation.
- Must always show the disclaimer `note`.
- Model covers Books and Electronics reviews only.
- Backend: stdlib HTTP server, single process, no CORS yet. Frontend on a different origin needs CORS or a Vite dev proxy.
- Raw TSV data is never loaded by the frontend.

## Brand Commitments

None yet. Plain research tool. Visual direction is open; no name, logo, or palette is binding.

## Evidence on Hand

- Five named patterns and their descriptions in `models/cluster_profiles.json`.
- Internal metrics (silhouette 0.1785, Davies-Bouldin 1.9654) in README. Do not show as UI accuracy; no supervised accuracy exists.
- Helpful-vote correlations are secondary, post-hoc only. Do not present as validation in the UI.

## Product Principles

- Show the model's limits next to every result.
- Present patterns as interpretations, never as verdicts on a review's quality.
- Keep the analysis view readable for research use: comparable results, not a consumer rating widget.
