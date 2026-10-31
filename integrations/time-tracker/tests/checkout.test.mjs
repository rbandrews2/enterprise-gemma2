import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import checkout from '../netlify/functions/create-checkout-session.mjs';
import webhook, { verifyStripeSignature, paidCompany, purchasedSeats } from '../netlify/functions/stripe-webhook.mjs';

const companyId = '11111111-1111-4111-8111-111111111111';
const requestId = '22222222-2222-4222-8222-222222222222';
const originalFetch = globalThis.fetch;
const originalNetlify = globalThis.Netlify;
afterEach(() => { globalThis.fetch = originalFetch; globalThis.Netlify = originalNetlify; });
function setup({ role = 'owner', existing = [], enabled = true, fail = false } = {}) {
  const values = { TRACKER_CHECKOUT_V2_ENABLED: String(enabled), STRIPE_MODE: 'test', STRIPE_SECRET_KEY: 'rk_test_synthetic',
    STRIPE_MONTHLY_PRICE_ID: 'price_base', STRIPE_EXTRA_USER_PRICE_ID: 'price_extra',
    SUPABASE_URL: 'https://synthetic.example', SUPABASE_ANON_KEY: 'synthetic',
    SUPABASE_SERVICE_ROLE_KEY: 'synthetic', SITE_URL: 'https://clock.superiorllc.org' };
  globalThis.Netlify = { env: { get: name => values[name] } };
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    if (fail) throw new Error('private upstream detail');
    if (url.endsWith('/auth/v1/user')) return Response.json({ id: 'user-test', email: 'synthetic@example.test' });
    if (url.endsWith('/rpc/tracker_reserve_checkout')) {
      const args = JSON.parse(options.body); return Response.json({ request_id: args.p_request, seats: args.p_seats });
    }
    if (url.includes('/memberships_2?')) return Response.json(role ? [{ role }] : []);
    if (url.includes('/company_billing_2?')) return Response.json(existing);
    if (url === 'https://api.stripe.com/v1/checkout/sessions') return Response.json({ livemode:false, url: 'https://checkout.stripe.com/c/pay/cs_test' });
    throw new Error('Unexpected request');
  };
  return calls;
}
function request(body = {}, authorized = true) {
  return new Request('https://clock.superiorllc.org/api/create-checkout-session', { method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(authorized ? { Authorization: 'Bearer synthetic' } : {}) },
    body: JSON.stringify({ companyId, requestId, seats: 1, ...body }) });
}
test('candidate remains disabled by default with no downstream work', async () => {
  const calls = setup({ enabled: false });
  assert.equal((await checkout(request())).status, 503); assert.equal(calls.length, 0);
});
test('anonymous purchase refused', async () => {
  const calls = setup(); assert.equal((await checkout(request({}, false))).status, 401); assert.equal(calls.length, 0);
});
for (const role of ['member', null]) test(`non-admin ${role} cannot start checkout`, async () => {
  const calls = setup({ role }); assert.equal((await checkout(request())).status, 403);
  assert.equal(calls.some(c => c.url.includes('api.stripe.com')), false);
});
for (const seats of [0, 31, 1.5, '2', null]) test(`invalid seat count ${seats} refused`, async () => {
  const calls = setup(); assert.equal((await checkout(request({ seats }))).status, 400);
  assert.equal(calls.some(c => c.url.includes('api.stripe.com')), false);
});
test('one seat has base only, no setup or zero-quantity line', async () => {
  const calls = setup(); const result = await checkout(request()); assert.equal(result.status, 200);
  assert.equal(result.headers.get('cache-control'), 'no-store');
  const call = calls.find(c => c.url.includes('api.stripe.com'));
  assert.equal(call.options.body.get('line_items[0][quantity]'), '1');
  assert.equal(call.options.body.has('line_items[1][price]'), false);
  assert.equal(calls.filter(c => c.url.includes('company_billing')).every(c => !c.options.method), true);
});
test('30 seats charge one base plus 29 extras and preserve company binding', async () => {
  const calls = setup(); assert.equal((await checkout(request({ seats: 30 }))).status, 200);
  const body = calls.find(c => c.url.includes('api.stripe.com')).options.body;
  assert.equal(body.get('line_items[1][price]'), 'price_extra');
  assert.equal(body.get('line_items[1][quantity]'), '29');
  assert.equal(body.get('subscription_data[metadata][seats]'), '30');
  assert.equal(body.get('client_reference_id'), companyId);
});
test('repeat attempt preserves idempotency key; changed quantities remain same attempt', async () => {
  const calls = setup(); await checkout(request()); await checkout(request()); await checkout(request({ seats: 2 }));
  const keys = calls.filter(c => c.url.includes('api.stripe.com')).map(c => c.options.headers['Idempotency-Key']);
  assert.equal(new Set(keys).size, 1); // Stripe refuses changed parameters for the same attempt.
});
test('existing subscription is not overwritten or charged again', async () => {
  const calls = setup({ existing: [{ status: 'past_due', stripe_subscription_id: 'sub_existing' }] });
  assert.equal((await checkout(request())).status, 409);
  assert.equal(calls.some(c => c.url.includes('api.stripe.com')), false);
});
test('upstream failures return safe retry text', async () => {
  setup({ fail: true }); const result = await checkout(request()); assert.equal(result.status, 503);
  assert.equal((await result.text()).includes('private upstream'), false);
});
const payload = '{"id":"evt_synthetic"}';
const now = 1800000000000;
function signature(t, data = payload) { return createHmac('sha256', 'synthetic').update(`${t}.${data}`).digest('hex'); }
test('signature supports rotated keys and rejects altered, stale and future payloads', () => {
  const t = now / 1000;
  assert.equal(verifyStripeSignature(payload, `t=${t},v1=${'0'.repeat(64)},v1=${signature(t)}`, 'synthetic', now), true);
  assert.equal(verifyStripeSignature(payload + ' ', `t=${t},v1=${signature(t)}`, 'synthetic', now), false);
  for (const delta of [-301, 301]) assert.equal(verifyStripeSignature(payload, `t=${t+delta},v1=${signature(t+delta)}`, 'synthetic', now), false);
  assert.equal(verifyStripeSignature(payload, `t=${t},t=${t},v1=${signature(t)}`, 'synthetic', now), false);
});
function paid() {
  const metadata = { company_id: companyId, product_id: 'prod_tracker' };
  return [{ livemode:false, mode: 'subscription', payment_status: 'paid', client_reference_id: companyId, metadata,
    subscription: 'sub_test', customer: 'cus_test' },
  { livemode:false, id: 'sub_test', customer: 'cus_test', status: 'active', metadata }];
}
test('paid session must match company, subscription, customer and product', () => {
  const [session, subscription] = paid();
  assert.equal(paidCompany(session, subscription, 'prod_tracker'), companyId);
  for (const patch of [{ payment_status: 'unpaid' }, { mode: 'payment' }, { customer: 'cus_other' }, { subscription: 'sub_other' }, { client_reference_id: requestId }]) {
    assert.equal(paidCompany({ ...session, ...patch }, subscription, 'prod_tracker'), null);
  }
  assert.equal(paidCompany(session, null, 'prod_tracker'), null);
  assert.equal(paidCompany(session, { ...subscription, status: 'incomplete' }, 'prod_tracker'), null);
  assert.equal(paidCompany(session, subscription, 'prod_wrong'), null);
});
test('disabled webhook does not acknowledge an event as fulfilled', async () => {
  const calls = setup({ enabled: false });
  assert.equal((await webhook(new Request('https://clock.superiorllc.org/api/stripe-webhook', { method: 'POST', body: payload }))).status, 503);
  assert.equal(calls.length, 0);
});

test('allowance comes from exact subscription price quantities, not metadata', () => {
  const make = data => ({ metadata: { seats: '300' }, items: { data, has_more: false } });
  const base = { price: { id: 'price_base' }, quantity: 1 };
  const extra = { price: { id: 'price_extra' }, quantity: 29 };
  assert.equal(purchasedSeats(make([base]), 'price_base','price_extra'), 1);
  assert.equal(purchasedSeats(make([base,extra]), 'price_base','price_extra'), 30);
  for (const items of [[extra], [base,base], [base,{...extra, quantity:30}], [base,{...extra,price:'price_other'}]]) {
    assert.equal(purchasedSeats(make(items),'price_base','price_extra'), null);
  }
  assert.equal(purchasedSeats({ items:{data:[base],has_more:true}},'price_base','price_extra'), null);
});

for (const scenario of ['paid','unpaid','event-live','session-live','subscription-live']) test(`signed ${scenario} event preserves payment environment and entitlement`,async()=>{
  const payment=scenario==='unpaid'?'unpaid':'paid';
  const values={TRACKER_CHECKOUT_V2_ENABLED:'true',STRIPE_MODE:'test',STRIPE_SECRET_KEY:'rk_test_synthetic',STRIPE_WEBHOOK_SECRET:'synthetic',
    STRIPE_PRODUCT_ID:'prod_tracker',STRIPE_MONTHLY_PRICE_ID:'price_base',STRIPE_EXTRA_USER_PRICE_ID:'price_extra',
    SUPABASE_URL:'https://synthetic.example',SUPABASE_SERVICE_ROLE_KEY:'synthetic'};
  globalThis.Netlify={env:{get:key=>values[key]}};
  const [session,subscription]=paid();
  Object.assign(session,{id:'cs_test',payment_status:payment});
  const metadata={company_id:companyId,product_id:'prod_tracker',request_id:requestId,seats:'2',integration:'tracker-v2'};
  session.metadata=metadata;subscription.metadata=metadata;
  subscription.items={has_more:false,data:[{price:{id:'price_base'},quantity:1},{price:{id:'price_extra'},quantity:1}]};
  if(scenario==='session-live') session.livemode=true;
  if(scenario==='subscription-live') subscription.livemode=true;
  const writes=[];
  globalThis.fetch=async(url,options={})=>{
    if(url.endsWith('/checkout/sessions/cs_test')) return Response.json(session);
    if(url.endsWith('/subscriptions/sub_test')) return Response.json(subscription);
    if(url.endsWith('/rpc/tracker_apply_billing_event')) { writes.push(JSON.parse(options.body));return Response.json('applied'); }
    throw new Error('Unexpected request');
  };
  const t=Math.floor(Date.now()/1000);
  const body=JSON.stringify({id:'evt_test',livemode:scenario==='event-live',created:t,type:'checkout.session.completed',data:{object:{id:'cs_test'}}});
  const result=await webhook(new Request('https://clock.superiorllc.org/api/stripe-webhook',{method:'POST',body,
    headers:{'stripe-signature':`t=${t},v1=${signature(t,body)}`}}));
  assert.equal(result.status,scenario==='event-live'?400:scenario.endsWith('-live')?500:200);
  assert.equal(writes.length,scenario==='paid'?1:0);
  if(writes.length) {assert.equal(writes[0].p_seats,2);assert.equal(writes[0].p_request,requestId);assert.equal(writes[0].p_initial,true);}
});

 test('Stripe mode must be explicit and match the API key before any downstream work',async()=>{
  for(const mode of [undefined,'live','unexpected']) {
   const calls=setup();const original=globalThis.Netlify.env.get;
   globalThis.Netlify.env.get=key=>key==='STRIPE_MODE'?mode:original(key);
   assert.equal((await checkout(request())).status,503);assert.equal(calls.length,0);
  }
 });
