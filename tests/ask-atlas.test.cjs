const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function setup({getMedia}={}){
 class Node{constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.value='';this.hidden=false;this.disabled=false;}append(...nodes){this.children.push(...nodes);}prepend(...nodes){this.children.unshift(...nodes);}replaceChildren(...nodes){this.children=nodes;}setAttribute(){}remove(){this.removed=true;}set innerHTML(value){throw Error('Unsafe HTML rendering');}}
 const main=new Node('main'),nav=new Node('button'),events={},calls=[],spoken=[],captures=[];nav.id='atlas-nav';let session={id:'a',organization_id:'alpha',edition:'enterprise'},reply=null;
 const all=node=>[node,...node.children.flatMap(all)];
 const document={createElement:tag=>new Node(tag),getElementById:id=>id==='main'?main:id==='atlas-nav'?nav:all(main).find(n=>n.id===id),querySelector:()=>null,addEventListener:(name,fn)=>(events[name]??=[]).push(fn)};
 const emit=async(name,detail)=>{await Promise.all((events[name]||[]).map(fn=>fn({detail})));};
 const speechSynthesis={cancel(){},getVoices:()=>[{lang:'en-US',localService:false},{lang:'en-US',localService:true}],speak:value=>spoken.push(value)};
 class Recorder{constructor(){captures.push(this);}}
 const window={MediaRecorder:Recorder,wzosDeviceSetup:{status:async()=> 'granted',remembered:()=>true},wzosClock:{getSession:()=>session},wzosAccount:{headers:async()=>({})},showWzosView:view=>{emit('wzos:view',view);return true;},addEventListener(){},speechSynthesis,SpeechSynthesisUtterance:class{constructor(text){this.text=text;}}};
 const fetch=async(path,options)=>{calls.push({path,options});const body=path.endsWith('/config')?{enabled:true,inference_enabled:true,speech_enabled:!!getMedia}:reply?await reply(path):{results:[]};return{ok:true,json:async()=>body};};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/ask-atlas.js','utf8'),{window,document,fetch,MediaRecorder:Recorder,navigator:{onLine:true,mediaDevices:{getUserMedia:getMedia}},crypto:require('node:crypto').webcrypto,AbortController,URL,Date,speechSynthesis,SpeechSynthesisUtterance:window.SpeechSynthesisUtterance,MutationObserver:class{observe(){}},setInterval,clearInterval});
 const find=text=>all(main).find(n=>n.textContent===text),question=()=>all(main).find(n=>n.tag==='textarea');
 return{window,document,main,nav,calls,spoken,captures,all,emit,find,question,setReply:fn=>reply=fn,setSession:value=>session=value};
}
test('Enterprise opens the separate page; Core cannot open or fetch its config',async()=>{
 const h=setup();await h.emit('wzos:session');assert.match(h.nav.textContent,/Work Zone Guardian/);assert.equal(h.window.wzosAskAtlas.open(),true);assert.equal(h.question().maxLength,500);
 h.setSession({id:'b',edition:'core'});await h.emit('wzos:session');const count=h.calls.length;assert.equal(h.window.wzosAskAtlas.open(),false);assert.equal(h.calls.length,count);assert.equal(h.nav.textContent,'Atlas assistant');
});
test('answers render as text with citations; reading is explicit and uses a local voice',async()=>{
 const h=setup();await h.emit('wzos:session');h.window.wzosAskAtlas.open();h.question().value='Synthetic question';
 const hostile='<img src=x onerror=alert(1)>';
 h.setReply(async()=>({draft:{status:'draft',claims:[{text:hostile,citation_id:'source:1'}],unresolved:[]},citations:[{citation_id:'source:1',title:'Synthetic source',page:1,edition:'test',url:'javascript:alert(1)'}]}));
 await h.all(h.main).find(n=>n.tag==='button'&&n.textContent==='Ask Atlas').onclick();
 assert.ok(h.all(h.main).some(n=>n.textContent===hostile));assert.equal(h.spoken.length,0);
 const source=h.find('Synthetic source');assert.equal(source.href,undefined);
 h.find('Read aloud').onclick();assert.equal(h.spoken.length,1);assert.equal(h.spoken[0].voice.localService,true);
});
test('leaving discards a late reply and sends explicit cancellation without retaining the question',async()=>{
 const h=setup();await h.emit('wzos:session');h.window.wzosAskAtlas.open();h.question().value='Transient question';let resolve;
 h.setReply(path=>path.endsWith('/cancel')?Promise.resolve({state:'cancel_requested'}):new Promise(r=>resolve=r));
 const pending=h.all(h.main).find(n=>n.tag==='button'&&n.textContent==='Ask Atlas').onclick();await flush();await h.emit('wzos:view','home');await flush();
 resolve({draft:{status:'draft',claims:[{text:'Late answer'}],unresolved:[]}});await pending;
 assert.equal(h.question().value,'');assert.equal(h.all(h.main).some(n=>n.textContent==='Late answer'),false);assert.ok(h.calls.some(c=>c.path.endsWith('/cancel')));
});
test('a microphone grant arriving after backgrounding never starts recording or uploading',async()=>{
 let grant,stops=0;const h=setup({getMedia:()=>new Promise(resolve=>grant=resolve)});
 await h.emit('wzos:session');h.window.wzosAskAtlas.open();
 const pending=h.find('● Record question').onclick();await flush();
 h.document.hidden=true;await h.emit('visibilitychange');grant({getTracks:()=>[{stop:()=>stops++}]});await pending;
 assert.equal(stops,1);assert.equal(h.captures.length,0);assert.equal(h.calls.some(c=>c.path.includes('/transcribe')),false);
});
