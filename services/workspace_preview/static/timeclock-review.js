"use strict";
// Time clock audit history, admin corrections and offline-draft review. Server enforces all permissions.
(() => {
 const node=id=>document.getElementById(id), text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 const button=(label,cls='secondary')=>{const b=text('button',label);b.type='button';b.className=cls;return b;};
 const labelled=(caption,control)=>{const l=text('label',caption);l.append(control);return l;};
 const option=(value,label)=>{const o=text('option',label);o.value=value;return o;};
 const TASKS={job_site:'Job Site',setup:'Setup',teardown:'Teardown',travel:'Travel Time',other:'Other'};
 const ACTIONS={clock_in:'Clock in',break_start:'Start break',break_end:'End break',switch_task:'Switch task',clock_out:'Clock out'};
 const KINDS={server_receipt:'Server-recorded action',admin_corrected:'Admin-corrected shift',admin_entered:'Admin-entered shift'};
 const local=value=>value?new Date(value).toLocaleString():'open';
 const hms=n=>[Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(v=>String(v).padStart(2,'0')).join(':');
 const api=(path,options)=>window.wzosClock.api(path,options);
 const session=()=>window.wzosClock.getSession();
 const isAdmin=()=>session()?.role==='admin';
 const say=value=>{node('clock-message').textContent=value;};
 const pad=n=>String(n).padStart(2,'0');
 const toInput=value=>{if(!value)return '';const d=new Date(value);return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;};
 // Inputs show whole seconds; an untouched field keeps the exact original time so saving never shifts it.
 const fromInput=input=>!input.value?null:input.value===input.dataset.initial?input.dataset.original:new Date(input.value).toISOString();
 const reveal=element=>element.scrollIntoView?.({behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
 const timeInput=(value,caption)=>{const input=document.createElement('input');input.type='datetime-local';input.step='1';input.value=toInput(value);if(value){input.dataset.initial=input.value;input.dataset.original=value;}input.setAttribute('aria-label',caption);return input;};

 // Review queue (admin only).
 const queue=document.createElement('section');queue.className='panel clock-queue';queue.id='clock-queue';queue.hidden=true;queue.setAttribute('aria-labelledby','clock-queue-title');
 const queueTitle=text('h2','Offline review queue');queueTitle.id='clock-queue-title';
 const addShift=button('Add missing shift');addShift.id='clock-add-shift';
 const queueList=document.createElement('ul');queueList.className='clock-queue-list';
 const queueHeading=document.createElement('div');queueHeading.className='panel-heading';queueHeading.append(queueTitle,addShift);
 queue.append(queueHeading,text('p','Drafts that crew members recorded while offline. The times are estimates from each device and are not verified attendance. Apply a draft through a correction, or mark it as a duplicate or reject it. Every decision is kept in the audit history.'),queueList);
 // Correction editor (admin only).
 const editor=document.createElement('section');editor.className='panel clock-editor';editor.id='clock-editor';editor.hidden=true;editor.setAttribute('aria-labelledby','clock-editor-title');
 node('clock-view').append(queue,editor);
 let editing=null, queueEpoch=0;

 function close(focus=true){const opener=editing?.opener;editing=null;editor.hidden=true;editor.replaceChildren();if(focus)(opener?.isConnected?opener:node('clock-refresh')).focus();}
 function intervalRow(container,kind,item={}){
  const row=document.createElement('div');row.className='clock-interval-row';
  const index=container.children.length+1, start=timeInput(item.start,`${kind} ${index} start`), end=timeInput(item.end,`${kind} ${index} end`);
  const remove=button('Remove');remove.setAttribute('aria-label',`Remove ${kind.toLowerCase()} ${index}`);remove.onclick=()=>{row.remove();(container.querySelector('input,select')||container.nextElementSibling)?.focus();};
  if(kind==='Task interval'){const task=document.createElement('select');task.setAttribute('aria-label',`Task interval ${index} task`);task.append(...Object.entries(TASKS).map(([k,v])=>option(k,v)));task.value=item.task||'job_site';row.append(task);}
  row.append(labelled('Start',start),labelled('End',end),remove);container.append(row);return row;
 }
 async function open(mode,entry,{opener,submission}={}){
  if(!isAdmin())return;
  editing={mode,entry,opener,request_id:crypto.randomUUID(),resolves:submission?[submission.id]:[]};
  editor.replaceChildren();editor.hidden=false;
  const title=text('h2',mode==='correction'?`Correct shift · ${entry.employee_name||entry.employee_id}`:'Add missing shift');title.id='clock-editor-title';
  const zone=Intl.DateTimeFormat().resolvedOptions().timeZone;
  editor.append(title,text('p',`Times are in your device timezone (${zone}). The audit history keeps the original record alongside this change, which will be labelled as an admin change, not a server-recorded time. ${mode==='correction'&&!entry.clock_out?'Correcting an active shift closes it.':''}`));
  if(submission){const hint=text('p',`Offline draft from ${submission.employee_name}: ${ACTIONS[submission.action]}${submission.task?' · '+TASKS[submission.task]:''} at about ${local(submission.estimated_at)}. This is estimated from the device clock (offset ${submission.device_offset_seconds}s). ${submission.note?'Note: '+submission.note:''}`);hint.className='clock-hint';editor.append(hint);}
  const form=document.createElement('form');form.noValidate=true;
  let person=null;
  if(mode==='manual'){person=document.createElement('select');person.required=true;person.append(option('','Choose employee'));form.append(labelled('Employee',person));
   try{const members=await api('/api/time/members');person.append(...members.items.map(p=>option(p.id,p.name)));}catch(error){say(error.message);}
   person.value=entry.employee_id||'';}
  const clockIn=timeInput(entry.clock_in,'Clock in'), clockOut=timeInput(entry.clock_out,'Clock out');
  const order=document.createElement('select');order.append(option('','Unassigned'),...window.wzosClock.getOrders().map(o=>option(o.id,o.title)));
  if(entry.order_id&&![...order.options].some(o=>o.value===entry.order_id))order.append(option(entry.order_id,entry.order_title||entry.order_id));order.value=entry.order_id||'';
  const breaks=document.createElement('div'),segments=document.createElement('div');breaks.className=segments.className='clock-intervals';
  for(const item of entry.breaks||[])intervalRow(breaks,'Break',item);
  for(const item of entry.segments?.length?entry.segments:[{task:'job_site',start:entry.clock_in,end:entry.clock_out}])intervalRow(segments,'Task interval',item);
  const addBreak=button('Add break'),addSegment=button('Add task interval');
  addBreak.onclick=()=>intervalRow(breaks,'Break').querySelector('input').focus();addSegment.onclick=()=>intervalRow(segments,'Task interval').querySelector('select').focus();
  const breakSet=document.createElement('fieldset');breakSet.append(text('legend','Breaks'),breaks,addBreak);
  const segmentSet=document.createElement('fieldset');segmentSet.append(text('legend','Task intervals'),segments,addSegment);
  const reason=document.createElement('textarea');reason.required=true;reason.minLength=5;reason.maxLength=500;reason.rows=2;reason.placeholder='Why the record is being changed, and who confirmed it';
  const error=text('p','');error.className='clock-error';error.setAttribute('role','alert');
  const save=button(mode==='correction'?'Save correction':'Add shift','primary');save.type='submit';const cancel=button('Cancel');cancel.onclick=()=>close();
  const actions=document.createElement('div');actions.className='clock-actions';actions.append(save,cancel);
  form.append(labelled('Clock in',clockIn),labelled('Clock out',clockOut),labelled('Work order',order),breakSet,segmentSet,labelled('Reason for change (required)',reason),error,actions);
  editor.append(form);
  form.onsubmit=async event=>{
   event.preventDefault();error.textContent='';
   const read=(container,withTask)=>[...container.children].map(row=>{const [start,end]=row.querySelectorAll('input');return {...(withTask?{task:row.querySelector('select').value}:{}),start:fromInput(start),end:fromInput(end)};});
   const body={request_id:editing.request_id,reason:reason.value.trim(),clock_in:fromInput(clockIn),clock_out:fromInput(clockOut),breaks:read(breaks,false),segments:read(segments,true),resolves:editing.resolves};
   const missing=!body.clock_in||!body.clock_out||[...body.breaks,...body.segments].some(i=>!i.start||!i.end)||(person&&!person.value);
   if(missing){error.textContent='Fill in every time, and choose an employee for a new shift.';return;}
   if(body.reason.length<5){error.textContent='Enter a reason of at least 5 characters.';reason.focus();return;}
   if(mode==='correction'){body.expected_version=entry.version;if(order.value!==(entry.order_id||''))body.order_id=order.value||null;}
   else{body.employee_id=person.value;body.order_id=order.value||null;}
   save.disabled=true;
   try{
    const path=mode==='correction'?`/api/time/entries/${encodeURIComponent(entry.id)}/corrections`:'/api/time/entries';
    await api(path,{method:'POST',body:JSON.stringify(body)});
    close();say(mode==='correction'?'Correction saved and added to the audit history.':'Shift added and recorded in the audit history.');
    document.dispatchEvent(new CustomEvent('wzos:clock-open'));
   }catch(failure){error.textContent=failure.status?failure.message:'Save not confirmed. Check the connection, then save again. Retrying will not apply the change twice.';}
   finally{save.disabled=false;}
  };
  editor.onkeydown=event=>{if(event.key==='Escape'){event.preventDefault();close();}};
  reveal(editor);(person||clockIn).focus();
 }
 function renderAudit(target,data){
  target.replaceChildren();
  const receipts=document.createElement('ul');for(const r of data.receipts)receipts.append(text('li',`${ACTIONS[r.action]} · ${local(r.occurred_at)}`));
  target.append(text('h4','Server-recorded actions'),data.receipts.length?receipts:text('p','None. This shift was entered by an admin.'));
  const changes=document.createElement('ul');
  for(const c of data.corrections){const item=text('li',`${local(c.occurred_at)} · ${c.admin_name} · ${c.kind==='manual_entry'?'added this shift':'corrected this shift'} · Reason: ${c.reason}`);
   const span=s=>`${local(s.clock_in)} → ${local(s.clock_out)} (${hms(s.work_seconds)} work, ${hms(s.break_seconds)} breaks)`;
   if(c.before)item.append(text('small',`Before: ${span(c.before)}`));item.append(text('small',`After: ${span(c.after)}`));changes.append(item);}
  target.append(text('h4','Admin changes'),data.corrections.length?changes:text('p','None. Times are as the server recorded them.'));
  if(data.offline_submissions.length){const linked=document.createElement('ul');for(const s of data.offline_submissions)linked.append(text('li',`${ACTIONS[s.action]} · estimated ${local(s.estimated_at)} · ${s.status}`));target.append(text('h4','Linked offline drafts'),linked);}
 }
 function decorate(article,entry){
  const audit=document.createElement('details');audit.className='clock-audit';audit.append(text('summary','Audit history'));
  const body=document.createElement('div');audit.append(body);let loaded=false;
  audit.addEventListener('toggle',async()=>{if(!audit.open||loaded)return;body.replaceChildren(text('p','Loading audit history…'));
   try{renderAudit(body,await api(`/api/time/entries/${encodeURIComponent(entry.id)}`));loaded=true;}catch(error){body.replaceChildren(text('p',error.message||'Audit history unavailable.'));}});
  article.append(audit);
  if(isAdmin()){const correct=button('Correct');correct.setAttribute('aria-label',`Correct shift for ${entry.employee_name||entry.employee_id} starting ${local(entry.clock_in)}`);correct.onclick=()=>open('correction',entry,{opener:correct});article.append(correct);}
 }
 async function apply(submission,opener){
  if(submission.known_shift_id){
   try{const {entry}=await api(`/api/time/entries/${encodeURIComponent(submission.known_shift_id)}`);
    const draft=JSON.parse(JSON.stringify(entry));
    if(submission.action==='clock_out'&&!draft.clock_out){draft.clock_out=submission.estimated_at;for(const list of [draft.segments,draft.breaks])if(list.length&&!list.at(-1).end)list.at(-1).end=submission.estimated_at;}
    return open('correction',draft,{opener,submission});
   }catch(error){if(error.status!==404){say(error.message);return;}}
  }
  const start=submission.action==='clock_in'?submission.estimated_at:null;
  open('manual',{employee_id:submission.employee_id,clock_in:start,clock_out:null,breaks:[],segments:[{task:submission.task||'job_site',start,end:null}]},{opener,submission});
 }
 async function resolve(submission,decision,reason,control){
  if(reason.value.trim().length<3){say('Enter a reason of at least 3 characters before rejecting or marking a duplicate.');reason.focus();return;}
  control.disabled=true;
  try{await api(`/api/time/offline-submissions/${encodeURIComponent(submission.id)}/resolve`,{method:'POST',body:JSON.stringify({decision,reason:reason.value.trim()})});say(decision==='duplicate'?'Draft marked as a duplicate. Attendance was not changed.':'Draft rejected. Attendance was not changed.');refreshQueue();}
  catch(error){say(error.message||'Decision not confirmed. Try again; it will not be applied twice.');}
  finally{control.disabled=false;}
 }
 async function refreshQueue(){
  const epoch=++queueEpoch;queue.hidden=!isAdmin();if(queue.hidden){queueList.replaceChildren();return;}
  try{
   const data=await api('/api/time/offline-submissions?team=true');if(epoch!==queueEpoch)return;
   queueList.replaceChildren();
   for(const s of data.items){
    const item=document.createElement('li');item.className='clock-queue-item';
    item.append(text('strong',`${s.employee_name} · ${ACTIONS[s.action]}${s.task?' · '+TASKS[s.task]:''}`),
     text('p',`About ${local(s.estimated_at)} (estimated). Device recorded it at ${local(s.captured_at)}${s.stated_at?`, stated time ${local(s.stated_at)}`:''}. Device clock offset ${s.device_offset_seconds}s. Received ${local(s.received_at)}.`));
    if(s.note)item.append(text('p','Note: '+s.note));
    for(const d of s.possible_duplicates){const warning=text('p',`Possible duplicate: ${KINDS[d.kind]||d.kind} at ${local(d.occurred_at)}`);warning.className='clock-warning';item.append(warning);}
    const reason=document.createElement('input');reason.maxLength=500;reason.placeholder='Reason (required to reject or mark duplicate)';
    const applyButton=button('Apply with correction','primary'),duplicate=button('Mark duplicate'),reject=button('Reject');
    applyButton.onclick=()=>apply(s,applyButton);duplicate.onclick=()=>resolve(s,'duplicate',reason,duplicate);reject.onclick=()=>resolve(s,'rejected',reason,reject);
    const actions=document.createElement('div');actions.className='clock-actions';actions.append(applyButton,duplicate,reject);
    item.append(labelled('Decision reason',reason),actions);queueList.append(item);
   }
   if(!data.items.length)queueList.append(text('li','No offline drafts are waiting for review.'));
  }catch(error){if(epoch===queueEpoch)queueList.replaceChildren(text('li',error.message||'Review queue unavailable.'));}
 }
 addShift.onclick=()=>open('manual',{employee_id:'',clock_in:null,clock_out:null,breaks:[],segments:[]},{opener:addShift});
 document.addEventListener('wzos:session',()=>{close(false);queueEpoch++;queueList.replaceChildren();queue.hidden=!isAdmin();});
 window.wzosClockReview={decorate,refreshQueue};
})();
