#!/usr/bin/env bash
# Cloud Shell local Docker acceptance only: no cloud resource/IAM/deployment.
set -euo pipefail
umask 077
evidence=${1:?Private evidence directory required}
base=${2:?Inspected official Python base digest required}
[[ $base =~ ^python:3\.12-slim-trixie@sha256:[0-9a-f]{64}$ ]] || exit 2
test "$(uname -s)" = Linux
test "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -ge 4200000
mkdir -p "$evidence"; evidence=$(realpath "$evidence")
context=$(mktemp -d /tmp/wzos-scanner-image.XXXXXXXX)
container=''
cleanup() {
  result=$?
  if [[ -n $container ]]; then
    docker logs "$container" > "$evidence/last-container.log" 2>&1 || true
    docker inspect --format '{{json .State}}' "$container" > "$evidence/last-container-state.json" 2>/dev/null || true
    docker rm -f "$container" >/dev/null 2>&1 || true
  fi
  case "$context" in /tmp/wzos-scanner-image.*) rm -rf -- "$context";; esac
  printf '%s\n' "$result" > "$evidence/image.exit"
}
trap cleanup EXIT
git rev-parse HEAD > "$evidence/source.txt"
printf '%s\n' "$base" > "$evidence/base.txt"
git archive HEAD Dockerfile.scanner requirements-scanner.txt services/__init__.py \
  services/workspace_preview/__init__.py services/workspace_preview/archive_policy.py \
  services/workspace_preview/clamd_scanner.py services/workspace_preview/security.py \
  services/workspace_preview/scanner_transport.py services/workspace_preview/scanner_service.py \
  services/workspace_preview/scanner_runtime.py | tar -x -C "$context"
if [[ -n ${WZOS_SCANNER_TEST_IMAGE:-} ]]; then
  [[ $WZOS_SCANNER_TEST_IMAGE =~ ^us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:[0-9a-f]{64}$ ]] || exit 2
  printf '%s\n' "$WZOS_SCANNER_TEST_IMAGE" > "$evidence/prebuilt-image.txt"
  timeout 300 docker pull --platform linux/amd64 "$WZOS_SCANNER_TEST_IMAGE" > "$evidence/build.log" 2>&1
  docker image inspect --format '{{.Id}}' "$WZOS_SCANNER_TEST_IMAGE" > "$evidence/image.id"
else
  timeout 900 docker build --platform linux/amd64 --build-arg "PYTHON_IMAGE=$base" \
    --iidfile "$evidence/image.id" -f "$context/Dockerfile.scanner" "$context" > "$evidence/build.log" 2>&1
fi
image=$(cat "$evidence/image.id")
launch() {
  container=$(docker run -d --memory=4g --cpus=1 --pids-limit=96 --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=768m --cap-drop=ALL --security-opt=no-new-privileges \
    --user 10001:10001 --env WZOS_SCANNER_AUDIENCE=https://wzos-synthetic.run.app \
    --env WZOS_SCANNER_CALLER=wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com \
    "$@" "$image")
}
ready() {
  for ((attempt=0; attempt<110; attempt++)); do
    test "$(docker inspect --format '{{.State.Running}}' "$container")" = true || return 1
    if docker exec "$container" python -c 'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8080/healthz",timeout=1).status==200' >/dev/null 2>&1; then return 0; fi
    sleep 2
  done
  return 1
}
launch
started=$SECONDS
ready
printf 'first_boot_seconds=%s\n' "$((SECONDS-started))" > "$evidence/timing.txt"
docker exec "$container" sh -c 'id; clamd --version; dpkg-query -W clamav-daemon clamav-freshclam' > "$evidence/runtime-packages.txt"
docker stats --no-stream --format '{{.MemUsage}}' "$container" > "$evidence/steady-memory.txt"
docker exec -i "$container" python - < scripts/check_scanner_container.py > "$evidence/engine-results.json"
timeout 15 docker wait "$container" > "$evidence/recycle.exit"
test "$(cat "$evidence/recycle.exit")" = 0
docker logs "$container" > "$evidence/recycle.log" 2>&1
docker rm "$container" >/dev/null; container=''
launch
started=$SECONDS
ready
printf 'second_boot_seconds=%s\n' "$((SECONDS-started))" >> "$evidence/timing.txt"
docker stop --time 9 "$container" >/dev/null
test "$(docker inspect --format '{{.State.ExitCode}}' "$container")" = 0
docker logs "$container" > "$evidence/shutdown.log" 2>&1
docker rm "$container" >/dev/null; container=''
launch --network none
timeout 95 docker wait "$container" > "$evidence/network-failure.exit"
test "$(cat "$evidence/network-failure.exit")" = 1
docker logs "$container" > "$evidence/network-failure.log" 2>&1
docker rm "$container" >/dev/null; container=''
launch --env WZOS_CLAM_CERTS_DIR=/missing-vendor-certificates
timeout 15 docker wait "$container" > "$evidence/certificate-failure.exit"
test "$(cat "$evidence/certificate-failure.exit")" = 1
echo SCANNER_IMAGE_GATE_PASS
