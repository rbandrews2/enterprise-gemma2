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
   const importButton=node('button','Import employees / View imported roster');importButton.type='button';importButton.onclick=()=>importEmployees(api);content.append(importButton);
   const imported=await api('/api/account/employee-import/roster');
   if(imported.items.length){content.append(node('h3',`Imported employees (${imported.total})`));for(const person of imported.items)content.append(node('p',`${person.name} — ${person.employee_number}`));}
   for(const person of data.items){const button=node('button',person.name+' — '+(person.employee_number||'Profile not configured')+(person.active?'':' — Inactive'));button.type='button';button.onclick=()=>run(()=>detail(person.id));content.append(button);}
   for(const [label,next] of [['Previous',offset-25],['Next',offset+25]])if(next>=0&&next<data.total){const button=node('button',label);button.type='button';button.onclick=()=>run(()=>directory(next));content.append(button);}
  }
  await run(()=>session.can_manage_team?directory():detail(session.id));
 }
 async function importEmployees(api){
  const dialog=node('dialog');dialog.className='account-dialog employee-import-dialog';
  const status=node('p');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  const content=node('div');let batch=null,busy=false,epoch=0;
  const makeButton=(text,action)=>{const b=node('button',text);b.type='button';b.onclick=action;return b;};
  const close=makeButton('Close',()=>dialog.close());
  dialog.addEventListener('close',()=>{epoch++;dialog.remove();},{once:true});
  const sessionChanged=()=>dialog.close();document.addEventListener('wzos:session',sessionChanged);
  dialog.addEventListener('close',()=>document.removeEventListener('wzos:session',sessionChanged),{once:true});
  const template=makeButton('Download CSV template',()=>{
   const url=URL.createObjectURL(new Blob(['name,email,employee_number,phone\r\n'],{type:'text/csv;charset=utf-8'}));
   const a=node('a');a.href=url;a.download='wzos-employees-template.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  const fileLabel=node('label','Employee CSV file');const file=node('input');file.type='file';file.accept='.csv,text/csv';fileLabel.append(file);
  const review=makeButton('Upload & review',async()=>{
   if(busy)return;if(!file.files?.[0]){status.textContent='Choose a CSV file first.';return;}
   if(file.files[0].size>512*1024){status.textContent='Choose a file no larger than 512 KiB.';return;}
   const generation=++epoch;busy=true;file.disabled=true;review.disabled=true;confirm.disabled=true;batch=null;content.replaceChildren();status.textContent='Checking employee rows…';
   try{let csv_text;try{csv_text=new TextDecoder('utf-8',{fatal:true}).decode(await file.files[0].arrayBuffer());}catch{throw Error('Save the file as UTF-8 CSV and try again.');}const data=await api('/api/account/employee-import/review',{csv_text});if(generation!==epoch)return;
    batch=data;renderRows(data.rows);checked.checked=false;
    status.textContent=`${data.ready} ready · ${data.duplicates} duplicates skipped · ${data.errors} errors. ${data.errors?'Correct errors in your file and upload again.':'Review the rows, then confirm.'}`;
   }catch(e){if(generation===epoch)status.textContent=e.message;}finally{if(generation===epoch){busy=false;file.disabled=false;review.disabled=false;sync();}}
  });
  const checked=node('input');checked.type='checkbox';const approve=node('label','I reviewed these employees and the skipped duplicates.');approve.prepend(checked);
  const confirm=makeButton('Confirm import',async()=>{
   if(busy||!batch||!checked.checked)return;busy=true;file.disabled=true;review.disabled=true;confirm.disabled=true;status.textContent='Importing employees…';const generation=epoch;
   try{const receipt=await api(`/api/account/employee-import/${encodeURIComponent(batch.id)}/confirm`,{reviewed:true});if(generation!==epoch)return;
    status.textContent=`Imported ${receipt.imported} employees. ${receipt.skipped} duplicates skipped. No invitations sent.`;batch=null;checked.checked=false;file.value='';
    const roster=await api('/api/account/employee-import/roster');if(generation===epoch){renderRows(roster.items);rosterPaging(roster);}
   }catch(e){if(generation===epoch)status.textContent=e.message;}finally{if(generation===epoch){busy=false;file.disabled=false;review.disabled=false;sync();}}
  });
  function sync(){confirm.disabled=busy||!batch||!batch.ready||!!batch.errors||!checked.checked;}
  checked.onchange=sync;file.onchange=()=>{if(busy)return;epoch++;batch=null;checked.checked=false;content.replaceChildren();status.textContent='';sync();};sync();
  function renderRows(rows){content.replaceChildren();const table=node('table');table.className='employee-import-table';const head=node('tr');
   for(const label of ['Row','Name','Email','Employee number','Phone','Review'])head.append(node('th',label));const thead=node('thead');thead.append(head);table.append(thead);const body=node('tbody');
   for(const r of rows){const tr=node('tr');for(const value of [r.row??'',r.name,r.email,r.employee_number,r.phone,r.issues?.length?r.issues.join(' '):(r.status||'Imported')])tr.append(node('td',String(value)));body.append(tr);}table.append(body);content.append(table);
  }
  async function loadRoster(offset=0){if(busy)return;busy=true;const generation=++epoch;batch=null;sync();status.textContent='Loading imported employees…';try{const data=await api('/api/account/employee-import/roster?offset='+offset);if(generation===epoch){renderRows(data.items);rosterPaging(data);status.textContent=data.total?`${data.total} imported employees.`:'No employees imported yet.';}}catch(e){if(generation===epoch)status.textContent=e.message;}finally{busy=false;sync();}}
  function rosterPaging(data){for(const [label,next] of [['Previous',data.offset-25],['Next',data.offset+25]])if(next>=0&&next<data.total)content.append(makeButton(label,()=>loadRoster(next)));}
  const roster=makeButton('View imported employees',()=>loadRoster());
  dialog.append(node('h2','Import employees'),node('p','Download the template, add up to 500 employees, then upload and review. Imports add roster records only. Invite employees separately through Team access.'),template,fileLabel,review,status,content,approve,confirm,roster,close);
  document.body.append(dialog);dialog.showModal();
 }
 return {open,importEmployees};
})();
