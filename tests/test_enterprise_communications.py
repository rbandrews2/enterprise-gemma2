"""Edition boundaries are enforced before provider work, independent of menu visibility."""
import os
import unittest
from uuid import uuid4
from tests import test_form_submissions as fixtures


class EnterpriseCommunicationsTests(unittest.TestCase):
    setUp = fixtures.FormSubmissionTests.setUp
    make_storage = fixtures.FormSubmissionTests.make_storage
    h = fixtures.FormSubmissionTests.h

    def test_core_roles_cannot_open_communications_or_create_notifications(self):
        for who in ('core-admin', 'core-general'):
            headers = self.h(who)
            for endpoint in ('/api/messages', '/api/meetings/config', '/api/messaging/sms/readiness', '/api/messaging/sms/outbox'):
                self.assertEqual(self.client.get(endpoint, headers=headers).status_code, 403, endpoint)
            for action in ('prepare', 'join'):
                self.assertEqual(self.client.post('/api/meetings/'+str(uuid4())+'/'+action, headers=headers).status_code, 403)
            self.assertEqual(self.client.post('/api/messages', headers=headers, json={
                'request_id':str(uuid4()), 'recipient_id':'core-general', 'text':'Synthetic test', 'sms_copy':True}).status_code, 403)
            self.assertEqual(self.client.get('/api/training', headers=headers).status_code, 200)
        modules = self.client.get('/api/admin/dashboard', headers=self.h('core-admin')).json()['modules']
        self.assertTrue({'messages', 'meetings'}.isdisjoint({module['id'] for module in modules}))


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL required')
class PostgreSQLEnterpriseCommunicationsTests(EnterpriseCommunicationsTests):
    make_storage = fixtures.PostgreSQLFormSubmissionTests.make_storage
