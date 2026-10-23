"use strict";
window.wzosBulkAccounts = (() => {
 const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 function open(api){
  const dialog=el('dialog');dialog.className='employee-import-dialog bulk-accounts-dialog';
  const status=el('p');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  const file=el('input');file.type='file';file.accept='.csv,.xlsx';file.setAttribute('aria-label','Employee accounts CSV or Excel file');
  const paste=el('textarea');paste.rows=5;paste.autocomplete='off';paste.spellcheck=false;paste.setAttribute('aria-label','Paste spreadsheet cells including column headers');
  const fileLabel=el('label','Upload CSV or Excel (.xlsx)');fileLabel.append(file);
  const pasteLabel=el('label','Or paste rows copied from your spreadsheet, including the header');pasteLabel.append(paste);
  const template=el('button','Download CSV template');template.type='button';
  template.onclick=()=>{const url=URL.createObjectURL(new Blob(['name,email,username,password,role\r\n'],{type:'text/csv;charset=utf-8'}));const a=el('a');a.href=url;a.download='wzos-account-template.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  const review=el('button','Review accounts'),confirm=el('button','Create reviewed accounts'),close=el('button','Close');
  const consent=el('input');consent.type='checkbox';const consentLabel=el('label','I reviewed the employees and their access levels. Create these accounts.');consentLabel.className='bulk-confirm';consentLabel.append(consent);
  const output=el('div');let upload=null,rows=[],busy=false,closed=false,results=new Map();
  confirm.disabled=true;consent.disabled=true;
  function invalidate(){upload=null;rows=[];results.clear();output.replaceChildren();consent.checked=false;consent.disabled=true;confirm.disabled=true;status.textContent='';}
  file.onchange=()=>{paste.value='';invalidate();};paste.oninput=()=>{file.value='';invalidate();};
  function lock(value){busy=value;file.disabled=value;paste.disabled=value;review.disabled=value;template.disabled=value;close.disabled=value;consent.disabled=value||!upload;confirm.disabled=value||!upload||!consent.checked;}
  function render(){
   const table=el('table');table.className='employee-import-table';const head=el('tr');for(const title of ['Row','Employee','Username','Access','Result'])head.append(el('th',title));table.append(head);
   for(const row of rows){const tr=el('tr');const result=results.get(row.index);for(const text of [String(row.index+1),`${row.name} · ${row.email}`,row.username,row.role,result?(result.created?'Created':result.error):(row.errors.join(' ')||(row.state==='ready'?'Already created':row.state==='pending'?'Reserved — retry setup':'Ready'))])tr.append(el('td',text));table.append(tr);}
   output.replaceChildren(table);
  }
  review.onclick=async()=>{
   if(busy)return;invalidate();lock(true);status.textContent='Reviewing employee accounts…';
   try{
    let content,format;
    if(file.files?.length){const source=file.files[0];if(source.size>1048576)throw Error('Use a file no larger than 1 MiB.');
     if(/\.xlsx$/i.test(source.name)){format='xlsx';const bytes=new Uint8Array(await source.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));content=btoa(binary);}
     else if(/\.csv$/i.test(source.name)){format='csv';content=await source.text();}else throw Error('Choose a CSV or XLSX file.');
    }else{content=paste.value;format=content.includes('\t')?'tsv':'csv';if(!content.trim())throw Error('Upload a file or paste spreadsheet rows first.');}
    const candidate={batch_id:crypto.randomUUID(),format,content};
    const data=await api('/api/account/managed/bulk/review',candidate);if(closed)return;
    rows=data.items;render();
    status.textContent=`${rows.length} employees reviewed. ${data.seats_needed} new logins needed. ${data.license.seats_available===null?'Seat allowance is not configured.':`${data.license.seats_available} logins available.`}`;
    if(data.ignored_columns.length)status.textContent+=` Not imported: ${data.ignored_columns.join(', ')}. Accounts belong to your current organization.`;
    if(!data.capacity_ok)status.textContent+=' Not enough available logins. Reduce the list or increase your allowance.';
    if(rows.some(r=>r.errors.length))status.textContent+=' Correct the indicated rows in your spreadsheet and review again.';
    if(data.valid)upload=candidate;
   }catch(e){if(!closed)status.textContent=e.message;}finally{if(!closed)lock(false);}
  };
  consent.onchange=()=>{confirm.disabled=busy||!upload||!consent.checked;};
  confirm.onclick=async()=>{
   if(busy||!upload||!consent.checked)return;lock(true);
   const remaining=rows.filter(r=>!results.get(r.index)?.created&&r.state!=='ready');
   try{
    for(let offset=0;offset<remaining.length&&!closed;offset+=5){
     const selection=remaining.slice(offset,offset+5).map(r=>r.index);
     status.textContent=`Creating accounts ${offset+1}–${Math.min(offset+5,remaining.length)} of ${remaining.length}…`;
     const response=await api('/api/account/managed/bulk/create',{...upload,reviewed:true,rows:selection});if(closed)break;
     for(const result of response.items)results.set(result.index,result);render();
    }
    if(!closed){const ready=rows.filter(r=>results.get(r.index)?.created||r.state==='ready').length;
     status.textContent=`${ready} of ${rows.length} accounts created. No invitations or messages were sent. Share initial passwords privately; employees must change them on first sign-in.`;
     if(ready===rows.length){upload=null;file.value='';paste.value='';confirm.textContent='Accounts created';}
     else{status.textContent+=' Review failed rows below. Retry only unfinished accounts.';confirm.textContent='Retry unfinished accounts';}
    }
   }catch(e){if(!closed){status.textContent=`${e.message} Completed rows are preserved. Retry unfinished accounts in this window.`;confirm.textContent='Retry unfinished accounts';}}
   finally{if(!closed)lock(false);}
  };
  const sessionChanged=()=>dialog.close();document.addEventListener('wzos:session',sessionChanged);
  dialog.addEventListener('cancel',event=>{if(busy)event.preventDefault();});close.onclick=()=>{if(!busy)dialog.close();};
  dialog.addEventListener('close',()=>{closed=true;upload=null;rows=[];results.clear();file.value='';paste.value='';document.removeEventListener('wzos:session',sessionChanged);dialog.remove();},{once:true});
  dialog.append(el('h2','Bulk create employee accounts'),el('p','Upload up to 500 employees, review access, then create their logins. Invitations are optional. Use admin or member for access level.'),template,fileLabel,pasteLabel,el('p','Passwords stay in this window during creation. Close it when finished. Existing accounts are never overwritten.'),review,status,output,consentLabel,confirm,close);
  document.body.append(dialog);dialog.showModal();return dialog;
 }
 return {open};
})();
