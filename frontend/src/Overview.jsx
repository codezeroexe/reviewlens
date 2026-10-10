import { useState } from "react";
import { useApp } from "./AppState.jsx";
import { fmt, plain, useApi } from "./api.js";
import { Fetching, Gated, PageHead, displayLabel } from "./ui.jsx";

const TYPE_TO_VIEW = { common_problem: "complaints", experience_gap: "contradictions", quality_warning: "suspicion", comparison: "insights" };
const TYPE_LABEL = {
  common_problem: "Common problem", experience_gap: "Experience gap", quality_warning: "Quality warning",
  comparison: "Comparison", emerging: "Emerging", informative_evidence: "Informative evidence",
};
const BADGE_CLASS = { Measured: "badge-accent", "Model prediction": "badge-warning", "Possible interpretation": "badge-muted" };
const EMPTY_FILTERS = { product: "", rating: "", date_from: "", date_to: "" };

const Badge = ({ kind }) => <span className={`badge ${BADGE_CLASS[kind]}`}>{kind}</span>;

function FilterBar({ options, filters, setFilters }) {
  const set = (key) => (e) => setFilters({ ...filters, [key]: e.target.value });
  const active = Object.values(filters).some(Boolean);
  return (
    <div className="filter-bar" role="group" aria-label="Filters">
      {options.products.length > 0 && (
        <select value={filters.product} onChange={set("product")} aria-label="Product">
          <option value="">All products (30+ reviews)</option>
          {options.products.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      )}
      {options.has_rating && (
        <select value={filters.rating} onChange={set("rating")} aria-label="Rating">
          <option value="">All ratings</option>
          {[1, 2, 3, 4, 5].map((r) => <option key={r} value={r}>{r} star</option>)}
        </select>
      )}
      {options.has_date && (
        <>
          <input type="date" value={filters.date_from} min={options.date_min} max={options.date_max} onChange={set("date_from")} aria-label="From date" />
          <input type="date" value={filters.date_to} min={options.date_min} max={options.date_max} onChange={set("date_to")} aria-label="To date" />
        </>
      )}
      <button type="button" className="chip" disabled={!active} onClick={() => setFilters(EMPTY_FILTERS)}>Reset</button>
    </div>
  );
}

/** The dataset itself: filters, counts, and the matching reviews. Works for demo and uploads. */
function DatasetSection() {
  const { dataset, resultsVersion } = useApp();
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const qs = new URLSearchParams(Object.entries(filters).filter(([, v]) => v)).toString();
  const { data, error, loading } = useApi(dataset.kind ? `/app/view?${qs}` : null, [dataset.name, dataset.rows, resultsVersion]);

  if (!dataset.kind) {
    return <section className="card"><div className="label">Dataset</div><p>Load the demo dataset or upload a CSV, TSV or XLSX file to begin.</p></section>;
  }
  if (!data) return <Fetching loading={loading} error={error} />;
  if (!data.available) return <section className="card"><p className="muted">{data.message}</p></section>;

  const m = data.metrics;
  const tiles = [
    { label: data.filtered ? "Reviews (filtered)" : "Reviews", value: fmt(m.reviews) },
    { label: "Products", value: fmt(m.products) },
    { label: "Date span", value: m.date_span?.every(Boolean) ? m.date_span.join(" → ") : "n/a", small: true },
    { label: "Complaint reviews (1–3★)", value: fmt(m.complaint_reviews) },
    ...(m.flagged === null ? [] : [{ label: "Flagged (any signal)", value: fmt(m.flagged) }]),
  ];
  return (
    <section className="overview">
      <h2 className="section-title">Dataset</h2>
      <FilterBar options={data.options} filters={filters} setFilters={setFilters} />
      <Fetching error={error} />
      <div className="metrics">
        {tiles.map((t) => (
          <div key={t.label} className="card tile">
            <div className="label">{t.label}</div>
            <div className={t.small ? "tile-value tile-value-small" : "tile-value"}>{t.value}</div>
            <Badge kind="Measured" />
          </div>
        ))}
      </div>
      <div className="card">
        <div className="label">Matching reviews: showing {data.reviews.length} of {fmt(data.matching)}{data.reviews.length > 1 ? ", newest first" : ""}</div>
        {data.reviews.length === 0 ? <p className="muted">No review matches these filters.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Product</th><th>Rating</th><th>Review</th></tr></thead>
              <tbody>
                {data.reviews.map((r) => (
                  <tr key={r.review_id}><td>{r.date ?? "—"}</td><td>{r.product_id ?? "—"}</td><td>{r.rating ?? "—"}</td><td className="review-text">{plain(r.text)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

/** Analysis findings. Full-sample results: the dataset filters above do not change them. */
function Findings({ go }) {
  const { resultsVersion } = useApp();
  const { data, error, loading } = useApi("/app/overview", [resultsVersion]);
  if (!data) return <Fetching loading={loading} error={error} />;
  if (!data.available) return <section className="card"><p className="muted">{data.message}</p></section>;
  const sus = data.suspicious;
  const counts = data.contradiction_counts;
  return (
    <section className="overview">
      <h2 className="section-title">Findings</h2>
      <p className="muted small">Full-sample results from the analysis run. The filters above do not change them.</p>

      <div className="cards-3">
        {data.discoveries.length === 0 && <p className="muted">No discovery qualified with enough evidence.</p>}
        {data.discoveries.map((d) => (
          <div key={d.id} className="card">
            <div className="row-between">
              <span className="label">{TYPE_LABEL[d.type] ?? d.type}</span>
              <Badge kind={d.type === "experience_gap" ? "Possible interpretation" : "Measured"} />
            </div>
            <h3 className="card-title">{d.headline}</h3>
            <p className="muted small">{d.interpretation}</p>
            {d.numbers.map((n) => (
              <div key={n.label} className="num-line">{fmt(n.numerator)} of {fmt(n.denominator)} ({n.pct}%) <span className="muted small">{n.label}</span></div>
            ))}
            {d.warning && <span className="badge badge-warning">{d.warning}</span>}
            <button type="button" className="chip"
                    onClick={() => go(TYPE_TO_VIEW[d.type] ?? "insights", d.type === "comparison" ? { insight_id: d.id } : d.evidence_ref?.filters)}>
              Investigate
            </button>
          </div>
        ))}
      </div>

      <div className="two-col">
        <div className="card">
          <div className="row-between">
            <h2 className="section-title">Complaint clusters</h2>
            <button type="button" className="chip" onClick={() => go("complaints")}>Open</button>
          </div>
          {data.clusters.length === 0 && <p className="muted">No complaint cluster found.</p>}
          {data.clusters.map((c) => {
            const mix = c.sentiment_mix;
            return (
              <button key={c.cluster_id} type="button" className="list-row" onClick={() => go("complaints", { cluster_id: c.cluster_id })}>
                <div className="row-between"><span>{displayLabel(c)}</span><span className="muted small">{fmt(c.size)} reviews</span></div>
                <div className="stack-bar" aria-label="sentiment mix">
                  <span style={{ width: `${mix.positive_pct}%`, background: "var(--sent-pos)" }} />
                  <span style={{ width: `${mix.mixed_pct}%`, background: "var(--sent-mix)" }} />
                  <span style={{ width: `${mix.negative_pct}%`, background: "var(--sent-neg)" }} />
                </div>
                {c.representative_reviews[0] && <p className="muted small clamp">"{plain(c.representative_reviews[0].text)}"</p>}
              </button>
            );
          })}
          <Badge kind="Measured" />
        </div>

        <div className="card">
          <div className="row-between">
            <h2 className="section-title">Contradictions</h2>
            <button type="button" className="chip" onClick={() => go("contradictions")}>Open</button>
          </div>
          <p className="muted small">{fmt(counts.pairs)} review pairs ({fmt(counts.aspect_matches)} aspect matches). Top 3 by NLI score:</p>
          {data.contradictions.length === 0 && <p className="muted">No contradiction found.</p>}
          {data.contradictions.map((c, i) => (
            <button key={i} type="button" className="list-row" onClick={() => go("contradictions", { product_id: c.product_id, aspect: c.aspect })}>
              <div className="small muted">{c.aspect} · product {c.product_id}</div>
              <p className="small clamp">+ "{plain(c.observed_evidence.positive.quote)}" ({c.observed_evidence.positive.rating}★)</p>
              <p className="small clamp">− "{plain(c.observed_evidence.negative.quote)}" ({c.observed_evidence.negative.rating}★)</p>
            </button>
          ))}
          <Badge kind="Possible interpretation" />
        </div>
      </div>

      <div className="card">
        <div className="row-between">
          <h2 className="section-title">Suspicious reviews</h2>
          <button type="button" className="chip" onClick={() => go("suspicion")}>View evidence</button>
        </div>
        <p className="muted small">
          Warning signals, not proof. {fmt(sus.flagged_total)} flagged; {fmt(sus.flagged_five_stars)} of them match the phrase “five stars”, which is often a rating headline rather than promotion.
        </p>
        <div className="kv-row">{Object.entries(sus.by_level).map(([k, v]) => <span key={k} className="kv"><span className="muted small">{k}</span> {fmt(v)}</span>)}</div>
        <div className="kv-row">{Object.entries(sus.by_signal).map(([k, v]) => <span key={k} className="kv"><span className="muted small">{k}</span> {fmt(v)}</span>)}</div>
        <Badge kind="Measured" />
      </div>

      {data.notes?.trend && <p className="muted small">{data.notes.trend}</p>}
    </section>
  );
}

export default function Overview({ go }) {
  return (
    <div className="page">
      <PageHead title="Overview" />
      <DatasetSection />
      <Gated><Findings go={go} /></Gated>
    </div>
  );
}
