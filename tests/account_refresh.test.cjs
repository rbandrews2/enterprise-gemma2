// Run with node --test tests/account_refresh.test.cjs. No network or real credentials.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');

class Element {
 constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.value='';}
 append(...nodes){this.children.push(...nodes);}
 setAttribute(name,value){this.attributes??={};this.attributes[name]=value;} addEventListener(){} showModal(){} close(){} remove(){}
 reportValidity(){return true;}
 insertBefore(node){this.append(node);}
 querySelectorAll(tag){return this.children.flatMap(c=>[...(c.tag===tag?[c]:[]),...c.querySelectorAll(tag)]);}
 querySelector(selector){return this.children.find(c=>selector==='.'+c.className)||new Element('span');}
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));

function accountFailureFixture(fetch){
 const body=new Element('body'),bar=new Element('bar');
 const sandbox={window:{},document:{body,createElement:t=>new Element(t),querySelector:()=>bar},fetch,Date,URLSearchParams,location:{hostname:'localhost',reload(){}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/account.js','utf8'),sandbox);
 const account=sandbox.window.wzosAccount;account.start({auth_api_key:'synthetic-only'});
 const panel=body.children[0],form=panel.children.find(c=>c.tag==='form');
 const inputs=form.querySelectorAll('input');inputs[0].value='synthetic@example.test';inputs[1].value='synthetic-only';
 return {account,panel,form,inputs,message:panel.children[panel.children.length-1],signup:form.querySelectorAll('button').find(b=>b.textContent==='Create account')};
}
test('password eye shows and hides the same value and remasks before a request',async()=>{
 let requests=0;const ui=accountFailureFixture(async()=>{requests++;return {ok:false,json:async()=>({error:{message:'EMAIL_EXISTS'}})};});
 const eye=ui.form.querySelectorAll('button').find(b=>b.className==='password-visibility-button');
 assert.equal(ui.inputs[1].type,'password');assert.equal(eye.type,'button');
 assert.equal(eye.attributes['aria-label'],'Show password');assert.match(eye.innerHTML,/m3 3 18 18/);
 eye.onclick();assert.equal(ui.inputs[1].type,'text');assert.equal(eye.attributes['aria-label'],'Hide password');
 assert.equal(eye.attributes['aria-pressed'],'true');assert.doesNotMatch(eye.innerHTML,/m3 3 18 18/);
 assert.equal(ui.inputs[1].value,'synthetic-only');assert.equal(requests,0);
 eye.onclick();assert.equal(ui.inputs[1].type,'password');eye.onclick();
 await ui.signup.onclick();assert.equal(ui.inputs[1].type,'password');assert.equal(requests,1);
});
for(const [code,expected] of [
 ['WEAK_PASSWORD : private provider detail','Choose a stronger password'],
 ['EMAIL_EXISTS','An account may already exist'],
 ['INVALID_EMAIL','Enter a valid email'],
 ['OPERATION_NOT_ALLOWED','temporarily unavailable'],
 ['TOO_MANY_ATTEMPTS_TRY_LATER','Wait a few minutes'],
 ['UNKNOWN_PRIVATE_DIAGNOSTIC','Check your details or try again']
])test('account creation reports safe actionable error '+code.split(' : ')[0],async()=>{
 const ui=accountFailureFixture(async()=>({ok:false,json:async()=>({error:{message:code}})}));
 await ui.signup.onclick();assert.ok(ui.message.textContent.includes(expected));
 assert.ok(!ui.message.textContent.includes('private provider detail'));
 assert.ok(!ui.message.textContent.includes('UNKNOWN_PRIVATE_DIAGNOSTIC'));
 assert.equal((await ui.account.headers()).Authorization,undefined);
});
for(const mode of ['network','malformed'])test('account creation handles '+mode+' response without leaking provider error',async()=>{
 const ui=accountFailureFixture(async()=>{if(mode==='network')throw Error('private URL and key');return {ok:false,json:async()=>{throw Error('private server body');}};});
 await ui.signup.onclick();assert.match(ui.message.textContent,mode==='network'?/could not be reached/:/unexpected response/);
 assert.doesNotMatch(ui.message.textContent,/private/);
});
test('created account with failed verification request clears tokens and permits safe resend',async()=>{
 const ui=accountFailureFixture(async url=>url.includes('signUp')?{ok:true,json:async()=>({idToken:'synthetic-token',refreshToken:'synthetic-refresh',expiresIn:3600})}:{ok:false,json:async()=>({error:{message:'PRIVATE_MAIL_FAILURE'}})});
 await ui.signup.onclick();assert.match(ui.message.textContent,/account was created/);
 assert.match(ui.message.textContent,/Resend verification email/);
 assert.equal(ui.inputs[1].value,'');assert.equal((await ui.account.headers()).Authorization,undefined);
});
test('failed sign-in does not distinguish missing account from invalid credentials',async()=>{
 const ui=accountFailureFixture(async()=>({ok:false,json:async()=>({error:{message:'EMAIL_NOT_FOUND'}})}));
 ui.form.onsubmit({preventDefault(){}});await settle();
 assert.match(ui.message.textContent,/Check your details or try again/);
 assert.doesNotMatch(ui.message.textContent,/EMAIL_NOT_FOUND|does not exist/);
});

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

async function organizationFixture(failure){
 const requests=[];
 const ui=accountFailureFixture(async(url,options)=>{
  requests.push({url,body:options.body});
  if(url.includes('signInWithPassword'))return {ok:true,json:async()=>({idToken:'synthetic',refreshToken:'synthetic',expiresIn:3600})};
  if(url==='/api/account')return {ok:true,json:async()=>({organizations:[]})};
  return failure;
 });
 ui.form.onsubmit({preventDefault(){}});await settle();
 return {...ui,requests,choices:ui.panel.children.find(c=>c.className==='account-choices')};
}
test('organization setup explains missing fields without submitting empty requests',async()=>{
 const ui=await organizationFixture();
 const inputs=ui.choices.querySelectorAll('input'),buttons=ui.choices.querySelectorAll('button');
 await buttons.find(b=>b.textContent==='Create organization').onclick();
 assert.match(ui.message.textContent,/organization name/);
 inputs[0].value='Synthetic company';
 await buttons.find(b=>b.textContent==='Create organization').onclick();
 assert.match(ui.message.textContent,/activation code is required/);
 await buttons.find(b=>b.textContent==='Join organization').onclick();
 assert.match(ui.message.textContent,/invitation token is required/);
 assert.equal(ui.requests.filter(r=>r.url==='/api/account/organizations'||r.url==='/api/account/join').length,0);
});
for(const field of ['activation_code','token'])test('organization validation safely explains '+field,async()=>{
 const ui=await organizationFixture({ok:false,status:422,json:async()=>({detail:[{loc:['body',field],input:'PRIVATE_VALUE',msg:'PRIVATE_ERROR'}]})});
 const inputs=ui.choices.querySelectorAll('input'),buttons=ui.choices.querySelectorAll('button');
 inputs[0].value=' Synthetic company ';inputs[1].value='x'.repeat(32);inputs[2].value='x'.repeat(32);
 await buttons.find(b=>b.textContent===(field==='token'?'Join organization':'Create organization')).onclick();
 assert.match(ui.message.textContent,field==='token'?/invitation token supplied/:/activation code supplied/);
 assert.doesNotMatch(ui.message.textContent,/PRIVATE/);
});
