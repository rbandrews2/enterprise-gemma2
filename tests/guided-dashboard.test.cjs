const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const flush=()=>new Promise(r=>setImmediate(r));
function setup(role='admin',edition='enterprise'){
 class Node{constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.open=false;this.hidden=false;}append(...n){this.children.push(...n);}prepend(...n){this.children.unshift(...n);}replaceChildren(...n){this.children=n;}setAttribute(k,v){this[k]=v;}addEventListener(){}showModal(){this.open=true;}close(){this.open=false;}remove(){this.removed=true;}querySelector(s){return all(this).find(n=>s===n.tag||s==='.'+n.className)||null;}}
 const all=n=>[n,...n.children.flatMap(all)],main=new Node('main'),nav=new Node('nav'),body=new Node('body'),events={},calls=[],clicks=[];let session={role,edition};
 const emit=(e,detail)=>{for(const f of events[e]||[])f({detail});};
 main.id='main';const document={body,createElement:t=>new Node(t),createTextNode:t=>new Node('text',t),getElementById:id=>all(main).concat(all(nav)).find(n=>n.id===id)||{click(){clicks.push(id);}},querySelector:s=>s.startsWith('nav')?nav:null,addEventListener:(e,f)=>(events[e]??=[]).push(f)};
 const data={organization:'Synthetic organization',status:'amber',checks:[],modules:[{id:'clock',label:'Time Tracker',icon:'bolt',nav_id:'clock-nav',visible:true},{id:'report',label:'Work Zone Report',icon:'report',nav_id:'report-nav',visible:edition==='enterprise'}],notes:[]};
 const window={wzosClock:{getSession:()=>session,api:async path=>{calls.push(path);return data;}},showWzosView:view=>emit('wzos:view',view),addEventListener(){}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/organization-hub.js','utf8'),{window,document,confirm:()=>false,crypto:{randomUUID:()=> 'synthetic'},Date});
 return{main,nav,body,all,emit,calls,clicks,change:(role,edition)=>{session={role,edition};emit('wzos:session');}};
}
test('guided landing uses authorized module data and working navigation',async()=>{
 const h=setup();h.emit('wzos:session');await flush();assert.equal(h.calls.length,1);
 assert.ok(h.all(h.main).some(n=>n.textContent==='Synthetic organization'));
 assert.ok(h.all(h.main).some(n=>n.textContent==='Your operation. In clear view.'));
 const feature=h.all(h.main).find(n=>n.className==='panel hub-card guided-feature');assert.ok(feature);feature.onclick();assert.deepEqual(h.clicks,['report-nav']);
 assert.equal(h.all(h.main).some(n=>/Status checks incomplete|No current verified|Security signals/.test(n.textContent)),false);
 assert.equal(h.all(h.main).find(n=>n.textContent==='Synthetic organization').className,'organization-heading');
});
test('Core upgrade is admin-only, informational and closes on session changes',async()=>{
 const h=setup('admin','core');h.emit('wzos:session');await flush();const upgrade=h.all(h.nav).find(n=>n.id==='core-upgrade');assert.equal(upgrade.hidden,false);upgrade.onclick();
 const dialog=h.body.children.at(-1);assert.equal(dialog.open,true);assert.ok(h.all(dialog).some(n=>n.textContent.includes('one-time $20 upgrade credit')));
 assert.equal(h.calls.filter(p=>p.includes('checkout')).length,0);h.change('member','core');assert.equal(upgrade.hidden,true);assert.equal(dialog.open,false);const count=h.body.children.length;upgrade.onclick();assert.equal(h.body.children.length,count);
 assert.equal(h.all(h.main).some(n=>n.textContent==='Synthetic organization'),false);
});
test('members and Enterprise accounts never see an upgrade nudge',async()=>{
 for(const [role,edition] of [['member','core'],['member','enterprise'],['admin','enterprise']]){const h=setup(role,edition);h.emit('wzos:session');await flush();assert.equal(h.all(h.nav).find(n=>n.id==='core-upgrade').hidden,true);if(role==='member')assert.equal(h.calls.length,0);}
});
