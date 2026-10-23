import os
import unittest

from services.workspace_preview.employee_import import parse_csv
from tests import test_employees, test_accounts_storage


class EmployeeImportTests(unittest.TestCase):
    setUp = test_employees.EmployeeTests.setUp
    make_storage = test_employees.EmployeeTests.make_storage
    headers = test_employees.EmployeeTests.headers
    CSV = 'name,email,employee_number,phone\r\nAlex Crew,alex@example.test,E-001,+15405550123\r\n'

    def review(self, csv_text=None, user='admin'):
        return self.client.post('/api/account/employee-import/review', headers=self.headers(user), json={'csv_text': self.CSV if csv_text is None else csv_text})

    def confirm(self, batch, user='admin', reviewed=True):
        return self.client.post(f'/api/account/employee-import/{batch}/confirm', headers=self.headers(user), json={'reviewed': reviewed})

    def test_template_admin_and_member_boundaries(self):
        for path in ['template', 'roster']:
            self.assertEqual(self.client.get('/api/account/employee-import/'+path, headers=self.headers('member')).status_code, 403)
        self.assertEqual(self.review(user='member').status_code, 403)
        r=self.client.get('/api/account/employee-import/template', headers=self.headers())
        self.assertEqual(r.text, 'name,email,employee_number,phone\r\n')
        self.assertEqual(r.headers['cache-control'], 'no-store')

    def test_review_confirm_receipt_and_no_membership_or_messages(self):
        before=self.client.get('/api/account/members',headers=self.headers()).json()
        batch=self.review().json()
        self.assertEqual((batch['ready'],batch['duplicates'],batch['errors']),(1,0,0))
        self.assertEqual(self.client.get('/api/account/employee-import/roster',headers=self.headers()).json()['items'],[])
        receipt=self.confirm(batch['id']).json()
        self.assertEqual(receipt['imported'],1)
        self.assertEqual(self.confirm(batch['id']).json(),receipt)
        self.assertEqual(self.client.get('/api/account/members',headers=self.headers()).json(),before)
        rows=self.client.get('/api/account/employee-import/roster',headers=self.headers()).json()['items']
        self.assertEqual(rows[0]['email'],'alex@example.test')
        with self.app.state.accounts.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invitations').fetchone()[0],1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM access_audit WHERE action='employee_roster_imported'").fetchone()[0],1)

    def test_duplicate_file_existing_member_and_roster(self):
        batch=self.review(self.CSV+'Alex Duplicate,ALEX@example.test,E-002,\nMember,member@example.test,E-003,\n').json()
        self.assertEqual((batch['ready'],batch['duplicates']),(1,2))
        self.assertEqual(self.confirm(batch['id']).json()['skipped'],2)
        again=self.review().json()
        self.assertEqual((again['ready'],again['duplicates']),(0,1))
        self.assertEqual(self.confirm(again['id']).status_code,422)

    def test_errors_block_atomic_confirmation_and_require_review(self):
        bad=self.review(self.CSV+'Bad,not-email,??,555\n').json()
        self.assertEqual(bad['errors'],1)
        self.assertEqual(self.confirm(bad['id']).status_code,422)
        good=self.review().json()
        self.assertEqual(self.confirm(good['id'],reviewed=False).status_code,422)
        self.assertEqual(self.client.get('/api/account/employee-import/roster',headers=self.headers()).json()['items'],[])

    def test_stale_review_conflicts(self):
        first=self.review().json()
        second=self.review(self.CSV.replace('alex@','jordan@').replace('E-001','E-002')).json()
        self.assertEqual(self.confirm(first['id']).status_code,200)
        self.assertEqual(self.confirm(second['id']).status_code,409)

    def test_tenant_actor_denial_and_expiry(self):
        batch=self.review().json()
        self.assertEqual(self.confirm(batch['id'],user='member').status_code,403)
        self.assertEqual(self.confirm(batch['id'],user='other').status_code,403)
        code=self.app.state.accounts.issue_activation('core')
        other_org=self.client.post('/api/account/organizations',headers=self.headers('other'),json={'name':'Other org','activation_code':code}).json()['id']
        h={'Authorization':'Bearer other','X-WZOS-Organization':other_org}
        self.assertEqual(self.client.post(f"/api/account/employee-import/{batch['id']}/confirm",headers=h,json={'reviewed':True}).status_code,404)
        self.assertEqual(self.client.get('/api/account/employee-import/roster',headers=h).json()['items'],[])
        with self.app.state.accounts.connect() as db:
            db.execute('UPDATE employee_import_batches SET expires_at=? WHERE id=?',('2000-01-01T00:00:00+00:00',batch['id']))
        self.assertEqual(self.confirm(batch['id']).status_code,409)

    def test_schema_limits_bom_and_safe_text(self):
        for text in ['name,name,email,employee_number\nA,B,c@d.test,1\n','name,email,employee_number,role\nA,b@c.test,1,admin\n', 'name,email,employee_number\n', 'name,email,employee_number\n"unterminated']:
            self.assertEqual(self.review(text).status_code,422,text)
        row=parse_csv('\ufeffname,email,employee_number,phone\n=Some Name,SAFE@example.test,e-1,\n',set(),set())[0]
        self.assertEqual(row['email'],'safe@example.test')
        self.assertEqual(row['name'],'=Some Name') # Rendered with textContent, never executed/exported as formula.
        self.assertEqual(self.review('name,email,employee_number\n'+('Valid,a@b.test,1\n'*501)).status_code,422)

    def test_core_pagination_and_duplicate_numbers(self):
        code=self.app.state.accounts.issue_activation('core')
        self.org=self.client.post('/api/account/organizations',headers=self.headers(),json={'name':'Core import','activation_code':code}).json()['id']
        text='name,email,employee_number\n'+''.join(f'Employee {i},crew{i}@example.test,E-{i}\n' for i in range(26))
        batch=self.review(text+'Duplicate number,another@example.test,E-0\n').json()
        self.assertEqual((batch['ready'],batch['duplicates']),(26,1))
        self.assertEqual(self.confirm(batch['id']).json()['imported'],26)
        first=self.client.get('/api/account/employee-import/roster',headers=self.headers()).json()
        second=self.client.get('/api/account/employee-import/roster?offset=25',headers=self.headers()).json()
        self.assertEqual((first['total'],len(first['items']),len(second['items'])),(26,25,1))
        self.assertEqual(len({r['email'] for r in first['items']+second['items']}),26)


@unittest.skipUnless(os.environ.get('WZOS_TEST_DATABASE_URL'),'Disposable PostgreSQL required')
class PostgreSQLEmployeeImportTests(EmployeeImportTests):
    make_storage=test_accounts_storage.PostgreSQLAccountStorageTests.make_storage
