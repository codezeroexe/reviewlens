import { createContext, useCallback, useContext, useEffect, useState } from "react";

// Shared app status (from /app/status). Pages read it; only the Shell polls it.
export const StatusContext = createContext({ status: null, refresh: () => {} });
export const useStatus = () => useContext(StatusContext);

const NAV = [
  { key: "overview", label: "Overview" },
  { key: "complaints", label: "Complaints" },
  { key: "contradictions", label: "Contradictions" },
  { key: "suspicion", label: "Suspicious Reviews" },
  { key: "insights", label: "Insights" },
  { key: "analyze", label: "Analyze" },
];

const BADGE = { "Not loaded": "muted", Loaded: "accent", Analyzing: "accent", Ready: "success", Error: "danger" };

export default function Shell({ view, setView, children }) {
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(null);
  const [actionError, setActionError] = useState(null);

  const refresh = useCallback(() => fetch("/app/status").then((r) => r.json()).then(setStatus).catch(() => {}), []);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (status?.data_state !== "Analyzing") return undefined;
    const timer = setInterval(refresh, 2000);
    return () => clearInterval(timer);
  }, [status?.data_state, refresh]);

  async function upload(file) {
    setBusy("upload"); setActionError(null);
    const res = await fetch("/app/upload", { method: "POST", headers: { "X-Filename": file.name }, body: file });
    const data = await res.json();
    setBusy(null);
    if (!res.ok) setActionError(data.error || "Upload failed.");
    refresh();
  }

  async function post(url, label) {
    setBusy(label); setActionError(null);
    const res = await fetch(url, { method: "POST" });
    const data = await res.json();
    setBusy(null);
    if (!res.ok) setActionError(data.error || "Request failed.");
    refresh();
  }

  const stats = status?.stats ?? {};
  const dataset = stats.source ? stats.source.split("/").pop() : "No dataset loaded";
  const loaded = Boolean(stats.review_count);
  const running = status?.data_state === "Analyzing";
  const job = status?.job;

  return (
    <StatusContext.Provider value={{ status, refresh }}>
      <div className="shell">
        <header className="topbar">
          <div className="brand-line">
            <span className="brand-name">ReviewLens</span>
            <span className="muted small">{dataset}{loaded ? ` · ${stats.categories?.join(", ")} · ${stats.review_count.toLocaleString()} reviews (sample)` : ""}</span>
          </div>
          <div className="topbar-actions">
            <span className={`badge badge-${BADGE[status?.data_state] ?? "muted"}`}>{status?.data_state ?? "…"}</span>
            <label className={`chip file-chip${busy || running ? " disabled" : ""}`}>
              {busy === "upload" ? "Uploading…" : "Upload CSV/XLSX"}
              <input type="file" accept=".csv,.tsv,.txt,.xlsx" hidden disabled={!!busy || running}
                     onChange={(e) => e.target.files[0] && upload(e.target.files[0])} />
            </label>
            <button type="button" className="chip" onClick={() => post("/app/load-demo", "load")} disabled={!!busy || running}>
              {busy === "load" ? "Loading…" : "Load demo dataset"}
            </button>
            <button type="button" className="cta" onClick={() => post("/app/run", "run")} disabled={!loaded || running || !!busy || !!status?.analysis_on} title={status?.analysis_on ? "Analysis runs on the demo sample only" : undefined}>
              {running ? "Running…" : "Run analysis"}
            </button>
          </div>
        </header>

        {running && job && (
          <div className="progress card-slim">
            Step {job.step_index} of {job.step_count}: {job.step} · {stats.review_count?.toLocaleString()} reviews · done: {job.done.join(", ") || "none"}
          </div>
        )}
        {job?.status === "error" && <div className="card-slim danger">Failed at "{job.error_step}": {job.error}</div>}
        {job?.status === "ready" && !running && <div className="card-slim success">Analysis complete in {job.runtime_s} s.</div>}
        {actionError && <div className="card-slim danger">{actionError}</div>}

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
    </StatusContext.Provider>
  );
}
