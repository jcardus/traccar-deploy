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
`from` value is strictly older than the configured retention period go
to the configured Lambda URL; all other requests go to the local Traccar.
Both paths use `set $database_retention_weeks 2;` in traccar.conf, equivalent
to the function's DATABASE_RETENTION_WEEKS default of two weeks. Change that
value to configure retention for both paths. Exactly at the cutoff stays local.
The cutoff uses UTC to match the edge runtime. Missing, empty and invalid
dates stay local; a range crossing the cutoff goes entirely to Lambda.
Live positions and lookups by `id` without `from` stay on Traccar. The exact
`/api/positions` path uses this rule; position subpaths keep normal proxying.
Both maps in traccar.conf must use the same archive hostname. If the dashboard
uses TRACCAR_REPORTS_SERVER, substitute its value before deploying.

Both /api/... and /traccar/api/... forms are accepted for reports and positions.
The leading /traccar/ prefix is removed before proxying, while the raw query,
body and authentication headers are preserved. Responses reflect the request
Origin (or * when absent) and set Access-Control-Allow-Credentials: true,
including error responses. Upstream CORS values are replaced to prevent
duplicate headers; Vary: Origin is added for caches. OPTIONS requests are
proxied, matching the corrected function rather than the earlier redirect code. Lambda uses its own Host/SNI and verified HTTPS. The regular proxy
also forwards WebSocket upgrades for /api/socket. Adjust the DNS resolver and
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
