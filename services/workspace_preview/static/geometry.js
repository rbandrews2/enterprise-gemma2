"use strict";
// Coordinate parsing and approach controls adapted from services/v2/workspace-job.js.
window.WzosGeometry=(()=>{
function parseRoadPoints(text){
  return text.trim()?text.trim().split(/\n/).map(row=>{
    const parts=row.split(",");
    if(parts.length!==2||parts.some(p=>!p.trim()||!Number.isFinite(Number(p))))throw Error("Use latitude,longitude on each coordinate line.");
    return {latitude:Number(parts[0]),longitude:Number(parts[1])};
  }):[];
}
function mountApproaches(form, geometry){
  const title=document.createElement("h3");title.textContent="Measured approaches (reported)";form.append(title);
  const note=document.createElement("p");note.textContent="Enter points in traffic-travel order, from upstream toward the work area. Record measurements and obstacles for each approach. These inputs remain unverified and do not define lane boundaries or approved placements.";form.append(note);
  const list=document.createElement("div");form.append(list);
  const add=document.createElement("button");add.type="button";add.textContent="Add approach";form.append(add);
  function append(value={}){
    const group=document.createElement("fieldset");group.className="approach-input";
    const legend=document.createElement("legend");legend.textContent="Reported approach";group.append(legend);
    for(const [key,labelText,type] of [["id","Approach ID","text"],["travel_direction","Approach travel direction","text"],["measurement_source","Measurement source","text"],["measured_on","Measurement date","date"],["lane_width_ft","Approach lane width (feet)","number"],["available_sight_distance_ft","Approach sight distance (feet)","number"],["obstruction_notes","Obstructions and access notes (state none if checked)","textarea"],["path","Approach path: latitude,longitude per line; upstream toward work","textarea"]]){
      const label=document.createElement("label");label.textContent=labelText;
      const input=document.createElement(type==="textarea"?"textarea":"input");input.dataset.field=key;input.required=true;
      if(type!=="textarea")input.type=type;
      if(type==="number")input.step="any";
      input.value=key==="path"?(value.path||[]).map(p=>`${p.latitude},${p.longitude}`).join("\n"):(value[key]??"");
      label.append(input);group.append(label);
    }
    const remove=document.createElement("button");remove.type="button";remove.textContent="Remove approach";
    remove.onclick=()=>{group.remove();form.dispatchEvent(new Event("input",{bubbles:true}));add.disabled=false;};group.append(remove);list.append(group);
    add.disabled=list.children.length>=8;
  }
  for(const approach of geometry?.approaches||[])append(approach);
  add.onclick=()=>{if(list.children.length>=8)return;append();form.dispatchEvent(new Event("input",{bubbles:true}));};
  return ()=>[...list.children].map(group=>{
    const value={};for(const input of group.querySelectorAll("[data-field]")){
      const key=input.dataset.field,raw=input.value.trim();
      value[key]=key==="path"?parseRoadPoints(raw):(input.type==="number"?Number(raw):raw);
    }return value;
  });
}

function mount(host,geometry){
 host.replaceChildren();
 const fields=[['closure_type','Closure type',['unknown','shoulder','lane','full_road','mobile','sidewalk','none']],['placement_scenario','Reference scenario',['','stationary_shoulder']],['road_class','Road classification',['','conventional','undivided','divided_non_limited','limited_access']],['duration_hours','Duration (hours)','number'],['lane_width_ft','Lane width (feet)','number'],['available_sight_distance_ft','Available sight distance (feet)','number'],['travel_direction','Affected travel directions','text'],['geometry_source','Geometry measurement source','text'],['work_limits','Work limits: latitude,longitude per line','textarea']];
 const controls={};
 for(const [key,title,type] of fields){const label=document.createElement('label');label.textContent=title;const input=document.createElement(Array.isArray(type)?'select':type==='textarea'?'textarea':'input');input.id='geometry-'+key;
 if(Array.isArray(type)){for(const value of type)input.add(new Option(value||'Not selected',value));}else if(type!=='textarea'){input.type=type;if(type==='number')input.step='any';}
 input.value=key==='work_limits'?(geometry?.work_limits||[]).map(p=>`${p.latitude},${p.longitude}`).join('\n'):(geometry?.[key]??(Array.isArray(type)?type[0]:''));label.append(input);host.append(label);controls[key]=input;}
 const readApproaches=mountApproaches(host,geometry);
 return ()=>{const result={};for(const [key,,type] of fields){const raw=controls[key].value.trim();result[key]=key==='work_limits'?parseRoadPoints(raw):type==='number'?(raw?Number(raw):null):(raw||null);}result.approaches=readApproaches();return result;};
}
return {mount};
})();
