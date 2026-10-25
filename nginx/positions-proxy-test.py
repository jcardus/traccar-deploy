"""Exercise nginx position routing with local Traccar and archive stand-ins."""
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import threading
from urllib.parse import urlencode


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "backend": self.server.backend,
            "uri": self.path,
            "authorization": self.headers.get("Authorization"),
            "cookie": self.headers.get("Cookie"),
            "accept": self.headers.get("Accept"),
        }).encode())


servers = []
try:
    for port, backend in [(8082, "traccar"), (8083, "archive")]:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        server.backend = backend
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)

    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=8)).isoformat()
    recent = (now - timedelta(days=6)).isoformat()
    cases = [
        ("/api/positions", "traccar"),
        ("/api/positions?id=1&id=2", "traccar"),
        ("/api/positions?from=", "traccar"),
        ("/api/positions?from=invalid", "traccar"),
        ("/api/positions?" + urlencode({"from": recent}), "traccar"),
        ("/api/positions?" + urlencode([
            ("from", old), ("to", now.isoformat()), ("deviceId", 1),
            ("deviceId", 2)]), "archive"),
        ("/api/positions?" + urlencode([("from", recent), ("from", old)]), "traccar"),
        ("/api/positions?" + urlencode([("from", old), ("from", recent)]), "archive"),
        ("/api/positions/123?" + urlencode({"from": old}), "traccar"),
        ("/api/reports/route?" + urlencode({"from": old}), "archive"),
    ]
    for origin in ["http://127.0.0.1", "http://[::1]"]:
        for path, expected in cases:
            response = json.loads(subprocess.check_output([
                "curl", "--noproxy", "*", "--fail", "--silent", "--show-error",
                "-H", "Host: alternate.example",
                "-H", "Authorization: Bearer ci-test",
                "-H", "Cookie: JSESSIONID=ci-test",
                "-H", "Accept: application/json", origin + path,
            ], text=True))
            assert response == {
                "backend": expected, "uri": path,
                "authorization": "Bearer ci-test",
                "cookie": "JSESSIONID=ci-test", "accept": "application/json",
            }, (origin, path, response)
    print("Passed 20 proxy checks for positions and reports.")
finally:
    for server in servers:
        server.shutdown()
        server.server_close()
