"use strict";
(() => {
 const node=id=>document.getElementById(id), text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 const button=(label,id)=>{const b=text('button',label);b.type='button';b.className='secondary';if(id)b.id=id;return b;};
 const labelled=(caption,control)=>{const l=text('label',caption);l.append(control);return l;};
 let active=null, loaded=false, busy=false, generation=0, offset=0, observed=0, baseSeconds=0, pending=null, actorId=null, lastVerified=null, drafts=[], submitting=false, membersLoaded=null, persistence='tab';
 const TASKS={job_site:'Job Site',setup:'Setup',teardown:'Teardown',travel:'Travel Time',other:'Other'};
 const ACTIONS={clock_in:'Clock in',break_start:'Start break',break_end:'End break',switch_task:'Switch task',clock_out:'Clock out'};
 const BASIS={server_recorded:'Server recorded',admin_corrected:'Admin corrected',admin_entered:'Admin entered'};
 const STATUS={pending:'Awaiting admin review',applied:'Applied by admin',rejected:'Rejected by admin',duplicate:'Marked duplicate by admin'};
 const scope=session=>session?`${session.organization_id}:${session.id}`:null;
 // Drafts persist on this device under one key per organization and account, so another
 // account on a shared device never loads them. They stay device estimates until an admin
 // reviews the submission; nothing here replays or verifies attendance.
 const STORE='wzos.clockDrafts.v1:', RETAIN_MS=14*864e5, LOCAL_FIELDS=['submission'];
 const storage=()=>{try{return window.localStorage||null;}catch(error){return null;}};
 const tooOld=d=>new Date(d.stated_at||d.captured_at).getTime()<Date.now()-RETAIN_MS;
 const wellFormed=d=>d&&typeof d.request_id==='string'&&ACTIONS[d.action]&&!isNaN(new Date(d.captured_at));
 const outgoing=d=>Object.fromEntries(Object.entries(d).filter(([k])=>!LOCAL_FIELDS.includes(k)));
 function loadDrafts(id){
  const store=storage();persistence=store?'device':'tab';if(!id||!store)return [];
  try{const saved=JSON.parse(store.getItem(STORE+id)||'null');return saved&&saved.scope===id&&Array.isArray(saved.drafts)?saved.drafts.filter(wellFormed):[];}
  catch(error){persistence='tab';return [];}
 }
 function saveDrafts(){
  const store=storage();if(!actorId||!store){persistence='tab';return;}
  try{if(drafts.length)store.setItem(STORE+actorId,JSON.stringify({scope:actorId,saved_at:new Date().toISOString(),drafts}));else store.removeItem(STORE+actorId);persistence='device';}
  catch(error){persistence='tab';}
 }
 const format=n=>[Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(v=>String(v).padStart(2,'0')).join(':');
 const message=value=>{node('clock-message').textContent=value;};
 const local=value=>new Date(value).toLocaleString();
 const option=(value,label)=>{const o=text('option',label);o.value=value;return o;};
 // Connection state is separate from the polite status message so it stays visible.
 const connection=text('p','Checking connection');connection.id='clock-connection';connection.className='clock-connection';connection.setAttribute('role','status');
 node('clock-message').before(connection);
 function setConnection(state,detail){connection.dataset.state=state;connection.textContent=detail;}
 // Admin filters and export detail, created here so shared markup stays unchanged.
 const employee=document.createElement('select');employee.id='clock-employee';employee.append(option('','All team members'));
 const employeeLabel=labelled('Employee',employee);employeeLabel.id='clock-employee-label';employeeLabel.hidden=true;
 const exportDetail=document.createElement('select');exportDetail.id='clock-export-detail';exportDetail.append(option('shifts','One row per shift'),option('intervals','Task and break intervals'));
 node('clock-to').parentNode?.after(employeeLabel);node('clock-export').before(labelled('Export detail',exportDetail));
 const filters=()=>`&team=${node('clock-team').checked}${employee.value?'&employee_id='+encodeURIComponent(employee.value):''}${node('clock-from').value?'&start_date='+node('clock-from').value:''}${node('clock-to').value?'&end_date='+node('clock-to').value:''}`;
 function controls(){
  const blocked=busy||!loaded||!!pending||!navigator.onLine, onBreak=active?.status==='on_break';
  node('clock-in').hidden=!!active;node('clock-out').hidden=!active;node('clock-break').hidden=!active;node('clock-switch').hidden=!active;
  for(const id of ['clock-in','clock-out','clock-break'])node(id).disabled=blocked;
  node('clock-switch').disabled=blocked||onBreak||node('clock-task').value===active?.task;
  node('clock-break').textContent=onBreak?'End break':'Start break';
  node('clock-order').disabled=blocked||!!active;node('clock-note').disabled=blocked||!!active;node('clock-task').disabled=blocked||onBreak;
  node('clock-retry').hidden=!pending;node('clock-retry').disabled=busy||!navigator.onLine;
  node('clock-refresh').disabled=busy;node('clock-team').disabled=busy;
  // Drafts are only for when confirmed clock actions are unavailable, which avoids duplicating live punches.
  const session=window.wzosClock.getSession();
  keep.disabled=!session||submitting||(loaded&&navigator.onLine)||drafts.length>=50;
  submit.disabled=!drafts.some(d=>!tooOld(d))||submitting||!loaded||!navigator.onLine;
  download.disabled=!drafts.length;removeLast.disabled=!drafts.length||submitting;discard.disabled=!drafts.length||submitting;
 }
 function renderActive(data){
  active=data.active;loaded=true;lastVerified=new Date().toISOString();observed=performance.now();baseSeconds=active?.work_seconds||0;
  node('clock-state').textContent=active?active.status==='on_break'?'ON BREAK':'CLOCKED IN':'OFF THE CLOCK';
  node('clock-active-job').textContent=active?`${active.order_title||'Unassigned work'} · ${data.tasks[active.task]} · revision ${active.version}`:'';
  if(active){node('clock-task').value=active.task;node('clock-order').value=active.order_id||'';node('clock-note').value=active.note;}
  setConnection('online','Online · shift verified with the server at '+new Date(lastVerified).toLocaleTimeString());
  tick();controls();renderDrafts();
 }
 function tick(){node('clock-timer').textContent=format(baseSeconds+(active?.status==='working'?Math.max(0,Math.floor((performance.now()-observed)/1000)):0));}
 async function loadMembers(session){
  if(session.role!=='admin'||membersLoaded===scope(session))return;
  const data=await window.wzosClock.api('/api/time/members');
  if(scope(session)!==scope(window.wzosClock.getSession()))return;
  membersLoaded=scope(session);employee.replaceChildren(option('','All team members'),...data.items.map(p=>option(p.id,p.name)));
 }
 async function refresh(){
  const session=window.wzosClock.getSession();if(!session)return;
  if(!navigator.onLine){showOffline();return;}
  const epoch=++generation;loaded=false;controls();
  const admin=session.role==='admin';node('clock-team-label').hidden=!admin;employeeLabel.hidden=!admin;if(!admin){node('clock-team').checked=false;employee.value='';}
  const options=[text('option','Unassigned')];options[0].value='';for(const row of window.wzosClock.getOrders()){const o=text('option',row.title);o.value=row.id;options.push(o);}node('clock-order').replaceChildren(...options);
  try{
   await loadMembers(session).catch(()=>{});
   const [state,history]=await Promise.all([window.wzosClock.api('/api/time/status'),window.wzosClock.api(`/api/time/entries?offset=${offset}${filters()}`)]);
   if(epoch!==generation||scope(session)!==scope(window.wzosClock.getSession()))return;
   renderActive(state);node('clock-history').replaceChildren();
   for(const entry of history.items){const article=document.createElement('article');article.className='clock-entry';
    const basis=text('span',BASIS[entry.record_basis]||'Server recorded');basis.className='clock-basis';basis.dataset.basis=entry.record_basis||'server_recorded';
    const title=text('strong',entry.order_title||'Unassigned work');
    article.append(title,basis,text('p',`${entry.employee_name||entry.employee_id} · ${local(entry.clock_in)} → ${entry.clock_out?local(entry.clock_out):'Active'}`),text('p',`${format(entry.work_seconds)} work · ${format(entry.break_seconds)} breaks${entry.correction_count?` · ${entry.correction_count} correction${entry.correction_count===1?'':'s'}`:''}`));
    const details=document.createElement('details');details.append(text('summary',`${entry.segments.length} task intervals`));for(const segment of entry.segments)details.append(text('p',`${state.tasks[segment.task]} · ${new Date(segment.start).toLocaleTimeString()} → ${segment.end?new Date(segment.end).toLocaleTimeString():'Active'}`));article.append(details);
    window.wzosClockReview?.decorate(article,entry,state.tasks);node('clock-history').append(article);
   }
   if(!history.items.length)node('clock-history').append(text('p','No time entries yet.'));
   node('clock-prev').disabled=offset===0;node('clock-next').disabled=offset+history.limit>=history.total;
   node('clock-page').textContent=`${history.total} records · showing ${history.items.length?offset+1:0}–${offset+history.items.length}. Times shown in your device timezone.`;
   loadSubmissions(session);window.wzosClockReview?.refreshQueue?.();
  }catch(error){if(epoch===generation){loaded=false;if(!error.status){showOffline();}else{active=null;lastVerified=null;baseSeconds=0;tick();node('clock-state').textContent='CLOCK STATUS UNAVAILABLE';setConnection('error','Server could not confirm your shift. Confirmed clock actions are paused.');node('clock-history').replaceChildren();message(error.message);}}}
  finally{if(epoch===generation)controls();}
 }
 async function send(action,retry=false){
  if(!navigator.onLine){showOffline();return;}
  if(busy||(!retry&&(!loaded||pending)))return;
  const session=window.wzosClock.getSession();if(!session)return;
  if(!retry)pending={actor:scope(session),body:{request_id:crypto.randomUUID(),action,shift_id:active?.id||null,expected_version:active?.version||0,task:node('clock-task').value,...(action==='clock_in'?{order_id:node('clock-order').value||null,note:node('clock-note').value}:{})}};
  if(pending.actor!==scope(session))return;
  busy=true;node('identity').disabled=true;controls();message('Saving clock action…');
  try{await window.wzosClock.api('/api/time/commands',{method:'POST',body:JSON.stringify(pending.body)});pending=null;message(session.restricted_staging?'Clock action saved in temporary cloud staging.':'Clock action saved locally.');document.dispatchEvent(new CustomEvent('wzos:time-context'));}
  catch(error){if(error.status>=400&&error.status<500){pending=null;message(error.message);}else message('Save not confirmed. Reconnect and retry the same action; duplicate records will be prevented.');}
  finally{busy=false;node('identity').disabled=false;await refresh();controls();}
 }
 node('clock-in').addEventListener('click',()=>send('clock_in'));node('clock-out').addEventListener('click',()=>send('clock_out'));
 node('clock-switch').addEventListener('click',()=>send('switch_task'));node('clock-break').addEventListener('click',()=>send(active?.status==='on_break'?'break_end':'break_start'));
 node('clock-retry').addEventListener('click',()=>send(null,true));node('clock-refresh').addEventListener('click',refresh);node('clock-task').addEventListener('change',controls);
 node('clock-team').addEventListener('change',()=>{offset=0;if(!node('clock-team').checked)employee.value='';refresh();});node('clock-prev').addEventListener('click',()=>{offset=Math.max(0,offset-20);refresh();});node('clock-next').addEventListener('click',()=>{offset+=20;refresh();});
 employee.addEventListener('change',()=>{offset=0;if(employee.value)node('clock-team').checked=true;refresh();});
 for(const id of ['clock-from','clock-to'])node(id).onchange=()=>{offset=0;refresh();};
 node('clock-export').onclick=async()=>{const exportButton=node('clock-export');exportButton.disabled=true;try{const response=await fetch(`/api/time/export?detail=${exportDetail.value}${filters()}`,{headers:{'X-Preview-Actor':window.wzosClock.getSession().id,...await window.wzosAccount.headers()}});if(!response.ok){const error=await response.json();throw Error(typeof error.detail==='string'?error.detail:'Check export dates');}const name=(response.headers.get('content-disposition')||'').match(/filename="([^"]+)"/)?.[1]||'wzos-time.csv';const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){message(error.message);}finally{exportButton.disabled=false;}};
 document.addEventListener('wzos:clock-open',refresh);
 document.addEventListener('wzos:session',()=>{const id=scope(window.wzosClock.getSession());if(id!==actorId){actorId=id;pending=null;active=null;lastVerified=null;drafts=loadDrafts(id);membersLoaded=null;employee.replaceChildren(option('','All team members'));submitted.replaceChildren();renderDrafts();baseSeconds=0;offset=0;node('clock-note').value='';node('clock-team').checked=false;node('clock-history').replaceChildren();node('clock-state').textContent='Loading clock';setConnection('checking','Checking connection');tick();message('');}refresh();});
 window.addEventListener('beforeunload',event=>{if(pending||submitting||(drafts.length&&persistence!=='device')){event.preventDefault();event.returnValue='';}});
 // Another open tab for the same account changed the saved drafts.
 window.addEventListener('storage',event=>{if(actorId&&event.key===STORE+actorId&&!submitting){drafts=loadDrafts(actorId);renderDrafts();}});
 // Offline attendance drafts: device-timestamped requests for admin review, never replayed as clock punches.
 const draftPanel=document.createElement('section');draftPanel.className='panel clock-drafts';draftPanel.id='clock-drafts';
 const draftAction=document.createElement('select');draftAction.id='clock-draft-action';draftAction.append(...Object.entries(ACTIONS).map(([k,v])=>option(k,v)));
 const draftTask=document.createElement('select');draftTask.id='clock-draft-task';draftTask.append(...Object.entries(TASKS).map(([k,v])=>option(k,v)));
 const draftWhen=document.createElement('input');draftWhen.type='datetime-local';draftWhen.id='clock-draft-when';draftWhen.step='60';
 const draftNote=document.createElement('textarea');draftNote.id='clock-draft-note';draftNote.maxLength=1000;draftNote.rows=2;draftNote.placeholder='What happened and why the clock was unavailable';
 const discard=button('Discard all drafts','clock-draft-discard'),keep=button('Keep draft','clock-draft-keep'),submit=button('Submit drafts for admin review','clock-draft-submit'),download=button('Download drafts','clock-draft-download'),removeLast=button('Remove last draft','clock-draft-remove');
 const storageNote=text('p','');storageNote.id='clock-draft-storage';storageNote.setAttribute('role','status');
 const draftList=document.createElement('ol');draftList.id='clock-draft-list';draftList.className='clock-draft-list';
 const submitted=document.createElement('ul');submitted.id='clock-submitted';submitted.className='clock-draft-list';
 const draftActions=document.createElement('div');draftActions.className='clock-actions';draftActions.append(keep,removeLast,submit,download,discard);
 draftPanel.append(text('h2','Offline attendance drafts'),text('p','When the clock cannot reach the server, record what happened here. Each draft keeps your device time. When you reconnect, submit the drafts for admin review. Drafts never change your shift automatically and are not verified attendance or payroll records.'),storageNote,
  labelled('What happened',draftAction),labelled('Task',draftTask),labelled('When, if earlier than now (device time, optional)',draftWhen),labelled('Note',draftNote),draftActions,draftList,text('h3','Submitted for review'),submitted);
 node('clock-view').append(draftPanel);
 const effective=d=>d.stated_at||d.captured_at;
 function expected(){
  // Replays drafts over the last verified status so impossible or duplicate sequences are refused.
  let state=lastVerified?(active?active.status:'off_clock'):'unknown', task=active?.task||null;
  for(const d of drafts){state=d.action==='break_start'?'on_break':d.action==='clock_out'?'off_clock':'working';if(d.task&&d.action!=='break_start')task=d.task;}
  return {state,task};
 }
 const allowed={off_clock:['clock_in'],working:['break_start','switch_task','clock_out'],on_break:['break_end','clock_out']};
 function renderDrafts(){
  draftList.replaceChildren();
  storageNote.dataset.persistence=persistence;
  storageNote.textContent=persistence==='device'?'Drafts are saved on this device for your account and organization until you submit or discard them, even if you close the app. Other people using this device cannot open them in WZOS, but keep the device secure.'
   :'This device is not saving drafts (private browsing or storage blocked). They stay only in this open tab, so submit or download them before you close it or sign out.';
  for(const d of drafts){
   const changed=lastVerified&&((active?.id||null)!==d.known_shift_id||(active?.version??null)!==d.known_version);
   const state=tooOld(d)?'Too old to submit (over 14 days) — download it and ask an admin for a manual entry':d.submission==='unconfirmed'?'Submission not confirmed — submit again; it will not create duplicates':persistence==='device'?'Saved on this device — not yet submitted':'In this tab only — not yet submitted';
   const item=text('li',`${ACTIONS[d.action]}${d.task?' · '+TASKS[d.task]:''} · ${local(effective(d))} (device time, unverified)${d.note?' · '+d.note:''}`);
   const status=text('small',' '+state);status.className='clock-draft-state';status.dataset.state=tooOld(d)?'too_old':d.submission||'local';item.append(status);
   if(changed)item.append(text('small',' Your shift changed on the server after this draft. The admin will check it for duplicates.'));
   draftList.append(item);
  }
  controls();
 }
 keep.onclick=()=>{
  const session=window.wzosClock.getSession();if(!session)return;
  const now=new Date(), stated=draftWhen.value?new Date(draftWhen.value):null, action=draftAction.value, {state,task}=expected();
  if(stated&&(isNaN(stated)||stated>now)){message('The earlier time must be a valid time that is not in the future.');return;}
  if(state!=='unknown'&&!allowed[state].includes(action)){message(`${ACTIONS[action]} does not follow your ${drafts.length?'last draft':'last confirmed status'}. Drafts must follow the order things happened.`);return;}
  if(action==='switch_task'&&task===draftTask.value){message('Choose a different task to record a task switch.');return;}
  if(drafts.length&&(stated||now)<new Date(effective(drafts.at(-1)))){message('Drafts must be in time order. Check the earlier time.');return;}
  drafts.push({request_id:crypto.randomUUID(),action,task:['clock_in','switch_task'].includes(action)?draftTask.value:null,note:draftNote.value.trim(),captured_at:now.toISOString(),...(stated?{stated_at:stated.toISOString()}:{}),known_shift_id:lastVerified?active?.id||null:null,known_version:lastVerified?active?.version??null:null});
  saveDrafts();draftNote.value='';draftWhen.value='';renderDrafts();message(`Draft ${persistence==='device'?'saved on this device':'kept in this tab only'}. It has not changed your shift. Submit it for review when you reconnect.`);
 };
 removeLast.onclick=()=>{drafts.pop();saveDrafts();renderDrafts();message('Removed the last draft.');};
 discard.onclick=()=>{if(!drafts.length||submitting||!window.confirm?.('Discard all unsubmitted offline drafts on this device? This cannot be undone.'))return;drafts=[];saveDrafts();renderDrafts();message('Offline drafts discarded. Nothing was sent to your admin.');};
 submit.onclick=async()=>{
  const session=window.wzosClock.getSession();if(!session||!drafts.length||!navigator.onLine||submitting)return;
  const owner=scope(session), batch=drafts.filter(d=>!tooOld(d));if(!batch.length)return;
  submitting=true;controls();message('Submitting drafts for admin review…');
  try{
   const result=await window.wzosClock.api('/api/time/offline-submissions',{method:'POST',body:JSON.stringify({device_submitted_at:new Date().toISOString(),drafts:batch.map(outgoing)})});
   if(owner!==scope(window.wzosClock.getSession()))return;
   const sent=new Set(batch.map(d=>d.request_id));drafts=drafts.filter(d=>!sent.has(d.request_id));saveDrafts();
   message(`${result.items.length} draft${result.items.length===1?'':'s'} submitted for admin review. Your recorded shift has not changed.`);loadSubmissions(session);
  }catch(error){
   if(owner!==scope(window.wzosClock.getSession()))return;
   const kept=persistence==='device'?'on this device':'in this tab';
   if(error.status&&error.status<500){message(`${error.message} Your drafts are still kept ${kept}.`);}
   else{const sent=new Set(batch.map(d=>d.request_id));drafts=drafts.map(d=>sent.has(d.request_id)?{...d,submission:'unconfirmed'}:d);saveDrafts();message(`Submission not confirmed. Your drafts are still kept ${kept}, and submitting again will not create duplicates.`);}
  }
  finally{submitting=false;renderDrafts();}
 };
 download.onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({type:'WZOS offline attendance drafts',automatic_sync:false,time_basis:'device_estimate_unverified',drafts:drafts.map(outgoing)},null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='wzos-offline-drafts.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 async function loadSubmissions(session){
  try{
   const data=await window.wzosClock.api('/api/time/offline-submissions?status=all');
   if(scope(session)!==scope(window.wzosClock.getSession()))return;
   submitted.replaceChildren(...data.items.slice(-10).reverse().map(s=>text('li',`${ACTIONS[s.action]} · estimated ${local(s.estimated_at)} · ${STATUS[s.status]||s.status}${s.resolution_reason&&s.status!=='pending'?' · '+s.resolution_reason:''}`)));
   if(!data.items.length)submitted.append(text('li','Nothing submitted yet.'));
  }catch(error){/* Status list is informational; the clock remains usable. */}
 }
 function showOffline(){loaded=false;node('clock-state').textContent=lastVerified?'CONNECTION UNAVAILABLE — LAST KNOWN STATUS':'CONNECTION UNAVAILABLE — STATUS NOT LOADED';setConnection('offline',lastVerified?'Offline · showing the status confirmed at '+new Date(lastVerified).toLocaleTimeString()+'. The timer is an estimate.':'Offline · your shift status has not loaded yet.');message(lastVerified?'Confirmed clock actions need a connection. You can keep offline drafts for admin review.':'Connect once to load your shift. You can keep offline drafts for admin review.');controls();}
 window.addEventListener('offline',()=>{generation++;showOffline();});
 window.addEventListener('online',()=>{setConnection('reconnecting','Reconnected · checking your current shift with the server');message(drafts.length?`Connection restored. You have ${drafts.length} offline draft${drafts.length===1?'':'s'}. Review and submit them for admin review; they do not change your shift.`:'Connection restored. Checking your current shift.');refresh();});
 renderDrafts();
 setInterval(tick,1000);controls();
})();
