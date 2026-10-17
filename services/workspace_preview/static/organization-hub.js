/* Organization data and credentials stay in memory and are cleared on view/session changes. */
'use strict';
(()=>{
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const nav=node('button','◈ Dashboard','nav-item');nav.id='dashboard-nav';nav.hidden=true;
 document.querySelector('nav[aria-label="Workspace navigation"]').prepend(nav);
 const root=node('section',undefined,'report-section guided-dashboard');root.id='dashboard-view';root.hidden=true;document.getElementById('main').prepend(root);
 let epoch=0,draft=false,active=false,upgradeDialog=null;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>{if(draft&&!confirm('Discard your unsaved dashboard note?'))return false;return !previous||previous();};
 const api=(...args)=>window.wzosClock.api(...args);
 const button=(label,action)=>{const b=node('button',label,'secondary');b.type='button';b.onclick=action;return b;};
 function clear(){epoch++;root.replaceChildren();draft=false;}
 async function render(){
  const retainedDraft=root.querySelector('textarea')?.value||'';
  clear();const generation=epoch;const state=window.wzosClock.getSession();if(state?.role!=='admin')return;
  const logo=node('img');logo.src='/wzos-logo.png?brand=20261017';logo.alt='Work Zone OS';logo.className='dashboard-brand-logo';logo.width=64;logo.height=71;root.append(logo);
  const heading=node('h1','Organization dashboard','organization-heading');root.append(heading);const status=node('p');status.hidden=true;status.setAttribute('role','status');root.append(status);
  const reportError=message=>{status.hidden=false;status.className='hub-error';status.textContent=message;};
  try{
   const data=await api('/api/admin/dashboard');if(generation!==epoch)return;
   root.querySelector('h1').textContent=data.organization;
   const layout=node('div',undefined,'guided-layout'),story=node('section',undefined,'panel guided-story'),content=node('section',undefined,'guided-content');
   story.append(node('p','Built for the work ahead','guided-kicker'),node('h2','Your operation. In clear view.'),node('p','From the first assignment to the final report, keep every crew connected to the work that matters.'));
   const atlas=node('img');atlas.src='/atlas-assistant.png';atlas.alt='Atlas, your WZOS AI assistant';atlas.width=220;atlas.height=220;
   story.append(atlas,button('Ask Atlas',()=>document.getElementById('assistant-open')?.click()));
   content.append(node('h2','Where would you like to begin?'));layout.append(story,content);root.append(layout);
   const grid=node('div',undefined,'hub-grid');for(const item of data.modules.filter(m=>m.visible)){
    const b=button('',()=>document.getElementById(item.nav_id)?.click());b.className=item.id==='report'?'panel hub-card guided-feature':'panel hub-card';b.append(node('span',item.icon,'hub-icon'),node('strong',item.label));if(item.id==='report')content.append(b);else grid.append(b);
   }
   for(const [label,selector,icon] of [['Employees','.account-employees','♙'],['Team access','.account-team','♧'],['Passkeys','.account-passkeys','⚿']]){
    if(document.querySelector(selector)){const b=button('',()=>document.querySelector(selector)?.click());b.className='panel hub-card';b.append(node('span',icon,'hub-icon'),node('strong',label));grid.append(b);}
   }content.append(grid);
   content.append(node('p','WZOS powered by Atlas AI Assistant','guided-footer'));
   if(window.wzosSecurity){const security=button('Atlas Security',()=>window.wzosSecurity.open());security.className='panel hub-card';content.append(security);}
   const options=node('details',undefined,'panel');options.append(node('summary','Dashboard preferences'));const selections=[];
   for(const item of data.modules){const label=node('label'),check=node('input');check.type='checkbox';check.checked=item.visible;label.append(check,document.createTextNode(item.label));options.append(label);selections.push([item.id,check]);}
   options.append(node('small','Shared dashboard shortcuts only. Hiding a card does not change access permissions.'));
   options.append(button('Save preferences',async()=>{try{await api('/api/admin/dashboard/preferences',{method:'PUT',body:JSON.stringify({expected_version:data.preferences_version,hidden_modules:selections.filter(([,c])=>!c.checked).map(([id])=>id)})});if(generation===epoch)render();}catch(e){if(generation===epoch)reportError(e.message);}}));root.append(options);
   const notes=node('section',undefined,'panel');notes.append(node('h2','Admin notes'));const form=node('form'),input=node('textarea');input.maxLength=500;input.required=true;input.rows=3;input.setAttribute('aria-label','Short message for organization admins');input.placeholder='Leave a short message for your fellow admins';input.oninput=()=>{draft=!!input.value;};
   input.value=retainedDraft;draft=!!retainedDraft;
   const save=node('button','Post note','primary');save.type='submit';form.append(input,save);let requestId=crypto.randomUUID(),last='';
   form.onsubmit=async e=>{e.preventDefault();if(last&&last!==input.value)requestId=crypto.randomUUID();last=input.value;save.disabled=true;try{await api('/api/admin/dashboard/notes',{method:'POST',body:JSON.stringify({request_id:requestId,text:input.value})});if(generation===epoch){input.value='';draft=false;render();}}catch(err){if(generation===epoch){reportError(err.message);save.disabled=false;}}};notes.append(form);
   for(const item of data.notes){const card=node('article',undefined,'hub-note');card.append(node('p',item.body),node('small',item.author_name+' · '+new Date(item.created_at).toLocaleString()),button('Remove',async()=>{if(!confirm('Remove this admin note?'))return;try{await api('/api/admin/dashboard/notes/'+encodeURIComponent(item.id),{method:'DELETE'});if(generation===epoch)render();}catch(e){if(generation===epoch)reportError(e.message);}}));notes.append(card);}if(!data.notes.length)notes.append(node('p','No admin notes yet.'));root.append(notes);
   const integrations=node('details',undefined,'panel');integrations.append(node('summary','Integration API'));const tools=node('div');integrations.append(tools);root.append(integrations);
   integrations.addEventListener('toggle',()=>{if(integrations.open&&!tools.childNodes.length)credentials(tools,generation);});
  }catch(e){if(generation===epoch)reportError('Could not load your dashboard. '+e.message);}
 }
 async function credentials(root,generation){
  root.replaceChildren();root.append(node('p','Read-only work-order and schedule connections. QuickBooks and Workday connectors are not yet configured.'));
  const status=node('p');status.setAttribute('role','status');root.append(status);
  try{const data=await api('/api/admin/integrations');if(generation!==epoch)return;
   const name=node('input');name.maxLength=80;name.placeholder='Connection name';name.setAttribute('aria-label','Connection name');const form=node('form'),scopeInputs=[];form.append(name);
   for(const scope of data.supported_scopes){const label=node('label'),check=node('input');check.type='checkbox';check.checked=scope==='orders:read';label.append(check,document.createTextNode(scope));form.append(label);scopeInputs.push([scope,check]);}
   const create=node('button','Create 30-day API credential','primary');create.type='submit';form.append(create);root.append(form);
   form.onsubmit=async e=>{e.preventDefault();create.disabled=true;try{const result=await api('/api/admin/integrations',{method:'POST',body:JSON.stringify({name:name.value,scopes:scopeInputs.filter(([,c])=>c.checked).map(([s])=>s),expires_in_days:30})});if(generation!==epoch)return;status.textContent=result.warning;const secret=node('input');secret.readOnly=true;secret.type='password';secret.value=result.token;secret.autocomplete='off';secret.setAttribute('aria-label','New API credential shown once');root.append(secret,button('Show / hide credential',()=>{secret.type=secret.type==='password'?'text':'password';}),button('Clear credential and refresh',()=>credentials(root,generation)));form.remove();}catch(err){if(generation===epoch){status.textContent=err.message;create.disabled=false;}}};
   for(const item of data.items){const line=node('p',`${item.name} · ${item.revoked_at?'Revoked':'Expires '+new Date(item.expires_at).toLocaleDateString()} · ${item.scopes.join(', ')}`);if(!item.revoked_at)line.append(button('Revoke',async()=>{if(!confirm('Revoke this connection immediately?'))return;try{await api('/api/admin/integrations/'+encodeURIComponent(item.id),{method:'DELETE'});if(generation===epoch)credentials(root,generation);}catch(e){if(generation===epoch)status.textContent=e.message;}}));root.append(line);}
  }catch(e){if(generation===epoch)status.textContent=e.message;}
 }
 nav.onclick=()=>window.showWzosView('dashboard');
 const upgrade=button('✦ Explore Enterprise',()=>{
  const session=window.wzosClock.getSession();if(session?.edition!=='core'||session.role!=='admin'||upgradeDialog?.open)return;
  const dialog=node('dialog',undefined,'panel upgrade-dialog');dialog.setAttribute('aria-label','Explore WZOS Enterprise');
  dialog.append(node('h2','Bring your operation together with Enterprise'),node('p','Add Work Zone Reports, employee job assignments and reviewed automated dispatch to your Core workspace.'));
  dialog.append(node('p','Enterprise: $999 setup and $249 per month, including 25 active logins. Additional active logins: $7 per month each.'),node('p','Established Core customers receive a one-time $20 upgrade credit. Online upgrade checkout is not yet available; no payment or edition change is made here.'));
  const close=button('Continue with Core',()=>{dialog.close();upgrade.focus?.();});dialog.append(close);dialog.addEventListener('close',()=>{dialog.remove();if(upgradeDialog===dialog)upgradeDialog=null;},{once:true});document.body.append(dialog);upgradeDialog=dialog;dialog.showModal();
 });upgrade.hidden=true;upgrade.className='nav-item core-upgrade';upgrade.id='core-upgrade';document.querySelector('nav[aria-label="Workspace navigation"]').append(upgrade);
 document.addEventListener('wzos:session',()=>{const session=window.wzosClock.getSession();upgrade.hidden=session?.edition!=='core'||session.role!=='admin';if(upgradeDialog){upgradeDialog.close();upgradeDialog.remove();upgradeDialog=null;}});
 document.addEventListener('wzos:view',e=>{active=e.detail==='dashboard';if(active)render();else{root.hidden=true;clear();}});
 document.addEventListener('wzos:session',()=>{const admin=window.wzosClock.getSession()?.role==='admin';nav.hidden=!admin;clear();if(admin)window.showWzosView('dashboard');else if(active)window.showWzosView('orders');});
 window.addEventListener('beforeunload',e=>{if(draft){e.preventDefault();e.returnValue='';}});
})();
