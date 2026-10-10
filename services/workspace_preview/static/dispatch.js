"use strict";
// Enterprise dispatch inside Messaging: admins plan, review and approve; members respond.
// Proposals come from deterministic server rules. Nothing is sent until an admin approves.
(() => {
 const api=(...a)=>window.wzosClock.api(...a);
 const node=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;return n;};
 const button=(text,cls='secondary')=>{const b=node('button',text);b.type='button';b.className=cls;return b;};
 const labelled=(caption,control)=>{const l=node('label',caption);l.append(control);return l;};
 const local=value=>new Date(value).toLocaleString();
 const inputTime=value=>{if(!value)return '';const d=new Date(value);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);};
 const STATUS={draft:'Draft — not sent',sent:'Approved and sent',superseded:'Replaced by a newer plan',cancelled:'Cancelled'};
 const ASSIGNMENT={sent:'Confirmation needed',accepted:'Receipt confirmed',declined:'Declined',cancelled:'Cancelled',replaced:'Replaced by a newer plan'};
 let selected='', notice=null, assignmentOffset=0, assignmentPhase='upcoming', assignmentEpoch=0;
 const say=text=>{if(notice)notice.textContent=text;};
 async function act(control,work,done,refresh){control.disabled=true;try{await work();await refresh();say(done);}catch(error){say(error.message);}finally{control.disabled=false;}}

 async function memberPanel(root,current){
  const data=await api('/api/dispatch/my-assignments?phase='+assignmentPhase+'&offset='+assignmentOffset);if(!current())return;
  const panel=node('section');panel.className='report-section panel';panel.append(node('h2','My assignments'));
  const tabs=node('div');tabs.className='clock-actions';
  for(const [phase,title] of [['upcoming','Coming up'],['finished','Finished / cancelled'],['all','All jobs']]){const b=button(title);b.setAttribute('aria-pressed',String(phase===assignmentPhase));b.onclick=()=>{assignmentPhase=phase;assignmentOffset=0;rerender(root,current).catch(error=>say(error.message));};tabs.append(b);}
  const reload=button('Refresh jobs');reload.onclick=()=>act(reload,()=>Promise.resolve(),'Jobs refreshed.',()=>rerender(root,current));tabs.append(reload);panel.append(tabs);
  if(!data.items.length)panel.append(node('p','No jobs in this list.'));
  for(const item of data.items){const card=node('details');card.className='assignment-card';
   const summary=node('summary');summary.append(node('strong',item.order_title),node('span',`${local(item.starts_at)} · ${ASSIGNMENT[item.status]||item.status}`));card.append(summary);
   const body=node('div');body.className='assignment-body';
   const details=node('dl');
   for(const [label,value] of [['Location',item.address],['Start time',local(item.starts_at)],['Estimated finish',local(item.ends_at)],['Your role',item.role_title],['Client company',item.client_company],['Client point of contact',item.client_contact_name],['Contact phone',item.client_contact_phone]])details.append(node('dt',label),node('dd',value||'Not provided'));
   body.append(details);const direction=window.WzosNavigation.link(item.address);if(direction)body.append(direction);
   body.append(node('h3','Assigned crew'));const crew=node('ul');for(const person of item.crew||[])crew.append(node('li',`${person.name} · ${person.role_title}`));if(!crew.children.length)crew.append(node('li','Crew details unavailable for this historical assignment.'));body.append(crew);
   body.append(node('h3','Dispatcher notes'),node('p',item.notes||'No additional instructions.'));
   body.append(node('p','Status: '+(ASSIGNMENT[item.status]||item.status)+(item.responded_at?' · '+local(item.responded_at):'')));
   if(item.snapshot_state!=='dispatched')body.append(node('p','Historical dispatched details were not preserved; the address/title shown may reflect later edits. Contact your dispatcher to confirm.'));
   if(item.status==='sent'){const row=node('div');row.className='clock-actions';
    for(const [response,label] of [['accepted','Confirm receipt'],['declined','Decline']]){const b=button(label,response==='accepted'?'primary':'secondary');
     b.onclick=()=>act(b,()=>api('/api/dispatch/assignments/'+item.id+'/respond',{method:'POST',body:JSON.stringify({response})}),response==='accepted'?'Receipt confirmed. Your admin can see the confirmation.':'Assignment declined. Your admin will see your response.',async()=>{await rerender(root,current);await updateNotifications();});row.append(b);}
    body.append(row);}card.append(body);
   panel.append(card);}
  const pages=node('div');pages.className='clock-actions';const prev=button('Previous jobs'),next=button('Next jobs');prev.disabled=assignmentOffset===0;next.disabled=assignmentOffset+data.limit>=data.total;
  prev.onclick=()=>{assignmentOffset=Math.max(0,assignmentOffset-data.limit);rerender(root,current).catch(error=>say(error.message));};next.onclick=()=>{assignmentOffset+=data.limit;rerender(root,current).catch(error=>say(error.message));};pages.append(prev,next);panel.append(node('p',`${data.total} job${data.total===1?"":"s"} · times shown in your device time zone`),pages);
  return panel;
 }

 function requirementsForm(state,refresh){
  const req=state.requirements, form=node('form');form.onsubmit=e=>e.preventDefault();
  const start=node('input'),end=node('input');start.type=end.type='datetime-local';start.value=inputTime(req?.starts_at);end.value=inputTime(req?.ends_at);
  const role=req?.roles?.[0]||{id:'crew',title:'Crew member',count:1,qualification_ids:[]};
  const title=node('input'),count=node('input'),quals=node('input'),notes=node('textarea');title.value=role.title;count.type='number';count.min=1;count.max=20;count.value=role.count;quals.value=(role.qualification_ids||[]).join(', ');notes.value=req?.notes||'';notes.maxLength=1000;
  const company=node('input'),contact=node('input'),phone=node('input');company.maxLength=200;contact.maxLength=120;phone.maxLength=80;company.value=req?.client_company||'';contact.value=req?.client_contact_name||'';phone.value=req?.client_contact_phone||'';phone.type='tel';
  quals.placeholder='Qualification identifiers, e.g. flagger';
  const save=button('Save staffing requirements','primary');
  if(req?.roles?.length>1)form.append(node('p',`This order has ${req.roles.length} roles; only the first is editable here. Other roles are kept.`));
  form.append(labelled('Job starts (your time zone)',start),labelled('Estimated finish',end),labelled('Client company',company),labelled('Client point of contact',contact),labelled('Client contact phone',phone),labelled('Role',title),labelled('People needed',count),labelled('Required qualification identifiers (comma separated)',quals),labelled('Dispatcher notes (visible to assigned employees)',notes),save);
  save.onclick=()=>{if(!start.value||!end.value){say('Enter the job start and end.');return;}
   const first={id:(role.id||'crew'),title:title.value.trim(),count:Number(count.value),qualification_ids:quals.value.split(',').map(q=>q.trim()).filter(Boolean)};
   const body={expected_version:req?.version||0,starts_at:new Date(start.value).toISOString(),ends_at:new Date(end.value).toISOString(),roles:[first,...(req?.roles||[]).slice(1)],notes:notes.value,client_company:company.value,client_contact_name:contact.value,client_contact_phone:phone.value};
   act(save,()=>api('/api/dispatch/orders/'+selected+'/requirements',{method:'PUT',body:JSON.stringify(body)}),'Staffing requirements saved.',refresh);};
  return form;
 }

 function planCard(plan,reasons,refresh,roles){
  const card=node('article');card.className='report-section panel';
  card.append(node('h3',`${STATUS[plan.status]||plan.status} · revision ${plan.version} · ${local(plan.created_at)}`));
  if(plan.stale)card.append(node('p','The work order or its requirements changed after this plan. Create a new proposal before sending.'));
  const why=codes=>codes.map(c=>reasons[c]||c).join('; ');
  if(plan.status==='draft'){
   // Candidate review: eligible people are pre-selected; warnings need a written justification.
   const picks=new Map(plan.assignments.map(a=>[a.role_id+':'+a.user_id,a.override_reason||'']));
   for(const [roleId,candidates] of Object.entries(plan.candidates)){
    card.append(node('h4','Role: '+(roles[roleId]||roleId)));const list=node('ul');
    for(const c of candidates){const item=node('li'),box=node('input'),label=node('label');box.type='checkbox';Object.assign(box.style,{width:'auto',display:'inline-block',marginRight:'.5rem'});
     const key=roleId+':'+c.user_id;box.checked=picks.has(key);box.disabled=c.blockers.length>0;
     label.append(box,`${c.name} — ${c.blockers.length?'Not eligible: '+why(c.blockers):c.warnings.length?'Needs review: '+why(c.warnings):'Eligible'} · availability ${c.availability} · ${c.recent_assignments} nearby assignments`);
     item.append(label);
     let reason=null;if(c.warnings.length&&!c.blockers.length){reason=node('input');reason.placeholder='Override justification (required to assign)';reason.maxLength=500;reason.value=picks.get(key)||'';reason.oninput=()=>{if(box.checked)picks.set(key,reason.value);};item.append(reason);}
     box.onchange=()=>{if(box.checked)picks.set(key,reason?.value||'');else picks.delete(key);};
     list.append(item);}
    card.append(list);}
   if(plan.unfilled.length)card.append(node('p','Unfilled: '+plan.unfilled.map(u=>`${u.title} needs ${u.missing} more`).join('; ')));
   const actions=node('div');actions.className='clock-actions';
   const saveEdit=button('Save plan changes'),approve=button('Approve and send assignments','primary'),cancel=button('Discard plan');
   saveEdit.onclick=()=>act(saveEdit,()=>api('/api/dispatch/plans/'+plan.id,{method:'PUT',body:JSON.stringify({expected_version:plan.version,assignments:[...picks].map(([key,override_reason])=>{const [role_id,user_id]=key.split(/:(.+)/);return {role_id,user_id,override_reason};})})}),'Plan saved. Review it, then approve to send.',refresh);
   approve.onclick=()=>{if(!confirm(`Send ${plan.assignments.length} saved assignment(s) now? Members receive a WZOS message, and a text if they enabled texts.`))return;act(approve,()=>api('/api/dispatch/plans/'+plan.id+'/approve',{method:'POST',body:JSON.stringify({request_id:plan._approval||(plan._approval=crypto.randomUUID()),expected_version:plan.version})}),'Assignments sent.',refresh);};
   cancel.onclick=()=>act(cancel,()=>api('/api/dispatch/plans/'+plan.id+'/cancel',{method:'POST',body:JSON.stringify({expected_version:plan.version,reason:'Discarded draft'})}),'Draft discarded.',refresh);
   approve.disabled=!plan.assignments.length||plan.stale;
   card.append(node('p',`Saved plan: ${plan.assignments.length?plan.assignments.map(a=>a.name+(a.override_reason?' (override: '+a.override_reason+')':'')).join(', '):'nobody assigned yet'}. Save changes before approving.`),actions);actions.append(saveEdit,approve,cancel);
  }else{
   const list=node('ul');for(const a of plan.sent_assignments){const name=plan.assignments.find(x=>x.user_id===a.user_id)?.name||a.user_id;list.append(node('li',`${name} · ${ASSIGNMENT[a.status]||a.status}${a.response_note?' · "'+a.response_note+'"':''}${a.sms?' · text: '+a.sms.status+(a.sms.reason?' ('+a.sms.reason+')':''):''}`));}
   card.append(list);
   if(plan.status==='sent'){const cancel=button('Cancel these assignments');cancel.onclick=()=>{const reason=prompt('Reason sent to the assigned people:');if(!reason||reason.trim().length<3)return;act(cancel,()=>api('/api/dispatch/plans/'+plan.id+'/cancel',{method:'POST',body:JSON.stringify({expected_version:plan.version,reason:reason.trim()})}),'Assignments cancelled and people notified.',refresh);};card.append(cancel);}
  }
  return card;
 }

 async function adminPanel(root,current){
  const panel=node('section');panel.className='report-section panel';panel.append(node('h2','Dispatch (Enterprise)'));
  panel.append(node('p','Choose a work order, set staffing needs, then propose assignments. Proposals use verified qualifications, recorded availability and existing assignments. Missing information is never treated as eligible. Nothing is sent until you approve.'));
  const orders=window.wzosClock.getOrders(),picker=node('select');picker.append(Object.assign(node('option','Select a work order'),{value:''}));
  for(const o of orders){const opt=node('option',o.title);opt.value=o.id;picker.append(opt);}picker.value=selected;
  panel.append(labelled('Work order',picker));const body=node('div');panel.append(body);
  const refresh=async()=>{body.replaceChildren();if(!selected)return;
   const state=await api('/api/dispatch/orders/'+selected);if(!current()||state.order_id!==selected)return;
   body.append(requirementsForm(state,refresh));
   if(state.requirements){const propose=button('Propose assignments','primary');propose.onclick=()=>act(propose,()=>api('/api/dispatch/orders/'+selected+'/proposals',{method:'POST'}),'Proposal ready for review. Nothing has been sent.',refresh);body.append(propose);}
   const roles=Object.fromEntries((state.requirements?.roles||[]).map(r=>[r.id,r.title]));for(const plan of state.plans)body.append(planCard(plan,state.reasons,refresh,roles));};
  picker.onchange=()=>{selected=picker.value;refresh().catch(error=>say(error.message));};
  await refresh();
  return panel;
 }

 async function rerender(root,current){const host=root.querySelector('[data-dispatch]');if(!host)return;let fresh;if(host.dataset.assignmentsOnly){fresh=node('div');fresh.dataset.dispatch='1';fresh.dataset.assignmentsOnly='1';const panel=await memberPanel(root,current);if(panel)fresh.append(panel);}else fresh=await build(root,current);if(fresh&&current())host.replaceWith(fresh);}
 async function build(root,current){
  const session=window.wzosClock.getSession();if(session?.edition!=='enterprise')return null;
  const wrap=node('div');wrap.dataset.dispatch='1';
  const mine=await memberPanel(root,current);if(mine)wrap.append(mine);
  if(session.role==='admin'){const admin=await adminPanel(root,current);if(admin)wrap.append(admin);}
  return wrap;
 }
 // Called by the Messaging view; renders nothing for Core organizations.
 window.wzosDispatch={async render(root,current,status){notice=status;try{const panel=await build(root,current);if(panel&&current())root.append(panel);}catch(error){if(current())say(error.message);}}};
 async function showAssignments(){
  const epoch=++assignmentEpoch,root=document.getElementById('team-content');root.replaceChildren();document.getElementById('team-title').textContent='My jobs';notice=document.getElementById('team-notice');notice.textContent='Loading assignments…';
  const session=window.wzosClock.getSession(),scope=session?.organization_id+':'+session?.id;
  const current=()=>epoch===assignmentEpoch&&scope===window.wzosClock.getSession()?.organization_id+':'+window.wzosClock.getSession()?.id;
  const host=node('div');host.dataset.dispatch='1';host.dataset.assignmentsOnly='1';root.append(host);
  try{const panel=await memberPanel(root,current);if(panel&&current()){host.append(panel);say('Open a job, review the details and confirm receipt.');}}catch(error){if(current())say(error.message);}
 }
 let polling=false,notificationScope='';
 async function updateNotifications(){
  const session=window.wzosClock.getSession(),nav=document.getElementById('assignments-nav'),count=document.getElementById('assignment-count'),alert=document.getElementById('assignment-alert');
  const scope=session?.organization_id+':'+session?.id;
  nav.hidden=session?.edition!=='enterprise';
  if(scope!==notificationScope){notificationScope=scope;count.textContent='…';alert.hidden=true;assignmentOffset=0;}
  if(nav.hidden){count.textContent='0';alert.hidden=true;return;}
  if(polling||document.hidden)return;
  if(!navigator.onLine){alert.hidden=false;alert.textContent='Offline — reconnect to check new work assignments.';return;}
  polling=true;
  try{const data=await api('/api/dispatch/notifications');const next=window.wzosClock.getSession();if(scope!==next?.organization_id+':'+next?.id)return;count.textContent=String(data.pending_count);alert.hidden=!data.pending_count;alert.textContent=`${data.pending_count} work assignment${data.pending_count===1?'':'s'} ${data.pending_count===1?"needs":"need"} your confirmation. Open My jobs to review.`;}catch(error){if(scope===notificationScope){alert.hidden=false;alert.textContent='New assignments could not be checked. Reconnect or refresh My jobs; WZOS will retry.';}}finally{polling=false;}
 }
 document.getElementById('assignments-nav').onclick=()=>window.showWzosView('assignments');
 document.addEventListener('wzos:view',event=>{assignmentEpoch++;if(event.detail==='assignments')showAssignments();});
 document.addEventListener('wzos:session',()=>{assignmentEpoch++;updateNotifications();});
 document.addEventListener('visibilitychange',updateNotifications);window.addEventListener('online',updateNotifications);
 setInterval(updateNotifications,30000);
})();
