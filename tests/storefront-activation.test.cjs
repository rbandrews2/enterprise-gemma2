const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function page(search){
 const nodes=new Map();const get=id=>{if(!nodes.has(id))nodes.set(id,{value:'',hidden:false,disabled:false,textContent:'',handlers:{},addEventListener(k,f){this.handlers[k]=f},querySelector(){return {}},replaceChildren(){}});return nodes.get(id)};
 const context={URL,URLSearchParams,Intl,location:{search,href:'https://store.example/checkout.html'+search},document:{getElementById:get,createElement:()=>({})}};
 vm.createContext(context);for(const name of ['catalog.js','checkout.js'])vm.runInContext(fs.readFileSync('storefront/'+name,'utf8'),context);
 return {get,submit(){get('checkout-form').handlers.submit({preventDefault(){}});return context.location.href}};
}
for(const [product,billing,seats,offer] of [['core','monthly',17,'core'],['core','annual',20,'core_annual'],['enterprise','annual',29,'enterprise_annual']])test('storefront transfers '+offer+' selection without exposing activation codes',()=>{
 const p=page(`?product=${product}&billing=${billing}&quantity=${seats}`),u=new URL(p.submit());
 assert.equal(u.origin,'https://app.workzoneos.org');assert.equal(u.searchParams.get('offer'),offer);assert.equal(u.searchParams.get('seats'),String(seats));assert.equal(u.searchParams.has('activation_code'),false);
});
test('custom team never starts ordinary checkout',()=>{const p=page('?product=core&quantity=40');assert.equal(new URL(p.submit()).hash,'#contact');});
test('standalone tracker stays separate and does not claim automated WZOS activation',()=>{const p=page('?product=tracker&quantity=3');assert.match(p.get('payment-note').textContent,/not automated/);assert.equal(new URL(p.submit()).hostname,'checkout.superiorllc.org');});
