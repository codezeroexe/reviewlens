import { useEffect, useMemo, useState } from "react";
import { useApp } from "./AppState.jsx";
import { fmt, getJson, plain, postJson, useApi } from "./api.js";
import { Fetching, Gated, PageHead } from "./ui.jsx";

const BANNER = "Heuristic / similarity-based signals. Not a validated fake-review classifier.";
const EMPTY = "No suspicious signals found for this selection.";

function Flags({ focus, clearFocus }) {
  const { resultsVersion } = useApp();
  const { data, error, loading } = useApi("/suspicion", [resultsVersion]);
  const [level, setLevel] = useState("");
  const [product, setProduct] = useState(focus?.product_id ?? "");
  const [signal, setSignal] = useState("");
  const [showDismissed, setShowDismissed] = useState(false);
  const [selected, setSelected] = useState(null);
  const [similar, setSimilar] = useState({ rows: [], error: null });
  const [dismissed, setDismissed] = useState({});
  const [actionError, setActionError] = useState(null);

  useEffect(() => { if (data) setDismissed(data.dismissed); }, [data]);
  const rows = data?.rows ?? [];
  const products = useMemo(() => [...new Set(rows.map((r) => r.product_id))].sort(), [rows]);
  const signals = useMemo(() => [...new Set(rows.flatMap((r) => (r.signals ? r.signals.split("; ") : [])))].sort(), [rows]);
  if (!data) return <Fetching loading={loading} error={error} />;

  const nameOf = (id) => data.names?.[id] ?? id;
  const shown = rows.filter((r) =>
    (!level || r.category === level) && (!product || r.product_id === product) &&
    (!signal || r.signals.split("; ").includes(signal)) && (showDismissed || !dismissed[r.review_id]));

  async function openReview(row) {
    setSelected(row); setSimilar({ rows: [], error: null });
    try { setSimilar({ rows: await getJson(`/suspicion/similar/${encodeURIComponent(row.review_id)}`), error: null }); }
    catch (e) { setSimilar({ rows: [], error: e.message }); }
  }

  async function dismissFlag(id) {
    setActionError(null);
    try {
      const entry = await postJson("/suspicion/dismiss", { review_id: id, note: "" });
      setDismissed((prev) => ({ ...prev, [id]: entry }));
    } catch (e) { setActionError(e.message); }
  }

  return (
    <>
      <div className="card muted small">
        Rule: 0 signals = No signals, 1 = Low, 2 = Medium, 3+ = High. Counts of different signals, not a probability.
        {" "}{fmt(data.five_stars_flagged)} of {fmt(rows.length)} flags match the phrase “five stars”, often a rating headline rather than promotion.
        {" "}Legacy model prediction: not available (no existing detector in this project).
      </div>

      <section className="card">
        <div className="label">Filters</div>
        <div className="filter-bar">
          <select value={level} onChange={(e) => setLevel(e.target.value)} aria-label="Level">
            <option value="">All levels</option>
            {["Low", "Medium", "High"].map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
          <select value={product} onChange={(e) => setProduct(e.target.value)} aria-label="Product">
            <option value="">All products</option>
            {products.map((p) => <option key={p} value={p}>{nameOf(p)}</option>)}
          </select>
          <select value={signal} onChange={(e) => setSignal(e.target.value)} aria-label="Signal">
            <option value="">Any signal</option>
            {signals.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <label><input type="checkbox" checked={showDismissed} onChange={(e) => setShowDismissed(e.target.checked)} /> show dismissed</label>
          <button type="button" className="chip" disabled={!level && !product && !signal}
                  onClick={() => { setLevel(""); setProduct(""); setSignal(""); clearFocus(); }}>Reset</button>
        </div>
        <p className="muted small">{fmt(shown.length)} flagged review(s) shown.</p>
      </section>

      {shown.length === 0 && <section className="card"><p>{EMPTY}</p></section>}

      {shown.length > 0 && (
        <section className="card">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Review</th><th>Category</th><th>Signals</th><th>Product</th></tr></thead>
              <tbody>
                {shown.slice(0, 200).map((r) => (
                  <tr key={r.review_id} className="clickable" tabIndex={0} style={dismissed[r.review_id] ? { opacity: 0.5 } : undefined}
                      onClick={() => openReview(r)} onKeyDown={(e) => e.key === "Enter" && openReview(r)}>
                    <td>{r.review_id}{dismissed[r.review_id] ? " (dismissed)" : ""}</td>
                    <td>{r.category}</td><td>{r.signals}</td><td title={r.product_id}>{nameOf(r.product_id)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {shown.length > 200 && <p className="muted small">Showing first 200 of {fmt(shown.length)}.</p>}
        </section>
      )}

      {selected && (
        <section className="card">
          <div className="label">Review {selected.review_id} · {selected.category}</div>
          <p className="review-text">{plain(selected.review_text)}</p>
          <div className="muted small">Rating {selected.rating} · verified {String(selected.verified_purchase)} · vine {String(selected.vine)}</div>
          <div className="label">Fired signals</div>
          <p className="description">{selected.signals || "none"}</p>
          <div className="label">Similar reviews</div>
          <Fetching error={similar.error} />
          {similar.rows.length === 0 && !similar.error && <p className="muted">None.</p>}
          {similar.rows.map((s) => <p key={s.review_id} className="review-text small">{s.review_id} (rating {s.rating}): {plain(s.review_text)}</p>)}
          <div className="label">Explanation</div>
          <p className="note">{selected.explanation}</p>
          {actionError && <div className="card-slim danger" role="alert">{actionError}</div>}
          <button type="button" className="cta" disabled={Boolean(dismissed[selected.review_id])} onClick={() => dismissFlag(selected.review_id)}>
            {dismissed[selected.review_id] ? "Dismissed" : "Dismiss flag"}
          </button>
        </section>
      )}
    </>
  );
}

export default function SuspicionInvestigator({ focus, clearFocus }) {
  return (
    <div className="page">
      <PageHead title="Suspicious Review Investigator" banner={BANNER} />
      <Gated><Flags focus={focus} clearFocus={clearFocus} /></Gated>
    </div>
  );
}
