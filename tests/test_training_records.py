import os,unittest
from datetime import date,timedelta
from uuid import uuid4
from tests import test_form_submissions as fixtures

class TrainingRecordTests(unittest.TestCase):
    setUp=fixtures.FormSubmissionTests.setUp
    make_storage=fixtures.FormSubmissionTests.make_storage
    h=fixtures.FormSubmissionTests.h
    def record_body(self):
        course=self.client.get('/api/training-records/catalog',headers=self.h()).json()['items'][0]
        return {'request_id':str(uuid4()),'course_id':course['id'],'catalog_hash':course['catalog_hash'],'completed_on':date.today().isoformat(),'minutes':30,'material_reference':'Synthetic study material','notes':'Read chapter one','acknowledged':True}
    def post_record(self,body,who='enterprise-general'):
        return self.client.post('/api/training-records',headers=self.h(who),json=body)
    def test_training_snapshot_retry_scope(self):
        body=self.record_body();r=self.post_record(body);self.assertEqual(r.status_code,200,r.text)
        self.assertFalse(r.json()['qualification_issued']);self.assertEqual(self.post_record(body).json(),r.json())
        self.assertEqual(self.post_record({**body,'minutes':31}).status_code,409)
        self.assertEqual(self.client.get('/api/training-records',headers=self.h('core-admin')).json()['items'],[])
        self.assertEqual(self.client.get('/api/training-records',headers=self.h('enterprise-admin')).json()['total'],1)
        self.assertEqual(r.json()['record']['acknowledgement']['material_reference'],body['material_reference'])
    def test_training_validation_and_paging(self):
        body=self.record_body()
        for change,code in [({'acknowledged':False},422),({'minutes':0},422),({'completed_on':(date.today()+timedelta(days=2)).isoformat()},422),({'catalog_hash':'0'*64},409),({'course_id':'unknown'},404)]:
            self.assertEqual(self.post_record({**body,**change}).status_code,code)
        self.post_record(body)
        self.assertEqual(self.client.get('/api/training-records?offset=1',headers=self.h()).json()['items'],[])
        self.assertEqual(self.client.get('/api/training-records?limit=51',headers=self.h()).status_code,422)
    def test_training_admin_review(self):
        record=self.post_record(self.record_body()).json();url='/api/training-records/'+record['id']+'/review'
        body={'expected_version':1,'status':'changes_requested','note':'Add material edition'}
        self.assertEqual(self.client.post(url,headers=self.h(),json=body).status_code,403)
        self.assertEqual(self.client.post(url,headers=self.h('core-admin'),json=body).status_code,404)
        result=self.client.post(url,headers=self.h('enterprise-admin'),json=body);self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(self.client.post(url,headers=self.h('enterprise-admin'),json=body).json(),result.json())
        self.assertEqual(self.client.post(url,headers=self.h('enterprise-admin'),json={**body,'status':'reviewed'}).status_code,409)

@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'),'Dedicated PostgreSQL database not configured')
class PostgreSQLTrainingRecordTests(TrainingRecordTests):
    make_storage=fixtures.PostgreSQLFormSubmissionTests.make_storage

