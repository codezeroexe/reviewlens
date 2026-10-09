# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

No build, lint, or test tooling is configured yet. Don't invent commands; add them here once a frontend or test setup exists.

Setup and smoke test (run from repo root, since the inference module loads `models/` relative to CWD):

```bash
pip install -r requirements.txt
python -c "from src.reviewlens_inference import ReviewLens; print(ReviewLens('models').analyze('I have used these headphones for six months. The battery lasts eight hours, but the earcups get uncomfortable.'))"
```

Frontend (`frontend/`, React 18 + Vite 5). Run backend first, then:

```bash
cd frontend && npm install && npm run dev      # http://localhost:5173, proxies /analyze to :8000
cd frontend && npm run build                    # production build to frontend/dist
```

No test or lint scripts exist yet.

Training happens only in `notebooks/ReviewLens_Training.ipynb` (Google Colab, reads raw Amazon TSVs from Google Drive). Never run training from the app or frontend.

## Architecture

**Status:** the repo is a Python ML prototype. There is no frontend, API, or server yet. The frontend is the work to be built.

**Backend:** `src/server.py` is a stdlib HTTP server (no framework). Run `python3 -m src.server` from repo root → `POST http://127.0.0.1:8000/analyze` with `{"text": "..."}`. Returns 200 with the analysis dict, or 400 `{"error": ...}` for empty text or bad JSON. Frontend calls this endpoint; it never imports the Python module directly.
- Single-process, no CORS headers, no auth. Frontend on another origin needs CORS added, or a dev proxy.
- Port 8000 may be taken locally; change the port in `src/server.py` or stop the other process.
- Sandboxed shells can't bind local ports; run the server from a normal terminal.

**Integration boundary:** `src/reviewlens_inference.py` → `ReviewLens` class, wrapped by `src/server.py`. The model loads once at server start (5 joblib artifacts + 2 JSON files), not per request.

`analyze()` returns a dict with `review_pattern`, `description`, `informational_value`, `alternative_pattern`, `closest_cluster`, `distance_to_closest_cluster`, and `note`. Show the first four plus the `note` disclaimer. Don't show the distance as a confidence or accuracy percentage. The model returns the closest of 5 unsupervised patterns, not a usefulness judgement or probability.

**Inference pipeline** (must stay identical to training, so change it only in lockstep with the notebook and artifacts):
`clean_review_text` → TF-IDF vectorizer (category-filtered vocabulary) + 9 style features (`build_style_features`, scaled and weighted by `style_weight` = 0.8) → `TruncatedSVD` (100 components) → `Normalizer` → `MiniBatchKMeans.transform` distances → nearest and second-nearest profile from `cluster_profiles.json`.

**Artifacts:** `models/` holds the trained files (`tfidf_vectorizer`, `svd_model`, `normalizer`, `clustering_model`, `style_scaler` `.joblib`, plus `cluster_profiles.json` and `model_metadata.json`). They were trained with scikit-learn **1.6.1**, which is pinned in `requirements.txt`. Loading with another sklearn version causes warnings or wrong results. Don't retrain or regenerate artifacts from the app side.

**Text cleaning must match training.** The inference code strips HTML, URLs, and whitespace, and lowercases. It keeps negation words (`not`, `no`, `never`) on purpose. Don't add stopword removal or stemming here without retraining.

## Constraints

- Raw TSV data (`data/`, `*.tsv`) is gitignored and not in the repo. The frontend must not read it.
- Keep each model file under GitHub's 100 MB limit before committing it.
- Profile labels are human interpretations of clusters. Keep user-facing wording consistent with `cluster_profiles.json` rather than rewriting it in UI code.
