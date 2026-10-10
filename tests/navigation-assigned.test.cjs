const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function harness(){
 const nodes=new Map(),events={},calls=[],navigator={onLine:true};
 const element=tag=>({tag,children:[],textContent:'',append(...c){this.children.push(...c);},replaceChildren(...c){this.children=c;}});
 const get=id=>{if(!nodes.has(id))nodes.set(id,element('div'));return nodes.get(id);};
 let session={id:'member',organization_id:'org1',edition:'enterprise'},hold=null;
 const window={addEventListener(){},wzosModulesCanLeave:()=>true,wzosClock:{getSession:()=>session,getOrders:()=>[],api:async url=>{
  calls.push(url);if(hold)return hold;
  if(url==='/api/orders')return{items:[{id:'same',title:'Private revised title',address:'Changed address'}]};
  return{items:[{order_id:'same',order_title:'Frozen dispatched job',address:'Norfolk, VA'}],total:1};
 }},WzosNavigation:{link:address=>({textContent:'Open in Navigation',href:address})}};
 const document={getElementById:get,createElement:element,addEventListener:(name,fn)=>events[name]=fn};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/team-modules.js','utf8'),{window,document,navigator,confirm:()=>true,URL,Blob,setTimeout});
 const flush=()=>new Promise(resolve=>setImmediate(resolve));
 const text=()=>{const flatten=n=>[n,...n.children.flatMap(c=>c.children?flatten(c):[c])];return flatten(get('team-content')).map(n=>n.textContent).join(' ');};
 return{events,calls,navigator,flush,text,setSession:s=>session=s,setHold:p=>hold=p};
}
test('Navigation deduplicates assigned jobs using dispatched destinations and limits Core to its orders',async()=>{
 const h=harness();h.events['wzos:view']({detail:'navigation'});await h.flush();
 assert.match(h.text(),/Frozen dispatched job/);assert.doesNotMatch(h.text(),/Private revised title/);
 assert.ok(h.calls.some(url=>url.includes('phase=upcoming')));
 h.setSession({id:'core',organization_id:'org2',edition:'core'});h.calls.length=0;h.events['wzos:session']();await h.flush();
 assert.deepEqual(h.calls,['/api/orders']);assert.doesNotMatch(h.text(),/Frozen dispatched job/);
});
test('Offline destinations do not cross organization switches and late responses cannot repopulate another session',async()=>{
 const h=harness();h.events['wzos:view']({detail:'navigation'});await h.flush();
 h.navigator.onLine=false;h.setSession({id:'other',organization_id:'org2',edition:'core'});h.events['wzos:session']();await h.flush();
 assert.doesNotMatch(h.text(),/Frozen dispatched job/);
 h.navigator.onLine=true;let release;h.setHold(new Promise(resolve=>release=resolve));h.events['wzos:view']({detail:'navigation'});
 h.setSession({id:'third',organization_id:'org3',edition:'core'});release({items:[{id:'private',title:'Late private destination',address:'Private'}]});await h.flush();
 assert.doesNotMatch(h.text(),/Late private destination/);
});
