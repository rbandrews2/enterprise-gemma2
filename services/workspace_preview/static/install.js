"use strict";
window.wzosInstall=(()=>{
 let invitation=null,installed=window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
 const widgets=[];
 function update(){for(const {button,note} of widgets){button.hidden=installed;note.textContent=installed?'WZOS is running as an installed app.':'Install WZOS on this device, or continue in your browser. Your organization access is the same.';}}
 window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();invitation=event;update();});
 window.addEventListener('appinstalled',()=>{installed=true;invitation=null;update();});
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
  widgets.push({button,note});area.append(button,note);container.append(area);update();
 }
 return {mount};
})();
