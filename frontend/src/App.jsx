import { Fragment, useEffect, useState } from "react";
import { PRODUCTS } from "./presets.js";
import ComplaintDiscovery from "./ComplaintDiscovery.jsx";
import ContradictionInvestigator from "./ContradictionInvestigator.jsx";
import SuspicionInvestigator from "./SuspicionInvestigator.jsx";
import InsightsPage from "./InsightsPage.jsx";
import Shell from "./Shell.jsx";
import Overview from "./Overview.jsx";
import { AppProvider } from "./AppState.jsx";
import { postJson } from "./api.js";
import { PageHead } from "./ui.jsx";

// Order and colours for the five learned patterns.
const PATTERNS = [
  { name: "Balanced Evaluative Review", color: "var(--pattern-1)" },
  { name: "Extended Analytical Review", color: "var(--pattern-2)" },
  { name: "Concise General Opinion", color: "var(--pattern-3)" },
  { name: "Long-Term Usage Experience", color: "var(--pattern-4)" },
  { name: "Personal Experience and Recommendation", color: "var(--pattern-5)" },
];
const colorOf = (pattern) => PATTERNS.find((p) => p.name === pattern)?.color ?? "var(--text-3)";

// One row per preset review, using each product's first subject so results are stable.
const BASE_ROWS = PRODUCTS.flatMap((product) =>
  product.reviews.map((review) => ({
    id: `${product.name}-${review.label}`,
    product: product.name,
    sample: review.label,
    subject: product.subjects[0],
    text: review.text.replaceAll("{subject}", product.subjects[0]),
  }))
);

const analyze = (text) => postJson("/analyze", { text });

function countBy(items, key) {
  const counts = {};
  for (const item of items) counts[item[key]] = (counts[item[key]] ?? 0) + 1;
  return counts;
}

function topKey(counts) {
  const entries = Object.entries(counts);
  if (!entries.length) return "—";
  return entries.sort((a, b) => b[1] - a[1])[0][0];
}

function AnalyzeTab({ rows, setRows }) {
  const [filter, setFilter] = useState("All");
  const [openKey, setOpenKey] = useState(null);
  const [draft, setDraft] = useState("");
  const [lastCustomId, setLastCustomId] = useState(null);
  const [view, setView] = useState("overview");
  const hasCustom = rows.some((r) => r.product === "Custom");

  // Run one analysis and write the result into the matching row.
  async function runRow(id, text) {
    try {
      const result = await analyze(text);
      setRows((prev) => prev.map((r) => (r.id === id ? { ...r, status: "done", result } : r)));
    } catch (err) {
      setRows((prev) => prev.map((r) => (r.id === id ? { ...r, status: "error", error: err.message } : r)));
    }
  }

  // Analyze the preset reviews when this tab is first opened (not at app start), sequentially, filling rows as results arrive.
  useEffect(() => {
    let cancelled = false;
    const todo = rows.filter((r) => r.status === "pending" && !r.id.startsWith("custom-"));
    (async () => {
      for (const row of todo) {
        if (cancelled) return;
        await runRow(row.id, row.text);
      }
    })();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function submitCustom(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const id = `custom-${Date.now()}`;
    setLastCustomId(id);
    setRows((prev) => [...prev, { id, product: "Custom", sample: "Your review", text, status: "pending" }]);
    setFilter("All");
    setDraft("");
    runRow(id, text);
  }

  const lastCustom = rows.find((r) => r.id === lastCustomId) ?? null;
  const analyzedAll = rows.filter((r) => r.status === "done");
  const visible = filter === "All" ? rows : rows.filter((r) => r.product === filter);
  const visibleDone = visible.filter((r) => r.status === "done");
  const patternCounts = countBy(visibleDone.map((r) => ({ p: r.result.review_pattern })), "p");
  const valueCounts = countBy(visibleDone.map((r) => ({ v: r.result.informational_value })), "v");
  const altCounts = countBy(visibleDone.map((r) => ({ a: r.result.alternative_pattern })), "a");
  const highShare = visibleDone.length
    ? Math.round((100 * visibleDone.filter((r) => r.result.informational_value.startsWith("High")).length) / visibleDone.length)
    : 0;
  const pending = rows.length - analyzedAll.length - rows.filter((r) => r.status === "error").length;

  return (
    <div className="page">
      <PageHead title="Analyze reviews" banner="Closest learned writing pattern per review. Not a usefulness judgement." />
      <div className="chips" role="tablist" aria-label="Product filter">
        {["All", ...PRODUCTS.map((p) => p.name), ...(hasCustom ? ["Custom"] : [])].map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={filter === name}
            className={filter === name ? "chip active" : "chip"}
            onClick={() => setFilter(name)}
          >
            {name}
          </button>
        ))}
      </div>

      <form className="card custom-input" onSubmit={submitCustom}>
        <div className="label">Analyze your own review</div>
        <textarea
          className="lined"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Paste a product review here..."
          aria-label="Your review"
        />
        <button type="submit" className="cta" disabled={!draft.trim()}>Add and analyze</button>
        {lastCustom && (
          <div className="custom-result" aria-live="polite">
            <div className="label">Result for your review</div>
            {lastCustom.status === "pending" && <p className="muted">Analyzing...</p>}
            {lastCustom.status === "error" && <p className="danger-text">{lastCustom.error}</p>}
            {lastCustom.status === "done" && (
              <>
                <div className="custom-pattern">
                  <span className="dot" style={{ background: colorOf(lastCustom.result.review_pattern) }} />
                  <b>{lastCustom.result.review_pattern}</b>
                  <span className="badge badge-muted">Informational value: {lastCustom.result.informational_value}</span>
                </div>
                <p className="description">{lastCustom.result.description}</p>
                <p className="muted small">Next closest pattern: {lastCustom.result.alternative_pattern}</p>
                <p className="note">{lastCustom.result.note}</p>
              </>
            )}
          </div>
        )}
      </form>

      <section className="kpis">
        <div className="card kpi">
          <div className="label">Analyzed</div>
          <div className="kpi-value">{analyzedAll.length}<span className="muted"> / {rows.length}</span></div>
          {pending > 0 && <div className="muted small">Running...</div>}
        </div>
        <div className="card kpi">
          <div className="label">Top pattern</div>
          <div className="kpi-text">{topKey(patternCounts)}</div>
        </div>
        <div className="card kpi">
          <div className="label">High informational value</div>
          <div className="kpi-value">{highShare}%</div>
        </div>
        <div className="card kpi">
          <div className="label">Top alternative</div>
          <div className="kpi-text">{topKey(altCounts)}</div>
        </div>
      </section>

      <section className="grid-2">
        <div className="card">
          <div className="label">Pattern mix by product</div>
          <div className="bars">
            {PRODUCTS.map((product) => {
              const done = rows.filter((r) => r.product === product.name && r.status === "done");
              const counts = countBy(done.map((r) => ({ p: r.result.review_pattern })), "p");
              return (
                <div key={product.name} className="bar-row">
                  <div className="bar-label">{product.name}</div>
                  <div className="stack">
                    {PATTERNS.map((p) => {
                      const n = counts[p.name] ?? 0;
                      return n ? (
                        <div
                          key={p.name}
                          className="seg"
                          style={{ width: `${(100 * n) / Math.max(done.length, 1)}%`, background: p.color }}
                          title={`${p.name}: ${n}`}
                        />
                      ) : null;
                    })}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="legend">
            {PATTERNS.map((p) => (
              <span key={p.name}><i style={{ background: p.color }} />{p.name}</span>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="label">Informational value</div>
          <div className="bars">
            {Object.entries(valueCounts).map(([value, n]) => (
              <div key={value} className="bar-row">
                <div className="bar-label">{value}</div>
                <div className="track">
                  <div className="fill" style={{ width: `${(100 * n) / Math.max(visibleDone.length, 1)}%` }} />
                </div>
                <div className="bar-count">{n}</div>
              </div>
            ))}
            {visibleDone.length === 0 && <p className="muted">No results yet.</p>}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="label">Reviews</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Sample</th>
                <th>Pattern</th>
                <th>Value</th>
                <th>Alternative</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((r) => {
                const key = r.id;
                const isOpen = openKey === key;
                return (
                  <Fragment key={key}>
                    <tr
                      className={isOpen ? "row-open clickable" : "clickable"}
                      onClick={() => setOpenKey(isOpen ? null : key)}
                      aria-expanded={isOpen}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setOpenKey(isOpen ? null : key);
                        }
                      }}
                    >
                      <td>{r.product}</td>
                      <td>{r.sample}</td>
                      {r.status === "done" ? (
                        <>
                          <td>
                            <span className="dot" style={{ background: colorOf(r.result.review_pattern) }} />
                            {r.result.review_pattern}
                          </td>
                          <td>{r.result.informational_value}</td>
                          <td>{r.result.alternative_pattern}</td>
                        </>
                      ) : (
                        <td colSpan={3} className="muted">{r.status === "error" ? r.error : "Analyzing..."}</td>
                      )}
                    </tr>
                    {isOpen && (
                      <tr className="detail">
                        <td colSpan={5}>
                          <div className="detail-body">
                            <div>
                              <div className="label">Review</div>
                              <p className="review-text">{r.text}</p>
                            </div>
                            {r.status === "done" && (
                              <div>
                                <div className="label">Result</div>
                                <p className="description">{r.result.description}</p>
                                <p className="note">{r.result.note}</p>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

const PAGES = { complaints: ComplaintDiscovery, contradictions: ContradictionInvestigator, suspicion: SuspicionInvestigator, insights: InsightsPage };

export default function App() {
  const [nav, setNav] = useState({ view: "overview", focus: null });
  const [rows, setRows] = useState(() => BASE_ROWS.map((r) => ({ ...r, status: "pending" })));
  // go(view, focus): pages open already filtered to the thing a link points at.
  const go = (view, focus = null) => setNav({ view, focus });
  const Page = PAGES[nav.view];

  return (
    <AppProvider>
      <Shell view={nav.view} setView={go}>
        {nav.view === "overview" && <Overview go={go} />}
        {Page && <Page key={JSON.stringify(nav.focus)} focus={nav.focus} clearFocus={() => go(nav.view)} />}
        {nav.view === "analyze" && <AnalyzeTab rows={rows} setRows={setRows} />}
      </Shell>
    </AppProvider>
  );
}
