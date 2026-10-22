const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function fixture(){
 const events={},writes=[],deleted=[],network=[];
 let marked=false;
 const cache={match:async()=>null,put:async(key)=>writes.push(typeof key==='string'?key:key.url)};
 const self={location:{origin:'https://wzos.example.test'},clients:{claim:async()=>{}},
  skipWaiting:async()=>{},addEventListener:(name,fn)=>events[name]=fn};
 const caches={open:async()=>cache,keys:async()=>['wzos-public-assets-old','wzos-offline-punches','other-app'],
  delete:async key=>deleted.push(key)};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/app-shell-worker.js','utf8'),{
  self,caches,URL,setTimeout,clearTimeout,fetch:async request=>{network.push(request);return{
   ok:true,headers:{get:()=>marked?'1':null},clone(){return this;}};}});
 return {writes,deleted,network,set marked(value){marked=value;},async install(){let done;events.install({waitUntil:p=>done=p});await done;},
  async activate(){let done;events.activate({waitUntil:p=>done=p});await done;},
  async request(path,options={}){let response;const waits=[];events.fetch({request:{method:'GET',mode:'cors',cache:'default',url:'https://wzos.example.test'+path,...options},
   respondWith:p=>response=p,waitUntil:p=>waits.push(p)});if(response)await response;await Promise.all(waits);return Boolean(response);}};
}

test('API, files, exports, recordings and external requests never enter the public cache',async()=>{
 const f=fixture();f.marked=true;
 for(const path of ['/api/account','/api/field-voice/transcribe','/api/form-submissions','/api/files/abc','/report.pdf','/audio.webm'])
  assert.equal(await f.request(path),false,path);
 assert.equal(await f.request('/workspace.js?v='+'a'.repeat(24),{method:'POST'}),false);
 assert.equal(await f.request('/workspace.js?v='+'a'.repeat(24),{url:'https://external.test/workspace.js?v='+'a'.repeat(24)}),false);
 assert.equal(f.writes.length,0);assert.equal(f.network.length,0);
});

test('unmarked shell and static responses are never persisted',async()=>{
 const f=fixture();await f.install();assert.equal(f.writes.length,0);
 assert.equal(await f.request('/workspace.js?v='+'a'.repeat(24)),true);
 assert.equal(f.writes.length,0);
});

test('only marked public shell and release-addressed assets are cached',async()=>{
 const f=fixture();f.marked=true;await f.install();assert.deepEqual(f.writes,['/']);
 assert.equal(await f.request('/workspace.js'),false);
 assert.equal(await f.request('/workspace.js?v=invalid'),false);
 assert.equal(await f.request('/workspace.js?v='+'a'.repeat(24)),true);
 assert.equal(f.writes.length,2);
 assert.equal(f.network[0],'/' );
});

test('activation removes only old public assets and preserves offline device records',async()=>{
 const f=fixture();await f.activate();assert.deepEqual(f.deleted,['wzos-public-assets-old']);
});

test('query-bearing navigation and worker script are not intercepted',async()=>{
 const f=fixture();assert.equal(await f.request('/?reset=synthetic',{mode:'navigate'}),false);
 assert.equal(await f.request('/app-shell-worker.js?v='+'a'.repeat(24)),false);
 assert.equal(f.network.length,0);
});
