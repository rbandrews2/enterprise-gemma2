"""Opt-in authenticated checkout, mounted into the existing accounts runtime."""
import json
import os
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field


class PurchaseRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    offer_id: str = Field(max_length=32)
    seats: int = Field(strict=True, ge=1, le=100000)


def configured_purchases(accounts):
    if os.getenv('WZOS_COMMERCE_ENABLED') != '1':
        return None
    from cryptography.fernet import Fernet
    from .purchases import Offer, Purchases, StripeProvider
    catalog = json.loads((Path(__file__).resolve().parents[2] / 'knowledge/billing/v2-stripe-catalog.json').read_text())
    mode = os.environ['WZOS_STRIPE_MODE']
    if mode not in ('test', 'live') or (mode == 'live') is not catalog['livemode']:
        raise RuntimeError('An explicit matching Stripe catalog and mode are required')
    live = mode == 'live'
    if live and os.getenv('WZOS_STRIPE_TAX_VERIFIED') != '1':
        raise RuntimeError('Live checkout requires accepted tax configuration')
    offers = [Offer(id=key, edition=key, **{field: value[field] for field in (
        'included_seats', 'maximum_seats', 'setup_cents', 'monthly_cents',
        'additional_seat_monthly_cents', 'setup_price_id', 'monthly_price_id',
        'additional_seat_price_id')}) for key, value in catalog['offers'].items()]
    provider = StripeProvider(os.environ['WZOS_STRIPE_API_KEY'], os.environ['WZOS_STRIPE_WEBHOOK_SECRET'],
                              livemode=live, automatic_tax=live, tax_configuration_verified=live)
    return Purchases(accounts, provider, offers, Fernet(os.environ['WZOS_PURCHASE_ENCRYPTION_KEY'].encode()),
                     livemode=live, require_automatic_tax=live, recurring_lifecycle=True)


def register(app, accounts, purchases=None):
    purchases = purchases if purchases is not None else configured_purchases(accounts)
    app.state.purchases = purchases
    if purchases:
        purchases.single_purchase_identity=True

    def new_customer(request):
        user = accounts.identity(request)
        with accounts.connect() as db:
            existing = db.execute('SELECT organization_id FROM memberships WHERE user_id=? AND active=1', (user['id'],)).fetchone()
        if existing:
            raise HTTPException(409, 'Use organization billing support to change an existing subscription. No new subscription was created.')
        return user

    @app.get('/api/account/commerce')
    def catalog(request: Request):
        user = accounts.identity(request)
        with accounts.connect() as db:
            existing = db.execute('SELECT organization_id FROM memberships WHERE user_id=? AND active=1', (user['id'],)).fetchone()
        if not purchases or existing:
            return {'enabled': False, 'offers': []}
        return {'enabled': True, 'offers': [
            {key: getattr(offer, key) for key in ('id', 'edition', 'included_seats', 'maximum_seats',
                'setup_cents', 'monthly_cents', 'additional_seat_monthly_cents')}
            for offer in purchases.offers.values()]}

    @app.post('/api/account/checkout')
    def checkout(body: PurchaseRequest, request: Request):
        if not purchases:
            raise HTTPException(503, 'Online checkout is not available yet.')
        user = new_customer(request)
        try:
            return purchases.checkout(str(body.request_id), user['email'], body.offer_id, body.seats)
        except HTTPException:
            raise
        except ValueError:
            raise HTTPException(400, 'Check the selected edition and seat count.') from None
        except Exception:
            raise HTTPException(503, 'Checkout could not be prepared. Retry the same request; no purchase was confirmed.') from None

    if not purchases:
        return
    purchases.register_private_receipts(app)

    @app.post('/api/commerce/webhook')
    async def webhook(request: Request):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 1024 * 1024:
                raise HTTPException(413, 'Webhook body too large')
        from starlette.concurrency import run_in_threadpool
        try:
            return await run_in_threadpool(purchases.webhook, bytes(body), request.headers.get('stripe-signature', ''))
        except HTTPException:
            raise
        except (ValueError, KeyError, TypeError):
            raise HTTPException(400, 'Webhook could not be verified or matched.') from None
        except Exception:
            raise HTTPException(503, 'Billing update not confirmed. Retry delivery.') from None
