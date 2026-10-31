(() => {
  const $ = id => document.getElementById(id), catalog = globalThis.WZOS_CATALOG;
  const params = new URLSearchParams(location.search);
  $('product').value = Object.prototype.hasOwnProperty.call(catalog, params.get('product')) ? params.get('product') : 'core';
  $('billing').value = params.get('billing') === 'annual' ? 'annual' : 'monthly';
  const requested = Number(params.get('quantity') || ($('product').value === 'tracker' ? 1 : 15));
  $('quantity').value = Number.isInteger(requested) && requested >= 1 && requested <= 5000 ? requested : 1;
  const money = cents => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(cents/100);
  function item(){ return catalog[$('product').value]; }
  function selection(){const product=item(),n=Number($('quantity').value),annual=$('billing').value==='annual'&&!!product.annual;return {product,n,annual,price:annual?product.annual:product.monthly,valid:Number.isInteger(n)&&n>=1&&n<=5000,custom:product===catalog.enterprise&&n>30};}
  function safeLink(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&u.hostname==='checkout.superiorllc.org'&&u.pathname.startsWith('/b/')?u:null;}catch{return null;}}
  function render(){
    const n=Number($('quantity').value);
    if(item().max===30&&Number.isInteger(n)&&n>30&&n<=5000)$('product').value='enterprise';
    if(!item().annual)$('billing').value='monthly';
    const {product,price,annual,valid,custom}=selection(),period=annual?'year':'month';
    const extras=Math.max(0,n-product.included),extraRate=annual?price.extraCents:product.extraCents;
    const extraCents=extras*extraRate,recurring=price.cents+extraCents;
    $('quantity').max=5000;
    $('name').textContent=product.name;
    $('description').textContent=product.description;
    const features=custom?['Custom user allowance','Custom billing and deployment scope']:[product.included+' users included',money(extraRate)+' per additional user/'+period,...(product.setupCents?[money(product.setupCents)+' one-time setup']:[]),...(product===catalog.enterprise?['Eligible Core upgrades: one-time $20 credit arranged with sales']:[])];
    $('features').replaceChildren(...features.map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));
    $('sum-quantity').textContent=valid?n:'Enter 1–5000';
    $('billing').disabled=!product.annual;
    $('billing').querySelector('option[value="annual"]').disabled=!product.annual;
    $('quote-note').hidden=!custom;
    $('sum-billing').textContent=custom?'Custom proposal':annual?'Annual — billed yearly':'Monthly';
    $('unit-label').textContent=`Organization base / ${period}`;
    $('unit').textContent=custom?'Custom pricing':`${money(price.cents)} / ${period}${annual?" · billed yearly":""}`;
    $('extras-row').hidden=custom;
    $('extras').textContent=valid?`${extras} × ${money(extraRate)} = ${money(extraCents)} / ${period}`:'Check user count';
    $('setup-row').hidden=custom||!product.setupCents;
    $('setup').textContent=money(product.setupCents||0);
    $('recurring-row').hidden=custom;
    $('recurring').textContent=valid?`${money(recurring)} / ${period}${annual?" · billed yearly":""}`:'Check user count';
    $('total-label').textContent='Estimated first invoice';
    $('total').textContent=custom?'Custom Enterprise quote':valid?money(recurring+(product.setupCents||0)):'Check user count';
    $('renewal').textContent=custom?'More than 30 users requires a custom Enterprise proposal.':`${money(price.cents)} per ${period} includes ${product.included} ${product.included===1?'user':'users'}. Additional users cost ${money(extraRate)} each/${period}. ${product.setupCents?'One-time organization setup is '+money(product.setupCents)+'. ':''}${annual?'Billed yearly, including additional users. Your subscription renews annually.':'Your subscription renews monthly.'}`;
    const automated=product!==catalog.tracker;
    const ready=automated||!!safeLink(price.link);
    $('continue').disabled=!valid||(!custom&&!ready);
    $('continue').textContent=custom?'Contact sales for custom pricing':ready?(automated?'Continue to WZOS checkout':'Continue to Stripe'):'Checkout connection pending';
    $('status').textContent=automated&&!custom?'Sign in or create your WZOS account, review this selection, then pay securely on Stripe. Your activation code is filled in after payment is confirmed.':custom?'Your user count is preserved. Contact sales to scope your Enterprise deployment.':`On Stripe, set the ${money(extraRate)} additional-user line to ${extras} ${extras===1?'user':'users'}. ${extras===0?'Remove that line (quantity 0); your included users are covered by the base subscription.':'Keep the organization base at quantity 1.'}`;
    $('payment-note').textContent=custom?'No inquiry is sent automatically.':automated?'Use the same WZOS account when you return from payment. No payment is submitted on this page.':'Stand-alone Time Tracker activation is separate and is not automated by this checkout yet. Confirm additional-user quantity on Stripe.';
    $('error').hidden=valid;$('error').textContent='Enter a whole number of users from 1 to 5000.';
  }
  $('checkout-form').addEventListener('input',render);
  $('checkout-form').addEventListener('change',render);
  $('checkout-form').addEventListener('submit',event=>{event.preventDefault();const s=selection();if(!s.valid)return;if(s.custom){location.href=new URL('index.html#contact',location.href).href;return;}if(s.product!==catalog.tracker){const url=new URL('https://app.workzoneos.org/');url.searchParams.set('offer',$('product').value+(s.annual?'_annual':''));url.searchParams.set('seats',String(s.n));location.href=url.href;return;}const url=safeLink(s.price.link);if(url)location.href=url.href;});
  render();
})();
