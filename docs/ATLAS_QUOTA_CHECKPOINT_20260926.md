# Approved Atlas deployment checkpoint

Ray approved the $15 initial deployment/test allocation and approximately $1.17
per month for retained model weights. This approval persists; do not ask again
for the same scope. Production, public DNS, V1 and training jobs are outside it.

## Completed

- Enabled `cloudquotas.googleapis.com` in `enterprise-gemma2` only. Set billing
  project explicitly for quota commands to avoid the Cloud Shell consumer-project
  error encountered earlier.
- Confirmed RTX non-zonal quota had no positive allocation in us-central1.
- Requested 1,000 milliGPU (one RTX GPU), preference
  `wzos-atlas-rtx-us-central1`, trace `b5b5389d-b1cb-45d3-b934-e69c20ac3749`.
  Initial response: grantedValue 0, preferredValue 1000, reconciling true.
- Pinned Google's vLLM image digest:
  `sha256:3fbc0e08c46e7736145c9effbcc8839682c80b15b413335146f4428fc3523c8a`.
- Added print-first deployment command builder in `scripts/deploy_atlas_vllm.sh`.
  It requires actual prepared storage/identity/network values; it is not yet a
  deployed or GPU-validated configuration.

Subsequent status: quota grantedValue 1000, stateDetail "Quota request approved
to 1000". Created isolated `wzos-atlas-vpc` / `wzos-atlas-us-central1` subnet
(10.83.0.0/26, Private Google Access), dedicated `wzos-atlas-inference` service
identity and private regional `enterprise-gemma2-atlas-models-us-central1` bucket.
Inference identity has object-viewer access only on that bucket. Model copying
started directly between Cloud Storage buckets; no local weight download.

## Resume

Read the existing quota preference (do not create duplicates). When a positive
allocation is granted, verify available capacity, prepare isolated regional model
storage and network/identity permissions, copy and manifest official model files,
then deploy the pinned container. Enforce the approved budget operationally; do
not rely on max instances or alerts as a dollar cap. Run the bounded evaluation,
review results, and connect the account service only after acceptance.
