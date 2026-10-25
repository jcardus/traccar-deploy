#!/usr/bin/env bash
# Debian/Ubuntu system-service deployment, invoked as root.
set -euo pipefail
deployment_dir="${1:?Usage: install.sh DEPLOYMENT_DIRECTORY}"
policy_created=false
cleanup() {
    if "$policy_created"; then rm -f /usr/sbin/policy-rc.d; fi
}
trap cleanup EXIT
# Prevent package installation from starting nginx while Traccar owns port 80.
# Preserve any policy supplied by the server administrator.
if [ ! -e /usr/sbin/policy-rc.d ]; then
    printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
    chmod 755 /usr/sbin/policy-rc.d
    policy_created=true
fi
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx libnginx-mod-http-js ca-certificates curl
cleanup
policy_created=false

install -d /etc/nginx/njs
install -m 644 "$deployment_dir/nginx/reports.js" /etc/nginx/njs/reports.js
install -m 644 "$deployment_dir/nginx/traccar.conf" /etc/nginx/conf.d/traccar.conf
# Disable only the packaged default-site symlink; preserve its source file.
if [ -L /etc/nginx/sites-enabled/default ] &&
    [ "$(readlink -f /etc/nginx/sites-enabled/default)" = /etc/nginx/sites-available/default ]; then
    unlink /etc/nginx/sites-enabled/default
fi
# Test before changing the running Traccar listener.
nginx -t
install -m 644 "$deployment_dir/traccar.xml" /opt/traccar/conf/traccar.xml
systemctl restart traccar
# Wait for the new listener before exposing it through nginx.
for attempt in {1..60}; do
    if curl --fail --silent http://127.0.0.1:8082/api/health > /dev/null; then
        systemctl enable nginx
        if systemctl is-active --quiet nginx; then
            systemctl reload nginx
        else
            systemctl start nginx
        fi
        exit 0
    fi
    sleep 1
done
echo "Traccar did not become healthy on 127.0.0.1:8082; nginx was not reloaded." >&2
exit 1
