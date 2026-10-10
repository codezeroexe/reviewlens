import { useEffect, useState } from "react";

const BANNER = "PRELIMINARY - cluster quality not yet evaluated";

async function getJson(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

function ReviewList({ reviews }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Rating</th>
            <th>Review</th>
            <th>Similarity</th>
            <th>Flag</th>
          </tr>
        </thead>
        <tbody>
          {reviews.map((r) => (
            <tr key={r.review_id}>
              <td>{r.rating}</td>
              <td className="review-text">{r.review_text}</td>
              <td>{r.similarity ?? "—"}</td>
              <td>{r.ambiguous ? "ambiguous" : r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ComplaintDiscovery({ onBack }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [showUnclustered, setShowUnclustered] = useState(false);
  const [unclustered, setUnclustered] = useState([]);

  useEffect(() => {
    getJson("/complaints").then(setData).catch((e) => setError(e.message));
  }, []);

  async function openCluster(id) {
    setSelected(id);
    setShowUnclustered(false);
    setReviews(await getJson(`/complaints/cluster/${id}/reviews`));
  }

  async function toggleUnclustered() {
    const next = !showUnclustered;
    setShowUnclustered(next);
    setSelected(null);
    if (next) setUnclustered(await getJson("/complaints/unclustered"));
  }

  return (
    <div className="page">
      <header className="header">
        <span className="brand">Complaint Discovery</span>
        <button type="button" className="chip" onClick={onBack}>Back to overview</button>
      </header>

      <div className="card" style={{ borderColor: "#FF7A1A" }}>
        <strong>{BANNER}</strong>
      </div>

      {error && <div className="card muted">{error}. Run complaints/run.py first.</div>}
      {!data && !error && <p className="muted">Loading...</p>}

      {data && (
        <>
          <section className="kpis">
            <div className="card kpi">
              <div className="label">Clusters</div>
              <div className="kpi-value">{data.meta.cluster_count}</div>
            </div>
            <div className="card kpi">
              <div className="label">Clustered reviews</div>
              <div className="kpi-value">{data.meta.clustered}</div>
            </div>
            <div className="card kpi">
              <div className="label">Unclustered</div>
              <button type="button" className="chip" onClick={toggleUnclustered}>
                {data.meta.unclustered} {showUnclustered ? "(hide)" : "(show)"}
              </button>
            </div>
            <div className="card kpi">
              <div className="label">Embedding</div>
              <div className="kpi-text small">{data.meta.embedding_method}</div>
            </div>
          </section>

          <section className="card">
            <div className="label">Problems found (click a row)</div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Problem (top terms)</th>
                    <th>Size</th>
                    <th>Products</th>
                    <th>Sentiment (pos / mixed / neg)</th>
                    <th>Useful</th>
                    <th>Suspicious</th>
                  </tr>
                </thead>
                <tbody>
                  {data.clusters.map((c) => (
                    <tr key={c.cluster_id} className="clickable" onClick={() => openCluster(c.cluster_id)}>
                      <td>{c.label}</td>
                      <td>{c.size}</td>
                      <td>{c.products_covered}</td>
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
              <div className="label">
                Reviews in "{data.clusters.find((c) => c.cluster_id === selected)?.label}" ({reviews.length} rows)
              </div>
              <ReviewList reviews={reviews} />
            </section>
          )}

          {showUnclustered && (
            <section className="card">
              <div className="label">Unclustered reviews (first 200)</div>
              <ReviewList reviews={unclustered} />
            </section>
          )}
        </>
      )}
    </div>
  );
}
