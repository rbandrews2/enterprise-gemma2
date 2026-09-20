"use strict";
const el = id => document.getElementById(id);
let record = null, draft = null, editing = null, dirty = false, formDirty = false, busy = false;
function status(message) { el("status").textContent = message; }
async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(response.status === 409 ? "Project changed elsewhere. Your draft is retained. Reload to review the latest version before editing again." : `Request failed (${response.status}): ${JSON.stringify(body.detail || body.error || body)}`);
  return body;
}
function discard() { return !(dirty || formDirty) || window.confirm("Discard unsaved edits?"); }
async function refresh() {
  if(busy) return;
  try {
    const items = []; let offset = 0;
    while (true) {
      const page = await api(`/v2/projects?limit=50&offset=${offset}`);
      items.push(...page.results); offset += page.results.length;
      if (offset >= page.total || !page.results.length) break;
    }
    el("project").replaceChildren(...items.map(p => new Option(`${p.name} · v${p.version}`, p.project_id)));
    el("load").disabled = !items.length;
    status(items.length ? "Select a project and load its latest revision." : "No saved projects. Create a development project through /docs to begin.");
  } catch (error) { status(error.message); }
}
function render() {
  el("atlas").disabled=false;
  el("atlasResults").replaceChildren();
  el("heading").textContent = `${draft.name} · loaded revision ${record.version}${dirty ? " · unsaved draft" : ""}`;
  el("markers").replaceChildren();
  const svg = el("plot"); svg.replaceChildren();
  const points = draft.annotations || [];
  if (!points.length) { el("markers").textContent = "No proposed markers yet."; return; }
  const xs = points.map(p => p.longitude), ys = points.map(p => p.latitude);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  points.forEach((p, i) => {
    const button = document.createElement("button"); button.textContent = `${i+1}. ${p.label} · ${p.kind}`;
    button.onclick = () => { if (!formDirty || window.confirm("Discard unapplied marker edits?")) edit(p.id); };
    el("markers").append(button);
    const x = maxX === minX ? 300 : 40 + 520*(p.longitude-minX)/(maxX-minX);
    const y = maxY === minY ? 180 : 320 - 280*(p.latitude-minY)/(maxY-minY);
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    for (const [k,v] of Object.entries({cx:x,cy:y,r:12,fill:"#176b78"})) circle.setAttribute(k,v);
    const text = document.createElementNS(circle.namespaceURI,"text"); text.setAttribute("x",x+16); text.setAttribute("y",y+5); text.textContent=i+1;
    svg.append(circle,text);
  });
}
function edit(id=null) {
  if(busy) return;
  editing=id; const p=draft.annotations.find(a=>a.id===id);
  el("editor").reset(); el("fields").disabled=false;
  for (const key of ["kind","label","latitude","longitude","rationale"]) if(p) el(key).value=p[key];
  el("markerId").value=p?.id || ""; el("markerId").readOnly=!!p;
  if(!p) { el("latitude").value=draft.intake.location.latitude ?? ""; el("longitude").value=draft.intake.location.longitude ?? ""; }
  el("evidence").replaceChildren(...draft.evidence.map(e=>new Option(`${e.id} · ${e.kind}`,e.id,false,p?.evidence_ids.includes(e.id)||false)));
  el("remove").disabled=!p; formDirty=false;
}
el("load").onclick=async()=>{
  if(busy) return;
  if(!discard()) return;
  busy=true; el("fields").disabled=true;
  try { record=await api(`/v2/projects/${el("project").value}`); draft=structuredClone(record.draft); draft.annotations ||= [];
    dirty=false; formDirty=false; render(); busy=false; edit(); el("new").disabled=false; el("save").disabled=false; status("Loaded. All markers remain proposed and unverified.");
  } catch(error) { status(error.message); } finally {busy=false;el("fields").disabled=!draft;}
};
el("new").onclick=()=>{if(!formDirty || window.confirm("Discard unapplied marker edits?")) edit();};
el("editor").oninput=()=>{formDirty=true;};
el("editor").onsubmit=event=>{
  event.preventDefault(); if(busy) return; const id=el("markerId").value.trim();
  if(!editing && draft.annotations.some(a=>a.id===id)) {status("Choose a unique marker ID.");return;}
  const evidence_ids=Array.from(el("evidence").selectedOptions,o=>o.value);
  const kind=el("kind").value;
  if(kind==="traffic_observation" && !draft.evidence.some(e=>e.kind==="traffic" && evidence_ids.includes(e.id))) {status("Select traffic evidence for this marker.");return;}
  if(!editing && draft.annotations.length>=200) {status("The project limit is 200 markers.");return;}
  const marker={id,kind,label:el("label").value.trim(),latitude:Number(el("latitude").value),longitude:Number(el("longitude").value),rationale:el("rationale").value.trim(),evidence_ids,status:"proposed"};
  if(!marker.label || !marker.rationale) {status("Label and rationale cannot be blank.");return;}
  draft.annotations=editing ? draft.annotations.map(a=>a.id===editing?marker:a) : [...draft.annotations,marker];
  dirty=true; render(); edit(id); status("Marker applied locally. Save the project revision to persist it.");
};
el("remove").onclick=()=>{if(busy) return;draft.annotations=draft.annotations.filter(a=>a.id!==editing);dirty=true;render();edit();};
el("save").onclick=async()=>{
  if(busy) return;
  if(formDirty) {status("Apply or discard the marker edits before saving.");return;}
  if(!dirty) {status("No applied changes to save.");return;}
  busy=true; el("fields").disabled=true; el("save").disabled=true;
  try { record=await api(`/v2/projects/${record.project_id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({...draft,expected_version:record.version})});
    draft=structuredClone(record.draft);dirty=false;render();status(`Saved revision ${record.version}. Field-use approval remains false.`);
  } catch(error) {status(error.message);} finally {busy=false;el("fields").disabled=false;el("save").disabled=false;}
};
el("refresh").onclick=refresh;
el("atlas").onclick=async()=>{
  if(busy || !record) return;
  if(dirty || formDirty) {status("Save or discard your edits before asking Atlas to review the saved project.");return;}
  busy=true; el("fields").disabled=true; el("atlas").disabled=true;
  const box=el("atlasResults"); box.replaceChildren();
  function line(tag,text,parent=box) {const node=document.createElement(tag);node.textContent=text;parent.append(node);return node;}
  try {
    const result=await api(`/v2/projects/${record.project_id}/atlas/prepare?expected_version=${record.version}`,{method:"POST"});
    line("h3",`Preparation for revision ${result.project_version}`);
    line("p","Official-reference preparation only. Gemma was not called; no sign or flagger placements were generated.");
    line("h4","Project recommendations and gaps");
    for(const category of ["project_context","forms","evidence","requested_function","operations"]) {
      const items=result.project_advice.filter(a=>a.category===category);
      const group=line("details","");line("summary",`${category.replaceAll("_"," ")} · ${items.length} review items`,group);
      for(const item of items) {
        line("h5",item.finding,group);
        line("p",`Status: ${item.state.replaceAll("_"," ")} · ${item.priority.replaceAll("_"," ")}`,group);
        line("p",item.reason,group);line("p",`Next: ${item.next_action}`,group);
      }
    }
    line("p","These are project-review suggestions, not verified legal requirements. Unknown items may already be handled outside WZOS.");
    line("h4","Information to confirm");
    const questions=line("ul",""); for(const q of result.questions) line("li",q.question,questions);
    line("h4","Evidence review");
    const issues=line("ul",""); for(const issue of result.evidence_review.issues) line("li",issue,issues);
    line("h4","Official reference candidates — applicability unresolved");
    for(const topic of result.references.topics) {
      const details=line("details",""); line("summary",`${topic.id.replaceAll("_"," ")} · ${topic.candidates.length} candidates`,details);
      if(!topic.candidates.length) line("p","No usable reference found. This does not mean no requirement applies.",details);
      for(const c of topic.candidates) {
        line("h5",`${c.agency}: ${c.title}`,details);
        line("p",`Edition: ${c.edition || "unknown"}; page: ${c.page ?? "n/a"}; section: ${c.section || "n/a"}; review: ${c.review_status}; revision: ${c.revision}`,details);
        line("p",c.text,details);
        try {const url=new URL(c.url);if(url.protocol==="https:"){const link=line("a","Official source",details);link.href=url.href;link.target="_blank";link.rel="noopener noreferrer";}} catch {}
      }
    }
    line("h4","Remaining gaps");
    const gaps=line("ul","");for(const gap of [...result.blockers,...result.references.coverage_gaps]) line("li",gap,gaps);
    status("Atlas preparation complete. Review questions and sources below; no placements were changed.");
  } catch(error) {status(error.message);} finally {busy=false;el("fields").disabled=false;el("atlas").disabled=false;}
};
window.addEventListener("beforeunload",event=>{if(dirty||formDirty){event.preventDefault();event.returnValue="";}});
refresh();
