/* Atlas Security: server facts and explicit admin actions. No model-issued commands. */
'use strict';
(()=>{
 const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const api=(...args)=>window.wzosClock.api(...args);
 const isAdmin=()=>window.wzosClock.getSession()?.role==='admin';
 const banner=node('aside');banner.className='atlas-security-alert';banner.hidden=true;
 banner.setAttribute('aria-label','Organization security notifications');
 document.getElementById('main').prepend(banner);
 const dialog=node('dialog');dialog.className='account-dialog security-dialog';document.body.append(dialog);
 let epoch=0,busy=false;
 const button=(text,click)=>{const b=node('button',text);b.type='button';b.className='secondary';b.onclick=click;return b;};
 const reset=()=>{epoch++;busy=false;banner.replaceChildren();banner.hidden=true;if(dialog.open)dialog.close();dialog.replaceChildren();};
 async function refresh(){
  const generation=epoch;if(!isAdmin()||document.hidden)return;
  try{const data=await api('/api/admin/security/summary');if(generation!==epoch||!isAdmin())return;
   banner.replaceChildren();banner.hidden=!data.open_incidents;
   if(data.open_incidents){const message=node('strong',`Atlas Security: ${data.open_incidents} unresolved incident${data.open_incidents===1?'':'s'}`);message.setAttribute('role','status');banner.append(message,button('Review alerts',open));}
  }catch(e){if(generation===epoch&&isAdmin()){banner.hidden=false;banner.replaceChildren(node('span','Security status unavailable.'),button('Retry',refresh));}}
 }
 async function render(offset=0){
  const generation=++epoch;if(!isAdmin())return;
  dialog.replaceChildren(button('Close',()=>dialog.close()),node('h2','Atlas Security'));
  const notice=node('p','Loading security incidents…');notice.setAttribute('role','status');dialog.append(notice);
  try{const data=await api('/api/admin/security?offset='+offset);if(generation!==epoch||!isAdmin())return;
   notice.textContent=data.open_incidents?`${data.open_incidents} incident(s) require review.`:'No unresolved application incidents recorded. This is not an all-clear security assessment.';
   dialog.append(node('p',data.file_scan_required?'Unscanned files are held until a clean scan.':'Scan enforcement is not activated. Existing unscanned files are not protected by malware scanning.'),node('small',data.coverage));
   const protocol=node('details');protocol.append(node('summary','Response protocol'),node('p','Notify admins → acknowledge → contain with a reason → investigate → verify recovery → resolve. Keep evidence. Atlas cannot suspend users or release files through conversation.'));dialog.append(protocol);
   for(const item of data.items){
    const card=node('article');card.className='security-incident';card.append(node('h3',item.title),node('p',`${item.severity.toUpperCase()} · ${item.status} · ${item.target_type}: ${item.target_id}`));
    if(item.file_security)card.append(node('p',`File: ${item.file_security.status}${item.file_security.quarantined?' · quarantined':''}`));
    const audit=node('details');audit.append(node('summary','Evidence and actions'));for(const event of item.actions)audit.append(node('p',`${event.action} · ${new Date(event.occurred_at).toLocaleString()} — ${event.reason}`));card.append(audit);
    const form=node('form'),reason=node('textarea');reason.required=true;reason.minLength=8;reason.maxLength=500;reason.rows=2;reason.placeholder='Record your review and reason';reason.setAttribute('aria-label','Reason for security action');
    const select=node('select');select.setAttribute('aria-label','Security action');const choices=[['acknowledge','Acknowledge'],['resolve','Resolve after recovery']];
    if(item.target_type==='file')choices.push(['quarantine_file','Quarantine file'],['rescan_file','Rescan preserved file'],['release_file','Release after clean scan']);
    if(item.target_type==='user')choices.push(['suspend_user','Suspend organization access'],['restore_user','Restore reviewed access']);
    if(item.target_type==='credential')choices.push(['revoke_credential','Revoke integration credential']);
    for(const [value,label]of choices){const option=node('option',label);option.value=value;select.append(option);}
    const submit=node('button','Apply reviewed action');submit.type='submit';submit.className='primary';form.append(reason,select,submit);
    form.onsubmit=async e=>{e.preventDefault();if(busy)return;if(!confirm('Apply this security action to this organization?'))return;busy=true;submit.disabled=true;
     try{await api('/api/admin/security/incidents/'+encodeURIComponent(item.id)+'/actions',{method:'POST',body:JSON.stringify({expected_version:item.version,action:select.value,reason:reason.value})});if(generation===epoch){await render(offset);await refresh();}}
     catch(err){if(generation===epoch){notice.textContent=err.message;submit.disabled=false;}}finally{busy=false;}
    };card.append(form);dialog.append(card);
   }
   const pager=node('div');if(offset)pager.append(button('Previous',()=>render(Math.max(0,offset-25))));if(data.items.length===25)pager.append(button('Next',()=>render(offset+25)));dialog.append(pager);
   const report=node('details');report.append(node('summary','Report a security concern'));const form=node('form'),kind=node('select');kind.setAttribute('aria-label','Concern target type');
   for(const value of ['activity','file','user','credential']){const option=node('option',value);option.value=value;kind.append(option);}
   const target=node('input');target.required=true;target.maxLength=128;target.placeholder='Affected record or user ID';target.setAttribute('aria-label','Affected record or user ID');
   const reason=node('textarea');reason.required=true;reason.minLength=8;reason.maxLength=500;reason.placeholder='Describe the observed evidence, without credentials';reason.setAttribute('aria-label','Observed security concern');const submit=node('button','Notify organization admins');submit.type='submit';submit.className='primary';form.append(kind,target,reason,submit);
   let requestId=crypto.randomUUID();form.onsubmit=async e=>{e.preventDefault();if(busy)return;busy=true;submit.disabled=true;try{await api('/api/admin/security/reports',{method:'POST',body:JSON.stringify({request_id:requestId,target_type:kind.value,target_id:target.value,reason:reason.value})});if(generation===epoch){await render();await refresh();}}catch(err){if(generation===epoch){notice.textContent=err.message;submit.disabled=false;requestId=crypto.randomUUID();}}finally{busy=false;}};report.append(form);dialog.append(report);
  }catch(err){if(generation===epoch)notice.textContent=err.message;}
 }
 function open(){if(!isAdmin())return;if(!dialog.open)dialog.showModal();render();}
 window.wzosSecurity={open};
 document.addEventListener('wzos:session',()=>{reset();refresh();});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
 setInterval(refresh,60000);
})();
