"use strict";
(() => {
 const make = (tag, text) => {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  return element;
 };
 function field(form, title, choices, type = "text") {
  const label = make("label", title);
  const input = make(choices ? "select" : "input");
  if (choices) for (const choice of choices) input.add(new Option(choice, choice));
  else input.type = type;
  input.setAttribute("aria-label",title);
  input.required = true;
  label.append(input);
  form.append(label);
  return input;
 }
 async function readPhoto(file) {
  if (!file || file.size > 1024 * 1024) throw Error("Choose an image up to 1 MB.");
  return new Promise((resolve, reject) => {
   const reader = new FileReader();
   reader.onload = () => resolve(reader.result.split(",")[1]);
   reader.onerror = () => reject(Error("The image could not be read."));
   reader.readAsDataURL(file);
  });
 }
 function showPhoto(parent, encoded) {
  const img = make("img");
  img.src = "data:image/jpeg;base64," + encoded;
  img.alt = "Uploaded evidence";
  img.width = 240;
  parent.append(img);
 }
 window.WzosEvidence = {readPhoto, showPhoto};

 const trigger = document.getElementById("open-inspections");
 document.getElementById("inspections-nav").onclick = () => trigger.click();
 trigger.onclick = async () => {
  const dialog = make("dialog");
  dialog.className = "account-dialog";
  const job = make("select"), area = make("div"), message = make("p");
  const close = make("button", "Close");
  message.setAttribute("role", "status");
  const label = make("label","Work order");
  label.append(job);
  dialog.append(make("h2","Day and night inspections"), label, message, area, close);
  document.body.append(dialog);
  const dismiss = () => dialog.close();
  document.addEventListener("wzos:session", dismiss);
  dialog.onclose = () => {document.removeEventListener("wzos:session",dismiss);dialog.remove();};
  close.onclick = dismiss;
  dialog.showModal();
  const api = window.wzosClock.api;
  async function refresh() {
   const id = job.value;
   const path = "/api/orders/" + encodeURIComponent(id) + "/inspections";
   area.replaceChildren();
   if (!id) {message.textContent = "No work orders available.";return;}
   message.textContent = "Loading inspections…";
   const data = await api(path);
   if (!dialog.open || job.value !== id) return;
   message.textContent = "";
   function submit(form, title, route, payload) {
    const button = make("button",title);
    form.append(button);
    form.onsubmit = async event => {
     event.preventDefault();
     button.disabled = true;
     try {
      const body = JSON.stringify(await payload());
      if (!dialog.open || job.value !== id) return;
      await api(route,{method:"PUT",body});
      if (dialog.open && job.value === id) await refresh();
     } catch(error) {message.textContent = error.message;}
     finally {button.disabled = false;}
    };
   }
   const schedule = make("form");
   const due = field(schedule,"Inspection date",null,"date");
   const shift = field(schedule,"Shift",["Day","Night"]);
   const closure = field(schedule,"Closure type",["Lane","Shoulder","Road","Moving","Pedestrian"]);
   const device = field(schedule,"Sign, device or route to inspect");
   const location = field(schedule,"Approach, station or mile marker");
   submit(schedule,"Schedule check",path + "/" + crypto.randomUUID(),() => ({
    due_on:due.value, shift:shift.value, closure_type:closure.value, checkpoint:device.value, location:location.value
   }));
   area.append(schedule);
   const print = make("button","Save inspection report to Work Zone Report");
   if (window.wzosClock.getSession()?.can_prepare_atlas && data.items.length &&
       job.selectedOptions[0]?.dataset.access === 'work_order') {
    const reportControls = make("div");
    const reportDay = field(reportControls,"Report date",null,"date");
    const today = new Date();
    reportDay.value = new Date(today.getTime()-today.getTimezoneOffset()*60000).toISOString().slice(0,10);
    let requestId = crypto.randomUUID();
    reportDay.onchange = () => {requestId=crypto.randomUUID();print.disabled=false;};
    print.onclick = async () => {
     if(!reportDay.reportValidity()) return;
     print.disabled = true;reportDay.disabled=true;
     try {
      const report = await api("/api/orders/"+encodeURIComponent(id)+"/report");
      await api("/api/orders/"+encodeURIComponent(id)+"/reports",{method:"POST",body:JSON.stringify({
       request_id:requestId,expected_order_version:report.order.version,inspection_date:reportDay.value
      })});
      message.textContent = "Saved in Work Zone Report.";
     } catch(error){message.textContent=error.message;print.disabled=false;} finally {reportDay.disabled=false;}
    };
    reportControls.append(print);area.append(reportControls);
   }
   for (const item of data.items) {
    const panel = make("section");
    panel.className = "panel";
    panel.append(make("h3",item.checkpoint+" · "+item.status),
     make("p",[item.due_on,item.shift,item.closure_type+" closure",item.location].join(" · ")));
    const url = path+"/"+item.id;
    if(item.finding) panel.append(make("p",item.finding+(item.repair_owner?" · Repair owner: "+item.repair_owner:"")));
    if(item.status === "Scheduled") {
     const form = make("form");
     const result = field(form,"Result",["Passed","Repair needed"]);
     const finding = field(form,"Observation");
     const owner = field(form,"Repair owner");
     owner.parentElement.hidden = true;
     owner.required = false;
     result.onchange = () => {owner.required = result.value === "Repair needed";owner.parentElement.hidden = !owner.required;};
     submit(form,"Record inspection",url+"/finding",() => ({status:result.value,finding:finding.value,repair_owner:owner.required?owner.value:""}));
     panel.append(form);
    } else if(item.status === "Repair needed") {
     const form = make("form");
     const note = field(form,"What did you verify after repair?");
     const photo = field(form,"Recheck photo (up to 1 MB)",null,"file");
     photo.accept = "image/jpeg,image/png,image/webp";
     submit(form,"Confirm repair and recheck",url+"/recheck",async () => ({note:note.value,photo:await readPhoto(photo.files[0])}));
     panel.append(form);
    } else if(item.status === "Rechecked") {
     panel.append(make("p",item.recheck_note));
     const see = make("button","View recheck photo");
     see.onclick = async () => {
      try {showPhoto(panel,(await api(url+"/photo")).photo);see.remove();}
      catch(error){message.textContent=error.message;}
     };
     panel.append(see);
    }
    area.append(panel);
   }
  }
  job.onchange = () => refresh().catch(error => {message.textContent = error.message;});
  try {
   let offset = 0;
   for (;;) {
    const page = await api("/api/time/jobs?offset="+offset);
    if (!dialog.open) return;
    for (const item of page.items) {
     const option = new Option(item.title,item.id);
     option.dataset.access = item.access_basis;
     job.add(option);
    }
    offset += page.items.length;
    if (!page.items.length || offset >= page.total) break;
   }
   const selected = window.wzosClock.getSelected()?.id;
   if ([...job.options].some(option => option.value === selected)) job.value = selected;
   await refresh();
  } catch(error){message.textContent = error.message;}
 };
})();
