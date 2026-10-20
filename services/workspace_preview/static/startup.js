'use strict';
// Public launch UI only. Never persist identities, permissions or private records.
window.wzosStartup=(()=>{
 let finished=false;
 const panel=()=>document.getElementById('app-boot');
 const message=text=>{const n=document.getElementById('app-boot-message');if(n)n.textContent=text;};
 function signingIn(){panel().hidden=true;}
 function ready(){finished=true;clearTimeout(slow);panel().hidden=true;document.body.classList.remove('app-starting');}
 function fail(){if(finished)return;panel().hidden=false;message(navigator.onLine===false?'You’re offline. Reconnect to open your workspace.':'We couldn’t open your workspace. Please try again.');document.getElementById('app-boot-retry').hidden=false;}
 const slow=setTimeout(()=>{if(!finished&&!panel().hidden){message('Still connecting… You can try again if this takes too long.');document.getElementById('app-boot-retry').hidden=false;}},8000);
 document.getElementById('app-boot-retry').onclick=()=>location.reload();
 window.addEventListener('error',fail);window.addEventListener('unhandledrejection',fail);
 // Install/update the public shell in the background, never blocking sign-in.
 if('serviceWorker' in navigator&&window.isSecureContext&&window.top===window){
  window.addEventListener('load',()=>{
   const version=document.querySelector('meta[name="wzos-release"]')?.content;
   if(/^[a-f0-9]{24}$/.test(version||''))navigator.serviceWorker.register('/app-shell-worker.js?v='+version,{scope:'/'}).catch(()=>{});
  },{once:true});
 }
 return {signingIn,ready,fail};
})();
