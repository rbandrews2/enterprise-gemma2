import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkoutReturnOrigin } from '../src/stripe-mode.mjs';
const stage = 'https://tracker-acceptance.example.test';
test('explicit test return is isolated; live return stays fixed', () => {
  assert.equal(checkoutReturnOrigin(stage + '/', false, stage), stage);
  assert.equal(checkoutReturnOrigin('https://clock.superiorllc.org', true), 'https://clock.superiorllc.org');
  assert.throws(() => checkoutReturnOrigin(stage, true, stage));
  assert.throws(() => checkoutReturnOrigin(stage, false));
  assert.throws(() => checkoutReturnOrigin('https://clock.superiorllc.org', false, stage));
});
test('credentials, paths and redirects cannot enter return-origin configuration', () => {
  for (const url of ['http://tracker-acceptance.example.test', stage+'?next=x', stage+'/#x',
    stage+'/path', 'https://user:pass@tracker-acceptance.example.test', stage+':8443', ' '+stage]) {
    assert.throws(() => checkoutReturnOrigin(url, false, stage));
  }
});
