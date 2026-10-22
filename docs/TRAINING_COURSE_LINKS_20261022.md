# Numbered course video links — October 22, 2026

## Local implementation

Admins receive ten numbered HTTPS URL fields with individual Save link actions,
mapped by stable course ID to the numbered cards below. Numbers/editor are hidden
from members; saved links appear on the matching member course without requiring
assessment authoring or publishing. Clearing a field removes its course link.
New/replacement links require the existing media ownership/license attestation and
source note. Save remains available, shows progress only during its request, restores
after failure and displays actionable validation/error/success feedback inline.

The original catalog had nine courses. A tenth Organization Training course was
added; existing IDs/order and each existing course's snapshot content remain intact.
Existing authored modules/media, assessments, assignments and study records remain.
The older authored-module editor is still available under Manage training content.

Training hides the unrelated office-review alert, removes the requested study-plan
disclaimer and uses smaller card gaps/bottom padding. Other pages retain the office
alert. Weather permission/tracking configuration is unchanged.

## API and persistence

- GET `/api/training-course-videos`: authenticated, organization-scoped, catalog order.
- PUT `/api/training-course-videos/{course_id}`: admin-only, known course, expected
  version and optional validated media. Null media explicitly removes a link.
- Version checks reject stale changes; identical request retry returns the same
  saved version. Database writes to the existing module/version tables are atomic.
- Reserved `course-video-` IDs and `catalog_video` status separate these links from
  scored modules. Generic authoring, version access and assignment paths cannot use
  the reserved IDs. Payloads retain the existing full draft shape for compatibility
  with assignment/completion title queries and older readers.
- No new tables, columns, startup DDL, IAM, credentials or paid providers.

Rollback restores prior code/assets; retain link/version rows. Older learner lists
exclude `catalog_video` status. Older admin module lists can show these reserved
entries; leave them untouched during rollback. Prior unsigned/signed forms and
training assessment history are not modified.

## Validation and status

- 16 focused SQLite training-content/record tests PASS, zero skips.
- 10 focused Node training-link/player tests PASS, zero skips.
- Browser: synthetic admin sees ten fields/cards; missing attestation shows clear
  validation; valid save confirms success and puts video controls on course 1;
  member sees saved video controls without admin fields/numbers. No external video
  was fetched or played; URL is a synthetic example.test fixture.
- Browser caught a missing-title conflict in the initial link payload; repaired
  with the compatible full draft shape and regression coverage of assignment and
  completion queries after a link save.
- Local simulator: http://127.0.0.1:8081/__simulator. Existing 8083 process was left
  untouched. This local candidate has not been deployed. PostgreSQL and release
  gates remain required before a production cutover.

The historical gray Save behavior was not reproduced on the live app. The new
course-link workflow replaces that path with an explicit save and feedback; it
does not claim a verified historical cause for the original failure.
