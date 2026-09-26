"use strict";
// Adapted interaction pattern from recovered Core GlobalAssistant / AssistantBubble.
// Quick guides plus server-mediated local inference; no autonomous actions.
(() => {
 const byId=id=>document.getElementById(id);
 const topics={
  orders:{match:/work order|save|job name|new job|draft|edit/i,target:"order-form",text:"I can help you manage a work order. Choose a job on the board, or select New work order. Enter the job name, work type, location and locality, then save. Reported site details help Atlas prepare relevant questions. If a save conflicts, reload the saved record before editing again."},
  checklist:{match:/checklist|readiness|revision|stale/i,target:"checklist-panel",text:"Save a work order first, then use its Job readiness checklist. Review all five categories, record notes and save the checklist separately. Explain any item marked Not applicable. Older revisions stay read-only, and a job change flags the checklist for review. Reported ready is not field approval."},
  planning:{match:/atlas|planning|reference|source|sign|flagger|mutcd|vdot|osha|gemma|recommend/i,target:"report-nav",text:"Open Work Zone Report and choose a saved Enterprise job. Review its geometry, checklist revision and linked incident drafts, then select Let Atlas help. I can surface missing information and candidate agency passages with page references. Save report revision preserves a personal draft and its reference results; open it from Saved draft reports. Refresh returns to current inputs. Review reference applicability and edition. Automatic sign placement is not connected in this preview. Core app guidance remains available here."},
  forms:{match:/form|pdf|document|permit|jsa|email/i,target:"forms-nav",text:"Open Forms hub to create, save and reopen incident, vehicle-inspection or JSA planning drafts with an optional work-order link. Choose Vehicle inspection for vehicle ID, mileage, pre/post-trip checks and defects. Failed checks need a description; saving does not clear a vehicle for operation. General users see their own drafts; admins see their organization drafts. Other templates, official submissions, PDF and email delivery are pending."},
  time:{match:/clock|timesheet|track|hours|payroll|break|shift/i,target:"clock-title",text:"Open Time clock to start your own shift, select an optional work order and task, switch tasks, record breaks, or clock out. Time history saves locally; admins can view their test team's records. Work time excludes tracked breaks in this preview. GPS, offline recording, pay calculations and corrections are not enabled. I can guide you, but only your clicks on the clock controls record time."},
  dispatch:{match:/dispatch|schedul|assign|crew/i,target:"schedule-nav",text:"Open Schedule management. Admins can create and edit team schedule drafts with start/end times, location, notes and an optional work-order link. General users can read the team schedule. Drafts can assign test organization members and reject overlapping assignments. Date filtering uses UTC start date. No dispatch or notifications are sent."},
  maps:{match:/map|navigat|street|image|route|gps/i,text:"In Work Zone Report, Load site imagery displays Google hybrid imagery for saved work-limit or approach coordinates when Maps access is configured. Nearby Street View may show a different position or an older capture; verify the site. Orange lines are reported work limits and blue lines are approaches. These are not sign placements. Navigation opens a saved work-order address in Google Maps for user verification. Offline maps, live hazards and imagery export remain unavailable."},
  messages:{match:/message|chat|video|meeting|contact/i,text:"Messaging has a synthetic test inbox for test organization members. Stored messages are not emails, SMS or real employee deliveries. Video meetings remain unconnected."},
  training:{match:/train|course|certif|quiz/i,text:"Training has the recovered V1 catalog and personal study-status tracking. Video content, quizzes and accreditation still need review. Study status does not count as course completion or issue a certificate."},
  integrations:{match:/integrat|connect|external|sync/i,text:"Integrations will connect approved outside services to WZOS. Connections are not configurable from this preview. Each integration needs its own tested permissions and settings; I will show its actual connection status when that workflow is available."},
  admin:{match:/admin|organization|permission|access|role|edition|account/i,text:"Both editions will have general and admin access. In this local preview, general test identities see their own work orders; admins see their test organization's orders. The Test identity selector is a demonstration tool, not production sign-in. Advanced planning is Enterprise-only; app guidance is available in both editions."}
 };
 let returnFocus=null, target=null, greetingDismissed=false, chatBusy=false, chatEpoch=0, chatHistory=[], chatController=null;
 const panel=byId("assistant-panel"), dock=byId("assistant-dock");
 function answer(key){
  byId("assistant-navigation").replaceChildren();
  const topic=topics[key];target=topic?.target||null;
  byId("assistant-answer").textContent=topic?.text||"I can help with WZOS functions. Choose a topic above so I can give you the right steps. Use the question box for a conversational reply.";
  byId("assistant-go").hidden=!target;
 }
 function openAssistant(){
  if(!panel.hidden)return;
  returnFocus=document.activeElement;panel.hidden=false;dock.hidden=true;
  byId("assistant-open").setAttribute("aria-expanded","true");
  answer(byId("assistant-topic").value);byId("assistant-topic").focus();
  window.atlasStatus().then(data=>{document.querySelector(".assistant-mode").textContent=data.ready?"Atlas conversation is ready on this computer. Verify AI guidance before use.":"Atlas conversation is unavailable. Quick guides remain available below.";}).catch(()=>{document.querySelector(".assistant-mode").textContent="Unable to check Atlas connection. Quick guides remain available.";});
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
 byId("assistant-question-form").addEventListener("submit",async event=>{
  event.preventDefault();if(chatBusy)return;
  const question=byId("assistant-question").value.trim();if(!question)return;
  const epoch=chatEpoch;chatBusy=true;chatController=new AbortController();byId("assistant-stop").hidden=false;byId("assistant-topic").disabled=true;byId("assistant-navigation").replaceChildren();const submit=byId("assistant-question-form").querySelector('button');submit.disabled=true;
  byId("assistant-go").hidden=true;byId("assistant-answer").textContent="Atlas is thinking...";
  try{
   const data=await window.askAtlas(question,chatHistory,chatController.signal);
   if(epoch!==chatEpoch)return;
   byId("assistant-answer").textContent=data.answer;
   if(data.order_version){const basis=document.createElement("p");basis.className="fine";basis.textContent=`Based on saved job revision ${data.order_version}. No actions were performed.`;byId("assistant-answer").append(basis);}
   if(data.time_basis && !byId('clock-view').hidden){const basis=document.createElement('p');basis.className='fine';basis.textContent=`Saved clock status: ${data.time_basis.status.replaceAll('_',' ')} · ${new Date(data.time_basis.as_of).toLocaleTimeString()}. Atlas performed no clock action.`;byId('assistant-answer').append(basis);}
   if(data.checklist_basis){const basis=document.createElement('p');basis.className='fine';const c=data.checklist_basis;basis.textContent=c.status==='not_saved'?'No saved readiness checklist.':`Checklist revision ${c.version} · job revision ${c.order_version}${c.stale?' · Job changed: review needed.':''}`;byId('assistant-answer').append(basis);}
   for(const action of data.navigation||[]){const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent=action.label;button.addEventListener('click',()=>{closeAssistant();if(!window.atlasNavigate(action.id))openAssistant();});byId('assistant-navigation').append(button);}
   chatHistory=[...chatHistory,{role:'user',content:question},{role:'assistant',content:data.answer}].slice(-8);while(chatHistory.reduce((sum,turn)=>sum+turn.content.length,0)>8000)chatHistory.shift();
   if(data.citations.length){const note=document.createElement('p');note.textContent='Candidate references supplied to Atlas (applicability unreviewed):';byId("assistant-answer").append(note);for(const ref of data.citations){const link=document.createElement('a');link.textContent=`${ref.agency}: ${ref.title} - ${ref.page?'PDF page '+ref.page:ref.section||'section'} (${ref.review_status})`;link.href=ref.url;link.target='_blank';link.rel='noopener noreferrer';byId("assistant-answer").append(link,document.createElement('br'));}}
  }catch(error){if(epoch===chatEpoch)byId("assistant-answer").textContent=error.name==="AbortError"?"Reply stopped. Your saved work is unchanged.":error.message;}
  finally{chatBusy=false;submit.disabled=false;chatController=null;byId("assistant-stop").hidden=true;byId("assistant-topic").disabled=false;}
 });
 function clearContext(){chatController?.abort();chatEpoch++;chatHistory=[];byId("assistant-question").value="";byId("assistant-topic").value="orders";answer("orders");}
 byId("assistant-stop").addEventListener("click",()=>chatController?.abort());
 document.addEventListener('wzos:job-context',clearContext);
 document.addEventListener('wzos:time-context',clearContext);
 document.addEventListener('wzos:view',clearContext);
 document.addEventListener('wzos:report-context',clearContext);
 byId("assistant-go").addEventListener("click",()=>{
  if(target==="forms-nav"||target==="schedule-nav"||target==="report-nav")window.showWzosView(target.split("-")[0]);else if(target==="clock-title")window.showWzosView("clock");else window.showWzosView("orders");
  const node=target&&byId(target);
  if(!node||node.hidden){byId("assistant-answer").textContent="Choose or save a work order first so I can show you that section.";return;}
  closeAssistant();node.scrollIntoView({behavior:"smooth",block:"center"});node.setAttribute("tabindex","-1");node.focus({preventScroll:true});
 });
 panel.addEventListener("keydown",event=>{if(event.key==="Escape"){event.preventDefault();closeAssistant();}});
 document.addEventListener("wzos:assistant-open",openAssistant);
 byId("identity").addEventListener("change",clearContext);
})();
