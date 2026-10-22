const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
async function setup(role='admin'){
 class Node{
  constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.textContent='';this.value='';this.disabled=false;}
  append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=[];this.append(...nodes);}setAttribute(k,v){this[k]=v;}
 }
 const ids=new Map(),events={},calls=[];let failure=false;
 const catalog=JSON.parse(fs.readFileSync('services/workspace_preview/training_catalog.json','utf8')).map(c=>({...c,study_status:'not_started'}));
 const api=async(path,options)=>{calls.push({path,options});if(options){if(failure)throw Error('Connection unavailable. Try again.');const body=JSON.parse(options.body);return {version:1,media:body.media?[body.media]:[]};}
  return path==='/api/training'?{items:catalog}:{items:[]};};
 const window={wzosModulesCanLeave:()=>true,addEventListener(){},wzosClock:{api,getSession:()=>({role})},WzosTrainingMedia:{safeURL:value=>value.startsWith('https://')?{}:null,render:()=>new Node('video'),stopAll(){}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/team-modules.js','utf8'),{window,document:{getElementById:id=>{if(!ids.has(id))ids.set(id,new Node('div'));return ids.get(id);},createElement:tag=>new Node(tag),addEventListener:(name,fn)=>events[name]=fn},confirm:()=>false,URL,Blob,setTimeout});
 await events['wzos:view']({detail:'training'});
 const root=ids.get('team-content'),all=(n,p)=>[...(p(n)?[n]:[]),...n.children.filter(c=>typeof c==='object').flatMap(c=>all(c,p))];
 return {root,all,calls,window,setFailure:()=>{failure=true;}};
}
test('admin sees ten numbered URL fields and matching course cards; members see neither editor nor numbers',async()=>{
 const admin=await setup(),urls=admin.all(admin.root,n=>n.type==='url');assert.equal(urls.length,10);
 assert.equal(admin.all(admin.root,n=>n.className==='training-course-number').length,10);
 assert.equal(urls[0].placeholder,'Paste video link for course 1');assert.equal(urls[9].placeholder,'Paste video link for course 10');
 const member=await setup('member');assert.equal(member.all(member.root,n=>n.type==='url').length,0);assert.equal(member.all(member.root,n=>n.className==='training-course-number').length,0);
});
test('save validates clearly, persists the right course and reports success without assessment publishing',async()=>{
 const h=await setup(),url=h.all(h.root,n=>n.type==='url')[0],save=h.all(h.root,n=>n.textContent==='Save link')[0],feedback=h.all(h.root,n=>n.className==='training-link-feedback')[0];
 url.value='https://example.test/video.mp4';url.oninput();assert.equal(h.window.wzosModulesCanLeave(),false);
 await save.onclick();assert.match(feedback.textContent,/confirm permission/);assert.equal(h.calls.filter(c=>c.options).length,0);
 h.all(h.root,n=>n.type==='checkbox')[0].checked=true;h.all(h.root,n=>n.type==='text')[0].value='Our crew';await save.onclick();
 const request=h.calls.find(c=>c.options);assert.equal(request.path,'/api/training-course-videos/pmt');assert.equal(JSON.parse(request.options.body).expected_version,0);
 assert.match(feedback.textContent,/Saved/);assert.equal(save.disabled,false);assert.equal(h.window.wzosModulesCanLeave(),true);
});
test('failed save restores the button, keeps the URL and explains the failure',async()=>{
 const h=await setup(),url=h.all(h.root,n=>n.type==='url')[1],save=h.all(h.root,n=>n.textContent==='Save link')[1];
 h.all(h.root,n=>n.type==='checkbox')[0].checked=true;h.all(h.root,n=>n.type==='text')[0].value='Our crew';url.value='https://example.test/video.mp4';url.oninput();h.setFailure();await save.onclick();
 assert.equal(save.disabled,false);assert.equal(save.textContent,'Save link');assert.equal(url.value,'https://example.test/video.mp4');assert.match(h.all(h.root,n=>n.className==='training-link-feedback')[1].textContent,/Connection unavailable/);assert.equal(h.window.wzosModulesCanLeave(),false);
});
