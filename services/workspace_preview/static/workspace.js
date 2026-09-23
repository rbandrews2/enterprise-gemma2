"use strict";
const $ = id => document.getElementById(id);
let identities = [], session = null, rows = [], selected = null, dirty = false, busy = false;
let requestId = crypto.randomUUID();
let lastCreateBody = null;
let readGeometry=()=>null;
let checklistDirty=false, checklistData=null, checklistGeneration=0, checklistLoading=false;
const types = {line_striping:"Line striping",underground_utility:"Underground utility",road_maintenance:"Road maintenance",other:"Other"};
function el(tag, text, className) {const node=document.createElement(tag); if(text!==undefined)node.textContent=text; if(className)node.className=className;return node;}
function notify(message,error=false){$("notice").hidden=false;$("notice").textContent=message;$("notice").classList.toggle("error",error);}
async function api(path, options={}) {
 const response=await fetch(path,{...options,headers:{"Content-Type":"application/json","X-Preview-Actor":session?.id || $("identity").value,...await window.wzosAccount.headers(),...options.headers}});
 const data=await response.json();
 if(!response.ok){const error=new Error(typeof data.detail==="string"?data.detail:"Check the fields and try again. Nothing was confirmed saved.");error.status=response.status;throw error;}
 return data;
}
function lock(value){busy=value;lockChecklist();$("identity").disabled=value;$("new-order").disabled=value;$("refresh").disabled=value;$("reload-order").disabled=value;$("save-order").disabled=value;$("prepare").disabled=value||dirty||!selected||!session?.can_prepare_atlas;for(const input of $("order-form").querySelectorAll("input,select,textarea,button"))input.disabled=value||checklistDirty;}
function canLeave(){return !(dirty||checklistDirty)||confirm("Discard unsaved job or checklist changes?");}
function renderList(){
 const query=$("search").value.toLowerCase();$("job-list").replaceChildren();
 const filtered=rows.filter(r=>`${r.title} ${r.address} ${r.locality}`.toLowerCase().includes(query));
 for(const row of filtered){const button=el("button",undefined,"job");button.type="button";button.setAttribute("aria-pressed",String(selected?.id===row.id));const top=el("span",undefined,"job-top");top.append(el("span",types[row.work_type],"job-type"),el("span","Draft","pill draft"));button.append(top,el("strong",row.title),el("small",row.address),el("small",row.work_date?`Planned ${row.work_date}`:"Work date needed"));button.addEventListener("click",()=>{if(!busy&&canLeave())open(row);});$("job-list").append(button);}
 if(!filtered.length)$("job-list").append(el("p",query?"No matching jobs. Try another search.":"No work orders yet. Create your first draft.","muted"));
 $("metric-total").textContent=rows.length;$("metric-drafts").textContent=rows.length;$("metric-date").textContent=rows.filter(r=>!r.work_date).length;$("nav-count").textContent=rows.length;
}
function open(record){
 readGeometry=window.WzosGeometry.mount($("geometry-fields"),record?.job_geometry);
 document.dispatchEvent(new CustomEvent("wzos:job-context"));
 let attachments=$("order-attachments");if(!attachments){attachments=el("div");attachments.id="order-attachments";$("order-form").after(attachments);}window.wzosFiles.mount(attachments,"order",record?.id);
 selected=record;dirty=false;requestId=crypto.randomUUID();lastCreateBody=null;$("atlas-output").replaceChildren();$("order-form").hidden=false;$("empty-detail").hidden=true;
 $("detail-title").textContent=record?record.title:"New work order";$("record-meta").textContent=record?`SAVED DRAFT · REVISION ${record.version}`:"NEW DRAFT";
 for(const name of ["title","address","locality","notes"])$(name).value=record?.[name]||"";
 $("work-type").value=record?.work_type||"line_striping";$("work-date").value=record?.work_date||"";
 $("save-state").textContent=record?"Saved locally":"Not saved yet";$("save-order").textContent=record?"Save changes":"Create draft";$("reload-order").hidden=!record;
 $("road-authority").value=record?.road_authority||"";$("speed-limit").value=record?.site?.speed_limit_mph??"";$("lane-count").value=record?.site?.lane_count??"";$("work-period").value=record?.site?.work_period||"unknown";
 renderList();lock(false);loadChecklist();
}
async function loadRows(){rows=(await api("/api/orders")).items;renderList();}
async function switchIdentity(){
 lock(true);$("order-attachments")?.replaceChildren();resetChecklist();$("notice").hidden=true;
 try{session=null;session=await api("/api/session");selected=null;dirty=false;rows=[];$("atlas-output").replaceChildren();$("order-form").hidden=true;$("empty-detail").hidden=false;$("detail-title").textContent="Select a work order";
 if(session.restricted_staging){document.querySelector('.preview-bar>div').textContent='RESTRICTED CLOUD STAGING · Shared synthetic records reset on restart. Do not enter real attendance or customer data.';$("identity").closest('label').hidden=true;document.querySelector('.sidebar-foot').textContent='Restricted staging · WZOS V2';document.querySelector('.app-footer').textContent='WZOS V2 staging · Test data only · Storage and cloud AI integration pending.';}
 $("org-name").textContent=session.organization;$("edition").textContent=`${session.edition==="core"?"Core":"Enterprise"} edition · synthetic`;
 $("actor-name").textContent=session.name;document.querySelector(".avatar").textContent=session.name.split(" ").map(n=>n[0]).join("");$("role-pill").textContent=session.role==="admin"?"Admin":"General";
 $("scope-note").textContent=session.can_manage_team?"Manage the team's draft work orders.":"Your assigned work orders and new drafts.";$("metric-scope").textContent=session.can_manage_team?"This test organization":"Assigned to this test user";
 $("atlas-description").textContent=session.can_prepare_atlas?"Check a saved job for missing site details before planning.":"Advanced job preparation is available in Enterprise. Core assistant integration is still pending.";
 await loadRows();if(rows.length)open(rows[0]);
 }catch(error){notify(error.message,true);}finally{lock(false);document.dispatchEvent(new CustomEvent("wzos:session"));}
}
$("identity").addEventListener("change",()=>{if(!canLeave() || (window.wzosModulesCanLeave && !window.wzosModulesCanLeave())){$("identity").value=session.id;return;}switchIdentity();});
$("search").addEventListener("input",renderList);
$("new-order").addEventListener("click",()=>{if(canLeave()){open(null);$("title").focus();}});
$("order-form").addEventListener("input",()=>{dirty=true;$("save-state").textContent="Unsaved changes";$("atlas-output").replaceChildren();$("prepare").disabled=true;lockChecklist();});
$("order-form").addEventListener("submit",async event=>{
 event.preventDefault();if(busy)return;if(checklistDirty){notify("Save or reload your checklist changes before saving job details.",true);return;}let geometry;try{geometry=readGeometry();}catch(error){notify(error.message,true);return;}lock(true);
 const body={title:$("title").value,work_type:$("work-type").value,address:$("address").value,locality:$("locality").value,work_date:$("work-date").value||null,notes:$("notes").value,road_authority:$("road-authority").value.trim()||null,site:{...selected?.site,speed_limit_mph:$("speed-limit").value?Number($("speed-limit").value):null,lane_count:$("lane-count").value?Number($("lane-count").value):null,work_period:$("work-period").value},job_geometry:geometry};
 if(!selected){const signature=JSON.stringify(body);if(lastCreateBody!==null&&lastCreateBody!==signature)requestId=crypto.randomUUID();lastCreateBody=signature;}
 try{const record=await api(selected?`/api/orders/${selected.id}`:"/api/orders",{method:selected?"PUT":"POST",body:JSON.stringify({...body,...(selected?{expected_version:selected.version}:{request_id:requestId})})});
  open(record);lock(true);notify(`Saved locally · revision ${record.version}.`);try{await loadRows();}catch{notify(`Saved revision ${record.version}, but the job board could not refresh. Use Refresh to try again.`,true);}
 }catch(error){notify(error.message,true);$("save-state").textContent="Save not confirmed · draft retained";}finally{lock(false);}
});
async function refresh(){if(busy||!canLeave())return;lock(true);try{const id=selected?.id;await loadRows();const record=rows.find(r=>r.id===id)||rows[0];if(record)open(record);else{resetChecklist();selected=null;dirty=false;$("order-form").hidden=true;$("empty-detail").hidden=false;$("atlas-output").replaceChildren();}notify("Loaded the latest saved records.");}catch(error){notify(error.message,true);}finally{lock(false);}}
$("refresh").addEventListener("click",refresh);$("reload-order").addEventListener("click",refresh);
$("prepare").addEventListener("click",async()=>{
 if(busy||dirty||!selected)return;lock(true);$("atlas-output").replaceChildren(el("p","Checking saved job details…","muted"));
 try{const data=await api(`/api/orders/${selected.id}/preparation?expected_version=${selected.version}`,{method:"POST"});const list=el("ul");for(const item of data.questions)list.append(el("li",item.question));
 const output=$("atlas-output");output.replaceChildren(el("strong",`Preparation for revision ${data.version}`),list,el("p",data.note,"fine"));
 const advicePanel=el("details");advicePanel.append(el("summary","Forms, evidence and operational review"),el("p","Checklist entries are saved separately and have not been verified by Atlas."));for(const item of data.project_advice){const entry=el("article");entry.append(el("strong",item.finding),el("p",item.next_action));advicePanel.append(entry);}output.append(advicePanel);
 output.append(el("h4",`Agency references - library ${data.references.library_status}`));
 for(const topic of data.references.topics){const section=el("details");section.append(el("summary",`${topic.id.replaceAll("_"," ")} (${topic.candidates.length})`));
 if(!topic.candidates.length)section.append(el("p","No candidate passages available. This does not establish that no requirement applies."));
 for(const ref of topic.candidates){const article=el("article");const link=el("a",`${ref.agency}: ${ref.title}`);if(ref.url.startsWith("https://")){link.href=ref.url;link.target="_blank";link.rel="noopener noreferrer";}
 article.append(link,el("p",`${ref.edition||"Edition unspecified"} | ${ref.page?'PDF page '+ref.page:ref.section||"Section unspecified"} | ${ref.review_status} | applicability unresolved`),el("p",ref.text),el("small",`Revision ${ref.revision} | Retrieved ${ref.retrieved_at}`));for(const warning of ref.warnings)article.append(el("p",warning));article.append(el("small",`Publication status: ${ref.publication_status}`));section.append(article);}output.append(section);}
 const gaps=el("details");gaps.append(el("summary","Coverage gaps and review limits"));for(const gap of data.references.coverage_gaps)gaps.append(el("p",gap));output.append(gaps);}
 catch(error){$("atlas-output").replaceChildren();notify(error.message,true);}finally{lock(false);}
});
$("atlas-nav").addEventListener("click",()=>{document.dispatchEvent(new CustomEvent("wzos:assistant-open"));});
$("jobs-nav").addEventListener("click",()=>{window.showWzosView("orders");$("list-title").scrollIntoView({behavior:"smooth",block:"start"});});
window.addEventListener("beforeunload",event=>{if(dirty||checklistDirty){event.preventDefault();event.returnValue="";}});
(async()=>{try{const config=await api("/api/identities");identities=config.identities;if(config.mode==="verified_accounts"){identities=[await window.wzosAccount.start(config)];}for(const identity of identities){const option=el("option",`${identity.edition==="core"?"Core":"Enterprise"} · ${identity.role} · ${identity.name}`);option.value=identity.id;$("identity").append(option);}$("identity").value=config.mode==="verified_accounts"?identities[0]?.id:"enterprise-admin";await switchIdentity();if(config.mode==="verified_accounts"){$("identity").disabled=true;$("identity").closest("label").hidden=true;}}catch(error){notify(error.message,true);}})();

function lockChecklist(){
 const blocked=busy||checklistLoading||!checklistData;
 const historical=checklistData?.checklist && checklistData.checklist.version!==checklistData.latest_version;
 for(const control of $("checklist-form").querySelectorAll("select,textarea,button"))control.disabled=blocked||historical||dirty;
 $("checklist-revision").disabled=busy||checklistLoading||!checklistData;
}
function resetChecklist(){checklistGeneration++;checklistData=null;checklistDirty=false;checklistLoading=false;$("checklist-panel").hidden=true;$("checklist-items").replaceChildren();}
async function loadChecklist(version){
 const orderId=selected?.id;resetChecklist();if(!orderId)return;
 const generation=checklistGeneration;checklistLoading=true;$("checklist-panel").hidden=false;$("checklist-state").textContent="Loading checklist…";lockChecklist();
 try{
  const data=await api(`/api/orders/${orderId}/checklist${version?'?version='+version:''}`);
  if(generation!==checklistGeneration)return;
  checklistData=data;const saved=data.checklist;
  $("checklist-state").textContent=!saved?"No checklist saved yet.":`Checklist ${saved.version} · job revision ${saved.order_version} · ${saved.author_id} · ${new Date(saved.saved_at).toLocaleString()}${saved.stale?' — Job changed: review every category before saving again.':''}${saved.version!==data.latest_version?' — Historical revision (read only).':''}`;
  $("checklist-state").classList.toggle("stale",Boolean(saved?.stale));
  const revisions=$("checklist-revision");revisions.replaceChildren();
  // Keep large histories bounded in the UI; any revision remains available through the API.
  for(let n=data.latest_version;n>Math.max(0,data.latest_version-50);n--){const option=el("option",`Revision ${n}${n===data.latest_version?' (latest)':''}`);option.value=n;revisions.append(option);}
  if(!data.latest_version){const option=el("option","Unsaved");option.value="";revisions.append(option);}
  revisions.value=saved?.version||"";
  for(const [key,label] of Object.entries(data.labels)){
   const field=el("fieldset"),legend=el("legend",label),statusLabel=el("label","Review status"),status=el("select"),notesLabel=el("label","Notes / reason if not applicable"),notes=el("textarea");
   status.id=`check-${key}`;statusLabel.htmlFor=status.id;status.dataset.key=key;
   for(const [value,text] of Object.entries({not_reviewed:"Not reviewed",needs_attention:"Needs attention",reported_ready:"Reported ready",not_applicable:"Not applicable"})){const option=el("option",text);option.value=value;status.append(option);}
   status.value=saved?.items[key].status||"not_reviewed";
   notes.id=`check-notes-${key}`;notesLabel.htmlFor=notes.id;notes.rows=2;notes.maxLength=2000;notes.value=saved?.items[key].notes||"";
   field.append(legend,statusLabel,status,notesLabel,notes);$("checklist-items").append(field);
  }
 }catch(error){if(generation===checklistGeneration){$("checklist-state").textContent="Checklist unavailable. Use Reload saved to retry.";notify(error.message,true);}}
 finally{if(generation===checklistGeneration){checklistLoading=false;lock(busy);}}
}
$("checklist-form").addEventListener("input",()=>{checklistDirty=true;lock(busy);});
$("checklist-revision").addEventListener("change",()=>{
 if(checklistDirty&&!confirm("Discard unsaved checklist changes?")){$("checklist-revision").value=checklistData.checklist?.version||"";return;}
 loadChecklist($("checklist-revision").value);
});
$("checklist-form").addEventListener("submit",async event=>{
 event.preventDefault();if(busy||dirty||!selected||!checklistData||checklistLoading)return;
 const items={};for(const key of Object.keys(checklistData.labels)){items[key]={status:$("check-"+key).value,notes:$("check-notes-"+key).value.trim()};if(items[key].status==="not_applicable"&&!items[key].notes){notify("Explain each item marked not applicable before saving.",true);return;}}
 lock(true);
 try{await api(`/api/orders/${selected.id}/checklist`,{method:"PUT",body:JSON.stringify({expected_version:checklistData.latest_version,expected_order_version:selected.version,items})});checklistDirty=false;await loadChecklist();notify("Checklist saved locally. It does not authorize field use.");}
 catch(error){notify(error.message,true);}finally{lock(false);}
});

window.askAtlas=async(question,history,signal)=>{
 const clockPage=!$("clock-view").hidden;
 if(!clockPage&&(busy||dirty||checklistDirty))throw Error('Save or reload your changes before asking Atlas about the current job.');
 return api('/api/assistant/chat',{method:'POST',signal,body:JSON.stringify({question,history,page:clockPage?"time_clock":"work_orders",...(!clockPage&&selected?{order_id:selected.id,expected_version:selected.version}:{})})});
};

window.atlasStatus=()=>api("/api/assistant/status");

window.atlasNavigate=id=>{
 if(id==='time_clock'){window.showWzosView("clock");return true;}
 window.showWzosView("orders");
 const targets={job_board:'list-title',checklist:'checklist-panel',geometry:'geometry-fields',planning:'atlas-title'};
 if(!targets[id]||(id!=='job_board'&&!selected)||(id==='planning'&&!session?.can_prepare_atlas))return false;
 const target=$(targets[id]);if(id==='geometry')target.closest('details').open=true;
 target.scrollIntoView({behavior:'smooth',block:'center'});target.setAttribute('tabindex','-1');target.focus({preventScroll:true});return true;
};

window.wzosClock={api,getSession:()=>session,getOrders:()=>rows};
window.showWzosView=view=>{
 if(!canLeave() || (window.wzosModulesCanLeave && !window.wzosModulesCanLeave()))return;
 $("team-view").hidden=!["training","messages","navigation"].includes(view);
 $("report-view").hidden=view!=="report";
 $("orders-view").hidden=view!=="orders";$("clock-view").hidden=view!=="clock";$("modules-view").hidden=!["forms","schedule"].includes(view);
 for(const [id,on] of [["training-nav",view==="training"],["messages-nav",view==="messages"],["navigation-nav",view==="navigation"],["report-nav",view==="report"],["jobs-nav",view==="orders"],["clock-nav",view==="clock"],["forms-nav",view==="forms"],["schedule-nav",view==="schedule"]]){ $(id).classList.toggle("active",on);if(on)$(id).setAttribute("aria-current","page");else $(id).removeAttribute("aria-current");}
 document.querySelector(".breadcrumb + strong").textContent=({training:"Video training",messages:"Messaging",navigation:"Navigation",report:"Work Zone Report",clock:"Time clock",forms:"Forms hub",schedule:"Schedule management"})[view]||"Work orders";
 document.dispatchEvent(new CustomEvent("wzos:view",{detail:view}));
 if(view==="clock")document.dispatchEvent(new CustomEvent("wzos:clock-open"));
};
$("clock-nav").addEventListener("click",()=>window.showWzosView("clock"));
