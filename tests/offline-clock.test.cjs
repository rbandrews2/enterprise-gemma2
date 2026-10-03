const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function harness({fail=()=>false}={}){
 const nodes=new Map(),events={},windowEvents={},created=[];
 const element=tag=>{const e={tag,value:'',checked:false,disabled:false,hidden:false,textContent:'',dataset:{},children:[],handlers:{},options:[],
  append(...x){this.children.push(...x)},after(x){this.afterNode=x},before(x){this.beforeNode=x},replaceChildren(...x){this.children=x},
  setAttribute(){},addEventListener(k,v){this.handlers[k]=v},click(){this.onclick?.()},focus(){},remove(){}};created.push(e);return e;};
 const get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id)};
 let session={id:'member',organization_id:'org-a',role:'member'},calls=[];
 const navigator={onLine:true};
 const document={getElementById:get,createElement:element,addEventListener(k,v){events[k]=v},dispatchEvent(){}};
 const responses=(path,options)=>{
  if(path.includes('/status'))return {active:{id:'shift',version:1,work_seconds:100,status:'working',task:'job_site'},tasks:{job_site:'Job Site'}};
  if(path.startsWith('/api/time/offline-submissions')&&options?.method==='POST')return {items:JSON.parse(options.body).drafts.map(d=>({...d,status:'pending'}))};
  if(path.startsWith('/api/time/entries'))return {items:[],limit:20,total:0};
  return {items:[]};
 };
 const window={addEventListener(k,v){windowEvents[k]=v},wzosClock:{getSession:()=>session,getOrders:()=>[],async api(path,options){calls.push([path,options]);if(fail(path,options))throw new Error('network');return responses(path,options);}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/timeclock.js','utf8'),{window,document,navigator,performance,Date,crypto:require('node:crypto').webcrypto,setInterval(){},setTimeout(){},URL,Blob,CustomEvent:class {}});
 const byId=id=>created.find(e=>e.id===id);
 const posts=prefix=>calls.filter(c=>c[1]?.method==='POST'&&c[0].startsWith(prefix));
 return {get,byId,navigator,events,windowEvents,calls,posts,setSession(s){session=s}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
async function offlineAfterLoad(options){const h=harness(options);h.events['wzos:session']();await settle();h.navigator.onLine=false;h.windowEvents.offline();return h;}
function draft(h,action,note=''){h.byId('clock-draft-action').value=action;h.byId('clock-draft-note').value=note;h.byId('clock-draft-keep').onclick();}

test('offline preserves last-known shift, shows connection state and cannot issue clock commands',async()=>{
 const h=harness();h.events['wzos:session']();await settle();assert.equal(h.get('clock-state').textContent,'CLOCKED IN');
 assert.equal(h.byId('clock-connection').dataset.state,'online');assert.equal(h.byId('clock-draft-keep').disabled,true);
 h.navigator.onLine=false;h.windowEvents.offline();assert.match(h.get('clock-state').textContent,/LAST KNOWN/);assert.equal(h.get('clock-out').disabled,true);
 assert.equal(h.byId('clock-connection').dataset.state,'offline');assert.match(h.byId('clock-connection').textContent,/estimate/);
 await h.get('clock-out').handlers.click();assert.equal(h.posts('/api/time/commands').length,0);
 h.navigator.onLine=true;h.windowEvents.online();assert.equal(h.byId('clock-connection').dataset.state,'reconnecting');
 await settle();assert.equal(h.get('clock-state').textContent,'CLOCKED IN');assert.equal(h.byId('clock-connection').dataset.state,'online');
});

test('offline drafts follow the known shift and refuse duplicate or impossible actions',async()=>{
 const h=await offlineAfterLoad();
 draft(h,'clock_in');assert.equal(h.byId('clock-draft-list').children.length,0);assert.match(h.get('clock-message').textContent,/does not follow/);
 draft(h,'break_start','Lunch');draft(h,'break_start');assert.equal(h.byId('clock-draft-list').children.length,1);
 draft(h,'clock_out','Signal lost');draft(h,'clock_out');assert.equal(h.byId('clock-draft-list').children.length,2);
 assert.equal(h.byId('clock-draft-submit').disabled,true);assert.equal(h.calls.filter(c=>c[1]?.method==='POST').length,0);
 h.byId('clock-draft-when').value='2999-01-01T00:00';draft(h,'clock_in');assert.match(h.get('clock-message').textContent,/not in the future/);
});

test('reconnect submits drafts for review once, keeps device times and never posts clock commands',async()=>{
 const h=await offlineAfterLoad();draft(h,'clock_out','Signal lost');
 h.navigator.onLine=true;h.windowEvents.online();await settle();assert.match(h.get('clock-message').textContent,/1 offline draft/);
 assert.equal(h.byId('clock-draft-submit').disabled,false);await h.byId('clock-draft-submit').onclick();
 const [[,request]]=h.posts('/api/time/offline-submissions');const body=JSON.parse(request.body);
 assert.equal(body.drafts.length,1);assert.equal(body.drafts[0].action,'clock_out');assert.equal(body.drafts[0].known_shift_id,'shift');assert.equal(body.drafts[0].known_version,1);
 assert.ok(body.drafts[0].captured_at&&body.device_submitted_at&&body.drafts[0].request_id);
 assert.equal(h.byId('clock-draft-list').children.length,0);assert.match(h.get('clock-message').textContent,/has not changed/);
 assert.equal(h.posts('/api/time/commands').length,0);
});

test('unconfirmed submission keeps drafts and retries with the same request ids',async()=>{
 let failing=true;const h=await offlineAfterLoad({fail:(path,options)=>failing&&options?.method==='POST'});draft(h,'clock_out');
 h.navigator.onLine=true;h.windowEvents.online();await settle();
 await h.byId('clock-draft-submit').onclick();assert.equal(h.byId('clock-draft-list').children.length,1);assert.match(h.get('clock-message').textContent,/will not create duplicates/);
 failing=false;await h.byId('clock-draft-submit').onclick();
 const [first,second]=h.posts('/api/time/offline-submissions').map(c=>JSON.parse(c[1].body).drafts[0].request_id);assert.equal(first,second);
 assert.equal(h.byId('clock-draft-list').children.length,0);
});

test('drafts clear on organization change and never show another scope',async()=>{
 const h=await offlineAfterLoad();draft(h,'clock_out','Ended work during connection loss');assert.equal(h.byId('clock-draft-list').children.length,1);
 h.setSession({id:'member',organization_id:'org-b',role:'member'});h.events['wzos:session']();assert.equal(h.byId('clock-draft-list').children.length,0);
 assert.match(h.get('clock-state').textContent,/NOT LOADED/);assert.equal(h.calls.filter(c=>c[1]?.method==='POST').length,0);
});
