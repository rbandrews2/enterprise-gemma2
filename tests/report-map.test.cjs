const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function setup(){
 const node=tag=>({tag,children:[],isConnected:true,append(...v){this.children.push(...v);},setAttribute(){}});
 const window={wzosClock:{api:async()=>({enabled:false})}};
 const document={createElement:node,addEventListener(){},removeEventListener(){}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/report-map.js','utf8'),{window,document,URLSearchParams,setTimeout,clearTimeout});
 const container=node('div');return{window,container};
}
test('Street View fallback stays available when embedded Maps is not configured',async()=>{
 const h=setup();h.window.WzosReportMap.mount(h.container,{version:1,job_geometry:{work_limits:[{latitude:36.8468,longitude:-76.2852}]}});
 const a=h.container.children.find(n=>n.tag==='a'),u=new URL(a.href);
 assert.equal(u.origin,'https://www.google.com');assert.equal(u.searchParams.get('api'),'1');
 assert.equal(u.searchParams.get('map_action'),'pano');assert.equal(u.searchParams.get('viewpoint'),'36.8468,-76.2852');
 assert.equal(a.target,'_blank');assert.equal(a.rel,'noopener noreferrer');assert.equal(a.hidden,false);
 await h.container.children.find(n=>n.textContent==='Load site imagery').onclick();
 assert.equal(a.hidden,false);assert.ok(h.container.children.some(n=>/not configured/.test(n.textContent)));
});
test('missing coordinates expose no misleading Street View destination',()=>{
 const h=setup();h.window.WzosReportMap.mount(h.container,{version:1});
 const a=h.container.children.find(n=>n.tag==='a');assert.equal(a.hidden,true);assert.equal(a.href,undefined);
 assert.equal(h.container.children.find(n=>n.textContent==='Load site imagery').disabled,true);
});
