"""Export an allowlisted Core revision to a NEW ignored build directory.

No environment files, Git internals, backend functions or customer data are copied.
The recovery checkout is never changed. Run from the enterprise-gemma2 root.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVISION = "e5d7167bd1834a393fae8e2e19ed8b515f08c0e9"
FILES = {
    "package.json", "package-lock.json", "index.html", "vite.config.ts",
    "postcss.config.js", "tailwind.config.ts", "tsconfig.json",
    "tsconfig.app.json", "tsconfig.node.json", "components.json",
    "eslint.config.js",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="core-build-baseline")
    args = parser.parse_args()
    if not args.name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.name):
        parser.error("name must contain lowercase letters, digits, hyphen or underscore")
    source = ROOT / ".local-recovery/core-source-dev"
    destination = ROOT / ".local-recovery" / args.name
    if destination.exists():
        parser.error("destination already exists; choose a new name to preserve prior work")

    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(source), *arguments])

    paths = git("ls-tree", "-r", "--name-only", REVISION).decode().splitlines()
    selected = [p for p in paths if p in FILES or p.startswith(("src/", "public/"))]
    selected = [p for p in selected if not any(part.startswith(".env") for part in Path(p).parts)]
    destination.mkdir(parents=True)
    records = []
    for relative in selected:
        content = git("show", f"{REVISION}:{relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        records.append({"path": relative, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    # Synthetic .invalid origin cannot route to production. No provider keys supplied.
    (destination / ".env.local").write_text(
        "VITE_SUPABASE_URL=https://core-baseline.invalid\n"
        "VITE_SUPABASE_ANON_KEY=synthetic-local-baseline\n", encoding="utf-8"
    )
    (destination / "baseline-manifest.json").write_text(json.dumps({
        "source_revision": REVISION, "files": records,
        "configuration": "synthetic only; .env.local generated separately",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(records)} files to {destination}; recovery source unchanged.")


if __name__ == "__main__":
    main()
