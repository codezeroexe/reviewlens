"""Stdlib HTTP endpoint: POST /analyze with {"text": "..."} -> ReviewLens result."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.reviewlens_inference import ReviewLens

model = ReviewLens("models")  # load once at startup


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
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
