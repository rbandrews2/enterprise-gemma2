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
