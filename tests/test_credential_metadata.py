import unittest
from scripts.audit_credential_metadata import audit


class CredentialMetadataTests(unittest.TestCase):
    def test_only_metadata_queries_and_explicit_missing_status(self):
        calls = []
        def query(*args):
            calls.append(args)
            return ["wzos-v2-staging-database-url"] if args[1] == "list" else ["ENABLED"]
        result = audit(query)
        self.assertTrue(result["metadata_verified"])
        self.assertFalse(result["secret_values_read"])
        self.assertEqual(result["items"]["database"]["status"], "enabled_version_present")
        self.assertEqual(result["items"]["authentication_web_config"]["status"], "missing")
        self.assertTrue(all("access" not in call for call in calls))

    def test_failure_does_not_expose_provider_error_or_claim_missing(self):
        def query(*args):
            raise RuntimeError("sensitive provider detail")
        result = audit(query)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["items"], {})
        self.assertNotIn("sensitive", str(result))

    def test_gcloud_lowercase_state_and_disabled_versions(self):
        for state, expected in [('enabled', 'enabled_version_present'), (' ENABLED ', 'enabled_version_present'), ('disabled', 'no_enabled_version'), ('destroyed', 'no_enabled_version')]:
            with self.subTest(state=state):
                def query(*args):
                    return ['wzos-v2-staging-database-url'] if args[1]=='list' else [state]
                self.assertEqual(audit(query)['items']['database']['status'],expected)
