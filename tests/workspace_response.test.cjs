const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function apiFixture(response){
 const code=fs.readFileSync('services/workspace_preview/static/workspace.js','utf8');
 const scope={fetch:async()=>response,window:{wzosAccount:{headers:async()=>({})}},session:null,$:()=>({value:'synthetic'})};
 vm.runInNewContext(code.slice(code.indexOf('async function api('),code.indexOf('function lock(')),scope);
 return scope.api;
}
for(const status of [200,403,502])test('workspace handles HTML response without claiming saved state '+status,async()=>{
 const api=apiFixture({ok:status===200,status,json:async()=>{throw new SyntaxError('Unexpected token < PRIVATE_HTML');}});
 await assert.rejects(api('/api/session'),e=>e.status===status&&/Nothing was confirmed saved/.test(e.message)&&/reconnect/.test(e.message)&&!/PRIVATE_HTML|Unexpected token/.test(e.message));
});
test('workspace preserves valid JSON and server access denial',async()=>{
 assert.equal((await apiFixture({ok:true,status:200,json:async()=>({id:'synthetic'})})('/api/session')).id,'synthetic');
 await assert.rejects(apiFixture({ok:false,status:403,json:async()=>({detail:'Active organization membership required'})})('/api/session'),e=>e.status===403&&e.message==='Active organization membership required');
});
