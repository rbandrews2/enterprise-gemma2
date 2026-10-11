"use strict";
(() => {
 let epoch=0, current=null, request=null;
 const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text||'';return n;};
 const scope=()=>{const s=window.wzosClock.getSession();return JSON.stringify([s?.organization_id,s?.id,s?.edition]);};
 function clear(){epoch++;if(request)request.abort();request=null;if(current)current.remove();current=null;}
 document.addEventListener('wzos:session',clear);
 document.addEventListener('wzos:view',clear);
 window.addEventListener('offline',clear);
 function attach(card,job){
  const open=node('button','Route inside WZOS');open.type='button';open.className='secondary';card.append(open);
  open.onclick=async()=>{
   clear();const token=epoch, identity=scope(), panel=node('section');current=panel;
   panel.className='panel navigation-route';panel.setAttribute('aria-label','In-app route to '+job.title);
   const active=()=>epoch===token&&scope()===identity&&panel.isConnected;
   const title=node('h3','Navigate to '+job.title),notice=node('p','Calculate sends your starting location and the saved job destination to Google. Location is read only when you request it; no background tracking.'),label=node('label','Starting address'),origin=node('input');
   origin.type='text';origin.maxLength=250;origin.placeholder='Enter starting address';origin.setAttribute('aria-label','Starting address');label.append(origin);
   const locate=node('button','Use my current location'),calculate=node('button','Calculate route'),close=node('button','Close route');
   locate.type=close.type='button';calculate.type='submit';locate.className=close.className='secondary';calculate.className='primary';
   const form=node('form'),status=node('p','Checking routing availability…'),result=node('div');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
   form.append(label,locate,calculate);panel.append(title,notice,form,close,status,result);card.append(panel);
   close.onclick=clear;let coordinates=null, configured=false, locating=false;
   origin.oninput=()=>{coordinates=null;};calculate.disabled=true;
   locate.onclick=()=>{
    if(locating||!navigator.geolocation)return;
    locating=true;locate.disabled=true;calculate.disabled=true;origin.disabled=true;status.textContent='Requesting location permission…';
    navigator.geolocation.getCurrentPosition(position=>{
     if(!active())return;coordinates={latitude:position.coords.latitude,longitude:position.coords.longitude};
     origin.value='Current location';status.textContent=`Reported location accuracy: approximately ${Math.round(position.coords.accuracy)} metres. Confirm the starting point before calculating.`;
     locating=false;locate.disabled=false;origin.disabled=false;calculate.disabled=!configured;
    },()=>{if(active()){coordinates=null;locating=false;origin.value='';origin.disabled=false;locate.disabled=false;calculate.disabled=!configured;status.textContent='Location was unavailable or permission was declined. Enter a starting address.';}},
    {enableHighAccuracy:false,timeout:10000,maximumAge:0});
   };
   locate.disabled=!navigator.geolocation;
   try{const config=await window.wzosClock.api('/api/navigation/config');if(!active())return;
    configured=config.routes_enabled&&navigator.onLine;calculate.disabled=!configured||locating;
    status.textContent=configured?'Ready. Confirm the job address and starting point.':'In-app routing is not configured or you are offline. Open in Navigation and saved destination sheets remain available.';
   }catch(error){if(active())status.textContent=error.message;}
   form.onsubmit=async event=>{
    event.preventDefault();if(!configured||locating||request)return;
    const start=coordinates||{address:origin.value.trim()};if(!coordinates&&!start.address){status.textContent='Enter a starting address or request your location.';return;}
    const controller=new AbortController();request=controller;calculate.disabled=true;locate.disabled=true;origin.disabled=true;result.replaceChildren();status.textContent='Calculating route…';
    try{
     const target=job.assignment_id?{assignment_id:job.assignment_id}:{order_id:job.id};
     const route=await window.wzosClock.api('/api/navigation/route',{method:'POST',signal:controller.signal,body:JSON.stringify({...target,origin:start})});if(!active())return;
     if(route.status!=='ready'){status.textContent=route.message||'No route returned.';return;}
     const summary=node('p',`${(route.distance_meters/1609.344).toFixed(1)} miles · about ${Math.ceil(route.duration_seconds/60)} minutes · calculated ${new Date(route.calculated_at).toLocaleTimeString()}`);
     const destination=node('p',route.destination+' · '+(route.destination_basis==='dispatched_snapshot'?'Dispatched destination':'Saved work-order destination'));
     const mapBox=node('div');mapBox.className='report-map navigation-map';mapBox.hidden=true;
     const list=node('ol');for(const step of route.directions)list.append(node('li',step.instruction||'Continue along the route'));
     result.append(summary,destination,mapBox,node('h4','Directions'),list,node('p','Google Maps · route estimate, not a guarantee of site access. This view does not provide background or voice guidance.'));
     if(route.directions_truncated)result.append(node('p','Directions were shortened; open Google Maps for the full route.'));
     status.textContent=route.traffic_fallback?'Google returned a fallback estimate; live traffic may be unavailable.':'Route ready. Review before travelling. Recalculate manually if conditions change.';
     try{
      await window.WzosReportMap.ready();if(!active())return;
      const geometry=await google.maps.importLibrary('geometry');if(!active())return;
      const path=geometry.encoding.decodePath(route.encoded_polyline);
      if(!path.length||path.length>10000||path.some(p=>!Number.isFinite(p.lat())||!Number.isFinite(p.lng())||Math.abs(p.lat())>90||Math.abs(p.lng())>180))throw Error('Invalid route line');
      mapBox.hidden=false;const map=new google.maps.Map(mapBox,{center:path[0],zoom:12,mapTypeId:'roadmap',streetViewControl:false});
      new google.maps.Polyline({map,path,strokeColor:'#efb956',strokeWeight:6});const bounds=new google.maps.LatLngBounds();path.forEach(p=>bounds.extend(p));map.fitBounds(bounds,40);
     }catch{if(active()){mapBox.hidden=true;status.textContent+=' Map display unavailable; directions remain below.';}}
    }catch(error){if(active())status.textContent=error.name==='AbortError'?'Route request cancelled.':error.message;}
    finally{if(request===controller)request=null;if(active()){calculate.disabled=!configured;locate.disabled=!navigator.geolocation;origin.disabled=false;}}
   };
  };
 }
 window.WzosNavigationRoute={attach,clear};
})();
