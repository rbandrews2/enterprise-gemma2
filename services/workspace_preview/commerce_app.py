"""Separate sandbox commerce surface. Not wired into the private workspace runtime.

Production remains refused by Purchases until recurring billing acceptance. Public
deployment/Secret Manager/price registration are explicit subsequent release gates.
"""
from uuid import UUID
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


class CheckoutRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    request_id: UUID
    email: str=Field(max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    offer_id: str=Field(max_length=32)
    seats: int=Field(strict=True,ge=1,le=100000)


def create_commerce_app(purchases):
    if purchases.livemode:raise ValueError('Sandbox-only commerce surface')
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    app.add_middleware(CORSMiddleware,allow_origins=['https://workzoneos.org'],allow_methods=['POST'],allow_headers=['Content-Type'])
    @app.middleware('http')
    async def boundary(request, call_next):
        if request.headers.get('origin') not in (None,'https://workzoneos.org'):
            return JSONResponse({'detail':'Origin not allowed'},status_code=403)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        return response

    @app.post('/api/commerce/checkout')
    def checkout(body: CheckoutRequest):
        try:return purchases.checkout(str(body.request_id),body.email,body.offer_id,body.seats)
        except HTTPException:raise
        except ValueError:raise HTTPException(400,'The selected purchase could not be prepared. Check the edition and seat count.') from None
        except Exception:raise HTTPException(503,'Checkout is temporarily unavailable. No purchase was confirmed.') from None

    @app.post('/api/commerce/webhook')
    async def webhook(request: Request):
        body=bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>1024*1024:raise HTTPException(413,'Webhook body too large')
        try:return purchases.webhook(bytes(body),request.headers.get('stripe-signature',''))
        except (ValueError,KeyError,TypeError):raise HTTPException(400,'Webhook could not be verified or matched.') from None
        except Exception:raise HTTPException(503,'Webhook processing was not confirmed. Retry delivery.') from None
    return app
