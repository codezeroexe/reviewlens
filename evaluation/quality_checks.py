"""Phase 8 C: application quality checks. Each check: PASS / FAIL / NOT VERIFIED + evidence. Writes reports/quality_check.{md,json}."""

import json
import random
import re
import time
from pathlib import Path

import pandas as pd

from batch.loader import DEMO_FILE, load_demo, load_reviews
from batch.predict import predict_batch
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
        "; ".join(f"{k}: dashboard={a}, report={b}" for k, a, b in pairs5) + ". Note: 'reviews' dashboard=20,000 sample; report=retained rows.")

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

    # 12-15. API checks on a spare port: strict JSON, gating during an upload, malformed requests, pair counts.
    import http.client
    import threading
    from http.server import ThreadingHTTPServer

    import src.server as srv
    from suspicion.signals import near_duplicates

    def strict(data: bytes):
        return json.loads(data, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f"non-JSON constant {c}")))

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]

    def call(method, path, body=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
        try:
            c.request(method, path, body=body)
            r = c.getresponse()
            raw = r.read()
            try:
                return r.status, strict(raw), None
            except ValueError as e:
                return r.status, None, str(e)
        except Exception as e:  # dropped connection etc.
            return "ERR", None, f"{type(e).__name__}"
        finally:
            c.close()

    try:
        # 12. Near-duplicate rows stay aligned after short reviews.
        demo = pd.DataFrame({"review_id": ["s1", "s2", "a", "b", "c"], "product_id": ["P"] * 5, "review_text": [
            "ok", "great", "the battery lasts very long indeed", "the battery lasts very long indeed", "something different here today"]})
        got = set(near_duplicates(demo))
        rec(12, "Near-duplicate signal finds a duplicate pair that follows short reviews", "PASS" if got == {"a", "b"} else "FAIL", f"flagged={sorted(got)}")

        # 13. Every GET endpoint returns strict JSON (no NaN) with the demo active.
        S.load_demo()
        cid = json.loads((REPORTS / "complaint_clusters.json").read_text())["clusters"][0]["cluster_id"]
        rid = json.loads((REPORTS / "contradictions.json").read_text())["conflicts"][0]["observed_evidence"]["positive"]["review_id"]
        paths = ["/complaints", "/complaints/unclustered", f"/complaints/cluster/{cid}/reviews", "/contradictions", f"/contradictions/review/{rid}",
                 "/suspicion", "/insights", "/insights/all", "/app/status", "/app/overview", "/app/view"]
        bad = []
        for pth in paths:
            status, _, err = call("GET", pth)
            if status != 200 or err:
                bad.append((pth, status, err))
        rec(13, f"{len(paths)} GET endpoints return strict JSON (NaN becomes null)", "PASS" if not bad else "FAIL", f"failures: {bad or 'none'}")

        # 14. Uploaded file active: every analysis endpoint answers 409 with the same rule.
        D.load_upload("gate.csv", b"review_id,product_id,star_rating,review_date,review_body\nG1,P1,4,2020-01-02,works fine for me\n")
        codes = {pth: call("GET", pth)[0] for pth in ["/complaints", "/contradictions", "/suspicion", "/insights", "/insights/all"]}
        st = call("GET", "/app/status")[1]
        ok = set(codes.values()) == {409} and st["results_for"] is None and st["dataset"]["kind"] == "upload"
        rec(14, "Uploaded file active: analysis endpoints refuse (409), status says no results for it", "PASS" if ok else "FAIL",
            f"codes={codes}, results_for={st['results_for']}, dataset.kind={st['dataset']['kind']}")
        D.FRAME.update(df=None, kind=None, name=None)
        S.load_demo()

        # 15. Malformed requests get JSON errors, never a dropped connection.
        cases = {"list body to /analyze": ("POST", "/analyze", b"[1]", 400), "bad JSON to dismiss": ("POST", "/suspicion/dismiss", b"x", 400),
                 "unknown insight id": ("GET", "/insights/evidence/nope", None, 404), "query string on route": ("GET", "/complaints?x=1", None, 200),
                 "bad rating filter": ("GET", "/app/view?rating=abc", None, 400), "non-numeric cluster id": ("GET", "/complaints/cluster/abc/reviews", None, 400)}
        wrong = {k: call(m, p, b)[0] for k, (m, p, b, want) in cases.items() if call(m, p, b)[0] != want}
        rec(15, "Malformed requests return JSON errors with the right status", "PASS" if not wrong else "FAIL", f"unexpected statuses: {wrong or 'none'}")

        # 16. Contradiction count is the same in the report, the API and the dashboard overview.
        conflicts = json.loads((REPORTS / "contradictions.json").read_text())["conflicts"]
        pairs_calc = len({(x["observed_evidence"]["positive"]["review_id"], x["observed_evidence"]["negative"]["review_id"]) for x in conflicts})
        api = call("GET", "/contradictions")[1]["unique_pairs"]
        dash_pairs = call("GET", "/app/overview")[1]["contradiction_counts"]["pairs"]
        rec(16, "Contradiction review-pair count agrees: report, API, dashboard", "PASS" if pairs_calc == api == dash_pairs else "FAIL",
            f"report={pairs_calc}, api={api}, dashboard={dash_pairs}; aspect matches={len(conflicts)}")
    finally:
        httpd.shutdown()
        for name in ("malformed.csv", "second.csv", "gate.csv"):  # test files this run created
            (D.UPLOAD_DIR / name).unlink(missing_ok=True)

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
