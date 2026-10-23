'use strict';
// Public launch UI only. Never persist identities, permissions or private records.
window.wzosStartup=(()=>{
 let finished=false,retry=null,retrying=false;
 const panel=()=>document.getElementById('app-boot');
 const message=text=>{const n=document.getElementById('app-boot-message');if(n)n.textContent=text;};
 function signingIn(){panel().hidden=true;}
 function ready(){finished=true;clearTimeout(slow);panel().hidden=true;document.body.classList.remove('app-starting');}
 function fail(){if(finished)return;panel().hidden=false;message(navigator.onLine===false?'You’re offline. Reconnect to open your workspace.':'We couldn’t open your workspace. Please try again.');document.getElementById('app-boot-retry').hidden=false;}
 const slow=setTimeout(()=>{if(!finished&&!panel().hidden){message('Still connecting… You can try again if this takes too long.');document.getElementById('app-boot-retry').hidden=false;}},8000);
 document.getElementById('app-boot-retry').onclick=async()=>{
  if(retrying)return;
  if(!retry){location.reload();return;}
  retrying=true;document.getElementById('app-boot-retry').disabled=true;
  message('Connecting to your workspace…');
  try{await retry();}catch{fail();}finally{retrying=false;document.getElementById('app-boot-retry').disabled=false;}
 };
 // Include response-body reads and authentication waits in the deadline. A
 // provider that ignores abort must not keep the launch UI waiting forever.
 function request(task,timeout=20000){
  const controller=new AbortController();let timer;
  return Promise.race([Promise.resolve().then(()=>task(controller.signal)),new Promise((_,reject)=>{
   timer=setTimeout(()=>{controller.abort();reject(Error('Connection took too long. Try again without closing WZOS.'));},timeout);
  })]).finally(()=>{clearTimeout(timer);controller.abort();});
 }
 window.addEventListener('error',fail);window.addEventListener('unhandledrejection',fail);
 // Install/update the public shell in the background, never blocking sign-in.
 if('serviceWorker' in navigator&&window.isSecureContext&&window.top===window){
  window.addEventListener('load',()=>{
   const version=document.querySelector('meta[name="wzos-release"]')?.content;
   if(/^[a-f0-9]{24}$/.test(version||''))navigator.serviceWorker.register('/app-shell-worker.js?v='+version,{scope:'/'}).catch(()=>{});
  },{once:true});
 }
 return {signingIn,ready,fail,request,setRetry:callback=>{retry=callback;}};
})();
