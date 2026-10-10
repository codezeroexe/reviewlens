"""Stdlib HTTP endpoint: POST /analyze with {"text": "..."} -> ReviewLens result."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from complaints.service import get_cluster_reviews, get_clusters, get_unclustered_reviews
from contradictions.service import find_contradictions, get_review
from suspicion.service import dismiss, get_results, get_similar, list_dismissed
from insights.service import get_all, get_evidence, get_overview
from dashboard.state import filtered_view, get_overview as app_overview, get_status, load_demo, start_run
from dashboard.data import UploadError, load_upload
from urllib.parse import parse_qs, urlparse
from src.reviewlens_inference import ReviewLens

model = ReviewLens("models")  # load once at startup


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Complaint Discovery (preliminary). Reads saved reports/ files written by complaints/run.py.
        try:
            if self.path == "/complaints":
                return self._send(200, get_clusters())
            # Contradiction Investigator (reads reports/contradictions.json written by contradictions/run.py).
            if self.path == "/contradictions":
                return self._send(200, {"conflicts": find_contradictions()})
            if self.path.startswith("/contradictions/review/"):
                row = get_review(self.path[len("/contradictions/review/"):])
                return self._send(200, row) if row else self._send(404, {"error": "review not found"})
            # Suspicious Review Investigator (heuristic). Reads reports/suspicion_results.csv.
            if self.path == "/suspicion":
                rows = get_results()
                rows = rows[rows["signal_count"] > 0].drop(columns=["details"], errors="ignore")
                return self._send(200, {"rows": rows.fillna("").to_dict(orient="records"),
                                        "dismissed": list_dismissed(),
                                        "rule": "0 signals: No signals; 1: Low; 2: Medium; 3+: High (counts of different signals, not a probability)"})
            if self.path.startswith("/suspicion/similar/"):
                return self._send(200, get_similar(self.path[len("/suspicion/similar/"):]))
            # Dashboard state (phase 7).
            if self.path == "/app/status":
                return self._send(200, get_status())
            if self.path.startswith("/app/view"):
                q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
                return self._send(200, filtered_view(q))
            if self.path == "/app/overview":
                return self._send(200, app_overview())
            # Insight engine (phase 6). Reads phase 3-5 outputs; cache in reports/insights.json.
            if self.path == "/insights":
                return self._send(200, get_overview())
            if self.path.startswith("/insights/all"):
                return self._send(200, get_all())
            if self.path.startswith("/insights/evidence/"):
                return self._send(200, get_evidence(self.path[len("/insights/evidence/"):]))
            if self.path == "/complaints/unclustered":
                return self._send(200, get_unclustered_reviews())
            if self.path.startswith("/complaints/cluster/") and self.path.endswith("/reviews"):
                cid = self.path[len("/complaints/cluster/"):-len("/reviews")]
                return self._send(200, get_cluster_reviews(int(cid)))
        except FileNotFoundError as error:
            return self._send(404, {"error": str(error)})
        except ValueError:
            return self._send(400, {"error": "bad cluster id"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/app/upload":
            try:
                data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                name = self.headers.get("X-Filename", "upload.csv")
                info = load_upload(name, data)
                return self._send(200, {**info, "status": get_status()})
            except UploadError as error:
                return self._send(400, {"error": str(error)})
        if self.path == "/app/load-demo":
            try:
                return self._send(200, load_demo())
            except FileNotFoundError as error:
                return self._send(404, {"error": str(error)})
        if self.path == "/app/run":
            try:
                return self._send(200, start_run())
            except RuntimeError as error:
                return self._send(409, {"error": str(error)})
        if self.path == "/suspicion/dismiss":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            return self._send(200, dismiss(str(body.get("review_id", "")), str(body.get("note", ""))))
        if self.path != "/analyze":
            return self._send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            result = model.analyze(body.get("text", ""))
        except ValueError as error:  # bad JSON or empty review
            return self._send(400, {"error": str(error)})
        self._send(200, result)

    def _send(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    # ponytail: stdlib server, one request at a time under GIL, no auth/CORS. Move to FastAPI when frontend needs CORS or concurrency.
    ThreadingHTTPServer(("127.0.0.1", 8001), Handler).serve_forever()
