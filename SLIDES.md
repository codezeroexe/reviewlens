# ReviewLens: slide outline and how to build the deck

Target: about 10 minutes plus Q&A, 11 slides. Source material: [REPORT.md](REPORT.md) and [README.md](README.md).

## Slide outline
| # | Title | On the slide | Say |
| --- | --- | --- | --- |
| 1 | ReviewLens | Name, one-line pitch: "Finding out *how* a review is written, without a usefulness label". Your name, course. | Set the question up front. |
| 2 | The problem | Three bullets: helpful votes are biased (popularity, age), new reviews have none, hand-labelling is subjective. Small "5 stars. Great." vs a detailed review image. | Reviews differ hugely in information; we lack trustworthy labels. |
| 3 | The idea | One sentence: unsupervised pattern discovery. Arrow: reviews -> patterns -> new review gets nearest pattern. | Discover patterns first, interpret afterwards. |
| 4 | Data | 100k Amazon reviews, 50k Books + 50k Electronics, from about 6.2M available. | Chunked sampling; raw data never in the repo. |
| 5 | Pipeline | Diagram from README (clean -> TF-IDF + style features -> SVD -> K-Means -> profile). | Walk left to right, one phrase per box. |
| 6 | Two design choices that matter | (1) Removed 4,052 category-specific terms. (2) Added 9 style features. Tiny before/after example: clusters were "author/story" vs "battery/sound". | This is the key insight: without it, clusters just recover the product category. |
| 7 | The five patterns | Table of profiles with informational value. | One example review per profile if space allows. |
| 8 | How good is it? | Silhouette 0.1785, Davies-Bouldin 1.9654, cluster sizes 14-30%, helpful-vote check. Footer: "no accuracy claimed, no labels exist". | Be upfront: internal metrics and human inspection, correlation not proof. |
| 9 | Live demo | Screenshot of the dashboard (KPIs, pattern mix by product, table). | Paste one short and one detailed review; show different patterns. |
| 10 | Who it helps | Four rows from REPORT.md section 6: analysts, platform teams, product/quality teams, UX writers. | Pick the 2 most relevant to your audience. |
| 11 | Limits and next steps | Limits (two categories, no ground truth). Next: sentiment layer by star rating, BiLSTM and small transformer comparison, more categories, aspect sentiment. | Close on the roadmap and the question for the audience. |

Optional backup slides: cluster feature signals, SVD explained variance, K = 3 to 8 comparison, tech stack.

## Assets to capture before building
- Dashboard screenshots: full view, one expanded row, the "Analyze your own review" box with a result. Start the app with the commands in REPORT.md section 9.
- Pipeline diagram: render the mermaid block in `README.md` (GitHub renders it) and screenshot, or redraw it with 5 boxes.
- One example review per pattern: use the preset labels in `frontend/src/presets.js` (Quick praise, Balanced, Long-term use, Detailed analysis, Personal recommendation).
- A bar of the five pattern colours from `frontend/src/App.jsx` for consistent chart colours.

## How to make the slides (pick one)
1. **Have Claude build it:** ask for a deck from this outline. Two options are available in this session: Gamma (AI deck generator, exports PPTX/PDF) or the pptx skill (local .pptx file). Attach screenshots afterwards.
2. **Google Slides / Keynote / PowerPoint, by hand:** one slide per row above, a big title, at most 4 bullets, and every chart or screenshot full-width. Use the "Say" column as speaker notes.
3. **Markdown tools (Marp, Slidev):** paste the table rows as slides; good if you want it version-controlled.

## Presenting tips
- Keep the demo short and rehearsed: have two reviews copied (a one-liner and a detailed one) so the pattern difference is obvious.
- Say the limitation yourself before anyone asks: the model describes writing style, it is not a quality verdict.
- Likely questions: Why not supervised? (no trustworthy label). Why 5 clusters? (metrics plus interpretability). How do you know the clusters mean something? (representative reviews, top terms, helpful-vote check as a secondary signal). What about sentiment? (planned next step, see slide 11).
