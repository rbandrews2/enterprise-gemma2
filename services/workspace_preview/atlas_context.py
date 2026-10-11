"""Bounded read-only operational facts for Atlas; never secrets or autonomous actions."""
import json
import re
from datetime import datetime, timezone


def operational_context(connect, user, page, question, account_workspace=False):
    stamp = datetime.now(timezone.utc).isoformat()
    result = {'observed_at': stamp, 'scope': 'own_account_in_selected_organization',
              'records_are_complete': False, 'actions_performed': []}
    org, uid = user['organization_id'], user['id']
    with connect() as db:
        if account_workspace and user['edition'] == 'enterprise' and (
                page in ('schedule', 'navigation') or re.search(r'assign|dispatch|next job|my jobs|acknowledg|confirm receipt', question, re.I)):
            clause = "a.organization_id=? AND a.user_id=? AND a.status IN ('sent','accepted') AND a.ends_at>=?"
            args = [org, uid, stamp]
            base = ' FROM dispatch_assignments a JOIN dispatch_plans p ON p.id=a.plan_id AND p.organization_id=a.organization_id WHERE ' + clause + " AND p.status='sent'"
            total = db.execute('SELECT COUNT(*)' + base, args).fetchone()[0]
            rows = db.execute('SELECT a.status,a.starts_at,a.ends_at,p.payload' + base + ' ORDER BY a.starts_at,a.id LIMIT 3', args).fetchall()
            items = []
            for row in rows:
                snapshot = json.loads(row['payload']).get('delivery_snapshot') or {}
                items.append({'title': str(snapshot.get('order_title', 'Historical assignment'))[:120],
                              'status': row['status'], 'starts_at': row['starts_at'], 'estimated_finish': row['ends_at'],
                              'snapshot_state': snapshot.get('snapshot_state', 'legacy_unavailable'),
                              'receipt_confirmation_needed': row['status'] == 'sent'})
            result['upcoming_assignments'] = {'total': total, 'items': items, 'truncated': total > len(items)}
        if page == 'forms' or re.search(r'form|submission|worksheet|jsa|inspection', question, re.I):
            base = " FROM module_records WHERE organization_id=? AND owner_id=? AND kind='forms'"
            total = db.execute('SELECT COUNT(*)' + base, (org, uid)).fetchone()[0]
            rows = db.execute('SELECT id,version,payload' + base + ' ORDER BY updated_at DESC,id LIMIT 3', (org, uid)).fetchall()
            items = []
            for row in rows:
                form = json.loads(row['payload'])
                sent = db.execute('SELECT status FROM form_submissions WHERE organization_id=? AND form_id=? AND form_version=?', (org, row['id'], row['version'])).fetchone()
                items.append({'title': str(form.get('title', 'Saved form'))[:120], 'type': form.get('form_type', 'incident'),
                              'version': row['version'], 'status': form.get('status', 'draft'),
                              'linked_job': bool(form.get('order_id')), 'current_version_submitted': bool(sent),
                              'internal_review_status': sent['status'] if sent else 'not_submitted'})
            result['own_saved_forms'] = {'total': total, 'items': items, 'truncated': total > len(items),
                                        'missing_records_are_not_missing_compliance': True}
        if user['role'] == 'admin' and re.search(r'review queue|pending review|team forms|submissions', question, re.I):
            rows = db.execute('SELECT status,COUNT(*) AS n FROM form_submissions WHERE organization_id=? GROUP BY status', (org,)).fetchall()
            result['organization_form_review_counts'] = {row['status']: row['n'] for row in rows}
    return result
