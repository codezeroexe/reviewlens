import { useApp } from "./AppState.jsx";
import { fmt } from "./api.js";

const NAV = [
  { key: "overview", label: "Overview" },
  { key: "complaints", label: "Complaints" },
  { key: "contradictions", label: "Contradictions" },
  { key: "suspicion", label: "Suspicious Reviews" },
  { key: "insights", label: "Insights" },
  { key: "check", label: "Check a review" },
];

const closeMenu = (event) => { const menu = event.currentTarget.closest("details"); if (menu) menu.open = false; };

/** Monochrome magnifying glass. Uses the text colour, so it matches the wordmark. */
function Logo() {
  return (
    <svg className="logo" viewBox="0 0 48 48" role="img" aria-label="ReviewLens logo" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="square">
      <circle cx="20" cy="20" r="13" />
      <path d="M31 31 L43 43" strokeWidth="7" />
      <path d="M13 18 A8 8 0 0 1 19 12" strokeWidth="3" />
    </svg>
  );
}

function Steps() {
  const { steps, job, analyzing } = useApp();
  if (!job || job.status === "idle") return null;
  const state = (label) => (job.error_step === label ? "failed" : job.done.includes(label) ? "done" : job.step === label && analyzing ? "current" : "pending");
  return (
    <div className="run-line">
      <ol className="steps" aria-label="Analysis steps">
        {steps.map((label) => <li key={label} className={`step ${state(label)}`}>{label}</li>)}
      </ol>
      {job.status === "ready" && <span className="muted small">Done in {job.runtime_s} s</span>}
      {job.status === "error" && <span className="danger-text">{job.error_step}: {job.error}</span>}
    </div>
  );
}

function DatasetBar() {
  const { dataset, job, busy, analyzing, resultsFor, actionError, upload, loadDemo, run } = useApp();
  const kind = dataset.kind;
  const disabled = Boolean(busy) || analyzing;
  const summary = kind
    ? `${dataset.name} · ${fmt(dataset.rows)} reviews · ${kind === "demo" ? "demo sample" : "uploaded file"}${dataset.restoring ? " · restoring…" : ""}`
    : "No dataset loaded";
  const primary = !kind ? { text: "Load demo dataset", onClick: loadDemo }
    : kind === "upload" ? { text: "Run analysis", onClick: run, blocked: "Analysis runs on the demo sample only." }
    : analyzing ? { text: `Running ${job?.step_index ?? 0} of ${job?.step_count ?? 4}`, onClick: run }
    : { text: resultsFor ? "Re-run analysis" : "Run analysis", onClick: run };

  return (
    <header className="databar">
      <div className="databar-main">
        <span className="brand-lockup"><Logo /><span className="brand-name">ReviewLens</span></span>
        <span className="dataset-chip" title={summary}>{summary}</span>
        <details className="menu">
          <summary className="chip">Change dataset</summary>
          <div className="menu-pop">
            <label className={`file-chip${disabled ? " disabled" : ""}`}>
              {busy === "upload" ? "Uploading…" : "Upload CSV, TSV or XLSX"}
              <input type="file" accept=".csv,.tsv,.txt,.xlsx" hidden disabled={disabled}
                     onChange={(e) => { const file = e.target.files[0]; closeMenu(e); e.target.value = ""; if (file) upload(file); }} />
            </label>
            <button type="button" className="chip" disabled={disabled} onClick={(e) => { closeMenu(e); loadDemo(); }}>
              {busy === "load" ? "Loading…" : "Load demo dataset"}
            </button>
          </div>
        </details>
        <button type="button" className="cta" onClick={primary.onClick} disabled={disabled || Boolean(primary.blocked)} title={primary.blocked}>
          {primary.text}
        </button>
      </div>
      <Steps />
      {actionError && <div className="card-slim danger" role="alert">{actionError}</div>}
    </header>
  );
}

export default function Shell({ view, setView, children }) {
  return (
    <div className="shell">
      <DatasetBar />
      <nav className="nav" aria-label="Sections">
        {NAV.map((n) => (
          <button key={n.key} type="button" className={view === n.key ? "nav-item active" : "nav-item"}
                  aria-current={view === n.key ? "page" : undefined} onClick={() => setView(n.key)}>
            {n.label}
          </button>
        ))}
      </nav>
      {children}
    </div>
  );
}
