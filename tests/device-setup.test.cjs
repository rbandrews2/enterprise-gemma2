const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
function fixture(states={microphone:'prompt',geolocation:'prompt'},deny=false,edition='enterprise'){
 const events={},storage=new Map(),calls={microphone:0,location:0,stopped:0};
 const element=tag=>({tag,children:[],hidden:false,append(...n){this.children.push(...n);},prepend(n){this.children.unshift(n);},replaceChildren(...n){this.children=n;},setAttribute(){},scrollIntoView(){}});
 const main=element('main'),window={wzosClock:{getSession:()=>({id:'member',organization_id:'org',edition})},addEventListener:(k,f)=>events[k]=f};
 const document={getElementById:()=>main,createElement:element,addEventListener:(k,f)=>events[k]=f,dispatchEvent:e=>events[e.type]?.()};
 const navigator={permissions:{query:async({name})=>({state:states[name]})},mediaDevices:{getUserMedia:async()=>{calls.microphone++;if(deny)throw Error('Denied');states.microphone='granted';return {getTracks:()=>[{stop(){calls.stopped++;}}]};}},geolocation:{getCurrentPosition(resolve,reject){calls.location++;if(deny)return reject(Error('Denied'));states.geolocation='granted';resolve({coords:{latitude:1,longitude:2}});}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/device-setup.js','utf8'),{CustomEvent:class{constructor(type){this.type=type;}},window,document,navigator,localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)}});
 return {window,events,panel:main.children[0],calls,storage};
}
test('onboarding requests neither device automatically; one enable action checks both and stops mic',async()=>{
 const f=fixture();await f.events['wzos:session']();assert.deepEqual(f.calls,{microphone:0,location:0,stopped:0});
 await f.panel.children.find(n=>n.tag==='button').onclick();assert.deepEqual(f.calls,{microphone:1,location:1,stopped:1});
 assert.deepEqual([...f.storage.values()],['done']);await f.events['wzos:session']();assert.equal(f.panel.hidden,true);assert.equal(f.calls.microphone,1);
});
test('existing granted permissions show no setup and open no device',async()=>{
 const f=fixture({microphone:'granted',geolocation:'granted'});await f.events['wzos:session']();assert.equal(f.panel.hidden,true);assert.equal(f.calls.microphone+f.calls.location,0);
});
test('denial is recoverable without repeated automatic prompts or storing coordinates',async()=>{
 const f=fixture(undefined,true);await f.events['wzos:session']();await f.panel.children.find(n=>n.tag==='button').onclick();
 assert.equal(f.calls.microphone,1);assert.equal(f.calls.location,1);await f.events['wzos:session']();assert.equal(f.panel.hidden,true);
 f.window.wzosDeviceSetup.open();assert.equal(f.panel.hidden,false);assert.equal(JSON.stringify([...f.storage]).includes('latitude'),false);
});

test('Enterprise setup explains cloud transcription before requesting microphone access',async()=>{
 const f=fixture();await f.events['wzos:session']();
 assert.match(f.panel.children.map(n=>n.textContent||'').join(' '),/Google processes the audio for transcription and Atlas/);
 assert.equal(f.calls.microphone,0);
 const core=fixture(undefined,false,'core');await core.events['wzos:session']();
 assert.doesNotMatch(core.panel.children.map(n=>n.textContent||'').join(' '),/Google processes the audio/);
});
