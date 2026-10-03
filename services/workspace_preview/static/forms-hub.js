"use strict";
// Forms Hub: download/print library. Team forms are admin uploads; WZOS printables can be filled in on screen.
// Entries in WZOS printables are never sent to the server. The server enforces team-form access.
(() => {
 const $=id=>document.getElementById(id), api=(...args)=>window.wzosClock.api(...args);
 const node=(tag,value,cls)=>{const n=document.createElement(tag);if(value!=null)n.textContent=value;if(cls)n.className=cls;return n;};
 const button=(label,cls='secondary')=>{const b=node('button',label,cls);b.type='button';return b;};
 const labelled=(caption,control)=>{const l=node('label',caption);l.append(control);return l;};
 const option=(value,label)=>Object.assign(node('option',label),{value});
 const notice=value=>{$('forms-notice').textContent=value;};
 const session=()=>window.wzosClock.getSession();
 const headers=async()=>({'X-Preview-Actor':session()?.id||'',...await window.wzosAccount.headers()});
 const size=bytes=>bytes>=1048576?(bytes/1048576).toFixed(1)+' MB':Math.max(1,Math.round(bytes/1024))+' KB';
 const today=()=>new Date().toISOString().slice(0,10);
 const reduced=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
 // The server accepts simple filenames only; keep the user's name recognizable.
 const safeName=name=>(name.replace(/[^\w .()-]+/g,'-').replace(/^[.\s-]+/,'').slice(0,200))||'form.pdf';
 let templates=[], library=null, epoch=0, dirty=false, pending=null, busy=false;
 const fullTemplates=new Map();

 window.wzosFormsCanLeave=()=>!busy&&(!dirty||confirm('Your entries are not saved. Leave without printing or downloading this form?'));
 window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
 $('forms-nav').onclick=()=>window.showWzosView('forms');

 async function template(summary){
  const key=summary.id+'@'+summary.revision;
  if(!fullTemplates.has(key))fullTemplates.set(key,await api(`/api/forms/templates/${encodeURIComponent(summary.id)}/${summary.revision}`));
  return fullTemplates.get(key);
 }
 const matches=(...parts)=>parts.join(' ').toLowerCase().includes($('forms-search').value.trim().toLowerCase());

 // ---------- Team forms (admin uploads) ----------
 async function download(file,control){
  control.disabled=true;
  try{
   const response=await fetch('/api/files/'+file.id,{headers:await headers()});
   if(!response.ok)throw Error('Download unavailable. The form may have been removed or your access changed.');
   const url=URL.createObjectURL(await response.blob()),a=node('a');a.href=url;a.download=file.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
   notice(`Downloaded ${file.filename}.`);
  }catch(error){notice(error.message);}finally{control.disabled=false;}
 }
 async function upload(itemId,fileId,file){
  const response=await fetch(`/api/files/${fileId}?entity_kind=form_library&entity_id=${itemId}&filename=${encodeURIComponent(safeName(file.name))}`,
   {method:'PUT',headers:{...await headers(),'Content-Type':file.type||'application/octet-stream'},body:file});
  const data=await response.json();
  if(!response.ok){const error=Error(typeof data.detail==='string'?data.detail:'Upload failed');error.status=response.status;throw error;}
  return data;
 }
 const saveItem=(id,body)=>api(`/api/forms/library/${id}`,{method:'PUT',body:JSON.stringify(body)});
 function renderLibrary(){
  const host=$('forms-library');host.replaceChildren();
  if(!library)return;
  for(const item of library.items.filter(i=>matches(i.title,i.description,i.category_label,i.file?.filename||''))){
   const card=node('article',null,'forms-card');card.append(node('h3',item.title));
   const b=node('span',item.category_label,'forms-badge');b.dataset.category=item.category;card.append(b);
   if(item.description)card.append(node('p',item.description));
   card.append(node('p',item.file?`${item.file.filename} · ${size(item.file.size_bytes)} · added by ${item.added_by}`:'No file uploaded yet. Only admins can see this entry.','fine'));
   const actions=node('div',null,'forms-actions');
   if(item.file){const d=button('Download','primary');d.setAttribute('aria-label',`Download ${item.title}`);d.onclick=()=>download(item.file,d);actions.append(d);}
   if(library.can_manage)actions.append(...manageControls(item,card));
   card.append(actions);host.append(card);
  }
  if(!host.children.length)host.append(node('p',library.items.length?'No team forms match that search.':library.can_manage?'No team forms yet. Add the forms your crews need, such as an official agency form.':'Your admin has not added any team forms yet.'));
 }
 function manageControls(item,card){
  const controls=[];
  if(library.uploads_enabled){
   const picker=node('input');picker.type='file';picker.accept='.pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg';picker.hidden=true;picker.setAttribute('aria-label',`Choose a replacement file for ${item.title}`);
   const replace=button(item.file?'Replace file':'Upload file');replace.setAttribute('aria-label',`${item.file?'Replace file for':'Upload file for'} ${item.title}`);replace.onclick=()=>picker.click();
   picker.onchange=async()=>{const file=picker.files[0];if(!file)return;replace.disabled=true;
    try{const stored=await upload(item.id,crypto.randomUUID(),file);await saveItem(item.id,{expected_version:item.version,title:item.title,category:item.category,description:item.description,file_id:stored.id});notice(`${item.title} now uses ${stored.filename}.`);await loadLibrary();}
    catch(error){notice(error.message+(error.status?'':' Try again.'));}finally{replace.disabled=false;picker.value='';}};
   controls.push(replace,picker);
  }
  const edit=button('Edit details');edit.setAttribute('aria-label',`Edit details for ${item.title}`);edit.onclick=()=>editDetails(item,card,edit);
  const remove=button('Remove');remove.setAttribute('aria-label',`Remove ${item.title} from team forms`);
  remove.onclick=async()=>{if(!confirm(`Remove “${item.title}” from team forms? Your team will no longer be able to download it.`))return;remove.disabled=true;
   try{await api(`/api/forms/library/${item.id}/remove`,{method:'POST',body:JSON.stringify({expected_version:item.version})});notice(`${item.title} was removed from team forms.`);await loadLibrary();}
   catch(error){notice(error.message);remove.disabled=false;}};
  controls.push(edit,remove);return controls;
 }
 function detailFields(values={}){
  const title=node('input');title.maxLength=120;title.required=true;title.value=values.title||'';
  const category=node('select');category.append(option('official_agency_form','Official agency form'),option('company_form','Company form'));category.value=values.category||'official_agency_form';
  const description=node('textarea');description.rows=2;description.maxLength=500;description.value=values.description||'';description.placeholder='For example: VDOT pavement marking daily log. Check the agency for the current edition.';
  return {title,category,description,elements:[labelled('Form name',title),labelled('Type',category),labelled('Description (optional)',description)]};
 }
 function editDetails(item,card,opener){
  const form=node('form',null,'forms-inline');const fields=detailFields(item);const save=button('Save details','primary');save.type='submit';const cancel=button('Cancel');
  const error=node('p',null,'forms-error');error.setAttribute('role','alert');const actions=node('div',null,'forms-actions');actions.append(save,cancel);
  form.append(...fields.elements,error,actions);card.append(form);opener.disabled=true;fields.title.focus();
  cancel.onclick=()=>{form.remove();opener.disabled=false;opener.focus();};
  form.onsubmit=async event=>{event.preventDefault();if(!fields.title.value.trim()){error.textContent='Enter a form name.';fields.title.focus();return;}save.disabled=true;
   try{await saveItem(item.id,{expected_version:item.version,title:fields.title.value,category:fields.category.value,description:fields.description.value,file_id:item.file?.id||null});notice('Team form details saved.');await loadLibrary();}
   catch(error2){error.textContent=error2.message;save.disabled=false;}};
 }
 function renderAdmin(){
  const host=$('forms-library-admin');host.replaceChildren();
  if(!library?.can_manage)return;
  const details=node('details',null,'forms-add');details.append(node('summary','Add a team form'));host.append(details);
  if(!library.uploads_enabled){details.append(node('p','File storage is not configured in this environment, so forms cannot be uploaded here.','fine'));return;}
  const form=node('form');const fields=detailFields();const file=node('input');file.type='file';file.accept='.pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg';file.required=true;
  const error=node('p',null,'forms-error');error.setAttribute('role','alert');const add=button('Add to team forms','primary');add.type='submit';
  form.append(...fields.elements,labelled('File (PDF, PNG or JPEG, up to 10 MB)',file),node('p','For an official agency form, upload the current copy from the agency. WZOS does not check editions or decide whether a form applies.','fine'),error,add);
  details.append(form);
  // Retrying after a failure reuses the same identifiers, so nothing is duplicated.
  const reset=()=>{pending=null;};file.onchange=reset;for(const f of [fields.title,fields.category,fields.description])f.addEventListener('input',reset);
  form.onsubmit=async event=>{
   event.preventDefault();error.textContent='';const chosen=file.files[0];
   if(!fields.title.value.trim()){error.textContent='Enter a form name.';fields.title.focus();return;}
   if(!chosen){error.textContent='Choose the file to upload.';file.focus();return;}
   if(chosen.size>10*1024*1024){error.textContent='The file is larger than 10 MB.';return;}
   pending=pending||{itemId:crypto.randomUUID(),fileId:crypto.randomUUID()};
   const meta={title:fields.title.value,category:fields.category.value,description:fields.description.value};
   add.disabled=true;busy=true;
   try{
    await saveItem(pending.itemId,{expected_version:0,...meta,file_id:null});
    const stored=await upload(pending.itemId,pending.fileId,chosen);
    await saveItem(pending.itemId,{expected_version:1,...meta,file_id:stored.id});
    pending=null;form.reset();notice(`${meta.title} was added to team forms. Everyone in your organization can download it.`);await loadLibrary();
   }catch(failure){error.textContent=failure.status?failure.message:'Upload not confirmed. Check the connection and select Add again; it will not create a duplicate.';}
   finally{add.disabled=false;busy=false;}
  };
 }
 async function loadLibrary(){
  const generation=epoch;
  try{const data=await api('/api/forms/library');if(generation!==epoch)return;library=data;renderAdmin();renderLibrary();}
  catch(error){if(generation===epoch)notice(error.message);}
 }

 // ---------- WZOS printable forms ----------
 function renderBuiltins(){
  const host=$('forms-builtin');host.replaceChildren();
  for(const t of templates.filter(t=>matches(t.title,t.summary))){
   const card=node('article',null,'forms-card');card.append(node('h3',t.title));
   const b=node('span','WZOS printable form','forms-badge');b.dataset.category='wzos_printable';card.append(b,node('p',t.summary));
   const actions=node('div',null,'forms-actions');
   const fill=button('Fill in','primary');fill.setAttribute('aria-label',`Fill in ${t.title}`);fill.onclick=()=>{if(window.wzosFormsCanLeave())openForm(t,fill);};
   const print=button('Print blank');print.setAttribute('aria-label',`Print blank ${t.title}`);print.onclick=async()=>printDocument(await template(t),null);
   const save=button('Download blank');save.setAttribute('aria-label',`Download blank ${t.title}`);save.onclick=async()=>downloadDocument(await template(t),null);
   actions.append(fill,print,save);card.append(actions);host.append(card);
  }
  if(!host.children.length)host.append(node('p','No WZOS forms match that search.'));
 }
 function control(field){
  const id='forms-field-'+field.key;let input;
  if(field.type==='textarea'){input=node('textarea');input.rows=3;input.maxLength=field.max_length||4000;}
  else if(field.type==='select'){input=node('select');input.append(option('','—'),...field.options.map(o=>option(o,o)));}
  else if(field.type==='multiselect'){
   const set=node('fieldset',null,'forms-choices');set.id=id;set.append(node('legend',field.label));
   for(const o of field.options){const box=node('input');box.type='checkbox';box.value=o;const l=node('label',null,'forms-choice');l.append(box,node('span',o));set.append(l);}
   return {element:set,read:()=>[...set.querySelectorAll('input:checked')].map(b=>b.value),clear:()=>set.querySelectorAll('input').forEach(b=>{b.checked=false;})};
  }
  else if(field.type==='rows'){
   const set=node('fieldset',null,'forms-rows');set.id=id;set.append(node('legend',`${field.label} · up to ${field.max_rows} rows`));
   const body=node('div');set.append(body);const add=button('Add row');
   const addRow=()=>{const row=node('div',null,'forms-row'),n=body.children.length+1;for(const c of field.columns){const i=node('input');i.maxLength=c.max_length||200;i.dataset.key=c.key;i.setAttribute('aria-label',`${field.label} row ${n}: ${c.label}`);row.append(labelled(c.label,i));}
    const remove=button('Remove row');remove.setAttribute('aria-label',`Remove ${field.label} row ${n}`);remove.onclick=()=>{row.remove();add.disabled=false;add.focus();};row.append(remove);body.append(row);add.disabled=body.children.length>=field.max_rows;return row;};
   add.onclick=()=>addRow().querySelector('input').focus();addRow();set.append(add);
   return {element:set,read:()=>[...body.children].map(r=>Object.fromEntries([...r.querySelectorAll('input')].map(i=>[i.dataset.key,i.value.trim()]))).filter(r=>Object.values(r).some(Boolean)),
    clear:()=>{body.replaceChildren();addRow();}};
  }
  else{input=node('input');input.type={date:'date',time:'time',number:'number'}[field.type]||'text';if(field.type==='number'){input.min=field.min??'';input.max=field.max??'';input.step='any';}else if(field.type==='text')input.maxLength=field.max_length||200;}
  input.id=id;
  return {element:labelled(field.label,input),read:()=>input.value.trim(),clear:()=>{input.value='';}};
 }
 async function openForm(summary,opener){
  let t;try{t=await template(summary);}catch(error){notice(error.message);return;}
  const editor=$('forms-editor');editor.replaceChildren();editor.hidden=false;dirty=false;
  const heading=node('h2',t.title);heading.id='forms-editor-title';heading.tabIndex=-1;
  const b=node('span','WZOS printable form','forms-badge');b.dataset.category='wzos_printable';
  editor.append(heading,b,node('p','Your entries stay on this screen only. They are not saved, so print or download the form before you leave.','forms-notice-box'),node('p',t.print_notice,'fine'));
  const form=node('form');form.noValidate=true;form.id='forms-form';const inputs=new Map();
  const order=node('select');order.id='forms-order';order.append(option('','None'),...window.wzosClock.getOrders().map(o=>option(o.title,o.title)));
  const location=node('input');location.id='forms-location';location.maxLength=500;
  const common=node('fieldset');common.append(node('legend','Job'),labelled('Work order (optional)',order),labelled('Location',location));form.append(common);
  for(const section of t.sections){const set=node('fieldset');set.append(node('legend',section.title));for(const field of section.fields){const c=control(field);inputs.set(field.key,c);set.append(c.element);}form.append(set);}
  const actions=node('div',null,'forms-actions');
  const values=()=>({fields:Object.fromEntries([...inputs].map(([k,c])=>[k,c.read()])),order:order.value,location:location.value.trim()});
  const print=button('Print or save as PDF','primary');print.onclick=()=>printDocument(t,values());
  const save=button('Download filled form');save.onclick=()=>{downloadDocument(t,values());dirty=false;};
  const clear=button('Clear entries');clear.onclick=()=>{if(!confirm('Clear everything you entered on this form?'))return;for(const c of inputs.values())c.clear();order.value='';location.value='';dirty=false;heading.focus();};
  const close=button('Close');close.onclick=()=>{if(!window.wzosFormsCanLeave())return;dirty=false;editor.hidden=true;editor.replaceChildren();if(opener?.isConnected)opener.focus();};
  actions.append(print,save,clear,close);form.append(actions);editor.append(form);
  form.addEventListener('input',()=>{dirty=true;});form.onsubmit=event=>event.preventDefault();
  editor.scrollIntoView?.({behavior:reduced()?'auto':'smooth',block:'start'});heading.focus({preventScroll:true});
 }
 // A printable document built with DOM text nodes only, so entries can never become markup.
 function buildDocument(t,data){
  const doc=node('article',null,'wzos-form-doc'),line=value=>node('span',value||'',value?'value':'value blank');
  doc.append(node('p','WZOS powered by Atlas AI Assistant','brand'),node('h1',t.title),node('p',t.print_notice,'notice'));
  const job=node('div',null,'field-grid');for(const [label,value] of [['Work order',data?.order],['Location',data?.location],['Prepared',data?today():'']]){const f=node('div',null,'field');f.append(node('span',label,'label'),line(value));job.append(f);}doc.append(job);
  for(const section of t.sections){doc.append(node('h2',section.title));const grid=node('div',null,'field-grid');doc.append(grid);
   for(const field of section.fields){const v=data?.fields[field.key];
    if(field.type==='rows'){const table=node('table'),head=node('tr');table.append(node('caption',field.label));for(const c of field.columns)head.append(node('th',c.label));table.append(head);
     const rows=[...(v||[])];while(rows.length<field.max_rows)rows.push({});for(const r of rows){const tr=node('tr');for(const c of field.columns)tr.append(node('td',r[c.key]||''));table.append(tr);}doc.append(table);continue;}
    const f=node('div',null,field.type==='textarea'||field.type==='multiselect'||field.type==='select'?'field wide':'field');f.append(node('span',field.label,'label'));
    if(field.type==='select'||field.type==='multiselect'){const chosen=field.type==='select'?[v]:(v||[]);const list=node('div',null,'choices');for(const o of field.options)list.append(node('span',`${chosen.includes(o)?'☑':'☐'} ${o}`,'choice'));f.append(list);}
    else if(field.type==='textarea')f.append(node('div',v||'','box'));
    else f.append(line(v));
    grid.append(f);}
  }
  doc.append(node('p',`WZOS printable form · ${t.title} · template revision ${t.revision} · ${data?'filled on screen; not saved in WZOS':'blank'}`,'footer'));
  return doc;
 }
 function printDocument(t,data){
  const out=$('forms-print');out.replaceChildren(buildDocument(t,data));
  document.body.classList.add('forms-printing');
  const done=()=>{document.body.classList.remove('forms-printing');window.removeEventListener('afterprint',done);};window.addEventListener('afterprint',done);
  window.print();
 }
 const DOC_CSS='body{margin:24px;font:11pt/1.45 "Segoe UI",Arial,sans-serif;color:#000;background:#fff}.brand,.footer{font-size:9pt;color:#444}h1{font-size:17pt;margin:4px 0}h2{font-size:12pt;border-bottom:1px solid #888;margin:18px 0 6px}.notice{border:1.5px solid #000;padding:6px 8px;font-weight:600}.field-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:6px 18px}.field.wide{grid-column:1/-1}.label{display:block;font-weight:600;font-size:9.5pt}.value{display:block;min-height:1.4em;border-bottom:1px solid #666}.box{min-height:4.5em;border:1px solid #666;padding:4px;white-space:pre-wrap}.choices{display:flex;flex-wrap:wrap;gap:2px 14px}table{width:100%;border-collapse:collapse;margin:10px 0;font-size:9.5pt}caption{text-align:left;font-weight:600;padding-bottom:3px}th,td{border:1px solid #666;padding:4px 6px;height:1.4em;text-align:left}@media print{body{margin:0}}';
 function downloadDocument(t,data){
  const title=node('title',`${t.title}${data?'':' (blank)'}`);
  const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${title.outerHTML}<style>${DOC_CSS}</style></head><body>${buildDocument(t,data).outerHTML}</body></html>`;
  const url=URL.createObjectURL(new Blob([html],{type:'text/html'})),a=node('a');a.href=url;a.download=`wzos-${t.id}-${data?'filled':'blank'}-${today()}.html`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  notice(`Downloaded ${t.title}${data?' with your entries':' (blank)'}. Open the file in any browser to print it or save it as a PDF.`);
 }

 async function show(){
  const generation=++epoch;notice('');
  try{const catalog=await api('/api/forms/templates');if(generation!==epoch)return;templates=catalog.items;renderBuiltins();}catch(error){notice(error.message);}
  await loadLibrary();
 }
 $('forms-search').oninput=()=>{renderBuiltins();renderLibrary();};
 $('forms-refresh').onclick=()=>show();
 document.addEventListener('wzos:view',event=>{if(event.detail==='forms')show();});
 document.addEventListener('wzos:session',()=>{epoch++;dirty=false;pending=null;library=null;$('forms-editor').hidden=true;$('forms-editor').replaceChildren();$('forms-library').replaceChildren();$('forms-library-admin').replaceChildren();if(!$('forms-view').hidden)show();});
})();
