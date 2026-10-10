import { useApp } from "./AppState.jsx";

/** Title plus an optional banner. Every page uses it, so pages look and read alike. */
export function PageHead({ title, banner }) {
  return (
    <header className="page-head">
      <h1 className="page-title">{title}</h1>
      {banner && <div className="banner">{banner}</div>}
    </header>
  );
}

/** Shared loading / error line for data a page is fetching. */
export function Fetching({ loading, error }) {
  if (error) return <div className="card-slim danger" role="alert">{error}</div>;
  if (loading) return <p className="muted">Loading…</p>;
  return null;
}

/** Analysis results exist for the demo sample only. One rule for every analysis page. */
export function Gated({ children }) {
  const { status, dataset, resultsFor } = useApp();
  if (!status) return <p className="muted">Loading…</p>;
  if (dataset.kind === "upload") {
    return (
      <section className="card">
        <div className="label">Not analysed</div>
        <p>Analysis runs on the demo sample only. Uploaded files are browsable but not analysed. Load the demo dataset to see this.</p>
      </section>
    );
  }
  if (!resultsFor) {
    return (
      <section className="card">
        <div className="label">No results yet</div>
        <p>{dataset.kind ? "Run analysis to see this." : "Load the demo dataset, then run analysis."}</p>
      </section>
    );
  }
  return children;
}

export const displayLabel = (cluster) => cluster.display_label ?? cluster.label;
