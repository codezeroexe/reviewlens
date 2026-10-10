"""Phase 8 C: application quality checks. Each check: PASS / FAIL / NOT VERIFIED + evidence. Writes reports/quality_check.{md,json}."""

import hashlib
import json
import random
import re
import time
from pathlib import Path

import pandas as pd

from batch.loader import DEMO_FILE, load_demo, load_reviews
from batch.predict import predict_batch
from batch.schema import clean_reviews
from complaints.service import discover
from dashboard import data as D
from dashboard import state as S
from src.reviewlens_inference import ReviewLens

REPORTS = Path("reports")
RESULTS = []


def rec(n, name, status, evidence):
    RESULTS.append({"n": n, "check": name, "status": status, "evidence": evidence})


def norm(t: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", str(t).lower()).split())


def raw_texts() -> dict:
    raw = pd.read_csv(DEMO_FILE, sep="\t", quoting=3, engine="python", on_bad_lines="skip", nrows=20000, dtype=str)
    return dict(zip(raw["review_id"], (raw["review_headline"].fillna("") + " " + raw["review_body"].fillna("")).str.strip()))


def main() -> None:
    texts = raw_texts()
    random.seed(42)

    # 1. Batch pipeline runs end to end (phases 3-6 via dashboard steps) + phase-2 batch predict.
    t0 = time.time()
    try:
        S._run_steps()
        ok = S.JOB["status"] == "ready"
        pt = time.time()
        sample = load_demo(nrows=2000)  # batch predict on a 2,000-row slice
        model = ReviewLens("models")
        out, rep = predict_batch(sample[0].head(2000), model)
        run_s = round(time.time() - t0, 1)
        rec(1, "Batch pipeline completes (phases 3-6 steps + phase 2 predict on 2,000 rows)", "PASS" if ok and rep["failed_in_batches"] == 0 else "FAIL",
            f"job status={S.JOB['status']}, steps={S.JOB['done']}, total runtime {run_s}s, predict rows={rep['rows']}, failed={rep['failed_in_batches']}")
    except Exception as e:
        rec(1, "Batch pipeline completes", "FAIL", f"{type(e).__name__}: {e}")

    # 2. Cluster links: 5 random clustered reviews vs raw.
    a = pd.read_csv(REPORTS / "complaint_assignments.csv", dtype={"review_id": str})
    cl = a[a["status"] == "clustered"].sample(5, random_state=42)
    bad = [r.review_id for r in cl.itertuples() if r.review_id not in texts or norm(texts[r.review_id]) != norm(r.review_text)]
    rec(2, "Cluster links: 5 random clustered reviews match raw ID and text", "PASS" if not bad else "FAIL",
        f"checked {list(cl.review_id)}; mismatches: {bad or 'none'}")

    # 3. Contradiction quotes: 3 pairs, both quotes are substrings of cited raw reviews.
    c = json.loads((REPORTS / "contradictions.json").read_text())["conflicts"]
    pairs = random.sample(c, 3)
    fails = []
    for x in pairs:
        for side in ("positive", "negative"):
            q = x["observed_evidence"][side]
            if q["quote"] not in texts.get(q["review_id"], ""):
                fails.append((q["review_id"], side))
    rec(3, "Contradiction quotes: 3 pairs are real substrings of cited reviews", "PASS" if not fails else "FAIL",
        f"checked {len(pairs)} pairs (6 quotes); not substring: {fails or 'none'}")

    # 4. Suspicious explanations: reproduce listed signals for 3 flagged reviews from raw.
    s = pd.read_csv(REPORTS / "suspicion_results.csv", dtype=str, keep_default_na=False)
    flagged = s[s["signal_count"].astype(int) > 0].sample(3, random_state=42)
    lines, all_ok = [], True
    raw_all = pd.read_csv(DEMO_FILE, sep="\t", quoting=3, engine="python", on_bad_lines="skip", nrows=20000, dtype=str)
    for r in flagged.itertuples():
        found = []
        n = norm(texts[r.review_id])
        if "exact duplicate" in r.signals:
            twins = [i for i, t in texts.items() if i != r.review_id and norm(t) == n]
            found.append(f"exact dup twins={len(twins)}")
            all_ok &= len(twins) > 0
        if "promotional" in r.signals:
            phr = [p for p in ["highly recommend", "best product ever", "must buy", "five stars", "buy now", "amazing product"] if re.search(r"\b" + p + r"\b", n)]
            found.append(f"promo phrases={phr}")
            all_ok &= bool(phr) or "top_word" in r.details
        if "reviewer activity" in r.signals:
            cust = raw_all.loc[raw_all["review_id"] == r.review_id, "customer_id"].iloc[0]
            day = raw_all.loc[raw_all["review_id"] == r.review_id, "review_date"].iloc[0]
            cnt = int(((raw_all["customer_id"] == cust) & (raw_all["review_date"] == day)).sum())
            found.append(f"reviewer same-day count={cnt}")
            all_ok &= cnt >= 5
        lines.append(f"{r.review_id}: signals [{r.signals}] -> {', '.join(found) or 'no signal re-derived'}")
    rec(4, "Suspicious explanations: 3 flagged reviews, listed signals reproduced from raw", "PASS" if all_ok else "FAIL", " | ".join(lines))

    # 5. Dashboard numbers vs backend/report files.
    ov = S.get_overview()
    dash = {"reviews": ov["metrics"]["reviews"], "complaint_clusters": ov["metrics"]["complaint_clusters"],
            "flagged": ov["metrics"]["flagged_reviews"], "top_discovery_numerator": ov["discoveries"][0]["numbers"][0]["numerator"]}
    rep_ds = json.loads((REPORTS / "dataset_report.json").read_text())
    rep_cl = json.loads((REPORTS / "complaint_clusters.json").read_text())["meta"]["cluster_count"]
    rep_fl = int((s["signal_count"].astype(int) > 0).sum())
    rep_ins = json.loads((REPORTS / "insights.json").read_text())["overview"][0]["numbers"][0]["numerator"]
    pairs5 = [("reviews", dash["reviews"], rep_ds["rows"]["retained"]), ("complaint_clusters", dash["complaint_clusters"], rep_cl),
              ("flagged", dash["flagged"], rep_fl), ("top_discovery_numerator", dash["top_discovery_numerator"], rep_ins)]
    mism = [p for p in pairs5 if p[1] != p[2]]
    rec(5, "Dashboard vs backend: 4 numbers (UI reads these endpoints)", "PASS" if not mism else "FAIL",
        "; ".join(f"{k}: dashboard={a}, report={b}" for k, a, b in pairs5) + f". Note: 'reviews' dashboard=20,000 sample; report=retained rows.")

    # 6. Empty file.
    try:
        D.load_upload("empty.csv", b"")
        rec(6, "Empty file -> clear error", "FAIL", "no error raised")
    except D.UploadError as e:
        rec(6, "Empty file -> clear error", "PASS", f"message: '{e}'")

    # 7. Malformed: bad dates, text in numeric columns -> counted, no crash.
    bad_csv = (b"review_id,product_id,star_rating,review_date,review_body\n"
               b"M1,P1,5,2020-01-02,good item\nM2,P1,abc,not-a-date,bad numbers\nM3,P1,9,2020-13-45,out of range\n")
    try:
        info = D.load_upload("malformed.csv", bad_csv)
        r = info["report"]
        ok = r["rating_set_null"] == 2 and r["date_set_null"] == 2
        rec(7, "Malformed file (bad dates, text in numeric, wrong range) -> counted, no crash", "PASS" if ok else "FAIL",
            f"report: rating_set_null={r['rating_set_null']}, date_set_null={r['date_set_null']}, kept={info['rows_kept']}")
    except Exception as e:
        rec(7, "Malformed file -> counted, no crash", "FAIL", f"{type(e).__name__}: {e}")
    try:
        D.load_upload("wrongcols.csv", b"id,stars,text\n1,3,hello\n")
        rec(7, "Wrong columns -> clear error", "FAIL", "no error")
    except D.UploadError as e:
        rec(7, "Wrong columns -> clear error", "PASS", f"message: '{e}'")

    # 8. Tiny dataset (10 rows): no crash, no fake clusters.
    tiny = load_reviews(DEMO_FILE, nrows=10)[0]
    try:
        clusters, assigned, meta = discover(tiny)
        ok = len(clusters) == 0 and meta["clustered"] == 0
        rec(8, "Tiny dataset (10 rows): no crash, no fake clusters", "PASS" if ok else "FAIL",
            f"clusters={len(clusters)}, clustered={meta['clustered']}, statuses={assigned['status'].value_counts().to_dict()}")
    except Exception as e:
        rec(8, "Tiny dataset", "FAIL", f"{type(e).__name__}: {e}")

    # 9. Second dataset after the first: old results must not mix in.
    D.load_upload("second.csv", b"review_id,product_id,star_rating,review_date,review_body\nU1,P9,4,2020-01-02,works\n")
    ov2 = S.get_overview()
    old_clusters = len(ov2.get("clusters", []))
    st = S.get_status()
    D.FRAME.update(df=None, kind=None, name=None)  # restore: no active dataset until demo is loaded again
    S.load_demo()
    rec(9, "Second upload: old clusters, insights, flags hidden (no mixing)", "PASS" if old_clusters == 0 and ov2["available"] is False else "FAIL",
        f"after upload, status={st['data_state']}, analysis_on={st.get('analysis_on')}, overview available={ov2['available']}, demo clusters shown={old_clusters}. Analysis is not re-run for uploads; phase-3 cache key is hashed on review IDs, so a new file gets a new cache key.")

    # 10. Usefulness prediction: no model exists.
    rec(10, "Original usefulness prediction works (one example)", "NOT VERIFIED",
        "No usefulness model in the project. batch/predict returns cluster patterns only (phase 2 checked, see phase1-findings).")

    # 11. Original suspicious/fake detector.
    rec(11, "Original suspicious/fake detection works (one example)", "NOT VERIFIED",
        "No existing fake-review detector in the project (reports/suspicion_audit.md). New heuristic example runs: see check 4.")

    order = {"FAIL": 0, "NOT VERIFIED": 1, "PASS": 2}
    RESULTS.sort(key=lambda r: (order[r["status"]], r["n"]))
    counts = pd.Series([r["status"] for r in RESULTS]).value_counts().to_dict()
    (REPORTS / "quality_check.json").write_text(json.dumps({"results": RESULTS, "counts": counts}, indent=2, default=str))
    md = ["# Quality check", "", "Failures first. Evidence is from code run in `evaluation/quality_checks.py`.", "",
          f"Counts: {counts}", "", "| # | Check | Status | Evidence |", "|---|---|---|---|"]
    md += [f"| {r['n']} | {r['check']} | {r['status']} | {r['evidence']} |" for r in RESULTS]
    (REPORTS / "quality_check.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
