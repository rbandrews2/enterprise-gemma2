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
    root.append(node('p','Loaded destinations remain available in this open app when offline. Save a destination sheet before travel for access after closing the app. Map imagery, live traffic and route guidance require connectivity or separately downloaded maps in your navigation app.'));
    let orders=window.wzosClock.getOrders(),cached=!navigator.onLine;
    if(navigator.onLine){try{orders=(await api('/api/orders')).items;}catch(error){if(error.status)throw error;cached=true;}}
    if(epoch!==generation)return;
    if(cached)root.append(node('p','Offline / connection unavailable — showing previously loaded destinations. Confirm addresses and site access before travel.'));
    if(!orders.length)root.append(node('p','No destinations loaded. Connect and open your jobs before going offline.'));
    else{const all=node('button','Save all destinations ('+orders.length+')');all.className='secondary';all.onclick=()=>saveSheet(orders,'wzos-destinations.txt');root.append(all);}
    for(const order of orders){const card=node('section','');card.className='report-section panel';card.append(node('h2',order.title),node('p',order.address));const a=node('a','Open destination in Google Maps');a.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(order.address);a.target='_blank';a.rel='noopener noreferrer';card.append(a);
     if(order.work_date)card.append(node('p','Work date: '+order.work_date));const save=node('button','Save destination sheet');save.className='secondary';save.onclick=()=>saveSheet([order],'wzos-destination.txt');card.append(save);root.append(card);}return;
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
 // Destination sheets are plain-text address references for travel without a connection.
 // They are not maps, routes or verified site access, and they never include private files.
 function saveSheet(orders,filename){
  const lines=['WZOS destination sheet','Saved on device: '+new Date().toISOString(),'Address reference only. No map, route, traffic or safe-access verification. Confirm details with your admin before travel.',''];
  for(const order of orders)lines.push(order.title,order.address,...(order.locality?['Locality: '+order.locality]:[]),...(order.work_date?['Work date: '+order.work_date]:[]),'Google Maps search: https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(order.address),'');
  const url=URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/plain;charset=utf-8'}));const link=node('a','');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 for(const name of ['training','messages','navigation'])$(name+'-nav').onclick=()=>window.showWzosView(name);
 document.addEventListener('wzos:view',event=>show(event.detail));
 document.addEventListener('wzos:session',()=>show(view));
 for(const event of ['online','offline'])window.addEventListener(event,()=>{if(view==='navigation')show(view);});
 window.addEventListener('beforeunload',event=>{if(dirty||sending){event.preventDefault();event.returnValue='';}});
})();
