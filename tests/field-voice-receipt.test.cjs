const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function harness(mode={}){
 class Node{constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.hidden=false;this.value='';}append(...items){this.children.push(...items);}prepend(...items){this.children.unshift(...items);}replaceChildren(...items){this.children=items;}setAttribute(){}scrollIntoView(){this.scrolled=true;}focus(){this.focused=true;}querySelectorAll(){return all(this).filter(n=>['input','textarea','select','button'].includes(n.tag));}}
 const all=n=>[n,...n.children.flatMap(all)],main=new Node('main'),menu=new Node('nav'),events={},calls=[];
 const document={createElement:t=>new Node(t),getElementById:id=>id==='main'?main:all(main).find(n=>n.id===id),querySelector:s=>s.startsWith('nav[')?menu:null,addEventListener:(n,f)=>(events[n]??=[]).push(f),dispatchEvent:e=>emit(e.type,e.detail)};
 const emit=async(type,detail)=>{await Promise.all((events[type]||[]).map(f=>f({detail})));};
 let listReads=0,failList=false,failSend=false;
 const draft={id:'receipt-id',job_id:'job',version:1,state:'draft',updated_at:'2026-10-20T14:00:00Z',submission_ids:[],fields:{work_date:'2026-10-20',report:{work_description:'Synthetic work',production_quantities:[],incidents:[],unresolved:[]}}};
 const fetch=async(path,opts={})=>{calls.push(path);let data,ok=true;
  if(path.endsWith('/config'))data={enabled:true,speech_enabled:!!mode.speech};
  else if(path.includes('/transcribe')){if(mode.transcribeStall)return new Promise(()=>{});data={transcript:'Synthetic report'};}
  else if(path.endsWith('/extract')){if(mode.extractStall)return new Promise(()=>{});data={fields:structuredClone(draft.fields)};}
  else if(path.endsWith('/jobs'))data={items:[{id:'job',version:1}]};
  else if(path.endsWith('/send-to-office')){ok=!failSend;data=ok?{...structuredClone(draft),state:'sent',version:2,submission_ids:['form-id']}:{detail:'Connection failed. Retry to confirm.'};}
  else if(path.endsWith('/drafts')){ok=!(failList&&++listReads>1);if(!failList)listReads++;data=ok?{items:[structuredClone(draft)]}:{detail:'List refresh failed.'};}
  else throw Error('Unexpected request '+path);
  return{ok,json:async()=>data};};
 let stopped=0,micResolve;const timers=new Map();let timerId=0;
 class Recorder{constructor(){this.state='inactive';this.mimeType='audio/webm';}start(){this.state='recording';}stop(){this.state='inactive';if(!mode.stopStall)queueMicrotask(()=>{this.ondataavailable?.({data:new Blob(['synthetic'])});this.onstop?.();});}}
 const window={MediaRecorder:Recorder,wzosDeviceSetup:{status:async()=> 'granted',remembered:()=>true,open(){}},wzosClock:{getSession:()=>({id:'admin',edition:'enterprise'})},wzosAccount:{headers:async()=>({})},showWzosView:()=>true,addEventListener(){}};
 const stream={getTracks:()=>[{stop(){stopped++;}}]};
 const navigator={onLine:true,mediaDevices:{getUserMedia:()=>mode.micStall?new Promise(r=>micResolve=r):Promise.resolve(stream)}};
 class Audio{decodeAudioData(){return mode.decodeStall?new Promise(()=>{}):Promise.resolve({duration:.1});}close(){return Promise.resolve();}}
 class Offline{createBufferSource(){return {connect(){},start(){}};}startRendering(){return Promise.resolve({getChannelData:()=>new Float32Array(1600)});}}
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/field-voice.js','utf8'),{document,window,fetch,crypto:require('node:crypto').webcrypto,structuredClone,Date,navigator,Blob,URLSearchParams,AudioContext:Audio,OfflineAudioContext:Offline,MediaRecorder:Recorder,confirm:()=>true,CustomEvent:class{constructor(type){this.type=type;}},clearInterval(){},setInterval(){return 1;},setTimeout:(fn,ms)=>{timers.set(++timerId,{fn,ms});return timerId;},clearTimeout:id=>timers.delete(id),AbortController,MutationObserver:class{observe(){}}});
 return{main,all,emit,draft,calls,window,stopped:()=>stopped,grant:()=>micResolve(stream),timeout:ms=>{const entry=[...timers.entries()].find(([,t])=>t.ms===ms);assert.ok(entry,'Expected timer '+ms);timers.delete(entry[0]);entry[1].fn();},find:text=>all(main).find(n=>n.textContent===text),setFailList:()=>failList=true,setFailSend:()=>failSend=true,open:async()=>{await window.wzosFieldVoice.open();all(main).find(n=>n.tag==='select').value='job';}};
}

const settle=()=>new Promise(resolve=>setImmediate(resolve));
for(const [mode,timeout] of [[{decodeStall:true},15000],[{transcribeStall:true},60000],[{extractStall:true},300000],[{stopStall:true},5000]])test('stalled recording phase recovers controls '+Object.keys(mode)[0],async()=>{
 const h=harness({speech:true,...mode});await h.emit('wzos:session');await h.open();await h.find('● Record').onclick();h.find('Stop').onclick();await settle();
 assert.equal(h.find('● Record').disabled,true);h.timeout(timeout);await settle();
 assert.equal(h.find('● Record').disabled,false);assert.equal(h.find('Create drafts with Atlas').disabled,false);assert.ok(h.stopped()>0);
 assert.equal(h.window.wzosModulesCanLeave(),true);
 if(mode.extractStall)assert.equal(h.all(h.main).find(n=>n.placeholder)?.value,'Synthetic report');
});
test('cancel processing is immediate even when fetch ignores abort, and a new attempt works',async()=>{
 const mode={speech:true,transcribeStall:true},h=harness(mode);await h.emit('wzos:session');await h.open();await h.find('● Record').onclick();h.find('Stop').onclick();await settle();
 const cancel=h.find('Cancel action');assert.equal(cancel.disabled,false);cancel.onclick();await settle();assert.equal(h.find('● Record').disabled,false);
 mode.transcribeStall=false;await h.find('● Record').onclick();h.find('Stop').onclick();await settle();
 assert.equal(h.find('Review field report').focused,true);assert.equal(h.find('● Record').disabled,false);
});
test('late microphone permission stops tracks after timeout and cannot relock the app',async()=>{
 const h=harness({speech:true,micStall:true});await h.emit('wzos:session');await h.open();const start=h.find('● Record').onclick();await settle();h.timeout(20000);await start;
 assert.equal(h.find('● Record').disabled,false);h.grant();await settle();assert.equal(h.stopped(),1);assert.equal(h.find('● Record').disabled,false);
});
test('navigation can cancel pending processing and a new session remains usable',async()=>{
 const h=harness({speech:true,transcribeStall:true});await h.emit('wzos:session');await h.open();await h.find('● Record').onclick();h.find('Stop').onclick();await settle();
 assert.equal(h.window.wzosModulesCanLeave(),true);await settle();await h.emit('wzos:session');assert.equal(h.window.wzosFieldVoice.available(),true);assert.equal(h.find('● Record').disabled,false);
});
test('submission receipt stays beside controls even when refreshing saved reports fails',async()=>{
 const h=harness();h.setFailList();await h.emit('wzos:session');await h.open();
 h.find('2026-10-20 · draft · Synthetic work').onclick();h.all(h.main).find(n=>n.type==='checkbox').checked=true;
 await h.find('Send to office').onclick();
 const receipt=h.all(h.main).find(n=>n.className==='voice-delivery');
 assert.equal(receipt.hidden,false);assert.match(receipt.textContent,/Receipt: receipt-id/);assert.match(receipt.textContent,/1 form\(s\) saved in Forms hub/);
 assert.equal(h.find('Received by office').disabled,true);
 assert.equal(h.calls.filter(p=>p.endsWith('/send-to-office')).length,1);
});
test('reopening a submitted report restores receipt and prevents resending',async()=>{
 const h=harness();h.draft.state='sent';h.draft.submission_ids=['a','b'];await h.emit('wzos:session');await h.open();
 h.find('2026-10-20 · sent · Synthetic work').onclick();
 assert.match(h.all(h.main).find(n=>n.className==='voice-delivery').textContent,/2 form\(s\)/);assert.equal(h.find('Received by office').disabled,true);
});

test('saved report review moves focus to visible editor and explains what opened',async()=>{
 const h=harness();await h.emit('wzos:session');await h.open();
 await h.find('Review saved field reports').onclick();assert.match(h.all(h.main).find(n=>n.className==='voice-notice').textContent,/Choose a saved/);
 h.find('2026-10-20 · draft · Synthetic work').onclick();
 assert.equal(h.find('Review field report').focused,true);assert.match(h.all(h.main).find(n=>n.className==='voice-delivery').textContent,/Report opened below for review/);
});
test('a failed send shows its error next to the button without a success receipt',async()=>{
 const h=harness();h.setFailSend();await h.emit('wzos:session');await h.open();h.find('2026-10-20 · draft · Synthetic work').onclick();h.all(h.main).find(n=>n.type==='checkbox').checked=true;
 await h.find('Send to office').onclick();const receipt=h.all(h.main).find(n=>n.className==='voice-delivery');
 assert.match(receipt.textContent,/Connection failed/);assert.doesNotMatch(receipt.textContent,/Receipt:/);assert.equal(h.find('Send to office').disabled,false);
});
test('office alert refreshes after review and discards a reply after changing account',async()=>{
 class Node{constructor(){this.children=[];this.attrs={};this.listeners={};this.classList={add(){}};}append(...n){this.children.push(...n);}before(...n){this.children.unshift(...n);}setAttribute(k,v){this.attrs[k]=v;}addEventListener(k,v){this.listeners[k]=v;}}
 const main=new Node(),area=new Node(),items=new Node(),events={};let session={role:'admin'},count=2,reply=null,calls=0;
 const emit=async(type)=>Promise.all((events[type]||[]).map(f=>f()));
 const document={body:{classList:{contains:()=>false}},querySelector:()=>main,createElement:()=>new Node(),getElementById:id=>id==='header-notifications'?area:id==='header-notification-items'?items:main,addEventListener:(type,f)=>(events[type]??=[]).push(f)};
 const window={wzosClock:{getSession:()=>session,api:async()=>{calls++;return reply?await reply:{pending_count:count};}},showWzosView(){}};
 const source=fs.readFileSync('services/workspace_preview/static/review-workflows.js','utf8').split('// Shared review workflow integration;')[0];
 vm.runInNewContext(source,{document,window,setInterval(){}});
 await emit('wzos:session');const alert=items.children[0];assert.equal(alert.id,'office-review-alert');assert.equal(alert.hidden,false);assert.match(alert.children[0].textContent,/2 forms/);assert.equal(area.hidden,false);assert.equal(alert.attrs['data-unread'],'true');
 alert.listeners.click();assert.equal(alert.attrs['data-unread'],'false');
 await emit('visibilitychange');assert.equal(alert.attrs['data-unread'],'false');
 count=3;await emit('wzos:office-sent');assert.equal(alert.attrs['data-unread'],'true');
 count=0;await emit('wzos:office-reviewed');assert.equal(alert.hidden,true);assert.equal(area.hidden,true);
 let resolve;reply=new Promise(r=>resolve=r);const pending=emit('wzos:office-sent');await Promise.resolve();
 session={role:'member'};await emit('wzos:session');resolve({pending_count:9});await pending;assert.equal(alert.hidden,true);
 const prior=calls;await emit('visibilitychange');assert.equal(calls,prior);
});
