"use strict";
// Google handles passwords. Tokens remain in memory and are never persisted in localStorage.
window.wzosAccount = (() => {
 let token=null, refresh=null, expires=0, organization=null, key=null, refreshing=null;
 let authBase='https://identitytoolkit.googleapis.com', tokenBase='https://securetoken.googleapis.com';
 const element=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 async function provider(action,body){
  const r=await fetch(`${authBase}/v1/accounts:${action}?key=${encodeURIComponent(key)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data=await r.json();if(!r.ok)throw Error('Account request could not be completed. Check your details or try again.');return data;
 }
 async function headers(){
  if(!token)return {};
  if(Date.now()>expires-60000){
   if(!refreshing)refreshing=(async()=>{
    const r=await fetch(`${tokenBase}/v1/token?key=${encodeURIComponent(key)}`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'refresh_token',refresh_token:refresh})});
    if(!r.ok)throw Error('Sign in again to continue.');const d=await r.json();token=d.id_token;refresh=d.refresh_token;expires=Date.now()+Number(d.expires_in)*1000;
   })().finally(()=>refreshing=null);
   await refreshing;
  }
  return {Authorization:'Bearer '+token,'X-WZOS-Organization':organization||''};
 }
 async function api(path,body,method){
  const r=await fetch(path,{method:method||(body?'POST':'GET'),headers:{'Content-Type':'application/json',...await headers()},...(body?{body:JSON.stringify(body)}:{})});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Account request failed');return d;
 }
 async function start(config){
  key=config.auth_api_key;
  if(config.auth_emulator){
   if(!['127.0.0.1','localhost'].includes(location.hostname)||config.auth_emulator!=='http://127.0.0.1:9099')throw Error('Local authentication configuration refused.');
   authBase=config.auth_emulator+'/identitytoolkit.googleapis.com';tokenBase=config.auth_emulator+'/securetoken.googleapis.com';
  }
  const panel=element('dialog');panel.className='account-dialog';
  const title=element('h2','Welcome to WZOS');const note=element('p',key?'Sign in to your organization.':'Account sign-in is awaiting Google authentication configuration.');
  const email=element('input');email.type='email';email.autocomplete='username';email.required=true;
  const password=element('input');password.type='password';password.autocomplete='current-password';password.required=true;
  const form=element('form');const emailLabel=element('label','Email');emailLabel.append(email);const passwordLabel=element('label','Password');passwordLabel.append(password);
  const signin=element('button','Sign in');signin.type='submit';signin.disabled=!key;
  const signup=element('button','Create account');signup.type='button';signup.disabled=!key;
  const reset=element('button','Reset password');reset.type='button';reset.disabled=!key;
  const verify=element('button','Resend verification email');verify.type='button';verify.disabled=!key;
  const message=element('p');message.setAttribute('role','status');
  form.append(emailLabel,passwordLabel,signin,signup,reset,verify);panel.append(title,note,form,message);document.body.append(panel);panel.addEventListener('cancel',e=>e.preventDefault());panel.showModal();
  const session=await new Promise(resolve=>{
   let working=false;
   async function run(task){if(working)return;working=true;for(const b of panel.querySelectorAll('button'))b.disabled=true;try{await task();}catch(e){message.textContent=e.message;}finally{working=false;for(const b of panel.querySelectorAll('button'))b.disabled=!key;}}
   async function choose(){
    const account=await api('/api/account');message.textContent='';password.value='';form.hidden=true;title.textContent='Your organization';note.textContent='Select an organization or use your activation code or invitation.';
    let choices=panel.querySelector('.account-choices');if(choices)choices.remove();choices=element('div');choices.className='account-choices';
    for(const org of account.organizations){const button=element('button',`${org.name}  -  ${org.role}  -  ${org.edition}`);button.onclick=()=>run(async()=>{organization=org.id;const current=await api('/api/session');panel.close();panel.remove();resolve(current);});choices.append(button);}
    const name=element('input');name.placeholder='Organization name';name.setAttribute('aria-label','Organization name');
    const activation=element('input');activation.placeholder='Activation code';activation.setAttribute('aria-label','Activation code');
    const create=element('button','Create organization');create.onclick=()=>run(async()=>{await api('/api/account/organizations',{name:name.value,activation_code:activation.value});await choose();});
    const invitation=element('input');invitation.placeholder='Invitation token';invitation.setAttribute('aria-label','Invitation token');
    const join=element('button','Join organization');join.onclick=()=>run(async()=>{await api('/api/account/join',{token:invitation.value});await choose();});
    choices.append(name,activation,create,invitation,join);panel.insertBefore(choices,message);
   }
   async function login(create){
    if(!email.reportValidity()||!password.reportValidity())return;
    const data=await provider(create?'signUp':'signInWithPassword',{email:email.value.trim(),password:password.value,returnSecureToken:true});
    token=data.idToken;refresh=data.refreshToken;expires=Date.now()+Number(data.expiresIn)*1000;
    if(create){try{await provider('sendOobCode',{requestType:'VERIFY_EMAIL',idToken:token});message.textContent='Check your email to verify your account, then sign in.';}finally{token=null;refresh=null;expires=0;password.value='';}return;}
    await choose();
   }
   form.onsubmit=e=>{e.preventDefault();run(()=>login(false));};signup.onclick=()=>run(()=>login(true));
   reset.onclick=()=>run(async()=>{if(!email.reportValidity())return;await provider('sendOobCode',{requestType:'PASSWORD_RESET',email:email.value.trim()});message.textContent='If the account is eligible, a reset email will arrive.';});
   verify.onclick=()=>run(async()=>{
    if(!email.reportValidity()||!password.reportValidity())return;
    const data=await provider('signInWithPassword',{email:email.value.trim(),password:password.value,returnSecureToken:true});
    try{await provider('sendOobCode',{requestType:'VERIFY_EMAIL',idToken:data.idToken});message.textContent='Check your email to verify your account, then sign in.';}finally{password.value='';}
   });
  });
  const controls=document.querySelector('.preview-bar');
  if(session.can_manage_team){const manage=element('button','Team access');manage.onclick=async()=>{
   const dialog=element('dialog');dialog.className='account-dialog';const status=element('p');status.setAttribute('role','status');const close=element('button','Close');close.onclick=()=>{dialog.close();dialog.remove();};dialog.append(element('h2','Organization access'),status,close);document.body.append(dialog);dialog.showModal();
   try{const data=await api('/api/account/members');
    const email=element('input');email.type='email';email.placeholder='Member email';email.setAttribute('aria-label','Member email');
    const role=element('select');role.setAttribute('aria-label','Invitation role');for(const value of (data.can_change_access?['member','admin']:['member'])){const option=element('option',value);option.value=value;role.append(option);}
    const invite=element('button','Create invitation');invite.onclick=async()=>{invite.disabled=true;try{const result=await api('/api/account/invitations',{email:email.value,role:role.value});const output=element('textarea');output.readOnly=true;output.value=result.token;output.setAttribute('aria-label','Private invitation token');dialog.append(output);status.textContent='Invitation created for this email. Share privately. No message was sent.';}catch(e){status.textContent=e.message;}finally{invite.disabled=false;}};dialog.append(email,role,invite);
    for(const member of data.items){const row=element('section');row.append(element('p',`${member.name}   -   ${member.role}   -   ${member.active?'Active':'Disabled'}`));if(data.can_change_access){const select=element('select');select.setAttribute('aria-label','Role for '+member.name);for(const value of ['member','admin']){const option=element('option',value);option.value=value;select.append(option);}select.value=member.role;const active=element('input');active.type='checkbox';active.checked=Boolean(member.active);const label=element('label','Active membership');label.append(active);const save=element('button','Save access');save.onclick=async()=>{save.disabled=true;try{await api('/api/account/members/'+encodeURIComponent(member.id),{role:select.value,active:active.checked},'PUT');status.textContent='Access updated. Changes apply on the next request.';if(member.id===session.id)location.reload();}catch(e){status.textContent=e.message;}finally{save.disabled=false;}};row.append(select,label,save);}dialog.append(row);}
   }catch(e){status.textContent=e.message;}
  };controls.append(manage);}
  controls.querySelector('strong').textContent='WZOS ACCOUNT';controls.querySelector('span').textContent=session.organization;
  const logout=element('button','Sign out');logout.onclick=()=>{token=null;refresh=null;location.reload();};controls.append(logout);
  document.querySelector('.app-footer span:last-child').textContent='Private organization workspace';
  return session;
 }
 return {headers,start};
})();
