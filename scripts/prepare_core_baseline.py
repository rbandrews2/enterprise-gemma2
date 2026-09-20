"""Export an allowlisted Core revision to a NEW ignored build directory.

No environment files, Git internals, backend functions or customer data are copied.
The recovery checkout is never changed. Run from the enterprise-gemma2 root.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

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
    parser.add_argument("--typescript-repairs", action="store_true", help="Apply the reviewed type-only repair patch to the new export")
    parser.add_argument("--reviewed-dependencies", action="store_true", help="Use the tested repair dependency manifest and pnpm lock")
    args = parser.parse_args()
    if not args.name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.name):
        parser.error("name must contain lowercase letters, digits, hyphen or underscore")
    source = ROOT / ".local-recovery/core-source-dev"
    destination = ROOT / ".local-recovery" / args.name
    if destination.exists():
        parser.error("destination already exists; choose a new name to preserve prior work")

    def git(*arguments):
        return subprocess.check_output(["git", "-c", "core.autocrlf=false", "-C", str(source), *arguments])

    paths = git("ls-tree", "-r", "--name-only", REVISION).decode().splitlines()
    selected = [p for p in paths if p in FILES or p.startswith(("src/", "public/"))]
    selected = [p for p in selected if not any(part.startswith(".env") for part in Path(p).parts)]
    destination.mkdir(parents=True)
    records = []
    archive = git("archive", "--format=tar", REVISION, "src", "public", *sorted(FILES))
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        for relative in selected:
            member = bundle.getmember(relative)
            if not member.isfile():
                raise ValueError(f"Refusing non-file source entry: {relative}")
            content = bundle.extractfile(member).read()
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
    if args.typescript_repairs:
        patch = ROOT / "scripts/core_typescript_repairs.patch"
        command = ["git", "apply", f"--directory=.local-recovery/{args.name}", str(patch)]
        subprocess.run(command[:2] + ["--check"] + command[2:], cwd=ROOT, check=True)
        subprocess.run(command, cwd=ROOT, check=True)
        (destination / "repair-manifest.json").write_text(json.dumps({
            "patch": patch.name,
            "sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
            "baseline_manifest": "baseline-manifest.json contains pre-repair hashes",
        }, indent=2) + "\n", encoding="utf-8")
    if args.reviewed_dependencies:
        dependencies = ROOT / "scripts/core-repair-dependencies"
        for filename in ("package.json", "pnpm-lock.yaml"):
            (destination / filename).write_bytes((dependencies / filename).read_bytes())
        # Keep the original npm lock for provenance, not as a competing active lock.
        (destination / "package-lock.json").rename(destination / "baseline-package-lock.json")
    print(f"Exported {len(records)} files to {destination}; recovery source unchanged.")


if __name__ == "__main__":
    main()
