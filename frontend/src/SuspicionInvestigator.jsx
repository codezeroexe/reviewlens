import { useEffect, useMemo, useState } from "react";

const BANNER = "Heuristic / similarity-based signals. Not a validated fake-review classifier.";
const RULE = "Rule: 0 signals = No signals, 1 = Low, 2 = Medium, 3+ = High. Counts of different signals, not a probability.";
const EMPTY = "No suspicious signals found for this selection.";

export default function SuspicionInvestigator({ onBack }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [level, setLevel] = useState("");
  const [product, setProduct] = useState("");
  const [signal, setSignal] = useState("");
  const [showDismissed, setShowDismissed] = useState(false);
  const [selected, setSelected] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [dismissed, setDismissed] = useState({});

  useEffect(() => {
    fetch("/suspicion").then(async (r) => {
      const json = await r.json();
      if (!r.ok) throw new Error(json.error || "Request failed.");
      setData(json);
      setDismissed(json.dismissed);
    }).catch((e) => setError(e.message));
  }, []);

  const rows = data?.rows ?? [];
  const products = useMemo(() => [...new Set(rows.map((r) => r.product_id))].sort(), [rows]);
  const signals = useMemo(() => [...new Set(rows.flatMap((r) => (r.signals ? r.signals.split("; ") : [])))].sort(), [rows]);
  const shown = rows.filter((r) =>
    (!level || r.category === level) &&
    (!product || r.product_id === product) &&
    (!signal || r.signals.split("; ").includes(signal)) &&
    (showDismissed || !dismissed[r.review_id])
  );

  async function openReview(row) {
    setSelected(row);
    const res = await fetch(`/suspicion/similar/${row.review_id}`);
    setSimilar(res.ok ? await res.json() : []);
  }

  async function dismissFlag(id) {
    const res = await fetch("/suspicion/dismiss", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_id: id, note: "" }),
    });
    const entry = await res.json();
    if (res.ok) setDismissed((prev) => ({ ...prev, [id]: entry }));
  }

  return (
    <div className="page">
      <header className="header">
        <span className="brand">Suspicious Review Investigator</span>
        <button type="button" className="chip" onClick={onBack}>Back to overview</button>
      </header>

      <div className="card" style={{ borderColor: "#FF7A1A" }}><strong>{BANNER}</strong><p className="muted small">{RULE}</p></div>
      <div className="card muted small">Legacy model prediction: not available (no existing detector in this project).</div>

      {error && <div className="card muted">{error}. Run suspicion/run.py first.</div>}
      {!data && !error && <p className="muted">Loading...</p>}

      {data && (
        <>
          <section className="card">
            <div className="label">Filters</div>
            <select value={level} onChange={(e) => setLevel(e.target.value)} aria-label="Level">
              <option value="">All levels</option>
              {["Low", "Medium", "High"].map((l) => <option key={l} value={l}>{l}</option>)}
            </select>{" "}
            <select value={product} onChange={(e) => setProduct(e.target.value)} aria-label="Product">
              <option value="">All products</option>
              {products.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>{" "}
            <select value={signal} onChange={(e) => setSignal(e.target.value)} aria-label="Signal">
              <option value="">Any signal</option>
              {signals.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>{" "}
            <label><input type="checkbox" checked={showDismissed} onChange={(e) => setShowDismissed(e.target.checked)} /> show dismissed</label>
            <p className="muted small">{shown.length} flagged review(s) shown.</p>
          </section>

          {shown.length === 0 && <section className="card"><p>{EMPTY}</p></section>}

          {shown.length > 0 && (
            <section className="card">
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Review</th><th>Category</th><th>Signals</th><th>Product</th><th>Legacy</th></tr>
                  </thead>
                  <tbody>
                    {shown.slice(0, 200).map((r) => (
                      <tr key={r.review_id} className="clickable" style={dismissed[r.review_id] ? { opacity: 0.5 } : undefined}
                          onClick={() => openReview(r)}>
                        <td>{r.review_id}{dismissed[r.review_id] ? " (dismissed)" : ""}</td>
                        <td>{r.category}</td>
                        <td>{r.signals}</td>
                        <td>{r.product_id}</td>
                        <td className="muted">{r.legacy_model_prediction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {shown.length > 200 && <p className="muted small">Showing first 200 of {shown.length}.</p>}
            </section>
          )}

          {selected && (
            <section className="card">
              <div className="label">Review {selected.review_id} · {selected.category}</div>
              <p className="review-text">{selected.review_text}</p>
              <div className="muted small">Rating {selected.rating} · verified {String(selected.verified_purchase)} · vine {String(selected.vine)}</div>
              <div className="label">Fired signals</div>
              <p className="description">{selected.signals || "none"}</p>
              <div className="label">Similar reviews</div>
              {similar.length === 0 && <p className="muted">None.</p>}
              {similar.map((s) => (
                <p key={s.review_id} className="review-text small">{s.review_id} (rating {s.rating}): {s.review_text}</p>
              ))}
              <div className="label">Explanation</div>
              <p className="note">{selected.explanation}</p>
              <button type="button" className="cta" onClick={() => dismissFlag(selected.review_id)}>Dismiss flag</button>
            </section>
          )}
        </>
      )}
    </div>
  );
}
