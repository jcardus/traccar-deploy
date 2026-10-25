"""Exercise nginx position routing with local Traccar and archive stand-ins."""
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import threading
from urllib.parse import urlencode


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(401 if "denied=1" in self.path else 200)
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
    old = (now - timedelta(days=15)).isoformat()
    recent = (now - timedelta(days=13)).isoformat()
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
    cases += [
        ("/api/positions?" + urlencode({"from": (now - timedelta(days=10)).isoformat()}), "traccar"),
        ("/api/reports/route?" + urlencode({"from": recent}), "traccar"),
    ]
    count = 0
    for origin in ["http://127.0.0.1", "http://[::1]"]:
        for path, expected in cases:
            for request_origin in [None, "https://dash.example"]:
                args = [
                    "curl", "--noproxy", "*", "--silent", "--show-error",
                    "--include", "-H", "Host: alternate.example",
                    "-H", "Authorization: Bearer ci-test",
                    "-H", "Cookie: JSESSIONID=ci-test",
                    "-H", "Accept: application/json",
                ]
                if request_origin:
                    args += ["-H", "Origin: " + request_origin]
                raw = subprocess.check_output(args + [origin + path], text=True)
                head, body = raw.split("\n\n", 1)
                assert "200 OK" in head, raw
                headers = {}
                for line in head.splitlines()[1:]:
                    key, value = line.split(":", 1)
                    headers.setdefault(key.lower(), []).append(value.strip())
                assert "access-control-allow-origin" not in headers, head
                assert "access-control-allow-credentials" not in headers, head
                assert "vary" not in headers, head
                assert json.loads(body) == {
                    "backend": expected, "uri": path,
                    "authorization": "Bearer ci-test",
                    "cookie": "JSESSIONID=ci-test", "accept": "application/json",
                }, (origin, path, body)
                count += 1
        for path in ["/api/positions?denied=1", "/api/reports/route?denied=1"]:
            raw = subprocess.check_output([
                "curl", "--noproxy", "*", "--silent", "--show-error", "--include",
                "-H", "Origin: https://dash.example", origin + path,
            ], text=True)
            assert "401 Unauthorized" in raw, raw
            assert "Access-Control-Allow-Origin:" not in raw, raw
            assert "Access-Control-Allow-Credentials:" not in raw, raw
            count += 1
    print("Passed", count, "proxy checks for positions, reports, response headers.")
finally:
    for server in servers:
        server.shutdown()
        server.server_close()
