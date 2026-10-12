"use strict";
(() => {
 const node=id=>document.getElementById(id), text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 const button=(label,id)=>{const b=text('button',label);b.type='button';b.className='secondary';if(id)b.id=id;return b;};
 const labelled=(caption,control)=>{const l=text('label',caption);l.append(control);return l;};
 let active=null, loaded=false, busy=false, generation=0, offset=0, observed=0, baseSeconds=0, pending=null, actorId=null, lastVerified=null, drafts=[], submitting=false, membersLoaded=null, persistence='tab', draftWrites=0;
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
  const store=storage();persistence=store&&navigator.locks?.request?'device':'tab';if(!id||!store)return [];
  try{const saved=JSON.parse(store.getItem(STORE+id)||'null');return saved&&saved.scope===id&&Array.isArray(saved.drafts)?saved.drafts.filter(wellFormed):[];}
  catch(error){persistence='tab';return [];}
 }
 // A shared origin-scoped Web Lock makes the read/edit/write one transaction across
 // tabs. Without it, retain changes in memory rather than risk lost device records.
 async function mutate(id,change){
  const store=storage();
  draftWrites++;
  try{
   if(id&&store&&navigator.locks?.request&&(persistence==='device'||id!==actorId)){
    try{
     await navigator.locks.request(STORE+id,()=>{
      let saved=null;try{saved=JSON.parse(store.getItem(STORE+id)||'null');}catch(error){saved=null;}
      const next=change(saved&&saved.scope===id&&Array.isArray(saved.drafts)?saved.drafts.filter(wellFormed):[]);
      if(next.length)store.setItem(STORE+id,JSON.stringify({scope:id,saved_at:new Date().toISOString(),drafts:next}));else store.removeItem(STORE+id);
      if(id===actorId)drafts=next;
     });
     return;
    }catch(error){if(id!==actorId)return;persistence='tab';}
   }
   if(id===actorId)drafts=change(drafts);
  }finally{draftWrites--;}
 }
 const format=n=>[Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(v=>String(v).padStart(2,'0')).join(':');
 const message=value=>{node('clock-message').textContent=value;};
 const local=value=>new Date(value).toLocaleString();
 const option=(value,label)=>{const o=text('option',label);o.value=value;return o;};
 const storageKey='wzos.time-tracker.v1:';
 let locations=[], locationBusy=false, flushing=false, snapshotAt=null, storageFailed=false;
 function persist(){
  if(!actorId)return false;
  try{window.localStorage.setItem(storageKey+actorId,JSON.stringify({owner:actorId,active,lastVerified,snapshotAt,baseSeconds,pending}));storageFailed=false;return true;}
  catch{storageFailed=true;locationStatus.textContent='Device tracker storage unavailable. Keep this tab open and download device records before closing.';return false;}
 }
 function restore(owner){
  if(!owner)return;
  try{const saved=JSON.parse(window.localStorage.getItem(storageKey+owner)||'null');
   if(saved?.owner===owner){active=saved.active;lastVerified=saved.lastVerified;snapshotAt=saved.snapshotAt;baseSeconds=saved.baseSeconds||0;pending=saved.pending;const evidence=JSON.parse(window.localStorage.getItem(storageKey+owner+':locations')||'null');locations=evidence?.owner===owner&&Array.isArray(evidence.items)?evidence.items.filter(p=>p&&typeof p.request_id==='string').slice(0,2000):[];observed=performance.now();node('clock-task').value=timeline().task;}
   else window.localStorage.removeItem(storageKey+owner);
  }catch{message('The saved clock could not be restored. Connect to verify your shift.');}
 }
 function timeline(){
  let state=lastVerified?(active?.status||'off_clock'):'unknown',task=active?.task||node('clock-task').value;
  let seconds=baseSeconds,cursor=Date.parse(snapshotAt||lastVerified)||Date.now(),taskStart=Date.parse(active?.segments?.at(-1)?.start)||cursor;
  for(const d of drafts){
   const when=Date.parse(effective(d));
   if(state==='working')seconds+=Math.max(0,(when-cursor)/1000);
   cursor=when;
   if(d.action==='clock_in'){seconds=0;taskStart=when;}
   if(d.action==='switch_task'||d.action==='break_end')taskStart=when;
   state=d.action==='break_start'?'on_break':d.action==='clock_out'?'off_clock':'working';
   if(d.task)task=d.task;
  }
  if(state==='working')seconds+=Math.max(0,(Date.now()-cursor)/1000);
  return {state,task,seconds:Math.floor(seconds),taskSeconds:state==='working'?Math.max(0,Math.floor((Date.now()-taskStart)/1000)):0};
 }
 const locationStatus=text('p','Location will be requested when you punch in.');locationStatus.id='clock-location';locationStatus.className='fine';locationStatus.setAttribute('role','status');node('clock-message').after(locationStatus);
 async function mutateLocations(owner,change){
  if(owner!==actorId)return;
  const store=storage(),key=storageKey+owner+':locations';
  try{
   if(!store||!navigator.locks?.request)throw Error('Device locking unavailable');
   await navigator.locks.request(key,()=>{
    if(owner!==actorId)return;
    let saved=null;try{saved=JSON.parse(store.getItem(key)||'null');}catch{}
    const list=saved?.owner===owner&&Array.isArray(saved.items)?saved.items.filter(p=>p&&typeof p.request_id==='string'):locations;
    const next=change(list);if(next.length)store.setItem(key,JSON.stringify({owner,items:next}));else store.removeItem(key);
    locations=next;
   });
  }catch{if(owner===actorId){storageFailed=true;locations=change(locations);locationStatus.textContent='Location evidence stays in this tab: device storage or locking unavailable. Download it before closing.';}}
 }
 async function flushLocations(){
  if(flushing||pending||!navigator.onLine||!locations.length)return;
  const owner=actorId;flushing=true;
  try{while(locations.length&&owner===actorId&&navigator.onLine){
   const batch=locations.slice(0,50),result=await window.wzosClock.api('/api/time/locations',{method:'POST',body:JSON.stringify({items:batch})});
   if(owner!==actorId)return;
   const sent=new Set(result.accepted);await mutateLocations(owner,list=>list.filter(p=>!sent.has(p.request_id)));persist();
   if(!batch.some(p=>sent.has(p.request_id)))break;
  }}catch(error){if(owner===actorId)locationStatus.textContent=error.status&&error.status<500?`Location upload needs review: ${error.message}. Download device records to preserve evidence.`:'Location upload pending. Saved evidence will retry when connected.';}
  finally{flushing=false;controls();}
 }
 async function captureLocation(event,commandId=null,task=timeline().task,shiftId=active?.id||null){
  const owner=actorId;if(!owner)return;
  if(locations.length>=2000){locationStatus.textContent='Location storage full. Connect to upload saved evidence.';return;}
  const item={request_id:crypto.randomUUID(),command_id:commandId,shift_id:shiftId,event,task,captured_at:new Date().toISOString()};
  const position=await new Promise(resolve=>{
   if(!navigator.onLine){resolve({unavailable:'offline'});return;}
   if(!navigator.geolocation){resolve({unavailable:'unavailable'});return;}
   navigator.geolocation.getCurrentPosition(p=>resolve({latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy}),
    e=>resolve({unavailable:e.code===1?'permission_denied':e.code===3?'timeout':'unavailable'}),{enableHighAccuracy:true,maximumAge:0,timeout:10000});
  });
  if(owner!==actorId)return;
  await mutateLocations(owner,list=>list.some(p=>p.request_id===item.request_id)?list:[...list,{...item,...position}]);if(owner!==actorId)return;persist();controls();
  locationStatus.textContent=position.unavailable?`Location ${position.unavailable.replaceAll('_',' ')} · time tracking continues.`:`Location captured at ${new Date(item.captured_at).toLocaleTimeString()} · accuracy ${Math.round(position.accuracy)} m.`;
  await flushLocations();
 }
 // Connection state is separate from the polite status message so it stays visible.
 const connection=text('p','Checking connection');connection.id='clock-connection';connection.className='clock-connection';connection.setAttribute('role','status');
 node('clock-message').before(connection);
 function setConnection(state,detail){connection.dataset.state=state;connection.textContent=detail;}
 // Admin filters and export detail, created here so shared markup stays unchanged.
 const employee=document.createElement('select');employee.id='clock-employee';employee.append(option('','All team members'));
 const employeeLabel=labelled('Employee',employee);employeeLabel.id='clock-employee-label';employeeLabel.hidden=true;
 const exportDetail=document.createElement('select');exportDetail.id='clock-export-detail';exportDetail.append(option('shifts','One row per shift'),option('intervals','Task and break intervals'));
 node('clock-to').parentNode?.after(employeeLabel);node('clock-export').before(labelled('Export detail',exportDetail));
 const locationHistory=document.createElement('details');locationHistory.className='clock-audit';
 const locationList=document.createElement('ul'),locationLoad=button('Load location history');
 locationHistory.append(text('summary','Location history'),text('p','Device-reported GPS evidence, including missing fixes. Team and employee filters also apply here.'),locationLoad,locationList);
 node('clock-page').after(locationHistory);
 locationLoad.onclick=async()=>{
  const owner=actorId;locationLoad.disabled=true;locationList.replaceChildren(text('li','Loading location evidence…'));
  try{const data=await window.wzosClock.api(`/api/time/locations?team=${node('clock-team').checked}${employee.value?'&employee_id='+encodeURIComponent(employee.value):''}`);
   if(owner!==actorId)return;
   locationList.replaceChildren(...data.items.map(p=>text('li',`${p.employee_id} · ${ACTIONS[p.event]||p.event} · ${TASKS[p.task]} · ${local(p.captured_at)} · ${p.unavailable?'Location '+p.unavailable.replaceAll('_',' '):`${p.latitude.toFixed(5)}, ${p.longitude.toFixed(5)} (±${Math.round(p.accuracy)} m)`} · device reported`)));
   if(!data.items.length)locationList.append(text('li','No location evidence recorded yet.'));
  }catch(error){if(owner===actorId)locationList.replaceChildren(text('li',error.message||'Location history unavailable.'));}
  finally{locationLoad.disabled=false;}
 };
 const filters=()=>`&team=${node('clock-team').checked}${employee.value?'&employee_id='+encodeURIComponent(employee.value):''}${node('clock-from').value?'&start_date='+node('clock-from').value:''}${node('clock-to').value?'&end_date='+node('clock-to').value:''}`;
 function controls(){
  const current=timeline(),hasShift=['working','on_break'].includes(current.state);
  const blocked=busy||(!loaded&&!lastVerified)||!!pending||drafts.length>=50, onBreak=current.state==='on_break';
  node('clock-in').hidden=hasShift;node('clock-out').hidden=!hasShift;node('clock-break').hidden=!hasShift;node('clock-switch').hidden=!hasShift;
  for(const id of ['clock-in','clock-out','clock-break'])node(id).disabled=blocked;
  node('clock-switch').disabled=blocked||onBreak||node('clock-task').value===current.task;
  node('clock-break').textContent=onBreak?'End break':'Start break';
  node('clock-order').disabled=blocked||hasShift;node('clock-note').disabled=blocked||hasShift;node('clock-task').disabled=blocked||onBreak;
  if(node('clock-order').parentNode)node('clock-order').parentNode.hidden=hasShift;
  if(node('clock-note').parentNode)node('clock-note').parentNode.hidden=hasShift;
  node('clock-retry').hidden=!pending;node('clock-retry').disabled=busy||!navigator.onLine;
  node('clock-refresh').disabled=busy;node('clock-team').disabled=busy;
  // Drafts are only for when confirmed clock actions are unavailable, which avoids duplicating live punches.
  const session=window.wzosClock.getSession();
  keep.disabled=!session||submitting||(loaded&&navigator.onLine)||drafts.length>=50;
  submit.disabled=!drafts.some(d=>!tooOld(d))||submitting||!loaded||!navigator.onLine;
  download.disabled=!drafts.length&&!locations.length;removeLast.disabled=!drafts.length||submitting;discard.disabled=!drafts.length||submitting;
 }
 function renderActive(data){
  // Preserve the original device timeline until offline evidence has been reconciled.
  if(!drafts.length){active=data.active;lastVerified=new Date().toISOString();snapshotAt=lastVerified;baseSeconds=active?.work_seconds||0;}
  loaded=true;observed=performance.now();persist();
  node('clock-state').textContent=active?active.status==='on_break'?'ON BREAK':'CLOCKED IN':'OFF THE CLOCK';
  node('clock-active-job').textContent=active?`${active.order_title||'Unassigned work'} · ${data.tasks[active.task]} · revision ${active.version}`:'';
  if(active){node('clock-task').value=timeline().task;node('clock-order').value=active.order_id||'';node('clock-note').value=active.note;}
  setConnection('online',drafts.length?'Online · device timeline pending admin verification':'Online · shift verified with the server at '+new Date(lastVerified).toLocaleTimeString());
  tick();controls();renderDrafts();flushLocations();
 }
 function tick(){const current=timeline();node('clock-timer').textContent=format(current.seconds);
  if(drafts.length){node('clock-state').textContent=current.state==='off_clock'?'CLOCKED OUT · DEVICE RECORD':current.state==='on_break'?'ON BREAK · DEVICE RECORD':'CLOCKED IN · DEVICE RECORD';node('clock-active-job').textContent=`${TASKS[current.task]} · ${format(current.taskSeconds)} on this task · pending admin review`;}
  else if(active)node('clock-active-job').textContent=`${active.order_title||'Unassigned work'} · ${TASKS[current.task]}${current.state==='working'?' · '+format(current.taskSeconds)+' on this task':''} · revision ${active.version}`;
 }
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
  try{
   const options=[option('','Unassigned')];let next=0;
   while(true){
    const jobs=await window.wzosClock.api(`/api/time/jobs?offset=${next}&limit=50`);
    if(epoch!==generation||scope(session)!==scope(window.wzosClock.getSession()))return;
    for(const row of jobs.items)options.push(option(row.id,row.title+(row.access_basis==='dispatched_summary'?' · assigned job':'')));
    next+=jobs.items.length;if(next>=jobs.total||!jobs.items.length)break;
   }
   node('clock-order').replaceChildren(...options);
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
  if(!retry&&(!navigator.onLine||!loaded||drafts.length)){
   if(busy||pending||!lastVerified||drafts.length>=50)return;
   const current=timeline();if(!allowed[current.state]?.includes(action))return;
   draftAction.value=action;draftTask.value=node('clock-task').value;draftNote.value=node('clock-note').value;draftWhen.value='';await keep.onclick();tick();controls();return;
  }
  if(!navigator.onLine){showOffline();return;}
  if(busy||(!retry&&(!loaded||pending)))return;
  const session=window.wzosClock.getSession();if(!session)return;
  if(!retry)pending={actor:scope(session),body:{request_id:crypto.randomUUID(),action,shift_id:active?.id||null,expected_version:active?.version||0,task:node('clock-task').value,...(action==='clock_in'?{order_id:node('clock-order').value||null,note:node('clock-note').value}:{})}};
  if(pending.actor!==scope(session))return;
  if(!retry)captureLocation(action,pending.body.request_id,pending.body.task);
  persist();busy=true;node('identity').disabled=true;controls();message('Saving clock action…');
  const owner=scope(session);
  try{await window.wzosClock.api('/api/time/commands',{method:'POST',body:JSON.stringify(pending.body)});if(owner!==actorId)return;pending=null;persist();message(session.restricted_staging?'Clock action saved in temporary cloud staging.':'Clock action saved locally.');document.dispatchEvent(new CustomEvent('wzos:time-context'));}
  catch(error){if(owner===actorId){if(error.status>=400&&error.status<500){pending=null;persist();message(error.message);}else message('Save not confirmed. Reconnect and retry the same action; duplicate records will be prevented.');}}
  finally{busy=false;node('identity').disabled=false;if(owner===actorId)await refresh();controls();}
 }
 node('clock-in').addEventListener('click',()=>send('clock_in'));node('clock-out').addEventListener('click',()=>send('clock_out'));
 node('clock-switch').addEventListener('click',()=>send('switch_task'));node('clock-break').addEventListener('click',()=>send(timeline().state==='on_break'?'break_end':'break_start'));
 node('clock-retry').addEventListener('click',()=>send(null,true));node('clock-refresh').addEventListener('click',refresh);node('clock-task').addEventListener('change',controls);
 node('clock-team').addEventListener('change',()=>{offset=0;if(!node('clock-team').checked)employee.value='';refresh();});node('clock-prev').addEventListener('click',()=>{offset=Math.max(0,offset-20);refresh();});node('clock-next').addEventListener('click',()=>{offset+=20;refresh();});
 employee.addEventListener('change',()=>{offset=0;if(employee.value)node('clock-team').checked=true;refresh();});
 for(const id of ['clock-from','clock-to'])node(id).onchange=()=>{offset=0;refresh();};
 node('clock-export').onclick=async()=>{const exportButton=node('clock-export');exportButton.disabled=true;try{const response=await fetch(`/api/time/export?detail=${exportDetail.value}${filters()}`,{headers:{'X-Preview-Actor':window.wzosClock.getSession().id,...await window.wzosAccount.headers()}});if(!response.ok){const error=await response.json();throw Error(typeof error.detail==='string'?error.detail:'Check export dates');}const name=(response.headers.get('content-disposition')||'').match(/filename="([^"]+)"/)?.[1]||'wzos-time.csv';const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){message(error.message);}finally{exportButton.disabled=false;}};
 document.addEventListener('wzos:clock-open',refresh);
 document.addEventListener('wzos:session',()=>{const id=scope(window.wzosClock.getSession());if(id!==actorId){actorId=id;pending=null;active=null;lastVerified=null;drafts=loadDrafts(id);locations=[];snapshotAt=null;baseSeconds=0;restore(id);membersLoaded=null;employee.replaceChildren(option('','All team members'));submitted.replaceChildren();renderDrafts();offset=0;node('clock-note').value='';node('clock-team').checked=false;node('clock-history').replaceChildren();node('clock-state').textContent='Loading clock';setConnection('checking','Checking connection');tick();message('');}refresh();});
  window.addEventListener('beforeunload',event=>{if(pending||submitting||draftWrites||(drafts.length&&persistence!=='device')||(storageFailed&&locations.length)){event.preventDefault();event.returnValue='';}});
 // Another open tab for the same account changed the saved drafts.
 window.addEventListener('storage',event=>{if(actorId&&event.key===STORE+actorId&&persistence==='device'){drafts=loadDrafts(actorId);renderDrafts();tick();}});
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
 draftPanel.append(text('h2','Device records & review'),text('p','Use the regular clock buttons offline after your shift loads. Device times and task changes are unverified estimates. Submit drafts after reconnecting for admin review; submission does not change attendance. Once submitted, the timer returns to the confirmed server shift; review status stays below.'),storageNote,
  labelled('What happened',draftAction),labelled('Task',draftTask),labelled('When, if earlier than now (device time, optional)',draftWhen),labelled('Note',draftNote),draftActions,draftList,text('h3','Submitted for review'),submitted);
 node('clock-view').append(draftPanel);
 const effective=d=>d.stated_at||d.captured_at;
 function expected(list=drafts){
  // Replays drafts over the last verified status so impossible or duplicate sequences are refused.
  let state=lastVerified?(active?active.status:'off_clock'):'unknown', task=active?.task||null;
  for(const d of list){state=d.action==='break_start'?'on_break':d.action==='clock_out'?'off_clock':'working';if(d.task&&d.action!=='break_start')task=d.task;}
  return {state,task};
 }
 const allowed={off_clock:['clock_in'],working:['break_start','switch_task','clock_out'],on_break:['break_end','clock_out']};
 function renderDrafts(){
  draftList.replaceChildren();
  storageNote.dataset.persistence=persistence;
  storageNote.textContent=persistence==='device'?'Drafts are saved on this device for your account and organization until you submit or discard them, even if you close the app. Other people using this device cannot open them in WZOS, but keep the device secure.'
   :'This browser cannot safely save draft changes (storage blocked or cross-tab locking unavailable). They stay only in this open tab, so submit or download them before you close it or sign out.';
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
 keep.onclick=async()=>{
  const session=window.wzosClock.getSession();if(!session)return;
  const owner=scope(session), now=new Date(), stated=draftWhen.value?new Date(draftWhen.value):null, action=draftAction.value;
  if(stated&&(isNaN(stated)||stated>now)){message('The earlier time must be a valid time that is not in the future.');return;}
  const draft={request_id:crypto.randomUUID(),action,task:['clock_in','switch_task'].includes(action)?draftTask.value:null,note:draftNote.value.trim(),captured_at:now.toISOString(),...(stated?{stated_at:stated.toISOString()}:{}),order_id:action==='clock_in'?node('clock-order').value||null:null,known_shift_id:lastVerified?active?.id||null:null,known_version:lastVerified?active?.version??null:null};
  let added=false;
  await mutate(owner,list=>{
   if(owner!==actorId)return list;
   const {state,task}=expected(list);
   if(state!=='unknown'&&!allowed[state].includes(action)){message(`${ACTIONS[action]} does not follow your ${list.length?'last draft':'last confirmed status'}. Drafts must follow the order things happened.`);return list;}
   if(action==='switch_task'&&task===draft.task){message('Choose a different task to record a task switch.');return list;}
   if(list.length&&(stated||now)<new Date(effective(list.at(-1)))){message('Drafts must be in time order. Check the earlier time.');return list;}
   added=true;return [...list,draft];
  });
  if(owner!==actorId)return;
  renderDrafts();tick();controls();if(added){persist();captureLocation(action,draft.request_id,draft.task||timeline().task);draftNote.value='';draftWhen.value='';message(`Draft ${persistence==='device'?'saved on this device':'kept in this tab only'}. It has not changed your shift. Submit it for review when you reconnect.`);}
 };
 removeLast.onclick=async()=>{const owner=actorId,last=drafts.at(-1);if(!last)return;await mutate(owner,list=>list.filter(d=>d.request_id!==last.request_id));if(owner!==actorId)return;renderDrafts();tick();controls();message('Removed the last draft.');};
 discard.onclick=async()=>{if(!drafts.length||submitting||!window.confirm?.('Discard all unsubmitted offline drafts on this device? This cannot be undone.'))return;const owner=actorId,shown=new Set(drafts.map(d=>d.request_id));await mutate(owner,list=>list.filter(d=>!shown.has(d.request_id)));if(owner!==actorId)return;renderDrafts();message('Offline drafts discarded. Nothing was sent to your admin.');};
 submit.onclick=async()=>{
  const session=window.wzosClock.getSession();if(!session||!drafts.length||!navigator.onLine||submitting)return;
  const owner=scope(session), batch=drafts.filter(d=>!tooOld(d));if(!batch.length)return;
  submitting=true;controls();message('Submitting drafts for admin review…');
  try{
   const result=await window.wzosClock.api('/api/time/offline-submissions',{method:'POST',body:JSON.stringify({device_submitted_at:new Date().toISOString(),drafts:batch.map(outgoing)})});
   const sent=new Set(batch.map(d=>d.request_id));await mutate(owner,list=>list.filter(d=>!sent.has(d.request_id)));
   if(owner!==scope(window.wzosClock.getSession()))return;
   message(`${result.items.length} draft${result.items.length===1?'':'s'} submitted for admin review. Your recorded shift has not changed.`);loadSubmissions(session);
  }catch(error){
   const sent=new Set(batch.map(d=>d.request_id)), uncertain=!(error.status&&error.status<500);
   // Mark only drafts still saved; a draft another tab already submitted is not re-created.
   if(uncertain)await mutate(owner,list=>list.map(d=>sent.has(d.request_id)?{...d,submission:'unconfirmed'}:d));
   if(owner!==scope(window.wzosClock.getSession()))return;
   const kept=persistence==='device'?'on this device':'in this tab';
   if(!uncertain){message(`${error.message} Your drafts are still kept ${kept}.`);}
   else{message(`Submission not confirmed. Your drafts are still kept ${kept}, and submitting again will not create duplicates.`);}
  }
  finally{submitting=false;renderDrafts();}
 };
 download.onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({type:'WZOS offline attendance drafts',automatic_sync:false,time_basis:'device_estimate_unverified',drafts:drafts.map(outgoing),location_evidence:locations},null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='wzos-offline-drafts.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 async function loadSubmissions(session){
  try{
   const data=await window.wzosClock.api('/api/time/offline-submissions?status=all');
   if(scope(session)!==scope(window.wzosClock.getSession()))return;
   submitted.replaceChildren(...data.items.slice(-10).reverse().map(s=>text('li',`${ACTIONS[s.action]} · estimated ${local(s.estimated_at)} · ${STATUS[s.status]||s.status}${s.resolution_reason&&s.status!=='pending'?' · '+s.resolution_reason:''}`)));
   if(!data.items.length)submitted.append(text('li','Nothing submitted yet.'));
  }catch(error){/* Status list is informational; the clock remains usable. */}
 }
 function showOffline(){loaded=false;node('clock-state').textContent=lastVerified?'OFFLINE · LAST KNOWN STATUS':'OFFLINE · STATUS NOT LOADED';setConnection('offline',lastVerified?'Offline · device time estimate · clock and task records stay on this device.':'Offline · connect once to load your shift.');message(lastVerified?'Keep using the clock. Device records need admin verification when connected.':'Connect once to load your shift.');tick();controls();}
 window.addEventListener('offline',()=>{generation++;showOffline();});
 window.addEventListener('online',()=>{setConnection('reconnecting','Reconnected · checking your current shift with the server');message(drafts.length?`Connection restored. You have ${drafts.length} offline draft${drafts.length===1?'':'s'} pending verification. Submit them for admin review.`:'Connection restored. Checking your current shift.');
  refresh().then(()=>{if(['working','on_break'].includes(timeline().state))captureLocation('reconnect');flushLocations();});});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden&&navigator.onLine&&['working','on_break'].includes(timeline().state))captureLocation('reconnect');});
 setInterval(()=>{if(!locationBusy&&['working','on_break'].includes(timeline().state)){locationBusy=true;captureLocation('interval').finally(()=>{locationBusy=false;});}},5*60*1000);
 renderDrafts();
 setInterval(tick,1000);controls();
})();
