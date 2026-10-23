const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function setup(){const nodes={'app-boot':{hidden:false},'app-boot-message':{textContent:''},'app-boot-retry':{hidden:true}},classes=new Set(['app-starting']),events={};let timeout,reloads=0;const window={addEventListener:(n,f)=>events[n]=f};vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/startup.js','utf8'),{window,document:{getElementById:id=>nodes[id],body:{classList:{remove:n=>classes.delete(n)}}},navigator:{onLine:true},setTimeout:f=>(timeout=f,1),clearTimeout(){},location:{reload:()=>reloads++}});return {nodes,classes,events,window,slow:()=>timeout(),reloads:()=>reloads};}
test('launch is released immediately on session readiness and late errors do not replace workspace',()=>{const h=setup();h.window.wzosStartup.ready();assert.equal(h.nodes['app-boot'].hidden,true);assert.equal(h.classes.has('app-starting'),false);h.events.error();assert.equal(h.nodes['app-boot'].hidden,true);});
test('sign-in owns its dialog while startup stays hidden; slow connection never reloads automatically',()=>{const h=setup();h.window.wzosStartup.signingIn();h.slow();assert.equal(h.nodes['app-boot'].hidden,true);assert.equal(h.reloads(),0);});
test('launch failure offers one explicit retry without revealing a wrong workspace',()=>{const h=setup();h.window.wzosStartup.fail();assert.equal(h.nodes['app-boot-retry'].hidden,false);assert.equal(h.classes.has('app-starting'),true);assert.equal(h.reloads(),0);h.nodes['app-boot-retry'].onclick();assert.equal(h.reloads(),1);});

test('retry reconnects in place and ignores duplicate clicks while pending',async()=>{
 const h=setup();let release,calls=0;h.window.wzosStartup.setRetry(()=>{calls++;return new Promise(resolve=>release=resolve);});
 const first=h.nodes['app-boot-retry'].onclick();await h.nodes['app-boot-retry'].onclick();
 assert.equal(calls,1);assert.equal(h.reloads(),0);assert.equal(h.nodes['app-boot-retry'].disabled,true);
 release();await first;assert.equal(h.nodes['app-boot-retry'].disabled,false);
});
test('request deadline releases a stalled body even if transport ignores abort',async()=>{
 let expire,signal;const nodes={'app-boot':{},'app-boot-retry':{}},window={addEventListener(){}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/startup.js','utf8'),{window,AbortController,document:{getElementById:id=>nodes[id]},navigator:{},setTimeout:f=>(expire=f,1),clearTimeout(){}});
 const pending=window.wzosStartup.request(s=>{signal=s;return new Promise(()=>{});});
 await Promise.resolve();expire();await assert.rejects(pending,/Connection took too long/);assert.equal(signal.aborted,true);
});
