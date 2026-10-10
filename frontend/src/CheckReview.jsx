import { useState } from "react";
import { useApp } from "./AppState.jsx";
import { fmt, postJson, useApi } from "./api.js";
import { PRODUCTS } from "./presets.js";
import { colorOf } from "./patterns.js";
import { PageHead } from "./ui.jsx";

const EXAMPLES = PRODUCTS[0].reviews.map((r) => ({ label: r.label, text: r.text.replaceAll("{subject}", PRODUCTS[0].subjects[0]) }));

/** Check one review against the learned writing patterns, and see how common that pattern is in the loaded dataset. */
export default function CheckReview() {
  const { dataset, resultsVersion } = useApp();
  const [draft, setDraft] = useState("");
  const [state, setState] = useState({ result: null, error: null, busy: false, text: "" });
  const view = useApi(dataset.kind ? "/app/view" : null, [dataset.name, dataset.rows, resultsVersion]);

  async function submit(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setState({ result: null, error: null, busy: true, text });
    try { setState({ result: await postJson("/analyze", { text }), error: null, busy: false, text }); }
    catch (e) { setState({ result: null, error: e.message, busy: false, text }); }
  }

  const { result } = state;
  const share = result && view.data?.patterns?.mix.find((m) => m.pattern === result.review_pattern);
  return (
    <div className="page">
      <PageHead title="Check a review" banner="The closest learned writing pattern. Not a usefulness or quality judgement." />
      <form className="card custom-input" onSubmit={submit}>
        <label className="label" htmlFor="review-draft">Paste a review</label>
        <textarea id="review-draft" className="lined" value={draft} onChange={(e) => setDraft(e.target.value)}
                  placeholder="Paste a product review here..." maxLength={20000} />
        <div className="row-between">
          <div className="chips" aria-label="Examples">
            {EXAMPLES.map((ex) => <button key={ex.label} type="button" className="chip" onClick={() => setDraft(ex.text)}>{ex.label}</button>)}
          </div>
          <button type="submit" className="cta" disabled={!draft.trim() || state.busy}>{state.busy ? "Checking…" : "Check review"}</button>
        </div>
      </form>

      {state.error && <div className="card-slim danger" role="alert">{state.error}</div>}
      {result && (
        <section className="card" aria-live="polite">
          <div className="label">Result</div>
          <div className="custom-pattern">
            <span className="dot" style={{ background: colorOf(result.review_pattern) }} />
            <b>{result.review_pattern}</b>
            <span className="badge badge-muted">Informational value: {result.informational_value}</span>
            <span className="badge badge-warning">Model prediction</span>
          </div>
          <p className="description">{result.description}</p>
          <p className="muted small">Next closest pattern: {result.alternative_pattern}</p>
          {share && (
            <p className="num-line">
              {share.pct}% of {fmt(view.data.patterns.scored)} reviews in {dataset.name} fall in this pattern
              <span className="muted small"> {view.data.filtered ? "(current filters)" : "(whole dataset)"}</span>
            </p>
          )}
          <p className="note">{result.note}</p>
        </section>
      )}
    </div>
  );
}
