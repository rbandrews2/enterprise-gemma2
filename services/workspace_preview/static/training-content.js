"use strict";
// Organization training: authored modules, assignments and scored assessments.
// Self-reported study, assessment completion and verified qualifications stay separate.
(() => {
 const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;if(tag==='button'){n.type='button';n.className='secondary';}return n;};
 const labelled=(caption,control)=>{const l=el('label',caption);l.append(control);return l;};
 const api=(...a)=>window.wzosClock.api(...a);
 const local=v=>v?new Date(v).toLocaleString():'';
 let view=null,epoch=0,busy=false,dirty=false;
 const previous=window.wzosModulesCanLeave;
 window.wzosModulesCanLeave=()=>!busy&&(!dirty||confirm('Leave unsaved training changes?'))&&(!previous||previous());
 const root=el('section');root.className='panel report-section';root.id='training-content-panel';
 document.getElementById('team-view').append(root);
 const notice=el('p');notice.setAttribute('role','status');
 const say=t=>{notice.textContent=t;};
 async function run(control,work,done){if(busy)return;busy=true;control.disabled=true;try{const result=await work();dirty=false;await show();say(typeof done==='function'?done(result):done);}catch(e){say(e.message);}finally{busy=false;control.disabled=false;}}

 function takeModule(item,host,generation){
  host.replaceChildren(el('h3',item.title),el('p',item.summary));
  for(const s of item.sections){host.append(el('h4',s.heading),el('p',s.body));}
  for(const m of item.media){const a=el('a',m.title+' (opens the organization’s link)');a.href=m.url;a.target='_blank';a.rel='noopener noreferrer';host.append(el('p',''),a,el('p','Use confirmed by your organization: '+m.rights_note));}
  const form=el('form');form.onsubmit=e=>e.preventDefault();
  item.questions.forEach((q,i)=>{const set=el('fieldset');set.append(el('legend',`${i+1}. ${q.prompt}`));q.options.forEach((o,j)=>{const lab=el('label'),r=el('input');r.type='radio';r.name='q'+i;r.value=String(j);Object.assign(r.style,{width:'auto',display:'inline-block',marginRight:'.5rem'});lab.append(r,o);set.append(lab);});form.append(set);});
  const submit=el('button',`Submit answers (pass mark ${item.passing_score}%)`);submit.className='primary';let retry=null;
  form.onchange=()=>{retry=null;};
  submit.onclick=()=>{const answers=item.questions.map((_,i)=>{const c=form.querySelector(`input[name=q${i}]:checked`);return c?Number(c.value):-1;});
   if(answers.includes(-1)){say('Answer every question first.');return;}
   retry=retry||{request_id:crypto.randomUUID(),module_version:item.version,answers};
   run(submit,async()=>{const r=await api(`/api/training-modules/${item.id}/attempts`,{method:'POST',body:JSON.stringify(retry)});retry=null;return r;},
    r=>r.passed?`Passed with ${r.score}%. This is an assessment completion record, not a certificate or verified qualification.`:`Scored ${r.score}% (pass mark ${r.passing_score}%). Attempts used: ${r.attempts_used} of ${r.attempts_allowed}. Open the training to try again.`);};
  form.append(submit);host.append(form);
 }

 function parseQuestions(text){
  // Format: "Q: prompt" then one option per line; "* " marks the correct option, "- " the others.
  const out=[];let q=null;
  for(const raw of text.split('\n')){const line=raw.trim();if(!line)continue;
   if(/^q:/i.test(line)){q={prompt:line.slice(2).trim(),options:[],answer:-1};out.push(q);continue;}
   if(!q||!/^[-*]\s/.test(line))throw Error('Questions: start with "Q:" and list options with "- " or "* " (correct).');
   if(line.startsWith('*'))q.answer=q.options.length;q.options.push(line.slice(2).trim());}
  for(const item of out)if(item.answer<0)throw Error(`Mark the correct option with "* " for: ${item.prompt}`);
  return out;
 }
 const formatQuestions=qs=>qs.map(q=>['Q: '+q.prompt,...q.options.map((o,i)=>(i===q.answer?'* ':'- ')+o)].join('\n')).join('\n\n');
 const parseSections=text=>text.split(/\n\s*\n/).map(b=>b.trim()).filter(Boolean).map(b=>{const [heading,...rest]=b.split('\n');return {heading:heading.trim(),body:rest.join('\n').trim()||heading.trim()};});
 const formatSections=ss=>ss.map(s=>s.heading+'\n'+s.body).join('\n\n');

 function editor(existing,host){
  const d=existing?.draft||{title:'',summary:'',sections:[],media:[],questions:[],passing_score:80,max_attempts:3};
  const form=el('form');form.onsubmit=e=>e.preventDefault();form.oninput=()=>{dirty=true;};
  const id=el('input'),title=el('input'),summary=el('textarea'),content=el('textarea'),questions=el('textarea'),pass=el('input'),tries=el('input');
  id.value=existing?.id||'';id.disabled=!!existing;id.pattern='[a-z0-9][a-z0-9_-]{0,59}';title.value=d.title;summary.value=d.summary;content.value=formatSections(d.sections);content.rows=8;questions.value=formatQuestions(d.questions);questions.rows=8;
  pass.type=tries.type='number';pass.min=50;pass.max=100;pass.value=d.passing_score;tries.min=1;tries.max=10;tries.value=d.max_attempts;
  content.placeholder='Heading on the first line, then the text. Separate sections with a blank line.';questions.placeholder='Q: Question text\n- Wrong option\n* Correct option';
  const media=d.media[0]||{},mTitle=el('input'),mUrl=el('input'),mRights=el('input'),mNote=el('input');mTitle.value=media.title||'';mUrl.value=media.url||'';mUrl.type='url';mUrl.placeholder='https://…';mRights.type='checkbox';mRights.checked=!!media.rights_confirmed;Object.assign(mRights.style,{width:'auto',display:'inline-block',marginRight:'.5rem'});mNote.value=media.rights_note||'';
  const rightsLabel=el('label');rightsLabel.append(mRights,'Our organization owns or is licensed to use this media for training');
  const save=el('button','Save draft'),publish=el('button','Publish current draft');publish.className='primary';publish.disabled=!existing;
  form.append(labelled('Module identifier (lowercase, cannot change later)',id),labelled('Title',title),labelled('Summary',summary),labelled('Training content',content),
   el('h4','Optional video or document link'),labelled('Link title',mTitle),labelled('Link (https)',mUrl),rightsLabel,labelled('Rights note (source, license or owner)',mNote),
   labelled('Assessment questions',questions),labelled('Pass mark (%)',pass),labelled('Attempts allowed per version',tries),save,publish);
  save.onclick=()=>{let body;try{body={expected_version:existing?.draft_version||0,title:title.value,summary:summary.value,sections:parseSections(content.value),
    media:mUrl.value?[{title:mTitle.value||'Training video',url:mUrl.value.trim(),rights_confirmed:mRights.checked,rights_note:mNote.value}]:[],questions:parseQuestions(questions.value),passing_score:Number(pass.value),max_attempts:Number(tries.value)};}catch(e){say(e.message);return;}
   run(save,()=>api('/api/training-modules/'+encodeURIComponent(id.value.trim()),{method:'PUT',body:JSON.stringify(body)}),'Draft saved. Members see it only after you publish.');};
  publish.onclick=()=>{if(dirty){say('Save the draft before publishing.');return;}run(publish,()=>api(`/api/training-modules/${existing.id}/publish`,{method:'POST',body:JSON.stringify({expected_version:existing.draft_version})}),'Published. Assign it to members below.');};
  host.replaceChildren(form);
 }

 async function recordQualification(c,org){
  // Uses Codex's employee qualification contract; creates an unreviewed record that an admin must verify.
  const qid=('training-'+c.module_id).slice(0,80),person=await api('/api/account/employees/'+encodeURIComponent(c.user_id));
  const current=(person.qualifications||[]).find(q=>q.id===qid);
  if(current&&current.review_status!=='unreviewed')throw Error('This qualification was already reviewed in Employees.');
  return api(`/api/account/employees/${encodeURIComponent(c.user_id)}/qualifications/${qid}`,{method:'PUT',body:JSON.stringify({expected_version:current?.version||0,title:c.title,issuer:org+' internal training',
   credential_number:'',issued_on:c.completed_at.slice(0,10),expires_on:null,review_status:'unreviewed',evidence_reference:`WZOS assessment completion ${c.id} (version ${c.module_version}, score ${c.score}%)`,review_note:''})});
 }

 async function show(){
  const generation=++epoch;root.replaceChildren();root.hidden=view!=='training';if(root.hidden)return;
  const session=window.wzosClock.getSession(),admin=session?.role==='admin';
  root.append(el('h2','Organization training'),el('p','Three separate records: self-reported study (above, your own statement), assessment completion (here, scored by WZOS on a published module) and verified qualifications (reviewed by an admin in Employees). Passing an assessment is not a certificate and does not verify a qualification.'),notice);
  try{
   const [modules,assignments,completions]=await Promise.all([api('/api/training-modules'),api('/api/training-assignments'),api('/api/training-completions')]);
   if(generation!==epoch)return;
   const due=Object.fromEntries(assignments.items.filter(a=>a.user_id===session?.id).map(a=>[a.module_id+':'+a.module_version,a]));
   // Learner view (admins can preview too).
   const learn=el('section');learn.append(el('h3','Available training'));const host=el('div');
   const published=admin?modules.items.filter(m=>m.status==='published'):modules.items;
   if(!published.length)learn.append(el('p','No published training yet.'));
   for(const m of published){const id=m.id,version=admin?m.published_version:m.version,title=admin?m.draft.title:m.title,a=due[id+':'+version];
    const row=el('p',`${title} · version ${version}${a?` · ${a.status==='completed'?'Completed':'Assigned'}${a.due_on?' · due '+a.due_on:''}`:''}`);
    const open=el('button','Open training');open.onclick=async()=>{try{takeModule(await api(`/api/training-modules/${id}/versions/${version}`),host,generation);host.scrollIntoView({block:'start'});}catch(e){say(e.message);}};
    learn.append(row,open);}
   learn.append(host);root.append(learn);
   const mine=completions.items.filter(c=>c.user_id===session?.id);
   const done=el('section');done.append(el('h3','My assessment completions'));
   done.append(mine.length?Object.assign(el('ul'),{}):el('p','None yet.'));
   if(mine.length){const ul=done.lastChild;for(const c of mine)ul.append(el('li',`${c.title} · version ${c.module_version} · ${c.score}% · ${local(c.completed_at)} · assessment completion (not a certificate)`));}
   root.append(done);
   if(!admin)return;
   // Admin authoring, assignment and oversight for this organization only.
   const authoring=el('section');authoring.append(el('h3','Training content (admin)'));
   const editorHost=el('div'),list=el('ul');
   for(const m of modules.items){const li=el('li',`${m.draft.title} (${m.id}) · ${m.status}${m.published_version?' · published v'+m.published_version:''}${m.draft_version?' · draft rev '+m.draft_version:''}`);const edit=el('button','Edit');edit.onclick=()=>editor(m,editorHost);li.append(' ',edit);list.append(li);}
   const create=el('button','New training module');create.onclick=()=>editor(null,editorHost);
   authoring.append(list,create,editorHost);root.append(authoring);
   const assign=el('section');assign.append(el('h3','Assign training'));
   const pick=el('select');for(const m of modules.items.filter(m=>m.status==='published')){const o=el('option',`${m.draft.title} (v${m.published_version})`);o.value=m.id;pick.append(o);}
   const roster=(await api('/api/modules/roster')).items;if(generation!==epoch)return;
   const people=el('div');for(const p of roster){const lab=el('label'),box=el('input');box.type='checkbox';box.value=p.id;Object.assign(box.style,{width:'auto',display:'inline-block',marginRight:'.5rem'});lab.append(box,`${p.name} · ${p.role}`);people.append(lab);}
   const dueOn=el('input');dueOn.type='date';const go=el('button','Assign');go.className='primary';go.disabled=!pick.options.length;
   go.onclick=()=>{const ids=[...people.querySelectorAll('input:checked')].map(b=>b.value);if(!ids.length){say('Choose at least one person.');return;}run(go,()=>api('/api/training-assignments',{method:'POST',body:JSON.stringify({module_id:pick.value,user_ids:ids,due_on:dueOn.value||null})}),'Training assigned.');};
   assign.append(labelled('Published module',pick),people,labelled('Due date (optional)',dueOn),go);
   const names=Object.fromEntries(roster.map(p=>[p.id,p.name])),status=el('ul');
   for(const a of assignments.items){const li=el('li',`${names[a.user_id]||a.user_id} · ${a.title} v${a.module_version} · ${a.status}${a.due_on?' · due '+a.due_on:''} · attempts ${a.attempts}`);
    if(a.status==='assigned'){const c=el('button','Cancel');c.onclick=()=>run(c,()=>api(`/api/training-assignments/${a.id}/cancel`,{method:'POST'}),'Assignment cancelled.');li.append(' ',c);}status.append(li);}
   assign.append(el('h4','Assignment status'),status);root.append(assign);
   const records=el('section');records.append(el('h3','Assessment completions (organization)'));
   const employees=await api('/api/account/employees?limit=1').then(()=>true,()=>false);if(generation!==epoch)return;
   if(!completions.items.length)records.append(el('p','None yet.'));
   for(const c of completions.items){const li=el('p',`${names[c.user_id]||c.user_id} · ${c.title} v${c.module_version} · ${c.score}% · ${local(c.completed_at)}`);
    if(employees){const q=el('button','Add as unreviewed qualification');q.onclick=()=>run(q,()=>recordQualification(c,session.organization),'Added to Employees as unreviewed. Verify it there before it counts for dispatch.');li.append(' ',q);}
    records.append(li);}
   if(!employees)records.append(el('p','Qualification records are managed in Employees when organization accounts are enabled.'));
   root.append(records);
  }catch(error){if(generation===epoch)say(error.message);}
 }
 document.addEventListener('wzos:view',e=>{view=e.detail;dirty=false;show();});
 document.addEventListener('wzos:session',()=>{dirty=false;show();});
})();
