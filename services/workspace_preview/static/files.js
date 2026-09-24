"use strict";
window.wzosFiles = {
 mount(host,kind,id){
  host.replaceChildren();
  if(!id||!window.wzosClock.getSession()?.file_storage_enabled)return;
  const node=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;};
  const section=node('section');section.className='panel';const title=node('h3','Attachments');
  const input=node('input');input.type='file';input.accept='.pdf,.png,.jpg,.jpeg';input.setAttribute('aria-label','Choose attachment');
  const upload=node('button','Upload attachment');upload.type='button';
  const notice=node('p');notice.setAttribute('role','status');const list=node('div');
  section.append(title,node('p','PDF, PNG or JPEG · up to 10 MiB. Downloaded files are not malware-scanned.'),input,upload,notice,list);host.append(section);
  let requestId=null,selectedFile=null,downloadUrl=null;
  input.onchange=()=>{requestId=crypto.randomUUID();selectedFile=input.files[0];};
  const active=()=>host.contains(section);
  const requestHeaders=async()=>({'X-Preview-Actor':window.wzosClock.getSession()?.id||'',...await window.wzosAccount.headers()});
  async function load(){
   try{const data=await window.wzosClock.api(`/api/files?entity_kind=${kind}&entity_id=${encodeURIComponent(id)}`);if(!active())return;list.replaceChildren();
    for(const file of data.items){const button=node('button',`${file.filename} · ${Math.ceil(file.size_bytes/1024)} KB`);button.type='button';button.onclick=async()=>{button.disabled=true;try{const response=await fetch('/api/files/'+file.id,{headers:await requestHeaders()});if(!response.ok)throw Error('Download unavailable. Your access or the file may have changed.');const blob=await response.blob();if(!active())return;if(downloadUrl)URL.revokeObjectURL(downloadUrl);const url=URL.createObjectURL(blob);downloadUrl=url;const a=node('a','Save '+file.filename);a.href=url;a.download=file.filename;notice.replaceChildren(node('span','Download ready. If it does not start, '),a);a.click();setTimeout(()=>{URL.revokeObjectURL(url);if(downloadUrl===url){downloadUrl=null;if(a.isConnected)a.replaceWith(node('span','select the attachment again.'));}},60000);}catch(e){if(active())notice.textContent=e.message;}finally{button.disabled=false;}};list.append(button);}
   }catch(e){if(active())notice.textContent=e.message;}
  }
  upload.onclick=async()=>{
   if(!selectedFile){notice.textContent='Choose a file first.';return;}
   if(selectedFile.size>10*1024*1024){notice.textContent='File exceeds 10 MiB.';return;}
   upload.disabled=true;input.disabled=true;
   try{const response=await fetch(`/api/files/${requestId}?entity_kind=${kind}&entity_id=${encodeURIComponent(id)}&filename=${encodeURIComponent(selectedFile.name)}`,{method:'PUT',headers:{...await requestHeaders(),'Content-Type':selectedFile.type||'application/octet-stream'},body:selectedFile});const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Upload failed');if(active()){notice.textContent='Attachment saved.';input.value='';selectedFile=null;requestId=null;await load();}}
   catch(e){if(active())notice.textContent=e.message+' You can retry the same file.';}
   finally{if(active()){upload.disabled=false;input.disabled=false;}}
  };
  load();
 }
};
