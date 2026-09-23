"use strict";
(() => {
 const node=id=>document.getElementById(id), text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 let active=null, loaded=false, busy=false, generation=0, offset=0, observed=0, baseSeconds=0, pending=null, actorId=null;
 const format=n=>[Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(v=>String(v).padStart(2,'0')).join(':');
 const message=value=>{node('clock-message').textContent=value;};
 const dateQuery=()=>`${node('clock-from').value?'&start_date='+node('clock-from').value:''}${node('clock-to').value?'&end_date='+node('clock-to').value:''}`;
 function controls(){
  const blocked=busy||!loaded||!!pending, onBreak=active?.status==='on_break';
  node('clock-in').hidden=!!active;node('clock-out').hidden=!active;node('clock-break').hidden=!active;node('clock-switch').hidden=!active;
  for(const id of ['clock-in','clock-out','clock-break'])node(id).disabled=blocked;
  node('clock-switch').disabled=blocked||onBreak||node('clock-task').value===active?.task;
  node('clock-break').textContent=onBreak?'End break':'Start break';
  node('clock-order').disabled=blocked||!!active;node('clock-note').disabled=blocked||!!active;node('clock-task').disabled=blocked||onBreak;
  node('clock-retry').hidden=!pending;node('clock-retry').disabled=busy;
  node('clock-refresh').disabled=busy;node('clock-team').disabled=busy;
 }
 function renderActive(data){
  active=data.active;loaded=true;observed=performance.now();baseSeconds=active?.work_seconds||0;
  node('clock-state').textContent=active?active.status==='on_break'?'ON BREAK':'CLOCKED IN':'OFF THE CLOCK';
  node('clock-active-job').textContent=active?`${active.order_title||'Unassigned work'} · ${data.tasks[active.task]} · revision ${active.version}`:'';
  if(active){node('clock-task').value=active.task;node('clock-order').value=active.order_id||'';node('clock-note').value=active.note;}
  tick();controls();
 }
 function tick(){node('clock-timer').textContent=format(baseSeconds+(active?.status==='working'?Math.max(0,Math.floor((performance.now()-observed)/1000)):0));}
 async function refresh(){
  const session=window.wzosClock.getSession();if(!session)return;
  const epoch=++generation;loaded=false;controls();
  node('clock-team-label').hidden=session.role!=='admin';if(session.role!=='admin')node('clock-team').checked=false;
  const options=[text('option','Unassigned')];options[0].value='';for(const row of window.wzosClock.getOrders()){const o=text('option',row.title);o.value=row.id;options.push(o);}node('clock-order').replaceChildren(...options);
  try{
   const [state,history]=await Promise.all([window.wzosClock.api('/api/time/status'),window.wzosClock.api(`/api/time/entries?offset=${offset}&team=${node('clock-team').checked}${dateQuery()}`)]);
   if(epoch!==generation||session.id!==window.wzosClock.getSession()?.id)return;
   renderActive(state);node('clock-history').replaceChildren();
   for(const entry of history.items){const article=document.createElement('article');article.className='clock-entry';article.append(text('strong',entry.order_title||'Unassigned work'),text('p',`${entry.employee_id} · ${new Date(entry.clock_in).toLocaleString()} → ${entry.clock_out?new Date(entry.clock_out).toLocaleString():'Active'}`),text('p',`${format(entry.work_seconds)} work · ${format(entry.break_seconds)} breaks`));
    const details=document.createElement('details');details.append(text('summary',`${entry.segments.length} task intervals`));for(const segment of entry.segments)details.append(text('p',`${state.tasks[segment.task]} · ${new Date(segment.start).toLocaleTimeString()} → ${segment.end?new Date(segment.end).toLocaleTimeString():'Active'}`));article.append(details);node('clock-history').append(article);
   }
   if(!history.items.length)node('clock-history').append(text('p','No time entries yet.'));
   node('clock-prev').disabled=offset===0;node('clock-next').disabled=offset+history.limit>=history.total;
   node('clock-page').textContent=`${history.total} records · showing ${history.items.length?offset+1:0}–${offset+history.items.length}. Times shown in your device timezone.`;
  }catch(error){if(epoch===generation){loaded=false;active=null;baseSeconds=0;tick();node('clock-state').textContent='CLOCK STATUS UNAVAILABLE';node('clock-history').replaceChildren();message(error.message);}}
  finally{if(epoch===generation)controls();}
 }
 async function send(action,retry=false){
  if(busy||(!retry&&(!loaded||pending)))return;
  const session=window.wzosClock.getSession();if(!session)return;
  if(!retry)pending={actor:session.id,body:{request_id:crypto.randomUUID(),action,shift_id:active?.id||null,expected_version:active?.version||0,task:node('clock-task').value,...(action==='clock_in'?{order_id:node('clock-order').value||null,note:node('clock-note').value}:{})}};
  if(pending.actor!==session.id)return;
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
 document.addEventListener('wzos:session',()=>{const id=window.wzosClock.getSession()?.id;if(id!==actorId){actorId=id;pending=null;active=null;baseSeconds=0;offset=0;node('clock-note').value='';node('clock-team').checked=false;node('clock-history').replaceChildren();node('clock-state').textContent='Loading clock';tick();message('');}refresh();});
 window.addEventListener('beforeunload',event=>{if(pending){event.preventDefault();event.returnValue='';}});
 setInterval(tick,1000);controls();
})();
