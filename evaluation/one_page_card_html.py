"""Render model_card_one_page.json as a one-page HTML card, then PDF via headless Chrome. Numbers come from the JSON only."""

import html
import json
import subprocess
from pathlib import Path

C = json.loads(Path("model_card_one_page.json").read_text())
o, pc = C["overall"], C["per_class"]
e = lambda s: html.escape(str(s))


def rows(items, cols):
    return "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in cols(i)) + "</tr>" for i in items)


sub = rows(C["subgroups"], lambda g: [g["name"], g["how"], f"{g['n']:,}", f"{g['accuracy']*100:.1f}%", f"{g['macro_f1']:.3f}"])
feat_u = "".join(f"<li>{e(w)} ({v:+.2f})</li>" for w, v in C["top_features"]["useful"])
feat_n = "".join(f"<li>{e(w)} ({v:+.2f})</li>" for w, v in C["top_features"]["not_useful"])
page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Model Card - Review Usefulness</title>
<style>
@page {{ size: A4; margin: 9mm; }}
body {{ font-family: Georgia, serif; font-size: 8.6pt; color: #111; margin: 0; line-height: 1.2; }}
h1 {{ font-size: 14pt; margin: 0 0 2px; }}
h2 {{ font-size: 10pt; margin: 6px 0 2px; }}
table {{ border-collapse: collapse; width: 100%; margin: 3px 0; }}
td, th {{ border: 1px solid #333; padding: 1px 4px; text-align: left; vertical-align: top; font-size: 8.2pt; }}
th {{ background: #eee; }}
ul {{ margin: 2px 0 2px 16px; padding: 0; }}
li {{ margin: 0; }}
p {{ margin: 2px 0; }}
.note {{ font-style: italic; color: #444; font-size: 8pt; }}
</style></head><body>
<h1>Model Card: Review Usefulness Classifier</h1>
<p class="note">Built from the ReviewLens experiment on Amazon Electronics reviews. Labels are derived from votes, not human-labelled. Numbers are from the test split only.</p>

<h2>1. Model details</h2>
<table>
<tr><th style="width:24%">Field</th><th>Description</th></tr>
<tr><td>Model name</td><td>{e(C['model'])}</td></tr>
<tr><td>Task</td><td>{e(C['task'])}</td></tr>
<tr><td>Model</td><td>{e(C['algorithm'])}</td></tr>
<tr><td>Training data</td><td>{e(C['training_data'])}</td></tr>
<tr><td>Test data</td><td>{e(C['split'])}</td></tr>
<tr><td>Labels</td><td>{e(C['labels'])}</td></tr>
<tr><td>Developed by</td><td>ReviewLens project; script <code>evaluation/one_page_card.py</code></td></tr>
</table>

<h2>2. Intended use</h2>
<ul>
<li><b>Intended:</b> ranking English product reviews by how useful other shoppers may find them; research and classroom demonstration.</li>
<li><b>Out of scope:</b> judging individual reviewers; any decision about sellers, products, or customers; other languages; reviews of other categories; fake-review detection.</li>
</ul>

<h2>3. Overall performance</h2>
<p>The model reaches {o['accuracy']*100:.1f}% accuracy and {o['macro_f1']:.3f} macro-F1 on the {C['errors']['of']:,} test reviews, against {o['baseline_accuracy']*100:.1f}% accuracy and {o['baseline_macro_f1']:.3f} macro-F1 for the {o['baseline_name']} baseline.</p>
<table>
<tr><th>Model</th><th>Accuracy</th><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th></tr>
<tr><td rowspan="2">Logistic regression (unigram)</td><td rowspan="2">{o['accuracy']*100:.1f}%</td>
<td>not useful (0)</td><td>{pc['not_useful']['precision']:.3f}</td><td>{pc['not_useful']['recall']:.3f}</td><td>{pc['not_useful']['f1']:.3f}</td></tr>
<tr><td>useful (1)</td><td>{pc['useful']['precision']:.3f}</td><td>{pc['useful']['recall']:.3f}</td><td>{pc['useful']['f1']:.3f}</td></tr>
<tr><td>Majority baseline</td><td>{o['baseline_accuracy']*100:.1f}%</td><td colspan="3">macro-F1 {o['baseline_macro_f1']:.3f}</td></tr>
</table>

<h2>4. Performance across text subgroups</h2>
<p><b>Key audit finding:</b> the model is weakest on reviews that begin with a rating title (&quot;Five Stars ...&quot;). It is also weak on the not-useful class (recall {pc['not_useful']['recall']:.2f}). The negation subgroup does not show the drop expected from a negation-blind model (see table).</p>
<table>
<tr><th>Subgroup</th><th>Definition</th><th>Test n</th><th>Accuracy</th><th>Macro-F1</th></tr>
{sub}
</table>

<h2>5. Explainability check</h2>
<p><b>Method 1: top coefficients (logistic regression).</b> The strongest words are rare terms such as <i>intone</i>, <i>itunes</i>, <i>upon</i>, <i>pairs</i>. They do not describe usefulness. The model fits rare words, so these weights are not evidence of real signal.</p>
<table><tr><th>Pushes toward useful</th><th>Pushes toward not useful</th></tr>
<tr><td><ul>{feat_u}</ul></td><td><ul>{feat_n}</ul></td></tr></table>
<p><b>Method 2: LIME.</b> {e(C['lime'])}. No LIME explanation is reported.</p>

<h2>6. Limitations and ethical considerations</h2>
<ul>
<li><b>Main limitation:</b> bag-of-words model. It does not model word order, so &quot;not great&quot; and &quot;great&quot; share features. Use only as a ranking aid.</li>
<li><b>Label noise:</b> usefulness comes from helpful votes. Votes depend on visibility and popularity, and new reviews have few votes. The 0.6 threshold was chosen by hand, not tuned.</li>
<li><b>Sample:</b> one category, English only, one week of review dates. The experiment used the first 500,000 rows of the file, not a random sample.</li>
<li><b>Class balance:</b> the majority baseline reaches {o['baseline_accuracy']*100:.1f}% accuracy, so use macro-F1 for comparison.</li>
<li><b>Data use:</b> the source data is licensed for academic research only.</li>
</ul>

<h2>7. Recommendations</h2>
<ul>
<li>Replace the vote-based label with human annotation on a random sample before any claim about usefulness.</li>
<li>Re-run the subgroup audit on a random sample of the full file and on other categories.</li>
<li>Try a contextual model (e.g., a fine-tuned DistilBERT) and compare on the same test split and subgroups.</li>
</ul>
</body></html>"""
Path("MODEL_CARD_ONE_PAGE.html").write_text(page)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                "--print-to-pdf=MODEL_CARD_ONE_PAGE.pdf", f"file://{Path('MODEL_CARD_ONE_PAGE.html').resolve()}"],
               check=False, capture_output=True, timeout=120)
print("wrote MODEL_CARD_ONE_PAGE.html and .pdf" if Path("MODEL_CARD_ONE_PAGE.pdf").exists() else "PDF not created")
