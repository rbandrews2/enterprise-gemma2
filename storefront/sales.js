(() => {
  const $ = s => document.querySelector(s);
  const seats = $('#seats'), billing = $('#billing');
  const money = cents => new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(cents/100);
  const edition = () => document.querySelector('input[name="edition"]:checked').value;
  const item = () => WZOS_CATALOG[edition()];
  let preferredBilling = 'monthly';
  function render() {
    const n = Number(seats.value);
    if (item().max === 30 && Number.isInteger(n) && n > 30 && n <= 5000) $('#ed-enterprise').checked = true;
    const product = item(), custom = edition() === 'enterprise' && n > 30, valid = Number.isInteger(n) && n >= 1 && n <= (product.max || 5000);
    seats.max = 5000;
    const annual = preferredBilling === 'annual' && !!product.annual, price = annual ? product.annual : product.monthly;
    billing.disabled = !product.annual;
    billing.querySelector('option[value="annual"]').disabled = !product.annual;
    billing.value = annual ? 'annual' : 'monthly';
    $('#bill-monthly').setAttribute('aria-pressed', String(preferredBilling === 'monthly'));
    $('#bill-annual').setAttribute('aria-pressed', String(preferredBilling === 'annual'));
    for (const key of ['core','enterprise']) { const card = document.querySelector('[data-price="'+key+'"]'); const yearly = preferredBilling === 'annual'; card.textContent = money(WZOS_CATALOG[key][yearly ? 'annual' : 'monthly'].cents); card.nextElementSibling.textContent = yearly ? 'per organization / year · billed yearly' : 'per organization / month'; }
    $('#sum-edition').textContent = product.name;
    $('#sum-seats').textContent = valid ? n : `Enter 1–${seats.max}`;
    $('#sum-billing').textContent = annual ? 'Annual — billed yearly' : 'Monthly';
    $('#sum-unit').textContent = custom ? 'Custom Enterprise pricing' : price ? `${money(price.cents)} / ${annual ? 'year · billed yearly' : 'month'} base` : 'Custom quote';
    const extras = product.model === 'organization' ? Math.max(0,n-product.included) * (annual ? price.extraCents : product.extraCents) : 0;
    $('#sum-total').textContent = custom ? 'Custom Enterprise quote' : product.model === 'organization' && valid ? `${money(price.cents + extras + (product.setupCents || 0))}${!product.setupCents ? ' / month' : ' incl. setup'}` : 'Quoted by sales';
    $('#sum-total-label').textContent = custom ? 'Enterprise quote' : !product.setupCents ? 'Monthly subscription subtotal' : 'First invoice subtotal';
    for (const key of ['core','enterprise']) { const p=WZOS_CATALOG[key],a=preferredBilling==='annual'; document.querySelector('[data-plan-detail="'+key+'"]').textContent = p.included+' active logins included. '+money(a?p.annual.extraCents:p.extraCents)+' per additional login/'+(a?'year':'month')+(a?' · billed yearly':'')+'; '+money(p.setupCents)+' one-time setup. '+(key==='core'?'Up to 30 total users.':'Above 30 users: custom pricing. Eligible Core upgrades receive a one-time $20 credit.'); }
    $('#sum-link').textContent = 'WZOS order review';
    $('#submit-btn').textContent = product.selfServe ? 'Review order' : 'Review rollout request';
    $('#placeholder-notice').hidden = true;
    if (annual && !custom) { $('#placeholder-notice').textContent = `${money(price.cents)} base, billed yearly, includes ${product.included} logins. Additional logins are ${money(price.extraCents)} each/year (${money(extras)}/year for this selection). The first invoice includes the annual base, annual additional logins and one-time setup.`; $('#placeholder-notice').hidden = false; }
    if (preferredBilling === 'annual' && !product.annual) { $('#placeholder-notice').textContent = 'Time Tracker is available with monthly billing. Annual billing applies to Core and Enterprise.'; $('#placeholder-notice').hidden = false; }
    if (custom) { $('#placeholder-notice').textContent = 'More than 30 users: Enterprise selected for custom pricing. Your user count is preserved.'; $('#placeholder-notice').hidden = false; }
  }
  $('#bill-monthly').addEventListener('click', () => { preferredBilling = 'monthly'; render(); });
  $('#bill-annual').addEventListener('click', () => { preferredBilling = 'annual'; render(); });
  billing.addEventListener('change', () => { preferredBilling = billing.value; render(); });
  document.querySelectorAll('input[name="edition"]').forEach(r=>r.addEventListener('change',render));
  seats.addEventListener('input',render);
  $('#seat-down').addEventListener('click',()=>{seats.value=Math.max(1,(Number(seats.value)||1)-1);render()});
  $('#seat-up').addEventListener('click',()=>{seats.value=Math.min(5000,(Number(seats.value)||0)+1);render()});
  document.querySelectorAll('[data-pick]').forEach(a=>a.addEventListener('click',()=>{const r=document.getElementById('ed-'+a.dataset.pick);if(r){r.checked=true;render()}}));
  $('#order-form').addEventListener('submit',e=>{
    e.preventDefault();
    const n=Number(seats.value), product=item(), err=$('#form-error');
    if(!Number.isInteger(n)||n<1||n>(product.max||5000)){err.textContent=`Enter a whole number of active logins from 1 to ${product.max||5000}.`;err.hidden=false;return;}
    err.hidden=true;
    const url=new URL('checkout.html',location.href);
    url.searchParams.set('product',edition());url.searchParams.set('billing',billing.value);url.searchParams.set('quantity',String(n));
    location.href=url.href;
  });
  document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',()=>{const done=()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy email',1600)};try{navigator.clipboard.writeText(b.dataset.copy).then(done,()=>b.textContent='Select the email to copy')}catch{b.textContent='Select the email to copy'}}));
  render();
})();

