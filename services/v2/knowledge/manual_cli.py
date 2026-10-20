"""Operator-only page index; no model calls, uploads or applicability approvals."""
import argparse
import json
from pathlib import Path

from .manuals import ManualIndex, ManualQuery
from .store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--output', type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('rebuild')
    outline = commands.add_parser('outline')
    outline.add_argument('source')
    for action in ('search', 'context'):
        query = commands.add_parser(action)
        query.add_argument('query')
        query.add_argument('--authority', required=True)
        query.add_argument('--region', required=True)
        query.add_argument('--as-of', required=True)
        query.add_argument('--source')
        query.add_argument('--edition')
        query.add_argument('--diagrams-only', action='store_true')
    render = commands.add_parser('render')
    render.add_argument('source')
    render.add_argument('revision')
    render.add_argument('page', type=int)
    render.add_argument('destination', type=Path)
    annotation = commands.add_parser('annotate')
    annotation.add_argument('source')
    annotation.add_argument('revision')
    annotation.add_argument('page', type=int)
    annotation.add_argument('--caption', required=True)
    annotation.add_argument('--keywords', required=True)
    annotation.add_argument('--note', required=True)
    args = parser.parse_args()
    index = ManualIndex(Store(data=args.data) if args.data else Store())
    if args.command == 'rebuild':
        result = index.rebuild()
    elif args.command == 'outline':
        result = index.outline(args.source)
    elif args.command == 'render':
        result = {'path': str(index.render_page(args.source, args.revision, args.page, args.destination))}
    elif args.command == 'annotate':
        result = index.annotate_page(args.source, args.revision, args.page, args.caption, args.keywords, args.note)
    else:
        request = ManualQuery(query=args.query, authority=args.authority, region=args.region,
                              as_of=args.as_of, source_id=args.source, edition=args.edition,
                              diagrams_only=args.diagrams_only)
        result = getattr(index, args.command)(request)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(payload, encoding='utf-8')
        print('Saved', args.output)
    else:
        print(payload)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
