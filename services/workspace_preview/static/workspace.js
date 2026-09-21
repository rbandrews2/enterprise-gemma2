"use strict";
const $ = id => document.getElementById(id);
let identities = [], session = null, rows = [], selected = null, dirty = false, busy = false;
let requestId = crypto.randomUUID();
let lastCreateBody = null;
const types = {line_striping:"Line striping",underground_utility:"Underground utility",road_maintenance:"Road maintenance",other:"Other"};
function el(tag, text, className) {const node=document.createElement(tag); if(text!==undefined)node.textContent=text; if(className)node.className=className;return node;}
function notify(message,error=false){$("notice").hidden=false;$("notice").textContent=message;$("notice").classList.toggle("error",error);}
async function api(path, options={}) {
 const response=await fetch(path,{...options,headers:{"Content-Type":"application/json","X-Preview-Actor":session?.id || $("identity").value,...options.headers}});
 const data=await response.json();
 if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:"Check the job fields and try again. Nothing was confirmed saved.");
 return data;
}
function lock(value){busy=value;$("identity").disabled=value;$("new-order").disabled=value;$("refresh").disabled=value;$("reload-order").disabled=value;$("save-order").disabled=value;$("prepare").disabled=value||dirty||!selected||!session?.can_prepare_atlas;for(const input of $("order-form").querySelectorAll("input,select,textarea"))input.disabled=value;}
function canLeave(){return !dirty||confirm("Discard the unsaved changes to this work order?");}
function renderList(){
 const query=$("search").value.toLowerCase();$("job-list").replaceChildren();
 const filtered=rows.filter(r=>`${r.title} ${r.address} ${r.locality}`.toLowerCase().includes(query));
 for(const row of filtered){const button=el("button",undefined,"job");button.type="button";button.setAttribute("aria-pressed",String(selected?.id===row.id));const top=el("span",undefined,"job-top");top.append(el("span",types[row.work_type],"job-type"),el("span","Draft","pill draft"));button.append(top,el("strong",row.title),el("small",row.address),el("small",row.work_date?`Planned ${row.work_date}`:"Work date needed"));button.addEventListener("click",()=>{if(!busy&&canLeave())open(row);});$("job-list").append(button);}
 if(!filtered.length)$("job-list").append(el("p",query?"No matching jobs. Try another search.":"No work orders yet. Create your first draft.","muted"));
 $("metric-total").textContent=rows.length;$("metric-drafts").textContent=rows.length;$("metric-date").textContent=rows.filter(r=>!r.work_date).length;$("nav-count").textContent=rows.length;
}
function open(record){
 selected=record;dirty=false;requestId=crypto.randomUUID();lastCreateBody=null;$("atlas-output").replaceChildren();$("order-form").hidden=false;$("empty-detail").hidden=true;
 $("detail-title").textContent=record?record.title:"New work order";$("record-meta").textContent=record?`SAVED DRAFT · REVISION ${record.version}`:"NEW DRAFT";
 for(const name of ["title","address","locality","notes"])$(name).value=record?.[name]||"";
 $("work-type").value=record?.work_type||"line_striping";$("work-date").value=record?.work_date||"";
 $("save-state").textContent=record?"Saved locally":"Not saved yet";$("save-order").textContent=record?"Save changes":"Create draft";$("reload-order").hidden=!record;
 renderList();lock(false);
}
async function loadRows(){rows=(await api("/api/orders")).items;renderList();}
async function switchIdentity(){
 lock(true);$("notice").hidden=true;
 try{session=null;session=await api("/api/session");selected=null;dirty=false;rows=[];$("atlas-output").replaceChildren();$("order-form").hidden=true;$("empty-detail").hidden=false;$("detail-title").textContent="Select a work order";
 $("org-name").textContent=session.organization;$("edition").textContent=`${session.edition==="core"?"Core":"Enterprise"} edition · synthetic`;
 $("actor-name").textContent=session.name;document.querySelector(".avatar").textContent=session.name.split(" ").map(n=>n[0]).join("");$("role-pill").textContent=session.role==="admin"?"Admin":"General";
 $("scope-note").textContent=session.can_manage_team?"Manage the team's draft work orders.":"Your assigned work orders and new drafts.";$("metric-scope").textContent=session.can_manage_team?"This test organization":"Assigned to this test user";
 $("atlas-description").textContent=session.can_prepare_atlas?"Check a saved job for missing site details before planning.":"Advanced job preparation is available in Enterprise. Core assistant integration is still pending.";
 await loadRows();if(rows.length)open(rows[0]);
 }catch(error){notify(error.message,true);}finally{lock(false);}
}
$("identity").addEventListener("change",()=>{if(!canLeave()){$("identity").value=session.id;return;}switchIdentity();});
$("search").addEventListener("input",renderList);
$("new-order").addEventListener("click",()=>{if(canLeave()){open(null);$("title").focus();}});
$("order-form").addEventListener("input",()=>{dirty=true;$("save-state").textContent="Unsaved changes";$("atlas-output").replaceChildren();$("prepare").disabled=true;});
$("order-form").addEventListener("submit",async event=>{
 event.preventDefault();if(busy)return;lock(true);
 const body={title:$("title").value,work_type:$("work-type").value,address:$("address").value,locality:$("locality").value,work_date:$("work-date").value||null,notes:$("notes").value};
 if(!selected){const signature=JSON.stringify(body);if(lastCreateBody!==null&&lastCreateBody!==signature)requestId=crypto.randomUUID();lastCreateBody=signature;}
 try{const record=await api(selected?`/api/orders/${selected.id}`:"/api/orders",{method:selected?"PUT":"POST",body:JSON.stringify({...body,...(selected?{expected_version:selected.version}:{request_id:requestId})})});
  open(record);lock(true);notify(`Saved locally · revision ${record.version}.`);try{await loadRows();}catch{notify(`Saved revision ${record.version}, but the job board could not refresh. Use Refresh to try again.`,true);}
 }catch(error){notify(error.message,true);$("save-state").textContent="Save not confirmed · draft retained";}finally{lock(false);}
});
async function refresh(){if(busy||!canLeave())return;lock(true);try{const id=selected?.id;await loadRows();const record=rows.find(r=>r.id===id)||rows[0];if(record)open(record);else{selected=null;dirty=false;$("order-form").hidden=true;$("empty-detail").hidden=false;$("atlas-output").replaceChildren();}notify("Loaded the latest saved records.");}catch(error){notify(error.message,true);}finally{lock(false);}}
$("refresh").addEventListener("click",refresh);$("reload-order").addEventListener("click",refresh);
$("prepare").addEventListener("click",async()=>{
 if(busy||dirty||!selected)return;lock(true);$("atlas-output").replaceChildren(el("p","Checking saved job details…","muted"));
 try{const data=await api(`/api/orders/${selected.id}/preparation?expected_version=${selected.version}`,{method:"POST"});const list=el("ul");for(const item of data.attention_items)list.append(el("li",item.message));$("atlas-output").replaceChildren(el("strong",`Preparation for revision ${data.version}`),list,el("p",data.note,"fine"));}
 catch(error){$("atlas-output").replaceChildren();notify(error.message,true);}finally{lock(false);}
});
$("atlas-nav").addEventListener("click",()=>{$("atlas-title").scrollIntoView({behavior:"smooth",block:"center"});});
$("jobs-nav").addEventListener("click",()=>{$("list-title").scrollIntoView({behavior:"smooth",block:"start"});});
window.addEventListener("beforeunload",event=>{if(dirty){event.preventDefault();event.returnValue="";}});
(async()=>{try{identities=(await api("/api/identities")).identities;for(const identity of identities){const option=el("option",`${identity.edition==="core"?"Core":"Enterprise"} · ${identity.role} · ${identity.name}`);option.value=identity.id;$("identity").append(option);}$("identity").value="enterprise-admin";await switchIdentity();}catch(error){notify(error.message,true);}})();
