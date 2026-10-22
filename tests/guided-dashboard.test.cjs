const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const flush=()=>new Promise(r=>setImmediate(r));
function setup(role='admin',edition='enterprise',responses={}){
 class Node{constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.dataset={};this.open=false;this.hidden=false;}append(...n){this.children.push(...n);}prepend(...n){this.children.unshift(...n);}replaceChildren(...n){this.children=n;}setAttribute(k,v){this[k]=v;}addEventListener(){}showModal(){this.open=true;}close(){this.open=false;}remove(){this.removed=true;}click(){return this.onclick?.();}querySelector(s){return all(this).find(n=>s===n.tag||s==='.'+n.className)||null;}}
 const all=n=>[n,...n.children.flatMap(all)],main=new Node('main'),nav=new Node('nav'),body=new Node('body'),events={},calls=[],requests=[],clicks=[];let session={role,edition,id:'synthetic-admin',organization_id:'synthetic-org'};
 const emit=(e,detail)=>{for(const f of events[e]||[])f({detail});};
 main.id='main';const document={body,createElement:t=>new Node(t),createTextNode:t=>new Node('text',t),getElementById:id=>all(main).concat(all(nav)).find(n=>n.id===id)||{click(){clicks.push(id);}},querySelector:s=>s.startsWith('nav')?nav:null,addEventListener:(e,f)=>(events[e]??=[]).push(f)};
 const data={organization:'Synthetic organization',status:'amber',checks:[],modules:[{id:'clock',label:'Time Tracker',icon:'bolt',nav_id:'clock-nav',visible:true},{id:'report',label:'Work Zone Report',icon:'report',nav_id:'report-nav',visible:edition==='enterprise'}],notes:[]};
 const window={wzosClock:{getSession:()=>session,api:async (path,options)=>{calls.push(path);requests.push({path,options});return typeof responses[path]==='function'?responses[path](options):(responses[path]||data);}},showWzosView:view=>emit('wzos:view',view),addEventListener(){}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/organization-hub.js','utf8'),{window,document,confirm:()=>false,crypto:{randomUUID:()=> 'synthetic'},Date,URL,Intl});
 return{main,nav,body,all,emit,calls,requests,clicks,change:(role,edition)=>{session={...session,role,edition};emit('wzos:session');}};
}
test('guided landing uses authorized module data and working navigation',async()=>{
 const h=setup();h.emit('wzos:session');await flush();assert.equal(h.calls.length,1);
 assert.ok(h.all(h.main).some(n=>n.textContent==='Synthetic organization'));
 assert.ok(h.all(h.main).some(n=>n.textContent==='Your operation. In clear view.'));
 assert.equal(h.all(h.main).some(n=>n.textContent==='Work Zone Report'),false);
 const clock=h.all(h.main).find(n=>n.children?.some(c=>c.textContent==='Time Tracker'));assert.ok(clock);clock.onclick();assert.deepEqual(h.clicks,['clock-nav']);
 assert.equal(h.all(h.main).some(n=>/Status checks incomplete|No current verified|Security signals/.test(n.textContent)),false);
 assert.equal(h.all(h.main).find(n=>n.textContent==='Synthetic organization').className,'organization-heading');
});
test('Core upgrade is admin-only and closes on session changes without starting payment',async()=>{
 const h=setup('admin','core');h.emit('wzos:session');await flush();const upgrade=h.all(h.nav).find(n=>n.id==='core-upgrade');assert.equal(upgrade.hidden,false);upgrade.onclick();
 const dialog=h.body.children.at(-1);assert.equal(dialog.open,true);assert.ok(h.all(dialog).some(n=>n.textContent.includes('one-time $20 upgrade credit')));
 assert.equal(h.calls.filter(p=>p.includes('checkout')).length,0);h.change('member','core');assert.equal(upgrade.hidden,true);assert.equal(dialog.open,false);const count=h.body.children.length;upgrade.onclick();assert.equal(h.body.children.length,count);
 assert.equal(h.all(h.main).some(n=>n.textContent==='Synthetic organization'),false);
});

test('Core admin landing has an upgrade launch card even when the mobile menu is hidden',async()=>{
 const h=setup('admin','core');h.emit('wzos:session');await flush();
 const card=h.all(h.main).find(n=>n.className==='panel hub-card'&&n.children.some(c=>c.textContent==='Explore Enterprise'));
 assert.ok(card);await card.click();assert.equal(h.body.children.at(-1).open,true);
 assert.equal(h.requests.some(r=>r.path.endsWith('/confirm')),false);
});

test('estimate requires explicit consent before confirming and resumes the same invoice',async()=>{
 const quote={status:'quoted',request_id:'synthetic-quote',quote:{amount_due_cents:102900,monthly_cents:24900,seats:25,expires_at:Date.now()/1000+600}};
 const h=setup('admin','core',{'/api/account/upgrade':{enabled:true,status:'available'},'/api/account/license':{seat_limit:15,seats_used:2},'/api/account/upgrade/quote':quote,'/api/account/upgrade/confirm':{status:'pending',request_id:'synthetic-quote',payment_url:'https://invoice.stripe.com/i/synthetic'}});
 h.emit('wzos:session');await flush();await h.all(h.nav).find(n=>n.id==='core-upgrade').click();
 const dialog=h.body.children.at(-1),find=t=>h.all(dialog).find(n=>n.textContent===t);
 await find('Review upgrade estimate').click();const pay=find('Confirm upgrade and pay');
 await pay.click();assert.equal(h.calls.includes('/api/account/upgrade/confirm'),false);
 const consent=h.all(dialog).find(n=>n.tag==='input'&&n.type==='checkbox');consent.checked=true;consent.onchange();await pay.click();
 const sent=JSON.parse(h.requests.find(r=>r.path==='/api/account/upgrade/confirm').options.body);
 assert.deepEqual(sent,{request_id:'synthetic-quote',confirmed:true});
 assert.equal(find('Continue payment securely with Stripe').href,'https://invoice.stripe.com/i/synthetic');
 assert.equal(h.requests.filter(r=>r.path==='/api/account/upgrade/confirm').length,1);
});

test('a late estimate cannot reopen billing after switching to a member session',async()=>{
 let resolve;const h=setup('admin','core',{'/api/account/upgrade':{enabled:true,status:'available'},'/api/account/license':{},'/api/account/upgrade/quote':()=>new Promise(r=>{resolve=r;})});
 h.emit('wzos:session');await flush();await h.all(h.nav).find(n=>n.id==='core-upgrade').click();const dialog=h.body.children.at(-1);
 const pending=h.all(dialog).find(n=>n.textContent==='Review upgrade estimate').click();h.change('member','core');
 resolve({status:'quoted',request_id:'late',quote:{}});await pending;
 assert.equal(dialog.open,false);assert.equal(h.calls.includes('/api/account/upgrade/confirm'),false);
});
test('members and Enterprise accounts never see an upgrade nudge',async()=>{
 for(const [role,edition] of [['member','core'],['member','enterprise'],['admin','enterprise']]){const h=setup(role,edition);h.emit('wzos:session');await flush();assert.equal(h.all(h.nav).find(n=>n.id==='core-upgrade').hidden,true);if(role==='member')assert.equal(h.calls.length,0);}
});
