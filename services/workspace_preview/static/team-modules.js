"use strict";
(() => {
 const $=id=>document.getElementById(id),api=(...a)=>window.wzosClock.api(...a),node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
 let generation=0, view=null, dirty=false, sending=false, destinationCache=null;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>previous()&&!sending&&(!dirty||confirm('Leave the unsaved message?'));
 async function show(name){
  generation++;view=name;dirty=false;const epoch=generation,root=$('team-content');root.replaceChildren();$('team-notice').textContent='';
  if(!['training','messages','navigation'].includes(name))return;
  $('team-title').textContent={training:'Video training',messages:'Text notifications',navigation:'Navigation'}[name];
  try{
   if(name==='navigation'){
    window.WzosNavigationRoute?.overview?.(root);
    window.WzosNavigationRoute?.planner?.(root);
    const session=window.wzosClock.getSession(),scope=session?JSON.stringify([session.organization_id,session.id,session.edition]):null;
    let orders=destinationCache?.scope===scope?destinationCache.items:window.wzosClock.getOrders(),cached=!navigator.onLine,assignmentsUnavailable=false;
    if(navigator.onLine){try{
     orders=(await api('/api/orders')).items;
     if(session?.edition==='enterprise'){
      const assigned=new Map();let offset=0;
      while(true){let page;try{page=await api(`/api/dispatch/my-assignments?phase=upcoming&offset=${offset}`);}catch(error){if(error.status!==404)throw error;assignmentsUnavailable=true;break;}
       if(epoch!==generation||JSON.stringify([window.wzosClock.getSession()?.organization_id,window.wzosClock.getSession()?.id,window.wzosClock.getSession()?.edition])!==scope)return;
       for(const job of page.items)if(!assigned.has(job.id))assigned.set(job.id,{id:job.order_id,assignment_id:job.id,title:job.order_title,address:job.address,assigned:true});
       offset+=page.items.length;if(offset>=page.total||!page.items.length)break;
      }
      orders=[...assigned.values(),...orders.filter(order=>![...assigned.values()].some(job=>job.id===order.id))];
     }
     if(epoch!==generation||JSON.stringify([window.wzosClock.getSession()?.organization_id,window.wzosClock.getSession()?.id,window.wzosClock.getSession()?.edition])!==scope)return;
     destinationCache={scope,items:orders};
    }catch(error){if(error.status)throw error;cached=true;orders=destinationCache?.scope===scope?destinationCache.items:window.wzosClock.getOrders();}}
    if(epoch!==generation||JSON.stringify([window.wzosClock.getSession()?.organization_id,window.wzosClock.getSession()?.id,window.wzosClock.getSession()?.edition])!==scope)return;
    if(assignmentsUnavailable)root.append(node('p','Assigned destinations are unavailable in this environment. Showing permitted work orders only.'));
    if(cached)root.append(node('p','Offline / connection unavailable — showing previously loaded destinations. Confirm addresses and site access before travel.'));
    if(orders.length){const all=node('button','Save all destinations ('+orders.length+')');all.className='secondary';all.onclick=()=>saveSheet(orders,'wzos-destinations.txt');root.append(all);}
    const requested=window.WzosNavigation.take?.();let found=false;
    for(const order of orders){const card=node('section','');card.className='report-section panel';card.append(node('h2',order.title),node('p',order.address));if(order.assigned)card.append(node('p','Dispatched destination · confirm current site access in My jobs.'));
     const selected=!!requested&&(requested.assignment_id?order.assignment_id===requested.assignment_id:order.id===requested.id);found=found||selected;
     if(window.WzosNavigationRoute)window.WzosNavigationRoute.attach(card,order,{autoOpen:selected});
     if(order.work_date)card.append(node('p','Work date: '+order.work_date));const save=node('button','Save destination sheet');save.className='secondary';save.onclick=()=>saveSheet([order],'wzos-destination.txt');card.append(save);root.append(card);}
    if(requested&&!found)$('team-notice').textContent='That destination is no longer available in your permitted active jobs.';return;
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
 const providerHelp={'21608':'Trial account: verify the recipient in Twilio.','21610':'Recipient opted out; they must opt back in.','21606':'Check the Twilio sender’s SMS capability.','30034':'Sender A2P registration is incomplete.','20003':'Twilio rejected authentication; check runtime secret bindings.'};
 const smsLine=sms=>'Text message: '+(SMS_STATUS[sms.status]||sms.status)+(sms.phone?' · '+sms.phone:'')+(sms.reason_text?' — '+sms.reason_text:'')+(sms.error_code?' (provider code '+sms.error_code+')':'')+(providerHelp[sms.error_code]?' '+providerHelp[sms.error_code]:'');
 async function guarded(epoch,control,work,done){control.disabled=true;try{await work();if(epoch===generation){await show('messages');if(done)$('team-notice').textContent=done;}}catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}finally{control.disabled=false;}}
 async function messagesView(root,epoch){
  const admin=window.wzosClock.getSession()?.role==='admin';
  const [roster,messages,contact,people,readiness,outbox]=await Promise.all([api('/api/modules/roster'),api('/api/messages'),api('/api/messaging/sms/contact'),
   admin?api('/api/messaging/sms/contacts'):null,admin?api('/api/messaging/sms/readiness'):null,admin?api('/api/messaging/sms/outbox'):null]);
  if(epoch!==generation)return;
  const names=Object.fromEntries(roster.items.map(m=>[m.id,m.name])),smsBy=Object.fromEntries((people?.items||[]).map(p=>[p.id,p.status]));
  root.append(node('p',admin?'Send one-way text notifications to your organization. Replies are not monitored.':'Notifications from your organization. Manage your mobile number below.'));
  // Compose
  const form=node('form',''),label=node('label','Send text to'),recipient=node('select',''),bodyLabel=node('label','Text message'),body=node('textarea',''),submit=node('button','Send text notification');form.className='panel sms-compose';submit.className='primary';body.required=true;body.rows=4;body.maxLength=600;let retry=null;
  for(const member of roster.items){const option=node('option',member.name+' · '+member.role);option.value=member.id;recipient.append(option);}label.append(recipient);bodyLabel.append(body);
  const ackLabel=node('label',''),ack=checkbox();ackLabel.append(ack,' Ask the recipient to acknowledge');
  const smsHint=node('p','');smsHint.setAttribute('role','status');smsHint.className='muted';
  const hint=()=>{const status=smsBy[recipient.value]||'none';submit.disabled=!admin||!readiness?.ready||status!=='verified';smsHint.textContent=!readiness?.ready?'Text sending is unavailable. Review Text message delivery below.':status!=='verified'?'This recipient must enable and verify their mobile number in My text message settings.':readiness.mode==='test'?'Controlled testing: only approved test numbers can receive texts.':'Ready to send by SMS.';};hint();
  form.append(node('h2','Send a text notification'),label,bodyLabel,ackLabel,smsHint,submit);form.oninput=()=>{dirty=true;retry=null;hint();};
  form.onsubmit=async event=>{event.preventDefault();if(sending||submit.disabled||!admin)return;retry=retry||{request_id:crypto.randomUUID(),recipient_id:recipient.value,text:body.value,request_acknowledgement:ack.checked,sms_copy:true};sending=true;submit.disabled=body.disabled=recipient.disabled=true;
   try{const saved=await api('/api/messages',{method:'POST',body:JSON.stringify(retry)});if(epoch===generation){dirty=false;await show('messages');$('team-notice').textContent=saved.sms?(saved.sms.status==='queued'?'Text notification queued. Delivery status appears below.':smsLine(saved.sms)):'Text notification was not queued. Review delivery settings.';}}
   catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}finally{sending=false;body.disabled=recipient.disabled=false;hint();}};if(admin)root.append(form);
  // Inbox and sent items
  const me=window.wzosClock.getSession()?.id;
  root.append(node('h2',admin?'Recent notifications':'My notifications'));
  for(const message of messages.items){if(message.assignment_id&&message.recipient_id===me)continue;const card=node('article','');card.className='report-section panel';
   card.append(node('p',`${names[message.sender_id]||message.sender_id} → ${names[message.recipient_id]||message.recipient_id} · ${new Date(message.created_at).toLocaleString()}`),node('p',message.body));
   if(message.sms)card.append(node('p',smsLine(message.sms)));
   if(message.acknowledgement_requested)card.append(node('p',message.acknowledged_at?'Acknowledged '+new Date(message.acknowledged_at).toLocaleString():'Acknowledgement requested — not yet acknowledged'));
   if(message.acknowledgement_requested&&!message.acknowledged_at&&message.recipient_id===me){const b=button('Acknowledge','primary');b.onclick=()=>guarded(epoch,b,()=>api('/api/messages/'+message.id+'/acknowledge',{method:'POST'}),'Acknowledged.');card.append(b);}
   root.append(card);}
  // Enterprise dispatch (assignments and admin planning) renders here when available.
  await window.wzosDispatch?.render(root,()=>epoch===generation,$('team-notice'));if(epoch!==generation)return;
  // The member's own text message settings; only the phone's owner can turn texts on.
  const mine=node('details',''),mineBody=node('form','');mineBody.onsubmit=event=>event.preventDefault();mine.className='report-section panel';mine.open=contact.status!=='verified';mine.append(node('summary','My text message settings'),mineBody);
  mineBody.append(node('p','Status: '+(CONTACT_STATUS[contact.status]||contact.status)+(contact.phone?' · '+contact.phone:'')));
  if(!contact.sms_ready)mineBody.append(node('p','Text sending is not available in this environment yet. You can still record your number and consent.'));
  const phoneLabel=node('label','Mobile number (US 10 digits or international +country code)'),phone=node('input','');phone.type='tel';phone.autocomplete='tel';phone.value=contact.phone||'';phoneLabel.append(phone);
  const consentLabel=node('label',''),consent=checkbox();consentLabel.append(consent,' '+contact.consent_text);
  const phoneNotice=node('p','');phoneNotice.setAttribute('role','status');phoneNotice.setAttribute('aria-live','polite');
  if(contact.verification_delivery)phoneNotice.textContent=smsLine(contact.verification_delivery);
  const activeExpiry=contact.code_expires_at?Date.parse(contact.code_expires_at):0;
  const activeDelivery=contact.verification_delivery;
  const activeCode=!contact.code_locked&&contact.status==='pending_verification'&&activeExpiry>Date.now()&&['sending','accepted','sent','delivered','ambiguous'].includes(activeDelivery?.status);
  if(activeDelivery&&contact.status==='pending_verification')mineBody.append(node('p','Request '+String(activeDelivery.reference_id||'').slice(-6).toUpperCase()+': code requested '+new Date(activeDelivery.created_at).toLocaleTimeString()+'. Expires '+new Date(activeExpiry).toLocaleTimeString()+'. Use that request�s text; older texts may arrive later.'));
  const request=button(contact.status==='verified'?'Change number':'Send verification code');
  if(activeCode){request.disabled=true;mineBody.append(node('p','A code is already on its way. Wait for it before requesting another. After expiry, refresh verification status.'));}
  phone.oninput=()=>{request.disabled=activeCode&&window.WzosPhone.normalize(phone.value)===contact.phone;};
  request.onclick=async()=>{
   if(!consent.checked){phoneNotice.textContent='Review and check the text message consent box first.';return;}
   const number=window.WzosPhone.normalize(phone.value);if(!number){phoneNotice.textContent='Enter a US 10-digit number, or an international number starting with + and its country code.';return;}
   request.disabled=true;phoneNotice.textContent='Requesting your verification text…';
   try{const result=await api('/api/messaging/sms/contact',{method:'PUT',body:JSON.stringify({request_id:crypto.randomUUID(),expected_version:contact.version,phone:number,consent:true,consent_version:contact.current_consent_version})});
    if(epoch!==generation)return;await show('messages');$('team-notice').textContent=result.existing_code_active?'Your current code is still valid. No replacement text was sent.':result.verification_delivery?smsLine(result.verification_delivery):'Verification requested. Check My text message settings for delivery status.';
   }catch(error){if(epoch===generation)phoneNotice.textContent='Verification not requested: '+error.message;}
   finally{request.disabled=false;}
  };
  const refreshPhone=button('Refresh verification status');refreshPhone.onclick=()=>show('messages');
  mineBody.append(phoneLabel,consentLabel,request,refreshPhone,phoneNotice);
  if(contact.status==='pending_verification'){const codeLabel=node('label','Verification code'),code=node('input','');code.inputMode='numeric';code.autocomplete='one-time-code';code.maxLength=6;codeLabel.append(code);const verify=button('Verify number','primary');
   verify.onclick=()=>{if(!/^[0-9]{6}$/.test(code.value.trim())){phoneNotice.textContent='Enter the 6-digit code from the text message.';return;}guarded(epoch,verify,()=>api('/api/messaging/sms/contact/verify',{method:'POST',body:JSON.stringify({code:code.value.trim()})}),'Number verified. Text messages are on.');};mineBody.append(codeLabel,verify);}
  if(['verified','pending_verification'].includes(contact.status)){const stop=button('Turn off text messages');stop.onclick=()=>guarded(epoch,stop,()=>api('/api/messaging/sms/contact/opt-out',{method:'POST',body:JSON.stringify({expected_version:contact.version})}),'Text messages turned off.');mineBody.append(stop);}
  mineBody.append(node('p','You can also reply STOP to any WZOS text. WZOS messages remain available in the app.'));
  if(contact.status!=='verified')root.prepend(mine);else root.append(mine);
  if(!admin)return;
  // Admin delivery oversight for this organization only.
  const panel=node('details',''),inner=node('section','');panel.className='report-section panel';panel.append(node('summary','Text message delivery (admin)'),inner);
  inner.append(node('p','Sending mode: '+readiness.mode+(readiness.ready?' · ready':' · not ready')+(readiness.mode==='test'?' · approved test numbers: '+readiness.test_recipient_count:'')));
  if(readiness.missing.length)inner.append(node('p','Missing settings: '+readiness.missing.join(', ')));
  const team=node('ul','');for(const p of people.items)team.append(node('li',`${p.name}: ${CONTACT_STATUS[p.status]||p.status}${p.phone?' · '+p.phone:''}`));inner.append(node('h3','Team text message status'),team);
  const run=button('Send queued texts now');run.onclick=()=>guarded(epoch,run,()=>api('/api/messaging/sms/process',{method:'POST'}),'Queue processed.');inner.append(node('h3','Recent texts'),run);
  if(!outbox.items.length)inner.append(node('p','No text messages yet.'));
  for(const row of outbox.items){const item=node('article','');item.className='clock-entry';
   item.append(node('p',`${names[row.recipient_id]||row.recipient_id} · ${row.purpose==='verification'?'Verification code':row.purpose==='form_submission'?'Office notification':'Text notification'} · ${new Date(row.created_at).toLocaleString()} · attempts ${row.attempts}`),node('p',smsLine(row)));
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
 // Destination sheets are plain-text address references for travel without a connection.
 // They are not maps, routes or verified site access, and they never include private files.
 function saveSheet(orders,filename){
  const lines=['WZOS destination sheet','Saved on device: '+new Date().toISOString(),'Address reference only. No map, route, traffic or safe-access verification. Confirm details with your admin before travel.',''];
  for(const order of orders)lines.push(order.title,order.address,...(order.locality?['Locality: '+order.locality]:[]),...(order.work_date?['Work date: '+order.work_date]:[]),'Google Maps search: https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(order.address),'');
  const url=URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/plain;charset=utf-8'}));const link=node('a','');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 window.addEventListener('beforeunload',event=>{if(dirty||sending){event.preventDefault();event.returnValue='';}});
})();
