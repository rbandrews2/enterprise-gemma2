"""Run with python -m services.v2.knowledge.cli; one operator at a time."""
import argparse
import json
from .store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("source", help="Catalog source ID or all")
    commands.add_parser("rebuild")
    retry = commands.add_parser("retry-extraction")
    retry.add_argument("source")
    retry.add_argument("revision")
    check = commands.add_parser("check-extraction")
    check.add_argument("source")
    check.add_argument("revision")
    check.add_argument("--note", required=True)
    args = parser.parse_args()
    store = Store()
    if args.command == "ingest":
        ids = list(store.catalog) if args.source == "all" else [args.source]
        if any(source_id not in store.catalog for source_id in ids):
            parser.error("Source must be in the approved catalog")
        results = {source_id: store.ingest(source_id) for source_id in ids}
        print(json.dumps(results, indent=2), flush=True)
        print(json.dumps({"indexed_passages": store.rebuild()}))
        return int(any(result["status"] in {"unavailable", "failed", "needs_review"} for result in results.values()))
    if args.command == "check-extraction":
        store.check_extraction(args.source, args.revision, args.note)
    if args.command == "retry-extraction":
        store.retry_extraction(args.source, args.revision)
    print(json.dumps({"indexed_passages": store.rebuild()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
