"""App state for the dashboard: demo load, run-analysis job with real step progress, overview data.

Reads only real files. Run runs the phase scripts in order in a background thread.
"""

import json
import threading
import time
from pathlib import Path

import pandas as pd

from batch.loader import DEMO_FILE, load_reviews
from dashboard.data import FRAME, set_demo

REPORTS = Path("reports")
SAMPLE_ROWS = 20_000
STEPS = [
    ("Complaint clusters", "complaints.run"),
    ("Contradictions", "contradictions.run"),
    ("Suspicious signals", "suspicion.run"),
    ("Insights", "insights.run"),
]
JOB = {"status": "idle", "step": None, "step_index": 0, "step_count": len(STEPS),
       "done": [], "error": None, "error_step": None, "runtime_s": None}
_lock = threading.Lock()
STATS_PATH = REPORTS / "dataset_stats.json"  # saved on load so numbers survive a server restart
_stats = json.loads(STATS_PATH.read_text()) if STATS_PATH.exists() else {}


def load_demo() -> dict:
    """Read the demo file's first SAMPLE_ROWS rows. Counts are for that sample, labelled as such."""
    if not Path(DEMO_FILE).exists():
        raise FileNotFoundError(f"Demo file not found at {DEMO_FILE}.")
    df, rep = load_reviews(Path(DEMO_FILE), nrows=SAMPLE_ROWS)
    set_demo(df, Path(DEMO_FILE).name)
    _stats.update({
        "review_count": int(len(df)),
        "products": int(df["product_id"].nunique()),
        "date_min": str(df["date"].min().date()) if len(df) else None,
        "date_max": str(df["date"].max().date()) if len(df) else None,
        "categories": sorted(df["product_category"].dropna().unique().tolist()),
        "source": str(DEMO_FILE),
        "load_report": rep,
    })
    REPORTS.mkdir(exist_ok=True)
    STATS_PATH.write_text(json.dumps(_stats, indent=2, default=str))
    return get_status()


def _run_steps() -> None:
    import importlib
    t0 = time.time()
    for i, (label, module) in enumerate(STEPS, start=1):
        with _lock:
            JOB.update(step=label, step_index=i)
        try:
            mod = importlib.import_module(module)
            (mod.build() if module == "insights.run" else mod.main())
        except Exception as error:  # report the real error and the step that failed
            with _lock:
                JOB.update(status="error", error=f"{type(error).__name__}: {error}", error_step=label)
            return
        with _lock:
            JOB["done"].append(label)
    with _lock:
        JOB.update(status="ready", step=None, runtime_s=round(time.time() - t0, 1))


def start_run() -> dict:
    if not _stats:
        raise RuntimeError("Load the demo dataset first.")
    if FRAME["kind"] == "upload":
        raise RuntimeError("Analysis runs on the demo sample only. Uploaded files are browsable, not analysed.")
    with _lock:
        if JOB["status"] == "running":
            return get_status()
        JOB.update(status="running", step=None, step_index=0, done=[], error=None, error_step=None, runtime_s=None)
    threading.Thread(target=_run_steps, daemon=True).start()
    return get_status()


def _status_for_upload() -> dict:
    from dashboard.data import metrics as frame_metrics
    m = frame_metrics(FRAME["df"])
    base = get_status_core()
    base["stats"] = {"source": FRAME["name"], "review_count": m["reviews"], "products": m["products"],
                     "date_min": m["date_span"][0], "date_max": m["date_span"][1],
                     "categories": sorted(FRAME["df"]["product_category"].dropna().unique().tolist())
                     if "product_category" in FRAME["df"] else []}
    base["analysis_on"] = "demo sample only"
    return base


def get_status_core() -> dict:
    if JOB["status"] == "running":
        data_state = "Analyzing"
    elif JOB["status"] == "error":
        data_state = "Error"
    else:
        data_state = "Loaded"
    return {"data_state": data_state, "stats": {}, "job": dict(JOB), "reports_present": _reports_present()}


def _reports_present() -> bool:
    return (REPORTS / "complaint_clusters.json").exists() and (REPORTS / "insights.json").exists()


def get_status() -> dict:
    if FRAME["kind"] == "upload":
        return _status_for_upload()
    if JOB["status"] == "running":
        data_state = "Analyzing"
    elif JOB["status"] == "error":
        data_state = "Error"
    elif _reports_present():
        data_state = "Ready"
    elif _stats:
        data_state = "Loaded"
    else:
        data_state = "Not loaded"
    return {"data_state": data_state, "stats": _stats, "job": dict(JOB), "reports_present": _reports_present()}


def _signal_counts(flagged: pd.DataFrame) -> dict:
    counts: dict[str, int] = {}
    for cell in flagged["signals"]:
        for name in filter(None, str(cell).split("; ")):
            counts[name] = counts.get(name, 0) + 1
    return counts


def get_overview() -> dict:
    if FRAME["kind"] == "upload":
        # Demo-sample results must not appear next to an uploaded file.
        return {"available": False, "message": "Uploaded file active. Demo-sample analysis results are hidden."}
    if not _reports_present():
        return {"available": False, "message": "Run analysis to see this."}
    clusters = json.loads((REPORTS / "complaint_clusters.json").read_text())
    contra = json.loads((REPORTS / "contradictions.json").read_text())
    susp = pd.read_csv(REPORTS / "suspicion_results.csv", dtype=str, keep_default_na=False)
    flagged = susp[susp["signal_count"].astype(int) > 0]
    top_clusters = sorted(clusters["clusters"], key=lambda c: -c["size"])[:5]
    # Same review pair can appear under two aspect keywords; show each pair once.
    seen, unique = set(), []
    for c in sorted(contra["conflicts"], key=lambda c: -(c["nli_score"] or 0)):
        key = (c["observed_evidence"]["positive"]["review_id"], c["observed_evidence"]["negative"]["review_id"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    top_contra = unique[:3]
    from insights.service import get_overview as insight_overview
    ins = insight_overview()
    return {
        "available": True,
        "metrics": {
            "reviews": _stats.get("review_count"),
            "products": _stats.get("products"),
            "date_span": [_stats.get("date_min"), _stats.get("date_max")],
            "complaint_clusters": clusters["meta"]["cluster_count"],
            "flagged_reviews": int(len(flagged)),
        },
        "discoveries": ins["insights"],
        "clusters": top_clusters,
        "contradictions": top_contra,
        "suspicious": {
            "by_level": susp["category"].value_counts().to_dict(),
            "by_signal": _signal_counts(flagged),
            "flagged_total": int(len(flagged)),
        },
        "notes": {"trend": "Not shown: all reviews fall in one week (fewer than 3 periods)."},
    }


def filtered_view(params: dict) -> dict:
    """Metrics for the active dataset after filters. Clusters/discoveries are not filterable (full-sample outputs)."""
    from dashboard.data import apply_filters, metrics as frame_metrics, filter_options
    df = FRAME["df"]
    if df is None:
        return {"available": False, "message": "Load a dataset first."}
    sub = apply_filters(df, params.get("product"), params.get("rating"), params.get("date_from"), params.get("date_to"))
    m = frame_metrics(sub)
    if FRAME["kind"] == "demo" and (REPORTS / "suspicion_results.csv").exists():
        susp = pd.read_csv(REPORTS / "suspicion_results.csv", dtype=str, keep_default_na=False)
        flagged_ids = set(susp.loc[susp["signal_count"].astype(int) > 0, "review_id"])
        m["flagged"] = int(sub["review_id"].astype(str).isin(flagged_ids).sum())
    else:
        m["flagged"] = None
    return {"available": True, "metrics": m, "filtered": any(params.get(k) for k in ("product", "rating", "date_from", "date_to")),
            "options": filter_options(df), "kind": FRAME["kind"], "source": FRAME["name"]}
