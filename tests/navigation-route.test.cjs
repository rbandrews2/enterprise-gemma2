const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function harness({enabled=true,mapFailure=true,manual=false}={}){
 const events={},windowEvents={},calls=[],gps=[],maps=[];let session={id:'member',organization_id:'org1',edition:'enterprise'},hold=null;
 function element(tag){return{tag,textContent:'',value:'',children:[],isConnected:true,append(...nodes){this.children.push(...nodes);},insertBefore(node,before){this.children.splice(this.children.indexOf(before),0,node);},replaceChildren(...nodes){this.children=nodes;},setAttribute(){},removeAttribute(name){delete this[name];},remove(){this.isConnected=false;}};}
 const document={createElement:element,addEventListener:(name,fn)=>events[name]=fn};
 const navigator={onLine:true,geolocation:{getCurrentPosition:(...args)=>gps.push(args)}};
 const response={status:'ready',distance_meters:2400,duration_seconds:300,calculated_at:new Date().toISOString(),destination:'Frozen site',destination_basis:'dispatched_snapshot',directions:[{instruction:'Head east <script>'}],encoded_polyline:'??'};
 const window={addEventListener:(name,fn)=>windowEvents[name]=fn,wzosClock:{getSession:()=>session,api:async(path,options)=>{
  calls.push({path,options});if(path.endsWith('/config'))return{routes_enabled:enabled};return hold||response;
 }},WzosReportMap:{ready:async()=>{if(mapFailure)throw Error('Maps unavailable');}}};
 const google={maps:{SymbolPath:{CIRCLE:0},importLibrary:async()=>({encoding:{decodePath:()=>[{lat:()=>36.8,lng:()=>-76.2},{lat:()=>36.9,lng:()=>-76.3}]}}),Map:class{constructor(node,options){this.record={node,options,fits:0};maps.push(this.record);}fitBounds(){this.record.fits++;}},Polyline:class{constructor(options){maps.push(options);}},LatLngBounds:class{extend(){}}}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/navigation.js','utf8'),{window,document,navigator,AbortController,Date,google});
 const card=element('article');window.WzosNavigationRoute.attach(card,manual?{manual:true,title:'your destination'}:{id:'order',assignment_id:'assignment',title:'Assigned job',address:'Saved destination'});
 const flatten=n=>[n,...n.children.flatMap(flatten)],find=text=>flatten(card).find(n=>n.textContent===text),text=()=>flatten(card).map(n=>n.textContent).join(' ');
 return{card,calls,gps,maps,events,windowEvents,navigator,find,text,response,overview:()=>window.WzosNavigationRoute.overview(card),open:()=>card.children[0].onclick(),submit:()=>find('Calculate route')&&flatten(card).find(n=>n.tag==='form').onsubmit({preventDefault(){}}),origin:()=>flatten(card).find(n=>n.tag==='input'),destination:()=>flatten(card).filter(n=>n.tag==='input')[1],setSession:s=>session=s,setHold:p=>hold=p};
}

test('Normal navigation accepts both addresses without a saved job and requires a destination',async()=>{
 const h=harness({manual:true});await h.open();h.origin().value='Norfolk station';
 await h.submit();assert.equal(h.calls.length,1);assert.match(h.text(),/Enter a destination/);
 assert.equal(h.destination().readOnly,false);h.destination().value='Richmond, VA';await h.submit();
 const body=JSON.parse(h.calls[1].options.body);assert.equal(body.destination,'Richmond, VA');assert.equal(body.origin.address,'Norfolk station');assert.equal(body.order_id,undefined);assert.equal(body.assignment_id,undefined);
});

test('Job navigation displays its destination without accepting an override',async()=>{
 const h=harness();await h.open();assert.equal(h.destination().value,'Saved destination');assert.equal(h.destination().readOnly,true);
});

test('Active guidance uses Google Maps from the device location, without sending GPS or origin',async()=>{
 const h=harness({manual:true,enabled:false});await h.open();const link=h.find('Start turn-by-turn in Google Maps');
 assert.equal(link.hidden,true);assert.equal(link.href,undefined);
 h.destination().value='Main & First, Norfolk VA';h.destination().oninput();
 const url=new URL(link.href);assert.equal(url.origin,'https://www.google.com');assert.equal(url.searchParams.get('destination'),'Main & First, Norfolk VA');
 assert.equal(url.searchParams.get('dir_action'),'navigate');assert.equal(url.searchParams.has('origin'),false);
 assert.equal(link.target,'_blank');assert.equal(link.rel,'noopener noreferrer');assert.equal(h.gps.length,0);assert.equal(h.calls.length,1);
 h.destination().value='';h.destination().oninput();assert.equal(link.hidden,true);assert.equal(link.href,undefined);
});
test('No automatic location or route calls; manual calculation uses assignment, retains directions on map failure',async()=>{
 const h=harness();await h.open();assert.equal(h.gps.length,0);assert.equal(h.calls.length,1);
 h.origin().value='Starting address';await h.submit();
 assert.equal(h.calls.length,2);assert.equal(h.calls[1].options.method,'POST');
 const body=JSON.parse(h.calls[1].options.body);assert.equal(body.assignment_id,'assignment');assert.equal(body.order_id,undefined);
 assert.equal(body.origin.address,'Starting address');assert.match(h.text(),/Head east <script>/);assert.match(h.text(),/Map display unavailable/);
});
test('Geolocation requires a click and denial allows manual address',async()=>{
 const h=harness();await h.open();h.find('Use my current location').onclick();assert.equal(h.gps.length,1);
 assert.equal(h.calls.length,1);h.gps[0][1]();assert.match(h.text(),/permission was declined/);
 h.origin().value='Manual origin';await h.submit();assert.equal(h.calls.length,2);
});
test('Configured map draws the returned route inside WZOS without extra route requests',async()=>{
 const h=harness({mapFailure:false});await h.open();h.origin().value='Public starting site';await h.submit();
 assert.equal(h.maps.length,2);assert.equal(h.maps[0].node.hidden,false);assert.equal(h.maps[1].path.length,2);assert.equal(h.maps[1].icons[0].offset,'0%');assert.equal(h.maps[1].icons[1].offset,'100%');assert.equal(h.maps[0].fits,1);h.find('Show full route').onclick();assert.equal(h.maps[0].fits,2);
 assert.equal(h.calls.filter(c=>c.path.endsWith('/route')).length,1);assert.doesNotMatch(h.text(),/Map display unavailable/);
});
test('Disabled routes cannot issue a billable request',async()=>{
 const h=harness({enabled:false});await h.open();h.origin().value='Norfolk';await h.submit();
 assert.equal(h.calls.length,1);assert.match(h.text(),/not configured/);assert.equal(h.find('Calculate route').disabled,true);
});
test('Organization changes abort pending requests and discard late route content',async()=>{
 const h=harness();await h.open();let release;h.setHold(new Promise(resolve=>release=resolve));h.origin().value='Origin';const task=h.submit();
 const panel=h.card.children[1],signal=h.calls[1].options.signal;h.setSession({id:'other',organization_id:'org2',edition:'core'});h.events['wzos:session']();
 assert.equal(signal.aborted,true);assert.equal(panel.isConnected,false);release(h.response);await task;
 assert.doesNotMatch(h.text(),/Frozen site/);assert.doesNotMatch(h.text(),/Head east/);
});
test('View change and offline clear route panels',async()=>{
 for(const event of ['view','offline']){const h=harness();await h.open();const panel=h.card.children[1];
  if(event==='view')h.events['wzos:view']();else h.windowEvents.offline();assert.equal(panel.isConnected,false);
 }
});

test('Navigation overview is interactive without requesting GPS or calculating a route',async()=>{
 const h=harness({mapFailure:false});await h.overview();assert.equal(h.maps.length,1);
 assert.equal(h.maps[0].node.hidden,false);assert.equal(h.maps[0].options.fullscreenControl,true);
 assert.ok(h.find('Map'));assert.doesNotMatch(h.text(),/Virginia overview/);assert.equal(h.gps.length,0);assert.equal(h.calls.length,0);
});
test('Offline navigation overview reports unavailable without loading Google',async()=>{
 const h=harness({mapFailure:false});h.navigator.onLine=false;await h.overview();
 assert.equal(h.maps.length,0);assert.match(h.text(),/Map unavailable offline/);
});
test('Overview map failure is explicit and does not remove destinations',async()=>{
 const h=harness();await h.overview();assert.match(h.text(),/Map unavailable: Maps unavailable/);
 assert.ok(h.find('Get directions'));assert.equal(h.maps.length,0);
});
