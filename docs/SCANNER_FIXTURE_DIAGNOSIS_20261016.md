# Scanner fixture classification diagnosis - October 16, 2026

## Conclusion

The failed workflow asserted that nonstandard PDF-wrapped EICAR must be detected.
That expectation is invalid. EICAR specifies its 68-byte test string at the start
of the test file; the workflow prepends nine PDF-header bytes and appends a PDF
terminator, without constructing a valid embedded-file PDF. Mocked mode used a
substring test and therefore accepted an expectation the real engine did not.
This is a test-harness discrepancy, not evidence that arbitrary malware scanning
is comprehensive or that the failed live fixture was definitively classified clean
(the old workflow did not log that classification).

## Actual comparison

Diagnostic source d7b6ab4 extends the existing isolated native engine gate. It does
not change application code, signatures, permissions, quarantine policy or production.
Cloud Shell account/project verified. Official distro packages downloaded/extracted
without installing services; current official definitions refreshed and validated.
ClamAV 1.5.4/28155 results:

| Fixture / condition | Observed classification |
| --- | --- |
| Benign PDF-looking bytes | clean |
| Exact standard 68-byte EICAR | infected |
| Workflow's PDF-header + EICAR + terminator | clean |
| Intact standard EICAR inside an OOXML ZIP container | infected |
| Expanded archive beyond policy limit | error |
| Missing engine endpoint | error |

CLAMAV_ENGINE_GATE_PASS; engine.exit0; daemon_stopped true; child peak RSS998704KiB.
Evidence: $HOME/wzos-fixture-diagnosis-latest.txt points to
/home/admin_/wzos-fixture-diagnosis.HB7ms4zG (engine-results.json, engine.log,
clamd.log, freshclam.log, package-download.log, engine.exit and launch.log).
No fixture executable was run. All fixture bytes were assembled in memory.
This was a Cloud Shell engine comparison, not another Cloud Run job or exact
replay of the old deployed scanner instance/signature snapshot. The engine version
is1.5.4; do not infer that its current daily revision matches the earlier live run.

## Required correction and remaining acceptance

- Replace the synthetic PDF wrapper detection expectation with an intact standard
  fixture in a supported document container and exercise the actual supported upload
  path (Forms Hub accepts OOXML documents). Do not accept clean as a successful
  detection test or add a custom substring rule to the production scanner.
- Keep the invalid wrapper as a clearly labeled diagnostic, without asserting that
  it must be infected. Mocked success is not independent engine acceptance.
- Add bounded diagnostics to future workflow failures: fixed check name, scan status
  and non-sensitive engine version only; no file contents, tokens or provider bodies.
- Validate corrected upload/hold/download/release behavior in the in-process harness
  before preparing another exact immutable live-test image. The previous single live
  job approval was consumed. Any new app-identity job requires its own scoped approval.
- The prior live run's22 preceding checks passed; final infected-file gates were not
  reached. Full live workflow acceptance, production activation and remaining OS
  vulnerability assessment remain open. Existing695 PostgreSQL/108 Node passes
  apply to unchanged application code; they were not redundantly rerun here.

## Primary references

- [EICAR test-file specification](https://www.eicar.org/download-anti-malware-testfile/)
- [ClamAV signature formats and matching](https://docs.clamav.net/manual/Signatures.html)
