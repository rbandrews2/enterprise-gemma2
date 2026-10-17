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
