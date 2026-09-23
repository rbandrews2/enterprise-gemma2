"use strict";
(() => {
 const $=id=>document.getElementById(id),api=(...a)=>window.wzosClock.api(...a),node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
 let generation=0, view=null, dirty=false, sending=false;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>previous()&&!sending&&(!dirty||confirm('Leave the unsaved test message?'));
 async function show(name){
  generation++;view=name;dirty=false;const epoch=generation,root=$('team-content');root.replaceChildren();$('team-notice').textContent='';
  if(!['training','messages','navigation'].includes(name))return;
  $('team-title').textContent={training:'Training study planner',messages:'Test messaging',navigation:'Navigation'}[name];
  try{
   if(name==='navigation'){
    root.append(node('p','Open a saved job destination in Google Maps. Confirm the location before starting directions. No offline maps or live hazard feed are connected.'));
    const data=await api('/api/orders');if(epoch!==generation)return;
    for(const order of data.items){const card=node('section','');card.className='report-section panel';card.append(node('h2',order.title),node('p',order.address));const a=node('a','Open destination in Google Maps');a.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(order.address);a.target='_blank';a.rel='noopener noreferrer';card.append(a);root.append(card);}return;
   }
   if(name==='training'){
    root.append(node('p','Recovered V1 course catalog. Course content and accreditation are awaiting review. These are personal study plans, not completion records or certificates.'));
    const data=await api('/api/training');if(epoch!==generation)return;
    for(const course of data.items){const card=node('section','');card.className='report-section panel';card.append(node('h2',course.title),node('p',course.description));const label=node('label','Study status'),select=node('select','');for(const [value,title] of Object.entries({not_started:'Not started',studying:'Studying',review_requested:'Ready for review (not sent)'})){const option=node('option',title);option.value=value;select.append(option);}select.value=course.study_status;const save=node('button','Save study status');save.className='secondary';save.onclick=async()=>{save.disabled=true;try{await api('/api/training/'+course.id,{method:'PUT',body:JSON.stringify({status:select.value})});if(epoch===generation)$('team-notice').textContent='Study status saved. No certificate or notification issued.';}catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}finally{save.disabled=false;}};label.append(select);card.append(label,save);root.append(card);}return;
   }
   const [roster,messages]=await Promise.all([api('/api/modules/roster'),api('/api/messages')]);if(epoch!==generation)return;
   root.append(node('p','Synthetic test inbox only. No email, SMS or real employee delivery. Shows up to 50 recent records.'));
   const form=node('form',''),label=node('label','Test recipient'),recipient=node('select',''),bodyLabel=node('label','Test message'),body=node('textarea',''),submit=node('button','Store test message');submit.className='primary';body.required=true;body.maxLength=2000;let retry=null;
   for(const member of roster.items){const option=node('option',member.name+' · '+member.role);option.value=member.id;recipient.append(option);}label.append(recipient);bodyLabel.append(body);form.append(label,bodyLabel,submit);form.oninput=()=>{dirty=true;retry=null;};
   form.onsubmit=async event=>{event.preventDefault();if(sending)return;retry=retry||{request_id:crypto.randomUUID(),recipient_id:recipient.value,text:body.value};sending=true;submit.disabled=body.disabled=recipient.disabled=true;
    try{await api('/api/messages',{method:'POST',body:JSON.stringify(retry)});if(epoch===generation){dirty=false;await show('messages');$('team-notice').textContent='Stored for the test recipient. No external delivery.';}}
    catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}finally{sending=false;submit.disabled=body.disabled=recipient.disabled=false;}};root.append(form);
   for(const message of messages.items){const card=node('article','');card.className='report-section panel';card.append(node('p',`${message.sender_id} → ${message.recipient_id} · ${new Date(message.created_at).toLocaleString()}`),node('p',message.body));root.append(card);}
  }catch(error){if(epoch===generation)$('team-notice').textContent=error.message;}
 }
 for(const name of ['training','messages','navigation'])$(name+'-nav').onclick=()=>window.showWzosView(name);
 document.addEventListener('wzos:view',event=>show(event.detail));
 document.addEventListener('wzos:session',()=>show(view));
 window.addEventListener('beforeunload',event=>{if(dirty||sending){event.preventDefault();event.returnValue='';}});
})();
