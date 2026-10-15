const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function setup(role='admin',handler=()=>Promise.resolve({open_incidents:1,items:[],file_scan_required:false,coverage:'Synthetic coverage'})){
 class Node{constructor(tag){this.tagName=tag;this.children=[];this.textContent='';this.open=false;this.hidden=false;}
  append(...items){this.children.push(...items);}prepend(...items){this.children.unshift(...items);}replaceChildren(...items){this.children=items;}setAttribute(name,value){this[name]=value;}showModal(){this.open=true;}close(){this.open=false;}}
 const main=new Node('main'),body=new Node('body'),events={},calls=[];let current={role};
 const window={wzosClock:{getSession:()=>current,api:(...args)=>{calls.push(args);return handler(...args);}}};
 const document={body,hidden:false,getElementById:()=>main,createElement:tag=>new Node(tag),createTextNode:text=>({textContent:text,children:[]}),addEventListener:(name,fn)=>events[name]=fn};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/security.js','utf8'),{window,document,crypto:{randomUUID:()=> 'synthetic-id'},setInterval:()=>{},confirm:()=>true});
 const all=(n,tag)=>[...(n.tagName===tag?[n]:[]),...n.children.filter(x=>x&&typeof x==='object').flatMap(x=>all(x,tag))];
 return {window,main,body,events,calls,all,change:role=>{current={role};events['wzos:session']();}};
}
test('members never request admin incidents or open the security dialog',async()=>{
 const s=setup('member');s.events['wzos:session']();s.window.wzosSecurity.open();await flush();assert.equal(s.calls.length,0);assert.equal(s.body.children[0].open,false);assert.equal(s.main.children[0].hidden,true);
});
test('admin notifications persist and offer a working incident review entry',async()=>{
 const s=setup();s.events['wzos:session']();await flush();const banner=s.main.children[0];assert.equal(banner.hidden,false);assert.match(s.all(banner,'strong')[0].textContent,/1 unresolved incident/);s.all(banner,'button')[0].onclick();await flush();assert.equal(s.body.children[0].open,true);assert.ok(s.calls.some(([url])=>url==='/api/admin/security?offset=0&state=open'));
});
test('session changes clear private incident text and ignore stale responses',async()=>{
 let done;const s=setup('admin',()=>new Promise(resolve=>done=resolve));s.window.wzosSecurity.open();s.change('member');done({open_incidents:1,items:[{title:'PRIVATE OLD ORGANIZATION'}]});await flush();assert.equal(s.body.children[0].open,false);assert.equal(s.body.children[0].children.length,0);assert.equal(s.main.children[0].hidden,true);
});
test('untrusted incident titles and reasons remain text, with explicit review actions',async()=>{
 const payload={open_incidents:1,file_scan_required:false,coverage:'Synthetic coverage',items:[{id:'fixture',title:'<img src=x onerror=alert(1)>',severity:'medium',status:'open',target_type:'activity',target_id:'example',version:1,actions:[{action:'reported',occurred_at:new Date().toISOString(),reason:'<script>untrusted</script>'}]}]};
 const s=setup('admin',()=>Promise.resolve(payload));s.window.wzosSecurity.open();await flush();assert.equal(s.all(s.body,'img').length,0);assert.equal(s.all(s.body,'script').length,0);assert.ok(s.all(s.body,'h3').some(n=>n.textContent===payload.items[0].title));assert.ok(s.all(s.body,'select').length>=1);assert.equal(s.all(s.body,'textarea')[0].minLength,8);
});
test('missing security observations show unavailable rather than an all-clear claim',async()=>{
 const s=setup('admin',()=>Promise.reject(Error('Unavailable')));s.events['wzos:session']();await flush();assert.equal(s.main.children[0].hidden,false);assert.equal(s.all(s.main,'span')[0].textContent,'Atlas security status unavailable.');
});
test('containment cannot submit before the admin explicitly confirms scope',async()=>{
 const payload={open_incidents:1,coverage:'Synthetic coverage',items:[{id:'fixture',title:'Synthetic report',severity:'medium',status:'open',target_type:'activity',target_id:'fixture',version:1,actions:[]}]};
 const s=setup('admin',()=>Promise.resolve(payload));s.window.wzosSecurity.open();await flush();const form=s.all(s.body,'form')[0];await form.onsubmit({preventDefault(){}});assert.equal(s.calls.filter(([,options])=>options?.method==='POST').length,0);assert.equal(s.all(form,'input')[0].required,true);
});
