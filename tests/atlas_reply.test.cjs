const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const context={};
const source=fs.readFileSync('services/workspace_preview/static/assistant.js','utf8');
vm.runInNewContext(source.slice(0,source.indexOf('(() => {')),context);
function element(tagName){return {tagName,children:[],textContent:'',append(...nodes){this.children.push(...nodes);}};}
const doc={createElement:element,createTextNode:text=>({textContent:text})};
function text(node){return node.textContent+((node.children||[]).map(text).join(''));}
test('reply rendering keeps model HTML inert and formats only supported markup',()=>{
 const root=context.renderAtlasReply(doc,'**Review**\n1. First\n2. Second\n\n<img src=x onerror=alert(1)>\n- <script>bad()</script>');
 assert.deepEqual(root.children.map(x=>x.tagName),['p','ol','p','ul']);
 assert.equal(root.children[0].children[1].tagName,'strong');
 assert.equal(root.children[1].children.length,2);
 assert.match(text(root),/<img src=x onerror=alert\(1\)>/);
 const tags=node=>[node.tagName,...(node.children||[]).flatMap(tags)].filter(Boolean);
 assert.equal(tags(root).some(t=>['script','img','a'].includes(t)),false);
});
test('status distinguishes enabled cold inference from explicitly disabled inference',()=>{
 assert.match(context.atlasConnectionMessage({ready:false,conversation_enabled:true}),/first reply may take/);
 assert.match(context.atlasConnectionMessage({ready:false,conversation_enabled:false}),/switched off/);
 assert.match(context.atlasConnectionMessage({ready:true,conversation_enabled:true}),/is ready/);
});

test('waiting notices stop after completion or cancellation and never claim measured progress',()=>{
 for(const abort of [false,true]){
  const pending=new Map(),messages=[];let serial=0;
  const clock={setTimeout(fn,delay){pending.set(++serial,{fn,delay});return serial;},clearTimeout(id){pending.delete(id);}};
  const controller=new AbortController();
  const stop=context.startAtlasWait(message=>messages.push(message),controller.signal,clock);
  assert.equal(messages.length,1);
  const callbacks=[...pending.values()];
  callbacks[0].fn();assert.match(messages.at(-1),/may take a few minutes/);
  if(abort)controller.abort();else stop();
  assert.equal(pending.size,0);
  const count=messages.length;callbacks.forEach(x=>x.fn());assert.equal(messages.length,count);
  assert.equal(messages.some(x=>/\d+%|Gemma/.test(x)),false);
 }
 const controller=new AbortController();controller.abort();
 context.startAtlasWait(()=>assert.fail('No notice after abort'),controller.signal,{});
});
