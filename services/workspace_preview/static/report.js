"use strict";
(() => {
 const $=id=>document.getElementById(id), api=(...args)=>window.wzosClock.api(...args);
 let epoch=0, current=null, saveRequest=null, saving=false;
 const node=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 function section(title){const s=node("section","");s.className="panel report-section";s.append(node("h2",title));$("report-content").append(s);return s;}
 function reset(){epoch++;current=null;saveRequest=null;$("report-save").disabled=true;$("report-history").replaceChildren();$("report-content").replaceChildren();$("report-references").replaceChildren();$("report-prepare").disabled=true;}
 async function load(){
  reset();const generation=epoch,id=$("report-order").value;if(!id)return;
  $("report-message").textContent="Loading saved report basis…";
  try{const data=await api(`/api/orders/${encodeURIComponent(id)}/report`);if(generation!==epoch)return;current=data;
   render(data);history(id,generation);
  }catch(error){if(generation===epoch)$("report-message").textContent=error.message;}
 }
 function render(data){$("report-content").replaceChildren();
   $("report-message").textContent=`Work-order revision ${data.order.version} · assembled ${new Date(data.generated_at).toLocaleString()}`;
   const job=section("Work order");job.append(node("h3",data.order.title),node("p",`${data.order.work_type.replaceAll("_"," ")} · ${data.order.address}`),node("p",data.order.notes||"No job notes."));
   const geometry=section("Reported geometry");
   if(data.order.job_geometry){
    const g=data.order.job_geometry, list=node("dl","");list.className="report-measurements";
    const fact=(label,value,unit="")=>{list.append(node("dt",label),node("dd",value==null||value===""?"Not recorded":String(value).replaceAll("_"," ")+unit));};
    fact("Closure",g.closure_type);fact("Road class",g.road_class);fact("Placement scenario",g.placement_scenario);fact("Travel direction",g.travel_direction);fact("Duration",g.duration_hours," hours");fact("Lane width",g.lane_width_ft," ft");fact("Available sight distance",g.available_sight_distance_ft," ft");fact("Measurement source",g.geometry_source);geometry.append(list,node("p","Customer-reported measurements · verification required."));
    function points(title,values){if(!values?.length)return;const d=node("details","");d.append(node("summary",title));const ol=node("ol","");for(const point of values)ol.append(node("li",`${point.latitude.toFixed(6)}, ${point.longitude.toFixed(6)}`));d.append(ol);geometry.append(d);}
    points("Work-limit coordinates",g.work_limits);
    for(const [index,approach] of (g.approaches||[]).entries()){geometry.append(node("h3",`Approach ${index+1} · ${approach.travel_direction}`),node("p",`Lane width: ${approach.lane_width_ft} ft · Sight distance: ${approach.available_sight_distance_ft} ft`),node("p",`Measured ${approach.measured_on} · ${approach.measurement_source}`),node("p",approach.obstruction_notes));points("Approach coordinates · upstream toward work area",approach.path);}
   }else geometry.append(node("p","Missing: enter work limits and measured approaches in Work orders."));
   const checklist=section("Readiness review");
   if(!data.checklist)checklist.append(node("p","No saved checklist. Review the job in Work orders."));
   else{checklist.append(node("p",`Checklist revision ${data.checklist.version} · based on work-order revision ${data.checklist.order_version}${data.checklist.stale?" · STALE: job changed; review every category":" · user-reported review only"}`));for(const [key,item] of Object.entries(data.checklist.items))checklist.append(node("h3",key.replaceAll("_"," ")),node("p",`${item.status.replaceAll("_"," ")}: ${item.notes||"No notes"}`));}
   const forms=section("Linked incident drafts");forms.append(node("p",`${data.forms.length} of ${data.forms_total} linked records shown. These do not establish required-form completion.`));
   for(const form of data.forms){const d=node("details","");d.append(node("summary",`${form.title} · revision ${form.version} · ${form.status}`),node("p",form.details));forms.append(d);}
   const limits=section("Sections still requiring work");for(const value of data.limitations)limits.append(node("p",value));
   $("report-prepare").disabled=false;$("report-save").disabled=saving;
 }
 async function enter(){reset();$("report-order").replaceChildren();$("report-message").textContent="";
  if(!window.wzosClock.getSession()?.can_prepare_atlas){$("report-message").textContent="Work Zone Report is an Enterprise feature. Core work orders remain available.";return;}
  const generation=epoch;
  try{const result=await api('/api/orders');if(generation!==epoch)return;for(const order of result.items){const option=node("option",order.title);option.value=order.id;$("report-order").append(option);}if(!result.items.length)$("report-message").textContent="Create and save a work order first.";else load();}catch(error){if(generation===epoch)$("report-message").textContent=error.message;}
 }
 async function history(id,generation){
  try{const data=await api(`/api/orders/${encodeURIComponent(id)}/reports`);if(generation!==epoch)return;
   $("report-history").replaceChildren(node("p",`${data.total} saved drafts · showing latest ${data.items.length}`));
   for(const item of data.items){const button=node("button",`${new Date(item.saved_at).toLocaleString()} · job revision ${item.order_version}${item.basis_changed?" · inputs changed":""}`);button.className="job";button.type="button";
    button.onclick=async()=>{const generation=++epoch;$("report-save").disabled=true;$("report-prepare").disabled=true;$("report-references").replaceChildren();
     try{const saved=await api(`/api/orders/${encodeURIComponent(id)}/reports/${item.id}`);if(generation!==epoch)return;current=null;render(saved.report);renderReferences(saved.report.preparation);$("report-save").disabled=true;$("report-prepare").disabled=true;$("report-message").textContent=`SAVED DRAFT · ${new Date(saved.saved_at).toLocaleString()}${saved.basis_changed?" · Inputs have changed; refresh for the current job.":" · Read only. Refresh to return to current inputs."}`;}catch(error){if(generation===epoch)$("report-message").textContent=error.message;}
    };$("report-history").append(button);}
  }catch(error){if(generation===epoch)$("report-history").replaceChildren(node("p",error.message));}
 }
 $("report-save").onclick=async()=>{
  if(!current||saving)return;const generation=epoch,id=current.order.id;
  saveRequest=saveRequest||{request_id:crypto.randomUUID(),expected_order_version:current.order.version};saving=true;$("report-save").disabled=true;
  try{await api(`/api/orders/${encodeURIComponent(id)}/reports`,{method:"POST",body:JSON.stringify(saveRequest)});if(generation!==epoch)return;saveRequest=null;$("report-message").textContent="Draft report saved with its reference results. Open it below to review.";await history(id,generation);}
  catch(error){if(generation===epoch)$("report-message").textContent=error.message;}finally{saving=false;if(generation===epoch)$("report-save").disabled=!current;}
 };
 $("report-nav").onclick=()=>window.showWzosView("report");
 document.addEventListener("wzos:view",event=>{if(event.detail==="report")enter();else reset();});
 document.addEventListener("wzos:session",()=>{reset();if(!$("report-view").hidden)enter();});
 $("report-order").onchange=load;$("report-refresh").onclick=load;
 function renderReferences(data){const output=$("report-references");output.replaceChildren(node("h2","Atlas reference preparation"),node("p",data.note));
   for(const question of data.questions||[])output.append(node("p",question.question));
   for(const recommendation of data.form_recommendations||[]) {output.append(node("h3",recommendation.title),node("p",recommendation.priority.replaceAll("_"," ")),node("p",recommendation.reason));}
   for(const topic of data.references.topics){const d=node("details","");d.append(node("summary",`${topic.id.replaceAll("_"," ")} · ${topic.candidates.length} candidates`));
    for(const c of topic.candidates){d.append(node("h3",c.title),node("p",`${c.agency} · ${c.edition||"Edition unverified"} · ${c.page?"page "+c.page:c.section||"section unavailable"} · ${c.review_status} · ${c.publication_status}`),node("p",c.text),node("p","Revision: "+c.revision));if(c.url.startsWith("https://")){const link=node("a","Official source");link.href=c.url;link.target="_blank";link.rel="noopener noreferrer";d.append(link);}}
    output.append(d);}
   for(const gap of data.references.coverage_gaps)output.append(node("p",gap));
 }
 $("report-prepare").onclick=async()=>{
  if(!current)return;const generation=epoch,basis=current.order;$("report-prepare").disabled=true;const output=$("report-references");output.replaceChildren(node("p","Checking saved job against the reference library…"));
  try{const data=await api(`/api/orders/${encodeURIComponent(basis.id)}/preparation?expected_version=${basis.version}`,{method:"POST"});if(generation!==epoch)return;renderReferences(data);
  }catch(error){if(generation===epoch)output.replaceChildren(node("p",error.message));}finally{if(generation===epoch)$("report-prepare").disabled=false;}
 };
})();
