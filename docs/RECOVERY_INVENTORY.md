# Recovery inventory — 2026-09-15

Verification update: 2026-09-17. Infrastructure status observations below remain dated September 15; source archives and build-source object generations were revalidated September 17.

## Scope and preservation policy

Inspection used the signed-in Google Cloud console and Cloud Shell for project `enterprise-gemma2` (`910004733138`), plus the local Git checkout. Preserve useful historical source, assets, and Git history. Do not delete originals or replace V2 files merely because another copy is larger or newer.

Cloud commands in this recovery created archive files in a new Cloud Shell home-directory folder and read project metadata. They did not deploy services, change IAM, enable APIs, send emails, or modify the source directories.

## Preserved material

| Source | State observed | Recovery copy |
| --- | --- | --- |
| GitHub V1 baseline | `390bb2a74c1574b6294faf80388bffe1a3586e8b` | Local `v1-recovery-2026-09-15` tag, `github-v1-baseline.zip`, and local history bundle |
| Local V2 | `e0547074c2bebd8bf9b7f0844bceb28398229a1c` | Local history bundle; current working branch `enterprise-v2` |
| Cloud Shell `~/gemma-cloudrun` | HEAD `88232a90a2e7af603908013a5f92a1318ac14605`; one commit ahead of its recorded `origin/main`; nested checkout marked modified | Working-tree files and `outer.bundle` in the Cloud Shell archive |
| Cloud Shell `~/gemma-cloudrun/gemma-cloudrun` | HEAD `0a0f7f040850fbbd653e885c27cc3dfa0f3fe4af`; tracked bytecode modified | Working-tree source/assets and `nested.bundle` in the Cloud Shell archive |
| Cloud Shell `~/gemma-inference` | Surviving inference Dockerfile | Working-tree file in the Cloud Shell archive |

The nested commit exactly matches the submodule pointer in the GitHub baseline. Its source has been located and archived; the active local submodule has not been changed.

The Cloud Shell archive contains **44 working-tree files plus two Git history bundles**, with a SHA-256 manifest for each entry. Historical PDFs, PNGs, and backup Python files were retained. `.git` working directories, caches, virtual environments, and dependency directories were excluded; independent history bundles preserve reachable Git history. Credential-pattern and symlink exclusions were configured; none were encountered among the remaining files. This is not a claim that historical Git content has undergone a full secrets audit. Keep archives private.

### Archive locations and checksums

Local recovery directory: `.local-recovery/20260915/` (ignored by Git).

- `local-v1-v2.bundle`: SHA-256 `020f6f4d88c6b58d21de4f3688cd683bbde9f32401bf0b0f27fa176f25b3d19b`; `git bundle verify` passed and reports complete history.
- `github-v1-baseline.zip`: historical source/assets exported from the V1 tag, including files removed from the V2 working tree by the earlier cleanup.
- `github-v1-baseline-exact.zip`: **1,371,360 bytes**, SHA-256 `84fb0122066df9985e4736f38657b0ad7914c19b4e2eb768e717ecca8b1c2b5b`. Created September 17 with `core.autocrlf=false`; all **34 file entries** match the original Git blobs byte for byte, and ZIP CRC checks passed. Use this archive for restoration. The earlier ZIP was retained but had Windows line-ending conversion in 31 entries, including two PDFs; it is not a byte-exact preservation copy. The complete Git history bundle is also verified and preserves original objects.

Cloud Shell directory: `/home/admin_/enterprise-v2-recovery-20260915-01/`.

- `cloudshell-survivors.zip`: **5,308,060 bytes**, SHA-256 `6e4ed64c70386a673cae2d3134a4d06b7599896fd6bc036e6eb1026710384f6e`.
- `cloud-inventory.json`: **14,116 bytes**, SHA-256 `ebe9e86a0ba90ca66d21bac6d8b372a2937dc53c120b520f6ef4ee885d3be707`.
- `outer.bundle`, `nested.bundle`, and `archive.sha256` also remain in the Cloud Shell recovery directory.

**Local recovery verified September 17.** After reconnecting Chrome, the source ZIP was downloaded, copied into `.local-recovery/20260915/`, and verified against its cloud SHA-256. ZIP CRC, all 46 manifest entries, and both history bundles passed validation. Files were extracted into `cloudshell-snapshot/` only after checking archive paths and rejecting links. A separate bare checkout of the outer history lives at `outer-history.git`; the active V2 repository was not replaced or merged.

`cloud-inventory.json` is also preserved in `.local-recovery/20260915/` and matches its recorded hash byte for byte. Its transfer was verified independently of the browser's download-success indication. The original Cloud Shell archives remain intact. `.gitignore`, `.dockerignore`, and `.gcloudignore` exclude `.local-recovery` from source control, Docker contexts, and gcloud source uploads; no deployment was performed to test those upload paths.

### Build-source recovery, September 17

Retrieved the exact object generations recorded in the successful Cloud Build jobs for API `v17` and inference `v3-python3`. Both downloads matched their Cloud Storage MD5 metadata. Preserved them in Cloud Shell at `/home/admin_/enterprise-v2-recovery-20260917-builds/` and locally at `.local-recovery/20260917/`.

- `build-sources-20260917.zip`: **21,046 bytes**, SHA-256 `55ce4cbd4080ccf45f72596ee542747021aa30976ba5aaf73d6a60a06395836a`; local ZIP CRC and manifest hashes passed.
- `api-v17.tgz`: **19,946 bytes**, SHA-256 `d008fdffc4975486f4aa53b63c66083b5d241eecd2e1f451327d9230fdf7466b`; source object generation `1781446216353084`.
- `inference-v3.tgz`: **465 bytes**, SHA-256 `764c58ba6c40e447ca49bb4435f91d5f9063370ee473140a2c79614861f3a747`; source object generation `1780766519272276`.

The two tar archives contain 16 regular files in total and were extracted into `build-sources-snapshot/` after path/type validation. These are archived build inputs, not a fresh image rebuild or runtime test.

The API build's `main.py` SHA-256 is `f9e8bd6e3ce45a245975610082240698c408e60336d13f50004170ae50ff9ccb`: **an exact match for the GitHub baseline**. Its frontend and several deployment/support files differ; preserve both versions. The inference build contains a clean 385-byte Dockerfile (SHA-256 `3149bae42d3b99a9a19f48e5a223e6f344f3d1ac51fe65ca0b09f1d36cc4a223`) using `vllm/vllm-openai:latest` and default `MODEL_ID=google/gemma-2-2b-it`. This historical default does not select the V2 model.

## Initial source validation

| File | Result | Consequence |
| --- | --- | --- |
| Local V2 `main.py` | Python compilation passed during baseline recovery; unchanged since | Retain as the initial implementation baseline |
| Cloud Shell outer `main.py` | 146,364 bytes, 4,314 lines; invalid Python syntax at line 47 | Preserve and recover useful sections selectively; do not substitute wholesale |
| Cloud Shell nested `main.py` | 38,860 bytes, 1,352 lines; AST parsing passed | Useful historical reference; runtime behavior not validated |
| Cloud Shell inference Dockerfile | 1,171 bytes, 36 lines; begins with `FROM vllm/vllm-openai:latestdiff --git ...` and contains diff markers | Damaged working source; reconstruct from known-good definitions after comparison |

Hashes for the outer Python file, nested Python file, and inference Dockerfile respectively:

```text
aa887df0486e60937876d09c6dfbcc26b65d12ff5e2e62c46df4e725ab8c9348
62e56d5d6f28270957775def59346fdebbd2e04cfff18ac3fc54b59fabe43a06
b4caa9ac309bfcd87d2a90deed6cba96526b35fafa0a1a9bcb21a1ece8405771
```

The damaged working Dockerfile does not establish the contents of the deployed image or the root cause of its startup failure.

## Live infrastructure findings

| Component | Observed state | V2 implication |
| --- | --- | --- |
| Cloud Run `gemma-assistant-api` | Ready; latest created/ready revision `gemma-assistant-api-00008-njc`; image tag `v17` in `us-central1` | Container startup works; generation and delivery were not functionally exercised |
| Application configuration | Uses the legacy dedicated Vertex endpoint in `us-east1` and `PACKAGE_BUCKET=gemma_think` | Reconcile configuration before any deployment |
| Cloud Run `gemma-inference` | Not ready; latest created revision `gemma-inference-00006-xfp`; no latest-ready revision reported | Repair or replace the inference runtime independently |
| Inference resources | 4 CPUs, 16 GiB RAM, 1 GPU; maximum scale 1; image tag `v3-python3`; port 8080 startup probe | Benchmark a validated runtime before choosing V2 sizing or raising limits |
| Inference error | Service state and retained audit logs report failure to listen on port 8080 before startup timeout | Generic startup failure confirmed; detailed runtime root cause remains unresolved |
| Vertex endpoints | Listing in `us-east1` returned no endpoints | The app's configured model target is not present in that project's regional inventory |
| Storage | Project listing returned `enterprise-gemma2_cloudbuild` and `gemma_think_v2`, both in US | `gemma_think` is absent from this project listing; cross-project existence/access was not tested |
| Artifact Registry | Docker repositories `enterprise-gemma2` and `gemma-repo` remain | Existing images/build sources may provide additional recovery material |
| Cloud Build | Latest returned build succeeded on 2026-06-14; historical inference image build also succeeded | Successful image build is not evidence of a working runtime |
| Build trigger | `deploy-to-main-branch` targets `rbandrews2/gemma-cloudrun`, branch regex `^main$`, configuration `cloudbuild.yaml` in the preserved September 15 snapshot | This is a different repository name from `enterprise-gemma2`; refresh trigger inventory before any deployment-related push. None pushed during recovery |
| Secret Manager | `GOOGLE_MAPS_API_KEY` secret exists; values not read | Validate use and access during integration; existence alone does not prove the API key works |
| Access | Application uses `AUTH_PROVIDER=iap`; backend `gemma-assistant-api-backend` has IAP enabled; service-level invoker policy includes the IAP service agent and the admin user | Preserve this access arrangement pending a full WZOS identity design; project-level inherited access and browser login were not exhaustively audited |
| Compute Engine | Instance listing returned no VMs | Does not establish zero project cost; billing and other resource classes remain to be assessed |

The recovered local `/deliver-package` route creates package assets and delivery-preview metadata. It does not implement actual Gmail sending. Authentication, organization isolation, model output quality, storage retrieval, and end-to-end package generation remain validation tasks.

## Recovery outcome and remaining limits

The identified surviving working trees, independent Git history, metadata snapshot, and two key build-source archives are preserved and locally verified. The [reconciliation report](V2_RECONCILIATION.md) records the useful feature drafts and baseline decision. No historical source was deleted, merged, or executed during recovery.

Remaining work: choose an independent long-term backup location/retention policy; diagnose inference startup from runtime evidence; validate cloud dependencies and end-to-end behavior in staging. The historical container images themselves, customer bucket contents, and all past build archives were not mirrored. Their existence and usefulness can be assessed separately without delaying the local service skeleton.
