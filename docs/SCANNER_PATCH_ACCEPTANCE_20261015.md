# Patched scanner and Atlas artifact verification - October 15, 2026

## Verified repair

- Scanner source2fffe783a47e9b0b445d2081d185fc10fe8b4d75.
- Official Ubuntu26.04 amd64 base inspected via Docker manifest:
  ubuntu:26.04@sha256:88a381d5b5eeb2b35d3ad70925a362c37ce569daf43ede89ff818ec20e4d3794.
- Uses only the supported distro/security feed, applies available OS updates,
  requires engine>=1.5.4 and vendor CVD certificates. No testing/unstable sources.
- Minimal Python venv; dependency consistency checked; pip removed from final
  venv and distro pip wheel removed. No app schema/API/dependency changes.
- Cloud Build40db26b2-9f1b-4f98-8742-348accc66b22 SUCCESS.
- Immutable result:
  us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:6190d698438aff6ab92ea9e8de8acce9f9149cd1e94c7e374ab5e0a95903da16.

## Container acceptance

Cloud Build33a26700-bbaa-4460-adea-8db133da5e23 SUCCESS, harness451bfc3.
Explicit SCANNER_IMAGE_GATE_PASS. Engine1.5.4/28154, distro package
1.5.4+dfsg-0ubuntu0.26.04.1, Python3.14.4, non-root10001. Runtime pip absence
asserted. Clean fixture clean, EICAR fixture infected, expanded ZIP limit error,
missing caller401, expired worker error; recycle/shutdown/network and missing
certificate checks pass. Both boots24s; steady1.116GiB under4GiB limit.
This is container behavior acceptance, not vulnerability clearance/deployment.

## Atlas preparation

Live read-only verification compared Google source and retained model object
names, sizes and CRC32C values. All10 objects/62,578,670,545 bytes match.
Saved object generations in cloud evidence atlas-artifacts.json; no weights
redownloaded and no GPU started. Current wzos-atlas-inference service absent;
old gemma-inference has no ready revision. HF_TOKEN access already verified.
Five focused local tests pass:2 HF checks and3 artifact-integrity cases,
including same-size changed checksum and missing-object rejection. Used bundled
Python runtime; Windows Store alias is not an installed Python interpreter.

## Pending

Review buildfd9f372c-a40b-43ea-86ac-7330efba06e9 SUCCESS; review.exit0.
96 findings: HIGH0, CRITICAL0, MEDIUM92, LOW3, MINIMAL1; fixAvailable0.
All18 previous HIGH findings and six fixAvailable pip findings absent. Remaining
lower-severity findings still need applicability review; do not label image clean.
Temporary binding removed; independent IAM lookup returned[]. Role stays unbound.
No scanner service, new runtime identity or production activation performed.
Cloud evidence pointer:~/wzos-scanner-patched-latest.txt.

Primary package evidence:
https://packages.ubuntu.com/search?keywords=clamav&suite=resolute

Existing Atlas subnet wzos-atlas-us-central1 has Private Google Access=true,
10.83.0.0/26; dedicated inference identity exists. These read-only checks do not
establish effective invocation permissions, current cost or live inference.
