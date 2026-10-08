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
for(const mode of ['opt-in','opt-out','restore']) test('persistent sign-in '+mode,async()=>{
 const body=new Element('body'),bar=new Element('bar');let cookie=mode==='restore',exchanges=0,signins=0,reloads=0;
 const response=(data,ok=true)=>({ok,json:async()=>data});
 const fetch=async(url,options)=>{
  if(url.includes('signInWithPassword')){signins++;return response({idToken:'first',refreshToken:'refresh',expiresIn:3600});}
  if(url==='/api/account/logout'){cookie=false;return response({signed_out:true});}
  if(url==='/api/account/session'){assert.equal(options.headers.Authorization,'Bearer first');assert.equal(options.headers['X-WZOS-Session'],'1');cookie=true;exchanges++;return response({persistent:true});}
  if(url==='/api/account'){if(!cookie&&!options.headers.Authorization)return response({detail:'Sign in'},false);return response({organizations:[{id:'org-1',name:'Synthetic',role:'member',edition:'core'}]});}
  if(url==='/api/session')return response({organization:'Synthetic',can_manage_team:false});
  throw Error('Unexpected '+url);
 };
 const sandbox={window:{},document:{body,createElement:t=>new Element(t),querySelector:()=>bar},fetch,Date,URLSearchParams,location:{hostname:'localhost',reload(){reloads++;}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/account.js','utf8'),sandbox);
 const account=sandbox.window.wzosAccount,started=account.start({auth_api_key:'fake',persistent_sessions:true});await settle();
 const panel=body.children[0],form=panel.children.find(c=>c.tag==='form');
 if(mode!=='restore'){const inputs=form.querySelectorAll('input');inputs[0].value='test@example.test';inputs[1].value='password';assert.equal(inputs[2].checked,false);inputs[2].checked=mode==='opt-in';form.onsubmit({preventDefault(){}});await settle();}
 const choices=panel.children.find(c=>c.className==='account-choices');assert.ok(choices);await choices.children[0].onclick();await started;
 const headers=await account.headers();assert.equal(headers['X-WZOS-Organization'],'org-1');assert.equal(headers['X-WZOS-Session'],'1');assert.equal(headers.Authorization,mode==='opt-out'?'Bearer first':undefined);
 assert.equal(exchanges,mode==='opt-in'?1:0);assert.equal(signins,mode==='restore'?0:1);
 await bar.children.find(c=>c.textContent==='Sign out').onclick();assert.equal(cookie,false);assert.equal(reloads,1);
});
for(const cancelled of [false,true]) test('passkey sign-in '+(cancelled?'cancellation retains password fallback':'uses Google exchange and organization checks'),async()=>{
 const body=new Element('body'),bar=new Element('bar');let exchanged=0,verified=0;
 const ok=data=>({ok:true,json:async()=>data});
 const fetch=async(url,options)=>{
  if(url==='/api/account/passkeys/login/options')return ok({challenge:'YWJj',rpId:'localhost',userVerification:'required'});
  if(url==='/api/account/passkeys/login/verify'){
   verified++;const credential=JSON.parse(options.body).credential;
   assert.equal(credential.response.signature,'AQID');assert.equal(credential.rawId,'AQID');return ok({custom_token:'verified-custom'});
  }
  if(url.includes('signInWithCustomToken')){exchanged++;assert.equal(JSON.parse(options.body).token,'verified-custom');return ok({idToken:'google-id',refreshToken:'refresh',expiresIn:3600});}
  if(url==='/api/account'){assert.equal(options.headers.Authorization,'Bearer google-id');return ok({organizations:[{id:'org-1',name:'Synthetic',role:'member',edition:'core'}]});}
  if(url==='/api/session')return ok({organization:'Synthetic',can_manage_team:false});
  throw Error('Unexpected request '+url);
 };
 const buffer=Uint8Array.from([1,2,3]).buffer;
 const sandbox={window:{isSecureContext:true,PublicKeyCredential:function(){}},navigator:{credentials:{get:async({publicKey})=>{
  assert.deepEqual(Array.from(publicKey.challenge),[97,98,99]);assert.equal(publicKey.userVerification,'required');
  if(cancelled){const e=Error();e.name='NotAllowedError';throw e;}
  return {id:'AQID',rawId:buffer,type:'public-key',response:{clientDataJSON:buffer,authenticatorData:buffer,signature:buffer,userHandle:buffer},getClientExtensionResults:()=>({})};
 }}},atob,btoa,Uint8Array,document:{body,createElement:t=>new Element(t),querySelector:()=>bar},fetch,Date,URLSearchParams,location:{hostname:'localhost',reload(){}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/account.js','utf8'),sandbox);
 const started=sandbox.window.wzosAccount.start({auth_api_key:'fake',passkeys:true});
 const panel=body.children[0],form=panel.children.find(c=>c.tag==='form');
 const button=form.children.find(c=>c.textContent==='Sign in with a passkey');assert.equal(button.hidden,false);
 await button.onclick();await settle();
 if(cancelled){assert.equal(verified,0);assert.equal(exchanged,0);assert.match(panel.children.at(-1).textContent,/cancelled or timed out/);assert.equal(form.children.find(c=>c.textContent==='Sign in').disabled,false);}
 else{const choices=panel.children.find(c=>c.className==='account-choices');await choices.children[0].onclick();await started;assert.equal(exchanged,1);assert.equal(verified,1);assert.equal((await sandbox.window.wzosAccount.headers())['X-WZOS-Organization'],'org-1');}
});
