import { useEffect, useState } from "react";
import { useApp } from "./AppState.jsx";
import { fmt, getJson, plain, useApi } from "./api.js";
import { Fetching, Gated, PageHead } from "./ui.jsx";

const TYPE_LABEL = {
  common_problem: "Common problem", experience_gap: "Experience gap", informative_evidence: "Informative evidence",
  emerging: "Emerging", comparison: "Comparison", quality_warning: "Quality warning",
};

function Card({ ins, onInspect, open, evidence }) {
  return (
    <div className="card">
      <div className="label">{TYPE_LABEL[ins.type] ?? ins.type}</div>
      <h3 className="card-title">{ins.headline}</h3>
      <p className="description">{ins.interpretation}</p>
      <ul className="note">
        {ins.numbers.map((n) => <li key={n.label}>{n.label}: {fmt(n.numerator)} of {fmt(n.denominator)} ({n.pct}%)</li>)}
      </ul>
      {ins.excerpts.map((e) => <p key={e.review_id + e.text} className="review-text small">"{plain(e.text)}" <span className="muted">({e.review_id})</span></p>)}
      {ins.warning && <span className="chip">{ins.warning}</span>}
      <div><button type="button" className="chip" onClick={() => onInspect(ins.id)}>{open ? "Hide evidence" : "Inspect evidence"}</button></div>
      {open && (
        <div className="table-wrap">
          <Fetching loading={evidence.loading} error={evidence.error} />
          {!evidence.loading && !evidence.error && (
            <table>
              <thead><tr><th>Review</th><th>Product</th><th>Rating</th><th>Text</th></tr></thead>
              <tbody>
                {evidence.rows.map((r) => <tr key={r.review_id}><td>{r.review_id}</td><td title={r.product_id}>{r.product_name ?? r.product_id}</td><td>{r.rating}</td><td className="review-text">{plain(r.review_text)}</td></tr>)}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

function List({ focus, clearFocus }) {
  const { resultsVersion } = useApp();
  const overview = useApi("/insights", [resultsVersion]);
  const all = useApi("/insights/all", [resultsVersion]);
  const [view, setView] = useState(focus?.insight_id ? "all" : "overview");
  const [typeFilter, setTypeFilter] = useState("");
  const [openId, setOpenId] = useState(null);
  const [evidence, setEvidence] = useState({ rows: [], loading: false, error: null });

  async function inspect(id) {
    if (openId === id) { setOpenId(null); return; }
    setOpenId(id); setEvidence({ rows: [], loading: true, error: null });
    try { setEvidence({ rows: await getJson(`/insights/evidence/${encodeURIComponent(id)}`), loading: false, error: null }); }
    catch (e) { setEvidence({ rows: [], loading: false, error: e.message }); }
  }

  // Deep link from the overview: open that insight's evidence once the list is here.
  useEffect(() => { if (focus?.insight_id && all.data && openId === null) inspect(focus.insight_id); }, [all.data]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!overview.data) return <Fetching loading={overview.loading} error={overview.error} />;
  const list = view === "overview" ? overview.data.insights : (all.data ?? []).filter((i) => !typeFilter || i.type === typeFilter);
  return (
    <>
      <div className="chips">
        <button type="button" className={view === "overview" ? "chip active" : "chip"} onClick={() => setView("overview")}>Overview</button>
        <button type="button" className={view === "all" ? "chip active" : "chip"} onClick={() => setView("all")}>All insights ({fmt(all.data?.length)})</button>
        {view === "all" && (
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} aria-label="Type">
            <option value="">All types</option>
            {Object.entries(TYPE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        )}
        {focus && <button type="button" className="chip" onClick={clearFocus}>Clear link</button>}
      </div>
      {overview.data.note && <div className="card muted small">{overview.data.note}</div>}
      <Fetching error={all.error} />
      {list.length === 0 && <div className="card"><p>No insights qualify for this view. Omitted types are listed in the run report.</p></div>}
      {list.map((ins) => <Card key={ins.id} ins={ins} onInspect={inspect} open={openId === ins.id} evidence={openId === ins.id ? evidence : { rows: [] }} />)}
      <p className="muted small">Quality warnings are heuristic signals, not proof. A usefulness prediction is not available in this app.</p>
    </>
  );
}

export default function InsightsPage({ focus, clearFocus }) {
  return (
    <div className="page">
      <PageHead title="Insights" />
      <Gated><List focus={focus} clearFocus={clearFocus} /></Gated>
    </div>
  );
}
