# Report routing on entrack

The existing SSH deployment installs nginx and its JavaScript module, validates
the configuration, then restarts Traccar on 127.0.0.1:8082 and starts/reloads
nginx on port 80. This first listener change causes a brief interruption.
The installer targets Debian/Ubuntu and requires njs >= 0.4.3.
Traccar is the default HTTP server on IPv4 and IPv6, so requests with an
alternate Host header also reach the API. The installer disables the packaged
sites-enabled/default symlink and preserves its source file. Other sites are
preserved; custom default_server listeners must be resolved before deployment. The Docker cloud-init path is separate and is unchanged.

Reports whose first decoded `from` value is strictly older than seven days go
to the configured Lambda URL; all other requests go to the local Traccar.
The cutoff uses UTC to match the edge runtime. Missing, empty and invalid
dates stay local; a range crossing the cutoff goes entirely to Lambda.
Both maps in traccar.conf must use the same archive hostname. If the dashboard
uses TRACCAR_REPORTS_SERVER, substitute its value before deploying.

The full request URI, query arguments, body and authentication headers are
preserved. Lambda uses its own Host/SNI and verified HTTPS. The regular proxy
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
