const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const A='a'.repeat(24),B='b'.repeat(24),C='c'.repeat(24);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function fixture(){
 const events={},documentEvents={},body={children:[],append(node){this.children.push(node);}};
 let now=100000,version=A,reloads=0,requests=0,poll;
 const element=tag=>({tag,children:[],hidden:false,setAttribute(){},append(...nodes){this.children.push(...nodes);}});
 const document={body,visibilityState:'visible',querySelector:()=>({content:A}),createElement:element,
  addEventListener:(name,fn)=>documentEvents[name]=fn};
 const navigator={onLine:true};
 const window={location:{reload(){reloads++;}},addEventListener(name,fn){(events[name]??=[]).push(fn);},
  dispatchEvent(event){for(const fn of events[event.type]||[])fn(event);}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/app-updates.js','utf8'),
  {window,document,navigator,Event,AbortController,setTimeout,clearTimeout,Date:{now:()=>now},
   setInterval(fn){poll=fn;},async fetch(url,options){requests++;assert.equal(url,'/api/app/version');
    assert.equal(options.cache,'no-store');assert.equal(options.credentials,'same-origin');
    if(version instanceof Error)throw version;
    return {ok:true,json:async()=>({version})};}});
 await flush();
 return {body,events,document,navigator,window,get reloads(){return reloads;},get requests(){return requests;},
  async tick(value){version=value;now+=30001;await poll();await flush();},
  get banner(){return body.children[0];},get install(){return body.children[0].children[1];}};
}
test('unchanged release stays quiet; changed release offers a user-controlled update',async()=>{
 const f=await fixture();assert.equal(f.body.children.length,0);await f.tick(B);
 assert.equal(f.banner.hidden,false);assert.equal(f.reloads,0);f.install.onclick();assert.equal(f.reloads,1);
});
test('existing module beforeunload guards prevent update reload when work is unsaved',async()=>{
 const f=await fixture();await f.tick(B);let dirty=true;
 f.window.addEventListener('beforeunload',e=>{if(dirty)e.preventDefault();});
 f.install.onclick();assert.equal(f.reloads,0);assert.match(f.banner.children[0].textContent,/Save your changes/);
 dirty=false;f.install.onclick();assert.equal(f.reloads,1);
});
test('offline state and an active meeting block installation',async()=>{
 const f=await fixture();await f.tick(B);f.navigator.onLine=false;f.install.onclick();assert.equal(f.reloads,0);
 f.navigator.onLine=true;f.window.WzosDailyMeetings={isActive:()=>true};f.install.onclick();assert.equal(f.reloads,0);
 assert.match(f.banner.children[0].textContent,/Leave your meeting/);
});
test('Later dismisses only that release and rollback to the loaded release hides the prompt',async()=>{
 const f=await fixture();await f.tick(B);f.banner.children[2].onclick();await f.tick(B);assert.equal(f.banner.hidden,true);
 await f.tick(C);assert.equal(f.banner.hidden,false);f.banner.children[2].onclick();await f.tick(C);assert.equal(f.banner.hidden,true);
 await f.tick(B);assert.equal(f.banner.hidden,false);await f.tick(A);assert.equal(f.banner.hidden,true);
});
test('failed and invalid version checks never reload; hidden and offline pages do not poll',async()=>{
 const f=await fixture();await f.tick(new Error('offline'));await f.tick('<html>');assert.equal(f.body.children.length,0);
 const count=f.requests;f.document.visibilityState='hidden';await f.tick(B);assert.equal(f.requests,count);
 f.document.visibilityState='visible';f.navigator.onLine=false;await f.tick(B);assert.equal(f.requests,count);assert.equal(f.reloads,0);
});
