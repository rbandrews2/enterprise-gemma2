const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm'),fs=require('node:fs');
const {weatherDistance,weatherProximity,weatherStale}=require('../services/workspace_preview/static/weather.js');
test('forecast remains valid through its actual period and stale cache stays stale',()=>{
 const time=Date.now(),data={status:'ready',basis:'forecast',source_time:new Date(time-3*3600000).toISOString(),valid_until:new Date(time+600000).toISOString()};
 assert.equal(weatherStale(data,time),false);assert.equal(weatherStale({...data,status:'stale'},time),true);assert.equal(weatherStale(data,time+700000),true);
});
const site={latitude:0,longitude:0,radius_meters:350};
const fix=(change={})=>({latitude:0,longitude:0,accuracy:10,timestamp:1000000,...change});
test('distance supports coincident points and known separation',()=>{
 assert.equal(weatherDistance(site,site),0);
 assert.ok(Math.abs(weatherDistance(site,{latitude:1,longitude:0})-111195)<2);
});
test('accuracy and hysteresis distinguish inside, outside, uncertain',()=>{
 assert.equal(weatherProximity(fix(),site,1000000),'inside');
 assert.equal(weatherProximity(fix({accuracy:400}),site,1000000),'uncertain');
 assert.equal(weatherProximity(fix({latitude:.004}),site,1000000),'outside');
 assert.equal(weatherProximity(fix({latitude:.0032}),site,1000000),'uncertain');
});
test('stale, future, missing and invalid fixes never confirm arrival',()=>{
 for(const change of [{timestamp:0},{timestamp:2000000},{accuracy:-1},{latitude:91},{latitude:NaN},{longitude:181}])assert.equal(weatherProximity(fix(change),site,1000000),'unavailable');
 assert.equal(weatherProximity(null,site,1000000),'unavailable');
});

function ui(permission='granted'){
 const events={},windowEvents={},timers=[],calls=[],cleared=[];let watcher,session={organization_id:'a',id:'m',role:'member'};
 class Element{
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.textContent='';}
  append(...items){for(const n of items){n.parent=this;this.children.push(n);}}
  replaceChildren(...items){this.children=[];this.append(...items);}
  after(n){n.parent=this.parent;this.parent?.children.push(n);}
  before(n){const i=this.parent.children.indexOf(this);n.parent=this.parent;this.parent.children.splice(i,0,n);}
  remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}
  setAttribute(k,v){this[k]=v;}
  querySelector(){return this.children.find(n=>n.dataset.weatherChooser)||null;}
 }
 const container=new Element('main'),root=new Element('section');container.append(root);const document={hidden:false,getElementById:()=>root,createElement:tag=>new Element(tag),addEventListener:(k,fn)=>events[k]=fn};
 const navigator={onLine:true,permissions:{query:async()=>({state:permission})},geolocation:{watchPosition(fn){watcher=fn;calls.push('watch');return 7;},clearWatch(id){cleared.push(id);}}};
 const pending=[];
 const window={wzosClock:{getSession:()=>session,getOrders:()=>[],api(path,options){calls.push(path);if(path==='/api/weather/current')return new Promise(resolve=>pending.push(resolve));return Promise.resolve({items:[]});}},addEventListener:(k,fn)=>windowEvents[k]=fn};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/weather.js','utf8'),{document,window,navigator,Date,Math,Set,Number,module:{exports:{}},setInterval:fn=>timers.push(fn)});
 const flat=(n=container)=>[n,...n.children.flatMap(flat)];
 return {document,events,pending,calls,cleared,flat,root,windowEvents,navigator,watch:(lat,lon)=>watcher({timestamp:Date.now(),coords:{latitude:lat,longitude:lon,accuracy:10}}),setSession(s){session=s;}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('location is opt-in, member settings hidden, watch clears on hide/logout',async()=>{
 const h=ui();await settle();assert.equal(h.calls.includes('watch'),true);
 assert.equal(h.flat().find(n=>n.children.some(c=>c.textContent==='Job weather & arrival settings')).hidden,true);
 await h.flat().find(n=>n.textContent==='Use location').onclick();assert.ok(h.calls.includes('watch'));
 h.document.hidden=true;h.events.visibilitychange();assert.ok(h.cleared.includes(7));
 h.document.hidden=false;h.events.visibilitychange();await settle();assert.equal(h.calls.filter(n=>n==='watch').length,3);
 const chooser=h.root.querySelector('[data-weather-chooser]');h.setSession(null);h.events['wzos:session']();assert.equal(h.root.hidden,true);assert.ok(h.cleared.length>=3);assert.equal(h.root.children.includes(chooser),false);
});
test('old location responses cannot overwrite a newer movement or another session',async()=>{
 const h=ui();await settle();await h.flat().find(n=>n.textContent==='Use location').onclick();h.watch(36.,-76.);h.watch(37.,-76.);
 h.pending.shift()({status:'ready',location:'Old location',alerts:[]});await settle();
 assert.equal(h.flat().some(n=>n.textContent==='Old location'),false);
 h.setSession({organization_id:'b',id:'m',role:'member'});h.events['wzos:session']();
 h.pending.shift()({status:'ready',location:'New location for former organization',alerts:[]});await settle();
 assert.equal(h.flat().some(n=>n.textContent==='New location for former organization'),false);
});

test('missing grants never start location or request permission on foreground refresh',async()=>{
 for(const state of ['prompt','denied']){const h=ui(state);await settle();await h.flat().find(n=>n.textContent==='Use location').onclick();h.events.visibilitychange();await settle();assert.equal(h.calls.includes('watch'),false);assert.equal(h.flat().some(n=>n.textContent==='Show job weather'),false);}
});
