"use strict";
// Reuses the provider workflow from services/v2/workspace-job.js.
(() => {
 let generation=0, loader=null, panorama=null, cleanup=null, authFailed=false;
 const element=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
 function clear(){generation++;if(cleanup)cleanup();cleanup=null;if(panorama)panorama.setVisible(false);panorama=null;}
 async function ready(){
  if(authFailed)throw Error("Maps access was rejected. Refresh after correcting the workspace key restrictions.");
  if(loader)return loader;
  const config=await window.wzosClock.api('/api/maps/config');
  if(!config.enabled)throw Error('Site imagery is not configured for this workspace yet. Saved measurements remain available.');
  loader=new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>reject(Error('Map loading timed out. Check connectivity and try refreshing.')),20000);
   window.wzosReportMapsReady=()=>{clearTimeout(timer);resolve();};
   window.gm_authFailure=()=>{authFailed=true;clearTimeout(timer);document.dispatchEvent(new Event('wzos:maps-auth-failed'));reject(Error('Maps access was rejected. The workspace key or allowed website needs attention.'));};
   const script=document.createElement('script');script.async=true;
   script.nonce=document.querySelector('script[nonce]')?.nonce||'';
   script.src='https://maps.googleapis.com/maps/api/js?'+new URLSearchParams({key:config.browser_key,callback:'wzosReportMapsReady',loading:'async',v:'quarterly'});
   script.onerror=()=>{clearTimeout(timer);reject(Error('Unable to load Google Maps. Refresh to retry.'));};document.head.append(script);
  });return loader;
 }
 function mount(container,order){
  const token=generation, geometry=order.job_geometry||{},limits=geometry.work_limits||[],approaches=geometry.approaches||[];
  const center=limits[0]||approaches.find(a=>a.path?.length)?.path[0];
  container.append(element('p',`Work-order revision ${order.version}. Orange: reported work limits. Blue: reported approaches. These are not sign or flagger placements.`));
  const status=element('p',center?'Imagery loads only when you request it. Saved coordinates will be sent to Google.':'Save work-limit or approach coordinates in Work orders before loading imagery. Address lookup is not connected.');status.setAttribute('role','status');
  const load=element('button','Load site imagery'), street=element('button','Nearby Street View');load.type=street.type='button';load.className=street.className='secondary';load.disabled=!center;street.disabled=true;
  const mapBox=element('div',''), streetBox=element('div','');mapBox.className=streetBox.className='report-map';mapBox.hidden=streetBox.hidden=true;
  container.append(load,street,status,mapBox,streetBox);
  const active=()=>token===generation&&container.isConnected;
  let map=null;
  const authFailure=()=>{if(active()){mapBox.hidden=streetBox.hidden=true;street.disabled=true;status.textContent='Google rejected map access. Check the workspace key and permitted website.';}};
  document.addEventListener('wzos:maps-auth-failed',authFailure,{once:true});cleanup=()=>document.removeEventListener('wzos:maps-auth-failed',authFailure);
  load.onclick=async()=>{
   load.disabled=true;status.textContent='Loading site imagery…';
   try{await ready();if(!active())return;mapBox.hidden=false;
    map=new google.maps.Map(mapBox,{center:{lat:center.latitude,lng:center.longitude},zoom:18,mapTypeId:'hybrid',streetViewControl:false});
    const bounds=new google.maps.LatLngBounds();
    for(const [points,color] of [[limits,'#e97221'],...approaches.map(a=>[a.path,'#496ad8'])]){if(!points.length)continue;const path=points.map(p=>({lat:p.latitude,lng:p.longitude}));path.forEach(p=>bounds.extend(p));new google.maps.Polyline({map,path,strokeColor:color,strokeWeight:4});}
    map.fitBounds(bounds,40);street.disabled=false;
    status.textContent='Google hybrid imagery with reported geometry. Confirm the correct site and current conditions. Imagery is not saved in report snapshots or approved for export.';
   }catch(error){if(active())status.textContent=error.message;}finally{if(active())load.disabled=false;}
  };
  street.onclick=async()=>{
   street.disabled=true;status.textContent='Looking for nearby Street View…';
   try{const result=await new google.maps.StreetViewService().getPanorama({location:{lat:center.latitude,lng:center.longitude},radius:50});if(!active())return;
    streetBox.hidden=false;if(panorama)panorama.setVisible(false);panorama=new google.maps.StreetViewPanorama(streetBox);panorama.setPano(result.data.location.pano);panorama.setVisible(true);
    status.textContent=`Nearby Street View · capture date ${result.data.imageDate||'unavailable'}. Verify it shows this work area. Overhead geometry is not projected onto the panorama.`;
   }catch{if(active()){streetBox.hidden=true;status.textContent='No nearby Street View was returned, or the provider request failed. Use the overhead map and field verification.';}}
   finally{if(active())street.disabled=false;}
  };
 }
 window.WzosReportMap={clear,mount};
})();
