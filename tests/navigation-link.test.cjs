const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function setup(){let session={id:'member',organization_id:'org1',edition:'core'},allow=true;const events={},views=[];const window={wzosClock:{getSession:()=>session},showWzosView:view=>{views.push(view);return allow;}};vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/navigation-link.js','utf8'),{window,document:{createElement:tag=>({tag}),addEventListener:(name,fn)=>events[name]=fn}});return{nav:window.WzosNavigation,views,events,setSession:s=>session=s,block:()=>allow=false};}
test('address action opens internal Navigation with selected job, without external URL or provider call',()=>{
 const h=setup(),a=h.nav.link('12 Main St, Norfolk VA',{id:'order1'});assert.equal(a.tag,'button');assert.equal(a.textContent,'Open in Navigation');assert.equal(a.href,undefined);assert.equal(a.target,undefined);a.onclick();assert.deepEqual(h.views,['navigation']);assert.equal(h.nav.take().id,'order1');assert.equal(h.nav.take(),null);
});
test('assignment action retains assignment identity and pending destination never crosses sessions',()=>{
 const h=setup(),a=h.nav.link('Frozen site',{id:'order1',assignment_id:'assignment1'});a.onclick();assert.equal(h.nav.take().assignment_id,'assignment1');a.onclick();h.setSession({id:'other',organization_id:'org2',edition:'enterprise'});assert.equal(h.nav.take(),null);a.onclick();h.events['wzos:session']();assert.equal(h.nav.take(),null);
});
test('unsaved-work navigation refusal discards pending target',()=>{const h=setup();h.block();h.nav.link('Public site',{id:'order1'}).onclick();assert.equal(h.nav.take(),null);});
test('invalid destinations or missing authorized job identity produce no action; external URL helper is explicit only',()=>{
 const {nav}=setup();for(const value of ['', '   ',null,undefined,{},'x'.repeat(501),'界'.repeat(500),'\ud800'])assert.equal(nav.link(value,{id:'order1'}),null);assert.equal(nav.link('Norfolk'),null);assert.equal(new URL(nav.url('36.85,-76.28')).searchParams.get('destination'),'36.85,-76.28');
});
