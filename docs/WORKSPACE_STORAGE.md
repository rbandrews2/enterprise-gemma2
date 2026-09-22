# Workspace storage transition

The workspace now shares a SQLite transaction component across work orders, checklists and time clock. Existing authorization and transaction behavior is retained. This is migration groundwork, not durable Cloud Run storage.

## Operator snapshots

Run `.venv/Scripts/python.exe scripts/workspace_snapshot.py SOURCE DESTINATION` with private local paths. The source must exist and pass SQLite integrity checking; the destination must not exist. SQLite online backup produces a consistent committed snapshot, including data that may reside in a journal. Restore by running the same command from the snapshot into a new file, then verify application records before selecting that file for a stopped local app. Never replace an active database. No public backup endpoint exists.

Snapshots may contain customer or attendance data: keep them outside Git, restrict filesystem access and include them in an encrypted backup policy. A local snapshot does not survive loss of this computer unless separately backed up. This tool does not upload data.

## Next cloud increment

Choose and provision the persistent database after inspecting existing Google Cloud resources and costs. Preserve atomic clock commands, unique active shifts, command receipts, expected revisions and organization-scoped queries in the chosen adapter. Do not mount SQLite onto object storage or treat container files as durable. Add verified identity and server-managed organization membership before accepting real records. Test backup restoration and cross-organization access before enabling customers. Current restricted staging remains ephemeral and synthetic; no production migration has occurred.
