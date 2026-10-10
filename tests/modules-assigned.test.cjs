const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function harness(){
 const nodes=new Map(),events={},calls=[];
 const element=tag=>({tag,children:[],elements:[],value:'',hidden:false,textContent:'',append(...c){this.children.push(...c);},replaceChildren(...c){this.children=c;},after(){},removeAttribute(){},setAttribute(){},parentNode:{after(){}}});
 const get=id=>{if(!nodes.has(id))nodes.set(id,element('div'));return nodes.get(id);};
 get('modules-view').hidden=false;let session={id:'member',organization_id:'org',role:'member',edition:'enterprise'},held=null;
 const window={wzosFiles:{mount(){}},addEventListener(){},wzosClock:{getSession:()=>session,api:async(url,options)=>{
  calls.push({url,options});
  if(url==='/api/modules/roster')return{items:[]};
  if(url.startsWith('/api/modules/jobs'))return{items:[{id:'job',title:'Dispatched utility work',access_basis:'dispatched_summary'}],total:1};
  if(url.startsWith('/api/dispatch/schedule'))return held?await held:{items:[{id:'assignment',title:'Dispatched utility work',address:'Norfolk',employee_name:'Member',status:'sent',starts_at:'2026-10-11T12:00:00+00:00',ends_at:'2026-10-11T20:00:00+00:00'}],total:1,limit:25};
  return{items:[],total:0,can_edit:session.role==='admin'||url.includes('forms')};
 }},WzosNavigation:{link:()=>({textContent:'Open in Navigation'})}};
 const document={getElementById:get,createElement:element,addEventListener:(name,fn)=>(events[name]??=[]).push(fn)};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/modules.js','utf8'),{window,document,confirm:()=>true,crypto:require('node:crypto').webcrypto});
 const flush=()=>new Promise(resolve=>setImmediate(resolve));
 const emit=(name,detail)=>{for(const fn of events[name]||[])fn({detail});};
 const text=id=>{const flatten=n=>[n,...n.children.flatMap(c=>c.children?flatten(c):[c])];return flatten(get(id)).map(n=>n.textContent).join(' ');};
 return{get,calls,flush,emit,text,setSession:s=>session=s,hold:p=>held=p};
}
test('member schedule renders dispatch as read-only and never acknowledges by viewing',async()=>{
 const h=harness();h.emit('wzos:view','schedule');await h.flush();
 assert.equal(h.get('module-new').hidden,true);assert.match(h.text('schedule-assignments'),/Dispatched utility work/);
 assert.match(h.text('schedule-assignments'),/Confirm receipt in My jobs/);
 assert.equal(h.calls.filter(c=>c.options?.method).length,0);
});
test('form picker includes assigned jobs without requiring original work-order access',async()=>{
 const h=harness();h.emit('wzos:view','form_drafts');await h.flush();h.get('module-new').onclick();
 assert.match(h.text('module-order'),/Dispatched utility work · assigned job/);
 assert.equal(h.calls.some(c=>c.url.startsWith('/api/orders')),false);
});
test('late schedule results cannot restore another organization assignments',async()=>{
 const h=harness();let release;h.hold(new Promise(resolve=>release=resolve));h.emit('wzos:view','schedule');await h.flush();
 h.setSession({id:'core',organization_id:'other',role:'member',edition:'core'});h.emit('wzos:session');
 release({items:[{title:'Private old assignment'}],total:1,limit:25});await h.flush();
 assert.doesNotMatch(h.text('schedule-assignments'),/Private old assignment/);
});
