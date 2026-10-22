const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('received form opens a visible review before explicit print and closes without retaining the record',()=>{
 const calls=[];
 const node=(tag,text)=>({tag,textContent:text||'',children:[],attrs:{},handlers:{},append(...nodes){for(const n of nodes){n.parent=this;this.children.push(n);}},setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,fn){this.handlers[k]=fn;},showModal(){this.open=true;},close(){this.open=false;this.handlers.close?.();},remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);},focus(){this.focused=true;}});
 const body=node('body'),source=fs.readFileSync('services/workspace_preview/static/forms-hub.js','utf8');
 const context={node,button:text=>node('button',text),document:{body},buildDocument:(t,r)=>node('article',r.fields.description),printDocument:()=>calls.push('print'),downloadDocument:()=>calls.push('download')};
 vm.runInNewContext(source.slice(source.indexOf(' let receivedPreview=null;'),source.indexOf(" document.addEventListener('wzos:session',closeReceived)"))+';globalThis.openPreview=reviewReceived;globalThis.closePreview=closeReceived;',context);
 const record={form_type:'printable',template:{title:'Synthetic report'},fields:{description:'Reviewed synthetic report'}};
 context.openPreview(record);const dialog=body.children[0];assert.equal(dialog.open,true);assert.equal(dialog.attrs['aria-labelledby'],'received-preview-title');assert.deepEqual(calls,[]);
 assert.equal(dialog.children.at(-1).textContent,'Reviewed synthetic report');
 dialog.children[2].children[0].onclick();assert.deepEqual(calls,['print']);
 dialog.children[2].children[2].onclick();assert.equal(body.children.length,0);
 assert.throws(()=>context.openPreview({form_type:'legacy'}),/no printable preview/);
});
