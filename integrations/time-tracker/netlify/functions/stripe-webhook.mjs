import { createHmac, timingSafeEqual } from 'node:crypto';

const env = (key) => Netlify.env.get(key);

const stripeGet = async (path, secretKey) => {
  const response = await fetch(`https://api.stripe.com/v1${path}`, {
    signal: AbortSignal.timeout(10000),
    headers: { Authorization: `Bearer ${secretKey}` },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message ?? 'Stripe request failed.');
  }

  return data;
};

export const verifyStripeSignature = (payload, signatureHeader, secret, now = Date.now()) => {
  if (!signatureHeader || !secret) return false;
  const parts = signatureHeader.split(',').map(part => part.trim().split('='));
  const timestamps = parts.filter(([key]) => key === 't').map(([, value]) => value);
  if (timestamps.length !== 1 || !/^\d+$/.test(timestamps[0])) return false;
  const timestamp = Number(timestamps[0]);
  if (!Number.isSafeInteger(timestamp) || Math.abs(now / 1000 - timestamp) > 300) return false;
  const expected = createHmac('sha256', secret).update(`${timestamps[0]}.${payload}`).digest();
  return parts.filter(([key]) => key === 'v1').some(([, value]) => {
    if (!/^[a-f0-9]{64}$/i.test(value || '')) return false;
    return timingSafeEqual(Buffer.from(value, 'hex'), expected);
  });
};

export const paidCompany = (session, subscription, productId) => {
  const companyId = session.client_reference_id;
  const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
  if (session.mode !== 'subscription' || session.payment_status !== 'paid' ||
      !uuid.test(companyId || '') || session.metadata?.company_id !== companyId ||
      !subscription || subscription.id !== session.subscription ||
      subscription.customer !== session.customer || subscription.status !== 'active' ||
      subscription.metadata?.company_id !== companyId ||
      session.metadata?.product_id !== productId || subscription.metadata?.product_id !== productId) return null;
  return companyId;
};

const supabaseRequest = async (path, options = {}) => {
  const supabaseUrl = env('SUPABASE_URL') || env('VITE_SUPABASE_URL');
  const serviceKey = env('SUPABASE_SERVICE_ROLE_KEY');

  const response = await fetch(`${supabaseUrl}/rest/v1${path}`, {
    ...options,
    signal: AbortSignal.timeout(10000),
    headers: {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      'Content-Type': 'application/json',
      Prefer: 'return=representation',
      ...(options.headers ?? {}),
    },
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(data?.message ?? 'Supabase request failed.');
  }
  return data;
};

const upsertBilling = async ({
  companyId,
  customerId,
  subscriptionId,
  productId,
  status,
  currentPeriodEnd,
}) => {
  if (!companyId) return;

  await supabaseRequest('/company_billing_2?on_conflict=company_id', {
    method: 'POST',
    signal: AbortSignal.timeout(10000),
    headers: { Prefer: 'resolution=merge-duplicates,return=representation' },
    body: JSON.stringify({
      company_id: companyId,
      stripe_customer_id: customerId,
      stripe_subscription_id: subscriptionId,
      stripe_product_id: productId || 'prod_USsnAqnFjc2KIa',
      status,
      current_period_end: currentPeriodEnd
        ? new Date(currentPeriodEnd * 1000).toISOString()
        : null,
    }),
  });
};

export default async (req) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed.', { status: 405 });
  }

  if (env('TRACKER_CHECKOUT_V2_ENABLED') !== 'true') {
    return new Response('Checkout update is not active yet.', { status: 503 });
  }
  const stripeSecretKey = env('STRIPE_SECRET_KEY');
  const webhookSecret = env('STRIPE_WEBHOOK_SECRET');
  const payload = await req.text();

  if (!verifyStripeSignature(payload, req.headers.get('stripe-signature'), webhookSecret)) {
    return new Response('Invalid signature.', { status: 400 });
  }

  let event;
  try { event = JSON.parse(payload); } catch { return new Response('Invalid event.', { status: 400 }); }

  try {
    if (['checkout.session.completed', 'checkout.session.async_payment_succeeded'].includes(event.type)) {
      const sessionId = event.data?.object?.id;
      if (!/^cs_[a-zA-Z0-9_]+$/.test(sessionId || '')) return new Response('Invalid session.', { status: 400 });
      const session = await stripeGet(`/checkout/sessions/${sessionId}`, stripeSecretKey);
      const subscription = session.subscription
        ? await stripeGet(`/subscriptions/${session.subscription}`, stripeSecretKey)
        : null;

      const companyId = paidCompany(session, subscription, env('STRIPE_PRODUCT_ID') || 'prod_USsnAqnFjc2KIa');
      if (!companyId) return new Response('No paid entitlement to activate.');
      await upsertBilling({
        companyId,
        customerId: session.customer,
        subscriptionId: session.subscription,
        productId: session.metadata?.product_id,
        status: subscription.status,
        currentPeriodEnd: subscription?.current_period_end,
      });
    }

    if (
      event.type === 'customer.subscription.updated' ||
      event.type === 'customer.subscription.deleted'
    ) {
      const incoming = event.data?.object;
      if (!/^sub_[a-zA-Z0-9]+$/.test(incoming?.id || '')) return new Response('Invalid subscription.', { status: 400 });
      // Re-read current state instead of replaying an older event snapshot.
      const subscription = await stripeGet(`/subscriptions/${incoming.id}`, stripeSecretKey);
      const productId = env('STRIPE_PRODUCT_ID') || 'prod_USsnAqnFjc2KIa';
      const companyId = subscription.metadata?.company_id;
      if (!companyId || subscription.metadata?.product_id !== productId) return new Response('Unrelated subscription.');
      const existing = await supabaseRequest(
        `/company_billing_2?select=stripe_subscription_id&company_id=eq.${encodeURIComponent(companyId)}&limit=1`
      );
      // Updates cannot create the initial paid entitlement or replace another subscription.
      if (existing?.[0]?.stripe_subscription_id !== subscription.id) return new Response('Unlinked subscription.');
      const knownStatuses = ['active', 'trialing', 'past_due', 'canceled', 'unpaid'];
      if (!knownStatuses.includes(subscription.status)) subscription.status = 'inactive';
      await upsertBilling({
        companyId: subscription.metadata?.company_id,
        customerId: subscription.customer,
        subscriptionId: subscription.id,
        productId: subscription.metadata?.product_id,
        status: subscription.status,
        currentPeriodEnd: subscription.current_period_end,
      });
    }
  } catch (error) {
    return new Response('Billing processing failed. Retry this event.', { status: 500 });
  }

  return new Response('ok');
};

export const config = {
  path: '/api/stripe-webhook',
  method: ['POST'],
};
