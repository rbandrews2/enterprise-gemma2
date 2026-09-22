"use strict";
// Adapted interaction pattern from recovered Core GlobalAssistant / AssistantBubble.
// Reviewed local help only: no remote calls, transcript storage, or autonomous actions.
(() => {
 const byId=id=>document.getElementById(id);
 const topics={
  orders:{match:/work order|save|job name|new job|draft|edit/i,target:"order-form",text:"I can help you manage a work order. Choose a job on the board, or select New work order. Enter the job name, work type, location and locality, then save. Reported site details help Atlas prepare relevant questions. If a save conflicts, reload the saved record before editing again."},
  checklist:{match:/checklist|readiness|revision|stale/i,target:"checklist-panel",text:"Save a work order first, then use its Job readiness checklist. Review all five categories, record notes and save the checklist separately. Explain any item marked Not applicable. Older revisions stay read-only, and a job change flags the checklist for review. Reported ready is not field approval."},
  planning:{match:/atlas|planning|reference|source|sign|flagger|mutcd|vdot|osha|gemma|recommend/i,target:"atlas-title",text:"For a saved Enterprise job, select Let Atlas help in Prepare the next step. I can surface missing information and candidate agency passages with page references. Review their applicability and edition. Automatic sign placement and Gemma conversation are not connected in this preview. Core app guidance remains available here."},
  forms:{match:/form|pdf|document|permit|jsa|email/i,text:"Forms and document delivery are planned shared workflows. The saved readiness checklist is available now; official form selection, PDF creation and email delivery are not connected to this workspace yet. I can explain their availability, but cannot create or send those documents here."},
  time:{match:/clock|timesheet|track|hours|payroll/i,text:"Time clock and tracking are part of WZOS Core and Enterprise. The recovered Core workflow is being integrated; clock-in, clock-out and timesheet changes are unavailable in this preview. No time entry has been recorded."},
  dispatch:{match:/dispatch|schedul|assign|crew/i,text:"Scheduling and dispatch will organize work windows, assignments and crew coordination. They are not connected here yet. You can save a planned work date and job notes now; that does not dispatch anyone or send a notification."},
  maps:{match:/map|navigat|street|image|route|gps/i,text:"Maps and navigation are being brought into this workspace from the existing V2 implementation. This page cannot yet open job imagery, navigate a crew or place signs. Record the work location now; measured geometry and imagery controls are the next integration steps."},
  messages:{match:/message|chat|video|meeting|contact/i,text:"Employee messaging and video meetings are planned communication tools. They are not connected to this preview. Asking me for help here sends no message to another person and starts no meeting."},
  training:{match:/train|course|certif|quiz/i,text:"Training will provide courses and completion records. That module is not connected here yet. I can guide users through it once integrated; a conversation with Atlas will not count as course completion or issue a certificate."},
  integrations:{match:/integrat|connect|external|sync/i,text:"Integrations will connect approved outside services to WZOS. Connections are not configurable from this preview. Each integration needs its own tested permissions and settings; I will show its actual connection status when that workflow is available."},
  admin:{match:/admin|organization|permission|access|role|edition|account/i,text:"Both editions will have general and admin access. In this local preview, general test identities see their own work orders; admins see their test organization's orders. The Test identity selector is a demonstration tool, not production sign-in. Advanced planning is Enterprise-only; app guidance is available in both editions."}
 };
 let returnFocus=null, target=null, greetingDismissed=false;
 const panel=byId("assistant-panel"), dock=byId("assistant-dock");
 function answer(key){
  const topic=topics[key];target=topic?.target||null;
  byId("assistant-answer").textContent=topic?.text||"I can help with WZOS functions. Choose a topic above so I can give you the right steps. Free-form Gemma conversation is not connected in this preview.";
  byId("assistant-go").hidden=!target;
 }
 function openAssistant(){
  if(!panel.hidden)return;
  returnFocus=document.activeElement;panel.hidden=false;dock.hidden=true;
  byId("assistant-open").setAttribute("aria-expanded","true");
  answer(byId("assistant-topic").value);byId("assistant-topic").focus();
 }
 function closeAssistant(){
  panel.hidden=true;dock.hidden=false;byId("assistant-open").setAttribute("aria-expanded","false");
  byId("assistant-greeting").hidden=greetingDismissed;
  const focus=returnFocus?.isConnected&&!returnFocus.closest("[hidden]")?returnFocus:byId("assistant-open");focus.focus();
 }
 byId("assistant-open").addEventListener("click",openAssistant);
 byId("assistant-greet-open").addEventListener("click",openAssistant);
 byId("assistant-close").addEventListener("click",closeAssistant);
 byId("assistant-dismiss").addEventListener("click",()=>{greetingDismissed=true;byId("assistant-greeting").hidden=true;byId("assistant-open").focus();});
 byId("assistant-topic").addEventListener("change",()=>answer(byId("assistant-topic").value));
 byId("assistant-question-form").addEventListener("submit",event=>{
  event.preventDefault();const question=byId("assistant-question").value.trim();
  // Prefer the selected topic when several keywords overlap; never treat text as an action.
  const selected=byId("assistant-topic").value;
  const key=topics[selected].match.test(question)?selected:Object.keys(topics).find(k=>topics[k].match.test(question));
  if(key)byId("assistant-topic").value=key;answer(key);
 });
 byId("assistant-go").addEventListener("click",()=>{
  const node=target&&byId(target);
  if(!node||node.hidden){byId("assistant-answer").textContent="Choose or save a work order first so I can show you that section.";return;}
  closeAssistant();node.scrollIntoView({behavior:"smooth",block:"center"});node.setAttribute("tabindex","-1");node.focus({preventScroll:true});
 });
 panel.addEventListener("keydown",event=>{if(event.key==="Escape"){event.preventDefault();closeAssistant();}});
 document.addEventListener("wzos:assistant-open",openAssistant);
 byId("identity").addEventListener("change",()=>{byId("assistant-question").value="";byId("assistant-topic").value="orders";answer("orders");});
})();
