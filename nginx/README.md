# Report and position routing on entrack

The existing SSH deployment installs nginx and its JavaScript module, validates
the configuration, then restarts Traccar on 127.0.0.1:8082 and starts/reloads
nginx on port 80. This first listener change causes a brief interruption.
The installer targets Debian/Ubuntu and requires njs >= 0.4.3.
Traccar is the default HTTP server on IPv4 and IPv6, so requests with an
alternate Host header also reach the API. The installer disables the packaged
sites-enabled/default symlink and preserves its source file. Other sites are
preserved; custom default_server listeners must be resolved before deployment. The Docker cloud-init path is separate and is unchanged.

Requests to `/api/reports/<report>` and `/api/positions` whose first decoded
`from` value is strictly older than seven days go
to the configured Lambda URL; all other requests go to the local Traccar.
Both paths share the original fixed seven-day cutoff. Exactly at the cutoff
stays local. The cutoff uses UTC to match the edge runtime. Missing, empty and invalid
dates stay local; a range crossing the cutoff goes entirely to Lambda.
Live positions and lookups by `id` without `from` stay on Traccar. The exact
`/api/positions` path uses this rule; position subpaths keep normal proxying.
Both maps in traccar.conf must use the same archive hostname. If the dashboard
uses TRACCAR_REPORTS_SERVER, substitute its value before deploying.

The original /api/... path, raw query, body and authentication headers are
preserved when proxying reports and positions. No CORS headers are added or
modified by nginx; the dashboard uses its same-origin API proxy. OPTIONS
requests are proxied normally. Lambda uses its own Host/SNI and verified HTTPS.
The regular proxy also forwards WebSocket upgrades for /api/socket. Adjust the DNS resolver and
CA bundle path if the server requires different values.

After deployment, verify recent and archived authenticated reports, exports,
repeated deviceId arguments, unauthenticated rejection and live WebSocket
updates. Verify upstream destinations using nginx logs.

Only after server verification should the dashboard's special
functions/api/reports/[report].js route and Vite /api/reports override be removed.
The shared edge route also handles traccar.jsrastreamento.com, so that backend
must be migrated too before removing it globally.

To roll back, retain the edge report route, stop nginx, restore web.port=80
and the previous web.address in Traccar's XML, then restart Traccar.

References:
- https://nginx.org/en/docs/http/ngx_http_js_module.html
- https://nginx.org/en/docs/http/ngx_http_proxy_module.html
