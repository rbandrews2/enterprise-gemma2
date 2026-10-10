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
 const ASSIGNMENT={sent:'Waiting for response',accepted:'Accepted',declined:'Declined',cancelled:'Cancelled',replaced:'Replaced by a newer plan'};
 let selected='', notice=null;
 const say=text=>{if(notice)notice.textContent=text;};
 async function act(control,work,done,refresh){control.disabled=true;try{await work();await refresh();say(done);}catch(error){say(error.message);}finally{control.disabled=false;}}

 async function memberPanel(root,current){
  const data=await api('/api/dispatch/my-assignments');if(!current())return;
  const panel=node('section');panel.className='report-section panel';panel.append(node('h2','My assignments'));
  if(!data.items.length)panel.append(node('p','No assignments yet.'));
  for(const item of data.items){const card=node('article');card.className='clock-entry';
   card.append(node('p',`${item.order_title} · ${item.role_title}`),node('p',`${local(item.starts_at)} → ${local(item.ends_at)} · ${item.address}`),node('p','Status: '+(ASSIGNMENT[item.status]||item.status)+(item.responded_at?' · '+local(item.responded_at):'')));
   if(item.status==='sent'){const row=node('div');row.className='clock-actions';
    for(const [response,label] of [['accepted','Accept'],['declined','Decline']]){const b=button(label,response==='accepted'?'primary':'secondary');
     b.onclick=()=>act(b,()=>api('/api/dispatch/assignments/'+item.id+'/respond',{method:'POST',body:JSON.stringify({response})}),response==='accepted'?'Assignment accepted.':'Assignment declined. Your admin will see your response.',()=>rerender(root,current));row.append(b);}
    card.append(row);}
   panel.append(card);}
  return panel;
 }

 function requirementsForm(state,refresh){
  const req=state.requirements, form=node('form');form.onsubmit=e=>e.preventDefault();
  const start=node('input'),end=node('input');start.type=end.type='datetime-local';start.value=inputTime(req?.starts_at);end.value=inputTime(req?.ends_at);
  const role=req?.roles?.[0]||{id:'crew',title:'Crew member',count:1,qualification_ids:[]};
  const title=node('input'),count=node('input'),quals=node('input'),notes=node('textarea');title.value=role.title;count.type='number';count.min=1;count.max=20;count.value=role.count;quals.value=(role.qualification_ids||[]).join(', ');notes.value=req?.notes||'';notes.maxLength=1000;
  quals.placeholder='Qualification identifiers, e.g. flagger';
  const save=button('Save staffing requirements','primary');
  if(req?.roles?.length>1)form.append(node('p',`This order has ${req.roles.length} roles; only the first is editable here. Other roles are kept.`));
  form.append(labelled('Job starts (your time zone)',start),labelled('Job ends',end),labelled('Role',title),labelled('People needed',count),labelled('Required qualification identifiers (comma separated)',quals),labelled('Notes for planning',notes),save);
  save.onclick=()=>{if(!start.value||!end.value){say('Enter the job start and end.');return;}
   const first={id:(role.id||'crew'),title:title.value.trim(),count:Number(count.value),qualification_ids:quals.value.split(',').map(q=>q.trim()).filter(Boolean)};
   const body={expected_version:req?.version||0,starts_at:new Date(start.value).toISOString(),ends_at:new Date(end.value).toISOString(),roles:[first,...(req?.roles||[]).slice(1)],notes:notes.value};
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

 async function rerender(root,current){const host=root.querySelector('[data-dispatch]');if(!host)return;const fresh=await build(root,current);if(fresh&&current())host.replaceWith(fresh);}
 async function build(root,current){
  const session=window.wzosClock.getSession();if(session?.edition!=='enterprise')return null;
  const wrap=node('div');wrap.dataset.dispatch='1';
  const mine=await memberPanel(root,current);if(mine)wrap.append(mine);
  if(session.role==='admin'){const admin=await adminPanel(root,current);if(admin)wrap.append(admin);}
  return wrap;
 }
 // Called by the Messaging view; renders nothing for Core organizations.
 window.wzosDispatch={async render(root,current,status){notice=status;try{const panel=await build(root,current);if(panel&&current())root.append(panel);}catch(error){if(current())say(error.message);}}};
})();
