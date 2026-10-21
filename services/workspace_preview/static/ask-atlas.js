'use strict';
(()=>{
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const user=()=>window.wzosClock?.getSession(),nav=document.getElementById('atlas-nav');
 const root=node('section',undefined,'panel ask-atlas');root.id='ask-atlas-view';root.hidden=true;document.getElementById('main').append(root);
 let sessionEpoch=0,epoch=0,controller=null,currentId=null,active=false,busy=false,config={},stream=null,recorder=null,chunks=[],timer=null,cancelled=false;
 const heading=node('h1','Ask Atlas'),intro=node('p','Work Zone Guardian · Ask about Virginia work-zone guidelines. Read the answer and check its cited sources.'),question=node('textarea'),date=node('input'),status=node('p'),answer=node('div'),references=node('div');
 question.maxLength=500;question.rows=4;question.placeholder='What do I need to know about this operation?';date.type='date';
 const label=(text,input)=>{const n=node('label',text);n.append(input);return n;};
 const button=(text,fn)=>{const b=node('button',text,'secondary');b.type='button';b.onclick=fn;return b;};
 const ask=button('Ask Atlas',()=>run('ask')),search=button('Find references',()=>run('search')),record=button('● Record question',start),stop=button('Stop recording',()=>stopRecording(false)),cancelRecording=button('Cancel recording',()=>stopRecording(true)),cancel=button('Stop waiting',abort),setup=button('Device permissions',()=>window.wzosDeviceSetup?.open()),read=button('Read aloud',speak),silence=button('Stop reading',()=>speechSynthesis.cancel()),clock=node('span','0 / 30 seconds');
 const actions=node('div',undefined,'atlas-actions');actions.append(ask,search,record,stop,cancelRecording,setup,cancel,clock);
 const settings=node('details'),region=node('p','Virginia · VDOT');settings.append(node('summary','Reference settings'),region,label('Reference date',date));
 const speechActions=node('div',undefined,'atlas-actions');speechActions.append(read,silence);
 status.setAttribute('role','status');status.setAttribute('aria-live','polite');answer.className='atlas-answer';references.className='atlas-references';
 root.append(heading,intro,settings,label('Your question',question),actions,status,answer,speechActions,references);
 question.oninput=()=>{window.speechSynthesis?.cancel();answer.replaceChildren();references.replaceChildren();read.hidden=silence.hidden=true;};
 function lock(value){busy=value;ask.disabled=value||!config.enabled||!config.inference_enabled;search.disabled=value||!config.enabled;record.disabled=value||!config.enabled||!config.speech_enabled;question.disabled=date.disabled=value;cancel.hidden=!value;stop.disabled=cancelRecording.disabled=!stream;stop.hidden=cancelRecording.hidden=clock.hidden=!stream;}
 async function api(path,options={}){
  const configuration=path==='/api/atlas/dot/config'||path.endsWith('/cancel'),generation=configuration?sessionEpoch:epoch,identity=user();const auth=await window.wzosAccount.headers();if(generation!==(configuration?sessionEpoch:epoch))throw Error('Account changed.');
  const response=await fetch(path,{...options,cache:'no-store',headers:{'Content-Type':'application/json','X-Preview-Actor':identity?.id,...auth,...options.headers}});
  let data;try{data=await response.json();}catch{throw Error('Atlas could not read the service response. Try again when ready.');}
  if(generation!==(configuration?sessionEpoch:epoch))throw Error('Account changed.');if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Atlas could not complete that request.');return data;
 }
 function abort(){
  if(currentId&&user()?.edition==='enterprise')api('/api/atlas/dot/requests/'+currentId+'/cancel',{method:'POST'}).catch(()=>{});
  controller?.abort();controller=null;currentId=null;epoch++;busy=false;lock(false);status.textContent='Stopped. Your question is still here.';
 }
 function stopTracks(){stream?.getTracks().forEach(t=>t.stop());stream=null;clearInterval(timer);timer=null;stop.disabled=cancelRecording.disabled=true;}
 function stopRecording(discard){if(!stream&&!recorder)return;cancelled=discard;if(recorder?.state==='recording')recorder.stop();stopTracks();if(discard){chunks=[];status.textContent='Recording discarded.';}}
 function clear(){stopRecording(true);abort();question.value='';answer.replaceChildren();references.replaceChildren();read.hidden=silence.hidden=true;window.speechSynthesis?.cancel();status.textContent='';}
 function link(citation){const a=node('a',citation.title||'Source');try{const url=new URL(citation.url);if(url.protocol==='https:'&&!url.username&&!url.password){a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';}}catch{}return a;}
 function excerpt(text){const details=node('details');details.append(node('summary','Read excerpt'),node('p',text));return details;}
 function render(data){
  answer.replaceChildren();references.replaceChildren();read.hidden=silence.hidden=true;
  if(data.draft){
   for(const claim of data.draft.claims){const paragraph=node('p',claim.text),number=(data.citations||[]).findIndex(c=>c.citation_id===claim.citation_id);if(number>=0){const citation=node('a',' ['+(number+1)+']');citation.href='#atlas-source-'+number;paragraph.append(citation);}answer.append(paragraph);}
   for(const item of data.draft.unresolved)answer.append(node('p',item,'atlas-clarify'));
   for(const calculation of data.calculations||[])answer.append(node('p',`${calculation.expression} = ${calculation.result} ${calculation.unit}. Arithmetic checked; confirm the formula applies to your site.`));
   references.append(node('h2','Sources'));for(const [index,citation] of (data.citations||[]).entries()){const card=node('article',undefined,'panel');card.id='atlas-source-'+index;card.append(link(citation),node('p',`${citation.edition||'Edition unspecified'} · PDF page ${citation.page}${citation.label?' · '+citation.label:''}`));references.append(card);}
   status.textContent=data.draft.status==='needs_clarification'?'Atlas needs a few more details.':'Check the cited conditions and exceptions before applying this guidance.';
   read.hidden=!answer.textContent;silence.hidden=read.hidden;
  }else if(data.results){
   status.textContent=data.results.length?'Reference matches. Review status is shown with each source.':'No matching references. Try an operation or section name.';
   for(const citation of data.results){const card=node('article',undefined,'panel');card.append(link(citation),node('p',`${citation.edition||'Edition unspecified'} · PDF page ${citation.page} · ${citation.answer_eligible?'Reviewed extraction; confirm applicability':'Source review needed'}`),excerpt(citation.excerpt||''));references.append(card);}
  }else{status.textContent='Atlas needs reviewed source material for this question. Use Find references.';for(const warning of data.warnings||[])answer.append(node('p',warning));}
 }
 async function run(kind){
  if(busy)return;if(question.value.trim().length>500){status.textContent='Shorten your question to 500 characters.';return;}if(!question.value.trim()){status.textContent='Enter or record a question first.';return;}if(!navigator.onLine){status.textContent='Connect to ask Atlas. Your question stays here.';return;}
  window.speechSynthesis?.cancel();answer.replaceChildren();references.replaceChildren();read.hidden=silence.hidden=true;
  const generation=epoch;currentId=crypto.randomUUID();controller=new AbortController();lock(true);status.textContent=kind==='ask'?'Atlas is reviewing the source context…':'Finding references…';
  try{const data=await api('/api/atlas/dot/'+kind,{method:'POST',signal:controller.signal,body:JSON.stringify({query:question.value.trim(),authority:'VDOT',region:'VA',as_of:date.value,...(kind==='ask'?{request_id:currentId}:{})})});if(generation===epoch)render(data);}
  catch(error){if(generation===epoch)status.textContent=error.message;}finally{if(generation===epoch){currentId=null;controller=null;lock(false);}}
 }
 async function start(){
  if(busy||recorder)return;const generation=epoch;question.oninput();lock(true);
  try{
   if(!navigator.onLine)throw Error('Connect to record a question, or type it instead.');
   const permission=await window.wzosDeviceSetup?.status('microphone');
   if(permission==='denied'||permission==='prompt'||(permission==='unknown'&&!window.wzosDeviceSetup?.remembered())){window.wzosDeviceSetup?.open();lock(false);return;}
   if(!window.MediaRecorder||!navigator.mediaDevices?.getUserMedia)throw Error('Recording is unavailable. Type your question.');
   const ownedStream=await navigator.mediaDevices.getUserMedia({audio:true});
   if(generation!==epoch||!active||document.hidden){ownedStream.getTracks().forEach(t=>t.stop());if(generation===epoch)lock(false);return;}
   stream=ownedStream;chunks=[];cancelled=false;let seconds=0;clock.textContent='0 / 30 seconds';lock(true);cancel.hidden=true;
   recorder=new MediaRecorder(stream);const owned=recorder,parts=chunks;
   owned.ondataavailable=event=>{if(recorder===owned&&!cancelled&&event.data.size)parts.push(event.data);};
   owned.onerror=()=>{if(recorder===owned){stopRecording(true);status.textContent='Recording stopped. Type your question instead.';}};
   owned.onstop=async()=>{
    if(recorder!==owned){ownedStream.getTracks().forEach(t=>t.stop());return;}
    const audio=new Blob(parts,{type:owned.mimeType});parts.length=0;chunks=[];recorder=null;stopTracks();
    if(cancelled||generation!==epoch||!active){if(generation===epoch)lock(false);return;}
    currentId=crypto.randomUUID();controller=new AbortController();lock(true);status.textContent='Atlas is transcribing your question…';
    try{const body=await window.wzosFieldVoice.encodeRecording(audio);if(generation!==epoch)return;const data=await api('/api/atlas/dot/transcribe?request_id='+currentId,{method:'POST',body,headers:{'Content-Type':'audio/wav'},signal:controller.signal});if(generation!==epoch)return;question.value=data.transcript;status.textContent=data.transcript.length>500?'Shorten the question to 500 characters, then select Ask Atlas.':'Review your question, then select Ask Atlas.';}
    catch(error){if(generation===epoch)status.textContent=error.message;}finally{if(generation===epoch){currentId=null;controller=null;lock(false);}}
   };
   recorder.start();timer=setInterval(()=>{clock.textContent=`${++seconds} / 30 seconds`;if(seconds>=30)stopRecording(false);},1000);status.textContent='Recording. Tap Stop when finished.';
  }catch(error){if(generation===epoch){stopTracks();lock(false);status.textContent=error.message;}}
 }
 function speak(){
  if(!window.speechSynthesis||!window.SpeechSynthesisUtterance){status.textContent='Read aloud is unavailable on this device.';return;}
  const voice=speechSynthesis.getVoices().find(v=>v.localService&&v.lang.toLowerCase().startsWith('en'));
  if(!voice){status.textContent='No local English voice is available. You can read the answer here.';return;}
  speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(answer.textContent);utterance.voice=voice;utterance.lang=voice.lang;speechSynthesis.speak(utterance);
 }
 function open(){return user()?.edition==='enterprise'&&window.showWzosView('ask_atlas');}
 function cards(){const grid=document.querySelector('#dashboard-view .hub-grid');if(user()?.edition!=='enterprise'||!grid||document.getElementById('ask-atlas-card'))return;const card=button('Ask Atlas — Work Zone Guardian',open);card.className='panel hub-card atlas-launch';card.id='ask-atlas-card';grid.prepend(card);}
 document.addEventListener('wzos:session',async()=>{sessionEpoch++;clear();config={};root.hidden=true;const enterprise=user()?.edition==='enterprise';nav.textContent=enterprise?'Ask Atlas — Work Zone Guardian':'Atlas assistant';document.getElementById('ask-atlas-card')?.remove();if(!enterprise)return;const generation=sessionEpoch;const today=new Date();date.value=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;cards();lock(false);try{const loaded=await api('/api/atlas/dot/config');if(generation!==sessionEpoch)return;config=loaded;lock(false);if(!config.enabled)status.textContent='Atlas’s DOT reference library is being prepared.';}catch(error){if(generation===sessionEpoch)status.textContent=error.message;}});
 document.addEventListener('wzos:view',event=>{active=event.detail==='ask_atlas';if(!active)clear();else if(!config.enabled)status.textContent='Atlas’s DOT reference library is being prepared.';else if(!config.inference_enabled)status.textContent='Browse references while Atlas answers are being prepared.';cards();});
 document.addEventListener('visibilitychange',()=>{if(document.hidden){stopRecording(true);window.speechSynthesis?.cancel();}});
 window.addEventListener('pagehide',clear);
 const dashboard=document.getElementById('dashboard-view');if(dashboard)new MutationObserver(cards).observe(dashboard,{childList:true,subtree:true});
 window.wzosAskAtlas={open};lock(false);read.hidden=silence.hidden=true;
})();
