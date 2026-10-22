import unittest
from scripts.pin_runtime_secrets import stable_public_content


class SecretPinGuardTests(unittest.TestCase):
    def baseline(self):
        return {'version':'a'*24,'/api/identities':'auth-hash','/startup.js':'asset-hash',
                'csp':'security-hash','anonymous_session_status':401}

    def test_expected_revision_marker_change_does_not_fail_same_content(self):
        before=self.baseline();after={**before,'version':'b'*24}
        self.assertEqual(stable_public_content(before),stable_public_content(after))

    def test_auth_drift_still_fails(self):
        before=self.baseline();after={**before,'version':'b'*24,'/api/identities':'different-key'}
        self.assertNotEqual(stable_public_content(before),stable_public_content(after))

    def test_asset_and_security_drift_still_fail(self):
        before=self.baseline()
        for key in ('/startup.js','csp','anonymous_session_status'):
            self.assertNotEqual(stable_public_content(before),stable_public_content({**before,key:'changed'}))
