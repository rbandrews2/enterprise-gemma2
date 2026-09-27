#!/usr/bin/env bash
# Render by default. Run --apply only after quota, bucket/IAM/network preflight.
# This creates only the approved private inference service; no V1 changes.
set -euo pipefail
mode="${1:---print}"
[[ "$mode" == --print || "$mode" == --apply ]] || { echo 'Use --print or --apply' >&2; exit 2; }
: "${ATLAS_MODEL_URI:?Set immutable prepared gs:// model directory}"
: "${ATLAS_RUNTIME_IDENTITY:?Set dedicated inference service account email}"
: "${ATLAS_NETWORK:?Set isolated network name}"
: "${ATLAS_SUBNET:?Set us-central1 subnet with Private Google Access}"
[[ "$ATLAS_MODEL_URI" == gs://enterprise-gemma2-*/* ]] || { echo 'Expected project model bucket' >&2; exit 2; }
[[ "$ATLAS_RUNTIME_IDENTITY" == *@enterprise-gemma2.iam.gserviceaccount.com ]] || exit 2
for value in "$ATLAS_MODEL_URI" "$ATLAS_RUNTIME_IDENTITY" "$ATLAS_NETWORK" "$ATLAS_SUBNET"; do
  [[ "$value" != *','* && "$value" != *$'\n'* ]] || exit 2
done
image='us-docker.pkg.dev/vertex-ai/vertex-vision-model-garden-dockers/pytorch-vllm-serve@sha256:3fbc0e08c46e7736145c9effbcc8839682c80b15b413335146f4428fc3523c8a'
args=(serve "$ATLAS_MODEL_URI" --served-model-name=google/gemma-4-31B-it
  --enable-chunked-prefill --enable-prefix-caching --generation-config=auto
  --reasoning-parser=gemma4 --dtype=bfloat16 --quantization=fp8 --kv-cache-dtype=fp8
  --max-num-seqs=2 --max-model-len=32767 --gpu-memory-utilization=0.95
  --tensor-parallel-size=1 --load-format=runai_streamer --port=8080 --host=0.0.0.0)
joined=$(IFS=,; echo "${args[*]}")
cmd=(gcloud beta run deploy wzos-atlas-inference --project enterprise-gemma2
  --labels=wzos-trial=20260926
  --region us-central1 --image "$image" --service-account "$ATLAS_RUNTIME_IDENTITY"
  --execution-environment gen2 --no-allow-unauthenticated --cpu 20 --memory 80Gi
  --gpu 1 --gpu-type nvidia-rtx-pro-6000 --no-gpu-zonal-redundancy
  --no-cpu-throttling --no-cpu-boost --min 0 --max 1 --min-instances 0 --max-instances 1
  --concurrency 2 --network "$ATLAS_NETWORK" --subnet "$ATLAS_SUBNET"
  --vpc-egress all-traffic --port 8080 --timeout 300
  --startup-probe tcpSocket.port=8080,initialDelaySeconds=0,failureThreshold=24,timeoutSeconds=5,periodSeconds=10
  --command vllm --args "$joined")
if [[ "$mode" == --print ]]; then
  printf '%q ' "${cmd[@]}"; printf '\n'
else
  # No retries. Operator must track session runtime and tear down failed services.
  "${cmd[@]}"
fi
