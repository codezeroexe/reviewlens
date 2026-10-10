import { useEffect, useMemo, useState } from "react";

const NO_RESULT = "No meaningful contradictions found for this selection.";
const METHOD_NOTE = {
  nli: "Method: NLI model (cross-encoder/nli-deberta-v3-small). Scores are model output, not probabilities of truth.",
  "sentiment-fallback": "Method: sentiment fallback. Opposing sentiment only, not verified as logical contradiction.",
};

function EvidenceCard({ side, data, aspect }) {
  return (
    <div className="card">
      <div className="label">{side} review · {data.rating}★ · {data.review_id}</div>
      <p className="review-text">{data.quote}</p>
      <div className="muted small">Aspect: {aspect}</div>
    </div>
  );
}

export default function ContradictionInvestigator({ onBack }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [product, setProduct] = useState("");
  const [aspect, setAspect] = useState("");

  useEffect(() => {
    fetch("/contradictions")
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.error || "Request failed.");
        setItems(data.conflicts);
      })
      .catch((e) => setError(e.message));
  }, []);

  const products = useMemo(() => [...new Set((items ?? []).map((i) => i.product_id))].sort(), [items]);
  const aspects = useMemo(() => [...new Set((items ?? []).map((i) => i.aspect))].sort(), [items]);
  const shown = (items ?? []).filter((i) => (!product || i.product_id === product) && (!aspect || i.aspect === aspect));

  return (
    <div className="page">
      <header className="header">
        <span className="brand">Contradiction Investigator</span>
        <button type="button" className="chip" onClick={onBack}>Back to overview</button>
      </header>

      {error && <div className="card muted">{error}. Run contradictions/run.py first.</div>}
      {!items && !error && <p className="muted">Loading...</p>}

      {items && (
        <>
          <section className="card">
            <div className="label">Filters</div>
            <select value={product} onChange={(e) => setProduct(e.target.value)} aria-label="Product">
              <option value="">All products ({products.length})</option>
              {products.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>{" "}
            <select value={aspect} onChange={(e) => setAspect(e.target.value)} aria-label="Aspect">
              <option value="">All aspects</option>
              {aspects.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
            <p className="muted small">{shown.length} of {items.length} conflicts shown. {METHOD_NOTE[items[0]?.method] ?? ""}</p>
          </section>

          {shown.length === 0 && <section className="card"><p>{NO_RESULT}</p></section>}

          {shown.slice(0, 50).map((c, idx) => (
            <section key={idx} className="card">
              <div className="label">{c.aspect} · product {c.product_id} · {c.verdict}</div>
              <div className="grid-2">
                <EvidenceCard side="Positive" data={{ ...c.observed_evidence.positive, quote: c.observed_evidence.positive.quote }} aspect={c.aspect} />
                <EvidenceCard side="Negative" data={{ ...c.observed_evidence.negative, quote: c.observed_evidence.negative.quote }} aspect={c.aspect} />
              </div>
              <div className="label">Possible interpretation</div>
              <p className="description">{c.possible_interpretation}</p>
              <div className="label">Unknown or missing context</div>
              <ul className="note">{c.unknown_or_missing_context.map((u) => <li key={u}>{u}</li>)}</ul>
            </section>
          ))}
          {shown.length > 50 && <p className="muted small">Showing first 50 of {shown.length}.</p>}
        </>
      )}
    </div>
  );
}
