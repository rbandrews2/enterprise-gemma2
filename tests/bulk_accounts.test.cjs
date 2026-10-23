const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
class Element{
 constructor(tag,text=''){this.tag=tag;this.textContent=text;this.children=[];this.events={};this.value='';}
 append(...nodes){this.children.push(...nodes);} replaceChildren(...nodes){this.children=nodes;}
 setAttribute(){} addEventListener(name,fn){this.events[name]=fn;} showModal(){} remove(){} close(){this.events.close?.();}
 all(tag){return this.children.flatMap(c=>[...(c.tag===tag?[c]:[]),...c.all(tag)]);}
}
function fixture(api){
 const document={body:new Element('body'),events:{},createElement:t=>new Element(t),addEventListener(k,f){this.events[k]=f;},removeEventListener(k){delete this.events[k];}};
 const sandbox={window:{addEventListener(){},removeEventListener(){}},document,crypto:{randomUUID:()=> 'stable-batch'},Map,Blob,URL,setTimeout,Uint8Array,btoa};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/bulk-accounts.js','utf8'),sandbox);
 const dialog=sandbox.window.wzosBulkAccounts.open(api);
 const button=text=>dialog.all('button').find(b=>b.textContent===text);
 return {document,dialog,button,paste:dialog.all('textarea')[0],consent:dialog.all('input').find(i=>i.type==='checkbox'),review:button('Review accounts'),confirm:button('Create reviewed accounts')};
}
const row=i=>({index:i,name:'Synthetic Employee',email:`test${i}@example.test`,username:`test${i}`,role:'member',errors:[],state:'new'});
const review=()=>({items:[row(0),row(1)],ignored_columns:[],license:{seats_available:24},seats_needed:2,capacity_ok:true,valid:true});
test('spreadsheet paste requires review and consent before creating; partial retry skips completed rows',async()=>{
 const calls=[];let attempt=0;
 const ui=fixture(async(path,body)=>{calls.push({path,body});if(path.endsWith('/review'))return review();attempt++;return {items:attempt===1?[{index:0,created:true},{index:1,created:false,error:'Retry setup'}]:[{index:1,created:true}]};});
 ui.paste.value='name\temail\tusername\tpassword\trole';
 await ui.confirm.onclick();assert.equal(calls.length,0);
 await ui.review.onclick();assert.equal(calls[0].body.format,'tsv');assert.equal(ui.confirm.disabled,true);
 ui.consent.checked=true;ui.consent.onchange();await ui.confirm.onclick();
 assert.equal(ui.confirm.textContent,'Retry unfinished accounts');await ui.confirm.onclick();
 assert.deepEqual(Array.from(calls[2].body.rows),[1]);assert.equal(calls[1].body.batch_id,calls[2].body.batch_id);
 assert.equal(ui.paste.value,'');assert.equal(ui.confirm.disabled,true);assert.equal(ui.confirm.textContent,'Accounts created');
});
test('uncertain network outcome retries the same batch and rows',async()=>{
 const bodies=[];let fail=true;
 const ui=fixture(async(path,body)=>{if(path.endsWith('/review'))return review();bodies.push(body);if(fail){fail=false;throw Error('Connection interrupted');}return {items:[{index:0,created:true},{index:1,created:true}]};});
 ui.paste.value='synthetic';await ui.review.onclick();ui.consent.checked=true;await ui.confirm.onclick();await ui.confirm.onclick();
 assert.equal(bodies.length,2);assert.equal(bodies[0].batch_id,bodies[1].batch_id);assert.deepEqual(bodies[0].rows,bodies[1].rows);
});
test('failed review cannot create and editing invalidates consent',async()=>{
 let create=0;
 const ui=fixture(async path=>{if(!path.endsWith('/review'))create++;return {...review(),valid:false,capacity_ok:false};});
 ui.paste.value='synthetic';await ui.review.onclick();ui.consent.checked=true;await ui.confirm.onclick();assert.equal(create,0);
 ui.paste.oninput();assert.equal(ui.consent.checked,false);assert.equal(ui.confirm.disabled,true);
});
test('session change clears credentials and stops the next chunk',async()=>{
 let ui,calls=0;
 ui=fixture(async path=>{if(path.endsWith('/review'))return {...review(),items:Array.from({length:6},(_,i)=>row(i))};calls++;ui.document.events['wzos:session']();return {items:[]};});
 ui.paste.value='private initial password';await ui.review.onclick();ui.consent.checked=true;await ui.confirm.onclick();assert.equal(calls,1);assert.equal(ui.paste.value,'');
});
