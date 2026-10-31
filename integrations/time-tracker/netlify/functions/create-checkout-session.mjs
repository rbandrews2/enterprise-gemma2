import { createHash } from 'node:crypto';
const stripeApi = async (path, body, secretKey, idempotencyKey) => {
  const response = await fetch(`https://api.stripe.com/v1${path}`, {
    method: 'POST',
    signal: AbortSignal.timeout(10000),
    headers: {
      Authorization: `Bearer ${secretKey}`,
      'Content-Type': 'application/x-www-form-urlencoded',
      'Idempotency-Key': idempotencyKey,
    },
    body: new URLSearchParams(body),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message ?? 'Stripe request failed.');
  }

  return data;
};

const env = (key) => Netlify.env.get(key);

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });

const getSupabaseUser = async (supabaseUrl, anonKey, token) => {
  const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
    signal: AbortSignal.timeout(10000),
    headers: {
      apikey: anonKey,
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) return null;
  return response.json();
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

const handle = async (req) => {
  if (req.method !== 'POST') {
    return json({ error: 'Method not allowed.' }, 405);
  }

  const stripeSecretKey = env('STRIPE_SECRET_KEY');
  // Separate candidate stays disabled until its database and client gates pass.
  if (env('TRACKER_CHECKOUT_V2_ENABLED') !== 'true') {
    return json({ error: 'Checkout update is not active yet.' }, 503);
  }
  const extraPriceId = env('STRIPE_EXTRA_USER_PRICE_ID');
  const monthlyPriceId = env('STRIPE_MONTHLY_PRICE_ID');
  const supabaseUrl = env('SUPABASE_URL') || env('VITE_SUPABASE_URL');
  const supabaseAnonKey = env('SUPABASE_ANON_KEY') || env('VITE_SUPABASE_ANON_KEY');
  const siteUrl = env('SITE_URL') || 'https://clock.superiorllc.org';
  const productId = env('STRIPE_PRODUCT_ID') || 'prod_USsnAqnFjc2KIa';

  if (!stripeSecretKey || !extraPriceId || !monthlyPriceId || !supabaseUrl || !supabaseAnonKey || !env('SUPABASE_SERVICE_ROLE_KEY')) {
    return json({ error: 'Billing is not fully configured.' }, 500);
  }

  const authHeader = req.headers.get('authorization') ?? '';
  const token = authHeader.replace(/^Bearer\s+/i, '');
  if (!token) {
    return json({ error: 'Missing Supabase session.' }, 401);
  }

  const user = await getSupabaseUser(supabaseUrl, supabaseAnonKey, token);
  if (!user?.id) {
    return json({ error: 'Invalid Supabase session.' }, 401);
  }

  let input;
  try { input = await req.json(); } catch { return json({ error: 'Invalid checkout request.' }, 400); }
  const { companyId, seats, requestId } = input || {};
  const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
  if (!uuid.test(companyId || '') || !uuid.test(requestId || '') ||
      !Number.isInteger(seats) || seats < 1 || seats > 30) {
    return json({ error: 'Select 1 to 30 users and retry checkout.' }, 400);
  }
  if (new URL(siteUrl).origin !== 'https://clock.superiorllc.org') {
    return json({ error: 'Checkout is not configured.' }, 503);
  }

  const membership = await supabaseRequest(
    `/memberships_2?select=role&company_id=eq.${encodeURIComponent(companyId)}&user_id=eq.${encodeURIComponent(user.id)}&limit=1`
  );

  if (!membership?.[0] || !['owner', 'admin'].includes(membership[0].role)) {
    return json({ error: 'Only a company admin can start billing.' }, 403);
  }

  const existing = await supabaseRequest(
    `/company_billing_2?select=status,stripe_subscription_id&company_id=eq.${encodeURIComponent(companyId)}&limit=1`
  );
  if (existing?.[0]?.stripe_subscription_id || ['active', 'trialing'].includes(existing?.[0]?.status)) {
    return json({ error: 'This company already has billing. Manage the existing subscription.' }, 409);
  }
  // Never reset an existing company's entitlement to pending during checkout.
  const idempotencyKey = createHash('sha256')
    .update(JSON.stringify([companyId, user.id, requestId])).digest('hex');

  const session = await stripeApi(
    '/checkout/sessions',
    {
      mode: 'subscription',
      success_url: `${siteUrl}/?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}/?checkout=cancelled`,
      client_reference_id: companyId,
      customer_email: user.email ?? '',
      'line_items[0][price]': monthlyPriceId,
      'line_items[0][quantity]': '1',
      ...(seats > 1 ? { 'line_items[1][price]': extraPriceId, 'line_items[1][quantity]': String(seats - 1) } : {}),
      'metadata[seats]': String(seats),
      'metadata[integration]': 'tracker-v2',
      'metadata[company_id]': companyId,
      'metadata[user_id]': user.id,
      'metadata[product_id]': productId,
      'subscription_data[metadata][seats]': String(seats),
      'subscription_data[metadata][integration]': 'tracker-v2',
      'subscription_data[metadata][company_id]': companyId,
      'subscription_data[metadata][product_id]': productId,
    },
    stripeSecretKey, idempotencyKey
  );

  if (!session.url || new URL(session.url).origin !== 'https://checkout.stripe.com') {
    return json({ error: 'Unable to open secure checkout.' }, 502);
  }
  return json({ url: session.url });
};

export default async (req) => {
  try { return await handle(req); }
  catch { return json({ error: 'Checkout is temporarily unavailable. Please try again.' }, 503); }
};

export const config = {
  path: '/api/create-checkout-session',
  method: ['POST'],
};
