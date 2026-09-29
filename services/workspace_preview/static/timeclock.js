"use strict";
(() => {
 const node=id=>document.getElementById(id), text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 let active=null, loaded=false, busy=false, generation=0, offset=0, observed=0, baseSeconds=0, pending=null, actorId=null, lastVerified=null, offlineNotes=[];
 const scope=session=>session?`${session.organization_id}:${session.id}`:null;
 const format=n=>[Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(v=>String(v).padStart(2,'0')).join(':');
 const message=value=>{node('clock-message').textContent=value;};
 const dateQuery=()=>`${node('clock-from').value?'&start_date='+node('clock-from').value:''}${node('clock-to').value?'&end_date='+node('clock-to').value:''}`;
 function controls(){
  const blocked=busy||!loaded||!!pending||!navigator.onLine, onBreak=active?.status==='on_break';
  node('clock-in').hidden=!!active;node('clock-out').hidden=!active;node('clock-break').hidden=!active;node('clock-switch').hidden=!active;
  for(const id of ['clock-in','clock-out','clock-break'])node(id).disabled=blocked;
  node('clock-switch').disabled=blocked||onBreak||node('clock-task').value===active?.task;
  node('clock-break').textContent=onBreak?'End break':'Start break';
  node('clock-order').disabled=blocked||!!active;node('clock-note').disabled=blocked||!!active;node('clock-task').disabled=blocked||onBreak;
  node('clock-retry').hidden=!pending;node('clock-retry').disabled=busy||!navigator.onLine;
  node('clock-refresh').disabled=busy;node('clock-team').disabled=busy;
 }
 function renderActive(data){
  active=data.active;loaded=true;lastVerified=new Date().toISOString();observed=performance.now();baseSeconds=active?.work_seconds||0;
  node('clock-state').textContent=active?active.status==='on_break'?'ON BREAK':'CLOCKED IN':'OFF THE CLOCK';
  node('clock-active-job').textContent=active?`${active.order_title||'Unassigned work'} · ${data.tasks[active.task]} · revision ${active.version}`:'';
  if(active){node('clock-task').value=active.task;node('clock-order').value=active.order_id||'';node('clock-note').value=active.note;}
  tick();controls();
 }
 function tick(){node('clock-timer').textContent=format(baseSeconds+(active?.status==='working'?Math.max(0,Math.floor((performance.now()-observed)/1000)):0));}
 async function refresh(){
  const session=window.wzosClock.getSession();if(!session)return;
  if(!navigator.onLine){showOffline();return;}
  const epoch=++generation;loaded=false;controls();
  node('clock-team-label').hidden=session.role!=='admin';if(session.role!=='admin')node('clock-team').checked=false;
  const options=[text('option','Unassigned')];options[0].value='';for(const row of window.wzosClock.getOrders()){const o=text('option',row.title);o.value=row.id;options.push(o);}node('clock-order').replaceChildren(...options);
  try{
   const [state,history]=await Promise.all([window.wzosClock.api('/api/time/status'),window.wzosClock.api(`/api/time/entries?offset=${offset}&team=${node('clock-team').checked}${dateQuery()}`)]);
   if(epoch!==generation||scope(session)!==scope(window.wzosClock.getSession()))return;
   renderActive(state);node('clock-history').replaceChildren();
   for(const entry of history.items){const article=document.createElement('article');article.className='clock-entry';article.append(text('strong',entry.order_title||'Unassigned work'),text('p',`${entry.employee_id} · ${new Date(entry.clock_in).toLocaleString()} → ${entry.clock_out?new Date(entry.clock_out).toLocaleString():'Active'}`),text('p',`${format(entry.work_seconds)} work · ${format(entry.break_seconds)} breaks`));
    const details=document.createElement('details');details.append(text('summary',`${entry.segments.length} task intervals`));for(const segment of entry.segments)details.append(text('p',`${state.tasks[segment.task]} · ${new Date(segment.start).toLocaleTimeString()} → ${segment.end?new Date(segment.end).toLocaleTimeString():'Active'}`));article.append(details);node('clock-history').append(article);
   }
   if(!history.items.length)node('clock-history').append(text('p','No time entries yet.'));
   node('clock-prev').disabled=offset===0;node('clock-next').disabled=offset+history.limit>=history.total;
   node('clock-page').textContent=`${history.total} records · showing ${history.items.length?offset+1:0}–${offset+history.items.length}. Times shown in your device timezone.`;
  }catch(error){if(epoch===generation){loaded=false;if(!error.status){showOffline();}else{active=null;lastVerified=null;baseSeconds=0;tick();node('clock-state').textContent='CLOCK STATUS UNAVAILABLE';node('clock-history').replaceChildren();message(error.message);}}}
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
 node('clock-team').addEventListener('change',()=>{offset=0;refresh();});node('clock-prev').addEventListener('click',()=>{offset=Math.max(0,offset-20);refresh();});node('clock-next').addEventListener('click',()=>{offset+=20;refresh();});
 for(const id of ['clock-from','clock-to'])node(id).onchange=()=>{offset=0;refresh();};
 node('clock-export').onclick=async()=>{const button=node('clock-export');button.disabled=true;try{const response=await fetch(`/api/time/export?team=${node('clock-team').checked}${dateQuery()}`,{headers:{'X-Preview-Actor':window.wzosClock.getSession().id,...await window.wzosAccount.headers()}});if(!response.ok){const error=await response.json();throw Error(typeof error.detail==='string'?error.detail:'Check export dates');}const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='wzos-test-time.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){message(error.message);}finally{button.disabled=false;}};
 document.addEventListener('wzos:clock-open',refresh);
 document.addEventListener('wzos:session',()=>{const id=scope(window.wzosClock.getSession());if(id!==actorId){actorId=id;pending=null;active=null;lastVerified=null;offlineNotes=[];renderNotes();baseSeconds=0;offset=0;node('clock-note').value='';node('clock-team').checked=false;node('clock-history').replaceChildren();node('clock-state').textContent='Loading clock';tick();message('');}refresh();});
 window.addEventListener('beforeunload',event=>{if(pending||offlineNotes.length){event.preventDefault();event.returnValue='';}});
 const offlinePanel=document.createElement('section');offlinePanel.className='panel';
 const noteTitle=text('h3','Offline time notes'),notice=text('p','While disconnected, keep device-timestamped notes in this open tab and download them for review. Notes are not clock punches, payroll records or automatically synchronized. Download before closing or signing out.');
 const noteInput=document.createElement('textarea');noteInput.maxLength=1000;noteInput.setAttribute('aria-label','Offline time note');noteInput.placeholder='Describe the clock-in, break, task change or clock-out to review';
 const add=text('button','Keep time note'),download=text('button','Download time notes'),noteList=document.createElement('div');add.type=download.type='button';add.className=download.className='secondary';
 offlinePanel.append(noteTitle,notice,noteInput,add,download,noteList);node('clock-message').after(offlinePanel);
 function renderNotes(){noteList.replaceChildren();for(const entry of offlineNotes)noteList.append(text('p',entry.device_time+' · '+entry.note));download.disabled=!offlineNotes.length;}
 add.onclick=()=>{if(!window.wzosClock.getSession()||!noteInput.value.trim())return;if(offlineNotes.length>=50){message('Download these 50 notes before starting another set.');return;}offlineNotes.push({scope:scope(window.wzosClock.getSession()),device_time:new Date().toISOString(),note:noteInput.value.trim(),record_type:'unverified_offline_note'});noteInput.value='';renderNotes();message('Time note kept in this tab only. Download it before leaving; it has not changed your shift.');};
 download.onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({type:'WZOS unverified time notes',automatic_sync:false,notes:offlineNotes},null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='wzos-time-notes.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 function showOffline(){loaded=false;node('clock-state').textContent=lastVerified?'CONNECTION UNAVAILABLE — LAST KNOWN STATUS':'CONNECTION UNAVAILABLE — STATUS NOT LOADED';message(lastVerified?'Last confirmed '+new Date(lastVerified).toLocaleString()+'. Timer is an estimate; clock changes require reconnection.':'Connect once to load your shift. You can keep and download unverified time notes.');controls();}
 window.addEventListener('offline',()=>{generation++;showOffline();});
 window.addEventListener('online',()=>{message('Connection restored. Checking current shift; offline notes are not sent automatically.');refresh();});
 renderNotes();
 setInterval(tick,1000);controls();
})();
