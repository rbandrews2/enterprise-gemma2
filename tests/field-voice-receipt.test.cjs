const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function harness(){
 class Node{constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.hidden=false;this.value='';}append(...items){this.children.push(...items);}prepend(...items){this.children.unshift(...items);}replaceChildren(...items){this.children=items;}setAttribute(){}querySelectorAll(){return all(this).filter(n=>['input','textarea','select','button'].includes(n.tag));}}
 const all=n=>[n,...n.children.flatMap(all)],main=new Node('main'),menu=new Node('nav'),events={},calls=[];
 const document={createElement:t=>new Node(t),getElementById:id=>id==='main'?main:all(main).find(n=>n.id===id),querySelector:s=>s.startsWith('nav[')?menu:null,addEventListener:(n,f)=>(events[n]??=[]).push(f),dispatchEvent:e=>emit(e.type,e.detail)};
 const emit=async(type,detail)=>{await Promise.all((events[type]||[]).map(f=>f({detail})));};
 let listReads=0,failList=false,failSend=false;
 const draft={id:'receipt-id',job_id:'job',version:1,state:'draft',updated_at:'2026-10-20T14:00:00Z',submission_ids:[],fields:{work_date:'2026-10-20',report:{work_description:'Synthetic work',production_quantities:[],incidents:[],unresolved:[]}}};
 const fetch=async(path,opts={})=>{calls.push(path);let data,ok=true;
  if(path.endsWith('/config'))data={enabled:true,speech_enabled:false};
  else if(path.endsWith('/jobs'))data={items:[{id:'job',version:1}]};
  else if(path.endsWith('/send-to-office')){ok=!failSend;data=ok?{...structuredClone(draft),state:'sent',version:2,submission_ids:['form-id']}:{detail:'Connection failed. Retry to confirm.'};}
  else if(path.endsWith('/drafts')){ok=!(failList&&++listReads>1);if(!failList)listReads++;data=ok?{items:[structuredClone(draft)]}:{detail:'List refresh failed.'};}
  else throw Error('Unexpected request '+path);
  return{ok,json:async()=>data};};
 const window={wzosClock:{getSession:()=>({id:'admin',edition:'enterprise'})},wzosAccount:{headers:async()=>({})},showWzosView:()=>true,addEventListener(){}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/field-voice.js','utf8'),{document,window,fetch,crypto:require('node:crypto').webcrypto,structuredClone,Date,navigator:{},confirm:()=>true,CustomEvent:class{constructor(type){this.type=type;}},clearInterval,setInterval,MutationObserver:class{observe(){}}});
 return{main,all,emit,draft,calls,find:text=>all(main).find(n=>n.textContent===text),setFailList:()=>failList=true,setFailSend:()=>failSend=true,open:()=>window.wzosFieldVoice.open()};
}
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
test('a failed send shows its error next to the button without a success receipt',async()=>{
 const h=harness();h.setFailSend();await h.emit('wzos:session');await h.open();h.find('2026-10-20 · draft · Synthetic work').onclick();h.all(h.main).find(n=>n.type==='checkbox').checked=true;
 await h.find('Send to office').onclick();const receipt=h.all(h.main).find(n=>n.className==='voice-delivery');
 assert.match(receipt.textContent,/Connection failed/);assert.doesNotMatch(receipt.textContent,/Receipt:/);assert.equal(h.find('Send to office').disabled,false);
});
test('office alert refreshes after review and discards a reply after changing account',async()=>{
 class Node{constructor(){this.children=[];}append(...n){this.children.push(...n);}prepend(...n){this.children.unshift(...n);}setAttribute(){}}
 const main=new Node(),events={};let session={role:'admin'},count=2,reply=null,calls=0;
 const emit=async(type)=>Promise.all((events[type]||[]).map(f=>f()));
 const document={createElement:()=>new Node(),getElementById:()=>main,addEventListener:(type,f)=>(events[type]??=[]).push(f)};
 const window={wzosClock:{getSession:()=>session,api:async()=>{calls++;return reply?await reply:{pending_count:count};}},showWzosView(){}};
 const source=fs.readFileSync('services/workspace_preview/static/review-workflows.js','utf8').split('// Shared review workflow integration;')[0];
 vm.runInNewContext(source,{document,window,setInterval(){}});
 await emit('wzos:session');const alert=main.children[0];assert.equal(alert.hidden,false);assert.match(alert.children[0].textContent,/2 forms/);
 count=0;await emit('wzos:office-reviewed');assert.equal(alert.hidden,true);
 let resolve;reply=new Promise(r=>resolve=r);const pending=emit('wzos:office-sent');await Promise.resolve();
 session={role:'member'};await emit('wzos:session');resolve({pending_count:9});await pending;assert.equal(alert.hidden,true);
 const prior=calls;await emit('visibilitychange');assert.equal(calls,prior);
});
