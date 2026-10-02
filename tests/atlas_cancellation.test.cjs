const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {randomUUID}=require('node:crypto');
function helper(){
 const context={crypto:{randomUUID},AbortController,AbortSignal,DOMException,setTimeout};
 const code=fs.readFileSync('services/workspace_preview/static/workspace.js','utf8');
 vm.runInNewContext(code.slice(code.indexOf('async function cancellableAtlas'),code.indexOf('window.askAtlas=')),context);
 return context.cancellableAtlas;
}
test('stop uses captured identity and confirms application cancellation before releasing UI',async()=>{
 const stop=new AbortController(),headers={'X-WZOS-Organization':'original-org'},calls=[];
 let started;const entered=new Promise(r=>started=r);let statusReads=0;
 const api=async(path,options)=>{
  calls.push({path,options});assert.equal(options.headers,headers);
  if(path.endsWith('/chat')){started();return new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(new DOMException('Stopped','AbortError'))));}
  if(path.endsWith('/cancel'))return {state:'cancel_requested'};
  statusReads++;return {state:'cancelled',provider_stop_verified:false};
 };
 const pending=helper()(api,{question:'test'},stop.signal,headers);
 const checked=assert.rejects(pending,/reply was cancelled.*Background model processing/);
 await entered;stop.abort();await checked;
 assert.equal(statusReads,1);assert.equal(calls.length,3);
 const id=JSON.parse(calls[0].options.body).request_id;
 assert.equal(calls[1].path,`/api/assistant/requests/${id}/cancel`);
});
test('failed cancellation does not claim a confirmed stop',async()=>{
 const stop=new AbortController();let started;const entered=new Promise(r=>started=r);
 const api=async(path,options)=>{
  if(path.endsWith('/chat')){started();return new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('aborted'))));}
  throw new Error('offline');
 };
 const pending=helper()(api,{question:'test'},stop.signal,{});
 const checked=assert.rejects(pending,/Cancellation could not be confirmed/);
 await entered;stop.abort();await checked;
});
test('already aborted inputs never send a request; successful replies remove cancellation listener',async()=>{
 const stop=new AbortController();stop.abort();let calls=0;
 await assert.rejects(helper()(async()=>{calls++;},{},stop.signal,{}),{name:'AbortError'});
 assert.equal(calls,0);
 const active=new AbortController();await helper()(async()=>{calls++;return {answer:'ok'};},{},active.signal,{});
 active.abort();await Promise.resolve();assert.equal(calls,1);
});
