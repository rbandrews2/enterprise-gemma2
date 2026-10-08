"use strict";
// Shared review workflow integration; module editors remain responsible for drafts.
(() => {
 const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;return n;};
 const api=(...args)=>window.wzosClock.api(...args);
 let view=null,epoch=0,offset=0,busy=false;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>!busy&&(!previous||previous());
 const root=el('section');root.className='panel report-section';root.id='form-submission-panel';
 document.getElementById('forms-view').append(root);
 async function show(){
  const generation=++epoch;root.replaceChildren();if(view!=='forms')return;
  root.append(el('h2','Submit a saved form'),el('p','Send a saved revision to your organization’s admin review queue. Save edits first. Attachments and email/text delivery are not included.'));
  const notice=el('p');notice.setAttribute('role','status');root.append(notice);
  try{
   const [drafts,submissions]=await Promise.all([api('/api/modules/forms?limit=50'),api(`/api/form-submissions?offset=${offset}`)]);
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
 document.addEventListener('wzos:view',event=>{view=event.detail;offset=0;show();});
 document.addEventListener('wzos:session',()=>{offset=0;show();});
})();
