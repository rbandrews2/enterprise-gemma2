"use strict";
(() => {
 const byId = id => document.getElementById(id);
 const button = byId("equipment-nav"), dialog = byId("equipment-dialog");
 const form = byId("equipment-form"), mode = form.elements.location_method;
 const type = form.elements.equipment_type;
 const notice = byId("equipment-status"), mapStatus = byId("equipment-map-status");
 const box = byId("equipment-map"), list = byId("equipment-list");
 const api = (...args) => window.wzosClock.api(...args);
 const endpoint = "/api/equipment-locator";
 const icons = {"Pickup truck":"🛻", TMA:"🛡️", "Message board":"▤", "Arrow board":"➜", Custom:"◆"};
 const photoFiles = {TMA:"tma", "Arrow board":"arrow-board", "Message board":"message-board"};
 const photos = new Map();
 function photoFor(type) {
  if (!photoFiles[type]) return;
  if (!photos.has(type)) {
   const image = new Image();
   image.onload = draw;
   image.src = "/equipment-icons/" + photoFiles[type] + ".png";
   photos.set(type,image);
  }
  return photos.get(type);
 }
 let generation = 0, revision = 0, map, popup, markers = [], items = [], lastRequest;
 const element = (tag,text) => {const node=document.createElement(tag);node.textContent=text;return node;};
 const name = item => item.custom_name || item.equipment_type;
 function fields() {
  for (const [id,visible] of [["equipment-address",mode.value==="address"],
     ["equipment-coordinates",mode.value==="coordinates"],["equipment-custom",type.value==="Custom"]]) {
   const section = byId(id);
   section.hidden = !visible;
   for (const input of section.querySelectorAll("input")) {input.disabled=!visible;input.required=visible;}
  }
 }
 type.onchange = mode.onchange = fields;
 function clearMarkers() {
  popup?.close();
  for (const marker of markers) marker.setMap(null);
  markers = [];
 }
 function draw() {
  clearMarkers();
  if (!map || !items.length) return;
  const groups = new Map(), bounds = new google.maps.LatLngBounds();
  for (const item of items) {
   const key = [item.latitude,item.longitude].join(",");
   if (!groups.has(key)) groups.set(key,[]);
   groups.get(key).push(item);
  }
  for (const group of groups.values()) {
   const first = group[0], position={lat:first.latitude,lng:first.longitude};
   bounds.extend(position);
   const title = group.map(item=>name(item)+" × "+item.quantity).join(", ");
   const types = [...new Set(group.map(item=>item.equipment_type))];
   const cellWidth = 60, height = 40, width = cellWidth * types.length;
   const canvas = document.createElement("canvas");
   canvas.width = width * 2;
   canvas.height = height * 2;
   const ctx = canvas.getContext("2d");
   ctx.scale(2,2);
   ctx.fillStyle="#282318";ctx.fillRect(0,0,width,height);
   ctx.strokeStyle="#ffc150";ctx.lineWidth=2;ctx.strokeRect(1,1,width-2,height-2);
   ctx.fillStyle="#ffe0a0";ctx.font="bold 24px sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";
   types.forEach((type,index)=>{
    const x = index * cellWidth, photo = photoFor(type);
    if (photo?.complete && photo.naturalWidth) ctx.drawImage(photo,x+2,2,56,36);
    else ctx.fillText(icons[type],x+cellWidth/2,height/2);
   });
   const marker = new google.maps.Marker({map,position,title,icon:{
    url:canvas.toDataURL(),scaledSize:new google.maps.Size(width,height)}});
   marker.addListener("click",()=>{
    const content=element("div","");
    group.forEach(item=>content.append(element("p",name(item)+" × "+item.quantity)));
    popup.setContent(content);popup.open({map,anchor:marker});
   });
   markers.push(marker);
  }
  if(groups.size===1){map.setCenter(bounds.getCenter());map.setZoom(16);}
  else map.fitBounds(bounds,45);
 }
 function render() {
  list.replaceChildren();
  if(!items.length) list.append(element("p","No equipment outstanding."));
  for(const item of items){
   const row=element("article",""), title=element("strong",icons[item.equipment_type]+" "+name(item)+" × "+item.quantity);
   const photo = photoFor(item.equipment_type);
   if (photo) {
    const icon = photo.cloneNode();
    icon.alt="";icon.width=56;icon.height=36;
    title.textContent=" "+name(item)+" × "+item.quantity;
    title.prepend(icon);
   }
   const location=item.address?[item.address.street,item.address.city,item.address.region].join(", "):[item.latitude,item.longitude].join(", ");
   const retrieve=element("button","Mark retrieved");retrieve.type="button";retrieve.className="secondary";
   retrieve.onclick=async()=>{
    if(!window.confirm("Mark all "+item.quantity+" × "+name(item)+" at "+location+" as retrieved?"))return;
    const token=generation;retrieve.disabled=true;
    try{
     await api(endpoint+"/"+item.id+"/retrieved",{method:"PUT"});
     if(token!==generation)return;
     items=items.filter(other=>other.id!==item.id);revision++;render();
     notice.textContent="Equipment marked retrieved.";
    }catch(error){if(token===generation){notice.textContent=error.message;retrieve.disabled=false;}}
   };
   row.append(title,element("p",location),retrieve);list.append(row);
  }
  draw();
 }
 async function refresh(token){
  const version=++revision;
  try{
   const result=await api(endpoint);
   if(token===generation && version===revision){items=result.items;render();}
  }catch(error){if(token===generation)notice.textContent=error.message;}
 }
 function reset() {
  generation++;revision++;clearMarkers();map=null;popup=null;items=[];lastRequest=null;
  list.replaceChildren();box.replaceChildren();box.hidden=true;
  notice.textContent="";mapStatus.textContent="";form.reset();fields();form.elements.submit_entry.disabled=false;
 }
 function session(){
  if(dialog.open)dialog.close();
  reset();button.hidden=window.wzosClock?.getSession()?.edition!=="enterprise";
 }
 document.addEventListener("wzos:session",session);
 byId("equipment-close").onclick=()=>dialog.close();
 dialog.addEventListener("close",reset);
 byId("equipment-refresh").onclick=()=>refresh(generation);
 document.addEventListener("wzos:maps-auth-failed",()=>{
  if(dialog.open){map=null;box.hidden=true;mapStatus.textContent="Map access was rejected by Google.";}
 });
 button.onclick=async()=>{
  if(window.wzosClock.getSession()?.edition!=="enterprise")return;
  reset();const token=generation;
  dialog.showModal();list.textContent="Loading equipment…";refresh(token);
  mapStatus.textContent="Loading map…";
  try{
   await window.WzosReportMap.ready();if(token!==generation)return;
   box.hidden=false;
   map=new google.maps.Map(box,{center:{lat:39,lng:-97},zoom:4,streetViewControl:false});
   popup=new google.maps.InfoWindow();draw();mapStatus.textContent="";
  }catch{if(token===generation)mapStatus.textContent="Map unavailable. Check the workspace Google Maps configuration or connection. Coordinate entry and the equipment list are available.";}
 };
 form.onsubmit=async event=>{
  event.preventDefault();
  if(form.elements.submit_entry.disabled||!form.reportValidity())return;
  const token=generation, data=Object.fromEntries(new FormData(form));
  const signature=JSON.stringify(data);
  form.elements.submit_entry.disabled=true;
  try{
   if(lastRequest?.signature!==signature){
    let latitude,longitude,address=null;
    if(data.location_method==="address"){
     address={street:data.street.trim(),city:data.city.trim(),region:data.region.trim()};
     if(Object.values(address).some(part=>!part))throw Error("Enter a street address, city and state or region.");
     notice.textContent="Locating the address…";
     await window.WzosReportMap.ready();if(token!==generation)return;
     const response=await new google.maps.Geocoder().geocode({address:Object.values(address).join(", ")});
     const matches=response.results.filter(result=>!result.partial_match && result.types.some(t=>["street_address","premise","subpremise"].includes(t)));
     if(matches.length!==1)throw Error("A unique street address could not be confirmed. Check the address or enter coordinates.");
     latitude=matches[0].geometry.location.lat();longitude=matches[0].geometry.location.lng();
    }else{latitude=Number(data.latitude);longitude=Number(data.longitude);}
    if(token!==generation)return;
    lastRequest={signature,id:crypto.randomUUID(),body:{latitude,longitude,address,location_method:data.location_method,
     equipment_type:data.equipment_type,custom_name:data.equipment_type==="Custom"?data.custom_name.trim():null,quantity:Number(data.quantity)}};
   }
   if(token!==generation)return;
   const {id,body}=lastRequest;
   await api(endpoint+"/"+id,{method:"PUT",body:JSON.stringify(body)});
   if(token!==generation)return;
   items=[...items.filter(item=>item.id!==id),{id,...body}];revision++;render();
   form.reset();fields();lastRequest=null;notice.textContent="Equipment placed.";
   await refresh(token);
  }catch(error){if(token===generation)notice.textContent=error.message||"Address lookup failed. Check the address or use coordinates.";}
  finally{if(token===generation)form.elements.submit_entry.disabled=false;}
 };
 fields();
})();
