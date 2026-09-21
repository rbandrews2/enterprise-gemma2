"""Start the isolated WZOS synthetic-data workspace on loopback only."""
import os
import sys
from pathlib import Path

if any(os.getenv(key) for key in ("K_SERVICE", "GAE_ENV", "NETLIFY")):
    raise SystemExit("Local preview cannot start in a cloud runtime")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    os.environ["WZOS_WORKSPACE_PREVIEW"] = "1"
    import uvicorn
    uvicorn.run("services.workspace_preview.app:create_app", factory=True,
                host="127.0.0.1", port=8083, proxy_headers=False)
