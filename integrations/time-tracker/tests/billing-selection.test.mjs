import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initialSeats,checkoutAttempt,billingMessage } from '../src/billing-selection.mjs';
test('URL accepts only 1-30 whole users',()=>{
  assert.equal(initialSeats('?seats=30'),30);
  for(const input of ['0','31','1.5','nope']) assert.equal(initialSeats(`?seats=${input}`),1);
});
test('attempt persists per user/company and changes only with selection',()=>{
  const values=new Map();const storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)};
  let n=0;const uuid=()=>`${String(++n).padStart(8,'0')}-1111-4111-8111-111111111111`;
  const a=checkoutAttempt(storage,'u','c',2,uuid);
  assert.deepEqual(checkoutAttempt(storage,'u','c',2,uuid),a);
  assert.notDeepEqual(checkoutAttempt(storage,'u','other',2,uuid),a);
  assert.notDeepEqual(checkoutAttempt(storage,'u','c',3,uuid),a);
});
test('URL return never implies payment',()=>{
  assert.match(billingMessage(null),/Waiting/);
  assert.match(billingMessage({status:'pending'}),/Waiting/);
  assert.match(billingMessage({status:'active'}),/workspace is active/);
});
