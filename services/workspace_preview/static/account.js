"use strict";
// Google handles passwords. Tokens remain in memory and are never persisted in localStorage.
window.wzosAccount = (() => {
 let token=null, refresh=null, expires=0, organization=null, key=null, refreshing=null;
 let authHeader='Authorization';
 let authBase='https://identitytoolkit.googleapis.com', tokenBase='https://securetoken.googleapis.com';
 const from64=s=>Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
 const to64=b=>btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 function optionsFromJSON(options){
  const result={...options,challenge:from64(options.challenge)};
  if(options.user)result.user={...options.user,id:from64(options.user.id)};
  for(const field of ['allowCredentials','excludeCredentials'])if(options[field])result[field]=options[field].map(c=>({...c,id:from64(c.id)}));
  return result;
 }
 function credentialJSON(credential){
  const r=credential.response, response={clientDataJSON:to64(r.clientDataJSON)};
  for(const field of ['attestationObject','authenticatorData','signature','userHandle'])if(r[field])response[field]=to64(r[field]);
  if(r.getTransports)response.transports=r.getTransports();
  return {id:credential.id,rawId:to64(credential.rawId),type:credential.type,response,clientExtensionResults:credential.getClientExtensionResults()};
 }
 async function passkeyCeremony(kind){
  try{
   const options=await api(`/api/account/passkeys/${kind}/options`,{});
   const credential=await navigator.credentials[kind==='register'?'create':'get']({publicKey:optionsFromJSON(options)});
   if(!credential)throw Error('Passkey request cancelled. You can use your password.');
   return await api(`/api/account/passkeys/${kind}/verify`,{credential:credentialJSON(credential)});
  }catch(e){if(e.name==='NotAllowedError'||e.name==='AbortError')throw Error('Passkey request cancelled or timed out. You can use your password.');throw e;}
 }
 const element=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 function providerMessage(action,data){
  // Never display provider payloads: they may contain identifiers or configuration.
  const code=typeof data?.error?.message==='string'?data.error.message.split(' : ')[0].split(':')[0].trim():'';
  if(code==='INVALID_EMAIL')return 'Enter a valid email address.';
  if(action==='signInWithPassword'&&['INVALID_LOGIN_CREDENTIALS','INVALID_PASSWORD','EMAIL_NOT_FOUND'].includes(code))return 'Incorrect password or username.';
  if(action==='signUp'&&code==='WEAK_PASSWORD')return 'Choose a stronger password that meets the account password requirements.';
  if(action==='signUp'&&code==='EMAIL_EXISTS')return 'An account may already exist for this email. Use Sign in or Reset password.';
  if(code==='TOO_MANY_ATTEMPTS_TRY_LATER'||code==='QUOTA_EXCEEDED')return 'Too many account requests. Wait a few minutes before trying again.';
  if(['OPERATION_NOT_ALLOWED','CONFIGURATION_NOT_FOUND','API_KEY_INVALID','API_KEY_SERVICE_BLOCKED'].includes(code))return 'Account sign-in is temporarily unavailable. Contact your organization administrator.';
  return 'Account request could not be completed. Check your details or try again.';
 }
 async function provider(action,body){
  let r;
  try{r=await fetch(`${authBase}/v1/accounts:${action}?key=${encodeURIComponent(key)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});}
  catch(e){throw Error('The account service could not be reached. Check your connection and try again.');}
  let data;try{data=await r.json();}catch(e){throw Error('The account service returned an unexpected response. Try again later.');}
  if(!r.ok)throw Error(providerMessage(action,data));return data;
 }
 async function headers(){
  if(!token)return {"X-WZOS-Session":"1","X-WZOS-Organization":organization||""};
  if(Date.now()>expires-60000){
   if(!refreshing)refreshing=(async()=>{
    const r=await fetch(`${tokenBase}/v1/token?key=${encodeURIComponent(key)}`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'refresh_token',refresh_token:refresh})});
    if(!r.ok)throw Error('Sign in again to continue.');const d=await r.json();token=d.id_token;refresh=d.refresh_token;expires=Date.now()+Number(d.expires_in)*1000;
   })().finally(()=>refreshing=null);
   await refreshing;
  }
  return {'X-WZOS-Session':'1',[authHeader]:'Bearer '+token,'X-WZOS-Organization':organization||''};
 }
 async function api(path,body,method){
  const task=async signal=>{
  let r;try{const auth=await headers();if(signal?.aborted)throw Error('Request cancelled.');r=await fetch(path,{method:method||(body?'POST':'GET'),...(signal?{signal}:{}),headers:{'Content-Type':'application/json',...auth},...(body?{body:JSON.stringify(body)}:{})});}catch(e){throw Error('The account service could not be reached. Check your connection and try again.');}
  let d;try{d=await r.json();}catch(e){throw Error('The account service returned an unexpected response. Try again later.');}
  if(!r.ok){
   if(r.status===422){
    const fields=Array.isArray(d.detail)?d.detail.map(item=>item?.loc?.[1]):[];
    if(fields.includes('name'))throw Error('Enter an organization name between 2 and 120 characters.');
    if(fields.includes('activation_code'))throw Error('Enter the activation code supplied for your organization (32–128 characters).');
    if(fields.includes('token'))throw Error('Enter the invitation token supplied by your organization administrator (32–128 characters).');
    throw Error('Check the required fields and try again.');
   }
   const error=Error(typeof d.detail==='string'?d.detail:'Account request failed. Try again or contact your organization administrator.');error.status=r.status;throw error;
  }return d;};
  return window.wzosStartup?.request&&!body&&!method&&['/api/account','/api/session'].includes(path)?window.wzosStartup.request(task):task();
 }
 function createManaged(api){
  const dialog=element('dialog');dialog.className='account-dialog';
  const form=element('form'),status=element('p');status.setAttribute('role','status');
  const fields={};
  for(const [id,label,type] of [['name','Employee name','text'],['email','Employee email','email'],['username','Username','text'],['password','Initial password (at least 12 characters)','password']]){
   const input=element('input');input.type=type;input.required=true;input.autocomplete=id==='password'?'new-password':'off';input.setAttribute('aria-label',label);
   const caption=element('label',label);caption.append(input);form.append(caption);fields[id]=input;
  }
  fields.password.minLength=12;fields.password.maxLength=128;fields.username.pattern='[A-Za-z0-9][A-Za-z0-9._-]{2,39}';
  const role=element('select');role.setAttribute('aria-label','Access level');for(const value of ['member','admin']){const opt=element('option',value==='admin'?'Admin':'Member');opt.value=value;role.append(opt);}
  const roleLabel=element('label','Access level');roleLabel.append(role);form.append(roleLabel);
  const save=element('button','Create account');save.type='submit';form.append(save);
  let requestId=null,details=null,busy=false;
  form.onsubmit=async event=>{event.preventDefault();if(busy||!form.reportValidity())return;
   const current=JSON.stringify([fields.name.value.trim(),fields.email.value.trim(),fields.username.value.trim(),role.value]);
   if(current!==details){requestId=crypto.randomUUID();details=current;}
   busy=true;save.disabled=true;status.textContent='Creating account…';
   try{const result=await api('/api/account/managed/accounts',{request_id:requestId,name:fields.name.value.trim(),email:fields.email.value.trim(),username:fields.username.value.trim(),password:fields.password.value,role:role.value});
    status.textContent=`Account ready: ${result.username} (${result.role}). No invitation is needed. Share the initial password privately; the employee will choose a new password on first sign-in.`;
    requestId=null;details=null;for(const input of Object.values(fields))input.value='';
   }catch(e){status.textContent=e.message;}finally{fields.password.value='';busy=false;save.disabled=false;}
  };
  const close=element('button','Close');close.type='button';close.onclick=()=>{if(!busy)dialog.close();};
  dialog.addEventListener('cancel',event=>{if(busy)event.preventDefault();});
  const sessionChanged=()=>dialog.close();document.addEventListener('wzos:session',sessionChanged);
  dialog.addEventListener('close',()=>{for(const input of Object.values(fields))input.value='';document.removeEventListener('wzos:session',sessionChanged);dialog.remove();},{once:true});
  dialog.append(element('h2','Create employee account'),element('p','Add a team member directly. Each active account uses one licensed login.'),form,status,close);document.body.append(dialog);dialog.showModal();
 }
 async function start(config){
  authHeader=config.auth_header||'Authorization';
  if(!['Authorization','X-WZOS-Authorization'].includes(authHeader))throw Error('Sign-in configuration is unavailable.');
  key=config.auth_api_key;
  if(config.auth_emulator){
   if(!['127.0.0.1','localhost'].includes(location.hostname)||config.auth_emulator!=='http://127.0.0.1:9099')throw Error('Local authentication configuration refused.');
   authBase=config.auth_emulator+'/identitytoolkit.googleapis.com';tokenBase=config.auth_emulator+'/securetoken.googleapis.com';
  }
  const passkeysAvailable=Boolean(config.passkeys&&window.isSecureContext&&window.PublicKeyCredential&&navigator.credentials);
  const panel=element('dialog');panel.className='account-dialog';
  const logo=element('img');logo.src='/wzos-logo.png?brand=20261017';logo.alt='Work Zone OS';logo.className='account-brand-logo';logo.width=80;logo.height=89;panel.append(logo);
  const title=element('h2','Welcome to WZOS');const note=element('p',key?'Sign in to your organization.':'Account sign-in is awaiting Google authentication configuration.');
  const email=element('input');email.type='text';email.autocomplete='username';email.required=true;
  const password=element('input');password.type='password';password.autocomplete='current-password';password.required=true;password.setAttribute('aria-label','Password');
  const form=element('form');const emailLabel=element('label','Email or username');emailLabel.append(email);const passwordLabel=element('label','Password');
  const passwordField=element('span');passwordField.className='password-field';
  const passwordVisibility=element('button');passwordVisibility.type='button';passwordVisibility.className='password-visibility-button';
  function passwordVisible(visible){
   password.type=visible?'text':'password';
   passwordVisibility.setAttribute('aria-label',visible?'Hide password':'Show password');
   passwordVisibility.setAttribute('aria-pressed',String(visible));
   passwordVisibility.title=visible?'Hide password':'Show password';
   passwordVisibility.innerHTML='<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>'+(visible?'':'<path d="m3 3 18 18"/>')+'</svg>';
  }
  passwordVisible(false);passwordVisibility.onclick=()=>passwordVisible(password.type==='password');
  passwordField.append(password,passwordVisibility);passwordLabel.append(passwordField);
  const remember=element('input');remember.type='checkbox';remember.checked=false;
  const rememberLabel=element('label','Stay signed in on this device for up to 14 days');rememberLabel.className='remember-choice';rememberLabel.append(remember);rememberLabel.hidden=!config.persistent_sessions;
  const privacy=element('p','Leave unchecked to sign in each time you reload or reopen WZOS. Use this on shared devices.');privacy.hidden=!config.persistent_sessions;
  const signin=element('button','Sign in');signin.type='submit';signin.disabled=!key;
  const signup=element('button','Create account');signup.type='button';signup.disabled=!key;
  const reset=element('button','Reset password');reset.type='button';reset.disabled=!key;
  const verify=element('button','Resend verification email');verify.type='button';verify.disabled=!key;
  const passkey=element('button','Sign in with a passkey');passkey.type='button';passkey.hidden=!passkeysAvailable;
  const message=element('p');message.setAttribute('role','status');
  form.append(emailLabel,passwordLabel,rememberLabel,privacy,signin,passkey,signup,reset,verify);panel.append(title,note,form,message);document.body.append(panel);panel.addEventListener('cancel',e=>e.preventDefault());panel.showModal();window.wzosStartup?.signingIn();
  const session=await new Promise(resolve=>{
   if(window.wzosInstall)window.wzosInstall.mount(panel);
   let working=false;
   async function run(task){if(working)return;working=true;for(const b of panel.querySelectorAll('button'))b.disabled=true;try{await task();}catch(e){message.textContent=e.message;}finally{working=false;for(const b of panel.querySelectorAll('button'))b.disabled=!key;}}
   async function choose(){
    const account=await api('/api/account');message.textContent='';password.value='';form.hidden=true;title.textContent='Your organization';note.textContent='Select your organization. Invitations are optional for accounts created by your administrator.';
    let choices=panel.querySelector('.account-choices');if(choices)choices.remove();choices=element('div');choices.className='account-choices';
    if(account.password_change_required){
     title.textContent='Choose your password';note.textContent='Replace the initial password your administrator provided before opening WZOS.';
     const next=element('input');next.type='password';next.autocomplete='new-password';next.minLength=12;next.maxLength=128;next.required=true;next.setAttribute('aria-label','New password');
     const again=element('input');again.type='password';again.autocomplete='new-password';again.required=true;again.setAttribute('aria-label','Confirm new password');
     const save=element('button','Save password');save.onclick=()=>run(async()=>{if(next.value!==again.value)throw Error('Passwords do not match.');if(next.value.length<12)throw Error('Use at least 12 characters.');try{await api('/api/account/managed/password',{password:next.value});token=null;refresh=null;expires=0;choices.remove();form.hidden=false;title.textContent='Sign in';note.textContent='Your password is updated. Sign in with your new password.';}finally{next.value='';again.value='';}});
     choices.append(next,again,save);panel.insertBefore(choices,message);return;
    }
    for(const org of account.organizations){const button=element('button',`${org.name}  -  ${org.role}  -  ${org.edition}`);button.onclick=()=>run(async()=>{organization=org.id;const current=await api('/api/session');panel.close();panel.remove();resolve(current);});choices.append(button);}
    const name=element('input');name.placeholder='Organization name';name.setAttribute('aria-label','Organization name');
    const activation=element('input');activation.placeholder='Activation code';activation.setAttribute('aria-label','Activation code');
    const create=element('button','Create organization');create.onclick=()=>run(async()=>{
     const orgName=name.value.trim(),code=activation.value.trim();
     if(orgName.length<2||orgName.length>120)throw Error('Enter an organization name between 2 and 120 characters.');
     if(!account.organization_creation_grant&&(code.length<32||code.length>128))throw Error('An activation code is required to create your organization. Ask WZOS support for your activation code.');
     await api('/api/account/organizations',{name:orgName,activation_code:code});await choose();});
    const invitation=element('input');invitation.placeholder='Invitation token';invitation.setAttribute('aria-label','Invitation token');
    const join=element('button','Join organization');join.onclick=()=>run(async()=>{
     const inviteToken=invitation.value.trim();if(inviteToken.length<32||inviteToken.length>128)throw Error('An invitation token is required to join. Ask your organization administrator for an invitation.');
     await api('/api/account/join',{token:inviteToken});await choose();});
    activation.hidden=Boolean(account.organization_creation_grant);
    const grant=account.organization_creation_grant;
    choices.append(element('p',grant?`Your ${grant.edition} organization with ${grant.seat_limit} active logins is approved. Enter its name to begin.`:'Create an organization with your activation code. If your admin has already added your account, select your organization above. Otherwise you may use an invitation.'),name,activation,create,invitation,join);panel.insertBefore(choices,message);
    // Purchase controls belong to new customers, never organization members.
    if(!account.organizations.length){
     const purchaseId=new URLSearchParams(location.search).get('purchase');
     if(purchaseId?.startsWith('cs_')&&purchaseId.length<512){
      const receiptBox=element('section');const receiptStatus=element('p','Checking your purchase…');
      const check=element('button','Check payment status');receiptBox.append(receiptStatus,check);choices.prepend(receiptBox);
      const checkReceipt=async()=>{
       const receipt=await api('/api/account/purchases/'+encodeURIComponent(purchaseId));
       if(receipt.status==='fulfilled'&&receipt.activation_code){
        activation.value=receipt.activation_code;
        receiptStatus.textContent=`Payment confirmed. ${receipt.edition==='enterprise'?'Enterprise':'Core'} includes ${receipt.seats} active logins. Enter your organization name to activate.`;
        check.hidden=true;history.replaceState(null,'',location.pathname+location.hash);
       }else receiptStatus.textContent='Payment confirmation is pending. Check again shortly; do not pay again.';
      };
      check.onclick=()=>run(checkReceipt);
      try{await checkReceipt();}catch(e){receiptStatus.textContent=e.message;}
     }
     try{
      const commerce=await api('/api/account/commerce');
      if(commerce.enabled){
       const purchase=element('details');purchase.append(element('summary','Purchase WZOS for a new organization'));
       for(const offer of commerce.offers){
        const card=element('section');const seats=element('input');seats.type='number';seats.required=true;seats.min=String(offer.included_seats);seats.max=String(offer.maximum_seats||100000);seats.step='1';seats.value=seats.min;seats.setAttribute('aria-label',offer.edition+' active logins');
        const total=element('p');const money=cents=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(cents/100);
        function price(){const count=Number(seats.value);const monthly=offer.monthly_cents+Math.max(0,count-offer.included_seats)*offer.additional_seat_monthly_cents;total.textContent=`${money(offer.setup_cents)} setup + ${money(monthly)}/month, plus applicable tax. ${offer.included_seats} logins included; each extra is ${money(offer.additional_seat_monthly_cents)}/month. Admins count as logins.`;}
        seats.oninput=price;price();
        const buy=element('button','Continue to secure checkout');let retryId=null,retrySeats=null;
        buy.onclick=()=>run(async()=>{
         if(!seats.reportValidity())return;const count=Number(seats.value);
         if(retrySeats!==count){retryId=crypto.randomUUID();retrySeats=count;}
         const result=await api('/api/account/checkout',{request_id:retryId,offer_id:offer.id,seats:count});
         if(!result.checkout_url)throw Error('This checkout is no longer open. Check your purchase status before trying again.');
         const destination=new URL(result.checkout_url);
         if(destination.protocol!=='https:'||!['checkout.stripe.com','checkout.superiorllc.org'].includes(destination.hostname))throw Error('Checkout destination was not accepted.');
         location.assign(destination.href);
        });
        card.append(element('h3',offer.edition==='enterprise'?'Enterprise':'Core'),total,seats,buy);purchase.append(card);
       }
       choices.append(purchase);
      }
     }catch(e){/* Existing activation and invitation flows remain available. */}
    }
   }
   async function login(create){
    if(!email.reportValidity()||!password.reportValidity())return;
    passwordVisible(false);
    if(config.persistent_sessions)await api('/api/account/logout',{});
    const identifier=email.value.trim();
    if(create&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(identifier))throw Error('Enter an email address to create a personal account. Your administrator can create a username account.');
    const data=!create&&!identifier.includes('@')?await api('/api/account/managed/sign-in',{username:identifier,password:password.value}):await provider(create?'signUp':'signInWithPassword',{email:identifier,password:password.value,returnSecureToken:true});
    token=data.idToken;refresh=data.refreshToken;expires=Date.now()+Number(data.expiresIn)*1000;
    if(create){try{await provider('sendOobCode',{requestType:'VERIFY_EMAIL',idToken:token});message.textContent='Check your email to verify your account, then sign in.';}
     catch(e){message.textContent='Your account was created, but the verification email could not be requested. Use Resend verification email or try again later.';}
     finally{token=null;refresh=null;expires=0;password.value='';}return;}
    if(remember.checked&&config.persistent_sessions){const account=await api('/api/account');if(!account.password_change_required){await api("/api/account/session",{});token=null;refresh=null;expires=0;}}
    await choose();
   }
   if(config.persistent_sessions){
    const reconnect=element('button','Retry saved sign-in');reconnect.type='button';reconnect.hidden=true;panel.append(reconnect);
    const restore=async()=>{reconnect.hidden=true;try{await choose();}catch(e){form.hidden=false;if(e.status===401){message.textContent='Sign in to continue.';}else{message.textContent='Your saved sign-in could not be checked. Retry the connection or sign in below.';reconnect.hidden=false;}}};
    reconnect.onclick=()=>run(restore);run(restore);
   }
   passkey.onclick=()=>run(async()=>{
    if(config.persistent_sessions)await api('/api/account/logout',{});
    const proof=await passkeyCeremony('login');
    const data=await provider('signInWithCustomToken',{token:proof.custom_token,returnSecureToken:true});
    token=data.idToken;refresh=data.refreshToken;expires=Date.now()+Number(data.expiresIn)*1000;
    if(remember.checked&&config.persistent_sessions){await api('/api/account/session',{});token=null;refresh=null;expires=0;}
    await choose();
   });
   form.onsubmit=e=>{e.preventDefault();run(()=>login(false));};signup.onclick=()=>run(()=>login(true));
   reset.onclick=()=>run(async()=>{if(!email.reportValidity())return;if(!email.value.includes('@'))throw Error('Enter your account email address to request a password reset.');await provider('sendOobCode',{requestType:'PASSWORD_RESET',email:email.value.trim()});message.textContent='If the account is eligible, a reset email will arrive.';});
   verify.onclick=()=>run(async()=>{
    if(!email.reportValidity()||!password.reportValidity())return;
    const data=await provider('signInWithPassword',{email:email.value.trim(),password:password.value,returnSecureToken:true});
    try{await provider('sendOobCode',{requestType:'VERIFY_EMAIL',idToken:data.idToken});message.textContent='Check your email to verify your account, then sign in.';}finally{password.value='';}
   });
  });
  const controls=document.querySelector('.preview-bar');
  controls.className='preview-bar account-bar';
  controls.setAttribute('aria-label','WZOS account');
  const menu=element('details');menu.className='account-menu';
  const menuToggle=element('summary','☰ Account');
  const actions=element('div');actions.className='account-actions';
  menu.append(menuToggle,actions);controls.append(menu);
  const phoneLayout=window.matchMedia?window.matchMedia('(max-width:760px)'):null;
  const resizeAccountMenu=()=>{menu.open=!phoneLayout?.matches;};
  resizeAccountMenu();phoneLayout?.addEventListener('change',resizeAccountMenu);
  const employeeButton=element('button',session.can_manage_team?'Employees':'My employee record');
  employeeButton.onclick=()=>window.wzosEmployees.open(api,session);employeeButton.className='account-glass account-employees';actions.append(employeeButton);
  if(session.can_manage_team){const importer=element('button','Import employees');importer.className='account-glass account-employee-import';importer.onclick=()=>window.wzosEmployees.importEmployees(api);actions.append(importer);}
  if(session.can_manage_team){const manage=element('button','Team access');manage.onclick=async()=>{
   const dialog=element('dialog');dialog.className='account-dialog';const status=element('p');status.setAttribute('role','status');const close=element('button','Close');close.onclick=()=>{dialog.close();dialog.remove();};dialog.append(element('h2','Organization access'),status,close);document.body.append(dialog);dialog.showModal();
   try{const data=await api('/api/account/members');
    const license=await api('/api/account/license');
    dialog.append(element('p',license.seat_limit===null?'Seat allowance awaiting configuration.':`${license.seats_used} of ${license.seat_limit} seats in use. Admins and members each use one seat.`));
    const provision=element('button','Create employee account');provision.onclick=()=>createManaged(api);dialog.append(provision,element('h3','Optional invitation'));
    const email=element('input');email.type='email';email.placeholder='Member email';email.setAttribute('aria-label','Member email');
    const role=element('select');role.setAttribute('aria-label','Invitation role');for(const value of (data.can_change_access?['member','admin']:['member'])){const option=element('option',value);option.value=value;role.append(option);}
    const invite=element('button','Create invitation');invite.onclick=async()=>{invite.disabled=true;try{const result=await api('/api/account/invitations',{email:email.value,role:role.value});const output=element('textarea');output.readOnly=true;output.value=result.token;output.setAttribute('aria-label','Private invitation token');dialog.append(output);status.textContent='Invitation created for this email. Share privately. No message was sent.';}catch(e){status.textContent=e.message;}finally{invite.disabled=false;}};dialog.append(email,role,invite);
    for(const member of data.items){const row=element('section');row.append(element('p',`${member.name}   -   ${member.role}   -   ${member.active?'Active':'Disabled'}`));if(data.can_change_access){const select=element('select');select.setAttribute('aria-label','Role for '+member.name);for(const value of ['member','admin']){const option=element('option',value);option.value=value;select.append(option);}select.value=member.role;const active=element('input');active.type='checkbox';active.checked=Boolean(member.active);const label=element('label','Active membership');label.append(active);const save=element('button','Save access');save.onclick=async()=>{save.disabled=true;try{await api('/api/account/members/'+encodeURIComponent(member.id),{role:select.value,active:active.checked},'PUT');status.textContent='Access updated. Changes apply on the next request.';if(member.id===session.id)location.reload();}catch(e){status.textContent=e.message;}finally{save.disabled=false;}};row.append(select,label,save);}dialog.append(row);}
   }catch(e){status.textContent=e.message;}
  };manage.className='account-glass account-team';actions.append(manage);}
  controls.querySelector('strong').textContent='WZOS ACCOUNT';controls.querySelector('span').textContent=session.organization;
  if(passkeysAvailable){
   const manageKeys=element('button','Passkeys');manageKeys.onclick=async()=>{
    const dialog=element('dialog');dialog.className='account-dialog';
    const status=element('p');status.setAttribute('role','status');
    const close=element('button','Close');close.onclick=()=>{dialog.close();dialog.remove();};
    const add=element('button','Add a passkey');
    dialog.append(element('h2','Your passkeys'),element('p','Use your device fingerprint, face, screen lock or security key. Sign in again first if requested. Your password remains available.'),status,add,close);
    document.body.append(dialog);dialog.showModal();
    add.onclick=async()=>{add.disabled=true;try{await passkeyCeremony('register');status.textContent='Passkey added. Close and reopen this panel to view it.';}catch(e){status.textContent=e.message;}finally{add.disabled=false;}};
    try{const data=await api('/api/account/passkeys');for(const item of data.items){
     const row=element('section');row.append(element('p',item.label));const remove=element('button','Remove passkey');
     remove.onclick=async()=>{remove.disabled=true;try{await api('/api/account/passkeys/'+encodeURIComponent(item.id),null,'DELETE');token=null;refresh=null;expires=0;location.reload();}catch(e){status.textContent=e.message;remove.disabled=false;}};row.append(remove);dialog.append(row);
    }}catch(e){status.textContent=e.message;}
   };manageKeys.className='account-glass account-passkeys';actions.append(manageKeys);
  }
  const logout=element('button','Sign out');logout.onclick=async()=>{logout.disabled=true;try{if(config.persistent_sessions)await api('/api/account/logout',{});token=null;refresh=null;expires=0;location.reload();}catch(e){logout.textContent='Sign out failed — retry';logout.disabled=false;}};logout.className='account-glass account-signout';actions.append(logout);
  if(config.persistent_sessions){const all=element('button','Forget remembered devices');all.onclick=async()=>{all.disabled=true;try{await api('/api/account/logout-all',{});token=null;refresh=null;expires=0;location.reload();}catch(e){all.textContent='Could not forget devices — retry';all.disabled=false;}};all.className='account-glass account-devices';actions.append(all);}
  return session;
 }
 return {headers,start};
})();
