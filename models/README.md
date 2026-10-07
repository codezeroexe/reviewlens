# Model artifacts

Copy these files produced by the training notebook from Google Drive into this folder before running the inference module:

- `tfidf_vectorizer.joblib`
- `svd_model.joblib`
- `normalizer.joblib`
- `clustering_model.joblib`
- `style_scaler.joblib`
- `cluster_profiles.json`
- `model_metadata.json`

The raw Amazon TSV files are training-only data and do not belong in this repository.

Before committing a model artifact, verify that it is below GitHub's 100 MB per-file limit. If an artifact is too large, distribute it through a release or a separate download location instead.
