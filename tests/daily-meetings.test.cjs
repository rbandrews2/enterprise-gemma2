const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function harness(role='admin'){
 const nodes=new Map(),events={},calls=[],handlers={},frames=[];
 const get=id=>{if(!nodes.has(id))nodes.set(id,{hidden:false,disabled:false,textContent:'',replaceChildren(){},requestFullscreen:async()=>{calls.push('fullscreen');}});return nodes.get(id);};
 let held=null,enabled=true;
 const window={addEventListener:(key,fn)=>(events[key]??=[]).push(fn),wzosClock:{getSession:()=>({role}),api:async(url,options)=>{
  calls.push({url,options});if(held&&url.endsWith('/join'))await held;
  if(url.endsWith('/config'))return{daily_enabled:enabled,daily_origin:'https://synthetic.daily.co'};
  return{url:'https://synthetic.daily.co/wzos-'+'a'.repeat(40),token:'synthetic-private-token'};
 }},DailyIframe:{createFrame:(container,options)=>{const frame={destroyed:false,options,on:(e,fn)=>handlers[e]=fn,join:async body=>calls.push({join:body}),destroy:async()=>{frame.destroyed=true;}};frames.push(frame);return frame;}}};
 const document={getElementById:get,addEventListener:(e,fn)=>(events[e]??=[]).push(fn)};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/daily-meetings.js','utf8'),{window,document,URL,Promise});
 return{get,calls,frames,handlers,controller:window.WzosDailyMeetings,emit:(e,detail)=>{for(const fn of events[e]||[])fn({detail});},hold:p=>held=p,disable:()=>enabled=false};
}
test('explicit admin join prepares privately and only joined event claims connected',async()=>{
 const h=harness();assert.equal(h.calls.length,0);await h.controller.start({id:'meeting'});
 assert.equal(h.calls.filter(c=>c.url?.endsWith('/prepare')).length,1);
 assert.equal(h.frames.length,1);assert.notEqual(h.get('meetings-state').textContent,'CONNECTED');
 assert.equal(h.calls.find(c=>c.join).join.token,'synthetic-private-token');
 assert.equal(h.calls.find(c=>c.join).join.url.includes('token'),false);
 h.handlers['joined-meeting']();assert.equal(h.get('meetings-state').textContent,'CONNECTED');
 h.get('meeting-leave').onclick();assert.equal(h.frames[0].destroyed,true);assert.equal(h.get('meeting-video').hidden,true);
});
test('member joins without creating a room and media cleans up on session/view/offline',async()=>{
 for(const event of ['wzos:session','wzos:view','offline']){
  const h=harness('member');await h.controller.start({id:'meeting'});
  assert.equal(h.calls.some(c=>c.url?.endsWith('/prepare')),false);
  h.emit(event,'schedule');assert.equal(h.frames[0].destroyed,true);
  h.handlers['joined-meeting']();assert.notEqual(h.get('meetings-state').textContent,'CONNECTED');
 }
});
test('late authorization after organization switch never opens camera frame',async()=>{
 const h=harness();let release;h.hold(new Promise(r=>release=r));const pending=h.controller.start({id:'meeting'});
 await new Promise(r=>setImmediate(r));h.emit('wzos:session');release();await pending;
 assert.equal(h.frames.length,0);assert.equal(h.get('meeting-video').hidden,true);
});
test('disabled provider stops cleanly and concurrent clicks do not double join',async()=>{
 const h=harness();h.disable();await h.controller.start({id:'meeting'});
 assert.match(h.get('meetings-notice').textContent,/awaiting secure/);assert.equal(h.frames.length,0);
 const other=harness();let release;other.hold(new Promise(r=>release=r));const pending=other.controller.start({id:'meeting'});
 await other.controller.start({id:'meeting'});release();await pending;assert.equal(other.frames.length,1);
});
