# ReviewLens

ReviewLens is an unsupervised NLP prototype that groups product reviews into interpretable writing patterns and maps a new review to its closest learned pattern.

## What it does

The model was prototyped on balanced samples of Amazon Books and Electronics reviews. It combines category-term-reduced TF-IDF features with writing-style signals, then applies Truncated SVD and MiniBatch K-Means clustering.

The discovered profiles are:

| Pattern | Interpretation |
| --- | --- |
| Balanced Evaluative Review | Weighs positive and negative points. |
| Extended Analytical Review | Long, multi-sentence explanation or analysis. |
| Concise General Opinion | Brief broad praise, criticism, or rating-led opinion. |
| Long-Term Usage Experience | Evidence from real use over time and specific performance details. |
| Personal Experience and Recommendation | First-person use, satisfaction, and recommendation language. |

## Results

For the five-cluster prototype:

- Silhouette score: **0.1785** (higher indicates better cluster separation)
- Davies–Bouldin index: **1.9654** (lower indicates better cluster distinction)
- SVD explained variance: **50.3%**
- Cluster sizes: approximately **14%–30%** of sampled reviews

Helpful votes were used only as secondary validation, never as the training target. The model does not produce accuracy, precision, recall, or F1 because the source data has no trustworthy ground-truth review-usefulness labels.

## Repository layout

```text
ReviewLens/
├── models/                       # Copy saved training artifacts here
├── notebooks/ReviewLens_Training.ipynb
├── src/reviewlens_inference.py   # Frontend/backend integration module
├── requirements.txt
└── README.md
```

## Run inference

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the artifacts listed in [models/README.md](models/README.md) from Google Drive into `models/`. Then use the module:

```python
from src.reviewlens_inference import ReviewLens

reviewlens = ReviewLens("models")
result = reviewlens.analyze(
    "I have used these headphones for six months. The battery lasts eight hours, "
    "but the earcups become uncomfortable after long use."
)
print(result)
```

## Important limitation

ReviewLens returns the closest learned review pattern. It is not an objective or guaranteed judgement of review usefulness, and it should not be presented as a calibrated probability or accuracy score.

## Data and retraining

Raw Amazon TSV datasets are intentionally excluded from this repository. To add categories later, retrain a new version using balanced, chunked samples from every included category, repeat cluster selection and interpretation, and replace the saved artifacts.
