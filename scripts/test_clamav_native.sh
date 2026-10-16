#!/usr/bin/env bash
# Disposable Cloud Shell acceptance; downloads official distro packages WITHOUT
# installing packages, running package hooks, or registering background services.
set -euo pipefail
umask 077
evidence=${1:?Pass a private evidence directory}
workflow_args=()
if [[ ${2:-} == --workflow ]]; then workflow_args=(--workflow)
elif [[ $# -gt 1 ]]; then echo 'ENGINE_GATE_BLOCKED: unknown option'; exit 2; fi
test "$(uname -s)" = Linux || { echo 'ENGINE_GATE_BLOCKED: Linux required'; exit 2; }
export PATH="/usr/sbin:/sbin:$PATH"
available=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$available" -ge 4200000 || { echo 'ENGINE_GATE_BLOCKED: less than 4GiB available'; exit 2; }
home_available=$(df --output=avail -k "$HOME" | tail -n 1 | tr -d ' ')
test "$home_available" -ge 1000000 || { echo 'ENGINE_GATE_BLOCKED: insufficient signature-cache disk'; exit 2; }
test -x .venv-accounts-test/bin/python || { echo 'ENGINE_GATE_BLOCKED: run regression gate first'; exit 2; }
mkdir -p "$evidence"
evidence=$(realpath "$evidence")
work=$(mktemp -d /tmp/wzos-clamav-native.XXXXXXXX)
cleanup() {
  case "$work" in /tmp/wzos-clamav-native.*) rm -rf -- "$work";; esac
}
trap 'result=$?; printf "%s\n" "$result" > "$evidence/engine.exit"; cleanup' EXIT
mkdir "$work/debs" "$work/tools"
if ! command -v clamd >/dev/null || ! command -v freshclam >/dev/null; then
  timeout 180 sudo -n apt-get -qq update > "$evidence/package-download.log" 2>&1
  timeout 360 sudo -n apt-get -qq -y --download-only --no-install-recommends \
    -o "Dir::Cache::archives=$work/debs" install clamav-daemon clamav-freshclam >> "$evidence/package-download.log" 2>&1
  for package in "$work/debs/"*.deb; do
    test -f "$package"
    dpkg-deb -x "$package" "$work/tools"
  done
  export PATH="$work/tools/usr/bin:$work/tools/usr/sbin:$PATH"
  export LD_LIBRARY_PATH="$work/tools/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH):${LD_LIBRARY_PATH:-}"
fi
command -v clamd >/dev/null; command -v freshclam >/dev/null
cert_args=()
engine_cert_args=()
if freshclam --help | grep -q -- '--cvdcertsdir'; then
  certs="$work/tools/etc/clamav/certs"
  if ! test -d "$certs"; then certs=/etc/clamav/certs; fi
  test -d "$certs" || { echo 'ENGINE_GATE_BLOCKED: official code-signature certificates missing'; exit 2; }
  cert_args=("--cvdcertsdir=$certs")
  engine_cert_args=(--certs-dir "$certs")
  # The database-testing child also needs the vendor's documented certificate path.
  export CVD_CERTS_DIR="$certs"
fi
database="$HOME/.cache/wzos-clamav/official-db"
mkdir -p "$database"; chmod 700 "$database"
cat > "$work/freshclam.conf" <<EOF
DatabaseDirectory $database
DatabaseOwner $(id -un)
DatabaseMirror database.clamav.net
ConnectTimeout 10
ReceiveTimeout 30
MaxAttempts 1
TestDatabases yes
EOF
timeout 360 freshclam --config-file="$work/freshclam.conf" "${cert_args[@]}" --stdout > "$evidence/freshclam.log" 2>&1
TZ=UTC timeout 240 .venv-accounts-test/bin/python scripts/check_clamav_engine.py \
  --database-dir "$database" --evidence-dir "$evidence" "${engine_cert_args[@]}" "${workflow_args[@]}" > "$evidence/engine.log" 2>&1
tail -n 3 "$evidence/engine.log"
