// Explicit environment binding prevents sandbox events from granting live access.
export function stripeLiveMode(mode, key) {
  if (!['test', 'live'].includes(mode) || typeof key !== 'string' ||
      !new RegExp(`^(?:rk|sk)_${mode}_[A-Za-z0-9]+$`).test(key)) {
    throw new Error('Stripe environment is not configured consistently');
  }
  return mode === 'live';
}

export function requireStripeMode(object, live) {
  if (object?.livemode !== live) throw new Error('Stripe object environment mismatch');
  return object;
}

export function checkoutReturnOrigin(siteUrl, live, testOrigin) {
  const parsed = new URL(siteUrl);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password ||
      parsed.search || parsed.hash || !['', '/'].includes(parsed.pathname) ||
      /\s/.test(siteUrl) || (parsed.port && parsed.port !== '443')) {
    throw new Error('Invalid checkout return origin');
  }
  const production = 'https://clock.superiorllc.org';
  if (live ? (parsed.origin !== production || testOrigin) :
      (testOrigin ? parsed.origin !== testOrigin || parsed.origin === production : parsed.origin !== production)) {
    throw new Error('Checkout return origin does not match its environment');
  }
  return parsed.origin;
}
