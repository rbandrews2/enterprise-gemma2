const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function preview(){
 const elements=Object.fromEntries(['app','shell','stage','device-space','fit','dimensions','width','height','device','apply','rotate','reload'].map(id=>[id,{style:{},value:'',checked:true,clientWidth:1100,clientHeight:700,reportValidity(){return !!this.value&&Number(this.value)>=280&&Number(this.value)<=1600;}}]));
 let reloads=0;elements.app.contentWindow={location:{reload(){reloads++;}}};const events={};
 vm.runInNewContext(fs.readFileSync('scripts/mobile_preview/preview.js','utf8'),{document:{getElementById:id=>elements[id]},window:{addEventListener:(name,fn)=>events[name]=fn},Math,Number});
 return {elements,events,reloads:()=>reloads};
}
test('viewport changes preserve the app and use actual CSS dimensions',()=>{
 const p=preview(),e=p.elements;assert.equal(e.app.style.width,'390px');assert.equal(e.app.style.height,'844px');
 e.rotate.onclick();assert.equal(e.app.style.width,'844px');assert.equal(e.app.style.height,'390px');assert.match(e.dimensions.value,/Landscape/);
 e.device.value='360,800';e.device.onchange();assert.equal(e.app.style.width,'360px');assert.equal(e.app.style.height,'800px');assert.equal(p.reloads(),0);
 e.width.value='960';e.height.value='600';e.apply.onclick();assert.equal(e.device.value,'custom');assert.equal(e.app.style.width,'960px');
 e.fit.checked=false;e.fit.onchange();assert.equal(e.shell.style.transform,'scale(1)');e.reload.onclick();assert.equal(p.reloads(),1);
});
test('invalid custom size preserves the previous viewport',()=>{const {elements:e}=preview();e.width.value='';e.apply.onclick();assert.equal(e.app.style.width,'390px');});
