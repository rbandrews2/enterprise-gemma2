const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
function fixture(standalone=false,related){
 const events={},widgets=[];
 const element=tag=>({tag,children:[],append(...n){this.children.push(...n);},setAttribute(){}});
 const window={matchMedia:()=>({matches:standalone}),addEventListener:(name,fn)=>events[name]=fn};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/install.js','utf8'),{window,navigator:{getInstalledRelatedApps:related},document:{createElement:element}});
 const root=element('div');window.wzosInstall.mount(root);
 return {events,root,area:root.children[0],button:root.children[0].children[0],note:root.children[0].children[1]};
}
test('installation fallback explains browser option and keeps browser access available',async()=>{
 const f=fixture();await f.button.onclick();assert.match(f.note.textContent,/Add to Home Screen/);assert.match(f.note.textContent,/optional/);
});
test('accepted prompt does not falsely claim completed installation',async()=>{
 const f=fixture();let prompted=0,prevented=0;
 f.events.beforeinstallprompt({preventDefault(){prevented++;},async prompt(){prompted++;},userChoice:Promise.resolve({outcome:'accepted'})});
 await f.button.onclick();assert.equal(prompted,1);assert.equal(prevented,1);assert.match(f.note.textContent,/requested/);assert.equal(f.button.hidden,false);
 f.events.appinstalled();assert.equal(f.button.hidden,true);assert.equal(f.area.hidden,true);assert.match(f.note.textContent,/installed on this device/);
});

test('related-app detection hides only this installed WZOS app, handles rejection and an installation race',async()=>{
 const tick=()=>new Promise(r=>setImmediate(r));
 const own=fixture(false,async()=>[{platform:'webapp',url:'https://app.workzoneos.org/manifest.webmanifest'}]);await tick();assert.equal(own.area.hidden,true);
 const unrelated=fixture(false,async()=>[{platform:'webapp',url:'https://other.example/manifest.webmanifest'}]);await tick();assert.equal(unrelated.area.hidden,false);
 const denied=fixture(false,async()=>{throw Error('denied');});await tick();assert.equal(denied.area.hidden,false);
 let complete;const race=fixture(false,()=>new Promise(r=>complete=r));race.events.appinstalled();complete([]);await tick();assert.equal(race.area.hidden,true);
});
test('already standalone hides install action and rejected prompt remains usable',async()=>{
 assert.equal(fixture(true).button.hidden,true);
 const f=fixture();f.events.beforeinstallprompt({preventDefault(){},async prompt(){throw Error('private');}});
 await f.button.onclick();assert.equal(f.button.disabled,false);assert.doesNotMatch(f.note.textContent,/private/);
});
test('manifest has install icons and launches workspace without an activation in the URL',()=>{
 const m=JSON.parse(fs.readFileSync('services/workspace_preview/static/manifest.webmanifest','utf8'));
 assert.equal(m.start_url,'/');assert.equal(m.scope,'/');assert.equal(m.display,'standalone');
 assert.deepEqual(m.icons.map(i=>i.sizes),['192x192','512x512','192x192','512x512']);
 assert.equal(m.id,'/');assert.deepEqual(m.icons.map(i=>i.purpose),['any','any','maskable','maskable']);
 for(const icon of m.icons)assert.ok(fs.existsSync('services/workspace_preview/static'+icon.src.split('?')[0]));
});
