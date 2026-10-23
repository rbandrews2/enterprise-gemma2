"""Server-owned edition/seat grants; no browser-selected billing entitlements."""
import re
from fastapi import HTTPException


DDL = (
    'CREATE TABLE IF NOT EXISTS activation_entitlements (activation_hash TEXT PRIMARY KEY,seat_limit INTEGER NOT NULL CHECK(seat_limit>0),purchaser_email TEXT)',
    'CREATE TABLE IF NOT EXISTS organization_entitlements (organization_id TEXT PRIMARY KEY,activation_hash TEXT NOT NULL UNIQUE,seat_limit INTEGER NOT NULL CHECK(seat_limit>0))',
)


class Licensing:
    def __init__(self, connect):
        self.connect = connect
        with connect() as db:
            for sql in DDL:
                db.execute(sql)

    @staticmethod
    def validate(seats, email=None):
        if type(seats) is not int or not 1 <= seats <= 100000:
            raise ValueError('Seat allowance must be an integer from 1 to 100000')
        if email is not None and (not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email)):
            raise ValueError('Purchaser email is invalid')

    def attach_activation(self, db, activation_hash, seats, email=None):
        self.validate(seats, email)
        db.execute('INSERT INTO activation_entitlements VALUES (?,?,?)',
                   (activation_hash, seats, email.lower() if email else None))

    def redeem(self, db, activation_hash, org, user):
        if getattr(self,'billing_check',None):
            self.billing_check(db,activation_hash)
        grant = db.execute('SELECT * FROM activation_entitlements WHERE activation_hash=?', (activation_hash,)).fetchone()
        if grant:
            if grant['purchaser_email'] and grant['purchaser_email'] != user['email']:
                raise HTTPException(403, 'Use the verified purchasing email to activate this organization')
            db.execute('INSERT INTO organization_entitlements VALUES (?,?,?)', (org, activation_hash, grant['seat_limit']))

    def status(self, db, org):
        grant = db.execute('SELECT seat_limit FROM organization_entitlements WHERE organization_id=?', (org,)).fetchone()
        used = db.execute('SELECT COUNT(*) FROM memberships WHERE organization_id=? AND active=1', (org,)).fetchone()[0]
        limit = grant['seat_limit'] if grant else None
        return {'seat_limit': limit, 'seats_used': used,
                'seats_available': max(0, limit-used) if limit is not None else None,
                'licensing_status': 'configured' if grant else 'legacy_unconfigured',
                'seat_policy': 'all_active_logins_including_admins'}

    def require_capacity(self, db, org):
        # Serialize capacity checks across invitations, reactivation and direct
        # admin provisioning. Callers already own the surrounding transaction.
        db.execute('UPDATE organizations SET active=active WHERE id=?', (org,))
        status = self.status(db, org)
        # Historical organizations retain access until an explicit licensing migration.
        if status['seat_limit'] is not None and status['seats_used'] >= status['seat_limit']:
            raise HTTPException(409, 'All purchased seats are in use. Disable an unused account or purchase additional seats.')
