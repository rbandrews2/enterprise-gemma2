'use strict';
// Only explicitly marked PUBLIC HTML/assets. APIs, files, media, tokens and
// transcripts never enter this cache. This does not provide offline account data.
const SHELL_CACHE='wzos-public-shell-v1';
const STATIC_CACHE='wzos-public-assets-__RELEASE__';
async function refreshShell(){
 const response=await fetch('/',{credentials:'omit',cache:'no-store',redirect:'error'});
 if(response.ok&&response.headers.get('X-WZOS-Public-Shell')==='1'){
  await (await caches.open(SHELL_CACHE)).put('/',response.clone());
 }
 return response;
}
self.addEventListener('install',event=>event.waitUntil((async()=>{try{await refreshShell();}catch{}await self.skipWaiting();})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 const keys=await caches.keys();
 for(const key of keys)if(key.startsWith('wzos-public-assets-')&&key!==STATIC_CACHE)await caches.delete(key);
 await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=='GET'||url.origin!==self.location.origin)return;
 if(request.mode==='navigate'&&url.pathname==='/'&&!url.search){
  event.respondWith((async()=>{
   // Prefer fresh HTML for updates/reloads too, but never strand a returning
   // user behind the OS splash when the network stalls. The cached shell is
   // public only; authenticated records are still checked with the server.
   const fresh=refreshShell();
   event.waitUntil(fresh.catch(()=>{}));
   const cached=await (await caches.open(SHELL_CACHE)).match('/');
   if(!cached)return fresh;
   // Prefer the current release, including rollback. A slow/offline connection
   // can still display the generic cached launch shell without a long OS splash.
   let timer;
   try{return await Promise.race([fresh,new Promise(resolve=>{timer=setTimeout(()=>resolve(cached),1500);})]);}
   catch{return cached;}
   finally{clearTimeout(timer);}
  })());return;
 }
 // An exact root-level static filename + release query is required. Never
 // intercept /api, uploaded objects, form exports, audio or external requests.
 if(!/^\/(?:[a-z0-9-]+\.(?:js|css|png|ico)|vendor\/daily-iframe\.js)$/.test(url.pathname)||
    !/^[a-f0-9]{24}$/.test(url.searchParams.get('v')||'')||url.pathname==='/app-shell-worker.js')return;
 event.respondWith((async()=>{
  const cache=await caches.open(STATIC_CACHE),cached=await cache.match(request);
  if(cached)return cached;
  const response=await fetch(request);
  if(response.ok&&response.headers.get('X-WZOS-Public-Asset')==='1')await cache.put(request,response.clone());
  return response;
 })());
});
