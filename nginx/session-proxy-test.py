"""CI-only stub: verify nginx forwards session POSTs and their bodies."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == "/api/health" else 404)
        self.end_headers()

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        valid = self.path == "/api/session" and body == b"email=test&password=test"
        self.send_response(200 if valid else 400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"proxied": valid}).encode())


HTTPServer(("127.0.0.1", 8082), Handler).serve_forever()
