import base64
import io
import os
import unittest
import zipfile
from uuid import uuid4

from fastapi import HTTPException
from services.workspace_preview.bulk_managed import Upload, parse
from tests import test_managed_accounts, test_accounts_storage


def workbook(sheet, extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('xl/worksheets/sheet1.xml', sheet)
        for name, value in (extra or {}).items():
            z.writestr(name, value)
    return base64.b64encode(stream.getvalue()).decode()


class BulkParserTests(unittest.TestCase):
    def upload(self, content, format='csv'):
        return Upload(batch_id=uuid4(), format=format, content=content)

    def test_csv_aliases_quoted_name_and_password_whitespace_preserved(self):
        records, ignored = parse(self.upload('NAME,ACCESS LEVEL,POSITION,USERNAME,PASSWORD,COMPANY_ID,EMAIL,TELEPHONE\n"Employee, Test",MEMBER,Operator,test.user,  synthetic-password  ,foreign,TEST@example.test,555\n'))
        self.assertEqual(records[0]['name'], 'Employee, Test')
        self.assertEqual(records[0]['role'], 'member')
        self.assertEqual(records[0]['password'], '  synthetic-password  ')
        self.assertNotIn('company_id', records[0])
        self.assertIn('company_id', ignored)

    def test_spreadsheet_paste_and_stable_row_ids(self):
        body=self.upload('name\temail\tusername\tpassword\trole\nTest User\ttest@example.test\ttest.user\tSynthetic-password\tmember', 'tsv')
        self.assertEqual(parse(body)[0], parse(body)[0])

    def test_excel_inline_and_shared_strings(self):
        cells=''.join(f'<c r="{chr(65+i)}1" t="inlineStr"><is><t>{value}</t></is></c>' for i,value in enumerate(['name','email','username','password','role']))
        values=''.join(f'<c r="{chr(65+i)}2" t="s"><v>{i}</v></c>' for i in range(5))
        sheet=f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row>{cells}</row><row>{values}</row></sheetData></worksheet>'
        strings='<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'+''.join(f'<si><t>{v}</t></si>' for v in ['Test User','test@example.test','test.user','Synthetic-password','member'])+'</sst>'
        records,_=parse(self.upload(workbook(sheet,{'xl/sharedStrings.xml':strings}),'xlsx'))
        self.assertEqual(records[0]['username'],'test.user')

    def test_reject_formula_entities_macros_multiple_sheets_and_oversize(self):
        cases=[workbook('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><f>1+1</f></worksheet>'),
               workbook('<!DOCTYPE x [<!ENTITY foo "bad">]><x/>'),
               workbook('<x/>',{'xl/vbaProject.bin':'bad'}),
               workbook('<x/>',{'xl/worksheets/sheet2.xml':'<x/>'}),
               workbook('<x/>',{'xl/externalLinks/externalLink1.xml':'<x/>'}),
               workbook('<x/>',{'large':'0'*(8*1024*1024)})]
        for content in cases:
            with self.subTest(length=len(content)),self.assertRaises(HTTPException):parse(self.upload(content,'xlsx'))

    def test_headers_and_row_limit(self):
        for content in ['name,email,username,password,role,role\na,b,c,d,e,f', 'name,email\na,b', 'name,email,username,password,role\n'+('Test,t@e.test,test,Synthetic-password,member\n'*501)]:
            with self.assertRaises(HTTPException):parse(self.upload(content))


class BulkManagedTests(unittest.TestCase):
    make_storage=test_accounts_storage.AccountStorageTests.make_storage
    build=test_accounts_storage.AccountStorageTests.build
    create_org=test_accounts_storage.AccountStorageTests.create_org
    headers=test_accounts_storage.AccountStorageTests.headers
    add=test_accounts_storage.AccountStorageTests.add

    def setUp(self):
        test_accounts_storage.AccountStorageTests.setUp(self)
        self.provider=test_managed_accounts.FakeProvider(self.claims)
        self.app.state.accounts.verify=self.provider
        self.body={'batch_id':str(uuid4()),'format':'csv','content':'name,email,username,password,role\nTest One,one@example.test,test.one,Synthetic-password-42,member\nTest Two,two@example.test,test.two,Synthetic-password-43,admin'}

    def call(self, action='review', who='creator', **values):
        body={**self.body,**values}
        return self.client.post('/api/account/managed/bulk/'+action,headers=self.headers(who),json=body)

    def create(self, **values):
        return self.call('create',reviewed=True,rows=[0,1],**values)

    def test_review_has_no_passwords_and_no_side_effects(self):
        response=self.call();self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(response.json()['valid']);self.assertEqual(self.provider.created,0)
        self.assertNotIn('Synthetic-password',response.text);self.assertIn('no-store',response.headers['cache-control'])

    def test_create_idempotency_and_roles(self):
        result=self.create();self.assertEqual(result.status_code,200,result.text)
        self.assertTrue(all(r['created'] for r in result.json()['items']))
        self.assertEqual(self.create().json(),result.json());self.assertEqual(self.provider.created,2)
        with self.app.state.accounts.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invitations').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM managed_accounts WHERE password_changed=0').fetchone()[0],2)
        self.assertTrue(self.call().json()['valid'])

    def test_member_and_unrelated_denied(self):
        self.add('member')
        for who in ('member','other'):
            self.assertEqual(self.call(who=who).status_code,403)
            self.assertEqual(self.call('create',who=who,reviewed=True,rows=[0]).status_code,403)
        self.assertEqual(self.provider.created,0)

    def test_later_chunk_only_creates_selected_row(self):
        response=self.call('create',reviewed=True,rows=[1])
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['items'][0]['index'],1)
        self.assertTrue(response.json()['items'][0]['created'])
        self.assertEqual(self.provider.created,1)
        self.assertEqual(next(iter(self.provider.users.values())).email,'two@example.test')

    def test_duplicate_invalid_and_existing_rows(self):
        for text in [self.body['content'].replace('two@example.test','one@example.test'),self.body['content'].replace(',admin',',owner'),self.body['content'].replace('one@example.test','creator@example.test')]:
            response=self.call(content=text)
            self.assertFalse(response.json()['valid']);self.assertNotIn('Synthetic-password',response.text)
            self.assertEqual(self.create(content=text).status_code,409)
        self.assertEqual(self.provider.created,0)

    def test_seat_race_partial_result_does_not_exceed_allowance(self):
        self.assertTrue(self.call().json()['valid'])
        with self.app.state.accounts.connect() as db:
            db.execute('INSERT INTO organization_entitlements VALUES (?,?,2)',(self.org,'bulk-seat-test'))
        self.assertFalse(self.call().json()['capacity_ok'])
        items=self.create().json()['items']
        self.assertTrue(items[0]['created']);self.assertFalse(items[1]['created']);self.assertEqual(self.provider.created,1)

    def test_provider_partial_failure_retry_and_changed_details(self):
        self.provider.fail_enable=True
        self.assertFalse(self.create().json()['items'][0]['created'])
        self.assertEqual(self.provider.created,2)
        self.provider.fail_enable=False
        self.assertTrue(all(r['created'] for r in self.create(batch_id=str(uuid4())).json()['items']));self.assertEqual(self.provider.created,2)
        changed=self.body['content'].replace('Test One','Different Name')
        self.assertEqual(self.create(content=changed).status_code,409)

    def test_explicit_confirmation_bounds_and_validation_redaction(self):
        for values in [{'reviewed':False,'rows':[0]}, {'reviewed':True,'rows':[0,0]}, {'reviewed':True,'rows':[-1]}, {'reviewed':True,'rows':list(range(6))}]:
            response=self.call('create',**values);self.assertEqual(response.status_code,422,response.text)
            self.assertNotIn('Synthetic-password',response.text)
        self.assertEqual(self.provider.created,0)


@unittest.skipUnless(os.environ.get('WZOS_TEST_DATABASE_URL'),'PostgreSQL test database required')
class PostgreSQLBulkManagedTests(BulkManagedTests):
    make_storage=test_accounts_storage.PostgreSQLAccountStorageTests.make_storage
