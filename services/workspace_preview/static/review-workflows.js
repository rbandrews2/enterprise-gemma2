"use strict";
// A visible in-app office alert, including reports submitted by the admin themself.
(() => {
 const alert=document.createElement('section'),text=document.createElement('span'),open=document.createElement('button');
 alert.className='panel report-section';alert.hidden=true;alert.setAttribute('role','status');alert.setAttribute('aria-live','polite');
 open.type='button';open.className='secondary';open.textContent='Open office forms';open.onclick=()=>window.showWzosView('forms');
 alert.append(text,open);document.getElementById('main').prepend(alert);
 let generation=0,pending=null;
 async function refresh(){
  const user=window.wzosClock.getSession(),scope=generation;
  if(user?.role!=='admin'||document.hidden){alert.hidden=true;return;}
  if(pending===scope)return;pending=scope;
  try{const data=await window.wzosClock.api('/api/form-submissions/summary');if(scope!==generation)return;
   alert.hidden=!data.pending_count;text.textContent=`${data.pending_count} form${data.pending_count===1?'':'s'} received by office and awaiting review. `;
  }catch{if(scope===generation)alert.hidden=true;}finally{if(pending===scope)pending=null;}
 }
 document.addEventListener('wzos:session',()=>{generation++;alert.hidden=true;refresh();});
 for(const event of ['wzos:office-sent','wzos:office-reviewed','visibilitychange'])document.addEventListener(event,refresh);
 setInterval(refresh,60000);
})();
// Shared review workflow integration; module editors remain responsible for drafts.
(() => {
 const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;if(tag==='button')n.className='secondary';return n;};
 const api=(...args)=>window.wzosClock.api(...args);
 let view=null,epoch=0,offset=0,draftOffset=0,busy=false;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>!busy&&(!previous||previous());
 const root=el('section');root.className='panel report-section';root.id='form-submission-panel';
 document.getElementById('forms-view').append(root);
 async function show(){
  const generation=++epoch;root.replaceChildren();if(view!=='forms')return;
  const notice=el('p');notice.setAttribute('role','status');root.append(notice);
  try{
   const submissions=await api(`/api/form-submissions?offset=${offset}`);
   if(generation!==epoch)return;
   root.append(el('h2',submissions.can_review?'Office received forms':'Your sent forms'));
   for(const item of submissions.items){
    const card=el('article');card.className='report-section panel';
    card.append(el('h3',item.form.title),el('p',`Revision ${item.form_version} · ${item.status.replaceAll('_',' ')} · ${new Date(item.submitted_at).toLocaleString()}`));
    const details=el('details');details.append(el('summary','View submitted content'));
    for(const key of ['location','details'])if(item.form[key])details.append(el('p',item.form[key]));
    for(const group of ['inspection','safety'])for(const [key,value] of Object.entries(item.form[group]||{}))details.append(el('p',`${key.replaceAll('_',' ')}: ${value??'Not recorded'}`));
    if(item.form.form_type==='printable'){
     if(item.form.order)details.append(el('p','Work order: '+item.form.order));
     for(const section of item.form.template?.sections||[]){details.append(el('h4',section.title));for(const field of section.fields){const value=item.form.fields[field.key];if(value!==undefined&&value!=='')details.append(el('p',field.label+': '+(typeof value==='object'?JSON.stringify(value):value)));}}
     const print=el('button','Print received form or save as PDF');print.onclick=()=>window.WzosForms?.printReceived(item.form);details.append(print);
    }
    details.append(el('p',`Submitted by: ${item.submitted_by}`));card.append(details);
    if(item.note)card.append(el('p',`Admin note: ${item.note}`));
    if(submissions.can_review&&item.status==='received'){
     const label=el('label','Review note'),note=el('textarea');note.maxLength=2000;label.append(note);card.append(label);
     for(const [status,title] of [['reviewed','Mark reviewed'],['changes_requested','Request changes']]){
      const button=el('button',title);button.onclick=async()=>{if(busy)return;busy=true;button.disabled=true;
       try{await api(`/api/form-submissions/${item.id}/review`,{method:'POST',body:JSON.stringify({expected_version:item.version,status,note:note.value})});if(generation===epoch){document.dispatchEvent(new CustomEvent('wzos:office-reviewed'));await show();}}
       catch(error){if(generation===epoch)notice.textContent=error.message;}finally{busy=false;button.disabled=false;}
      };card.append(button);
     }
    }
    root.append(card);
   }
   root.append(el('p',`${submissions.total} submissions · page ${Math.floor(offset/25)+1}. Internal review does not establish regulatory approval.`));
   for(const [title,step,disabled] of [['Previous',-25,offset===0],['Next',25,offset+25>=submissions.total]]){const button=el('button',title);button.disabled=disabled;button.onclick=()=>{if(!busy){offset=Math.max(0,offset+step);show();}};root.append(button);}
  }catch(error){if(generation===epoch)notice.textContent=error.message;}
 }
 document.addEventListener('wzos:office-sent',()=>{offset=0;show();});
 document.addEventListener('wzos:view',event=>{view=event.detail;offset=0;draftOffset=0;show();});
 document.addEventListener('wzos:session',()=>{offset=0;draftOffset=0;show();});
})();

// Study acknowledgements are independent of the study-plan editor.
(() => {
 const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;if(tag==='button')n.className='secondary';return n;};
 const api=(...args)=>window.wzosClock.api(...args);
 let view=null,epoch=0,offset=0,busy=false;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>!busy&&(!previous||previous());
 const root=el('details');root.className='panel report-section workspace-details';root.id='training-record-panel';
 document.getElementById('team-view').append(root);
 async function show(){
  const generation=++epoch;root.replaceChildren();root.hidden=view!=='training';if(root.hidden)return;
  root.append(el('summary','Study records and review'),el('p','Report completed study. These records do not issue certificates or verify qualifications.'));
  const notice=el('p');notice.setAttribute('role','status');root.append(notice);
  try{
   const [catalog,records]=await Promise.all([api('/api/training-records/catalog'),api(`/api/training-records?offset=${offset}`)]);
   if(generation!==epoch)return;
   const form=el('form'),course=el('select');
   for(const row of catalog.items){const option=el('option',row.title);option.value=row.id;course.append(option);}
   const add=(title,input)=>{const label=el('label',title);label.append(input);form.append(label);return input;};
   add('Course',course);
   const day=add('Study date',el('input'));day.type='date';day.required=true;day.value=new Date().toISOString().slice(0,10);day.max=day.value;
   const minutes=add('Minutes studied',el('input'));minutes.type='number';minutes.min=1;minutes.max=1440;minutes.step=1;minutes.required=true;
   const material=add('Material studied (title or reference)',el('input'));material.required=true;material.minLength=3;material.maxLength=1000;
   const notes=add('Study notes',el('textarea'));notes.maxLength=2000;
   const confirmed=add('I personally completed this study',el('input'));confirmed.type='checkbox';confirmed.required=true;
   const submit=el('button','Submit study record');submit.type='submit';submit.className='primary';form.append(submit);let retry=null;
   form.addEventListener('input',()=>{retry=null;});
   form.onsubmit=async event=>{event.preventDefault();if(busy||!form.reportValidity())return;busy=true;submit.disabled=true;
    const selected=catalog.items.find(item=>item.id===course.value);
    retry=retry||crypto.randomUUID();
    try{await api('/api/training-records',{method:'POST',body:JSON.stringify({request_id:retry,course_id:selected.id,catalog_hash:selected.catalog_hash,completed_on:day.value,minutes:Number(minutes.value),material_reference:material.value,notes:notes.value,acknowledged:confirmed.checked})});if(generation===epoch)await show();}
    catch(error){if(generation===epoch)notice.textContent=error.message;}finally{busy=false;submit.disabled=false;}
   };root.append(form,el('h2',records.can_review?'Organization study review':'Your study records'));
   if(!records.items.length)root.append(el('p','No study records yet.'));
   for(const item of records.items){
    const card=el('article');card.className='panel report-section';const study=item.record.acknowledgement;
    card.append(el('h3',item.record.course.title),el('p',`${item.status.replaceAll('_',' ')} · ${study.completed_on} · ${study.minutes} minutes`),el('p',study.material_reference),el('p',`Reported by ${item.user_id} · course status: ${item.record.course.status}`));
    if(study.notes)card.append(el('p',study.notes));if(item.note)card.append(el('p',`Admin note: ${item.note}`));
    if(records.can_review&&item.status==='received'){
     const label=el('label','Review note'),note=el('textarea');note.maxLength=2000;label.append(note);card.append(label);
     for(const [status,title] of [['reviewed','Acknowledge review'],['changes_requested','Request follow-up']]){
      const button=el('button',title);button.onclick=async()=>{if(busy)return;busy=true;button.disabled=true;
       try{await api(`/api/training-records/${item.id}/review`,{method:'POST',body:JSON.stringify({expected_version:item.version,status,note:note.value})});if(generation===epoch)await show();}
       catch(error){if(generation===epoch)notice.textContent=error.message;}finally{busy=false;button.disabled=false;}
      };card.append(button);
     }
    }root.append(card);
   }
   root.append(el('p',`${records.total} records · page ${Math.floor(offset/25)+1}`));
   for(const [title,step,disabled] of [['Previous records',-25,offset===0],['Next records',25,offset+25>=records.total]]){const button=el('button',title);button.disabled=disabled;button.onclick=()=>{if(!busy){offset=Math.max(0,offset+step);show();}};root.append(button);}
  }catch(error){if(generation===epoch)notice.textContent=error.message;}
 }
 document.addEventListener('wzos:view',event=>{view=event.detail;offset=0;show();});
 document.addEventListener('wzos:session',()=>{offset=0;show();});
})();
