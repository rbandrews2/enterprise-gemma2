const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function harness(failed=false){
 const events={},fetches=[],puts=[],entries=new Map();
 const cache={match:async key=>entries.get(typeof key==='string'?key:key.url),put:async(key,value)=>{puts.push(key);entries.set(typeof key==='string'?key:key.url,value);}};
 const response={ok:true,headers:{get:()=> '1'},clone(){return this;}};
 const context={URL,setTimeout,clearTimeout,self:{location:{origin:'https://app.workzoneos.org'},addEventListener:(name,fn)=>events[name]=fn,skipWaiting:async()=>{},clients:{claim:async()=>{}}},caches:{open:async()=>cache,keys:async()=>[],delete:async()=>true},fetch:async request=>{fetches.push(request);if(failed)throw Error("offline");return response;}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/app-shell-worker.js','utf8'),context);
 async function run(path,{method='GET',mode='cors',cache='default'}={}){let result;events.fetch({request:{url:'https://app.workzoneos.org'+path,method,mode,cache},respondWith:p=>result=p,waitUntil:p=>p.catch(()=>{})});return result?await result:null;}
 return {run,fetches,puts,entries};
}
test('private APIs, exports, media, queries and mutations never enter shell cache',async()=>{
 const h=harness();for(const path of ['/api/session','/api/forms?v=abcdef123456abcdef123456','/uploads/private.png?v=abcdef123456abcdef123456','/recording.webm','/?activation=private'])assert.equal(await h.run(path,{mode:'navigate'}),null);
 assert.equal(await h.run('/',{method:'POST',mode:'navigate'}),null);assert.equal(h.fetches.length,0);assert.equal(h.puts.length,0);
});
test('current shell wins for update and rollback, with offline cached fallback',async()=>{
 const h=harness(),old={old:true};h.entries.set('/',old);assert.notEqual(await h.run('/',{mode:'navigate'}),old);
 const offline=harness(true);offline.entries.set('/',old);assert.equal(await offline.run('/',{mode:'navigate'}),old);
 const fresh=await h.run('/',{mode:'navigate',cache:'reload'});assert.notEqual(fresh,old);assert.equal(h.entries.get('/'),fresh);
});
test('versioned public assets cache; unversioned assets do not intercept',async()=>{
 const h=harness();assert.equal(await h.run('/workspace.js'),null);await h.run('/workspace.js?v=abcdef123456abcdef123456');assert.equal(h.puts.length,1);
});
