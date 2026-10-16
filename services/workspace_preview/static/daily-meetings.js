"use strict";
(() => {
 const $=id=>document.getElementById(id), api=(...args)=>window.wzosClock.api(...args);
 let epoch=0, frame=null, loading=null, active=false, cleanup=Promise.resolve();
 const status=message=>{$('meetings-notice').textContent=message;};
 function sdk(){
  if(window.DailyIframe)return Promise.resolve(window.DailyIframe);
  if(!loading)loading=new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/daily-sdk.js';script.onload=()=>window.DailyIframe?resolve(window.DailyIframe):reject(new Error('Meeting controls could not load.'));script.onerror=()=>{script.remove();reject(new Error('Meeting controls could not load. Retry when online.'));};document.head.append(script);}).catch(error=>{loading=null;throw error;});
  return loading;
 }
 function stop(){
  epoch++;active=false;const old=frame;frame=null;
  if(old){try{cleanup=Promise.resolve(old.destroy()).catch(()=>{});}catch{}}
  $('meeting-video').replaceChildren();$('meeting-video').hidden=true;$('meeting-standby').hidden=false;
  $('meeting-leave').hidden=$('meeting-fullscreen').hidden=true;$('meeting-embedded-join').disabled=false;
 }
 async function start(row){
  if(active)return;
  stop();active=true;const generation=epoch;
  const same=()=>generation===epoch, button=$('meeting-embedded-join');button.disabled=true;
  status('Preparing your private meeting…');
  try{
   await cleanup;if(!same())return;
   const config=await api('/api/meetings/config');if(!same())return;
   if(!config.daily_enabled)throw new Error('Embedded meetings are awaiting secure Daily configuration.');
   if(window.wzosClock.getSession()?.role==='admin'){await api(`/api/meetings/${row.id}/prepare`,{method:'POST'});if(!same())return;}
   const access=await api(`/api/meetings/${row.id}/join`,{method:'POST'});if(!same())return;
   const url=new URL(access.url);if(url.origin!==config.daily_origin||!/^\/wzos-[a-f0-9]{40}$/.test(url.pathname)||url.search||url.hash)throw new Error('Meeting address could not be verified.');
   const daily=await sdk();if(!same())return;
   $('meeting-video').hidden=false;$('meeting-standby').hidden=true;$('meeting-leave').hidden=false;$('meeting-fullscreen').hidden=false;
   const call=daily.createFrame($('meeting-video'),{showLeaveButton:true,showFullscreenButton:true,iframeStyle:{width:'100%',height:'100%',border:'0'}});frame=call;
   call.on('joined-meeting',()=>{if(same()){$('meetings-state').textContent='CONNECTED';status('You are connected. Use the meeting controls to enable your camera or microphone.');}});
   call.on('left-meeting',()=>{if(same()){stop();$('meetings-state').textContent='SCHEDULED';status('You left the meeting.');}});
   call.on('error',()=>{if(same()){stop();$('meetings-state').textContent='UNAVAILABLE';status('Meeting connection failed. Check your connection and retry.');}});
   status('Opening meeting controls. Camera and microphone start off.');
   // Authorization stays in memory and is passed to the SDK, never to a URL or storage.
   await call.join({url:access.url,token:access.token});
  }catch(error){if(same()){stop();$('meetings-state').textContent='UNAVAILABLE';status(error.message||'Meeting could not connect.');}}
 }
 $('meeting-leave').onclick=()=>{stop();$('meetings-state').textContent='SCHEDULED';status('You left the meeting.');};
 $('meeting-fullscreen').onclick=()=>{$('meeting-video').requestFullscreen?.().catch(()=>status('Full screen is unavailable on this device.'));};
 document.addEventListener('wzos:view',e=>{if(e.detail!=='meetings')stop();});
 document.addEventListener('wzos:session',stop);
 window.addEventListener('pagehide',stop);window.addEventListener('offline',()=>{stop();status('Meeting disconnected. Rejoin when online.');});
 window.WzosDailyMeetings={start,stop,isActive:()=>active};
})();
