const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const sharedLocks=new WeakMap();
function lockManager(storage){
 if(!sharedLocks.has(storage)){
  const waiting=new Map();
  sharedLocks.set(storage,{async request(name,run){
   const previous=waiting.get(name)||Promise.resolve();let release;
   const done=new Promise(resolve=>{release=resolve});waiting.set(name,done);
   await previous;try{return await run();}finally{release();if(waiting.get(name)===done)waiting.delete(name);}
  }});
 }
 return sharedLocks.get(storage);
}
function harness({fail=()=>false,gate=()=>null,storage,locks,confirm=()=>true,session:initial,geo=false,denyGeo=false}={}){
 const nodes=new Map(),events={},windowEvents={},created=[];
 const element=tag=>{const e={tag,value:'',checked:false,disabled:false,hidden:false,textContent:'',dataset:{},children:[],handlers:{},options:[],
  append(...x){this.children.push(...x)},after(x){this.afterNode=x},before(x){this.beforeNode=x},replaceChildren(...x){this.children=x},
  setAttribute(){},addEventListener(k,v){this.handlers[k]=v},click(){this.onclick?.()},focus(){},remove(){}};created.push(e);return e;};
 const get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id)};
 const intervals=[];let now=Date.now();class DeviceDate extends Date{constructor(...args){super(...(args.length?args:[now]))}static now(){return now}};
 let session=initial||{id:'member',organization_id:'org-a',role:'member'},calls=[];
 const navigator={onLine:true,permissions:{query:async()=>({state:geo&&!denyGeo?'granted':'denied'})},...(geo?{geolocation:{getCurrentPosition(ok,fail){if(denyGeo)fail({code:1});else ok({coords:{latitude:37,longitude:-79,accuracy:12}})}}}:{}),locks:locks===false?undefined:locks||(storage?lockManager(storage):undefined)};
 const document={getElementById:get,createElement:element,addEventListener(k,v){events[k]=v},dispatchEvent(){}};
 const responses=(path,options)=>{
  if(path.includes('/status'))return {active:{id:'shift',version:1,work_seconds:100,status:'working',task:'job_site',note:''},tasks:{job_site:'Job Site'}};
  if(path.startsWith('/api/time/offline-submissions')&&options?.method==='POST')return {items:JSON.parse(options.body).drafts.map(d=>({...d,status:'pending'}))};
  if(path.startsWith('/api/time/locations'))return {accepted:JSON.parse(options.body).items.map(i=>i.request_id)};
  if(path.startsWith('/api/time/entries'))return {items:[],limit:20,total:0};
  return {items:[]};
 };
 const window={localStorage:storage,confirm,addEventListener(k,v){windowEvents[k]=v},wzosClock:{getSession:()=>session,getOrders:()=>[],async api(path,options){calls.push([path,options]);const wait=gate(path,options);if(wait)await wait;if(fail(path,options))throw new Error('network');return responses(path,options);}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/timeclock.js','utf8'),{window,document,navigator,performance,Date:DeviceDate,crypto:require('node:crypto').webcrypto,setInterval(fn,ms){intervals.push([fn,ms])},setTimeout(){},URL,Blob,CustomEvent:class {}});
 const byId=id=>created.find(e=>e.id===id);
 const posts=prefix=>calls.filter(c=>c[1]?.method==='POST'&&c[0].startsWith(prefix));
 return {get,byId,navigator,events,windowEvents,calls,posts,storage,intervals,advance(seconds){now+=seconds*1000;intervals.find(i=>i[1]===1000)[0]()},setSession(s){session=s}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
async function offlineAfterLoad(options){const h=harness(options);h.events['wzos:session']();await settle();h.navigator.onLine=false;h.windowEvents.offline();return h;}
async function draft(h,action,note=''){h.byId('clock-draft-action').value=action;h.byId('clock-draft-note').value=note;await h.byId('clock-draft-keep').onclick();}

test('normal punches keep the offline timeline and never issue server clock commands',async()=>{
 const h=harness();h.events['wzos:session']();await settle();assert.equal(h.get('clock-state').textContent,'CLOCKED IN');
 assert.equal(h.byId('clock-connection').dataset.state,'online');assert.equal(h.byId('clock-draft-keep').disabled,true);
 h.navigator.onLine=false;h.windowEvents.offline();assert.match(h.get('clock-state').textContent,/LAST KNOWN/);assert.equal(h.get('clock-out').disabled,false);
 assert.equal(h.byId('clock-connection').dataset.state,'offline');assert.match(h.byId('clock-connection').textContent,/estimate/);
 await h.get('clock-out').handlers.click();assert.equal(h.posts('/api/time/commands').length,0);assert.match(h.get('clock-state').textContent,/CLOCKED OUT/);
 h.navigator.onLine=true;h.windowEvents.online();assert.equal(h.byId('clock-connection').dataset.state,'reconnecting');
 await settle();assert.match(h.get('clock-state').textContent,/CLOCKED OUT/);assert.equal(h.byId('clock-connection').dataset.state,'online');
});

test('offline drafts follow the known shift and refuse duplicate or impossible actions',async()=>{
 const h=await offlineAfterLoad();
 await draft(h,'clock_in');assert.equal(h.byId('clock-draft-list').children.length,0);assert.match(h.get('clock-message').textContent,/does not follow/);
 await draft(h,'break_start','Lunch');await draft(h,'break_start');assert.equal(h.byId('clock-draft-list').children.length,1);
 await draft(h,'clock_out','Signal lost');await draft(h,'clock_out');assert.equal(h.byId('clock-draft-list').children.length,2);
 assert.equal(h.byId('clock-draft-submit').disabled,true);assert.equal(h.calls.filter(c=>c[1]?.method==='POST').length,0);
 h.byId('clock-draft-when').value='2999-01-01T00:00';await draft(h,'clock_in');assert.match(h.get('clock-message').textContent,/not in the future/);
});

test('reconnect submits drafts for review once, keeps device times and never posts clock commands',async()=>{
 const h=await offlineAfterLoad();await draft(h,'clock_out','Signal lost');
 h.navigator.onLine=true;h.windowEvents.online();await settle();assert.match(h.get('clock-message').textContent,/1 offline draft/);
 assert.equal(h.byId('clock-draft-submit').disabled,false);await h.byId('clock-draft-submit').onclick();
 const [[,request]]=h.posts('/api/time/offline-submissions');const body=JSON.parse(request.body);
 assert.equal(body.drafts.length,1);assert.equal(body.drafts[0].action,'clock_out');assert.equal(body.drafts[0].known_shift_id,'shift');assert.equal(body.drafts[0].known_version,1);
 assert.ok(body.drafts[0].captured_at&&body.device_submitted_at&&body.drafts[0].request_id);
 assert.equal(h.byId('clock-draft-list').children.length,0);assert.equal(h.byId('clock-draft-submit').disabled,true);assert.match(h.get('clock-message').textContent,/has not changed/);
 assert.equal(h.posts('/api/time/commands').length,0);
});

test('unconfirmed submission keeps drafts and retries with the same request ids',async()=>{
 let failing=true;const h=await offlineAfterLoad({fail:(path,options)=>failing&&options?.method==='POST'});await draft(h,'clock_out');
 h.navigator.onLine=true;h.windowEvents.online();await settle();
 await h.byId('clock-draft-submit').onclick();assert.equal(h.byId('clock-draft-list').children.length,1);assert.match(h.get('clock-message').textContent,/will not create duplicates/);
 failing=false;await h.byId('clock-draft-submit').onclick();
 const [first,second]=h.posts('/api/time/offline-submissions').map(c=>JSON.parse(c[1].body).drafts[0].request_id);assert.equal(first,second);
 assert.equal(h.byId('clock-draft-list').children.length,0);assert.equal(h.byId('clock-draft-submit').disabled,true);
});

test('drafts clear on organization change and never show another scope',async()=>{
 const h=await offlineAfterLoad();await draft(h,'clock_out','Ended work during connection loss');assert.equal(h.byId('clock-draft-list').children.length,1);
 h.setSession({id:'member',organization_id:'org-b',role:'member'});h.events['wzos:session']();assert.equal(h.byId('clock-draft-list').children.length,0);
 assert.match(h.get('clock-state').textContent,/NOT LOADED/);assert.equal(h.calls.filter(c=>c[1]?.method==='POST').length,0);
});

// Device persistence: a Map-backed stand-in for window.localStorage.
function deviceStorage({failWrites=false}={}){const data=new Map();return {data,getItem:k=>data.has(k)?data.get(k):null,setItem(k,v){if(failWrites)throw new Error('quota');data.set(k,String(v));},removeItem:k=>{data.delete(k);}};}
const KEY='wzos.clockDrafts.v1:org-a:member';
async function reopen(storage,options={}){const h=harness({storage,...options});h.events['wzos:session']();await settle();return h;}

test('drafts survive closing and reopening the app and submit without local-only fields',async()=>{
 const storage=deviceStorage();const first=await offlineAfterLoad({storage});await draft(first,'break_start','Lunch, no signal');await draft(first,'break_end');
 assert.equal(JSON.parse(storage.data.get(KEY)).drafts.length,2);assert.match(first.get('clock-message').textContent,/saved on this device/);
 assert.equal(first.byId('clock-draft-storage').dataset.persistence,'device');
 const event={preventDefault(){this.prevented=true}};first.windowEvents.beforeunload(event);assert.equal(event.prevented,undefined);
 const second=await reopen(storage);const list=second.byId('clock-draft-list').children;
 assert.equal(list.length,2);assert.equal(list[0].children[0].dataset.state,'local');assert.match(list[0].children[0].textContent,/Saved on this device/);
 await second.byId('clock-draft-submit').onclick();
 const body=JSON.parse(second.posts('/api/time/offline-submissions')[0][1].body);assert.equal(body.drafts.length,2);
 assert.ok(body.drafts.every(d=>!('submission' in d)));assert.equal(body.drafts[0].note,'Lunch, no signal');
 assert.equal(storage.data.has(KEY),false);assert.equal(second.byId('clock-draft-list').children.length,0);
 assert.equal(second.posts('/api/time/commands').length,0);
});

test('saved drafts stay separate by organization and account',async()=>{
 const storage=deviceStorage();const owner=await offlineAfterLoad({storage});await draft(owner,'clock_out','Private note');
 const otherOrg=await reopen(storage,{session:{id:'member',organization_id:'org-b',role:'member'}});assert.equal(otherOrg.byId('clock-draft-list').children.length,0);
 const otherUser=await reopen(storage,{session:{id:'coworker',organization_id:'org-a',role:'admin'}});assert.equal(otherUser.byId('clock-draft-list').children.length,0);
 otherUser.setSession({id:'member',organization_id:'org-a',role:'member'});otherUser.events['wzos:session']();await settle();
 assert.equal(otherUser.byId('clock-draft-list').children.length,1);
 // A record copied under the wrong key, or malformed entries, never load.
 storage.data.set('wzos.clockDrafts.v1:org-b:member',storage.data.get(KEY));
 assert.equal((await reopen(storage,{session:{id:'member',organization_id:'org-b',role:'member'}})).byId('clock-draft-list').children.length,0);
 storage.data.set(KEY,JSON.stringify({scope:'org-a:member',drafts:[{action:'delete_everything'},null]}));
 assert.equal((await reopen(storage)).byId('clock-draft-list').children.length,0);
 storage.data.set(KEY,'not json');assert.equal((await reopen(storage)).byId('clock-draft-list').children.length,0);
});

test('unconfirmed submission is remembered after reopening and retried with the same ids',async()=>{
 const storage=deviceStorage();let failing=true;
 const first=await offlineAfterLoad({storage,fail:(path,options)=>failing&&options?.method==='POST'});await draft(first,'clock_out');
 first.navigator.onLine=true;first.windowEvents.online();await settle();await first.byId('clock-draft-submit').onclick();
 assert.match(first.get('clock-message').textContent,/kept on this device/);assert.equal(JSON.parse(storage.data.get(KEY)).drafts[0].submission,'unconfirmed');
 failing=false;const second=await reopen(storage);
 assert.equal(second.byId('clock-draft-list').children[0].children[0].dataset.state,'unconfirmed');
 await second.byId('clock-draft-submit').onclick();
 const ids=[...first.posts('/api/time/offline-submissions'),...second.posts('/api/time/offline-submissions')].map(c=>JSON.parse(c[1].body).drafts[0].request_id);
 assert.equal(ids.length,2);assert.equal(ids[0],ids[1]);assert.equal(storage.data.has(KEY),false);
});

test('drafts older than the review window are kept for download but never submitted',async()=>{
 const storage=deviceStorage(),old=new Date(Date.now()-15*864e5).toISOString(),recent=new Date(Date.now()-60e3).toISOString();
 storage.data.set(KEY,JSON.stringify({scope:'org-a:member',drafts:[{request_id:'00000000-0000-4000-8000-000000000001',action:'clock_out',task:null,note:'',captured_at:old},{request_id:'00000000-0000-4000-8000-000000000002',action:'clock_in',task:'job_site',note:'',captured_at:recent}]}));
 const h=await reopen(storage);const list=h.byId('clock-draft-list').children;
 assert.equal(list[0].children[0].dataset.state,'too_old');assert.match(list[0].children[0].textContent,/manual entry/);
 await h.byId('clock-draft-submit').onclick();const body=JSON.parse(h.posts('/api/time/offline-submissions')[0][1].body);
 assert.deepEqual(body.drafts.map(d=>d.action),['clock_in']);assert.equal(JSON.parse(storage.data.get(KEY)).drafts.length,1);
 assert.equal(h.byId('clock-draft-submit').disabled,true);assert.equal(h.byId('clock-draft-download').disabled,false);
});

test('blocked device storage falls back to this tab and warns before closing',async()=>{
 const h=await offlineAfterLoad({storage:deviceStorage({failWrites:true})});await draft(h,'clock_out');
 assert.match(h.get('clock-message').textContent,/kept in this tab only/);assert.equal(h.byId('clock-draft-storage').dataset.persistence,'tab');
 assert.match(h.byId('clock-draft-list').children[0].children[0].textContent,/In this tab only/);
 const event={preventDefault(){this.prevented=true}};h.windowEvents.beforeunload(event);assert.equal(event.prevented,true);
});

test('discarding drafts needs confirmation and clears the device copy',async()=>{
 const storage=deviceStorage();let answer=false;const h=await offlineAfterLoad({storage,confirm:()=>answer});await draft(h,'clock_out');
 await h.byId('clock-draft-discard').onclick();assert.equal(storage.data.has(KEY),true);assert.equal(h.byId('clock-draft-list').children.length,1);
 answer=true;await h.byId('clock-draft-discard').onclick();assert.equal(storage.data.has(KEY),false);assert.equal(h.byId('clock-draft-list').children.length,0);
 assert.equal(h.calls.filter(c=>c[1]?.method==='POST').length,0);
});

test('another tab for the same account refreshes the draft list',async()=>{
 const storage=deviceStorage();const a=await offlineAfterLoad({storage}),b=await offlineAfterLoad({storage});await draft(a,'clock_out');
 assert.equal(b.byId('clock-draft-list').children.length,0);b.windowEvents.storage({key:'wzos.clockDrafts.v1:org-b:member'});assert.equal(b.byId('clock-draft-list').children.length,0);
 b.windowEvents.storage({key:KEY});assert.equal(b.byId('clock-draft-list').children.length,1);
});

// Review repair (CLAUDE_MODULE_REVIEW_20261010 finding 2): tabs sharing device storage.
const SUBMIT=(path,options)=>options?.method==='POST'&&path.startsWith('/api/time/offline-submissions');
function held(){let release;const gate=(path,options)=>SUBMIT(path,options)?new Promise(r=>{release=r;}):null;return {gate,release:()=>release()};}
const stored=storage=>storage.data.has(KEY)?JSON.parse(storage.data.get(KEY)).drafts:[];

test('another tab draft added during a delayed submission is kept after success',async()=>{
 for(const deliverEvent of [true,false]){
  const storage=deviceStorage(),hold=held();
  const a=await offlineAfterLoad({storage,gate:hold.gate});await draft(a,'clock_out','Tab A');
  const b=await offlineAfterLoad({storage});
  a.navigator.onLine=true;a.windowEvents.online();await settle();
  const submitting=a.byId('clock-draft-submit').onclick();await settle();
  await draft(b,'clock_in','Tab B');assert.deepEqual(stored(storage).map(d=>d.note),['Tab A','Tab B']);
  if(deliverEvent)a.windowEvents.storage({key:KEY});
  hold.release();await submitting;
  assert.deepEqual(stored(storage).map(d=>d.note),['Tab B']);
  assert.deepEqual(a.byId('clock-draft-list').children.map(li=>li.textContent.includes('Tab B')),[true]);
  assert.equal(JSON.parse(a.posts('/api/time/offline-submissions')[0][1].body).drafts.length,1);
 }
});

test('uncertain submission marks only its drafts and keeps concurrent additions',async()=>{
 const storage=deviceStorage();let failing=true;
 const a=await offlineAfterLoad({storage,fail:(path,options)=>failing&&SUBMIT(path,options)});await draft(a,'clock_out','Tab A');
 const b=await offlineAfterLoad({storage});await draft(b,'clock_in','Tab B');
 a.navigator.onLine=true;a.windowEvents.online();await settle();await a.byId('clock-draft-submit').onclick();
 assert.deepEqual(stored(storage).map(d=>[d.note,d.submission||'local']),[['Tab A','unconfirmed'],['Tab B','local']]);
 const firstIds=JSON.parse(a.posts('/api/time/offline-submissions')[0][1].body).drafts.map(d=>d.request_id);
 // Same account: tab A now shows and resubmits both drafts, reusing tab A's original request ID.
 failing=false;await a.byId('clock-draft-submit').onclick();
 const second=JSON.parse(a.posts('/api/time/offline-submissions')[1][1].body).drafts;
 assert.deepEqual(second.map(d=>d.note),['Tab A','Tab B']);assert.equal(second[0].request_id,firstIds[0]);
 assert.deepEqual(stored(storage),[]);
});

test('a stale tab cannot restore a submitted draft or discard drafts it never saw',async()=>{
 const storage=deviceStorage();
 const a=await offlineAfterLoad({storage});await draft(a,'clock_out','First');
 const b=await offlineAfterLoad({storage});
 b.navigator.onLine=true;b.windowEvents.online();await settle();await b.byId('clock-draft-submit').onclick();
 assert.deepEqual(stored(storage),[]);
 // Tab A still shows "First" (no storage event). Removing its last draft must not resurrect anything.
 await a.byId('clock-draft-remove').onclick();assert.deepEqual(stored(storage),[]);
 const c=await offlineAfterLoad({storage});await draft(c,'clock_out','Unseen by A');
 await draft(a,'clock_out','A after reload');
 assert.deepEqual(stored(storage).map(d=>d.note),['Unseen by A']);
 const d=await offlineAfterLoad({storage});await draft(d,'clock_in','Newest');
 // Tab A's screen shows only the draft it reloaded; discarding must not remove the newer one.
 assert.deepEqual(a.byId('clock-draft-list').children.map(li=>li.textContent.includes('Unseen by A')),[true]);
 await a.byId('clock-draft-discard').onclick();
 assert.deepEqual(stored(storage).map(x=>x.note),['Newest']);
});

test('switching account during a submission clears only the acknowledged drafts of the original account',async()=>{
 const storage=deviceStorage(),hold=held();
 const a=await offlineAfterLoad({storage,gate:hold.gate});await draft(a,'clock_out','Org A draft');
 a.navigator.onLine=true;a.windowEvents.online();await settle();
 const submitting=a.byId('clock-draft-submit').onclick();await settle();
 a.setSession({id:'member',organization_id:'org-b',role:'member'});a.events['wzos:session']();await settle();
 hold.release();await submitting;
 assert.equal(storage.data.has(KEY),false);assert.equal(a.byId('clock-draft-list').children.length,0);
 assert.equal(storage.data.has('wzos.clockDrafts.v1:org-b:member'),false);
});

test('overlapping device mutations wait for the shared lock and validate the newest sequence',async()=>{
 const storage=deviceStorage(),locks=lockManager(storage);let release,entered;
 const ready=new Promise(resolve=>{entered=resolve});
 const blocked=locks.request(KEY,async()=>{entered();await new Promise(resolve=>{release=resolve});});
 await ready;
 const a=await offlineAfterLoad({storage}),b=await offlineAfterLoad({storage});
 const first=draft(a,'break_start','Tab A'),second=draft(b,'clock_out','Tab B');
 await settle();assert.equal(storage.data.has(KEY),false,'Writes happened outside the shared lock');
 const closing={preventDefault(){this.prevented=true}};a.windowEvents.beforeunload(closing);assert.equal(closing.prevented,true);
 release();await blocked;await Promise.all([first,second]);
 assert.deepEqual(stored(storage).map(d=>[d.action,d.note]),[['break_start','Tab A'],['clock_out','Tab B']]);
 // Two simultaneous duplicate punches must validate against each other's commits.
 const c=await offlineAfterLoad({storage}),d=await offlineAfterLoad({storage});
 await Promise.all([draft(c,'clock_in','Next'),draft(d,'clock_in','Duplicate')]);
 assert.deepEqual(stored(storage).map(d=>d.note),['Tab A','Tab B','Next']);
 assert.match(d.get('clock-message').textContent,/does not follow/);
});

test('a storage read cannot interleave a second-tab write inside a locked mutation',async()=>{
 const storage=deviceStorage(),read=storage.getItem;let inject=null,second;
 storage.getItem=k=>{const value=read(k);if(inject){const run=inject;inject=null;run();}return value;};
 const a=await offlineAfterLoad({storage}),b=await offlineAfterLoad({storage});
 inject=()=>{second=draft(b,'clock_out','Concurrent tab');};
 await draft(a,'break_start','First tab');await second;
 assert.deepEqual(stored(storage).map(d=>d.note),['First tab','Concurrent tab']);
});

test('without cross-tab locks, changes stay in this tab and device records are untouched',async()=>{
 const storage=deviceStorage(),h=await offlineAfterLoad({storage,locks:false});
 await draft(h,'clock_out','No locking support');
 assert.equal(storage.data.has(KEY),false);assert.equal(h.byId('clock-draft-list').children.length,1);
 assert.equal(h.byId('clock-draft-storage').dataset.persistence,'tab');
 assert.match(h.byId('clock-draft-storage').textContent,/locking unavailable/);
 const closing={preventDefault(){this.prevented=true}};h.windowEvents.beforeunload(closing);assert.equal(closing.prevented,true);
});

test('an account switch while waiting for a storage lock cannot save a draft under either account',async()=>{
 const storage=deviceStorage(),locks=lockManager(storage);let release,entered;
 const ready=new Promise(resolve=>{entered=resolve});
 const blocked=locks.request(KEY,async()=>{entered();await new Promise(resolve=>{release=resolve});});await ready;
 const h=await offlineAfterLoad({storage});const adding=draft(h,'clock_out','Original account');
 h.setSession({id:'member',organization_id:'org-b',role:'member'});h.events['wzos:session']();await settle();
 release();await blocked;await adding;
 assert.equal(storage.data.has(KEY),false);assert.equal(storage.data.has('wzos.clockDrafts.v1:org-b:member'),false);
 assert.equal(h.byId('clock-draft-list').children.length,0);
});

test('a refused cross-tab lock falls back safely without deleting saved device data',async()=>{
 const storage=deviceStorage(),h=await offlineAfterLoad({storage,locks:{async request(){throw Error('lock refused')}}});
 await draft(h,'clock_out','Fallback');
 assert.equal(storage.data.has(KEY),false);assert.equal(h.byId('clock-draft-list').children.length,1);
 assert.equal(h.byId('clock-draft-storage').dataset.persistence,'tab');
});

test('device timer excludes offline breaks and resumes the selected task',async()=>{
 const storage=deviceStorage(),h=await offlineAfterLoad({storage});h.advance(60);assert.equal(h.get('clock-timer').textContent,'00:02:40');
 await h.get('clock-break').handlers.click();h.advance(120);assert.equal(h.get('clock-timer').textContent,'00:02:40');
 await h.get('clock-break').handlers.click();h.advance(30);assert.equal(h.get('clock-timer').textContent,'00:03:10');
 h.get('clock-task').value='travel';await h.get('clock-switch').handlers.click();h.advance(20);assert.match(h.get('clock-active-job').textContent,/Travel Time/);assert.equal(h.posts('/api/time/commands').length,0);
 const resumed=await reopen(storage);assert.equal(resumed.get('clock-task').value,'travel');assert.match(resumed.get('clock-active-job').textContent,/pending admin review/);
});
test('offline device GPS can be captured without internet and reconnect stays separate',async()=>{
 const storage=deviceStorage(),h=await offlineAfterLoad({storage,geo:true});h.get('clock-task').value='setup';await h.get('clock-switch').handlers.click();await settle();
 const key='wzos.time-tracker.v1:org-a:member:locations',saved=JSON.parse(storage.data.get(key));assert.equal(saved.items[0].unavailable,undefined);assert.equal(saved.items[0].latitude,37);
 h.navigator.onLine=true;h.windowEvents.online();await settle();await settle();const items=h.posts('/api/time/locations').flatMap(c=>JSON.parse(c[1].body).items);
 assert.ok(items.some(p=>p.event==='switch_task'&&p.latitude===37));assert.ok(items.some(p=>p.event==='reconnect'&&p.latitude===37));
});
test('location permission denial preserves clock actions and uploads the reason',async()=>{
 const h=harness({storage:deviceStorage(),geo:true,denyGeo:true});h.events['wzos:session']();await settle();await h.get('clock-out').handlers.click();await settle();
 assert.equal(h.posts('/api/time/commands').length,1);assert.ok(h.posts('/api/time/locations').some(c=>JSON.parse(c[1].body).items.some(p=>p.unavailable==='permission_denied')));
});
test('uncertain clock command retains its original retry ID after reopening',async()=>{
 const storage=deviceStorage(),first=await reopen(storage,{fail:p=>p==='/api/time/commands'});await first.get('clock-out').handlers.click();
 const original=JSON.parse(first.posts('/api/time/commands')[0][1].body).request_id,second=await reopen(storage);await second.get('clock-retry').handlers.click();
 assert.equal(JSON.parse(second.posts('/api/time/commands')[0][1].body).request_id,original);
});

test('an offline clock-out stops further GPS even while attendance waits for admin review',async()=>{
 const h=await offlineAfterLoad({storage:deviceStorage(),geo:true});await h.get('clock-out').handlers.click();await settle();
 h.navigator.onLine=true;h.windowEvents.online();await settle();await settle();await h.byId('clock-draft-submit').onclick();
 h.intervals.find(i=>i[1]===300000)[0]();await settle();await settle();
 const items=h.posts('/api/time/locations').flatMap(c=>JSON.parse(c[1].body).items);assert.ok(items.some(p=>p.event==='clock_out'));assert.ok(items.every(p=>p.event!=='interval'&&p.event!=='reconnect'));
});

test('shared GPS outbox keeps concurrent evidence and stale tabs cannot resurrect acknowledged items',async()=>{
 const storage=deviceStorage(),a=await offlineAfterLoad({storage}),b=await offlineAfterLoad({storage});
 a.get('clock-task').value='setup';await a.get('clock-switch').handlers.click();await settle();
 b.get('clock-task').value='travel';await b.get('clock-switch').handlers.click();await settle();
 const key='wzos.time-tracker.v1:org-a:member:locations',old=JSON.parse(storage.data.get(key)).items;assert.equal(old.length,2);
 a.navigator.onLine=true;a.windowEvents.online();await settle();await settle();await settle();
 const sent=a.posts('/api/time/locations').flatMap(c=>JSON.parse(c[1].body).items);assert.ok(old.every(p=>sent.some(e=>e.request_id===p.request_id)));
 b.get('clock-task').value='teardown';await b.get('clock-switch').handlers.click();await settle();
 const fresh=JSON.parse(storage.data.get(key)).items;assert.ok(fresh.every(p=>!old.some(e=>e.request_id===p.request_id)));
});
