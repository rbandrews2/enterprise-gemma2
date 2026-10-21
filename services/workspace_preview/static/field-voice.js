'use strict';
(()=>{
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const getUser=()=>window.wzosClock.getSession();
 async function api(path,options={}){const generation=epoch,user=getUser(),headers=await window.wzosAccount.headers();if(generation!==epoch)throw Error('Account changed.');const response=await fetch(path,{...options,headers:{'Content-Type':'application/json','X-Preview-Actor':user?.id,...headers,...options.headers}});let data;try{data=await response.json();}catch{throw Error('WZOS could not read the response. Nothing was confirmed saved.');}if(generation!==epoch)throw Error('Account changed.');if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Check the report fields and try again.');return data;}
 const root=node('section',undefined,'panel field-voice');root.id='field-voice-view';root.hidden=true;document.getElementById('main').append(root);
 const nav=node('button','Smart Field Voice','nav-item');nav.id='field-voice-nav';nav.hidden=true;nav.onclick=()=>open();document.querySelector('nav[aria-label="Workspace navigation"]').append(nav);
 let available=false,speech=false,previewOnly=false,jobs=[],epoch=0,active=false,dirty=false,busy=false,fields=null,draft=null,requestId=crypto.randomUUID();
 let stream=null,recorder=null,chunks=[],timer=null,seconds=0,cancelled=false,controller=null;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>!busy&&(!dirty||confirm('Leave this unsaved field report?'))&&(!previous||previous());
 const title=node('h1','Smart Field Voice'),notice=node('p','','voice-notice'),choose=node('select'),transcript=node('textarea'),dateInput=node('input'),description=node('textarea'),locationInput=node('input'),review=node('input'),editor=node('div'),quantities=node('div'),incidents=node('div'),warnings=node('div'),savedList=node('details');
 notice.setAttribute('role','status');transcript.maxLength=6000;transcript.placeholder='Speak or type what happened. Review numbers, units and times.';dateInput.type='date';review.type='checkbox';
 const label=(text,input)=>{const l=node('label',text);l.append(input);return l;};
 const button=(text,fn)=>{const b=node('button',text);b.type='button';b.onclick=fn;return b;};
 const record=button('● Record',start),stop=button('Stop',()=>stopRecording(false)),cancel=button('Cancel recording',()=>stopRecording(true)),generate=button('Create drafts with Atlas',()=>extract()),save=button('Save draft',()=>persist(false)),send=button('Send to office',()=>persist(true)),newReport=button('New report',()=>{if(!dirty||confirm('Discard the unsaved report?'))reset();}),setup=button('Device permissions',()=>window.wzosDeviceSetup.open()),clock=node('p','0 / 30 seconds','voice-timer');
 const actions=node('div',undefined,'voice-actions');actions.append(record,stop,cancel,setup,clock);
 const edits=node('div');edits.append(label('Work date — confirm before sending',dateInput),label('Work description',description),label('Reported location — compare with selected job',locationInput));
 editor.append(edits,node('h2','Production quantities'),quantities,button('Add quantity',()=>{fields.report.production_quantities.push({item_name:'',quantity:null,unit:null});renderEditor();mark();}),node('h2','Incident drafts'),incidents,warnings,label('I reviewed these quantities, incident details, times and priorities.',review));
 const delivery=node('p','','voice-delivery');delivery.setAttribute('role','status');delivery.setAttribute('aria-live','polite');delivery.hidden=true;
 const controls=node('div',undefined,'voice-actions');controls.append(save,send,newReport);editor.append(controls,delivery);editor.hidden=true;
 savedList.append(node('summary','Saved field reports'));root.append(button('Previous reports',()=>window.showWzosView('report')));
 root.append(title,node('p','Choose a job, then record or type your work update. Review Atlas’s drafts, correct any details, and select Send to office when ready.'),label('Selected job',choose),notice,actions,label('Transcript — kept only in this review session',transcript),generate,editor,savedList);
 transcript.oninput=()=>{mark();generate.textContent='Generate drafts from edited transcript';};
 for(const input of [dateInput,description,locationInput])input.oninput=mark;
 choose.onchange=()=>{if(fields&&!confirm('Clear the current unsaved report and switch jobs?')){choose.value=draft?.job_id||jobs[0]?.id||'';return;}reset();};
 function mark(){dirty=true;review.checked=false;}
 function message(text){notice.textContent=text;if(!editor.hidden&&draft?.state!=='sent'){delivery.hidden=!text;delivery.textContent=text;}}
 function receipt(){if(draft?.state!=='sent')return;delivery.hidden=false;delivery.textContent=`Received by office · ${new Date(draft.updated_at).toLocaleString()}\n${draft.submission_ids.length} form(s) saved in Forms hub for your organization’s admins.\nReceipt: ${draft.id}`;send.textContent='Received by office';}
 function lock(value){busy=value;for(const b of [generate,save,send,record,newReport,choose,transcript])b.disabled=value;for(const input of editor.querySelectorAll('input,textarea,select,button'))input.disabled=value||draft?.state==='sent';newReport.disabled=value;generate.disabled=value||previewOnly;record.disabled=value||!speech;}
 function selected(){return jobs.find(j=>j.id===choose.value);}
 function basis(){const job=selected();if(!job)throw Error('Select an authorized job first.');return {job_id:job.id,expected_job_version:job.version};}
 function reset(clear=true){stopRecording(true);fields=null;draft=null;dirty=false;requestId=crypto.randomUUID();editor.hidden=true;delivery.hidden=true;delivery.textContent='';send.textContent='Send to office';review.checked=false;if(clear)transcript.value='';message('Select a job, record or type, then review before sending.');}
 function stopTracks(){if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;clearInterval(timer);timer=null;stop.disabled=cancel.disabled=true;}
 function stopRecording(discard){cancelled=discard;if(recorder?.state==='recording')recorder.stop();stopTracks();if(discard){chunks=[];message('Recording discarded.');}}
 async function wav(blob){
  const context=new AudioContext();let decoded;try{decoded=await context.decodeAudioData(await blob.arrayBuffer());}finally{await context.close();}
  const length=Math.min(Math.floor(decoded.duration*16000),480000);if(!length)throw Error('No speech was recorded.');
  const offline=new OfflineAudioContext(1,length,16000),source=offline.createBufferSource();source.buffer=decoded;source.connect(offline.destination);source.start();const audio=await offline.startRendering(),samples=audio.getChannelData(0),buffer=new ArrayBuffer(44+samples.length*2),view=new DataView(buffer);
  const text=(at,value)=>{for(let i=0;i<value.length;i++)view.setUint8(at+i,value.charCodeAt(i));};text(0,'RIFF');view.setUint32(4,buffer.byteLength-8,true);text(8,'WAVE');text(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,16000,true);view.setUint32(28,32000,true);view.setUint16(32,2,true);view.setUint16(34,16,true);text(36,'data');view.setUint32(40,samples.length*2,true);for(let i=0;i<samples.length;i++){const s=Math.max(-1,Math.min(1,samples[i]));view.setInt16(44+i*2,s<0?s*32768:s*32767,true);}return new Blob([buffer],{type:'audio/wav'});
 }
 async function start(){
  const generation=epoch;record.disabled=true;try{
   basis();if(!navigator.onLine)throw Error('Voice processing needs a connection. Type your report instead.');
   const permission=await window.wzosDeviceSetup.status('microphone');
   if(permission==='denied'||permission==='prompt'||(permission==='unknown'&&!window.wzosDeviceSetup.remembered())){record.disabled=!speech;window.wzosDeviceSetup.open();return;}
   if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw Error('Recording is unavailable on this browser. Type your report instead.');
   stream=await navigator.mediaDevices.getUserMedia({audio:true});if(generation!==epoch||!active){stopTracks();return;}
   chunks=[];cancelled=false;seconds=0;recorder=new MediaRecorder(stream);const owned=recorder;record.disabled=true;stop.disabled=cancel.disabled=false;
   owned.ondataavailable=e=>{if(!cancelled&&e.data.size)chunks.push(e.data);};
   owned.onerror=()=>{stopRecording(true);message('Recording stopped. You can type your report.');};
   owned.onstop=async()=>{
    const audio=new Blob(chunks,{type:owned.mimeType});chunks=[];recorder=null;stopTracks();record.disabled=!speech;
    if(cancelled||generation!==epoch||!active)return;lock(true);controller=new AbortController();
    try{message('Atlas is transcribing your recording…');const body=await wav(audio);if(generation!==epoch||!active)return;const data=await api('/api/field-voice/transcribe?'+new URLSearchParams(basis()),{method:'POST',headers:{'Content-Type':'audio/wav'},body,signal:controller.signal});if(generation!==epoch)return;transcript.value=data.transcript;dirty=true;await extract(true);}
    catch(e){if(generation===epoch)message(e.message);}finally{if(generation===epoch)lock(false);controller=null;}
   };
   recorder.start();timer=setInterval(()=>{seconds++;clock.textContent=`${seconds} / 30 seconds`;if(seconds>=30)stopRecording(false);},1000);message('Recording. Tap Stop when finished.');
  }catch(e){stopTracks();record.disabled=!speech;message('Microphone unavailable. Check Device permissions, or type your report.');}
 }
 async function extract(fromAudio=false){
  if(fields&&!confirm('Replace the current draft fields with a new extraction? Your manual edits will be replaced.'))return;
  const generation=epoch;lock(true);controller ||= new AbortController();
  try{message('Atlas is preparing drafts for your review…');const result=await api('/api/field-voice/extract',{method:'POST',body:JSON.stringify({...basis(),transcript:transcript.value}),signal:controller.signal});if(generation!==epoch)return;fields=result.fields;draft=null;requestId=crypto.randomUUID();renderEditor();mark();message('Review the draft. Nothing has been sent to office.');}
  catch(e){if(generation===epoch)message(e.message);}finally{if(generation===epoch)lock(false);if(!fromAudio)controller=null;}
 }
 function renderEditor(){
  if(!fields)return;editor.hidden=false;delivery.hidden=true;send.textContent='Send to office';dateInput.value=fields.work_date||'';description.value=fields.report.work_description||'';locationInput.value=fields.report.route_location||'';quantities.replaceChildren();incidents.replaceChildren();warnings.replaceChildren();
  for(const q of fields.report.production_quantities){const row=node('div',undefined,'voice-row');for(const [key,title,type] of [['item_name','Item','text'],['quantity','Quantity','number'],['unit','Unit','text']]){const input=node('input');input.type=type;input.value=q[key]??'';if(type==='number'){input.min='0';input.step='any';}input.oninput=()=>{q[key]=type==='number'?(input.value===''?null:Number(input.value)):(input.value||null);mark();};row.append(label(title,input));}row.append(button('Remove',()=>{fields.report.production_quantities=fields.report.production_quantities.filter(v=>v!==q);renderEditor();mark();}));quantities.append(row);}
  for(const incident of fields.report.incidents){const card=node('section',undefined,'panel voice-incident'),details=node('textarea'),time=node('input'),priority=node('select');details.value=incident.details;time.value=incident.time_mentioned||'';for(const value of ['','low','medium','high']){const option=node('option',value||'Unconfirmed priority');option.value=value;priority.append(option);}priority.value=incident.priority||'';details.oninput=()=>{incident.details=details.value;mark();};time.oninput=()=>{incident.time_mentioned=time.value||null;mark();};priority.onchange=()=>{incident.priority=priority.value||null;mark();};card.append(label('Incident details',details),label('Time mentioned — do not guess a date/timezone',time),label('Priority suggestion — review',priority),button('Remove incident',()=>{fields.report.incidents=fields.report.incidents.filter(v=>v!==incident);renderEditor();mark();}));incidents.append(card);}
  for(const warning of fields.report.unresolved)warnings.append(node('p',warning,'voice-warning'));receipt();lock(busy);
 }
 async function persist(toOffice){
  if(!fields)return;if(toOffice&&!review.checked){message('Review the report and check the confirmation before sending.');return;}
  fields.work_date=dateInput.value||null;fields.report.work_description=description.value||null;fields.report.route_location=locationInput.value||null;
  const generation=epoch;lock(true);message(toOffice?'Sending to office…':'Saving draft…');try{
   if(draft?.state==='sent'){receipt();return;}
   if(!draft)draft=await api('/api/field-voice/drafts',{method:'POST',body:JSON.stringify({...basis(),request_id:requestId,fields})});
   else if(dirty)draft=await api('/api/field-voice/drafts/'+draft.id,{method:'PATCH',body:JSON.stringify({expected_version:draft.version,fields})});
   if(generation!==epoch)return;dirty=false;
   if(toOffice){draft=await api('/api/field-voice/drafts/'+draft.id+'/send-to-office',{method:'POST',body:JSON.stringify({expected_version:draft.version,reviewed:true})});if(generation!==epoch)return;transcript.value='';receipt();message('Received by office. Your receipt is below the Send button.');document.dispatchEvent(new CustomEvent('wzos:office-sent'));}
   else message('Structured draft saved. Audio and transcript were not saved.');await saved();
  }catch(e){if(generation===epoch)message(e.message);}finally{if(generation===epoch)lock(false);}
 }
 async function saved(){const generation=epoch;try{const data=await api('/api/field-voice/drafts');if(generation!==epoch)return;savedList.replaceChildren(node('summary','Saved field reports'));for(const item of data.items){savedList.append(button(`${item.fields.work_date||'Date needed'} · ${item.state} · ${item.fields.report.work_description||'Draft'}`,()=>{if(dirty&&!confirm('Discard current unsaved draft?'))return;choose.value=item.job_id;draft=item;fields=structuredClone(item.fields);transcript.value='';dirty=false;renderEditor();message(item.state==='sent'?'Received by office. Start a new report to make another submission.':'Reopened structured draft.');}));}}catch(e){message(e.message);}}
 async function open(jobId){if(!available||!window.showWzosView('field_voice'))return;active=true;const generation=epoch;try{jobs=(await api('/api/field-voice/jobs')).items;if(generation!==epoch)return;choose.replaceChildren();for(const job of jobs){const option=node('option',`${job.title} · ${job.address}`);option.value=job.id;choose.append(option);}if(jobId)choose.value=jobId;await saved();if(!fields)message('');}catch(e){message(e.message);}}
 function jobButton(id){return button('Record field report',()=>open(id));}
 function mountCard(){const grid=document.querySelector('#dashboard-view .hub-grid');if(available&&grid&&!document.getElementById('field-voice-card')){const b=button('Smart Field Voice',()=>open());b.id='field-voice-card';b.className='panel hub-card voice-launch';grid.prepend(b);}}
 const dashboard=document.getElementById('dashboard-view');if(dashboard)new MutationObserver(mountCard).observe(dashboard,{childList:true,subtree:true});
 async function session(){epoch++;active=false;controller?.abort();stopRecording(true);fields=null;draft=null;jobs=[];choose.replaceChildren();savedList.replaceChildren(node('summary','Saved field reports'));quantities.replaceChildren();incidents.replaceChildren();warnings.replaceChildren();description.value=locationInput.value=dateInput.value=transcript.value='';editor.hidden=true;review.checked=false;dirty=false;busy=false;available=false;nav.hidden=true;root.hidden=true;document.getElementById('field-voice-card')?.remove();const generation=epoch;if(getUser()?.edition!=='enterprise')return;try{const config=await api('/api/field-voice/config');if(generation!==epoch)return;available=config.enabled;previewOnly=config.preview_only===true;speech=config.speech_enabled&&!previewOnly;nav.hidden=!available;record.disabled=!speech;generate.disabled=setup.disabled=previewOnly;stop.disabled=cancel.disabled=true;mountCard();const menu=document.querySelector('nav[aria-label="Workspace navigation"]');if(available){menu.prepend(nav);nav.after(document.getElementById('atlas-nav'));}}catch{}}
 document.addEventListener('wzos:session',session);
 document.addEventListener('wzos:view',e=>{active=e.detail==='field_voice';if(!active){epoch++;controller?.abort();stopRecording(true);transcript.value='';dirty=false;fields=null;draft=null;editor.hidden=true;}mountCard();});
 document.addEventListener('wzos:job-context',()=>queueMicrotask(()=>{const area=document.getElementById('order-navigation'),job=window.wzosClock.getSelected?.();if(area&&job&&available)area.append(jobButton(job.id));}));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stopRecording(true);});window.addEventListener('pagehide',()=>{controller?.abort();stopRecording(true);});window.addEventListener('beforeunload',e=>{if(dirty||busy||stream||recorder?.state==='recording'){e.preventDefault();e.returnValue='';}});
 window.wzosFieldVoice={available:()=>available,open,jobButton,encodeRecording:wav};
})();
