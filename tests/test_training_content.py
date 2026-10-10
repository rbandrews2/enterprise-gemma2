import os, unittest
from datetime import date, timedelta
from uuid import uuid4
from tests import test_form_submissions as fixtures


def module(**change):
    return {'expected_version': 0, 'title': 'Flagger refresher (organization)', 'summary': 'Our crew flagging procedure.',
            'sections': [{'heading': 'Stop/slow paddle', 'body': 'Hold the paddle at shoulder height...'}],
            'media': [{'title': 'Crew video', 'url': 'https://video.example.test/flagging', 'rights_confirmed': True, 'rights_note': 'Recorded by our own crew in 2026'}],
            'questions': [{'prompt': 'Paddle height?', 'options': ['Waist', 'Shoulder'], 'answer': 1},
                          {'prompt': 'Face traffic?', 'options': ['Yes', 'No'], 'answer': 0}],
            'passing_score': 100, 'max_attempts': 2, **change}


class TrainingContentTests(unittest.TestCase):
    setUp = fixtures.FormSubmissionTests.setUp
    make_storage = fixtures.FormSubmissionTests.make_storage
    h = fixtures.FormSubmissionTests.h

    def save(self, who='enterprise-admin', module_id='flagger', **change):
        return self.client.put('/api/training-modules/' + module_id, headers=self.h(who), json=module(**change))

    def publish(self, version=1, module_id='flagger'):
        return self.client.post(f'/api/training-modules/{module_id}/publish', headers=self.h('enterprise-admin'), json={'expected_version': version})

    def attempt(self, answers, version=1, who='enterprise-general', request_id=None):
        return self.client.post('/api/training-modules/flagger/attempts', headers=self.h(who), json={'request_id': request_id or str(uuid4()), 'module_version': version, 'answers': answers})

    def ready(self):
        self.assertEqual(self.save().status_code, 200); self.assertEqual(self.publish().status_code, 200)

    def test_only_admins_author_and_media_rights_are_required(self):
        self.assertEqual(self.save('enterprise-general').status_code, 403)
        self.assertEqual(self.save(media=[{'title': 'Clip', 'url': 'https://x.test/v', 'rights_confirmed': False, 'rights_note': 'Found online'}]).status_code, 422)
        self.assertEqual(self.save(media=[{'title': 'Clip', 'url': 'http://x.test/v', 'rights_confirmed': True, 'rights_note': 'Our video'}]).status_code, 422)
        self.assertEqual(self.save(questions=[{'prompt': 'Bad?', 'options': ['A', 'A'], 'answer': 0}]).status_code, 422)
        self.assertEqual(self.save(questions=[{'prompt': 'Bad?', 'options': ['A', 'B'], 'answer': 2}]).status_code, 422)
        self.assertEqual(self.save(module_id='Bad Id').status_code, 422)
        self.assertEqual(self.save().json()['draft_version'], 1); self.assertEqual(self.save().json()['draft_version'], 1)
        self.assertEqual(self.save(title='Changed title').status_code, 409)

    def test_publishing_requires_content_and_questions_and_versions_are_immutable(self):
        self.save(questions=[])
        self.assertEqual(self.publish().status_code, 422)
        self.save(expected_version=1)
        self.assertEqual(self.publish(1).status_code, 409)
        self.assertEqual(self.publish(2).json()['published_version'], 1)
        self.assertEqual(self.publish(2).json()['published_version'], 1)
        self.save(expected_version=2, title='Flagger refresher v2')
        v1 = self.client.get('/api/training-modules/flagger/versions/1', headers=self.h()).json()
        self.assertEqual(v1['title'], 'Flagger refresher (organization)')

    def test_members_see_published_content_without_answers_or_other_organizations(self):
        self.save()
        self.assertEqual(self.client.get('/api/training-modules', headers=self.h()).json()['items'], [])
        self.publish()
        item = self.client.get('/api/training-modules', headers=self.h()).json()['items'][0]
        self.assertNotIn('answer', str(item['questions'])); self.assertFalse(item['certificate_issued']); self.assertFalse(item['qualification_issued'])
        self.assertEqual(item['media'][0]['rights_note'], 'Recorded by our own crew in 2026')
        self.assertEqual(self.client.get('/api/training-modules', headers=self.h('core-general')).json()['items'], [])
        self.assertEqual(self.client.get('/api/training-modules/flagger/versions/1', headers=self.h('core-admin')).status_code, 404)

    def test_scored_attempts_record_completion_separately_from_study_and_qualifications(self):
        self.ready()
        assigned = self.client.post('/api/training-assignments', headers=self.h('enterprise-admin'), json={'module_id': 'flagger', 'user_ids': ['enterprise-general'], 'due_on': (date.today() + timedelta(days=7)).isoformat()})
        self.assertEqual(assigned.status_code, 200, assigned.text)
        self.assertEqual(self.attempt([1]).status_code, 422)
        failed = self.attempt([0, 0]).json(); self.assertEqual((failed['score'], failed['passed'], failed['record_type']), (50, False, 'assessment_attempt'))
        self.assertNotIn('answer', failed)
        request_id = str(uuid4())
        passed = self.attempt([1, 0], request_id=request_id).json()
        self.assertEqual((passed['score'], passed['passed'], passed['record_type'], passed['attempts_used']), (100, True, 'assessment_completion', 2))
        self.assertFalse(passed['qualification_issued']); self.assertFalse(passed['certificate_issued'])
        self.assertEqual(self.attempt([1, 0], request_id=request_id).json(), passed)
        self.assertEqual(self.attempt([1, 0]).status_code, 409)
        mine = self.client.get('/api/training-assignments', headers=self.h()).json()['items'][0]
        self.assertEqual((mine['status'], mine['attempts']), ('completed', 2))
        completions = self.client.get('/api/training-completions', headers=self.h('enterprise-admin')).json()['items']
        self.assertEqual(len(completions), 1); self.assertEqual(completions[0]['record_type'], 'assessment_completion')
        self.assertEqual(self.client.get('/api/training-completions', headers=self.h('core-admin')).json()['items'], [])
        # Self-reported study records are untouched by assessment completion.
        self.assertEqual(self.client.get('/api/training-records', headers=self.h('enterprise-admin')).json()['total'], 0)

    def test_attempt_limits_retry_conflicts_and_version_changes(self):
        self.ready()
        rid = str(uuid4())
        self.attempt([0, 1], request_id=rid)
        self.assertEqual(self.attempt([1, 1], request_id=rid).status_code, 409)
        self.attempt([0, 1])
        self.assertEqual(self.attempt([1, 0]).status_code, 409)
        self.save(expected_version=1, title='Updated procedure'); self.publish(2)
        self.assertEqual(self.attempt([1, 0], version=1).status_code, 409)
        self.assertTrue(self.attempt([1, 0], version=2).json()['passed'])

    def test_assignments_are_admin_only_and_organization_scoped(self):
        self.save()
        body = {'module_id': 'flagger', 'user_ids': ['enterprise-general']}
        self.assertEqual(self.client.post('/api/training-assignments', headers=self.h('enterprise-admin'), json=body).status_code, 409)
        self.publish()
        self.assertEqual(self.client.post('/api/training-assignments', headers=self.h(), json=body).status_code, 403)
        self.assertEqual(self.client.post('/api/training-assignments', headers=self.h('enterprise-admin'), json={**body, 'user_ids': ['core-general']}).status_code, 422)
        first = self.client.post('/api/training-assignments', headers=self.h('enterprise-admin'), json=body).json()['items'][0]
        self.assertEqual(self.client.post('/api/training-assignments', headers=self.h('enterprise-admin'), json=body).json()['items'][0]['id'], first['id'])
        self.assertEqual(self.client.post(f"/api/training-assignments/{first['id']}/cancel", headers=self.h('core-admin')).status_code, 404)
        self.assertEqual(self.client.post(f"/api/training-assignments/{first['id']}/cancel", headers=self.h('enterprise-admin')).json()['status'], 'cancelled')
        self.assertEqual(self.client.get('/api/training-assignments', headers=self.h('core-general')).json()['items'], [])
        self.client.post('/api/training-modules/flagger/retire', headers=self.h('enterprise-admin'))
        self.assertEqual(self.client.get('/api/training-modules', headers=self.h()).json()['items'], [])
        self.assertEqual(self.attempt([1, 0]).status_code, 409)


    def attempts_stored(self):
        with self.storage.connect() as db:
            return db.execute('SELECT COUNT(*) FROM training_attempts').fetchone()[0]

    def test_assessment_retry_identity_includes_the_module_version(self):
        self.ready(); self.save(expected_version=1, title='Updated procedure'); self.publish(2)
        self.save(expected_version=2, title='Third procedure')
        rid = str(uuid4())
        first = self.attempt([0, 1], version=2, request_id=rid); self.assertEqual(first.status_code, 200, first.text)
        self.publish(3); stored = self.attempts_stored()
        # Same request ID, same answers, different version: a conflict with no new write.
        self.assertEqual(self.attempt([0, 1], version=3, request_id=rid).status_code, 409)
        self.assertEqual(self.attempts_stored(), stored)
        # The exact retry still returns the original result.
        self.assertEqual(self.attempt([0, 1], version=2, request_id=rid).json(), first.json())
        self.assertEqual(self.attempts_stored(), stored)

    def test_cancelled_assignment_is_explicitly_reassigned_with_audit(self):
        self.ready(); admin = self.h('enterprise-admin')
        due = (date.today() + timedelta(days=7)).isoformat(); later = (date.today() + timedelta(days=14)).isoformat()
        body = {'module_id': 'flagger', 'user_ids': ['enterprise-general'], 'due_on': due}
        item = self.client.post('/api/training-assignments', headers=admin, json=body).json()['items'][0]
        url = f"/api/training-assignments/{item['id']}"
        self.assertEqual(self.client.post(url + '/cancel', headers=admin).json()['status'], 'cancelled')
        self.assertEqual(self.client.post(url + '/cancel', headers=admin).json()['status'], 'cancelled')
        # An assign retry never silently restores a cancellation; it says reassignment is required.
        again = self.client.post('/api/training-assignments', headers=admin, json=body).json()['items'][0]
        self.assertEqual((again['id'], again['status'], again['reassign_required']), (item['id'], 'cancelled', True))
        self.assertEqual(self.client.post(url + '/reassign', headers=self.h(), json={'due_on': due}).status_code, 403)
        self.assertEqual(self.client.post(url + '/reassign', headers=self.h('core-admin'), json={'due_on': due}).status_code, 404)
        restored = self.client.post(url + '/reassign', headers=admin, json={'due_on': due}).json()
        self.assertEqual((restored['status'], restored['due_on'], restored['reassign_required']), ('assigned', due, False))
        self.assertEqual(self.client.post(url + '/reassign', headers=admin, json={'due_on': due}).json(), restored)
        self.assertEqual(self.client.post(url + '/reassign', headers=admin, json={'due_on': later}).json()['due_on'], later)
        self.assertEqual(self.client.get('/api/training-assignments', headers=self.h()).json()['items'][0]['status'], 'assigned')
        self.assertTrue(self.attempt([1, 0]).json()['passed'])
        self.assertEqual(self.client.post(url + '/reassign', headers=admin, json={'due_on': later}).status_code, 409)
        self.assertEqual(self.client.post(url + '/cancel', headers=admin).status_code, 409)
        events = [e['event'] for e in self.client.get(url + '/events', headers=admin).json()['items']]
        self.assertEqual(events, ['assigned', 'cancelled', 'reassigned', 'due_changed', 'completed'])
        self.assertEqual(self.client.get(url + '/events', headers=self.h('core-admin')).status_code, 404)

    def test_reassigning_a_cancelled_old_version_requires_the_current_version(self):
        self.ready(); admin = self.h('enterprise-admin')
        item = self.client.post('/api/training-assignments', headers=admin, json={'module_id': 'flagger', 'user_ids': ['enterprise-general']}).json()['items'][0]
        self.client.post(f"/api/training-assignments/{item['id']}/cancel", headers=admin)
        self.save(expected_version=1, title='Revised'); self.publish(2)
        self.assertEqual(self.client.post(f"/api/training-assignments/{item['id']}/reassign", headers=admin, json={}).status_code, 409)
        fresh = self.client.post('/api/training-assignments', headers=admin, json={'module_id': 'flagger', 'user_ids': ['enterprise-general']}).json()['items'][0]
        self.assertEqual((fresh['module_version'], fresh['status']), (2, 'assigned'))


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Dedicated PostgreSQL database not configured')
class PostgreSQLTrainingContentTests(TrainingContentTests):
    make_storage = fixtures.PostgreSQLFormSubmissionTests.make_storage


if __name__ == '__main__':
    unittest.main()
