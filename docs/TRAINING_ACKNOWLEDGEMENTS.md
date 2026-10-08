# Training acknowledgements and admin review

Members record their own completed study, date, duration and material reference against a hash-bound course-catalog snapshot. Admins can review organization records and request follow-up. The existing catalog remains content_review_pending; an acknowledgement is self-reported, not proof of viewing, assessment, accreditation or a qualification. No certificate or automatic dispatch eligibility is created. Playable authorized course media and assessments remain launch work.

POST /api/training-records; GET /api/training-records/catalog; GET /api/training-records; POST /api/training-records/{id}/review. Pagination <=50, immutable submitted content, UUID retry protection, stale review/catalog conflicts, organization isolation and admin-only reviews.

Additive startup DDL (deployment applies migration):
```sql
CREATE TABLE IF NOT EXISTS training_records (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,user_id TEXT NOT NULL,course_id TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,version INTEGER NOT NULL,submitted_at TEXT NOT NULL,reviewed_by TEXT,reviewed_at TEXT,note TEXT NOT NULL);
```
Rollback removes routes/UI, preserving inert acknowledgements. No existing qualifications or study plans changed. PostgreSQL, browser, role boundaries and review/retry checks required before cloud deployment.

Validation October8: full Python337 (270passed,67PostgreSQL skips); Node21passed. Local browser member submit, admin review, member sees note and other organization sees zero records passed. Synthetic screenshot .local-data/training-review-proof.png; PostgreSQL and cloud acceptance remain open.
