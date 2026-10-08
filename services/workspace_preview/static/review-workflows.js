"use strict";
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
  root.append(el('h2','Submit a saved form'),el('p','Send a saved revision to your organization’s admin review queue. Save edits first. Attachments and email/text delivery are not included.'));
  const notice=el('p');notice.setAttribute('role','status');root.append(notice);
  try{
   const [drafts,submissions]=await Promise.all([api(`/api/modules/forms?limit=50&offset=${draftOffset}`),api(`/api/form-submissions?offset=${offset}`)]);
   if(generation!==epoch)return;
   const label=el('label','Saved revision'),select=el('select');
   for(const row of drafts.items){const option=el('option',`${row.title} · revision ${row.version}`);option.value=row.id;select.append(option);}label.append(select);
   const submit=el('button','Submit saved revision');submit.type='button';submit.className='primary';submit.disabled=!drafts.items.length;let retry=null;
   select.onchange=()=>{retry=null;};
   submit.onclick=async()=>{
    if(busy)return;const row=drafts.items.find(item=>item.id===select.value);if(!row)return;
    retry=retry||{request_id:crypto.randomUUID(),form_id:row.id,expected_form_version:row.version};busy=true;submit.disabled=true;
    try{await api('/api/form-submissions',{method:'POST',body:JSON.stringify(retry)});if(generation===epoch){await show();}}
    catch(error){if(generation===epoch)notice.textContent=error.message;}finally{busy=false;submit.disabled=false;}
   };
   root.append(label,submit,el('p',`Showing ${drafts.items.length} of ${drafts.total} saved forms. Submission history below confirms receipt.`));
   for(const [title,step,disabled] of [['Previous saved forms',-50,draftOffset===0],['Next saved forms',50,draftOffset+50>=drafts.total]]){const button=el('button',title);button.disabled=disabled;button.onclick=()=>{if(!busy){draftOffset=Math.max(0,draftOffset+step);show();}};root.append(button);}
   const refresh=el('button','Refresh saved forms and submissions');refresh.onclick=()=>{if(!busy)show();};root.append(refresh);
   root.append(el('h2',submissions.can_review?'Organization form review queue':'Your submissions'));
   for(const item of submissions.items){
    const card=el('article');card.className='report-section panel';
    card.append(el('h3',item.form.title),el('p',`Revision ${item.form_version} · ${item.status.replaceAll('_',' ')} · ${new Date(item.submitted_at).toLocaleString()}`));
    const details=el('details');details.append(el('summary','View submitted content'));
    for(const key of ['location','details'])if(item.form[key])details.append(el('p',item.form[key]));
    for(const group of ['inspection','safety'])for(const [key,value] of Object.entries(item.form[group]||{}))details.append(el('p',`${key.replaceAll('_',' ')}: ${value??'Not recorded'}`));
    details.append(el('p',`Submitted by: ${item.submitted_by}`));card.append(details);
    if(item.note)card.append(el('p',`Admin note: ${item.note}`));
    if(submissions.can_review&&item.status==='received'){
     const label=el('label','Review note'),note=el('textarea');note.maxLength=2000;label.append(note);card.append(label);
     for(const [status,title] of [['reviewed','Mark reviewed'],['changes_requested','Request changes']]){
      const button=el('button',title);button.onclick=async()=>{if(busy)return;busy=true;button.disabled=true;
       try{await api(`/api/form-submissions/${item.id}/review`,{method:'POST',body:JSON.stringify({expected_version:item.version,status,note:note.value})});if(generation===epoch)await show();}
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
 const root=el('section');root.className='panel report-section';root.id='training-record-panel';
 document.getElementById('team-view').append(root);
 async function show(){
  const generation=++epoch;root.replaceChildren();root.hidden=view!=='training';if(root.hidden)return;
  root.append(el('h2','Record completed study'),el('p','Report study you personally completed. These records and admin reviews do not issue a certificate or establish a qualification. Course content remains pending review.'));
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
