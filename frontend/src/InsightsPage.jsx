import { useEffect, useState } from "react";

const TYPE_LABEL = {
  common_problem: "Common problem", experience_gap: "Experience gap", informative_evidence: "Informative evidence",
  emerging: "Emerging", comparison: "Comparison", quality_warning: "Quality warning",
};

function Card({ ins, onInspect, open, evidence }) {
  return (
    <div className="card">
      <div className="label">{TYPE_LABEL[ins.type] ?? ins.type}</div>
      <h3>{ins.headline}</h3>
      <p className="description">{ins.interpretation}</p>
      <ul className="note">
        {ins.numbers.map((n) => (
          <li key={n.label}>{n.label}: {n.numerator} of {n.denominator} ({n.pct}%)</li>
        ))}
      </ul>
      {ins.excerpts.map((e) => (
        <p key={e.review_id + e.text} className="review-text small">"{e.text}" <span className="muted">({e.review_id})</span></p>
      ))}
      {ins.warning && <span className="chip">{ins.warning}</span>}
      <div>
        <button type="button" className="chip" onClick={() => onInspect(ins.id)}>{open ? "Hide evidence" : "Inspect evidence"}</button>
      </div>
      {open && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Review</th><th>Product</th><th>Rating</th><th>Text</th></tr></thead>
            <tbody>
              {evidence.map((r) => (
                <tr key={r.review_id}><td>{r.review_id}</td><td>{r.product_id}</td><td>{r.rating}</td><td className="review-text">{r.review_text}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function InsightsPage({ onBack }) {
  const [overview, setOverview] = useState(null);
  const [all, setAll] = useState(null);
  const [error, setError] = useState(null);
  const [view, setView] = useState("overview");
  const [typeFilter, setTypeFilter] = useState("");
  const [openId, setOpenId] = useState(null);
  const [evidence, setEvidence] = useState([]);

  useEffect(() => {
    fetch("/insights").then((r) => r.json()).then(setOverview).catch((e) => setError(e.message));
    fetch("/insights/all").then((r) => r.json()).then(setAll).catch(() => {});
  }, []);

  async function inspect(id) {
    if (openId === id) { setOpenId(null); return; }
    setOpenId(id);
    const res = await fetch(`/insights/evidence/${id}`);
    setEvidence(res.ok ? await res.json() : []);
  }

  const list = view === "overview" ? (overview?.insights ?? []) : (all ?? []).filter((i) => !typeFilter || i.type === typeFilter);

  return (
    <div className="page">
      <header className="header">
        <span className="brand">Insights</span>
        <button type="button" className="chip" onClick={onBack}>Back to overview</button>
      </header>

      {error && <div className="card muted">{error}</div>}
      {!overview && !error && <p className="muted">Loading...</p>}

      {overview && (
        <>
          <div className="chips">
            <button type="button" className={view === "overview" ? "chip active" : "chip"} onClick={() => setView("overview")}>Overview</button>
            <button type="button" className={view === "all" ? "chip active" : "chip"} onClick={() => setView("all")}>All insights</button>
            {view === "all" && (
              <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} aria-label="Type">
                <option value="">All types</option>
                {Object.entries(TYPE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            )}
          </div>

          {overview.note && <div className="card muted small">{overview.note}</div>}
          {list.length === 0 && <div className="card"><p>No insights qualify for this view. Omitted types are listed in the run report.</p></div>}

          {list.map((ins) => (
            <Card key={ins.id} ins={ins} onInspect={inspect} open={openId === ins.id} evidence={openId === ins.id ? evidence : []} />
          ))}

          <p className="muted small">Usefulness = model prediction. Suspicion = warning signal, not proof.</p>
        </>
      )}
    </div>
  );
}
