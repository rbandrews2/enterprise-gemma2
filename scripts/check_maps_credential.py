"""Run in authenticated Cloud Shell. Read-only; never prints credentials/errors."""
import base64
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request


def main():
    token = subprocess.run(["gcloud", "auth", "print-access-token"],
                           capture_output=True, text=True, timeout=45)
    if token.returncode:
        print("Credential check: Cloud Shell authentication unavailable")
        return
    headers = {"Authorization": "Bearer " + token.stdout.strip()}

    def get(url):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            print("Credential check HTTP status:", urllib.parse.urlsplit(url).hostname, error.code)
            details = json.load(error).get("error", {})
            print("Error status:", details.get("status"))
            print("Error reasons:", [d.get("reason") for d in details.get("details", []) if d.get("reason")])
            return None

    secret = get("https://secretmanager.googleapis.com/v1/projects/enterprise-gemma2/secrets/GOOGLE_MAPS_API_KEY/versions/latest:access")
    if secret is None:
        return
    value = base64.b64decode(secret["payload"]["data"]).decode().strip()
    if not re.fullmatch(r"AIza[A-Za-z0-9_-]{35}", value):
        print("Stored secret does not match the expected API-key format; value withheld.")
        return
    lookup = get("https://apikeys.googleapis.com/v2/keys:lookupKey?" + urllib.parse.urlencode({"keyString": value}))
    if lookup is None:
        return
    name = lookup.get("name", "")
    if not re.fullmatch(r"projects/[0-9]+/locations/global/keys/[A-Za-z0-9-]+", name):
        print("Key lookup did not return a recognized resource name.")
        return
    print(json.dumps({"key_resource": name, "parent": lookup.get("parent")}, indent=2))
    metadata = get("https://apikeys.googleapis.com/v2/" + name)
    if metadata is not None:
        print(json.dumps({k: metadata.get(k) for k in ("displayName", "restrictions", "deleteTime")}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Network errors can contain URLs with credentials; never echo exceptions.
        print("Credential check could not finish; no credential or raw error was printed.")
