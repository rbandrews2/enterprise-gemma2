"use strict";
let siteMap=null, sitePanorama=null, mapLoader=null, mapFeatures=[];
const jobFields=[
  ["locality","City/county","text"],["road_authority","Road authority (reported)","text"],
  ["latitude","Project latitude","number"],["longitude","Project longitude","number"],
  ["project_date","Work date","date"],["speed_limit_mph","Posted speed (mph)","number"],
  ["lane_count","Lane count","number"],["closure_type","Closure type","select",["unknown","shoulder","lane","full_road","mobile","sidewalk","none"]],
  ["duration_hours","Duration (hours)","number"],["lane_width_ft","Lane width (feet)","number"],
  ["available_sight_distance_ft","Available sight distance (feet)","number"],
  ["travel_direction","Affected travel directions","text"],["geometry_source","Geometry source / measurement reference","text"],
  ["work_period","Work period","select",["unknown","day","night","mixed"]],
  ["pedestrians_present","Pedestrians affected","select",["unknown","yes","no"]],
  ["intersections_present","Intersections affected","select",["unknown","yes","no"]]
];
function mountJob(){
  const host=el("jobEditor");host.replaceChildren();
  if(!draft){host.textContent="Load a project to edit job details.";return;}
  const form=document.createElement("form");host.append(form);
  const values={...draft.intake.location,...draft.intake.site,...draft.job_geometry,project_date:draft.intake.project_date};
  for(const [id,title,type,options] of jobFields){
    const label=document.createElement("label");label.textContent=title;
    const input=document.createElement(type==="select"?"select":"input");input.id="job_"+id;
    if(options)for(const value of options)input.add(new Option(value,value));
    else {input.type=type;if(type==="number")input.step="any";}
    input.value=typeof values[id]==="boolean"?(values[id]?"yes":"no"):(values[id]??(options?options[0]:""));
    label.append(input);form.append(label);
  }
  const label=document.createElement("label");label.textContent="Work-limit line: one latitude,longitude pair per line (at least two distinct points)";
  const limits=document.createElement("textarea");limits.id="job_work_limits";limits.rows=5;
  limits.value=(draft.job_geometry?.work_limits||[]).map(p=>`${p.latitude},${p.longitude}`).join("\n");label.append(limits);form.append(label);
  const note=document.createElement("p");note.textContent="Reported geometry is not surveyed or approved. This line records work limits, not lane boundaries or sign spacing.";form.append(note);
  const save=document.createElement("button");save.textContent="Save job details";form.append(save);
  form.oninput=()=>{form.dataset.dirty="true";};
  form.onsubmit=async event=>{
    event.preventDefault();if(busy)return;
    if(dirty||formDirty||el("atlasResults").querySelector('form[data-dirty="true"]')){status("Save or discard other edits first.");return;}
    const updated=structuredClone(draft), geometry={};
    try{
      for(const [id,,type] of jobFields){
        const raw=el("job_"+id).value.trim();let value=raw||null;
        if(type==="number"&&raw){value=Number(raw);if(!Number.isFinite(value))throw Error("Enter finite numeric values.");}
        if(["pedestrians_present","intersections_present"].includes(id))value=raw==="unknown"?null:raw==="yes";
        if(["locality","road_authority","latitude","longitude"].includes(id))updated.intake.location[id]=value;
        else if(id==="project_date")updated.intake.project_date=value;
        else if(["speed_limit_mph","lane_count","work_period","pedestrians_present","intersections_present"].includes(id))updated.intake.site[id]=value;
        else geometry[id]=value;
      }
      geometry.work_limits=limits.value.trim()?limits.value.trim().split(/\n/).map(row=>{
        const parts=row.split(",");if(parts.length!==2||parts.some(p=>!p.trim()||!Number.isFinite(Number(p))))throw Error("Use latitude,longitude on each work-limit line.");
        return {latitude:Number(parts[0]),longitude:Number(parts[1])};
      }):[];
      updated.job_geometry=geometry;busy=true;save.disabled=true;el("fields").disabled=true;
      record=await api(`/v2/projects/${record.project_id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({...updated,expected_version:record.version})});
      draft=structuredClone(record.draft);form.dataset.dirty="false";render();status(`Job details saved in revision ${record.version}. Previous Atlas responses may need reconfirmation.`);
    }catch(error){status(error.message);}finally{busy=false;save.disabled=false;el("fields").disabled=false;}
  };
}
function refreshMap(){
  if(sitePanorama)sitePanorama.setVisible(false);
  if(!siteMap)return;
  for(const feature of mapFeatures)feature.setMap(null);mapFeatures=[];
  const limits=draft?.job_geometry?.work_limits||[];
  if(limits.length)mapFeatures.push(new google.maps.Polyline({map:siteMap,path:limits.map(p=>({lat:p.latitude,lng:p.longitude})),strokeColor:"#e97221",strokeWeight:4}));
  for(const marker of draft?.annotations||[]){
    const feature=new google.maps.Circle({map:siteMap,center:{lat:marker.latitude,lng:marker.longitude},radius:2,fillColor:"#176b78",fillOpacity:1,strokeColor:"#fff",strokeWeight:1});
    feature.addListener("click",()=>{if(!busy&&!formDirty)edit(marker.id);});mapFeatures.push(feature);
  }
  const location=draft?.intake.location;
  if(location?.latitude!=null)siteMap.setCenter({lat:location.latitude,lng:location.longitude});
  else if(limits.length)siteMap.setCenter({lat:limits[0].latitude,lng:limits[0].longitude});
  else {el("googleMap").hidden=true;el("mapStatus").textContent="This project needs coordinates before displaying Google imagery.";return;}
  el("googleMap").hidden=false;
}
async function googleReady(){
  if(mapLoader)return mapLoader;
  const config=await api("/v2/maps/config");
  if(!config.enabled)throw Error("Google map access is not configured. Set WZOS_GOOGLE_MAPS_BROWSER_KEY to a website-restricted Maps JavaScript key.");
  mapLoader=new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>reject(Error("Google Maps did not load. Check connectivity, key restrictions and billing.")),20000);
    window.wzosMapsReady=()=>{clearTimeout(timeout);resolve();};
    window.gm_authFailure=()=>{clearTimeout(timeout);el("mapStatus").textContent="Google Maps authorization failed. Check the browser key, restrictions and billing.";reject(Error("Google Maps authorization failed."));};
    const script=document.createElement("script");script.async=true;
    const params=new URLSearchParams({key:config.browser_key,callback:"wzosMapsReady",loading:"async",v:"quarterly"});
    script.src="https://maps.googleapis.com/maps/api/js?"+params;
    script.onerror=()=>{clearTimeout(timeout);reject(Error("Unable to load Google Maps."));};document.head.append(script);
  });return mapLoader;
}
el("loadMap").onclick=async()=>{
  if(busy)return;
  if(!draft||draft.intake.location.latitude==null){el("mapStatus").textContent="Load a project and save its coordinates first. Address geocoding is not connected.";return;}
  busy=true;el("loadMap").disabled=true;
  try{await googleReady();el("googleMap").hidden=false;
    if(!siteMap)siteMap=new google.maps.Map(el("googleMap"),{center:{lat:draft.intake.location.latitude,lng:draft.intake.location.longitude},zoom:18,mapTypeId:"hybrid",streetViewControl:false});
    refreshMap();el("mapStatus").textContent="Google hybrid imagery with reported work limits and proposed marker points. Imagery may predate current site conditions.";
  }catch(error){el("mapStatus").textContent=error.message;}finally{busy=false;el("loadMap").disabled=false;}
};
el("streetView").onclick=async()=>{
  if(busy)return;
  if(!siteMap||!draft||draft.intake.location.latitude==null){el("mapStatus").textContent="Load the Google map for a project with coordinates first.";return;}
  busy=true;el("streetView").disabled=true;
  try{
    const result=await new google.maps.StreetViewService().getPanorama({location:{lat:draft.intake.location.latitude,lng:draft.intake.location.longitude},radius:50});
    el("googleStreet").hidden=false;
    if(!sitePanorama)sitePanorama=new google.maps.StreetViewPanorama(el("googleStreet"));
    sitePanorama.setPano(result.data.location.pano);sitePanorama.setVisible(true);
    el("mapStatus").textContent="Nearby Street View loaded. Confirm it shows the correct site; capture date: "+(result.data.imageDate||"not provided")+". Overhead markers are not projected onto Street View.";
  }catch{if(sitePanorama)sitePanorama.setVisible(false);el("mapStatus").textContent="Street View is unavailable here or the provider request failed.";}finally{busy=false;el("streetView").disabled=false;}
};
window.addEventListener("wzos-project",()=>{mountJob();refreshMap();});mountJob();
