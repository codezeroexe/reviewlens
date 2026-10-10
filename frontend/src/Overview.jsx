import { useEffect, useState } from "react";
import { useStatus } from "./Shell.jsx";

const TYPE_TO_VIEW = { common_problem: "complaints", experience_gap: "contradictions", quality_warning: "suspicion", comparison: "insights" };
const TYPE_LABEL = {
  common_problem: "Common problem", experience_gap: "Experience gap", quality_warning: "Quality warning",
  comparison: "Comparison", emerging: "Emerging", informative_evidence: "Informative evidence",
};
const SENT_COLORS = { positive: "#3fb68b", mixed: "#b5b5b5", negative: "#e5604d" };

function Badge({ kind }) {
  const cls = { Measured: "badge-accent", "Model prediction": "badge-warning", "Possible interpretation": "badge-muted" }[kind];
  return <span className={`badge ${cls}`}>{kind}</span>;
}

function NotRun({ text = "Run analysis to see this." }) {
  return <p className="muted">{text}</p>;
}

const EMPTY_FILTERS = { product: "", rating: "", date_from: "", date_to: "" };

function FilterBar({ options, filters, setFilters }) {
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });
  const active = Object.values(filters).some(Boolean);
  return (
    <div className="filter-bar" role="group" aria-label="Filters">
      <select value={filters.product} onChange={set("product")} aria-label="Product">
        <option value="">All products</option>
        {options.products.map((p) => <option key={p} value={p}>{p}</option>)}
      </select>
      <select value={filters.rating} onChange={set("rating")} aria-label="Rating">
        <option value="">All ratings</option>
        {[1, 2, 3, 4, 5].map((r) => <option key={r} value={r}>{r} star</option>)}
      </select>
      <input type="date" value={filters.date_from} min={options.date_min} max={options.date_max} onChange={set("date_from")} aria-label="From date" />
      <input type="date" value={filters.date_to} min={options.date_min} max={options.date_max} onChange={set("date_to")} aria-label="To date" />
      <button type="button" className="chip" disabled={!active} onClick={() => setFilters(EMPTY_FILTERS)}>Reset</button>
    </div>
  );
}

export default function Overview({ setView }) {
  const { status } = useStatus();
  const [data, setData] = useState(null);
  const [view, setViewData] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const ready = status?.data_state === "Ready";
  const uploaded = Boolean(status?.analysis_on);

  useEffect(() => {
    fetch("/app/overview").then((r) => r.json()).then(setData).catch(() => setData({ available: false }));
  }, [ready, status?.job?.runtime_s]);

  useEffect(() => {
    const qs = new URLSearchParams(Object.entries(filters).filter(([, v]) => v)).toString();
    fetch(`/app/view?${qs}`).then((r) => r.json()).then(setViewData).catch(() => setViewData(null));
  }, [filters, status?.stats?.review_count, status?.stats?.source]);

  if (!data) return <p className="muted">Loading…</p>;
  if (uploaded) {
    const um = view?.metrics ?? {};
    return (
      <div className="overview">
        {view?.options && <FilterBar options={view.options} filters={filters} setFilters={setFilters} />}
        <section className="metrics">
          <div className="card tile"><div className="label">Reviews (uploaded)</div><div className="tile-value">{um.reviews ?? "—"}</div><Badge kind="Measured" /></div>
          <div className="card tile"><div className="label">Products</div><div className="tile-value">{um.products ?? "—"}</div><Badge kind="Measured" /></div>
          <div className="card tile"><div className="label">Date span</div><div className="tile-value tile-value-small">{um.date_span?.join(" → ") ?? "—"}</div><Badge kind="Measured" /></div>
          <div className="card tile"><div className="label">Complaint reviews (1–3★)</div><div className="tile-value">{um.complaint_reviews ?? "—"}</div><Badge kind="Measured" /></div>
        </section>
        <section className="card"><NotRun text={`Showing "${status?.stats?.source}". Analysis (clusters, discoveries, contradictions, suspicion) is not run on uploads. Load the demo dataset to see those.`} /></section>
      </div>
    );
  }
  if (view && !view.available) {
    return <section className="card"><div className="label">Overview</div><NotRun text={view.message} /></section>;
  }
  if (!data.available && !view) {
    return (
      <section className="card">
        <div className="label">Overview</div>
        <NotRun text={status?.stats?.review_count ? "Dataset loaded. Run analysis to see discoveries." : "Load the demo dataset, then run analysis."} />
      </section>
    );
  }

  const m = data.metrics;
  const vm = view?.metrics ?? {};
  const fmt = (n) => (n === null || n === undefined ? "n/a" : Number(n).toLocaleString());
  const tiles = [
    { label: view?.filtered ? "Reviews (filtered)" : "Reviews", value: fmt(vm.reviews) },
    { label: "Products", value: fmt(vm.products) },
    { label: "Date span", value: vm.date_span?.join(" → "), small: true },
    { label: "Complaint reviews (1–3★)", value: fmt(vm.complaint_reviews) },
    { label: "Flagged (any signal)", value: vm.flagged === null ? "n/a (uploads not analysed)" : fmt(vm.flagged), small: vm.flagged === null },
  ];

  return (
    <div className="overview">
      {view?.options && <FilterBar options={view.options} filters={filters} setFilters={setFilters} />}
      <section className="metrics">
        {tiles.map((t) => (
          <div key={t.label} className="card tile">
            <div className="label">{t.label}</div>
            <div className={t.small ? "tile-value tile-value-small" : "tile-value"}>{t.value ?? "—"}</div>
            <Badge kind="Measured" />
          </div>
        ))}
      </section>

      {uploaded && <div className="card-slim muted">Discoveries, clusters, contradictions and suspicion results below are from the demo sample. They were not run on the uploaded file.</div>}
      {view?.filtered && !uploaded && <div className="card-slim muted">Filters change the tiles above. Discoveries and clusters are full-sample outputs and do not change.</div>}

      <section>
        <h2 className="section-title">Key discoveries</h2>
        {data.discoveries.length === 0 && <NotRun text="No discovery qualified with enough evidence." />}
        <div className="cards-3">
          {data.discoveries.map((d) => (
            <div key={d.id} className="card">
              <div className="row-between">
                <span className="label">{TYPE_LABEL[d.type] ?? d.type}</span>
                <Badge kind={d.type === "experience_gap" ? "Possible interpretation" : "Measured"} />
              </div>
              <h3 className="card-title">{d.headline}</h3>
              <p className="muted small">{d.interpretation}</p>
              {d.numbers.map((n) => (
                <div key={n.label} className="num-line">{n.numerator} of {n.denominator} ({n.pct}%) <span className="muted small">{n.label}</span></div>
              ))}
              {d.warning && <span className="badge badge-warning">{d.warning}</span>}
              <button type="button" className="chip" onClick={() => setView(TYPE_TO_VIEW[d.type] ?? "insights")}>Investigate</button>
            </div>
          ))}
        </div>
      </section>

      <section className="two-col">
        <div className="card">
          <div className="row-between">
            <h2 className="section-title">Complaint clusters</h2>
            <button type="button" className="chip" onClick={() => setView("complaints")}>Open</button>
          </div>
          {m.complaint_clusters === 0 && <NotRun text="No complaint cluster found." />}
          {data.clusters.map((c) => {
            const mix = c.sentiment_mix;
            return (
              <button key={c.cluster_id} type="button" className="list-row" onClick={() => setView("complaints")}>
                <div className="row-between"><span>{c.label}</span><span className="muted small">{c.size} reviews</span></div>
                <div className="stack-bar" aria-label="sentiment mix">
                  <span style={{ width: `${mix.positive_pct}%`, background: SENT_COLORS.positive }} />
                  <span style={{ width: `${mix.mixed_pct}%`, background: SENT_COLORS.mixed }} />
                  <span style={{ width: `${mix.negative_pct}%`, background: SENT_COLORS.negative }} />
                </div>
                {c.representative_reviews[0] && <p className="muted small clamp">"{c.representative_reviews[0].text}"</p>}
              </button>
            );
          })}
          <Badge kind="Measured" />
        </div>

        <div className="card">
          <div className="row-between">
            <h2 className="section-title">Contradictions</h2>
            <button type="button" className="chip" onClick={() => setView("contradictions")}>Open</button>
          </div>
          {data.contradictions.length === 0 && <NotRun text="No contradiction found." />}
          {data.contradictions.map((c, i) => (
            <div key={i} className="list-row static">
              <div className="small muted">{c.aspect} · product {c.product_id}</div>
              <p className="small clamp">+ "{c.observed_evidence.positive.quote}" ({c.observed_evidence.positive.rating}★)</p>
              <p className="small clamp">− "{c.observed_evidence.negative.quote}" ({c.observed_evidence.negative.rating}★)</p>
            </div>
          ))}
          <Badge kind="Possible interpretation" />
        </div>
      </section>

      <section className="card">
        <div className="row-between">
          <h2 className="section-title">Suspicious reviews</h2>
          <button type="button" className="chip" onClick={() => setView("suspicion")}>View evidence</button>
        </div>
        <p className="muted small">Warning signals, not proof. Heuristic, not a validated classifier.</p>
        <div className="kv-row">
          {Object.entries(data.suspicious.by_level).map(([k, v]) => (
            <span key={k} className="kv"><span className="muted small">{k}</span> {v.toLocaleString()}</span>
          ))}
        </div>
        <div className="kv-row">
          {Object.entries(data.suspicious.by_signal).map(([k, v]) => (
            <span key={k} className="kv"><span className="muted small">{k}</span> {v.toLocaleString()}</span>
          ))}
        </div>
        <Badge kind="Measured" />
      </section>

      <p className="muted small">{data.notes?.trend}</p>
    </div>
  );
}
