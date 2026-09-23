"""Start the isolated WZOS synthetic-data workspace on loopback only."""
import os
import sys
from pathlib import Path

if any(os.getenv(key) for key in ("K_SERVICE", "GAE_ENV", "NETLIFY")):
    raise SystemExit("Local preview cannot start in a cloud runtime")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--atlas", action="store_true", help="Enable the local Atlas model connection")
    parser.add_argument("--maps", action="store_true", help="Load the dedicated restricted browser key; uses authorized loopback port 8081")
    options = parser.parse_args()
    if options.maps:
        key_file = Path(__file__).resolve().parents[1] / ".local-data/credentials/wzos-v2-browser-key.txt"
        if not key_file.exists():
            raise SystemExit("Dedicated Maps browser key file is missing")
        os.environ["WZOS_GOOGLE_MAPS_BROWSER_KEY"] = key_file.read_text(encoding="utf-8-sig").strip()
    if options.atlas:
        os.environ["WZOS_ATLAS_LOCAL_MODEL"] = "1"
    os.environ["WZOS_WORKSPACE_PREVIEW"] = "1"
    import uvicorn
    uvicorn.run("services.workspace_preview.app:create_app", factory=True,
                host="127.0.0.1", port=8081 if options.maps else 8083, proxy_headers=False)
