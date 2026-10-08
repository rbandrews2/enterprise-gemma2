"use strict";
// Forms Hub: download/print library. Team forms are admin uploads (files or Google links); WZOS printables can be filled in on screen.
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
 let templates=[], library=null, epoch=0, dirty=false, pending=null, busy=false, transfer=null, cleaning=false;
 const fullTemplates=new Map();

 const canDiscard=()=>!dirty||confirm('Your entries are not saved. Leave without printing or downloading this form?');
 window.wzosFormsCanLeave=()=>busy?confirm('A team form is still uploading. Leave and cancel the upload?')&&(transfer?.abort(),true):canDiscard();
 window.addEventListener('beforeunload',event=>{if(dirty||busy){event.preventDefault();event.returnValue='';}});
 $('forms-nav').onclick=()=>window.showWzosView('forms');

 async function template(summary){
  const key=summary.id+'@'+summary.revision;
  if(!fullTemplates.has(key))fullTemplates.set(key,await api(`/api/forms/templates/${encodeURIComponent(summary.id)}/${summary.revision}`));
  return fullTemplates.get(key);
 }
 const matches=(...parts)=>parts.join(' ').toLowerCase().includes($('forms-search').value.trim().toLowerCase());

 // ---------- Team forms (admin uploads and Google links) ----------
 const FILE_TYPES={pdf:'application/pdf',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg',
  docx:'application/vnd.openxmlformats-officedocument.wordprocessingml.document',xlsx:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'};
 const KIND_NAMES={'application/pdf':'PDF','image/png':'PNG image','image/jpeg':'JPEG image',[FILE_TYPES.docx]:'Word document',[FILE_TYPES.xlsx]:'Excel workbook'};
 const ACCEPT='.pdf,.png,.jpg,.jpeg,.docx,.xlsx',MAX_BYTES=10*1024*1024;
 const GROUPS=[['official_agency_form','Official agency forms'],['company_form','Company forms']];
 const GOOGLE=/^https:\/\/(docs\.google\.com\/(document|spreadsheets|forms)\/d\/|drive\.google\.com\/file\/d\/)/i;
 const typeOf=file=>FILE_TYPES[(file.name.split('.').pop()||'').toLowerCase()];
 // Check a file before anything is sent, so a bad file never creates an entry.
 function checkFile(file){
  if(!file)return 'Choose the file to upload.';
  const ext=(file.name.split('.').pop()||'').toLowerCase();
  if(ext==='doc'||ext==='xls'||ext==='docm'||ext==='xlsm')return `${file.name} is an older or macro-enabled Office format. Save it as a Word (.docx) or Excel (.xlsx) file first, then upload that copy.`;
  if(!typeOf(file))return `${file.name} isn't a supported type. Use PDF, PNG, JPEG, Word (.docx) or Excel (.xlsx).`;
  if(!file.size)return `${file.name} is empty.`;
  if(file.size>MAX_BYTES)return `${file.name} is ${size(file.size)}. The limit is 10 MB.`;
  return '';
 }
 const checkLink=value=>!value?'Paste the Google link.':GOOGLE.test(value)?'':'Use a link to a Google Doc, Sheet, Form or Drive file (it starts with https://docs.google.com/ or https://drive.google.com/).';
 // Network drops, timeouts and temporary server errors can be retried with the same identifiers.
 const retryable=error=>[0,408,429,502,503,504].includes(error.status||0);
 const sentence=text=>/[.!?]$/.test(text)?text:text+'.';
 async function download(file,control){
  control.disabled=true;
  try{
   const response=await fetch('/api/files/'+file.id,{headers:await headers()});
   if(!response.ok)throw Error('Download unavailable. The form may have been deleted or your access changed.');
   const url=URL.createObjectURL(await response.blob()),a=node('a');a.href=url;a.download=file.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
   notice(`Downloaded ${file.filename}.`);
  }catch(error){notice(error.message);}finally{control.disabled=false;}
 }
 // XMLHttpRequest instead of fetch so the admin sees upload progress and can cancel.
 async function upload(itemId,fileId,file,progress){
  const auth=await headers();
  return new Promise((resolve,reject)=>{
   const xhr=new XMLHttpRequest();transfer=xhr;
   const fail=(message,status=0)=>{transfer=null;const error=Error(message);error.status=status;error.upload=true;reject(error);};
   xhr.open('PUT',`/api/files/${fileId}?entity_kind=form_library&entity_id=${itemId}&filename=${encodeURIComponent(safeName(file.name))}`);
   for(const [k,v] of Object.entries(auth))xhr.setRequestHeader(k,v);
   xhr.setRequestHeader('Content-Type',typeOf(file));xhr.timeout=180000;
   xhr.upload.onprogress=event=>{if(event.lengthComputable)progress?.(event.loaded/event.total);};
   xhr.onload=()=>{let data={};try{data=JSON.parse(xhr.responseText);}catch{}
    if(xhr.status>=200&&xhr.status<300){transfer=null;resolve(data);}else fail(typeof data.detail==='string'?data.detail:'The upload was refused.',xhr.status);};
   xhr.onerror=()=>fail('The connection dropped during the upload.');
   xhr.ontimeout=()=>fail('The upload timed out.');
   xhr.onabort=()=>fail('Upload canceled.');
   xhr.send(file);
  });
 }
 async function uploadWithRetry(itemId,fileId,file,progress,status){
  try{return await upload(itemId,fileId,file,progress);}
  catch(error){
   if(!retryable(error)||error.message==='Upload canceled.')throw error;
   status('Connection problem. Retrying the upload…');await new Promise(r=>setTimeout(r,1500));
   return upload(itemId,fileId,file,progress);  // same file ID: the server never stores it twice
  }
 }
 const saveItem=(id,body)=>api(`/api/forms/library/${id}`,{method:'PUT',body:JSON.stringify(body)});
 async function deleteItem(id,version){
  // The form is hidden as soon as this succeeds; cleanup_pending means stored files are still being erased.
  try{return await api(`/api/forms/library/${id}/delete`,{method:'POST',body:JSON.stringify({expected_version:version})});}
  catch(error){if(error.status!==404)throw error;return {deleted:true,cleanup_pending:false};}  // 404: already deleted
 }
 function progressBar(){
  const wrap=node('div',null,'forms-progress');wrap.hidden=true;
  const bar=node('progress');bar.max=1;bar.value=0;const text=node('span',null,'fine');text.setAttribute('role','status');text.setAttribute('aria-live','polite');
  wrap.append(bar,text);
  return {element:wrap,
   set:(fraction,label)=>{wrap.hidden=false;bar.value=fraction;bar.setAttribute('aria-label',label);text.textContent=fraction>=1?'Upload received. Finishing…':`${label} ${Math.round(fraction*100)}%`;},
   status:value=>{wrap.hidden=false;text.textContent=value;},
   hide:()=>{wrap.hidden=true;text.textContent='';bar.value=0;}};
 }
 function sourceLine(item){
  if(item.file)return `${KIND_NAMES[item.file.content_type]||'File'} · ${item.file.filename} · ${size(item.file.size_bytes)} · added by ${item.added_by}`;
  if(item.link)return `${item.link.service} link · added by ${item.added_by}. Google's sharing settings decide who can open it.`;
  return 'The upload didn\'t finish, so this entry has no file. Only admins can see it. Upload the file again or delete the entry.';
 }
 function card(item){
  const article=node('article',null,'forms-card');article.append(node('h4',item.title));
  const b=node('span',item.category_label,'forms-badge');b.dataset.category=item.category;article.append(b);
  if(!item.complete){const warn=node('span','Upload incomplete','forms-badge');warn.dataset.category='incomplete';article.append(' ',warn);}
  if(item.description)article.append(node('p',item.description));
  article.append(node('p',sourceLine(item),'fine'));
  const actions=node('div',null,'forms-actions');
  if(item.file){const d=button('Download','primary');d.setAttribute('aria-label',`Download ${item.title}`);d.onclick=()=>download(item.file,d);actions.append(d);}
  if(item.link){
   const open=node('a',`Open in ${item.link.service}`,'button primary');open.href=item.link.url;open.target='_blank';open.rel='noopener noreferrer';open.setAttribute('aria-label',`Open ${item.title} in ${item.link.service} (new tab)`);actions.append(open);
   for(const d of item.link.downloads){const a=node('a',`Download ${d.label}`,'button secondary');a.href=d.url;a.target='_blank';a.rel='noopener noreferrer';a.setAttribute('aria-label',`Download ${item.title} as ${d.label} from Google (new tab)`);actions.append(a);}
  }
  if(library.can_manage)actions.append(...manageControls(item,article));
  article.append(actions);return article;
 }
 function renderLibrary(){
  const host=$('forms-library');host.replaceChildren();
  if(!library)return;
  const shown=library.items.filter(i=>matches(i.title,i.description,i.category_label,i.file?.filename||'',i.link?.service||''));
  const unfinished=shown.filter(i=>!i.complete);
  if(unfinished.length){
   const group=node('section',null,'forms-group forms-unfinished');
   group.append(node('h3',unfinished.length===1?'1 form didn\'t finish uploading':`${unfinished.length} forms didn't finish uploading`),node('p','Only admins see these entries. Upload the file again, or delete the entry.','fine'),...unfinished.map(card));
   host.append(group);
  }
  for(const [category,heading] of GROUPS){
   const items=shown.filter(i=>i.complete&&i.category===category);if(!items.length)continue;
   const group=node('section',null,'forms-group');group.append(node('h3',`${heading} (${items.length})`),...items.map(card));host.append(group);
  }
  if(!host.children.length)host.append(node('p',library.items.length?'No team forms match that search.':library.can_manage?'No team forms yet. Add the forms your crews need, such as official agency forms or company forms.':'Your admin hasn\'t added any team forms yet.'));
 }
 function manageControls(item,article){
  const controls=[];
  if(library.uploads_enabled&&!item.link){
   const picker=node('input');picker.type='file';picker.accept=ACCEPT;picker.hidden=true;
   const replace=button(item.file?'Replace file':'Upload file',item.complete?'secondary':'primary');replace.setAttribute('aria-label',`${item.file?'Replace file for':'Upload file for'} ${item.title}`);replace.onclick=()=>picker.click();
   const bar=progressBar();article.append(bar.element);
   picker.onchange=async()=>{
    const file=picker.files[0];picker.value='';if(!file)return;
    const problem=checkFile(file);if(problem){notice(problem);return;}
    replace.disabled=true;busy=true;
    try{
     const stored=await uploadWithRetry(item.id,crypto.randomUUID(),file,f=>bar.set(f,`Uploading ${file.name}`),bar.status);
     bar.status('Saving…');
     const saved=await saveItem(item.id,{expected_version:item.version,title:item.title,category:item.category,description:item.description,file_id:stored.id,link:null});
     bar.hide();await loadLibrary();
     notice(`${item.title} now uses ${stored.filename}.${!item.file?'':saved.cleanup_pending?' The previous file is no longer available and will be erased shortly.':' The previous file was erased.'}`);
    }catch(error){bar.hide();notice(`${file.name} wasn't uploaded: ${sentence(error.message)}${retryable(error)?' Nothing changed; choose the file again to retry.':''}`);}
    finally{replace.disabled=false;busy=false;}
   };
   controls.push(replace,picker);
  }
  const edit=button('Edit details');edit.setAttribute('aria-label',`Edit details for ${item.title}`);edit.onclick=()=>editDetails(item,article,edit);
  const remove=button('Delete','secondary forms-danger');remove.setAttribute('aria-label',`Delete ${item.title} permanently`);
  remove.onclick=async()=>{
   const what=item.file?' Its file will be erased from WZOS.':'';
   if(!confirm(`Permanently delete “${item.title}”?${what} Your team will no longer see it. This can't be undone.`))return;
   remove.disabled=true;
   try{const result=await deleteItem(item.id,item.version);await loadLibrary();
    notice(result.cleanup_pending?`${item.title} was deleted and your team can no longer open it. Its stored file couldn't be erased yet; WZOS will keep retrying.`:`${item.title} was permanently deleted.`);}
   catch(error){notice(error.message);remove.disabled=false;}
  };
  controls.push(edit,remove);return controls;
 }
 function detailFields(values={}){
  const title=node('input');title.maxLength=120;title.required=true;title.value=values.title||'';
  const category=node('select');category.append(option('official_agency_form','Official agency form'),option('company_form','Company form'));category.value=values.category||'official_agency_form';
  const description=node('textarea');description.rows=2;description.maxLength=500;description.value=values.description||'';description.placeholder='For example: VDOT pavement marking daily log. Check the agency for the current edition.';
  return {title,category,description,elements:[labelled('Form name',title),labelled('Type',category),labelled('Description (optional)',description)]};
 }
 const linkInput=value=>{const input=node('input');input.type='url';input.maxLength=500;input.placeholder='https://docs.google.com/…';input.value=value||'';input.autocomplete='off';return input;};
 function editDetails(item,article,opener){
  const form=node('form',null,'forms-inline');const fields=detailFields(item);const save=button('Save details','primary');save.type='submit';const cancel=button('Cancel');
  // A Google-link entry (or an unfinished one) can have its link set here; files are replaced with Replace file.
  const link=!item.file?linkInput(item.link?.url):null;
  const error=node('p',null,'forms-error');error.setAttribute('role','alert');const actions=node('div',null,'forms-actions');actions.append(save,cancel);
  form.append(...fields.elements,...(link?[labelled('Google link',link)]:[]),error,actions);article.append(form);opener.disabled=true;fields.title.focus();
  cancel.onclick=()=>{form.remove();opener.disabled=false;opener.focus();};
  form.onsubmit=async event=>{event.preventDefault();error.textContent='';
   if(!fields.title.value.trim()){error.textContent='Enter a form name.';fields.title.focus();return;}
   const url=link?.value.trim()||null;
   if(link&&(item.link||url)){const problem=checkLink(url);if(problem){error.textContent=problem;link.focus();return;}}
   save.disabled=true;
   try{await saveItem(item.id,{expected_version:item.version,title:fields.title.value,category:fields.category.value,description:fields.description.value,file_id:item.file?.id||null,link:url});await loadLibrary();notice('Team form details saved.');}
   catch(error2){error.textContent=error2.message;save.disabled=false;}};
 }
 function renderAdmin(){
  const host=$('forms-library-admin');host.replaceChildren();
  if(!library?.can_manage)return;
  const details=node('details',null,'forms-add');details.append(node('summary','Add a team form'));host.append(details);
  const form=node('form');const fields=detailFields();
  const source=node('fieldset',null,'forms-source');source.append(node('legend','How do you want to add it?'));
  const radio=(value,label,checked)=>{const r=node('input');r.type='radio';r.name='forms-source';r.value=value;r.checked=r.defaultChecked=checked;const l=node('label',null,'forms-choice');l.append(r,node('span',label));source.append(l);return r;};
  const viaFile=radio('file','Upload a file (PDF, PNG, JPEG, Word or Excel, up to 10 MB)',library.uploads_enabled);
  const viaLink=radio('link','Link a Google Doc, Sheet, Form or Drive file',!library.uploads_enabled);
  if(!library.uploads_enabled){viaFile.disabled=true;source.append(node('p','File storage isn\'t configured in this environment, so only Google links can be added here.','fine'));}
  const file=node('input');file.type='file';file.accept=ACCEPT;const fileLabel=labelled('File',file);
  const link=linkInput();const linkLabel=labelled('Google link',link);
  const linkHelp=node('p','Share the Google file with your team in Google first. WZOS links to it but can\'t change who can open it.','fine');
  const fileHelp=node('p','For an official agency form, upload the current copy from the agency. WZOS doesn\'t check editions or decide whether a form applies. Save older .doc or .xls files as .docx or .xlsx first.','fine');
  const bar=progressBar();
  const error=node('p',null,'forms-error');error.setAttribute('role','alert');
  const add=button('Add to team forms','primary');add.type='submit';
  const cancel=button('Cancel upload');cancel.hidden=true;cancel.onclick=()=>transfer?.abort();
  const discard=button('Discard');discard.hidden=true;
  const actions=node('div',null,'forms-actions');actions.append(add,cancel,discard);
  form.append(...fields.elements,source,fileLabel,fileHelp,linkLabel,linkHelp,bar.element,error,actions);
  details.append(form);
  const sync=()=>{const isFile=viaFile.checked;fileLabel.hidden=fileHelp.hidden=!isFile;linkLabel.hidden=linkHelp.hidden=isFile;};
  viaFile.onchange=viaLink.onchange=sync;sync();
  if(pending){details.open=true;restore();}
  // Show early what's wrong with a chosen file.
  file.onchange=()=>{error.textContent=checkFile(file.files[0]);};
  function restore(){
   // Re-rendering (for example after Refresh) keeps an unfinished add so it can be retried.
   Object.assign(fields.title,{value:pending.meta.title});fields.category.value=pending.meta.category;fields.description.value=pending.meta.description;
   if(pending.link){viaLink.checked=true;link.value=pending.link;}sync();
   error.textContent=pending.message||'';
   add.textContent=pending.file?'Retry upload':'Retry';discard.hidden=false;
  }
  function settle(){pending=null;form.reset();sync();bar.hide();add.textContent='Add to team forms';discard.hidden=true;}
  discard.onclick=async()=>{
   discard.disabled=true;
   try{if(pending?.version)await deleteItem(pending.itemId,pending.version);settle();error.textContent='';await loadLibrary();notice('The unfinished form was discarded.');}
   catch(failure){error.textContent=`Couldn't discard it yet: ${failure.message}`;}
   finally{discard.disabled=false;}
  };
  form.onsubmit=async event=>{const generation=epoch;
   event.preventDefault();error.textContent='';
   const meta={title:fields.title.value.trim(),category:fields.category.value,description:fields.description.value.trim()};
   if(!meta.title){error.textContent='Enter a form name.';fields.title.focus();return;}
   const chosen=viaFile.checked?file.files[0]||pending?.file:null,url=viaLink.checked?link.value.trim():null;
   const problem=viaFile.checked?checkFile(chosen):checkLink(url);
   if(problem){error.textContent=problem;(viaFile.checked?file:link).focus();return;}
   // A retry reuses the entry and file identifiers, so nothing is duplicated.
   if(!pending)pending={itemId:crypto.randomUUID(),version:0};
   if(chosen&&pending.file!==chosen){pending.file=chosen;pending.fileId=crypto.randomUUID();}
   Object.assign(pending,{meta,link:url,file:chosen});
   add.disabled=discard.disabled=true;cancel.hidden=!chosen;busy=true;
   try{
    if(!pending.version){
     bar.status('Creating the entry…');
     try{pending.version=(await saveItem(pending.itemId,{expected_version:0,...meta,file_id:null,link:url})).version;pending.saved=!chosen;}
     catch(failure){if(failure.status!==409)throw failure;pending.version=(await api('/api/forms/library')).items.find(i=>i.id===pending.itemId)?.version||0;if(!pending.version)throw failure;}
    }
    if(chosen){
     const stored=await uploadWithRetry(pending.itemId,pending.fileId,chosen,f=>bar.set(f,`Uploading ${chosen.name}`),bar.status);
     bar.status('Saving…');
     await saveItem(pending.itemId,{expected_version:pending.version,...meta,file_id:stored.id,link:null});
    }else if(!pending.saved){
     await saveItem(pending.itemId,{expected_version:pending.version,...meta,file_id:null,link:url});
    }
    settle();await loadLibrary();notice(`${meta.title} was added to team forms. Everyone in your organization can ${chosen?'download':'open'} it.`);
   }catch(failure){if(generation!==epoch)return;  // identity changed mid-upload
    bar.hide();
    if(failure.upload&&!retryable(failure)&&pending.version){
     // The server refused the file itself: remove the empty entry so nothing is left behind.
     try{await deleteItem(pending.itemId,pending.version);settle();error.textContent=`${chosen.name} wasn't added: ${sentence(failure.message)} Nothing was saved. Choose a different file and try again.`;await loadLibrary();return;}
     catch{/* fall through: keep the retry/discard controls */}
    }
    const reason=sentence(failure.message||'The connection dropped.');
    pending.message=`${chosen?`The upload of ${chosen.name} didn't finish. `:''}${reason} ${failure.status&&!retryable(failure)?'':`Your details${chosen?' and file':''} are kept here. `}Select ${chosen?'Retry upload':'Retry'}, or Discard.`;
    error.textContent=pending.message;
    add.textContent=chosen?'Retry upload':'Retry';discard.hidden=false;
    if(pending.version)loadLibrary();
   }finally{add.disabled=discard.disabled=false;cancel.hidden=true;busy=false;}
  };
 }
 async function loadLibrary(){
  const generation=epoch;
  try{const data=await api('/api/forms/library');if(generation!==epoch)return;library=data;if(!busy)renderAdmin();renderLibrary();
   // Finish erasing files left by an interrupted delete or replacement (idempotent; harmless if it fails again).
   if(data.can_manage&&data.cleanup_pending&&!cleaning){cleaning=true;api('/api/forms/library/cleanup',{method:'POST'}).catch(()=>{}).finally(()=>{cleaning=false;});}}
  catch(error){if(generation===epoch)notice(error.message);}
 }

 // ---------- WZOS printable forms ----------
 function renderBuiltins(){
  const host=$('forms-builtin');host.replaceChildren();
  for(const t of templates.filter(t=>matches(t.title,t.summary))){
   const card=node('article',null,'forms-card');card.append(node('h3',t.title));
   const b=node('span','WZOS printable form','forms-badge');b.dataset.category='wzos_printable';card.append(b,node('p',t.summary));
   const actions=node('div',null,'forms-actions');
   const fill=button('Fill in','primary');fill.setAttribute('aria-label',`Fill in ${t.title}`);fill.onclick=()=>{if(canDiscard())openForm(t,fill);};
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
  const save=button('Download filled form');save.onclick=()=>downloadDocument(t,values());
  const clear=button('Clear entries');clear.onclick=()=>{if(!confirm('Clear everything you entered on this form?'))return;for(const c of inputs.values())c.clear();order.value='';location.value='';dirty=false;heading.focus();};
  const close=button('Close');close.onclick=()=>{if(!canDiscard())return;dirty=false;editor.hidden=true;editor.replaceChildren();if(opener?.isConnected)opener.focus();};
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
  notice(`Download requested for ${t.title}${data?' with your entries':' (blank)'}. Check your browser downloads before leaving. Open the file in any browser to print it or save it as a PDF.`);
 }

 async function show(){
  const generation=++epoch;notice('');
  try{const catalog=await api('/api/forms/templates');if(generation!==epoch)return;templates=catalog.items;renderBuiltins();}catch(error){notice(error.message);}
  await loadLibrary();
 }
 $('forms-search').oninput=()=>{renderBuiltins();renderLibrary();};
 $('forms-refresh').onclick=()=>show();
 document.addEventListener('wzos:view',event=>{if(event.detail==='forms')show();});
 document.addEventListener('wzos:session',()=>{epoch++;transfer?.abort();dirty=false;pending=null;library=null;$('forms-editor').hidden=true;$('forms-editor').replaceChildren();$('forms-library').replaceChildren();$('forms-library-admin').replaceChildren();if(!$('forms-view').hidden)show();});
})();
