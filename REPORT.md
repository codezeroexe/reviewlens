# ReviewLens: Discovering Review-Writing Patterns with Unsupervised NLP

## Abstract
Product reviews vary widely in how informative they are, yet datasets rarely offer a trustworthy "useful / not useful" label. ReviewLens is an unsupervised NLP system that learns recurring **review-writing patterns** from 100,000 Amazon reviews (Books and Electronics) and assigns any new review to its closest pattern. It combines category-filtered TF-IDF text features with nine writing-style features, reduces them with Truncated SVD, and clusters them with MiniBatch K-Means into five interpretable profiles. A small web dashboard (React frontend, Python backend) lets an analyst submit reviews and compare pattern mixes across products. The system describes *how* a review is written; it does not claim to judge whether a review is true, useful, or positive.

## 1. Problem and motivation
- Helpful-vote counts are a weak proxy for review quality: they depend on product popularity, review age, and visibility, and new reviews have none.
- Hand-labelling "useful" reviews is subjective and expensive.
- Question addressed: *can NLP discover meaningful review-writing patterns without training on a hand-made usefulness label?*

## 2. Data
| Item | Value |
| --- | --- |
| Source | Amazon customer-review TSV files (Books, Electronics) |
| Source size | about 3.1 million reviews per category |
| Training sample | 100,000 reviews (50,000 per category), random, balanced |
| Fields used | review headline and body (helpful votes only for post-hoc checks) |

Raw data is training-only and is not stored in the repository.

## 3. Method
1. **Cleaning:** join headline and body, decode HTML, strip tags and URLs, lowercase, drop texts under 15 characters. Negations ("not", "never") are kept because removing them can flip meaning.
2. **Category-aware text features:** unigram and bigram TF-IDF after removing 4,052 terms that are strongly specific to one category (so clusters do not simply become "books" vs "electronics"); 75,948 text features remain.
3. **Universal style features (9):** log word count, sentence count, vocabulary diversity, numeric-detail rate, first-person rate, long-term-use rate, comparison rate, contrast / pros-and-cons rate, exclamation count. Standardised, L2-normalised, weighted by 0.8.
4. **Dimensionality reduction:** Truncated SVD to 100 components (50.3% explained variance), then L2 normalisation.
5. **Clustering:** MiniBatch K-Means; K = 3 to 8 compared; K = 5 selected for the best balance of internal metrics and interpretability.
6. **Interpretation:** five profiles named by inspecting representative reviews, top terms, and feature signals *after* clustering.

## 4. Results
### Internal metrics
| Metric | Result |
| --- | ---: |
| Clusters | 5 |
| Silhouette score | 0.1785 |
| Davies-Bouldin index | 1.9654 |
| Cluster-size range | about 14%-30% |
| SVD explained variance | 50.3% |

### The five profiles
| Profile | What it looks like | Informational value |
| --- | --- | --- |
| Balanced Evaluative Review | Weighs positive and negative points | Moderate to high |
| Extended Analytical Review | Long, multi-sentence explanation or analysis | High |
| Concise General Opinion | Brief praise or criticism, rating-led | Low to moderate |
| Long-Term Usage Experience | Evidence from real use over time, specific performance | High |
| Personal Experience and Recommendation | First-person experience and recommendation | Moderate |

### Secondary check
Helpful votes were never used for training. Afterwards, the Extended Analytical cluster had the longest reviews and the best average helpfulness ratios in both categories, and Concise General Opinion the lowest. This is correlation, not proof of usefulness.

### Why no accuracy or F1
Those metrics need ground-truth labels, and this task deliberately has none. Quality is judged by internal metrics, cluster-size balance, and human inspection of representative reviews.

## 5. The application
- **Backend:** Python standard-library HTTP server. `POST /analyze` with `{"text": "..."}` returns the closest pattern, description, informational value, alternative pattern, and a disclaimer. Artifacts load once at startup; one review is processed in milliseconds.
- **Frontend:** React 18 + Vite dashboard.
  - KPI cards: reviews analysed, top pattern, share of high-informational-value reviews, top alternative pattern.
  - Charts: pattern mix per product (stacked bars) and informational-value distribution.
  - Review table with expandable rows (full text, description, disclaimer) and product filter chips.
  - "Analyze your own review" box, plus 35 preset reviews across 5 sample products for demos.
- **Design rule:** results always show the model's limits; the raw cluster distance is never shown as a confidence or accuracy score.

## 6. Who this is useful for
| Audience | How they could use it |
| --- | --- |
| E-commerce and marketplace analysts | Profile a review corpus by writing type; find the share of detailed, experience-based reviews per product or seller. |
| Review-platform product teams | Rank or surface informative reviews without relying on helpful votes, including brand-new reviews that have no votes yet. |
| Product and quality teams | Pull the "Long-Term Usage Experience" reviews first when looking for durability or reliability problems. |
| UX writers | Design review prompts that encourage the high-value patterns (for example, "how long have you used it?"). |
| NLP students and researchers | A worked, reproducible example of unsupervised text profiling with controls for topic leakage. |

## 7. Limitations
- Trained on Books and Electronics only; other domains need retraining.
- Some clusters still show category skew; topic dominance is reduced, not eliminated.
- Profile names are human interpretations of unsupervised clusters.
- No supervised accuracy is claimed; there is no independently annotated test set yet.
- The system outputs the closest pattern, not a calibrated probability, and not a verdict on quality or truthfulness.

## 8. Future work
- **Sentiment layer (planned):** add positive / neutral / negative classification trained from star ratings, then analyse sentiment *by writing pattern* (for example, are Long-Term Usage reviews mostly positive?). Compare logistic regression, BiLSTM, and a small from-scratch transformer, and add simple aspect-level sentiment (battery, price, story).
- More categories and a held-out category to test domain transfer.
- A small manually annotated evaluation set for the pattern labels.
- CSV upload and filtering in the dashboard; model versioning.

## 9. Reproducing
```bash
pip install -r requirements.txt
python3 -m src.server                                   # backend on 127.0.0.1:8001
cd frontend && npm install && npm run dev                # dashboard on http://localhost:5173
```
Training lives in `notebooks/ReviewLens_Training.ipynb` (Google Colab, needs the raw TSV files).
