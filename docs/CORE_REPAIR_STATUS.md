# Core local repair candidate

2026-09-20. Production and the preserved recovery baseline are unchanged.

## Implemented

- Fixed all six TypeScript errors in a separate `.local-recovery/core-repair` export. The reviewable patch is `scripts/core_typescript_repairs.patch`.
- Card refs now accept the actual anchor/button elements through a typed callback. No unsafe cast or disabled compiler check was added.
- Company Forms infers its file type from the declared Supabase client dependency, rather than importing an undeclared transitive package.
- Dashboard card metadata explicitly permits an optional `locked` flag, preserving existing behavior.
- Updated dependency versions within existing ranges. Preserved the tested package manifest and full pnpm lock under `scripts/core-repair-dependencies/`; the original source and lock remain in the recovery baseline.
- Accelerated source export using Git archive, explicitly disabling automatic CRLF conversion. Verified all 309 pre-repair file hashes against the original export; applied the repair patch successfully to a fresh export.

## Validation and limitations

- TypeScript passes before and after dependency updates.
- Production-mode Vite build passes after updates.
- Updated app renders in the isolated browser preview; `/admin` redirects a signed-out visitor to the public home. External connections remain blocked by preview-server CSP.
- Registry audit changed from 42 findings (16 high, 19 moderate, 7 low) to two moderate findings, with zero high/critical/low findings. This is dependency advisory coverage, not a complete application security assessment.
- No authenticated sessions, backend requests, payment flows, map requests or customer-data changes were tested. These checks do not establish general/admin or tenant security in production.
- Supabase inventory/backup remains blocked by Ray's reported authenticator-app problem. Continue local work using synthetic configuration; do not replace or bypass production authentication.

## Remaining dependency work

Both remaining findings concern React Router 6 and identify fixes in version 7.18.0 or later:

- [Open redirect through navigation paths](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6): inspect all dynamic navigation destinations and test a separate router upgrade.
- [SSR hydration constructor injection](https://github.com/advisories/GHSA-337j-9hxr-rhxg): the active recovered entry uses a client-rendered BrowserRouter, so an affected SSR path was not established in this inspection. Keep the advisory open until the dependency upgrade is tested; do not suppress it on that basis alone.

The two version-7 future flags already present in the recovered BrowserRouter will need review during the major upgrade. Verify direct links, back/forward, nested and parameterized routes, redirects, missing routes and authenticated guards with test identities. Broader changes from the dependency refresh also need authenticated feature regression tests before release.

## Reproduce this candidate

From the repository root:

```text
python scripts/prepare_core_baseline.py --name core-repair-check --typescript-repairs --reviewed-dependencies
cd .local-recovery/core-repair-check
pnpm install --frozen-lockfile --ignore-scripts
node node_modules/typescript/bin/tsc -p tsconfig.app.json --noEmit
pnpm run build
pnpm audit --json
```

Use Node 24.19.0 and pnpm 11.19.0 as tested. The original npm lock is retained as `baseline-package-lock.json` for provenance; pnpm is the candidate's active lock. Do not run `pnpm import` on this repaired candidate. No original environment files are copied; synthetic `.env.local` is generated. Avoid inherited production environment values.

Preview from the repository root using `python scripts/preview_core_baseline.py --name core-repair-check`. It binds to `127.0.0.1:8082` and blocks external browser requests. Stop with Ctrl+C.

## Next local milestone

Prepare the app-style Core/Enterprise shell using synthetic organizations, general/admin test identities and clearly labeled test records. Put task navigation, jobs, forms, crew operations and Atlas in the application; leave product/module explanations on `workzoneos.org`. Keep test identity handling isolated from any future production build. Integrate one saved work-order workflow before expanding the UI. Live backend parity, off-device recovery, router upgrade and production authorization remain separate completion gates.
