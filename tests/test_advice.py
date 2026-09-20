import unittest
from services.v2.advice import review_project
from services.v2.intake import assess
from services.v2.projects import evidence_review
from shared.projects import ProjectDraft


class AdviceTests(unittest.TestCase):
    def advice(self, **changes):
        intake = {'work_type':'line_striping','location':{'address':'Example'},
                  'requested_outputs':['annotated_image'], **changes}
        draft = ProjectDraft.model_validate({'name':'Example','intake':intake})
        return review_project(draft, assess(draft.intake), evidence_review(draft))

    def test_broad_review_and_unknown_distinction(self):
        items=self.advice()
        self.assertEqual({a['category'] for a in items},
                         {'project_context','forms','evidence','requested_function','operations'})
        self.assertEqual(len({a['id'] for a in items}),len(items))
        by_id={a['id']:a for a in items}
        self.assertEqual(by_id['crew_readiness']['state'],'unknown')
        self.assertEqual(by_id['intake_locality']['state'],'missing')
        self.assertEqual(by_id['delivery_annotated_image']['state'],'not_implemented')
        self.assertTrue(all(a['legally_required'] is None for a in items))
        self.assertTrue(all(a['reason'] and a['next_action'] for a in items))

    def test_context_and_requested_function_change_advice(self):
        items=self.advice(work_type='underground_utility', requested_outputs=['email_delivery'],
                          site={'work_period':'night','excavation_planned':True})
        ids={a['id'] for a in items}
        self.assertIn('intake_utility_work',ids)
        self.assertIn('intake_night_work',ids)
        self.assertIn('delivery_email_delivery',ids)
        self.assertNotIn('delivery_annotated_image',ids)
        self.assertNotIn('intake_striping_operation',ids)
