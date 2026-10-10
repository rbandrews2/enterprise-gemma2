"use strict";
window.wzosEmployees = (() => {
 const node=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 async function open(api,session){
  const dialog=node('dialog');dialog.className='account-dialog';
  const message=node('p');message.setAttribute('role','status');
  const content=node('div');const close=node('button','Close');close.type='button';
  let dirty=false;
  function dismiss(){if(dirty&&!window.confirm('Discard unsaved employee changes?'))return;dialog.close();dialog.remove();}
  close.onclick=dismiss;dialog.addEventListener('cancel',e=>{e.preventDefault();dismiss();});
  dialog.append(node('h2',session.can_manage_team?'Employee directory':'My employee record'),message,content,close);
  document.body.append(dialog);dialog.showModal();
  async function run(task){message.textContent='Loading…';try{await task();}catch(e){message.textContent=e.message;}}
  function field(form,label,value,type='text',required=false){
   const wrap=node('label',label);const input=node('input');input.type=type;input.value=value||'';input.required=required;
   input.oninput=()=>{dirty=true;};wrap.append(input);form.append(wrap);return input;
  }
  async function detail(id){
   const data=await api('/api/account/employees/'+encodeURIComponent(id));content.replaceChildren();dirty=false;message.textContent='';
   content.append(node('h3',data.name),node('p',data.active?'Active membership':'Inactive membership'));
   const profile=data.profile||{};const form=node('form');
   const number=field(form,'Employee number',profile.employee_number,'text',true);number.maxLength=40;
   const address=field(form,'Address (private)',profile.address);address.maxLength=400;
   const phone=field(form,'Phone (international format, e.g. +15555550123)',profile.phone,'tel');phone.maxLength=20;
   const start=field(form,'Agreed starting location',profile.starting_location);start.maxLength=400;
   const notes=field(form,'Profile notes',profile.notes);notes.maxLength=1000;
   const availability=(profile.availability||[]).map(item=>({...item}));
   form.append(node('h3','Availability'),node('p','Explicit available or unavailable periods. Unspecified time remains unknown. Enter times in your device timezone; saved records use UTC.'));
   const windows=node('div');form.append(windows);
   function renderWindows(){windows.replaceChildren();if(!availability.length)windows.append(node('p','No availability recorded.'));
    availability.forEach((item,index)=>{const row=node('section');row.append(node('p',item.status+' • '+new Date(item.starts_at).toLocaleString()+' to '+new Date(item.ends_at).toLocaleString()),node('p',item.note));
     if(session.can_manage_team){const remove=node('button','Remove period');remove.type='button';remove.onclick=()=>{availability.splice(index,1);dirty=true;renderWindows();};row.append(remove);}windows.append(row);});
   }renderWindows();
   if(session.can_manage_team){
    const inputs=node('div');const from=field(inputs,'Period start','','datetime-local');const until=field(inputs,'Period end','','datetime-local');
    const label=node('label','Availability');const state=node('select');for(const value of ['available','unavailable']){const option=node('option',value);option.value=value;state.append(option);}label.append(state);inputs.append(label);
    const note=field(inputs,'Period note','');note.maxLength=200;const add=node('button','Add period');add.type='button';
    add.onclick=()=>{if(!from.value||!until.value){message.textContent='Enter both start and end times.';return;}
     const start=new Date(from.value),end=new Date(until.value);if(!Number.isFinite(start.getTime())||!Number.isFinite(end.getTime())||end<=start){message.textContent='End time must follow start time.';return;}
     if(availability.length>=100){message.textContent='Maximum100 availability periods.';return;}
     if(availability.some(item=>new Date(item.starts_at)<end&&new Date(item.ends_at)>start)){message.textContent='Availability periods must not overlap.';return;}
     availability.push({starts_at:start.toISOString(),ends_at:end.toISOString(),status:state.value,note:note.value});availability.sort((a,b)=>a.starts_at.localeCompare(b.starts_at));dirty=true;from.value=until.value=note.value='';renderWindows();message.textContent='Period added to draft. Save employee to keep it.';
    };inputs.append(add);form.append(inputs);
   }
   if(!session.can_manage_team){for(const input of form.querySelectorAll('input'))input.readOnly=true;}
   else{const save=node('button','Save employee');save.type='submit';form.append(save);
    form.onsubmit=e=>{e.preventDefault();if(!form.reportValidity())return;save.disabled=true;run(async()=>{
     await api('/api/account/employees/'+encodeURIComponent(id),{expected_version:profile.version||0,employee_number:number.value,address:address.value,phone:phone.value,starting_location:start.value,notes:notes.value,availability},'PUT');
     await detail(id);message.textContent='Employee saved.';
    }).finally(()=>{save.disabled=false;});};}
   content.append(form,node('h3','Qualifications'),node('p','Admin verification records the evidence reviewed. It does not establish eligibility for every job or issue an agency certificate.'));
   for(const qualification of data.qualifications){const row=node('section');row.className='panel';row.append(node('p',qualification.title+' — '+qualification.current_status),node('p','Issuer: '+(qualification.issuer||'Not recorded')+' • Expiry: '+(qualification.expires_on||'Not recorded')));
    if(session.can_manage_team){const edit=node('button','Edit qualification');edit.type='button';edit.onclick=()=>qualificationEditor(id,qualification);row.append(edit);}content.append(row);}
   if(session.can_manage_team){const add=node('button','Add qualification');add.type='button';add.onclick=()=>qualificationEditor(id,null);content.append(add);
    const back=node('button','Back to directory');back.type='button';back.onclick=()=>{if(dirty&&!window.confirm('Discard unsaved changes?'))return;dirty=false;run(()=>directory());};content.append(back);}
  }
  function qualificationEditor(id,current){
   if(dirty&&!window.confirm('Discard unsaved changes?'))return;
   const q=current||{};content.replaceChildren();dirty=false;message.textContent='';const form=node('form');
   content.append(node('h3',current?'Edit qualification':'Add qualification'));
   const title=field(form,'Qualification title',q.title,'text',true);title.maxLength=160;
   const issuer=field(form,'Issuing organization',q.issuer);issuer.maxLength=160;
   const number=field(form,'Credential number',q.credential_number);number.maxLength=100;
   const issued=field(form,'Issue date',q.issued_on,'date');const expiry=field(form,'Expiry date',q.expires_on,'date');
   const evidence=field(form,'Evidence reference (secure record or document identifier)',q.evidence_reference);evidence.maxLength=500;
   const note=field(form,'Review note',q.review_note);note.maxLength=1000;
   const label=node('label','Review status');const status=node('select');for(const value of ['unreviewed','verified','rejected']){const o=node('option',value);o.value=value;status.append(o);}status.value=q.review_status||'unreviewed';status.onchange=()=>{dirty=true;};label.append(status);form.append(label);
   const save=node('button','Save qualification');save.type='submit';const back=node('button','Back');back.type='button';back.onclick=()=>{if(dirty&&!window.confirm('Discard unsaved changes?'))return;run(()=>detail(id));};form.append(save,back);content.append(form);
   const qualificationId=q.id||crypto.randomUUID();
   form.onsubmit=e=>{e.preventDefault();if(!form.reportValidity())return;save.disabled=true;run(async()=>{
    await api('/api/account/employees/'+encodeURIComponent(id)+'/qualifications/'+encodeURIComponent(qualificationId),{expected_version:q.version||0,title:title.value,issuer:issuer.value,credential_number:number.value,issued_on:issued.value||null,expires_on:expiry.value||null,evidence_reference:evidence.value,review_note:note.value,review_status:status.value},'PUT');
    await detail(id);message.textContent='Qualification saved.';
   }).finally(()=>{save.disabled=false;});};
  }
  async function directory(offset=0){
   const data=await api('/api/account/employees?offset='+offset+'&limit=25');content.replaceChildren();dirty=false;message.textContent='';
   content.append(node('p',data.total+' organization members'));
   for(const person of data.items){const button=node('button',person.name+' — '+(person.employee_number||'Profile not configured')+(person.active?'':' — Inactive'));button.type='button';button.onclick=()=>run(()=>detail(person.id));content.append(button);}
   for(const [label,next] of [['Previous',offset-25],['Next',offset+25]])if(next>=0&&next<data.total){const button=node('button',label);button.type='button';button.onclick=()=>run(()=>directory(next));content.append(button);}
  }
  await run(()=>session.can_manage_team?directory():detail(session.id));
 }
 return {open};
})();
