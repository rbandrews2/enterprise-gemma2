# Restricted staging preview

Run `bash scripts/start_restricted_preview.sh` in an authorized Cloud Shell session after stopping the previous preview proxy on port 8080. It uses the existing restricted `wzos-v2-accounts` service and the installed official Cloud SDK proxy. No IAM or deployment changes are made.

The supervisor obtains an operator identity token without printing it, binds only to 127.0.0.1:8080, and restarts the proxy with a fresh token every 45 minutes. Keep its terminal running; use Cloud Shell's Web Preview on port 8080. The preview requires the authorized Google account and an active Cloud Shell session. Stop the supervisor with Ctrl+C. The current passkey origin is specific to the configured Cloud Shell hostname; a different hostname requires reviewed configuration.

October 8 validation: the old proxy returned HTML401 for both GET identities and POST logout although direct authenticated Cloud Run returned JSON200. A fresh explicit token repaired the proxy. Browser login with the approved synthetic tester succeeded and loaded Enterprise admin controls. Logout succeeded. Ray reported mobile sign-in. Shell syntax and live preview GET/POST checks passed. The 45-minute renewal interval has not yet elapsed during observation.

Remembered-cookie desktop reload did not restore the session in this Cloud Shell preview, despite successful cookie-only access in the direct server probe. Keep browser persistence and actual Android passkey enrollment/login open as release gates. Do not infer either from password sign-in success.

No passwords or token values are stored in repository files. The isolated test organization is empty; account and UI acceptance do not establish completion of other modules.

Follow-up October8: Ray reported Android session persistence across page refresh and closing/reopening the page. This accepts those Android lifecycle scenarios. Desktop reload behavior, actual Android passkey ceremonies and logout/revocation remain distinct checks.
