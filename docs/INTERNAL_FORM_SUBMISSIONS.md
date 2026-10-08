# Internal form submission workflow

Scope: members submit a saved form they own; admins may submit any form in their organization. A submission preserves its saved payload/version and SHA256 hash. Later draft edits cannot change it. Same-organization admins review; members see only their submissions. Review is an internal acknowledgement, not regulatory approval. No email, SMS or MMS is sent. Attachments/external delivery remain separate launch work.

API: POST /api/form-submissions (request_id, form_id, expected_form_version), GET /api/form-submissions (bounded pagination), POST /api/form-submissions/{id}/review (expected_version,status,note). Repeated identical requests are idempotent; conflicting retries and stale versions return409.

Additive startup DDL (deployment applies migration):
```sql
CREATE TABLE IF NOT EXISTS form_submissions (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,form_id TEXT NOT NULL,form_version INTEGER NOT NULL,submitted_by TEXT NOT NULL,payload TEXT NOT NULL,payload_hash TEXT NOT NULL,status TEXT NOT NULL,version INTEGER NOT NULL,submitted_at TEXT NOT NULL,reviewed_by TEXT,reviewed_at TEXT,note TEXT NOT NULL,UNIQUE(organization_id,form_id,form_version));
```
Existing drafts are untouched. Rollback removes routes/UI and retains inert submission records. Test both databases, member/admin and organization boundaries, immutable snapshot, retries, stale edits/reviews and reload persistence before deployment.
