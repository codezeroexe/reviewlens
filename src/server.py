"""Stdlib HTTP endpoint: POST /analyze with {"text": "..."} -> ReviewLens result, plus the dashboard API.

Every response is strict JSON (NaN becomes null). Unexpected errors return a JSON error, never a dropped connection.
"""

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

import pandas as pd

from complaints.service import get_cluster_reviews, get_clusters, get_unclustered_reviews
from contradictions.service import find_contradictions, get_review
from suspicion.service import dismiss, get_results, get_similar, list_dismissed
from insights.service import get_all, get_evidence, get_overview
from dashboard.state import filtered_view, get_overview as app_overview, get_status, load_demo, start_run
from dashboard.data import MAX_BYTES, UploadError, load_upload
from src.reviewlens_inference import ReviewLens

model = ReviewLens("models")  # load once at startup

ANALYZE_LIMIT = 100_000
SMALL_LIMIT = 10_000


def _clean(value):
    """Make a payload strict-JSON safe: NaN/NaT/NA -> None, numpy scalars -> Python."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if pd.isna(value):
        return None
    if isinstance(value, float):
        return None if value in (float("inf"), float("-inf")) else value
    return value.item() if hasattr(value, "item") else str(value)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._guard(self._get)

    def do_POST(self):
        self._guard(self._post)

    def _guard(self, handler):
        """Route on the path only (query strings allowed) and turn every failure into a JSON error."""
        parsed = urlparse(self.path)
        self.route, self.query = unquote(parsed.path), {k: v[0] for k, v in parse_qs(parsed.query).items()}
        try:
            handler()
        except (FileNotFoundError, KeyError) as error:
            self._send(404, {"error": str(error.args[0]) if isinstance(error, KeyError) else str(error)})
        except RuntimeError as error:
            self._send(409, {"error": str(error)})
        except ValueError as error:  # UploadError is a ValueError
            self._send(400, {"error": str(error)})
        except Exception:  # noqa: BLE001 - last resort, keep the server answering
            traceback.print_exc()
            self._send(500, {"error": "Internal server error."})

    # ---- GET ----
    def _get(self):
        path = self.route
        if path == "/complaints":
            return self._send(200, get_clusters())
        if path == "/complaints/unclustered":
            return self._send(200, get_unclustered_reviews())
        if path.startswith("/complaints/cluster/") and path.endswith("/reviews"):
            cid = path[len("/complaints/cluster/"):-len("/reviews")]
            if not cid.isdigit():
                raise ValueError("bad cluster id")
            return self._send(200, get_cluster_reviews(int(cid)))
        if path == "/contradictions":
            return self._send(200, {"conflicts": find_contradictions()})
        if path.startswith("/contradictions/review/"):
            row = get_review(path[len("/contradictions/review/"):])
            return self._send(200, row) if row else self._send(404, {"error": "review not found"})
        if path == "/suspicion":
            rows = get_results()
            rows = rows[rows["signal_count"] > 0].drop(columns=["details"], errors="ignore")
            return self._send(200, {"rows": rows.fillna("").to_dict(orient="records"),
                                    "dismissed": list_dismissed(),
                                    "rule": "0 signals: No signals; 1: Low; 2: Medium; 3+: High (counts of different signals, not a probability)"})
        if path.startswith("/suspicion/similar/"):
            return self._send(200, get_similar(path[len("/suspicion/similar/"):]))
        if path == "/app/status":
            return self._send(200, get_status())
        if path == "/app/view":
            return self._send(200, filtered_view(self.query))
        if path == "/app/overview":
            return self._send(200, app_overview())
        if path == "/insights":
            return self._send(200, get_overview())
        if path == "/insights/all":
            return self._send(200, get_all(self.query.get("type")))
        if path.startswith("/insights/evidence/"):
            return self._send(200, get_evidence(path[len("/insights/evidence/"):]))
        self._send(404, {"error": "not found"})

    # ---- POST ----
    def _post(self):
        path = self.route
        if path == "/app/upload":
            data = self._body(MAX_BYTES)
            info = load_upload(self.headers.get("X-Filename", "upload.csv"), data)
            return self._send(200, {**info, "status": get_status()})
        if path == "/app/load-demo":
            return self._send(200, load_demo())
        if path == "/app/run":
            return self._send(200, start_run())
        if path == "/suspicion/dismiss":
            body = self._json(SMALL_LIMIT)
            return self._send(200, dismiss(str(body.get("review_id", "")), str(body.get("note", ""))))
        if path == "/analyze":
            body = self._json(ANALYZE_LIMIT)
            return self._send(200, model.analyze(body.get("text", "")))
        self._send(404, {"error": "not found"})

    def _body(self, limit: int) -> bytes:
        length = self.headers.get("Content-Length", "")
        if not length.isdigit():
            raise ValueError("Content-Length header is required.")
        if int(length) > limit:
            self.close_connection = True  # body is left unread
            raise ValueError(f"Request body is larger than {limit:,} bytes.")
        return self.rfile.read(int(length))

    def _json(self, limit: int) -> dict:
        try:
            body = json.loads(self._body(limit))
        except json.JSONDecodeError:
            raise ValueError("Request body is not valid JSON.") from None
        if not isinstance(body, dict):
            raise ValueError('Request body must be a JSON object, e.g. {"text": "..."}.')
        return body

    def _send(self, status, payload):
        data = json.dumps(_clean(payload), allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    # ponytail: stdlib server, no auth/CORS. Move to FastAPI when the frontend needs CORS or real concurrency.
    ThreadingHTTPServer(("127.0.0.1", 8001), Handler).serve_forever()
