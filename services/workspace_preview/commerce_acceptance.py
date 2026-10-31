"""Isolated deployed acceptance surface; never mounted in the customer app.

The control service MUST require Cloud Run IAM. Its synthetic buyer selector is
not an authentication credential. The public service exposes only the existing
signed webhook handler. Both use a separately provisioned PostgreSQL database.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .accounts import Accounts
from .commerce_runtime import register
from .postgres import PostgreSQLStorage

SERVICES = {'wzos-checkout-acceptance-control': 'control',
            'wzos-checkout-acceptance-webhook': 'webhook'}


def validate_environment(environment):
    from psycopg.conninfo import conninfo_to_dict
    role = SERVICES.get(environment.get('K_SERVICE'))
    if (not role or environment.get('WZOS_CHECKOUT_ACCEPTANCE') != '1'
            or environment.get('WZOS_STRIPE_MODE') != 'test'
            or environment.get('WZOS_COMMERCE_ENABLED') != '1'
            or not environment.get('WZOS_STRIPE_TEST_CATALOG')
            or not environment.get('WZOS_STRIPE_TEST_RETURN_ORIGIN')):
        raise RuntimeError('Explicit isolated acceptance configuration required')
    dsn = environment.get('WZOS_DATABASE_URL', '')
    if conninfo_to_dict(dsn).get('dbname') != 'wzos_checkout_acceptance':
        raise RuntimeError('Acceptance requires its dedicated database')
    return role


def synthetic_buyer(selector):
    if selector not in ('core', 'enterprise'):
        raise ValueError('Unknown synthetic buyer')
    return {'uid': 'acceptance-' + selector, 'email': selector + '-acceptance@example.test',
            'email_verified': True}


def create_app():
    role = validate_environment(os.environ)
    storage = PostgreSQLStorage(os.environ['WZOS_DATABASE_URL'])
    storage.initialize()
    accounts = Accounts(storage.connect, synthetic_buyer, auth_header='X-WZOS-Authorization')

    @asynccontextmanager
    async def lifespan(app):
        yield
        storage.close()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    accounts.register(app)
    register(app, accounts)
    if role == 'webhook':
        app.router.routes = [route for route in app.router.routes
                             if route.path == '/api/commerce/webhook']
    else:
        app.router.routes = [route for route in app.router.routes
                             if route.path != '/api/commerce/webhook']

    @app.middleware('http')
    async def no_store(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/', response_class=HTMLResponse)
    def returned():
        return '<h1>WZOS test checkout</h1><p>Return received. Payment and activation must still be verified through the authenticated receipt.</p>'

    return app
