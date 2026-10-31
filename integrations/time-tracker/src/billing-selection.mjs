export function initialSeats(search) {
  const value = Number(new URLSearchParams(search).get('seats') || 1);
  return Number.isInteger(value) && value >= 1 && value <= 30 ? value : 1;
}

// Only checkout selection, never tokens or payment details, is stored here.
export function checkoutAttempt(storage, user, company, seats, uuid) {
  if (!Number.isInteger(seats) || seats < 1 || seats > 30) throw new Error('Select 1 to 30 users.');
  const key = `tracker-checkout:${user}:${company}`;
  let previous;
  try { previous = JSON.parse(storage.getItem(key)); } catch { /* empty or unavailable storage */ }
  if (previous?.seats === seats && /^[a-f0-9-]{36}$/i.test(previous.requestId || '')) return previous;
  const attempt = { seats, requestId: uuid() };
  try { storage.setItem(key, JSON.stringify(attempt)); } catch { /* server reservation still deduplicates */ }
  return attempt;
}

export function billingMessage(billing) {
  if (['active', 'trialing'].includes(billing?.status)) return 'Your Time Tracker workspace is active.';
  return 'Waiting for payment confirmation. You can refresh billing status without paying again.';
}
