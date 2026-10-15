# Hugging Face credential and Gemma startup verification - October15

## Verified

- User's corrected canonical Secret Manager name is `HF_TOKEN`, project
  enterprise-gemma2. Version1 is enabled. No token value appears in Git, output,
  shell arguments, browser configuration or diagnostic files.
- Operator-only scripts/check_huggingface_access.py reads the secret into process
  memory, uses verified HTTPS to the fixed huggingface.co origin with redirects
  and environment proxies disabled, checks identity and repository authorization,
  and emits status codes/role only. No CLI login/token cache or model weights.
- Live identity200, fineGrained token role, selected repository
  google/gemma-4-31B-it authorization200. Repository access is confirmed;
  successful download, startup and inference are NOT established by this check.
- The older configured repository google/gemma-2-2b-it returned403 with this token.
  Do not broaden the token to access this unrelated model automatically.
- User also created wzos-v2-google-gemma-api-key. Its label does not make it a
  Google inference API key. Do not copy either credential into Google API calls,
  frontend config, scanner environments, Git or logs. Do not delete either secret
  without a separately reviewed reason; use HF_TOKEN as the canonical HF name.

## Actual reported failure

Read failed revision gemma-inference-00007-njh and its logs directly. It was
loading google/gemma-2-2b-it and failed with Hugging Face GatedRepoError401 for
config.json before the server could listen on8080. Generic Cloud Run PORT timeout
is the consequence, not proof of a port mismatch. Latest created revision still07;
no latest ready revision reported. Runtime identity is the default compute service
account. No inference restart/deploy or secret-access grant made in this inspection.

The current approved Atlas deployment helper scripts/deploy_atlas_vllm.sh targets
Gemma4 31B and prepared Google Storage model artifacts. It does not use a Hugging
Face token. Do not reactivate the old2B service as the production Atlas engine.

## Correct consumption when the HF source is selected

Map Secret Manager HF_TOKEN's reviewed version to the server-side `HF_TOKEN`
environment variable only in the dedicated model-download/runtime process that
actually reads Hugging Face. Grant that consumer secretAccessor only on this one
secret, subject to the required explicit access review. Do not grant project-wide
secret access or attach the token to the account web service or scanner.
For the existing immutable Google Storage loading path, keep object-viewer access
on its model artifact path; do not inject an unused HF credential.

Before production inference: verify selected model and immutable weight revisions,
complete artifact/integrity manifest, trusted compatible serving image, accelerator
memory, network/cold-start and caller identity. Keep bounded capacity/runtime and
an explicit cleanup guard. No change to Google model terms or HF license acceptance
is performed by these checks. Any terms acceptance or credential edit stays with Ray.

## Verification repair

The HF auth-check endpoint can return plain text with200. Fixed the operator
checker to use that status without parsing it as JSON. Two focused tests PASS,
including denied-model behavior and no token in output/subprocess arguments.
This helper change does not alter application code or its accepted689/108 gate.

Primary references:
- https://huggingface.co/docs/hub/security-tokens
- https://huggingface.co/docs/huggingface_hub/v1.6.0/en/package_reference/hf_api
- https://huggingface.co/google/gemma-4-31B-it
