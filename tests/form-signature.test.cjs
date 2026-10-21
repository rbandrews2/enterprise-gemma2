const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function fixture(){
 const nodes=[];
 function node(tag,text,cls){
  const n={tag,textContent:text??'',children:[],value:'',checked:false,disabled:false,hidden:false,handlers:{},attrs:{},classList:{add(){}},
   append(...xs){this.children.push(...xs);},replaceChildren(...xs){this.children=[...xs];},get childNodes(){return this.children;},
   setAttribute(k,v){this.attrs[k]=v;},toggleAttribute(k,on){if(on)this.attrs[k]='';else delete this.attrs[k];},removeAttribute(k){delete this.attrs[k];},addEventListener(k,fn){this.handlers[k]=fn;},dispatchEvent(){this.changes=(this.changes||0)+1;},
   querySelector(tag){for(const c of this.children){if(c.tag===tag)return c;const found=c.querySelector?.(tag);if(found)return found;}},
   getBoundingClientRect(){return {left:10,top:20,width:600,height:180};},setPointerCapture(id){this.captured=id;},hasPointerCapture(id){return this.captured===id;},releasePointerCapture(){this.captured=null;},focus(){}};
  nodes.push(n);return n;
 }
 const source=fs.readFileSync('services/workspace_preview/static/forms-hub.js','utf8');
 const context={node,button:label=>node('button',label),labelled:(label,input)=>{const n=node('label',label);n.append(input);return n;},
  document:{createElementNS:(ns,tag)=>Object.assign(node(tag),{namespaceURI:ns})},Event:class{},structuredClone};
 vm.runInNewContext(source.slice(source.indexOf(' function signatureImage('),source.indexOf(' async function openForm('))+';globalThis.pad=signaturePad();globalThis.image=signatureImage;',context);
 vm.runInNewContext(source.slice(source.indexOf(' function buildDocument('),source.indexOf(' function printDocument('))+';globalThis.documentView=buildDocument;',Object.assign(context,{today:()=> '2026-10-20'}));
 const pad=context.pad,svg=nodes.find(n=>n.attrs['aria-label']==='Signature drawing area'),name=nodes.find(n=>n.tag==='input'),typed=nodes.find(n=>n.type==='checkbox');
 const event=(x,y)=>({clientX:x,clientY:y,pointerId:1,button:0,preventDefault(){}});
 return {pad,svg,name,typed,nodes,event,image:context.image,documentView:context.documentView};
}
test('touch/pen/mouse strokes retain normalized points, require name and clear cleanly',()=>{
 const f=fixture();assert.equal(f.pad.read(),null);
 f.svg.handlers.pointerdown(f.event(70,56));f.svg.handlers.pointermove(f.event(370,164));
 assert.throws(()=>f.pad.read(),/Finish signing/);f.svg.handlers.pointerup(f.event(370,164));
 assert.throws(()=>f.pad.read(),/signer name/);f.name.value='Synthetic Worker';
 const saved=JSON.parse(JSON.stringify(f.pad.read()));assert.equal(saved.mode,'drawn');assert.deepEqual(saved.strokes,[[{x:.1,y:.2},{x:.6,y:.8}]]);
 f.nodes.find(n=>n.tag==='button'&&n.textContent==='Clear signature').onclick();assert.equal(f.pad.read(),null);assert.equal(f.svg.children.length,0);assert.ok(f.pad.element.changes>=2);
});
test('cancelled pointers discard partial ink and disabled forms reject drawing',()=>{
 const f=fixture();f.svg.handlers.pointerdown(f.event(100,100));f.svg.handlers.pointercancel(f.event(110,110));assert.equal(f.pad.read(),null);
 f.name.disabled=true;f.svg.handlers.pointerdown(f.event(100,100));assert.equal(f.pad.read(),null);
});
test('typed alternative is explicit, and print renderer treats names as plain text',()=>{
 const f=fixture();f.typed.checked=true;f.typed.onchange();assert.ok('hidden' in f.svg.attrs);f.name.value='<img onerror=bad>';
 const signature=f.pad.read();assert.equal(signature.mode,'typed');assert.equal(signature.strokes.length,0);
 const result=f.image(signature);assert.equal(result.children[1].textContent,'<img onerror=bad>');assert.equal(result.querySelector('img'),undefined);
});
test('print/download document preserves signature geometry and blank forms have a signing line',()=>{
 const f=fixture(),template={title:'Synthetic form',revision:1,print_notice:'Test only',sections:[]};
 const signature={mode:'drawn',signer_name:'Synthetic Signer',strokes:[[{x:.1,y:.2},{x:.6,y:.8}]]};
 const doc=f.documentView(template,{fields:{},signature});
 const polyline=doc.querySelector('polyline');assert.equal(polyline.attrs.points,'60,36 360,144');assert.equal(polyline.attrs.stroke,'#111');
 assert.equal(f.documentView(template,null).querySelector('svg'),undefined);
});
