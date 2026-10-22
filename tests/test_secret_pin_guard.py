import unittest
from scripts.pin_runtime_secrets import normalized_csp, stable_public_content


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

    def test_nonce_rotation_is_the_only_normalized_security_value(self):
        before="script-src 'nonce-Ab_12-x' 'strict-dynamic'; frame-ancestors 'none'"
        after="script-src 'nonce-Cd_34-y' 'strict-dynamic'; frame-ancestors 'none'"
        self.assertEqual(normalized_csp(before),normalized_csp(after))
        self.assertNotEqual(normalized_csp(before),normalized_csp(after+"; connect-src https://unexpected.test"))

    def test_removing_nonce_or_adding_unsafe_inline_is_not_ignored(self):
        before="script-src 'nonce-Ab_12-x' 'strict-dynamic'"
        for after in ("script-src 'strict-dynamic'",before+" 'unsafe-inline'"):
            self.assertNotEqual(normalized_csp(before),normalized_csp(after))
