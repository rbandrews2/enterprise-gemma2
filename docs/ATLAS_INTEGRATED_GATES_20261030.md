# Ask Atlas integrated release gates — October 30, 2026

Step 1 is complete for candidate `061900a0c1d176f23a1fcdcc9cd0071ab7b63fe2`.

| Gate | Result | Failures / errors / skips |
| --- | --- | --- |
| Full Node suite, Node v24.22.1 | 199 passed | 0 / 0 / 0 |
| Full backend suite with disposable PostgreSQL 16 | 972 passed in 434.756 seconds | 0 / 0 / 0 |

The PostgreSQL gate included all 11 PostgreSQL Time Tracker correction cases.
No source repairs were necessary. The first shell launch stopped before tests
because the archived script contained CRLF line endings. The successful invocation
normalized only the shell input stream:

```bash
bash <(sed 's/\r$//' scripts/test_postgres_native.sh)
```

The script created a private Unix-socket database under a mode-700 temporary
directory, without a TCP listener, and removed it afterward. Independent readback
found no temporary gate cluster directories or running gate/database processes.
Every extracted candidate file still matched the uploaded archive after testing.

## Evidence

- Local: `.local-data/release-gates-061900a-20261030/` contains Node log, exit code,
  candidate archive and metadata. These ignored artifacts are not Git-backed.
- Cloud: `/home/admin_/wzos-gates-061900a-20261030/` contains the extracted source,
  `postgres.log`, `postgres.exit` (0), and the separate failed shell-preflight log.
- Archive SHA256: `a742c3487fcd14a7646624cbc616d0791969ccdcb0c638fa430bb4d901e6c223`.
- PostgreSQL log SHA256: `176107ac9693cf838343ada7a92dc4d88cfb4fea65d836023f5028d276363119`.
- Screenshot: ignored `.local-data/release-gates-061900a-20261030/cloud-result.png`.

This was a synthetic/disposable test run. No paid model calls, production database
changes, customer sends, IAM grants or live deployment. Existing model acceptance
and speed evidence was reused rather than repeated.

## Next

Authenticated in-app Ask Atlas acceptance remains, followed by the release build,
deployment and live verification. Broader source review and eight unresolved source
holds remain separate. Do not rerun these gates for documentation-only changes;
reuse this evidence while the tested application candidate remains unchanged.
