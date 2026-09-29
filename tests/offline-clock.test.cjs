const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function harness(){
 const nodes=new Map(),events={},windowEvents={};
 const element=()=>({value:'',checked:false,children:[],handlers:{},append(...x){this.children.push(...x)},after(x){this.afterNode=x},replaceChildren(...x){this.children=x},setAttribute(){},addEventListener(k,v){this.handlers[k]=v},click(){this.onclick?.()}});
 const get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id)};
 let session={id:'member',organization_id:'org-a',role:'member'},calls=[];
 const navigator={onLine:true};
 const document={getElementById:get,createElement:element,addEventListener(k,v){events[k]=v},dispatchEvent(){}};
 const window={addEventListener(k,v){windowEvents[k]=v},wzosClock:{getSession:()=>session,getOrders:()=>[],async api(path,options){calls.push([path,options]);return path.includes('status')?{active:{id:'shift',version:1,work_seconds:100,status:'working',task:'work'},tasks:{work:'Work'}}:{items:[],limit:20,total:0}}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/timeclock.js','utf8'),{window,document,navigator,performance,Date,crypto:require('node:crypto').webcrypto,setInterval(){},setTimeout(){},URL,Blob,CustomEvent:class {}});
 return {get,navigator,events,windowEvents,calls,setSession(s){session=s}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('offline preserves last-known shift and cannot issue clock commands',async()=>{
 const h=harness();h.events['wzos:session']();await settle();assert.equal(h.get('clock-state').textContent,'CLOCKED IN');
 h.navigator.onLine=false;h.windowEvents.offline();assert.match(h.get('clock-state').textContent,/LAST KNOWN/);assert.equal(h.get('clock-out').disabled,true);
 await h.get('clock-out').handlers.click();assert.equal(h.calls.filter(c=>c[1]?.method==='POST').length,0);
 h.navigator.onLine=true;h.windowEvents.online();await settle();assert.equal(h.get('clock-state').textContent,'CLOCKED IN');
});
test('offline notes stay separate from attendance and clear on organization change',async()=>{
 const h=harness();h.events['wzos:session']();await settle();h.navigator.onLine=false;h.windowEvents.offline();
 const panel=h.get('clock-message').afterNode;const input=panel.children[2],add=panel.children[3],list=panel.children[5];
 input.value='Ended work during connection loss';add.onclick();assert.equal(list.children.length,1);assert.equal(h.calls.filter(c=>c[1]?.method==='POST').length,0);
 h.setSession({id:'member',organization_id:'org-b',role:'member'});h.events['wzos:session']();assert.equal(list.children.length,0);assert.match(h.get('clock-state').textContent,/NOT LOADED/);
});
