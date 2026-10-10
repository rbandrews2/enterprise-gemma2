const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function harness(){
 const nodes=new Map(),events={},calls=[],timers=[];
 const element=tag=>({tag,textContent:'',children:[],dataset:{},hidden:false,setAttribute(){},append(...children){for(const c of children){if(typeof c==='object')c.parent=this;this.children.push(c);}},replaceChildren(...children){this.children=[];this.append(...children);},replaceWith(next){const i=this.parent.children.indexOf(this);this.parent.children[i]=next;next.parent=this.parent;},querySelector(){return this.children.find(c=>c?.dataset?.dispatch)||null;}});
 const get=id=>{if(!nodes.has(id))nodes.set(id,element('div'));return nodes.get(id);};
 let session={id:'m',organization_id:'org',role:'member',edition:'enterprise'},pending=1,failNotifications=false;
 const assignment={id:'a',order_title:'Example job',role_title:'Flagger',address:'Norfolk, VA',starts_at:'2026-12-01T12:00:00Z',ends_at:'2026-12-01T20:00:00Z',client_company:'Example client',client_contact_name:'Alex',client_contact_phone:'555-0100',crew:[{name:'Casey',role_title:'Crew lead'}],notes:'West entrance\nBring radios',snapshot_state:'dispatched',status:'sent'};
 const window={addEventListener(){},showWzosView(){},wzosClock:{getSession:()=>session,getOrders:()=>[],async api(path,options){calls.push({path,options});if(path==='/api/dispatch/notifications'){if(failNotifications)throw Error('Connection unavailable');return {pending_count:pending};}if(options){assignment.status='accepted';pending=0;return {status:'accepted'};}return {items:[assignment],limit:25,offset:0,total:1,pending_count:pending};}}};
 const document={hidden:false,getElementById:get,createElement:element,addEventListener(k,f){events[k]=f;}};
 const context={window,document,navigator:{onLine:true},setInterval(fn,delay){timers.push({fn,delay});},Date,Map};vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/navigation-link.js','utf8'),context);vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/dispatch.js','utf8'),context);
 const flatten=n=>[n,...(n.children||[]).flatMap(c=>typeof c==='object'?flatten(c):[])];
 return {window,get,events,calls,timers,flatten,setSession(value){session=value;},setNotificationFailure(value){failNotifications=value;}};
}
test('assignment opens all dispatched details and only an explicit confirmation answers it',async()=>{
 const h=harness(),root=h.get('root');await h.window.wzosDispatch.render(root,()=>true,h.get('notice'));
 let nodes=h.flatten(root),text=nodes.map(n=>n.textContent).join(' ');
 for(const required of ['Example client','Alex','555-0100','Casey','West entrance','Estimated finish','Confirm receipt'])assert.ok(text.includes(required),required);
 assert.equal(h.calls.filter(c=>c.options).length,0);
 const directions=nodes.find(n=>n.textContent==='Open in Navigation');assert.equal(new URL(directions.href).searchParams.get('destination'),'Norfolk, VA');
 await nodes.find(n=>n.textContent==='Confirm receipt').onclick();
 assert.equal(JSON.parse(h.calls.find(c=>c.options).options.body).response,'accepted');
 assert.ok(h.flatten(root).some(n=>n.textContent.includes('Receipt confirmed')));
});
test('notifications are bounded polling and hide when the organization is Core',async()=>{
 const h=harness();assert.equal(h.timers[0].delay,30000);await h.timers[0].fn();
 assert.equal(h.get('assignment-count').textContent,'1');assert.equal(h.get('assignment-alert').hidden,false);
 h.setSession({id:'other',organization_id:'core',role:'admin',edition:'core'});await h.timers[0].fn();
 assert.equal(h.get('assignments-nav').hidden,true);assert.equal(h.get('assignment-alert').hidden,true);
 assert.equal(h.get('assignment-count').textContent,'0');
});
test('a failed notification check stays explicitly unknown and recovers on retry',async()=>{
 const h=harness();h.setNotificationFailure(true);await h.timers[0].fn();
 assert.equal(h.get('assignment-count').textContent,'…');assert.equal(h.get('assignment-alert').hidden,false);
 assert.ok(h.get('assignment-alert').textContent.includes('could not be checked'));
 h.setNotificationFailure(false);await h.timers[0].fn();assert.equal(h.get('assignment-count').textContent,'1');
});
