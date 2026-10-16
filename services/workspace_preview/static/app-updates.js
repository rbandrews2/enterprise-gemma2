"use strict";
(()=>{
 const current=document.querySelector('meta[name="wzos-release"]')?.content;
 if(!/^[a-f0-9]{24}$/.test(current||''))return;
 let checking=false,last=0,dismissed='',displayed='',banner=null,message=null;
 function show(version){
  if(dismissed===version)return;
  displayed=version;
  if(!banner){
   banner=document.createElement('section');banner.className='app-update';banner.setAttribute('role','status');
   message=document.createElement('p');message.textContent='Install updates for an improved experience.';
   const install=document.createElement('button');install.type='button';install.textContent='Install updates';
   const later=document.createElement('button');later.type='button';later.textContent='Later';
   install.onclick=()=>{
    if(navigator.onLine===false){message.textContent='Reconnect to install this update.';return;}
    if(window.WzosDailyMeetings?.isActive?.()){message.textContent='Leave your meeting before installing updates.';return;}
    // Reuse the existing module guards, including unsaved forms and pending punches.
    // This synthetic event does not invoke a browser confirmation dialog.
    const guard=new Event('beforeunload',{cancelable:true});window.dispatchEvent(guard);
    if(guard.defaultPrevented){message.textContent='Save your changes or finish the current action, then install updates.';return;}
    window.location.reload();
   };
   later.onclick=()=>{dismissed=displayed;banner.hidden=true;};
   banner.append(message,install,later);document.body.append(banner);
  }
  banner.hidden=false;
 }
 async function check(){
  if(checking||document.visibilityState==='hidden'||navigator.onLine===false||Date.now()-last<30000)return;
  checking=true;last=Date.now();const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),10000);
  try{
   const response=await fetch('/api/app/version',{credentials:'same-origin',cache:'no-store',signal:controller.signal});
   if(!response.ok)return;
   const data=await response.json();
   if(!/^[a-f0-9]{24}$/.test(data.version||''))return;
   if(data.version!==current)show(data.version);
   else if(banner)banner.hidden=true;
  }catch{/* Offline or failed checks never force a reload or discard device data. */}
  finally{clearTimeout(timeout);checking=false;}
 }
 setInterval(check,300000);window.addEventListener('focus',check);window.addEventListener('online',check);
 document.addEventListener('visibilitychange',check);check();
})();
