"use strict";
(() => {
 const $=id=>document.getElementById(id), api=(...args)=>window.wzosClock.api(...args);
 const safetyFields={competent_person:"Competent person / reviewer",tasks:"Job tasks",hazards:"Hazards",controls:"Controls",emergency_plan:"Emergency plan",ppe:"PPE"};
 for(const [key,label] of Object.entries(safetyFields)){const wrap=document.createElement('label');wrap.textContent=label;const input=document.createElement('textarea');input.id='safety-'+key;input.maxLength=key==='competent_person'?200:key==='ppe'?1000:key==='emergency_plan'?2000:4000;wrap.append(input);$('safety-fields').append(wrap);}
 let roster=[];
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
  for(const order of window.wzosClock.getOrders()){const option=text("option",order.title);option.value=order.id;$("module-order").append(option);}
  $("module-order").value=row?.order_id||"";
  $("module-start").value=localTime(row?.start);$("module-end").value=localTime(row?.end);$("module-status").value=row?.status||"draft";
  $("module-version").textContent=row?`Saved revision ${row.version} · ${new Date(row.updated_at).toLocaleString()}`:"Unsaved draft";
  const readOnly=kind==="schedule"&&window.wzosClock.getSession()?.role!=="admin";
  for(const input of $("module-form").elements)input.disabled=readOnly;
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
  }catch(error){if(generation===epoch)notice(error.message);}
 }
 async function show(view){
  if(!["forms","schedule"].includes(view))return;
  $("module-attachments")?.replaceChildren();const showGeneration=++epoch;kind=view;offset=0;dirty=false;current=null;$("module-form").hidden=true;notice("");
  $("module-title").textContent=kind==="forms"?"Forms hub":"Schedule management";
  $("module-description").textContent=kind==="forms"?"Incident, vehicle inspection and JSA planning drafts. Save, reopen and link to a work order. Official submissions and other templates are pending.":"Team schedule drafts. Admins edit; team members can read. Assignments use test members; overlapping active drafts are rejected. Saving does not dispatch or notify anyone.";
  $("module-day-label").hidden=kind!=="schedule";$("module-assignees-label").hidden=kind!=="schedule";$("module-history").replaceChildren();
  try{const result=await api("/api/modules/roster");if(showGeneration!==epoch)return;roster=result.items;}catch(error){if(showGeneration!==epoch)return;roster=[];notice(error.message);}
  $("module-type-label").hidden=kind!=="forms";
  $("module-times").hidden=kind!=="schedule";$("module-start").required=$("module-end").required=kind==="schedule";
  refresh();
 }
 for(const key of ["forms","schedule"])$(key+"-nav").onclick=()=>window.showWzosView(key);
 document.addEventListener("wzos:view",event=>show(event.detail));
 document.addEventListener("wzos:session",()=>{$("module-attachments")?.replaceChildren();epoch++;dirty=false;current=null;$("module-list").replaceChildren();$("module-form").hidden=true;if(!$("modules-view").hidden)show(kind);});
 $("module-day").onchange=()=>{offset=0;refresh();};
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
  if(kind==="schedule"){body.assignees=Array.from($("module-assignees").selectedOptions,o=>o.value);body.start=new Date($("module-start").value).toISOString();body.end=new Date($("module-end").value).toISOString();if(body.end<=body.start){notice("End must be after start.");return;}}
  saving=true;for(const input of $("module-form").elements)input.disabled=true;$("identity").disabled=true;
  try{const saved=await api(`/api/modules/${kind}/${record.id}`,{method:"PUT",body:JSON.stringify(body)});if(generation!==epoch)return;edit(saved);notice("Draft saved. No submission or notification was sent.");await refresh();}
  catch(error){notice(error.message);}finally{saving=false;for(const input of $("module-form").elements)input.disabled=false;$("identity").disabled=false;$("module-type").disabled=Boolean(current?.version);}
 };
})();
