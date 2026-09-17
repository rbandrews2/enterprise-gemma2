# Gemma responsibilities in WZOS 2.0

Owner: Molecular Project Development LLC. Requirements baseline: 2026-09-17.
Status: requirements and source reconciliation; these capabilities are not yet implemented in V2.

## Product boundary

The [WZOS homepage](https://workzoneos.org), reviewed September 17, describes Atlas as a crew assistant for work orders, safety forms, schedules, setup, and workflow questions. Its surrounding modules cover time tracking, messaging, navigation, dispatch, training, organization roles, reporting, and integrations. Listed forms include C85, JSA, DVIR, incident, whistleblower, and company forms. The page does not explicitly describe the full imagery, document delivery, jurisdiction knowledge, and traffic-data workflow requested by Ray.

Design assumption: Gemma supplies intelligence behind Atlas and WZOS workflows. WZOS owns identity, organization membership, permissions, business records, and subscriptions. A published feature is a product requirement reference, not proof of an available integration API. Confirm API contracts during integration. Dispatch tier descriptions on the page differ; keep entitlements configurable until resolved. The site still uses the former company name; a future content update should align it with Molecular Project Development LLC.

## Capability and recovery map

| ID | V2 responsibility | Surviving implementation | Required work and acceptance evidence |
| --- | --- | --- | --- |
| WZ-01 | Help authorized crews prepare work orders, complete forms, and understand schedules | General chat and package prompts; no verified WZOS connector | Scoped read/write tools, structured drafts, user confirmation of changes, and audit records. A denied user cannot retrieve or change a job. Never report a saved record without a successful system response. |
| WZ-02 | Assist with time entries, dispatch/navigation context, messages, training, and reporting | Corridor and communication drafts in damaged recovered source | Introduce adapters incrementally. Show unavailable integrations honestly. Check permissions on every operation; require explicit authorization for outbound messages and operational changes. Restrict sensitive incident/whistleblower records by their own policy. |
| WZ-03 | Use actual work-zone imagery with editable annotations and road-work symbols | `fetch_streetview_image`, `draw_workzone_overlay`; separate Imagen generation | Accept crew photos and licensed street/aerial imagery. Preserve the original, location, capture date when known, retrieval date, provider attribution and permitted usage. Store annotations separately with normalized coordinates, symbol identity, labels, legend, author, and revision. Support work boundaries, lane closures, signs, cones/channelizers, flaggers, buffers, access, and pedestrian routes as reviewed overlays. Check correct positioning across image sizes. Label unknown dates, missing imagery, and unverified placement. Never substitute generated imagery for site evidence. |
| WZ-04 | Create useful PDF packages | `build_package_pdf` produces text-only output with old branding | Produce a versioned package with project/location, inputs, annotated real images, forms/checklists, source references, unresolved items, and review status. Verify multi-page layout, long text, legible symbols, missing images, and source links. Use current company branding. Preserve both original image and rendered derivative. |
| WZ-05 | Deliver reviewed PDFs by email | `/deliver-package` prepares preview metadata; no actual send | Add a provider adapter, authorized recipient review, durable queue, attachment/access-link policy, and provider message ID. Track prepared, approved, queued, provider-accepted, failed, and unknown outcomes; distinguish provider acceptance from confirmed delivery. Retry without duplicate sends, including an ambiguous timeout after provider acceptance. Editing recipients or package content invalidates prior approval. |
| WZ-06 | Find applicable forms and safety requirements for the project's state, locality, road authority, and date | State input defaults to VA; source-loader draft references a missing knowledge file | Resolve jurisdiction explicitly, including road ownership and local permit authority. Curate authoritative federal/state/local sources and current form templates. Record edition, effective dates, section/page, source URL, retrieval time, applicability, and review status. Identify conflicts and missing coverage. Never describe model memory as complete legal knowledge. Unsupported or unresolved requirements prevent approval of the affected package. |
| WZ-07 | Incorporate traffic volume, posted speed, and relevant site conditions | `WorkDetails.speed_limit` and `traffic_volume` are optional free text | Use typed values with units, provenance, date, road segment, direction, and verification state. Distinguish posted speed, temporary authorized speed, design speed, and observed speed. Separate annual average daily traffic, hourly/directional counts, and current conditions. Preserve truck/pedestrian/cyclist context and closure timing. Never turn an unknown value into zero or label historical counts live. |
| WZ-08 | Explain planning recommendations and identify missing information | Prompt-generated text and unvalidated JSON | Retrieve applicable sources before reasoning; cite supported requirements and label assumptions. Use tested deterministic calculations where geometry or numeric rules apply. Do not infer real-world distances from uncalibrated photo pixels. Qualified review is required for field-use layouts. Test unsupported, conflicting, and out-of-date source cases. |
| WZ-09 | Keep organizational data private and control operating cost | Shared package prefix and synchronous generation chain | Enforce organization/job ownership throughout retrieval, generation, storage, and delivery. Use durable jobs, request idempotency, bounded retries, stage reuse, and cost/latency measurements. Cache only within appropriate access and freshness boundaries. Real imagery annotation and PDF rendering should not require an image-generation call. |

## First end-to-end workflow (proposed implementation order)

1. An authenticated supervisor selects a WZOS job and confirms address/corridor, coordinates, state, locality, road authority, dates, work type, lanes, and affected road users.
2. Collect actual imagery and verified speed/traffic inputs. Show missing information instead of generating substitute facts.
3. Resolve applicable requirements and form versions, retrieve supporting passages, and list coverage gaps.
4. Generate structured draft content and editable overlays, preserving the evidence and assumptions behind them.
5. Render a branded draft PDF with annotated imagery, forms, references, and outstanding issues.
6. Record qualified review against an immutable package revision. Substantive changes require another review.
7. An authorized user approves the recipient list and delivery. Queue and record the provider result without claiming preview or acceptance means successful delivery.

This workflow is the first implementation target, not a claim that all listed WZOS modules must be rebuilt inside Gemma. Email production credentials, WZOS API contracts, pilot jurisdictions, and measurable latency/cost thresholds remain integration/product decisions. No jurisdiction receives a supported designation until its source coverage has been checked.

## Initial evaluation cases

- A supported jurisdiction, known road authority, dated real photos, verified traffic inputs, and applicable form templates produces a traceable draft.
- Missing locality, unknown speed, stale traffic counts, or unavailable imagery remains visibly incomplete; no facts are invented.
- A project spanning jurisdictions identifies each authority and conflicting requirements instead of applying the VA default.
- Photo rotation/resizing preserves annotation alignment; the original image remains unchanged. Generated illustrations are distinctly labeled.
- An expired or superseded source/form triggers revalidation for the project date; an unresolved conflict blocks field approval.
- Cross-organization read, image access, search, and email attempts are denied.
- A late PDF/storage failure resumes completed stages; an uncertain email response does not blindly resend.
- Package changes invalidate approval, and emailed assets correspond exactly to the approved revision.

## Scope of this update

Ray's requested capabilities are added to V2 requirements. This document does not edit the public website, enable outbound email, certify safety compliance, select a model, or change the preserved V1 application.
