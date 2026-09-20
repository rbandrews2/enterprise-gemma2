# Placement rule foundation

Atlas preparation now returns `placement_readiness`, tied to the response's project revision/hash. Policy version `placement-readiness-1` identifies missing inputs, reported but unverified values, and review requirements. The workspace displays these checks. This is WZOS readiness policy, not an agency requirements determination.

Coordinates, authority, date, speed, closure, work limits, width, direction, duration, sight distance, pedestrians and intersections are checked separately. Zero sight distance is a supplied value requiring review, never a passing engineering result. References are counted as candidates only. Customer claims and keyword matches cannot activate placement generation. No approved rules or generated placements exist yet.

## Next rule implementation contract

Each reviewed rule must carry an immutable rule ID/version, source ID and SHA-256 document revision, edition, PDF page and printed page/section/table/figure, official URL, extraction verification, reviewer identity/date, applicability conditions and exclusions. Pin numeric inputs, units, outputs, rounding, table bounds and exceptional cases. Preserve the exact input/project revision and rule/source versions with each future recommendation.

Start with one explicitly scoped stationary closure scenario after reviewing the official typical application and every referenced note/table. Do not infer a rule from extracted text alone. Require measured approach paths with direction, lane boundaries and obstructions before converting longitudinal distances to coordinates. Work-limit lines do not provide that geometry. Test each table boundary, unsupported scenario, superseded revision and missing evidence before enabling any rule. Flagger stations require their own visibility/site review; they are not generic points at a fixed distance.

## Source check

On 2026-09-20, [VDOT's publication page](https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/) identified VWAPM version 11.0 (January 2026) and described exceptions for earlier contracts/permits. Its field guide is an informal companion. This check does not establish applicability to a Norfolk road or approve an edition for a specific project.

No new agency spacing values, model calls, cloud changes or field-use approvals are introduced in this increment.

## First reference-table implementation — 2026-09-20

`POST /v2/placement/reference-preview` accepts `scenario: stationary_shoulder`, a reported `road_class` (`conventional`, `undivided`, `divided_non_limited`, `limited_access`) and numeric `posted_speed_mph`. It returns the recommended A-spacing range from Table 6P-V3 and the exact buffer row from Table 6P-V4. This endpoint is behind the existing local-only boundary and makes no external calls. It does not save or modify a project. Example request:

```json
{"scenario":"stationary_shoulder","road_class":"conventional","posted_speed_mph":35}
```

Source: January 2026 VWAPM, SHA-256 `f16aa1782e85c4b1237823eb8fbaafdf06128f3cc8d2c17c16fb696b92415274`, PDF page 157 / printed page 147. Codex visually checked rendered tables and shoulder notes/diagram on PDF pages 166–167 / printed pages 156–157. Original bytes match the pinned hash. This is a technical transcription check, not qualified engineering approval. Publication and known-error links were checked live on 2026-09-20; the live manual exceeded the web reader's size limit, so visual inspection used the preserved revision.

### Source issue prevents complete layout implementation

Figure TTC-4.0 is visibly marked **Known Error (VDOT)**. Its references to notes 1c and 1f do not match the accompanying notes page. The current official known-errors list also calls for removing the note 1c reference (its printed-page reference differs from the inspected manual). These inconsistencies are recorded, not silently repaired. The figure/notes also differ in sign depictions. No sign sequence, taper, vehicle position, flagger placement or geographic coordinate is generated from this figure.

The preview returns `reference_only`, or `unsupported_table_input` where a table has no supported row. Individual unavailable values are null; buffer values are never interpolated/extrapolated. It retains the A range rather than selecting a midpoint. Reported road classes are explicit inputs, not inferred from a locality. Non-limited-access classes use the conventional-road rows at lower speeds. All results include source revision, page citations, limitations and `approved_for_field_use: false`. No claim is made that this pinned source is the current applicable revision.

Validation: all 81 tests passed, including spacing boundaries, road classes, all buffer rows, unsupported inputs, request validation and remote rejection. A real loopback HTTP request returned the cited preview. This backend increment does not yet add a workspace preview control. Next: resolve the TTC-4 source discrepancies and collect measured approach geometry before enabling any sign-layout calculation; connect reference previews to explicit scenario selection in the workspace.
