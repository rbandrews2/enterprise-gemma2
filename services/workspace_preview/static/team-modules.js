"use strict";
(() => {
 const $=id=>document.getElementById(id),api=(...a)=>window.wzosClock.api(...a),node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
 let generation=0, view=null, dirty=false, sending=false;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>previous()&&!sending&&(!dirty||confirm('Leave the unsaved message?'));
 async function show(name){
  generation++;view=name;dirty=false;const epoch=generation,root=$('team-content');root.replaceChildren();$('team-notice').textContent='';
  if(!['training','messages','navigation'].includes(name))return;
  $('team-title').textContent={training:'Training study planner',messages:'Messaging',navigation:'Navigation'}[name];
  try{
   if(name==='navigation'){
    root.append(node('p','Loaded destinations remain available in this open app when offline. Save a destination sheet before travel for access after closing the app. Map imagery, live traffic and route guidance require connectivity or separately downloaded maps in your navigation app.'));
    let orders=window.wzosClock.getOrders(),cached=!navigator.onLine;
    if(navigator.onLine){try{orders=(await api('/api/orders')).items;}catch(error){if(error.status)throw error;cached=true;}}
    if(epoch!==generation)return;
    if(cached)root.append(node('p','Offline / connection unavailable — showing previously loaded destinations. Confirm addresses and site access before travel.'));
    if(!orders.length)root.append(node('p','No destinations loaded. Connect and open your jobs before going offline.'));
    for(const order of orders){const card=node('section','');card.className='report-section panel';card.append(node('h2',order.title),node('p',order.address));const a=node('a','Open destination in Google Maps');a.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(order.address);a.target='_blank';a.rel='noopener noreferrer';card.append(a);
     const save=node('button','Save destination sheet');save.className='secondary';save.onclick=()=>{const content=['WZOS destination sheet',order.title,order.address,'Saved on device: '+new Date().toISOString(),'Address reference only. No route, map, traffic or safe-access verification.'].join('\n');const url=URL.createObjectURL(new Blob([content],{type:'text/plain;charset=utf-8'}));const link=node('a','');link.href=url;link.download='wzos-destination.txt';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};card.append(save);root.append(card);}return;
   }
   if(name==='training'){
    root.append(node('p','Recovered V1 course catalog. Course content and accreditation are awaiting review. These are personal study plans, not completion records or certificates.'));
    const data=await api('/api/training');if(epoch!==generation)return;
    for(const course of data.items){const card=node('section','');card.className='report-section panel';card.append(node('h2',course.title),node('p',course.description));const label=node('label','Study status'),select=node('select','');for(const [value,title] of Object.entries({not_started:'Not started',studying:'Studying',review_requested:'Ready for review (not sent)'})){const option=node('option',title);option.value=value;select.append(option);}select.value=course.study_status;const save=node('button','Save study status');save.className='secondary';save.onclick=async()=>{save.disabled=true;try{await api('/api/training/'+course.id,{method:'PUT',body:JSON.stringify({status:select.value})});if(epoch===generation)$('team-notice').textContent='Study status saved. No certificate or notification issued.';}catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}finally{save.disabled=false;}};label.append(select);card.append(label,save);root.append(card);}return;
   }
   await messagesView(root,epoch);
  }catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}
 }
 // Provider acceptance, carrier delivery and the recipient's acknowledgement are shown separately.
 const SMS_STATUS={queued:'Queued',sending:'Sending to provider',accepted:'Accepted by provider',sent:'Sent to carrier',delivered:'Delivered to phone',undelivered:'Not delivered',failed:'Failed',ambiguous:'Unknown — needs admin review',blocked:'Not sent',cancelled:'Cancelled'};
 const CONTACT_STATUS={none:'Not enabled',pending_verification:'Waiting for verification code',verified:'Verified — text messages on',opted_out:'Opted out'};
 const checkbox=()=>{const box=node('input','');box.type='checkbox';Object.assign(box.style,{width:'auto',display:'inline-block',margin:'0 .5rem 0 0',verticalAlign:'middle'});return box;};
 const button=(text,cls='secondary')=>{const b=node('button',text);b.type='button';b.className=cls;return b;};
 const smsLine=sms=>'Text message: '+(SMS_STATUS[sms.status]||sms.status)+(sms.phone?' · '+sms.phone:'')+(sms.reason_text?' — '+sms.reason_text:'')+(sms.error_code?' (provider code '+sms.error_code+')':'');
 async function guarded(epoch,control,work,done){control.disabled=true;try{await work();if(epoch===generation){await show('messages');if(done)$('team-notice').textContent=done;}}catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}finally{control.disabled=false;}}
 async function messagesView(root,epoch){
  const admin=window.wzosClock.getSession()?.role==='admin';
  const [roster,messages,contact,people,readiness,outbox]=await Promise.all([api('/api/modules/roster'),api('/api/messages'),api('/api/messaging/sms/contact'),
   admin?api('/api/messaging/sms/contacts'):null,admin?api('/api/messaging/sms/readiness'):null,admin?api('/api/messaging/sms/outbox'):null]);
  if(epoch!==generation)return;
  const names=Object.fromEntries(roster.items.map(m=>[m.id,m.name])),smsBy=Object.fromEntries((people?.items||[]).map(p=>[p.id,p.status]));
  root.append(node('p',messages.synthetic_only?'Synthetic test inbox. Text messages go only to approved test numbers when test sending is configured. Shows up to 50 recent messages.':'Organization messages. Shows up to 50 recent messages.'));
  // Compose
  const form=node('form',''),label=node('label','Recipient'),recipient=node('select',''),bodyLabel=node('label','Message'),body=node('textarea',''),submit=node('button','Send message');submit.className='primary';body.required=true;body.maxLength=2000;let retry=null;
  for(const member of roster.items){const option=node('option',member.name+' · '+member.role);option.value=member.id;recipient.append(option);}label.append(recipient);bodyLabel.append(body);
  const ackLabel=node('label',''),ack=checkbox();ackLabel.append(ack,' Ask the recipient to acknowledge');
  const smsLabel=node('label',''),smsBox=checkbox(),smsHint=node('p','');smsLabel.append(smsBox,' Also send a text message copy');smsHint.className='muted';smsLabel.hidden=smsHint.hidden=!admin;
  const hint=()=>{const status=smsBy[recipient.value]||'none';smsHint.textContent=readiness&&!readiness.ready?'Text sending is not available: '+(readiness.mode==='disabled'?'turned off for this environment.':'settings incomplete.'):'Recipient text messages: '+(CONTACT_STATUS[status]||status)+'.';};hint();
  form.append(label,bodyLabel,ackLabel,smsLabel,smsHint,submit);form.oninput=()=>{dirty=true;retry=null;hint();};
  form.onsubmit=async event=>{event.preventDefault();if(sending)return;retry=retry||{request_id:crypto.randomUUID(),recipient_id:recipient.value,text:body.value,request_acknowledgement:ack.checked,sms_copy:admin&&smsBox.checked};sending=true;submit.disabled=body.disabled=recipient.disabled=true;
   try{const saved=await api('/api/messages',{method:'POST',body:JSON.stringify(retry)});if(epoch===generation){dirty=false;await show('messages');$('team-notice').textContent='Message saved in WZOS.'+(saved.sms?(saved.sms.status==='queued'?' Text message copy queued — its delivery status is shown on the message.':' '+smsLine(saved.sms)+'.'):'');}}
   catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}finally{sending=false;submit.disabled=body.disabled=recipient.disabled=false;}};root.append(form);
  // Inbox and sent items
  const me=window.wzosClock.getSession()?.id;
  for(const message of messages.items){const card=node('article','');card.className='report-section panel';
   card.append(node('p',`${names[message.sender_id]||message.sender_id} → ${names[message.recipient_id]||message.recipient_id} · ${new Date(message.created_at).toLocaleString()}`),node('p',message.body));
   if(message.sms)card.append(node('p',smsLine(message.sms)));
   if(message.acknowledgement_requested)card.append(node('p',message.acknowledged_at?'Acknowledged '+new Date(message.acknowledged_at).toLocaleString():'Acknowledgement requested — not yet acknowledged'));
   if(message.acknowledgement_requested&&!message.acknowledged_at&&message.recipient_id===me){const b=button('Acknowledge','primary');b.onclick=()=>guarded(epoch,b,()=>api('/api/messages/'+message.id+'/acknowledge',{method:'POST'}),'Acknowledged.');card.append(b);}
   root.append(card);}
  // The member's own text message settings; only the phone's owner can turn texts on.
  const mine=node('details',''),mineBody=node('form','');mineBody.onsubmit=event=>event.preventDefault();mine.className='report-section panel';mine.open=contact.status==='pending_verification';mine.append(node('summary','My text message settings'),mineBody);
  mineBody.append(node('p','Status: '+(CONTACT_STATUS[contact.status]||contact.status)+(contact.phone?' · '+contact.phone:'')));
  if(!contact.sms_ready)mineBody.append(node('p','Text sending is not available in this environment yet. You can still record your number and consent.'));
  const phoneLabel=node('label','Mobile number (international format, e.g. +15551234567)'),phone=node('input','');phone.type='tel';phone.autocomplete='tel';phone.value=contact.phone||'';phone.pattern='^\\+[1-9][0-9]{7,14}$';phoneLabel.append(phone);
  const consentLabel=node('label',''),consent=checkbox();consentLabel.append(consent,' '+contact.consent_text);
  const request=button(contact.status==='verified'?'Change number':'Send verification code');
  request.onclick=()=>{if(!consent.checked){$('team-notice').textContent='Review and accept the text message consent first.';return;}if(!phone.checkValidity()||!phone.value){$('team-notice').textContent='Enter the number in international format, starting with +.';return;}
   guarded(epoch,request,()=>api('/api/messaging/sms/contact',{method:'PUT',body:JSON.stringify({request_id:crypto.randomUUID(),expected_version:contact.version,phone:phone.value.trim(),consent:true,consent_version:contact.current_consent_version})}),'Verification requested. Enter the code sent to your phone.');};
  mineBody.append(phoneLabel,consentLabel,request);
  if(contact.status==='pending_verification'){const codeLabel=node('label','Verification code'),code=node('input','');code.inputMode='numeric';code.autocomplete='one-time-code';code.maxLength=6;codeLabel.append(code);const verify=button('Verify number','primary');
   verify.onclick=()=>{if(!/^[0-9]{6}$/.test(code.value.trim())){$('team-notice').textContent='Enter the 6-digit code from the text message.';return;}guarded(epoch,verify,()=>api('/api/messaging/sms/contact/verify',{method:'POST',body:JSON.stringify({code:code.value.trim()})}),'Number verified. Text messages are on.');};mineBody.append(codeLabel,verify);}
  if(['verified','pending_verification'].includes(contact.status)){const stop=button('Turn off text messages');stop.onclick=()=>guarded(epoch,stop,()=>api('/api/messaging/sms/contact/opt-out',{method:'POST',body:JSON.stringify({expected_version:contact.version})}),'Text messages turned off.');mineBody.append(stop);}
  mineBody.append(node('p','You can also reply STOP to any WZOS text. WZOS messages remain available in the app.'));
  root.append(mine);
  if(!admin)return;
  // Admin delivery oversight for this organization only.
  const panel=node('details',''),inner=node('section','');panel.className='report-section panel';panel.append(node('summary','Text message delivery (admin)'),inner);
  inner.append(node('p','Sending mode: '+readiness.mode+(readiness.ready?' · ready':' · not ready')+(readiness.mode==='test'?' · approved test numbers: '+readiness.test_recipient_count:'')));
  if(readiness.missing.length)inner.append(node('p','Missing settings: '+readiness.missing.join(', ')));
  const team=node('ul','');for(const p of people.items)team.append(node('li',`${p.name}: ${CONTACT_STATUS[p.status]||p.status}${p.phone?' · '+p.phone:''}`));inner.append(node('h3','Team text message status'),team);
  const run=button('Send queued texts now');run.onclick=()=>guarded(epoch,run,()=>api('/api/messaging/sms/process',{method:'POST'}),'Queue processed.');inner.append(node('h3','Recent texts'),run);
  if(!outbox.items.length)inner.append(node('p','No text messages yet.'));
  for(const row of outbox.items){const item=node('article','');item.className='clock-entry';
   item.append(node('p',`${names[row.recipient_id]||row.recipient_id} · ${row.purpose==='verification'?'Verification code':'Message copy'} · ${new Date(row.created_at).toLocaleString()} · attempts ${row.attempts}`),node('p',smsLine(row)));
   const actions=node('div','');actions.className='clock-actions';
   const act=(text,action,confirmText)=>{const b=button(text);b.onclick=()=>{if(confirmText&&!confirm(confirmText))return;guarded(epoch,b,()=>api('/api/messaging/sms/outbox/'+row.id+'/resolve',{method:'POST',body:JSON.stringify({action,confirm_possible_duplicate:action==='retry'&&row.status==='ambiguous'})}),'Text message updated.');};actions.append(b);};
   if(row.status==='ambiguous'){if(row.purpose!=='verification')act('Resend (may duplicate)','retry','The provider may already have sent this text. Resend anyway?');act('Mark failed','mark_failed');}
   if(row.status==='blocked'){if(row.purpose!=='verification')act('Try again','retry');act('Cancel','cancel');}
   if(row.status==='queued')act('Cancel','cancel');
   if(actions.childElementCount)item.append(actions);inner.append(item);}
  root.append(panel);
 }
 for(const name of ['training','messages','navigation'])$(name+'-nav').onclick=()=>window.showWzosView(name);
 document.addEventListener('wzos:view',event=>show(event.detail));
 document.addEventListener('wzos:session',()=>show(view));
 for(const event of ['online','offline'])window.addEventListener(event,()=>{if(view==='navigation')show(view);});
 window.addEventListener('beforeunload',event=>{if(dirty||sending){event.preventDefault();event.returnValue='';}});
})();
