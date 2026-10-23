"""Bounded, transient account imports. Never persist uploads or passwords."""
import base64
import binascii
import csv
import io
import re
import zipfile
from collections import Counter
from uuid import UUID, uuid5
from xml.etree import ElementTree as ET

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError
from starlette.responses import JSONResponse

MAX_BYTES = 1024 * 1024
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
COLUMNS = ('name', 'email', 'username', 'password', 'role')
IGNORED = {'position', 'company_id', 'telephone', 'employee_number', 'phone'}


class Upload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    batch_id: UUID
    format: str = Field(pattern=r'^(csv|tsv|xlsx)$')
    content: SecretStr = Field(min_length=1, max_length=1400000)


class Confirmation(Upload):
    reviewed: bool
    rows: list[int] = Field(min_length=1, max_length=5)


def fail(message='Use a valid CSV or single-sheet XLSX file, up to 1 MiB and 500 employees.'):
    raise HTTPException(422, message)


def xml(data):
    # Reject DTD/entity declarations, including UTF-16 encoded XML.
    if b'<!DOCTYPE' in data.replace(b'\x00', b'').upper() or b'<!ENTITY' in data.replace(b'\x00', b'').upper():
        fail('XML entities are not supported.')
    return ET.fromstring(data)


def xlsx_rows(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > 200 or sum(e.file_size for e in entries) > 8 * MAX_BYTES:
            fail('Spreadsheet is too large. Use the account template with up to 500 rows.')
        names = archive.namelist()
        if len(set(names)) != len(names) or any('vba' in n.lower() or 'externallinks/' in n.lower() for n in names):
            fail('Use an XLSX file without macros or external links.')
        sheets = [n for n in names if re.fullmatch(r'xl/worksheets/[^/]+\.xml', n)]
        if len(sheets) != 1:
            fail('Use a workbook with one worksheet containing the employee table.')
        strings = []
        if 'xl/sharedStrings.xml' in names:
            strings = [''.join(n.itertext()) for n in xml(archive.read('xl/sharedStrings.xml')).findall(NS+'si')]
        root = xml(archive.read(sheets[0]))
        if root.find('.//'+NS+'f') is not None:
            fail('Replace spreadsheet formulas with values before uploading.')
        rows = []
        for row in root.findall('.//'+NS+'sheetData/'+NS+'row'):
            values = [''] * 10
            seen = set()
            for cell in row.findall(NS+'c'):
                ref = re.fullmatch(r'([A-J])\d+', cell.get('r', ''))
                if not ref:
                    fail('Use no more than ten columns (A–J).')
                col = ord(ref[1])-65
                if col in seen:
                    fail()
                seen.add(col)
                kind = cell.get('t', '')
                value = cell.findtext(NS+'v', '')
                if kind == 's':
                    value = strings[int(value)]
                elif kind == 'inlineStr':
                    value = ''.join(cell.find(NS+'is').itertext())
                elif kind not in ('', 'str', 'n'):
                    fail('Use text cells for account details.')
                if len(value) > 1000:
                    fail('A spreadsheet cell is too long.')
                values[col] = value
            while values and not values[-1]:
                values.pop()
            if values:
                rows.append(values)
            if len(rows) > 501:
                fail('Import up to 500 employees at a time.')
        return rows


def parse(upload):
    try:
        content = upload.content.get_secret_value()
        if upload.format == 'xlsx':
            raw = base64.b64decode(content, validate=True)
            if len(raw) > MAX_BYTES:
                fail()
            rows = xlsx_rows(raw)
        else:
            if len(content.encode('utf-8')) > MAX_BYTES or '\x00' in content:
                fail()
            rows = []
            for row in csv.reader(io.StringIO(content.lstrip('\ufeff'), newline=''), delimiter='\t' if upload.format == 'tsv' else ',', strict=True):
                if any(row):
                    rows.append(row)
                if len(rows) > 501 or len(row) > 10:
                    fail()
        if len(rows) < 2:
            fail('Include a header and at least one employee.')
        headers = [h.strip().lower().replace(' ', '_') for h in rows[0]]
        headers = ['role' if h == 'access_level' else h for h in headers]
        if len(set(headers)) != len(headers) or not set(COLUMNS).issubset(headers) or set(headers)-set(COLUMNS)-IGNORED:
            fail('Required columns: name, email, username, password, role. Access level may be used instead of role.')
        records = []
        for index, row in enumerate(rows[1:]):
            if len(row) > len(headers):
                fail('A row has more columns than the header.')
            record = dict(zip(headers, row + ['']*(len(headers)-len(row))))
            values = {k: record[k] if k == 'password' else record[k].strip() for k in COLUMNS}
            for k in ('email', 'username', 'role'):
                values[k] = values[k].lower()
            records.append({**values, 'request_id': str(uuid5(upload.batch_id, str(index)))})
        return records, sorted(set(headers) & IGNORED)
    except HTTPException:
        raise
    except (ValueError, KeyError, IndexError, AttributeError, OSError, RuntimeError, zipfile.BadZipFile, ET.ParseError, csv.Error, binascii.Error):
        fail()


def register(app, accounts, admin, create, account_model, password_value):
    def review(upload, actor):
        records, ignored = parse(upload)
        counts = {key: Counter(r[key] for r in records) for key in ('email', 'username')}
        items = []
        with accounts.connect() as db:
            license = accounts.licensing.status(db, actor['organization_id'])
            for index, record in enumerate(records):
                errors = []
                try:
                    body = account_model(**record)
                    password_value(body.password)
                    if any(ord(c) < 32 for c in body.name):
                        errors.append('Name contains unsupported characters.')
                except (ValidationError, HTTPException):
                    errors.append('Check name, email, username, role (admin/member) and password (12–128 characters).')
                if any(counts[k][record[k]] > 1 for k in counts):
                    errors.append('Duplicate email or username in this upload.')
                own = db.execute('SELECT * FROM managed_accounts WHERE organization_id=? AND request_id=? AND created_by=?', (actor['organization_id'],record['request_id'],actor['id'])).fetchone()
                if not own and (db.execute('SELECT 1 FROM managed_accounts WHERE username=? OR email=?',(record['username'],record['email'])).fetchone() or db.execute('SELECT 1 FROM accounts WHERE lower(email)=?',(record['email'],)).fetchone()):
                    errors.append('Email or username already registered. Use an invitation for an existing account.')
                items.append({'index':index,'name':record['name'],'email':record['email'],'username':record['username'],'role':record['role'], 'errors':errors, 'state':own['state'] if own else 'new'})
        needed = sum(not i['errors'] and i['state']=='new' for i in items)
        capacity = license['seats_available'] is None or needed <= license['seats_available']
        return records, {'items':items, 'ignored_columns':ignored, 'license':license, 'seats_needed':needed, 'capacity_ok':capacity, 'valid':capacity and not any(i['errors'] for i in items)}

    @app.post('/api/account/managed/bulk/review')
    def preview(body: Upload, request: Request):
        _, result = review(body, admin(request))
        return JSONResponse(result, headers={'Cache-Control':'no-store'})

    @app.post('/api/account/managed/bulk/create')
    def confirm(body: Confirmation, request: Request):
        actor = admin(request)
        if not body.reviewed or len(set(body.rows)) != len(body.rows):
            raise HTTPException(422, 'Review and confirm the employee accounts first.')
        records, result = review(body, actor)
        if any(i < 0 or i >= len(records) for i in body.rows):
            raise HTTPException(422, 'Choose valid employee rows.')
        # Block erroneous rows; a seat race or provider failure is reported per row.
        if any(result['items'][i]['errors'] for i in body.rows):
            raise HTTPException(409, 'Some selected rows need correction. Review the upload again.')
        results = []
        for index in body.rows:
            try:
                receipt = create(account_model(**records[index]), request)
                results.append({'index':index,'created':True,'username':receipt['username']})
            except HTTPException as exc:
                results.append({'index':index,'created':False,'error':str(exc.detail)})
        return JSONResponse({'items':results}, headers={'Cache-Control':'no-store'})
