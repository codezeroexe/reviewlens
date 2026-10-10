import { useMemo, useState } from "react";
import { useApp } from "./AppState.jsx";
import { fmt, plain, useApi } from "./api.js";
import { Fetching, Gated, PageHead } from "./ui.jsx";

const NO_RESULT = "No meaningful contradictions found for this selection.";
const BANNER = "PRELIMINARY - a model flags opposing sentences. It is not proof of a contradiction.";
const METHOD_NOTE = {
  nli: "Method: NLI model (cross-encoder/nli-deberta-v3-small). Scores are model output, not probabilities of truth.",
  "sentiment-fallback": "Method: sentiment fallback. Opposing sentiment only, not verified as logical contradiction.",
};

function EvidenceCard({ side, data, aspect }) {
  return (
    <div className="card">
      <div className="label">{side} review · {data.rating}★ · {data.review_id}</div>
      <p className="review-text">{plain(data.quote)}</p>
      <div className="muted small">Aspect: {aspect}</div>
    </div>
  );
}

function Conflicts({ focus, clearFocus }) {
  const { resultsVersion } = useApp();
  const { data, error, loading } = useApi("/contradictions", [resultsVersion]);
  const [product, setProduct] = useState(focus?.product_id ?? "");
  const [aspect, setAspect] = useState(focus?.aspect ?? "");
  const items = data?.conflicts ?? [];
  const products = useMemo(() => [...new Set(items.map((i) => i.product_id))].sort(), [items]);
  const aspects = useMemo(() => [...new Set(items.map((i) => i.aspect))].sort(), [items]);
  if (!data) return <Fetching loading={loading} error={error} />;
  const shown = items.filter((i) => (!product || i.product_id === product) && (!aspect || i.aspect === aspect));
  const reset = () => { setProduct(""); setAspect(""); clearFocus(); };

  return (
    <>
      <section className="card">
        <div className="label">Filters</div>
        <div className="filter-bar">
          <select value={product} onChange={(e) => setProduct(e.target.value)} aria-label="Product">
            <option value="">All products ({products.length})</option>
            {products.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select value={aspect} onChange={(e) => setAspect(e.target.value)} aria-label="Aspect">
            <option value="">All aspects</option>
            {aspects.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <button type="button" className="chip" disabled={!product && !aspect} onClick={reset}>Reset</button>
        </div>
        <p className="muted small">
          {fmt(shown.length)} of {fmt(items.length)} aspect matches shown ({fmt(data.unique_pairs)} unique review pairs overall; one pair can match two aspects). {METHOD_NOTE[items[0]?.method] ?? ""}
        </p>
      </section>

      {shown.length === 0 && <section className="card"><p>{NO_RESULT}</p></section>}

      {shown.slice(0, 50).map((c, idx) => (
        <section key={idx} className="card">
          <div className="label">{c.aspect} · product {c.product_id} · {c.verdict}</div>
          <div className="grid-2">
            <EvidenceCard side="Positive" data={c.observed_evidence.positive} aspect={c.aspect} />
            <EvidenceCard side="Negative" data={c.observed_evidence.negative} aspect={c.aspect} />
          </div>
          <div className="label">Possible interpretation</div>
          <p className="description">{c.possible_interpretation}</p>
          <div className="label">Unknown or missing context</div>
          <ul className="note">{c.unknown_or_missing_context.map((u) => <li key={u}>{u}</li>)}</ul>
        </section>
      ))}
      {shown.length > 50 && <p className="muted small">Showing first 50 of {fmt(shown.length)}.</p>}
    </>
  );
}

export default function ContradictionInvestigator({ focus, clearFocus }) {
  return (
    <div className="page">
      <PageHead title="Contradiction Investigator" banner={BANNER} />
      <Gated><Conflicts focus={focus} clearFocus={clearFocus} /></Gated>
    </div>
  );
}
