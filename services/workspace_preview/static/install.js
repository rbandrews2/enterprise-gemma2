"use strict";
window.wzosInstall=(()=>{
 const display=window.matchMedia('(display-mode: standalone)');
 let invitation=null,installed=display.matches||navigator.standalone===true,checking=false,confirmed=false;
 const widgets=[];
 function update(){for(const {area,button,note} of widgets){area.hidden=installed;button.hidden=installed;note.textContent=installed?'WZOS is installed on this device.':'Install WZOS on this device, or continue in your browser. Your organization access is the same.';}}
 async function detect(){
  if(display.matches||navigator.standalone===true){installed=true;update();return;}
  if(checking||!navigator.getInstalledRelatedApps)return;
  checking=true;
  try{const apps=await navigator.getInstalledRelatedApps();
   installed=confirmed||display.matches||navigator.standalone===true||apps.some(app=>app.platform==='webapp'&&app.url==='https://app.workzoneos.org/manifest.webmanifest');update();
  }catch{/* Unsupported or denied detection must not claim the app is installed. */}
  finally{checking=false;}
 }
 display.addEventListener?.('change',detect);window.addEventListener('pageshow',detect);
 window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();invitation=event;update();});
 window.addEventListener('appinstalled',()=>{confirmed=true;installed=true;invitation=null;update();});
 function mount(container){
  const area=document.createElement('section');area.className='wzos-install';
  const button=document.createElement('button');button.type='button';button.textContent='Install WZOS';
  const note=document.createElement('p');note.setAttribute('role','status');
  button.onclick=async()=>{
   if(!invitation){note.textContent='Use your browser’s Install app or Add to Home Screen option. Installation is optional; you can continue here.';return;}
   button.disabled=true;
   try{const current=invitation;invitation=null;await current.prompt();const result=await current.userChoice;note.textContent=result.outcome==='accepted'?'Installation requested. Open WZOS from your device when it is ready.':'Installation dismissed. You can continue in your browser.';}
   catch(e){note.textContent='Installation is unavailable right now. You can continue in your browser.';}
   finally{button.disabled=false;}
  };
  widgets.push({area,button,note});area.append(button,note);container.append(area);update();detect();
 }
 return {mount};
})();
