// Run with node --test tests/account_refresh.test.cjs. No network or real credentials.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

class Element {
 constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.value='';}
 append(...nodes){this.children.push(...nodes);}
 setAttribute(){} addEventListener(){} showModal(){} close(){} remove(){}
 reportValidity(){return true;}
 insertBefore(node){this.append(node);}
 querySelectorAll(tag){return this.children.flatMap(c=>[...(c.tag===tag?[c]:[]),...c.querySelectorAll(tag)]);}
 querySelector(selector){return this.children.find(c=>selector==='.'+c.className)||new Element('span');}
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));

for (const authHeader of ['Authorization','X-WZOS-Authorization']) test(authHeader+': session refresh is shared, preserves organization, and fails closed',async()=>{
 const body=new Element('body'),bar=new Element('bar');let now=0,refreshes=0,fail=false;
 const document={body,createElement:t=>new Element(t),querySelector:()=>bar};
 const response=data=>({ok:true,json:async()=>data});
 const fetch=async(url,options)=>{
  if(url.includes('signInWithPassword'))return response({idToken:'first',refreshToken:'refresh',expiresIn:3600});
  if(url.includes('/v1/token')){refreshes++;await settle();return fail?{ok:false}:response({id_token:'renewed',refresh_token:'rotated',expires_in:3600});}
  if(url==='/api/account')return response({organizations:[{id:'org-1',name:'Synthetic',role:'member',edition:'core'}]});
  if(url==='/api/session')return response({organization:'Synthetic',can_manage_team:false});
  throw Error('Unexpected request '+url);
 };
 const sandbox={window:{},document,fetch,Date:{now:()=>now},URLSearchParams,location:{hostname:'localhost',reload(){}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/account.js','utf8'),sandbox);
 const account=sandbox.window.wzosAccount;
 const started=account.start({auth_api_key:'fake',auth_header:authHeader});
 const panel=body.children[0],form=panel.children.find(c=>c.tag==='form');
 const inputs=form.querySelectorAll('input');inputs[0].value='synthetic@example.test';inputs[1].value='fake';
 form.onsubmit({preventDefault(){}});await settle();
 const choices=panel.children.find(c=>c.className==='account-choices');assert.ok(choices);
 await choices.children[0].onclick();await started;
 assert.equal((await account.headers())[authHeader],'Bearer first');
 now=3550*1000;
 const headers=await Promise.all([account.headers(),account.headers(),account.headers()]);
 assert.equal(refreshes,1);
 for(const h of headers){assert.equal(h[authHeader],'Bearer renewed');assert.equal(h['X-WZOS-Organization'],'org-1');}
 now+=3550*1000;fail=true;
 await assert.rejects(account.headers(),/Sign in again/);
 fail=false;
 assert.equal((await account.headers())[authHeader],'Bearer renewed');
 assert.equal(refreshes,3);
});
