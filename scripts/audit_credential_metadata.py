"""Read Secret Manager metadata only; never read or print secret payloads."""
import json
import subprocess

PROJECT = "enterprise-gemma2"
EXPECTED = {
    "database": "wzos-v2-staging-database-url",
    "authentication_web_config": "wzos-v2-staging-auth-web-key",
}


def gcloud(*args):
    result = subprocess.run(["gcloud", *args, "--project=" + PROJECT, "--quiet"],
                            capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise RuntimeError("Metadata query unavailable")
    return result.stdout.splitlines()


def audit(query=gcloud):
    report = {"project": PROJECT, "manager": "Google Secret Manager",
              "metadata_verified": False, "secret_values_read": False, "items": {}}
    try:
        names = {n.strip().rsplit("/", 1)[-1] for n in query("secrets", "list", "--format=value(name)")}
    except (RuntimeError, OSError, subprocess.TimeoutExpired):
        report["status"] = "unavailable"
        return report
    report["metadata_verified"] = True
    for purpose, name in EXPECTED.items():
        status = "missing"
        if name in names:
            try:
                states = query("secrets", "versions", "list", name, "--format=value(state)")
                status = "enabled_version_present" if "ENABLED" in states else "no_enabled_version"
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                status = "version_metadata_unavailable"
        report["items"][purpose] = {"secret_name": name, "status": status}
    report["status"] = "metadata_checked"
    report["integration_configuration_unverified"] = [
        "Maps browser key restrictions and current origins", "Twilio account/sender credentials",
        "Email provider and verified sender", "Video meeting provider and OAuth configuration",
        "Runtime service-account access and secret injection"]
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["metadata_verified"] else 2)
