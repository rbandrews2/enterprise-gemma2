"""Run the verified portable local runtime without registering a Windows service."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / ".local-data/atlas-runtime"
binary = runtime / "ollama-0.34.2/ollama.exe"
if __name__ == "__main__":
    if any(os.getenv(k) for k in ("K_SERVICE", "GAE_ENV", "NETLIFY")):
        raise SystemExit("Local runtime only")
    if not binary.is_file():
        raise SystemExit("Portable runtime missing; see docs/ATLAS_LOCAL_INTELLIGENCE.md")
    env = {**os.environ, "OLLAMA_HOST": "127.0.0.1:11435", "OLLAMA_NO_CLOUD": "1",
           "OLLAMA_MODELS": str(runtime / "models"), "OLLAMA_NUM_PARALLEL": "1",
           "OLLAMA_MAX_LOADED_MODELS": "1"}
    subprocess.run([str(binary), "serve"], env=env, check=True)
