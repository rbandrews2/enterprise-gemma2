const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

function navigation({core=false,job=true,leave=true,moduleLeave=true}={}){
 const elements=new Map(),events=[];
 const get=id=>{
  if(!elements.has(id))elements.set(id,{hidden:false,classList:{toggle(){}},setAttribute(){},removeAttribute(){},scrollIntoView(){},focus(){},closest(){return {};}});
  return elements.get(id);
 };
 const context={window:{wzosModulesCanLeave:()=>moduleLeave},session:{can_prepare_atlas:!core},selected:job?{id:'synthetic'}:null,
  api(){},rows:[],canLeave:()=>leave,$:get,atlasPage:'work_orders',CustomEvent:class{constructor(type,options){this.type=type;this.detail=options?.detail;}},
  document:{querySelector:()=>({}),dispatchEvent:event=>events.push(event)}};
 const code=fs.readFileSync('services/workspace_preview/static/workspace.js','utf8');
 // Run the actual shipped navigation definitions, with only their DOM dependencies stubbed.
 vm.runInNewContext(code.slice(code.indexOf('window.atlasNavigate='),code.indexOf('$("clock-nav").addEventListener')),context);
 return {context,events,elements};
}

test('Atlas navigation respects denied transitions and leaves the current view intact',()=>{
 for(const refusal of [{leave:false},{moduleLeave:false}]){
  const {context,events}=navigation(refusal);
  for(const target of ['forms','time_clock','checklist','job_board'])assert.equal(context.window.atlasNavigate(target),false);
  assert.equal(events.length,0);assert.equal(context.atlasPage,'work_orders');
 }
});

test('Core report, unknown targets and missing-job links cannot navigate',()=>{
 const {context,events}=navigation({core:true,job:false});
 for(const target of ['report','planning','checklist','arbitrary_script'])assert.equal(context.window.atlasNavigate(target),false);
 assert.equal(context.window.showWzosView('report'),false);
 assert.equal(context.window.showWzosView('unknown'),false);
 assert.equal(events.length,0);
});

test('Valid module navigation updates the context and reports success',()=>{
 const {context,events,elements}=navigation();
 assert.equal(context.window.atlasNavigate('forms'),true);
 assert.equal(context.atlasPage,'forms');assert.equal(elements.get('modules-view').hidden,false);
 assert.equal(events.at(-1).detail,'forms');
 assert.equal(context.window.atlasNavigate('time_clock'),true);
 assert.equal(context.atlasPage,'time_clock');assert.equal(events.at(-1).type,'wzos:clock-open');
});
