'use strict';
window.wzosDeviceSetup=(()=>{
 const node=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 const panel=node('section');panel.className='panel device-setup';panel.hidden=true;panel.id='device-setup';
 document.getElementById('main').prepend(panel);
 let scope='',generation=0,busy=false,locationConfirmed=false;
 const key=()=>`wzos-device-setup-v1:${scope}`;
 function remembered(){try{return localStorage.getItem(key())==='done';}catch{return false;}}
 function remember(){try{localStorage.setItem(key(),'done');}catch{}}
 async function status(name){try{return (await navigator.permissions.query({name})).state;}catch{return name==='geolocation'&&locationConfirmed?'granted':'unknown';}}
 const mic=async()=>{const stream=await navigator.mediaDevices.getUserMedia({audio:true});stream.getTracks().forEach(t=>t.stop());};
 const location=()=>new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(()=>{locationConfirmed=true;resolve();},error=>{locationConfirmed=false;reject(error);},{timeout:12000,maximumAge:0,enableHighAccuracy:false}));
 function open(){if(!panel.children.length){render().then(open);return;}panel.hidden=false;panel.scrollIntoView({block:'nearest'});}
 async function render(){
  const current=++generation,user=window.wzosClock?.getSession();if(!user){panel.hidden=true;return;}
  scope=`${user.organization_id}:${user.id}`;panel.replaceChildren();
  panel.append(node('h2','Set up your device'),node('p','Enable microphone for voice reports and meetings, and location for local weather, navigation and time records. Setup records no audio, saves no coordinates and starts no background tracking. Your browser controls how long permissions last.'));
  if(user.edition==='enterprise')panel.append(node('p','When you record a field report, Google processes the audio for transcription and Atlas uses the transcript to draft your reports. WZOS discards the recording after transcription. Review the drafts before sending them to your office.'));
  const message=node('p');message.setAttribute('role','status');
  const enable=node('button','Enable microphone & location');enable.type='button';enable.className='primary';
  enable.onclick=async()=>{
   if(busy)return;busy=true;enable.disabled=true;const results=[];
   for(const [name,run] of [['microphone',mic],['geolocation',location]]){
    if(current!==generation)break;
    try{if(await status(name)!=='granted')await run();results.push(`${name==='geolocation'?'Location':'Microphone'} ready`);}
    catch{results.push(`${name==='geolocation'?'Location':'Microphone'} unavailable; you can enable it later in browser settings`);}
   }
   busy=false;if(current!==generation)return;remember();message.textContent=results.join('. ')+'.';enable.disabled=false;enable.textContent='Check device permissions';document.dispatchEvent(new CustomEvent('wzos:device-permissions'));
  };
  const later=node('button','Continue');later.type='button';later.onclick=()=>{remember();panel.hidden=true;};
  panel.append(enable,later,message);
  const states=await Promise.all([status('microphone'),status('geolocation')]);if(current!==generation)return;
  panel.hidden=remembered()||states.every(s=>s==='granted');
 }
 document.addEventListener('wzos:session',render);window.addEventListener('appinstalled',render);
 if(window.wzosClock?.getSession())render();
 return {open,status,remembered};
})();
