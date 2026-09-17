# Enterprise Gemma V2

Development foundation for a service from **Molecular Project Development LLC**, formerly **Superior Consultation LLC**, to integrate into [Work Zone OS](https://workzoneos.org).

## Recovery baseline

- Source: https://github.com/rbandrews2/enterprise-gemma2
- Recovered commit: `390bb2a74c1574b6294faf80388bffe1a3586e8b`
- V2 branch: `enterprise-v2`
- Local V1 preservation tag: `v1-recovery-2026-09-15`
- `main.py` passes Python syntax compilation. This does not establish runtime or cloud-service health.
- The recovered application includes `/deliver-package`, package retrieval, and email preview routes.

## Deployment hold

Do not execute `deploy.sh`, `cloudbuild.yaml`, or apply `cloudrun-service.yaml` yet. These are legacy configurations requiring review before reuse. No deployment is part of the recovery cleanup.

## First milestone

This cleanup preserves application behavior and removes tracked historical backups, bytecode, and generated outputs. Original files remain available in the V1 tag and Git history. `main.py` remains unchanged until a separately bootable V2 service skeleton is validated.

- `services/`: future application services and inference adapters.
- `shared/`: future shared contracts and configuration.
- `knowledge/`: future source inventory and curated knowledge.

Next, implement and boot the service skeleton locally, then introduce an inference interface before migrating legacy routes. Choose and verify the model/backend separately; the project name does not select a model version.

## Recovery status

`gemma-cloudrun` is a Git submodule pointer at `0a0f7f040850fbbd653e885c27cc3dfa0f3fe4af`, but the repository has no `.gitmodules` mapping. The matching source checkout has now been located in Cloud Shell and archived with its Git history. The active submodule remains unchanged while the recovered versions are compared. See [recovery inventory](docs/RECOVERY_INVENTORY.md) for validation and transfer status.

## V2 roadmap

Follow the [numbered implementation plan](docs/V2_PLAN.md). Preserve useful old material; further deletion is optional, not a requirement. The next milestones are verified recovery, version reconciliation, and a locally testable service skeleton. Production timing will be agreed with Ray after readiness is assessed.

## Product direction

Work Zone OS is the destination product; Enterprise Gemma V2 is the development project. The user leads product vision and business requirements; the assistant handles most technical implementation and design collaboratively.

The [WZOS/Gemma capability map](docs/WZOS_GEMMA_REQUIREMENTS.md) connects the website's Atlas assistant role to recovered code and adds real-image annotations, PDF/email delivery, jurisdiction-specific forms and safety sources, and verified traffic/speed inputs. These are V2 requirements, not claims of completed functionality. See the [source register](knowledge/SOURCE_REGISTER.md) for initial authoritative discovery links and remaining coverage work.
