"use strict";
(() => {
 const $=id=>document.getElementById(id), api=(...args)=>window.wzosClock.api(...args);
 const safetyFields={competent_person:"Competent person / reviewer",tasks:"Job tasks",hazards:"Hazards",controls:"Controls",emergency_plan:"Emergency plan",ppe:"PPE"};
 for(const [key,label] of Object.entries(safetyFields)){const wrap=document.createElement('label');wrap.textContent=label;const input=document.createElement('textarea');input.id='safety-'+key;input.maxLength=key==='competent_person'?200:key==='ppe'?1000:key==='emergency_plan'?2000:4000;wrap.append(input);$('safety-fields').append(wrap);}
 let roster=[],linkableJobs=[],assignmentOffset=0;
 const checks={tires:"Tires",fluids:"Fluids",brakes:"Brakes",ebrake:"Emergency brake",mirrors:"Mirrors",windows:"Windows"};
 for(const [key,label] of Object.entries(checks)){const wrap=document.createElement("label");wrap.textContent=label;const select=document.createElement("select");select.id="dvir-"+key;for(const [value,title] of Object.entries({not_checked:"Not checked",pass:"Pass (reported)",fail:"Fail (reported)"})){const option=document.createElement("option");option.value=value;option.textContent=title;select.append(option);}wrap.append(select);$("dvir-checks").append(wrap);}
 function template(){$("module-safety").hidden=kind!=="forms"||$("module-type").value!=="jsa";const enabled=kind==="forms"&&$("module-type").value==="dvir";$("module-inspection").hidden=!enabled;$("dvir-vehicle").required=enabled;}
 $("module-type").onchange=template;
 let kind="forms", current=null, dirty=false, saving=false, epoch=0, offset=0, total=0;
 const text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 const notice=value=>{$("module-notice").textContent=value;};
 window.wzosModulesCanLeave=()=>!saving&&(!dirty||confirm("Leave unsaved module changes?"));
 function localTime(value){if(!value)return "";const d=new Date(value);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);}
 function edit(row){
  let attachments=$("module-attachments");if(!attachments){attachments=text("div","");attachments.id="module-attachments";$("module-form").after(attachments);}window.wzosFiles.mount(attachments,"form",kind==="forms"?row?.id:null);
  $("module-type").value=row?.form_type||"incident";$("module-type").disabled=Boolean(row);
  const inspection=row?.inspection;$("dvir-vehicle").value=inspection?.vehicle_id||"";$("dvir-odometer").value=inspection?.odometer??"";$("dvir-trip").value=inspection?.trip_type||"pre-trip";$("dvir-defects").value=inspection?.defects||"";for(const key of Object.keys(checks))$("dvir-"+key).value=inspection?.[key]||"not_checked";template();
  for(const key of Object.keys(safetyFields))$("safety-"+key).value=row?.safety?.[key]||"";
  $("module-assignees").replaceChildren();for(const member of roster){const option=text("option",member.name+" · "+member.role);option.value=member.id;option.selected=(row?.assignees||[]).includes(member.id);$("module-assignees").append(option);}
  $("module-history").replaceChildren();if(row)loadHistory(row);
  current=row||{id:crypto.randomUUID(),version:0};dirty=false;$("module-form").hidden=false;
  for(const [id,key] of [["name","title"],["location","location"],["details","details"]])$("module-"+id).value=row?.[key]||"";
  const none=text("option","No linked work order");none.value="";$("module-order").replaceChildren(none);
  for(const order of linkableJobs){const option=text("option",order.title+(order.access_basis==='dispatched_summary'?' · assigned job':''));option.value=order.id;$("module-order").append(option);}
  if(row?.order_id&&!linkableJobs.some(order=>order.id===row.order_id)){const option=text('option',(row.order_reference?.title||'Previously linked job')+' · saved reference');option.value=row.order_id;$("module-order").append(option);}
  $("module-order").value=row?.order_id||"";
  let reference=$('module-job-reference');if(!reference){reference=text('p','');reference.id='module-job-reference';$('module-order').parentNode.after(reference);}reference.textContent=row?.order_reference?`Saved job reference: ${row.order_reference.title} · ${row.order_reference.address}`:'';
  $("module-start").value=localTime(row?.start);$("module-end").value=localTime(row?.end);$("module-status").value=row?.status||"draft";
  $("module-version").textContent=row?`Saved revision ${row.version} · ${new Date(row.updated_at).toLocaleString()}`:"Unsaved draft";
  $("module-meeting-url").value=row?.meeting_url||"";
  const join=$("module-meeting-join");join.removeAttribute("href");join.hidden=true;
  if(kind==="schedule"&&row?.status!=="cancelled"&&/^https:\/\/meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}$/.test(row?.meeting_url||"")){join.href=row.meeting_url;join.hidden=false;}
  const readOnly=kind==="schedule"&&window.wzosClock.getSession()?.role!=="admin";
  for(const input of $("module-form").elements)input.disabled=readOnly;
  $("module-meeting-create").hidden=readOnly;$("module-meeting-help").hidden=readOnly;
  $("module-type").disabled=readOnly||Boolean(row);
 }
 async function refresh(){
  const generation=++epoch;
  try{const data=await api(`/api/modules/${kind}?offset=${offset}${kind==="schedule"&&$("module-day").value?"&day="+$("module-day").value:""}`);if(generation!==epoch)return;
   total=data.total;$("module-list").replaceChildren();$("module-new").hidden=!data.can_edit;
   for(const row of data.items){const button=text("button",`${row.title} · ${row.status}${row.start?" · "+new Date(row.start).toLocaleString():""}`);button.type="button";button.className="job";button.onclick=()=>{if(window.wzosModulesCanLeave())edit(row);};$("module-list").append(button);}
   if(!data.items.length)$("module-list").append(text("p","No saved records on this page."));
   $("module-page").textContent=`${total} records · ${data.items.length?offset+1:0}–${offset+data.items.length}`;
   $("module-prev").disabled=offset===0;$("module-next").disabled=offset+25>=total;
   if(kind==='schedule')await showAssignments(generation);
  }catch(error){if(generation===epoch)notice(error.message);}
 }
 async function show(view){
  // Reuse the scoped, versioned draft editor alongside the printable Forms library.
  if(!["schedule","form_drafts"].includes(view))return;
  $("module-attachments")?.replaceChildren();$("schedule-assignments")?.replaceChildren();const showGeneration=++epoch;kind=view==="form_drafts"?"forms":"schedule";offset=0;assignmentOffset=0;linkableJobs=[];dirty=false;current=null;$("module-new").disabled=true;$("module-form").hidden=true;notice("");$("module-meeting-join").hidden=true;$("module-meeting-join").removeAttribute("href");
  $("module-title").textContent=kind==="forms"?"Saved form drafts":"Schedule management";
  $("module-description").textContent=kind==="forms"?"Save and reopen incident, vehicle inspection and JSA drafts linked to your jobs. Submit saved versions for internal review in Forms hub.":"Admins manage team schedule drafts; members can read. Dispatched assignments appear separately below. Saving a schedule draft does not dispatch or notify anyone.";
  $("module-library").hidden=kind!=="forms";
  $("module-day-label").hidden=kind!=="schedule";$("module-assignees-label").hidden=kind!=="schedule";$("module-history").replaceChildren();
  try{const result=await api("/api/modules/roster");if(showGeneration!==epoch)return;roster=result.items;
   let next=0;while(true){const page=await api(`/api/modules/jobs?offset=${next}&limit=50`);if(showGeneration!==epoch)return;linkableJobs.push(...page.items);next+=page.items.length;if(next>=page.total||!page.items.length)break;}
   $('module-new').disabled=false;
  }catch(error){if(showGeneration!==epoch)return;roster=[];notice(error.message);}
  $("module-meeting").hidden=kind!=="schedule";
  $("module-type-label").hidden=kind!=="forms";
  $("module-times").hidden=kind!=="schedule";$("module-start").required=$("module-end").required=kind==="schedule";
  refresh();
 }
 $("forms-drafts-open").onclick=()=>window.showWzosView("form_drafts");
 $("module-library").onclick=()=>window.showWzosView("forms");
 $("schedule-nav").onclick=()=>window.showWzosView("schedule");
 document.addEventListener("wzos:view",event=>show(event.detail));
 document.addEventListener("wzos:session",()=>{$("module-attachments")?.replaceChildren();$("schedule-assignments")?.replaceChildren();linkableJobs=[];$("module-meeting-join").hidden=true;$("module-meeting-join").removeAttribute("href");epoch++;dirty=false;current=null;$("module-list").replaceChildren();$("module-form").hidden=true;if(!$("modules-view").hidden)show(kind==="forms"?"form_drafts":"schedule");});
 $("module-day").onchange=()=>{offset=0;assignmentOffset=0;refresh();};
 async function showAssignments(generation){
  let root=$('schedule-assignments');if(!root){root=text('section','');root.id='schedule-assignments';root.className='panel report-section';$('module-list').after(root);}root.replaceChildren();
  if(window.wzosClock.getSession()?.edition!=='enterprise')return;
  const data=await api(`/api/dispatch/schedule?offset=${assignmentOffset}${$('module-day').value?'&day='+$('module-day').value:''}`);if(generation!==epoch||kind!=='schedule')return;
  root.append(text('h2','Dispatched assignments'),text('p','Read-only assignments · date filter uses UTC days; times below use your device timezone. Confirm receipt in My jobs.'));
  for(const row of data.items){const card=text('article','');card.className='report-section panel';card.append(text('h3',row.title),text('p',`${row.employee_name} · ${row.status}`),text('p',`${new Date(row.starts_at).toLocaleString()} → ${new Date(row.ends_at).toLocaleString()} (estimated finish)`),text('p',row.address));const link=window.WzosNavigation.link(row.address);if(link)card.append(link);if(row.snapshot_state==='legacy_unavailable')card.append(text('p','Historical dispatched details are unavailable.'));root.append(card);}
  if(!data.items.length)root.append(text('p','No dispatched assignments on this page.'));
  const prev=text('button','Previous assignments'),next=text('button','Next assignments');prev.type=next.type='button';prev.disabled=assignmentOffset===0;next.disabled=assignmentOffset+data.limit>=data.total;
  prev.onclick=()=>{if(window.wzosModulesCanLeave()){assignmentOffset=Math.max(0,assignmentOffset-data.limit);refresh();}};next.onclick=()=>{if(window.wzosModulesCanLeave()){assignmentOffset+=data.limit;refresh();}};
  root.append(prev,next,text('p',`${data.total} assignments · ${data.items.length?assignmentOffset+1:0}–${assignmentOffset+data.items.length}`));
 }
 async function loadHistory(row){const selectedKind=kind;try{const data=await api(`/api/modules/${kind}/${row.id}/history`);if(current?.id!==row.id||selectedKind!==kind)return;$("module-history").append(text("h3","Saved revision history"));for(const entry of data.items){const d=text("details","");d.append(text("summary",`Revision ${entry.version} · ${new Date(entry.saved_at).toLocaleString()}`),text("p",entry.record.title),text("p",entry.record.details||"No notes"));for(const [key,value] of Object.entries(entry.record.safety||{}))d.append(text("p",`${safetyFields[key]}: ${value||"Not recorded"}`));$("module-history").append(d);}}catch(error){notice(error.message);}}
 $("module-new").onclick=()=>{if(window.wzosModulesCanLeave())edit(null);};
 $("module-refresh").onclick=()=>{if(window.wzosModulesCanLeave()){dirty=false;$("module-form").hidden=true;refresh();}};
 $("module-prev").onclick=()=>{if(window.wzosModulesCanLeave()){offset=Math.max(0,offset-25);refresh();}};
 $("module-next").onclick=()=>{if(window.wzosModulesCanLeave()){offset+=25;refresh();}};
 $("module-form").oninput=()=>{dirty=true;};
 window.addEventListener("beforeunload",event=>{if(dirty||saving){event.preventDefault();event.returnValue="";}});
 $("module-form").onsubmit=async event=>{
  event.preventDefault();if(saving)return;
  const generation=epoch, record=current;
  const body={request_id:record.id,expected_version:record.version,title:$("module-name").value,location:$("module-location").value,details:$("module-details").value,order_id:$("module-order").value||null,status:$("module-status").value,start:null,end:null};
  if(kind==="forms"){body.form_type=$("module-type").value;if(body.form_type==="dvir"){body.inspection={vehicle_id:$("dvir-vehicle").value,odometer:$("dvir-odometer").value===""?null:Number($("dvir-odometer").value),trip_type:$("dvir-trip").value,defects:$("dvir-defects").value};for(const key of Object.keys(checks))body.inspection[key]=$("dvir-"+key).value;if(Object.keys(checks).some(key=>body.inspection[key]==="fail")&&!body.inspection.defects.trim()){notice("Describe the failed inspection items in Defects.");return;}}}
  if(kind==="forms"&&body.form_type==="jsa"){body.safety={};for(const key of Object.keys(safetyFields))body.safety[key]=$("safety-"+key).value;}
  if(kind==="schedule"){body.meeting_url=$("module-meeting-url").value.trim();body.assignees=Array.from($("module-assignees").selectedOptions,o=>o.value);body.start=new Date($("module-start").value).toISOString();body.end=new Date($("module-end").value).toISOString();if(body.end<=body.start){notice("End must be after start.");return;}}
  saving=true;for(const input of $("module-form").elements)input.disabled=true;$("identity").disabled=true;
  try{const saved=await api(`/api/modules/${kind}/${record.id}`,{method:"PUT",body:JSON.stringify(body)});if(generation!==epoch)return;edit(saved);notice("Draft saved. No submission or notification was sent.");await refresh();}
  catch(error){notice(error.message);}finally{saving=false;for(const input of $("module-form").elements)input.disabled=false;$("identity").disabled=false;$("module-type").disabled=Boolean(current?.version);}
 };
})();
(() => {
 const $=id=>document.getElementById(id);let epoch=0,offset=0;
 const safe=url=>/^https:\/\/meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}$/.test(url||'');
 function reset(){const a=$('meeting-screen-join');a.hidden=true;a.removeAttribute('href');$('meeting-selected-title').textContent='A place to connect.';$('meeting-selected-detail').textContent='Select a scheduled meeting below.';$('meetings-state').textContent='STANDBY';}
 async function refresh(){const generation=++epoch;reset();$('meetings-cards').replaceChildren();$('meetings-notice').textContent='Loading meetings...';$('meetings-manage').hidden=window.wzosClock.getSession()?.role!=='admin';
 try{const data=await window.wzosClock.api(`/api/modules/schedule?meetings_only=true&limit=50&offset=${offset}`);if(generation!==epoch)return;const rows=data.items.filter(r=>safe(r.meeting_url));for(const row of rows){const card=document.createElement('button');card.type='button';card.className='meeting-glass-card';card.setAttribute('aria-pressed','false');for(const [tag,value] of [['small',row.status==='cancelled'?'CANCELLED':'GOOGLE MEET'],['strong',row.title],['span',new Date(row.start).toLocaleString()]]){const n=document.createElement(tag);n.textContent=value;card.append(n);}card.onclick=()=>{reset();$('meeting-selected-title').textContent=row.title;$('meeting-selected-detail').textContent=new Date(row.start).toLocaleString();$('meetings-state').textContent=row.status==='cancelled'?'CANCELLED':'SCHEDULED';if(row.status!=='cancelled'){$('meeting-screen-join').href=row.meeting_url;$('meeting-screen-join').hidden=false;}for(const c of $('meetings-cards').children)c.setAttribute('aria-pressed',String(c===card));};$('meetings-cards').append(card);}$('meetings-notice').textContent=rows.length?'Select a meeting card. Google host admission controls apply.':'No meetings on this page.';$('meetings-page').textContent=`Meetings ${data.items.length?offset+1:0}-${offset+data.items.length} of ${data.total}`;$('meetings-prev').disabled=offset===0;$('meetings-next').disabled=offset+50>=data.total;}catch(e){if(generation===epoch)$('meetings-notice').textContent=e.message;}}
 $('meetings-nav').onclick=()=>window.showWzosView('meetings');$('meetings-manage').onclick=()=>window.showWzosView('schedule');$('meetings-refresh').onclick=refresh;$('meetings-prev').onclick=()=>{offset=Math.max(0,offset-50);refresh();};$('meetings-next').onclick=()=>{offset+=50;refresh();};document.addEventListener('wzos:view',e=>{if(e.detail==='meetings'){offset=0;refresh();}else epoch++;});document.addEventListener('wzos:session',()=>{epoch++;reset();$('meetings-cards').replaceChildren();if(!$('meetings-view').hidden){offset=0;refresh();}});
})();
