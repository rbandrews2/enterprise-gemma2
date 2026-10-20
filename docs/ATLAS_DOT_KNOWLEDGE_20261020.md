# Atlas DOT knowledge base - implementation plan and contract

## Product direction

Latest direction supersedes the earlier diagram/report proposal: highlight
Smart Field Voice and Ask Atlas - Work Zone Guardian as separate Enterprise
features. Gemma reasons over complete source context, with citations, conditions,
clarifications and reviewed formula arithmetic. Guidance is not attached to Voice
reports in this release; maps/navigation is separate. Retire the visible legacy
report builder while preserving read-only historical reports/PDFs.

See ASK_ATLAS_ENTERPRISE_20261020.md for the current implementation, seven-source
library, page/OCR/correction review controls, APIs, activation and rollback.
The remainder of this file records the earlier foundation increment and evidence;
its older proposed report workflow is historical, not the current product scope.

## Actual supplied documents

- Virginia MUTCD v11.0 January2026:1006 physical pages, SHA256
  7d6277e9a3fdf0d5798b087025b340288663fbc2b6a812e306dc85602a43ae58.
  Drive13fRCTI7tMTEVReNszwEXH2Hfh76ENReu. Introduction physicalp3 explains that
  temporary traffic control Part6 is the separate VWAPM. Authority/contract/local
  adoption and amendments still matter. Official VDOT download has different bytes;
  the supplied copy must retain user-import provenance, not be silently substituted.
- Pavement Markings:49 pages; p2 identifies a November18,2019 Thornburg training
  presentation. SHA2565c6bbed42a753cc03d338fe30e1ba4efa2697d17a3e52a0aa4f7f9316dcf22e0.
  Drive1KiJYduRaieZWVr-N8QzSLFKvWfsrIm4a. Training, not a current specification.
- Existing official library already catalogs VWAPM, federal MUTCD, VDOT pavement
  specifications/amendments. Reuse them with their actual review/currency status.
  NCDOT/Caltrans content is not supplied or represented as available.

Ray first narrowed work to MUTCD while finding pavement material, then supplied:

| Source | Physical pages | Edition/scope |
| --- | ---: | --- |
| Road and Bridge Standards Volume II |374|2016 base edition; June2026 updates present; PM-series in Section1300 |
| Traffic Engineering Design Manual |163|April2020, Revision1 March2023; some cross-references predate2026 MUTCD |
| Road and Bridge Standards Volume I |574|2016 base edition; preserve individual sheet revision dates |

These three are separately hash-pinned in sources.json with original Drive URLs,
official publication pages, actual editions and unknown copy currency. User-import
status is explicit; the official-source downloader still rejects Drive origins.
The2019 presentation remains held and is not ingested into the new library.

## Architecture

1. Extend existing Source/Store and operator CLI, not application authentication or
   customer persistence. Import only catalog-pinned PDFs; preserve SHA256 originals,
   Drive provenance, edition, document role, region and unreviewed status. User
   imports do not expand the official downloader's network allowlist.
2. PDFium (already pinned) extracts every physical page with original line breaks,
   page labels, section/figure/table caption candidates and explicit text gaps.
   SQLite FTS5 (already available) is a rebuildable page-search index in the same
   ignored source-library directory. No new provider, package or customer-table DDL.
3. Search requires authority, region, project date and optional source/edition.
   Literal safe queries, a small reviewed synonym vocabulary, immutable revision
   citations, pagination and full page/neighbor references. Never substitute another
   state's manual or training slides for missing governing material.
4. Build a bounded context from complete matching pages and adjacent notes, without
   clipping a table/page to meet the budget. Unreviewed, unknown-currency, imported,
   historical-training or out-of-date evidence stays discoverable but cannot enable
   an authoritative model answer. Sparse/image-only pages need OCR/manual review;
   no automatic OCR, table interpretation or blanket extraction approval.
5. A separate structured Gemma adapter reuses Google metadata ID-token auth and the
   approved private service. One call, no paid retries/fallbacks/tools, bounded body
   and timeout. Validate citation IDs and exact supporting quotes; validation cannot
   prove engineering correctness or semantic entailment. Always preserve qualified
   review and unresolved details. Ordinary Atlas chat/Field Voice remain unchanged.
6. Enterprise authenticated read-only search/context and ask routes behind an OFF
   feature flag. All requests use the existing actor/organization boundary. This
   increment does not grant permissions, turn on ordinary Atlas, change hosting,
   record audio, send reports/SMS, deploy, or replace report/PDF presentation.

## Context and figures

Google documents256K for31B, but checked repository hosting uses max-model-len32767
and ordinary chat has a16000-character guard. Do not raise GPU/context settings here.
Use conservative byte budgets and retrieved complete pages. Full-manual indexing
means all topics can be found; it does not mean every page was visually validated.

Figure matching is deterministic text discovery of printed caption candidates,
with a link to the original page. A candidate is not a reconstructed diagram or a
verified match. Opening neighboring pages preserves figure notes and table context.
An image-render helper can render the exact pinned PDF page for local review;
no LLM-generated drawings or diagram dimensions are accepted.

## Validation and rollout

Focused tests: hash-pinned import, wrong authority/date/edition, training/unreviewed
exclusion, complete-page budgets, injection/literal FTS, page/quote/citation integrity,
tampering/stale index, image-only gaps, disabled/Core/anonymous denial and provider
no-call paths. Index the four supplied manuals locally; keep originals/indexes ignored. No paid
inference or production changes in this task. Full PostgreSQL/Node release gates,
domain expert content/diagram review, source currency review and bounded live model
acceptance precede a separately authorized public activation.

Next report integration: ask for road layout/work type/closure/speed/lane width,
authority and contract date; show missing facts and multiple candidate diagrams;
save preparer's selections and exact revision/pages with the report; include citations
and links in PDF; invalidate stale preparation when job/source basis changes.
Do not delete historical report snapshots or silently rewrite saved evidence.

VDOT's Road and Bridge Standards page permits complete-manual download/printing but
prohibits insertion or modification of Standard Drawings in plan assemblies. TEDM's
publication page restricts sale/distribution for profit. Original-page previews are
for review, not permission to redistribute drawings in commercial WZOS reports.
Prefer exact sheet/edition/page citations and official links; obtain appropriate
reuse rights before adding embedded drawings or paid redistribution. Do not imply
that a2016 base edition is obsolete solely from its title: published individual
sheet/revision letters control; the current VDOT page lists June2026 revisions.

## Implemented local workflow

Existing Python dependencies suffice: PDFium, Pydantic, FastAPI, httpx and SQLite
FTS5. No vector database, external embedding API or large new framework required.

```powershell
python -m services.v2.knowledge.cli import-pdf vdot-mutcd-user-20261020 PATH_TO_MUTCD.pdf
python -m services.v2.knowledge.cli import-pdf vdot-rb-vol2-user-20261020 PATH_TO_VOLUME_II.pdf
python -m services.v2.knowledge.cli import-pdf vdot-tedm-user-20261020 PATH_TO_TEDM.pdf
python -m services.v2.knowledge.cli import-pdf vdot-rb-vol1-user-20261020 PATH_TO_VOLUME_I.pdf
python -m services.v2.knowledge.manual_cli rebuild
python -m services.v2.knowledge.manual_cli search "double yellow centerline" --authority VDOT --region VA --as-of 2026-10-20 --diagrams-only
python -m services.v2.knowledge.manual_cli context "centerline markings" --authority VDOT --region VA --as-of 2026-10-20
python -m services.v2.knowledge.manual_cli outline vdot-mutcd-user-20261020
```

`manual_cli --output FILE ...` writes results as UTF-8; `--data DIRECTORY` selects
an operator library. `render SOURCE SHA256 PHYSICAL_PAGE NEW_PNG` previews one full
verified original page without overwriting an existing output. Search excludes
contents-list caption entries, distinguishes Figures/standard sheets from Tables,
and can discover diagram pages using adjacent explanatory text. Partial keyword
matches are labeled and cannot trigger inference. Source changes invalidate the
derived index; rebuild and snapshot packaging verify original/index hashes.

Authenticated Enterprise routes (default OFF):

- POST `/api/atlas/dot/search` (ManualQuery JSON)
- POST `/api/atlas/dot/context`
- POST `/api/atlas/dot/ask`
- GET `/api/atlas/dot/sources/{source_id}/outline`

ManualQuery requires query/authority/region/as_of; optional source_id/edition,
diagrams_only, limit/offset. Authority filtering never silently falls back to
another state or federal sources. User imports/unknown currency/training/unchecked
extraction stay discoverable but cannot enable a model answer. Existing source
metadata changes cannot relabel an older PDF as a newer edition.

`WZOS_ATLAS_DOT_ENABLED=1` enables reference routes; separate
`WZOS_ATLAS_DOT_INFERENCE_ENABLED=1` permits the reviewed-evidence model path.
The operator-configured `WZOS_ATLAS_DOT_MODEL_URL` can reuse the private Voice model
origin; fallback is only the existing configured WZOS_FIELD_VOICE_MODEL_URL, never
a user URL/provider. These flags remain OFF; no live configuration was changed.
Ordinary Atlas/Voice transports, weather and saved report schema are unchanged.

Rollback disables the new feature flag and removes the derived manual index if
necessary; original source revisions and already saved reports remain intact.

## Local results - October20

- Imported all four supplied manuals using exact catalog hashes. Full legacy
  extraction3361 passages; page index2117 physical pages. The2019 training file
  remains outside ingestion. No general "all pages reviewed" flag was set.
- MUTCD1006pages/136 low-body-text pages; Road and Bridge VolumeI574/11;
  VolumeII374/7; TEDM163/0. These154 pages include image-heavy and blank material,
  not154 independently confirmed defects. Header/footer-only pages are flagged.
- Found and fixed contents-list false matches, hyphenated standard-code splitting,
  page/edition relabeling risk and image-only diagrams mistaken for usable body text.
  Direct/caption matches precede adjacent-page candidates. Partial matches require
  clarification. PM-1 now prioritizes VolumeII physicalp315 (standard sheet1330.10,
  June2022 revision visible); never silently transfer another PM-series sheet.
- Visually inspected full original MUTCDp621 (printed585):Figure3B-2, Yellow Center
  Lines for Four-or-More Lane, Two-Way Applications. Recorded a revision-bound
  operator search tag with an AI-assisted review note. This is not extracted rule
  text, OCR, source approval or a divided-highway lane-closure recommendation.
  Image-only pages still block model answering; source search/review remains usable.
- 42 focused tests PASS in20.053seconds, including existing source ingest/package
  and Atlas reference-selection regressions; no paid inference or provider traffic.
  Test/model input/output was synthetic. Python syntax and Git diff checks PASS.
- Workspace factory smoke check confirms the new routes are registered and return
  anonymous401, Core403 and disabled Enterprise503 before any model invocation.
- New API is registered in the workspace but OFF. Full PostgreSQL/Node deployment
  gates, real model acceptance, source/currency/reuse-rights review, user-facing
  Ask Atlas wiring and saved-report citation selection remain rollout work.
  Live app remains ui-6047e5b; Voice/weather/model resources unchanged.

Ignored local artifacts: `.local-data/knowledge/` (originals/manifests/indexes),
`.local-data/dot-manuals/` (coverage/search results, original-page previews and
focused-tests.log). Preserve originals, page-annotations.json and manifests together;
SQLite alone is not a backup. New page tags use `manual_cli annotate SOURCE SHA256
PAGE --caption ... --keywords ... --note ...`; existing tags cannot be silently
overwritten, and any annotation change requires a derived-index rebuild.

## Primary references inspected

- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/virginia-mutcd/
- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/
- https://ai.google.dev/gemma/docs/core/model_card_4
- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/road-and-bridge-standards/
- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/traffic-engineering-design-manual/
- User-supplied Drive files listed above; do not publish authenticated download URLs.
