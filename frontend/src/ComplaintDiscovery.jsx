import { useEffect, useState } from "react";
import { useApp } from "./AppState.jsx";
import { fmt, getJson, plain, useApi } from "./api.js";
import { Fetching, Gated, PageHead, displayLabel } from "./ui.jsx";

const BANNER = "PRELIMINARY - cluster quality not yet evaluated";

function ReviewList({ reviews }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Rating</th><th>Review</th><th>Similarity</th><th>Flag</th></tr></thead>
        <tbody>
          {reviews.map((r) => (
            <tr key={r.review_id}>
              <td>{r.rating}</td>
              <td className="review-text">{plain(r.review_text)}</td>
              <td>{r.similarity ?? "—"}</td>
              <td>{r.ambiguous ? "ambiguous" : r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Clusters({ focus, clearFocus }) {
  const { resultsVersion } = useApp();
  const { data, error, loading } = useApi("/complaints", [resultsVersion]);
  const [selected, setSelected] = useState(null);       // cluster id, or "noise"
  const [reviews, setReviews] = useState({ rows: [], error: null, loading: false });

  async function show(target) {
    setSelected(target);
    setReviews({ rows: [], error: null, loading: true });
    try {
      const rows = await getJson(target === "noise" ? "/complaints/unclustered" : `/complaints/cluster/${target}/reviews`);
      setReviews({ rows, error: null, loading: false });
    } catch (e) {
      setReviews({ rows: [], error: e.message, loading: false });
    }
  }

  // Deep link from an insight or the overview: open that cluster once the list is here.
  useEffect(() => {
    if (data && focus?.cluster_id !== undefined && selected === null) show(focus.cluster_id);
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!data) return <Fetching loading={loading} error={error} />;
  const cluster = data.clusters.find((c) => c.cluster_id === selected);
  return (
    <>
      <section className="kpis">
        <div className="card kpi"><div className="label">Clusters</div><div className="kpi-value">{data.meta.cluster_count}</div></div>
        <div className="card kpi"><div className="label">Clustered reviews</div><div className="kpi-value">{fmt(data.meta.clustered)}</div></div>
        <div className="card kpi">
          <div className="label">Unclustered</div>
          <button type="button" className="chip" onClick={() => (selected === "noise" ? setSelected(null) : show("noise"))}>
            {fmt(data.meta.unclustered)} {selected === "noise" ? "(hide)" : "(show)"}
          </button>
        </div>
        <div className="card kpi"><div className="label">Embedding</div><div className="kpi-text small">{data.meta.embedding_method}</div></div>
      </section>

      <section className="card">
        <div className="label">Problems found (click a row)</div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Problem</th><th>Size</th><th>Products</th><th>Sentiment (pos / mixed / neg)</th><th>Useful</th><th>Suspicious</th></tr></thead>
            <tbody>
              {data.clusters.map((c) => (
                <tr key={c.cluster_id} className="clickable" tabIndex={0} onClick={() => show(c.cluster_id)}
                    onKeyDown={(e) => e.key === "Enter" && show(c.cluster_id)}>
                  <td>{displayLabel(c)}{c.label_quality === "generic" && <div className="muted small">top terms: {c.label}</div>}</td>
                  <td>{fmt(c.size)}</td>
                  <td>{fmt(c.products_covered)}</td>
                  <td>{c.sentiment_mix.positive_pct}% / {c.sentiment_mix.mixed_pct}% / {c.sentiment_mix.negative_pct}%</td>
                  <td className="muted">{c.usefulness}</td>
                  <td className="muted">{c.suspicious_pct}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selected !== null && (
        <section className="card">
          <div className="row-between">
            <div className="label">
              {selected === "noise" ? "Unclustered reviews (first 200)" : `Reviews in "${cluster ? displayLabel(cluster) : selected}" (${fmt(reviews.rows.length)} rows)`}
            </div>
            {focus && <button type="button" className="chip" onClick={() => { clearFocus(); setSelected(null); }}>Clear</button>}
          </div>
          <Fetching loading={reviews.loading} error={reviews.error} />
          {!reviews.loading && !reviews.error && <ReviewList reviews={reviews.rows} />}
        </section>
      )}
    </>
  );
}

export default function ComplaintDiscovery({ focus, clearFocus }) {
  return (
    <div className="page">
      <PageHead title="Complaint Discovery" banner={BANNER} />
      <Gated><Clusters focus={focus} clearFocus={clearFocus} /></Gated>
    </div>
  );
}
