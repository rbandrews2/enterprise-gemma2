import os
import unittest
from uuid import uuid4

from tests import test_employees as fixtures
from tests import test_accounts_storage


class EquipmentTests(unittest.TestCase):
    headers = fixtures.EmployeeTests.headers
    make_storage = fixtures.EmployeeTests.make_storage

    def setUp(self):
        fixtures.EmployeeTests.setUp(self)
        self.base = '/api/equipment-locator'
        self.url = self.base + '/' + str(uuid4())
        self.placement = dict(equipment_type='TMA', quantity=2, location_method='coordinates',
                              latitude=0, longitude=-76.3)

    def test_shared_placements_retries_and_retrieval(self):
        headers = self.headers('member')
        for _ in range(2):
            self.assertEqual(self.client.put(self.url,headers=headers,json=self.placement).status_code,200)
        self.assertEqual(self.client.put(self.url,headers=headers,json={**self.placement,'quantity':4}).status_code,409)
        rows = self.client.get(self.base,headers=self.headers()).json()['items']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['quantity'],2)
        for _ in range(2):
            self.assertEqual(self.client.put(self.url+'/retrieved',headers=self.headers()).status_code,200)
        self.client.put(self.url,headers=headers,json=self.placement)
        self.assertEqual(self.client.get(self.base,headers=headers).json()['items'],[])

    def test_validate_both_modes_and_custom_equipment(self):
        for patch in ({'longitude':None},{'latitude':91},{'longitude':181},{'quantity':0},
                      {'quantity':1.5},{'quantity':True},{'equipment_type':'Custom'},
                      {'custom_name':'unselected'},{'location_method':'address'},
                      {'location_method':'address','address':{'street':'Broad','city':' ','region':'VA'}}):
            with self.subTest(patch=patch):
                self.assertEqual(self.client.put(self.url,headers=self.headers(),json={**self.placement,**patch}).status_code,422)
        valid = {**self.placement,'equipment_type':'Custom','custom_name':'Light tower','location_method':'address',
                 'address':{'street':'120 Main Street','city':'Richmond','region':'VA'}}
        self.assertEqual(self.client.put(self.url,headers=self.headers(),json=valid).status_code,200)

    def test_access_and_tenant_isolation(self):
        self.client.put(self.url,headers=self.headers(),json=self.placement)
        self.assertEqual(self.client.get(self.base).status_code,401)
        for edition in ['enterprise','core']:
            code = self.app.state.accounts.issue_activation(edition)
            org = self.client.post('/api/account/organizations',headers=self.headers('other'),
                    json={'name':'Other crew','activation_code':code}).json()['id']
            headers = {**self.headers('other'),'X-WZOS-Organization':org}
            response = self.client.get(self.base,headers=headers)
            if edition == 'core':
                self.assertEqual(response.status_code,403)
                self.assertEqual(self.client.put(self.url,headers=headers,json=self.placement).status_code,403)
                self.assertEqual(self.client.put(self.url+'/retrieved',headers=headers).status_code,403)
            else:
                self.assertEqual(response.json()['items'],[])
                self.assertEqual(self.client.put(self.url+'/retrieved',headers=headers).status_code,404)


@unittest.skipUnless(os.getenv('WZOS_TEST_DATABASE_URL'), 'Disposable PostgreSQL required')
class PostgreSQLEquipmentTests(EquipmentTests):
    make_storage = test_accounts_storage.PostgreSQLAccountStorageTests.make_storage
