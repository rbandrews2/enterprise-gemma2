## SMS challenge stability repair - October17 candidate

User reports delayed texts and both entered codes rejected. Live safe outbox history
shows successive requests at 00:25,00:26,00:33,00:42 Eastern; earlier messages were
reported delivered while the later challenge was sending. This establishes an
out-of-order/replacement hazard, not proof that every mismatch was caused by it.

Candidate preserves the currently sent challenge for the same phone until its
original ten-minute expiry or five-attempt lockout. Repeated requests return that
challenge's status without another send, hash change or daily-limit increment.
Different phone, expired, failed/blocked or locked challenge can request a new code.
UI shows request label, original request time and expiry; future SMS includes the
same non-secret label. Pending valid challenge disables same-number replacement.
Expiry and incorrect-attempt lockout now have distinct errors. No verification
bypass, longer TTL, extra attempts, new DDL, permissions or provider changes.

19 focused local SMS tests PASS in32.338s; JS syntax/diff checks PASS. New regression
proves repeated request cannot invalidate a sent code and that original verifies.
Focused PostgreSQL gate queued next: overlap, expiry/retry/daily-limit and account
access. Release helper rebased onto live image454a9747, office-6caf8ee rollback;
exclude test venv from Cloud Build upload. Device acceptance remains open.

## LIVE SMS challenge repair - October17

Candidate8d09c4a6fa59c600eddba9c2a95f1ed66b819491 deployed successfully to
wzos-v2-accounts-office-8d09c4a,100% traffic; release exit0 and fourteen public
asset hashes/version check PASS. Immutable image
sha256:6a2312b6ca77f675398a5858621e08e0b87e7dfd878495bc25ce01b6f950a83d.
Cloud Build078099e3-279a-4971-8f88-97752c668566 SUCCESS. Staged configuration
preserved. No owned temporary PostgreSQL cluster running. Rollbackoffice-6caf8ee.
8 focused PostgreSQL tests PASS/no skips in5.459s;19 local SMS tests PASS.

User confirmed all earlier texts eventually arrived, but entered codes were expired
or mismatched. Latest code arrived; user explicitly will not request any more.
Respect that: no more codes requested, no consent entry or verification bypass.
Do not label phone verification complete. Repair prevents overlapping active codes
and adds matching request labels/time/expiry; real fresh-code acceptance remains
pending until user voluntarily resumes. Sending remains controlled test mode.
