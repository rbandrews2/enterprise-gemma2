"use strict";
// Forms Hub: template catalog, saved forms, editor, review status, print and JSON export. The server enforces access.
(() => {
 const $=id=>document.getElementById(id), api=(...args)=>window.wzosClock.api(...args);
 const node=(tag,value,cls)=>{const n=document.createElement(tag);if(value!=null)n.textContent=value;if(cls)n.className=cls;return n;};
 const button=(label,cls='secondary')=>{const b=node('button',label,cls);b.type='button';return b;};
 const labelled=(caption,control,required)=>{const l=node('label',caption);if(required){l.append(node('span',' (required)','forms-required'));control.setAttribute('aria-required','true');}l.append(control);return l;};
 const CATEGORY={internal_worksheet:'Internal WZOS worksheet',official_form_reference:'Official form reference',legacy:'Legacy draft'};
 const STATUS={draft:'Draft',ready_for_review:'Ready for review',returned:'Returned for changes',reviewed:'Reviewed (internal)',cancelled:'Cancelled'};
 const badge=(category)=>{const b=node('span',CATEGORY[category]||category,'forms-badge');b.dataset.category=category;return b;};
 const chip=status=>{const c=node('span',STATUS[status]||status,'forms-status');c.dataset.status=status;return c;};
 const notice=value=>{$('forms-notice').textContent=value;};
 const session=()=>window.wzosClock.getSession();
 const people={};
 let templates=[], fullTemplates=new Map(), offset=0, epoch=0, current=null, dirty=false, saving=false, inputs=new Map();

 window.wzosFormsCanLeave=()=>!saving&&(!dirty||confirm('Leave this form without saving your changes?'));
 window.addEventListener('beforeunload',event=>{if(dirty||saving){event.preventDefault();event.returnValue='';}});
 $('forms-nav').onclick=()=>window.showWzosView('forms');

 async function template(id,revision){
  const key=id+'@'+revision;if(!fullTemplates.has(key))fullTemplates.set(key,await api(`/api/forms/templates/${encodeURIComponent(id)}/${revision}`));return fullTemplates.get(key);
 }
 function renderTemplates(){
  const query=$('forms-template-search').value.trim().toLowerCase();const host=$('forms-templates');host.replaceChildren();
  for(const t of templates.filter(t=>`${t.title} ${t.summary} ${CATEGORY[t.category]}`.toLowerCase().includes(query))){
   const card=node('article',null,'forms-template');const title=node('h3',t.title);
   card.append(title,badge(t.category),node('p',t.summary));
   if(t.official_reference){const ref=t.official_reference;card.append(node('p',`${ref.authority} · ${ref.form_identifier}. The official form is not stored here. Source review: ${ref.source.review_status}. Applicability: not determined.`,'forms-official-note'));}
   card.append(node('p',`Template revision ${t.revision}`,'fine'));
   const start=button('Start form','primary');start.setAttribute('aria-label',`Start ${t.title}`);start.onclick=()=>{if(window.wzosFormsCanLeave())openNew(t,start);};
   card.append(start);host.append(card);
  }
  if(!host.children.length)host.append(node('p','No templates match that search.'));
 }
 function orderOptions(select,value,emptyLabel){
  select.replaceChildren(Object.assign(node('option',emptyLabel),{value:''}));
  for(const order of window.wzosClock.getOrders())select.append(Object.assign(node('option',order.title),{value:order.id}));
  if(value&&![...select.options].some(o=>o.value===value))select.append(Object.assign(node('option','Linked work order (not in your list)'),{value}));
  select.value=value||'';
 }
 async function refreshList(){
  const generation=++epoch;const params=new URLSearchParams({offset:String(offset)});
  for(const [key,id] of [['q','forms-search'],['status','forms-status'],['category','forms-category'],['order_id','forms-order']])if($(id).value)params.set(key,$(id).value);
  try{
   const data=await api('/api/forms?'+params);if(generation!==epoch)return;
   const list=$('forms-list');list.replaceChildren();
   for(const item of data.items){
    const open=button('','forms-record');open.setAttribute('aria-label',`Open ${item.title}, ${STATUS[item.status]||item.status}`);
    const line=node('span',null,'forms-record-line');line.append(node('strong',item.title),chip(item.status));
    const meta=`${item.template?item.template.title+' · rev '+item.template.revision:'Legacy '+(item.legacy_type||'draft')} · revision ${item.version}${session()?.role==='admin'?' · '+item.owner_name:''} · ${new Date(item.updated_at).toLocaleString()}`;
    open.append(line,badge(item.template?item.template.category:'legacy'),node('span',meta,'forms-record-meta'));
    if(item.missing_count)open.append(node('span',`${item.missing_count} required item${item.missing_count===1?'':'s'} missing`,'forms-missing-count'));
    open.onclick=()=>{if(window.wzosFormsCanLeave())openRecord(item.id,open);};list.append(open);
   }
   if(!data.items.length)list.append(node('p','No saved forms match these filters.'));
   $('forms-page').textContent=`${data.total} form${data.total===1?'':'s'} · showing ${data.items.length?offset+1:0}–${offset+data.items.length}`;
   $('forms-prev').disabled=offset===0;$('forms-next').disabled=offset+data.limit>=data.total;
  }catch(error){if(generation===epoch)notice(error.message);}
 }
 async function show(){
  notice('');closeEditor(false);orderOptions($('forms-order'),$('forms-order').value,'Any work order');
  try{
   const [catalog,roster]=await Promise.all([api('/api/forms/templates'),api('/api/modules/roster')]);
   templates=catalog.items;for(const member of roster.items)people[member.id]=member.name;renderTemplates();
  }catch(error){notice(error.message);}
  await refreshList();
 }
 function closeEditor(focus=true){
  const opener=current?.opener;current=null;dirty=false;inputs=new Map();$('forms-editor').hidden=true;$('forms-editor').replaceChildren();$('forms-attachments').replaceChildren();
  if(focus&&opener?.isConnected)opener.focus();
 }
 async function openNew(summary,opener){
  try{const full=await template(summary.id,summary.revision);current={record:null,template:full,opener,id:crypto.randomUUID(),version:0};render();}
  catch(error){notice(error.message);}
 }
 async function openRecord(id,opener){
  try{const record=await api(`/api/forms/${id}`);const full=record.template?await template(record.template.id,record.template.revision):null;current={record,template:full,opener,id:record.id,version:record.version};render();}
  catch(error){notice(error.message);}
 }
 function fieldControl(field,value,disabled){
  const id=`forms-field-${field.key}`;let control;
  if(field.type==='textarea'){control=node('textarea');control.rows=3;control.maxLength=field.max_length||4000;control.value=value||'';}
  else if(field.type==='select'){control=node('select');if(!field.default)control.append(Object.assign(node('option','Choose…'),{value:''}));for(const o of field.options)control.append(Object.assign(node('option',o),{value:o}));control.value=value??field.default??'';}
  else if(field.type==='multiselect'){
   control=node('fieldset',null,'forms-choices');control.append(node('legend',field.label+(field.required?' (required)':'')));
   for(const o of field.options){const box=node('input');box.type='checkbox';box.value=o;box.checked=(value||[]).includes(o);box.disabled=disabled;const l=node('label',null,'forms-choice');l.append(box,node('span',o));control.append(l);}
   control.id=id;return {element:control,read:()=>[...control.querySelectorAll('input:checked')].map(b=>b.value),focus:()=>control.querySelector('input')?.focus()};
  }
  else if(field.type==='rows')return rowsControl(field,value||[],disabled);
  else{control=node('input');control.type={date:'date',time:'time',number:'number'}[field.type]||'text';if(field.type==='number'){control.min=field.min??'';control.max=field.max??'';control.step='any';}else if(field.type==='text')control.maxLength=field.max_length||200;control.value=value??'';}
  control.id=id;control.disabled=disabled;
  const read=()=>field.type==='number'?(control.value===''?null:Number(control.value)):control.value;
  return {element:labelled(field.label,control,field.required),read,focus:()=>control.focus()};
 }
 function rowsControl(field,rows,disabled){
  const set=node('fieldset',null,'forms-rows');set.id=`forms-field-${field.key}`;set.append(node('legend',`${field.label}${field.required?' (required)':''} · up to ${field.max_rows} rows`));
  const body=node('div',null,'forms-rows-body');set.append(body);
  const add=button('Add row');add.disabled=disabled;
  function addRow(values={}){
   const row=node('div',null,'forms-row');const index=body.children.length+1;
   for(const column of field.columns){const input=node('input');input.maxLength=column.max_length||200;input.value=values[column.key]||'';input.dataset.key=column.key;input.disabled=disabled;input.setAttribute('aria-label',`${field.label} row ${index}: ${column.label}`);row.append(labelled(column.label,input));}
   const remove=button('Remove row');remove.disabled=disabled;remove.setAttribute('aria-label',`Remove ${field.label} row ${index}`);remove.onclick=()=>{row.remove();dirty=true;sync();add.focus();};
   row.append(remove);body.append(row);sync();return row;
  }
  const sync=()=>{add.disabled=disabled||body.children.length>=field.max_rows;};
  add.onclick=()=>{addRow().querySelector('input').focus();dirty=true;};
  for(const values of rows)addRow(values);if(!rows.length&&!disabled)addRow();
  set.append(add);
  return {element:set,read:()=>[...body.children].map(row=>Object.fromEntries([...row.querySelectorAll('input')].map(i=>[i.dataset.key,i.value]))),focus:()=>(body.querySelector('input')||add).focus()};
 }
 function render(){
  const {record,template:t}=current, editor=$('forms-editor');editor.replaceChildren();editor.hidden=false;inputs=new Map();dirty=false;
  const can=record?.permissions||{can_edit:true};const disabled=!can.can_edit;
  const heading=node('h2',record?record.title:`New ${t?.title||'form'}`);heading.id='forms-editor-title';heading.tabIndex=-1;
  const meta=node('div',null,'forms-meta');meta.append(badge(t?t.category:'legacy'));if(record)meta.append(chip(record.status));
  meta.append(node('span',t?`${t.title} · template revision ${t.revision} · checksum ${t.checksum.slice(0,12)}`:`Legacy ${record.legacy_type||''} draft`,'fine'));
  if(record)meta.append(node('span',`Saved revision ${record.version} · ${new Date(record.updated_at).toLocaleString()}${record.owner_id!==session()?.id?' · owner '+record.owner_name:''}`,'fine'));
  editor.append(heading,meta);
  if(t)editor.append(node('p',t.print_notice,'forms-notice-box'));
  if(t?.official_reference){const ref=t.official_reference,box=node('div',null,'forms-official');
   box.append(node('h3','Official form reference'),node('p',`${ref.authority}: ${ref.form_identifier}, “${ref.official_title}”. WZOS does not store or reproduce the official form. Applicability to this project has not been determined.`),
    node('p',`Source: ${ref.source.title}, ${ref.source.section} (catalog ${ref.source.catalog_id}, content ${ref.source.content_sha256.slice(0,12)}…, review status: ${ref.source.review_status}).`),node('blockquote',ref.source.excerpt));editor.append(box);}
  if(record?.review?.note||record?.status==='returned'||record?.status==='reviewed'){const r=record.review||{};editor.append(node('p',`${STATUS[record.status]}${r.by?' by '+(people[r.by]||r.by):''}${r.at?' · '+new Date(r.at).toLocaleString():''}${r.note?' · '+r.note:''}`,'forms-review-note'));}
  if(record?.legacy){
   editor.append(node('p','This draft was created before Forms Hub templates. It is shown read-only and stays available to the Work Zone Report. Start a new form to continue on a current template.','forms-notice-box'));
   const legacy=record.legacy_record||{};if(legacy.details)editor.append(node('p',legacy.details));
   for(const group of [legacy.inspection,legacy.safety])if(group)for(const [k,v] of Object.entries(group))editor.append(node('p',`${k.replaceAll('_',' ')}: ${v??'Not recorded'}`));
  }
  const missing=node('div',null,'forms-missing');missing.id='forms-missing';missing.setAttribute('role','status');editor.append(missing);
  const form=node('form');form.noValidate=true;form.id='forms-form';
  if(!record?.legacy){
   const title=node('input');title.id='forms-record-title';title.maxLength=120;title.value=record?.title||t.title;title.disabled=disabled;
   const order=node('select');order.id='forms-record-order';orderOptions(order,record?.order_id,'No linked work order');order.disabled=disabled;
   const location=node('input');location.id='forms-record-location';location.maxLength=500;location.value=record?.location||'';location.disabled=disabled;
   const common=node('fieldset');common.append(node('legend','Form details'),labelled('Form title',title,true),labelled('Linked work order',order),labelled('Location',location));form.append(common);
   inputs.set('__title',{read:()=>title.value,focus:()=>title.focus()});inputs.set('__order',{read:()=>order.value||null});inputs.set('__location',{read:()=>location.value});
   for(const section of t.sections){const set=node('fieldset');set.append(node('legend',section.title));
    for(const field of section.fields){const control=fieldControl(field,record?.fields?.[field.key],disabled);inputs.set(field.key,control);set.append(control.element);}
    form.append(set);}
  }
  const error=node('p',null,'forms-error');error.id='forms-error';error.setAttribute('role','alert');
  const actions=node('div',null,'forms-actions');
  const add=(label,cls,handler,show=true)=>{if(!show)return null;const b=button(label,cls);b.onclick=handler;actions.append(b);return b;};
  const saveButton=add('Save draft','primary',()=>save(),!record?.legacy&&can.can_edit);
  const submitButton=add('Submit for review','secondary',()=>transition('submit'),!!record&&can.can_edit);
  const note=node('textarea');note.id='forms-review-input';note.rows=2;note.maxLength=1000;
  if(can.can_review){const l=labelled('Review note (required to return)',note);form.append(l);add('Mark reviewed','primary',()=>transition('mark_reviewed',note.value));add('Return for changes','secondary',()=>transition('return',note.value));}
  add('Reopen as draft','secondary',()=>transition('reopen'),!!can.can_reopen);
  add('Cancel form','secondary',()=>{if(confirm('Cancel this form? An admin can reopen it.'))transition('cancel');},!!record&&!!can.can_cancel);
  add('Print','secondary',()=>print(),!!record);
  add('Export JSON','secondary',()=>exportJson(),!!record);
  add('Close','secondary',()=>{if(window.wzosFormsCanLeave())closeEditor();});
  form.append(error,actions);editor.append(form);
  const history=node('details',null,'forms-history');history.append(node('summary','Revision history'));const historyBody=node('div');history.append(historyBody);
  if(record){history.ontoggle=async()=>{if(!history.open||historyBody.childElementCount)return;try{const data=await api(`/api/forms/${record.id}/history`);for(const h of data.items)historyBody.append(node('p',`Revision ${h.version} · ${new Date(h.saved_at).toLocaleString()} · ${h.author_name} · ${STATUS[h.status]||h.status}${h.review?.note&&h.status!=='draft'?' · note: '+h.review.note:''}${h.changed_fields.length?' · changed: '+h.changed_fields.join(', '):''}${h.title_changed?' · title changed':''}${h.template_revision?' · template rev '+h.template_revision:''}`));}catch(e){historyBody.append(node('p',e.message));}};editor.append(history);}
  const refreshMissing=list=>{missing.replaceChildren();if(!list?.length)return;missing.append(node('h3',`${list.length} required item${list.length===1?'':'s'} missing before submission`));const ul=node('ul');for(const m of list){const li=node('li');const jump=button(m.message,'forms-link');jump.onclick=()=>inputs.get(m.key)?.focus?.();li.append(jump);ul.append(li);}missing.append(ul);};
  refreshMissing(record?.missing_required);
  if(submitButton){submitButton.disabled=!can.can_submit;submitButton.title=can.can_submit?'':'Save the form and complete required items first';}
  // The admin review note is not form content; typing it must not mark the form as changed.
  form.addEventListener('input',event=>{if(event.target===note)return;dirty=true;if(submitButton)submitButton.disabled=true;});
  form.onsubmit=event=>{event.preventDefault();if(saveButton)save();};
  current.lock=value=>{saving=value;for(const b of actions.querySelectorAll('button'))b.disabled=value;if(!value&&submitButton)submitButton.disabled=!can.can_submit||dirty;};
  if(record&&!record.legacy)window.wzosFiles.mount($('forms-attachments'),'form',record.id);else $('forms-attachments').replaceChildren();
  editor.scrollIntoView?.({behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});heading.focus({preventScroll:true});
 }
 function values(){const fields={};for(const [key,control] of inputs)if(!key.startsWith('__'))fields[key]=control.read();return fields;}
 async function save(){
  if(saving||!current)return;const t=current.template,error=$('forms-error');error.textContent='';
  const title=inputs.get('__title').read().trim();if(!title){error.textContent='Enter a form title.';inputs.get('__title').focus();return;}
  const body={expected_version:current.version,template_id:t.id,template_revision:t.revision,template_checksum:t.checksum,title,location:inputs.get('__location').read(),order_id:inputs.get('__order').read(),fields:values()};
  const snapshot=current;current.lock(true);
  try{const record=await api(`/api/forms/${snapshot.id}`,{method:'PUT',body:JSON.stringify(body)});if(current!==snapshot)return;
   current={...snapshot,record,version:record.version};render();notice(`Draft saved as revision ${record.version}. Nothing was sent to an agency or reviewer.`);refreshList();}
  catch(failure){if(current===snapshot){error.textContent=failure.status===409?failure.message+' Use Refresh form to load the latest saved revision; your unsaved entries stay on screen until then.':failure.status?failure.message:'Save not confirmed. Check the connection and save again; an identical retry will not create a duplicate revision.';if(failure.status===409)addReload();}}
  finally{saving=false;if(current===snapshot)current.lock(false);}
 }
 function addReload(){if($('forms-reload'))return;const b=button('Refresh form');b.id='forms-reload';b.onclick=()=>{if(dirty&&!confirm('Discard your unsaved entries and load the latest saved revision?'))return;dirty=false;openRecord(current.id,current.opener);};$('forms-error').after(b);}
 async function transition(action,note=''){
  if(saving||!current?.record)return;if(dirty){$('forms-error').textContent='Save your changes first.';return;}
  const snapshot=current;current.lock(true);
  try{const record=await api(`/api/forms/${snapshot.id}/status`,{method:'POST',body:JSON.stringify({expected_version:snapshot.version,action,note:note.trim()})});if(current!==snapshot)return;
   current={...snapshot,record,version:record.version};render();notice(`Status is now ${STATUS[record.status]}. This is an internal WZOS status, not an agency submission.`);refreshList();}
  catch(failure){if(current===snapshot){$('forms-error').textContent=failure.message||'Status change not confirmed. Try again; it will not be applied twice.';if(failure.status===409)addReload();}}
  finally{saving=false;if(current===snapshot)current.lock(false);}
 }
 function print(){
  const {record,template:t}=current, out=$('forms-print');out.replaceChildren();
  const orders=Object.fromEntries(window.wzosClock.getOrders().map(o=>[o.id,o.title]));
  out.append(node('p','WZOS powered by Atlas AI Assistant · Forms hub','forms-print-brand'),node('h1',record.title),node('p',t?t.print_notice:'Legacy WZOS draft record.','forms-print-notice'));
  const facts=[['Type',CATEGORY[t?t.category:'legacy']],['Template',t?`${t.title} · revision ${t.revision} · checksum ${t.checksum.slice(0,16)}`:'Legacy draft'],['Status',STATUS[record.status]||record.status],['Record revision',String(record.version)],['Owner',record.owner_name],['Work order',record.order_id?orders[record.order_id]||record.order_id:'None'],['Location',record.location||'—'],['Last saved',new Date(record.updated_at).toLocaleString()]];
  const dl=node('dl');for(const [k,v] of facts)dl.append(node('dt',k),node('dd',v));out.append(dl);
  if(t?.official_reference){const ref=t.official_reference;out.append(node('p',`Official form: ${ref.authority} ${ref.form_identifier}, “${ref.official_title}”. Source ${ref.source.catalog_id} ${ref.source.section}, review status ${ref.source.review_status}. Applicability not determined.`,'forms-print-notice'));}
  if(record.missing_required?.length)out.append(node('p','Incomplete: '+record.missing_required.map(m=>m.label).join('; '),'forms-print-notice'));
  for(const section of t?.sections||[]){out.append(node('h2',section.title));
   for(const field of section.fields){const v=record.fields[field.key];
    if(field.type==='rows'){out.append(node('h3',field.label));if(!v?.length){out.append(node('p','No entries'));continue;}const table=node('table'),head=node('tr');for(const c of field.columns)head.append(node('th',c.label));table.append(head);for(const row of v){const tr=node('tr');for(const c of field.columns)tr.append(node('td',row[c.key]||''));table.append(tr);}out.append(table);}
    else out.append(node('p',`${field.label}: ${Array.isArray(v)?(v.join(', ')||'—'):(v??'—')}`));}}
  out.append(node('p',`Printed ${new Date().toLocaleString()} by ${session()?.name||''}. Not an official submission.`,'forms-print-footer'));
  document.body.classList.add('forms-printing');
  const done=()=>{document.body.classList.remove('forms-printing');window.removeEventListener('afterprint',done);};window.addEventListener('afterprint',done);
  window.print();
 }
 async function exportJson(){
  try{const response=await fetch(`/api/forms/${current.id}/export`,{headers:{'X-Preview-Actor':session()?.id||'',...await window.wzosAccount.headers()}});
   if(!response.ok){const data=await response.json();throw Error(typeof data.detail==='string'?data.detail:'Export unavailable');}
   const name=(response.headers.get('content-disposition')||'').match(/filename="([^"]+)"/)?.[1]||'wzos-form.json';
   const url=URL.createObjectURL(await response.blob()),a=node('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notice('Form exported as JSON. It is a WZOS record, not an agency submission.');}
  catch(error){notice(error.message);}
 }
 $('forms-template-search').oninput=renderTemplates;
 for(const id of ['forms-status','forms-category','forms-order'])$(id).onchange=()=>{offset=0;refreshList();};
 let searchTimer=null;$('forms-search').oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{offset=0;refreshList();},250);};
 $('forms-prev').onclick=()=>{offset=Math.max(0,offset-25);refreshList();};$('forms-next').onclick=()=>{offset+=25;refreshList();};
 $('forms-refresh').onclick=()=>{if(window.wzosFormsCanLeave())show();};
 document.addEventListener('wzos:view',event=>{if(event.detail==='forms')show();});
 document.addEventListener('wzos:session',()=>{epoch++;closeEditor(false);$('forms-list').replaceChildren();fullTemplates=new Map();if(!$('forms-view').hidden)show();});
})();
