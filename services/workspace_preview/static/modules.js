"use strict";
(() => {
 const $=id=>document.getElementById(id), api=(...args)=>window.wzosClock.api(...args);
 let kind="forms", current=null, dirty=false, saving=false, epoch=0, offset=0, total=0;
 const text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 const notice=value=>{$("module-notice").textContent=value;};
 window.wzosModulesCanLeave=()=>!saving&&(!dirty||confirm("Leave unsaved module changes?"));
 function localTime(value){if(!value)return "";const d=new Date(value);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);}
 function edit(row){
  current=row||{id:crypto.randomUUID(),version:0};dirty=false;$("module-form").hidden=false;
  for(const [id,key] of [["name","title"],["location","location"],["details","details"]])$("module-"+id).value=row?.[key]||"";
  const none=text("option","No linked work order");none.value="";$("module-order").replaceChildren(none);
  for(const order of window.wzosClock.getOrders()){const option=text("option",order.title);option.value=order.id;$("module-order").append(option);}
  $("module-order").value=row?.order_id||"";
  $("module-start").value=localTime(row?.start);$("module-end").value=localTime(row?.end);$("module-status").value=row?.status||"draft";
  $("module-version").textContent=row?`Saved revision ${row.version} · ${new Date(row.updated_at).toLocaleString()}`:"Unsaved draft";
  const readOnly=kind==="schedule"&&window.wzosClock.getSession()?.role!=="admin";
  for(const input of $("module-form").elements)input.disabled=readOnly;
 }
 async function refresh(){
  const generation=++epoch;
  try{const data=await api(`/api/modules/${kind}?offset=${offset}`);if(generation!==epoch)return;
   total=data.total;$("module-list").replaceChildren();$("module-new").hidden=!data.can_edit;
   for(const row of data.items){const button=text("button",`${row.title} · ${row.status}${row.start?" · "+new Date(row.start).toLocaleString():""}`);button.type="button";button.className="job";button.onclick=()=>{if(window.wzosModulesCanLeave())edit(row);};$("module-list").append(button);}
   if(!data.items.length)$("module-list").append(text("p","No saved records on this page."));
   $("module-page").textContent=`${total} records · ${data.items.length?offset+1:0}–${offset+data.items.length}`;
   $("module-prev").disabled=offset===0;$("module-next").disabled=offset+25>=total;
  }catch(error){if(generation===epoch)notice(error.message);}
 }
 function show(view){
  if(!["forms","schedule"].includes(view))return;
  kind=view;offset=0;dirty=false;current=null;$("module-form").hidden=true;notice("");
  $("module-title").textContent=kind==="forms"?"Forms hub":"Schedule management";
  $("module-description").textContent=kind==="forms"?"Incident drafts: record title, location and description. These are internal drafts, not agency submissions. Other V1 form templates are pending.":"Team schedule drafts. Admins edit; team members can read. Saving does not dispatch or notify anyone.";
  $("module-times").hidden=kind!=="schedule";$("module-start").required=$("module-end").required=kind==="schedule";
  refresh();
 }
 for(const key of ["forms","schedule"])$(key+"-nav").onclick=()=>window.showWzosView(key);
 document.addEventListener("wzos:view",event=>show(event.detail));
 document.addEventListener("wzos:session",()=>{epoch++;dirty=false;current=null;$("module-list").replaceChildren();$("module-form").hidden=true;if(!$("modules-view").hidden)show(kind);});
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
  if(kind==="schedule"){body.start=new Date($("module-start").value).toISOString();body.end=new Date($("module-end").value).toISOString();if(body.end<=body.start){notice("End must be after start.");return;}}
  saving=true;for(const input of $("module-form").elements)input.disabled=true;$("identity").disabled=true;
  try{const saved=await api(`/api/modules/${kind}/${record.id}`,{method:"PUT",body:JSON.stringify(body)});if(generation!==epoch)return;edit(saved);notice("Draft saved. No submission or notification was sent.");await refresh();}
  catch(error){notice(error.message);}finally{saving=false;for(const input of $("module-form").elements)input.disabled=false;$("identity").disabled=false;}
 };
})();
