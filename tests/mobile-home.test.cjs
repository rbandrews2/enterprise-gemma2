const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function fixture({mobile=true,user={id:'worker',organization_id:'org-a',role:'member',edition:'core',can_prepare_atlas:false},allowed=true}={}){
 const events={},nodes={},calls=[],scrolls=[];let current=user,accept=allowed,change;
 const classes=new Set();
 const element=()=>({hidden:false,dataset:{},children:[],textContent:'',append(n){this.children.push(n);},prepend(n){this.children.unshift(n);},addEventListener(name,fn){this[name]=fn;}});
 for(const name of ['side','bar','menu','title','brand','label','report-nav','assignments-nav'])nodes[name]=element();
 nodes.side.querySelector=s=>s==='.brand'?nodes.brand:s==='.nav-label'?nodes.label:null;
 const document={body:{classList:{contains:n=>classes.has(n),remove:n=>classes.delete(n)}},createElement:element,
  getElementById:id=>nodes[id],querySelector:s=>({'.sidebar':nodes.side,'.topbar':nodes.bar,'nav[aria-label="Workspace navigation"]':nodes.menu,'.breadcrumb + strong':nodes.title})[s],addEventListener:(name,fn)=>events[name]=fn};
 const media={matches:mobile,addEventListener:(name,fn)=>change=fn};
 const window={matchMedia:()=>media,wzosClock:{getSession:()=>current},scrollTo:options=>scrolls.push(options),showWzosView(view){calls.push(view);if(!accept)return false;if(view==='home')classes.add('mobile-home-active');else classes.delete('mobile-home-active');events['wzos:view']?.({detail:view});return true;}};
 vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/mobile-home.js','utf8'),{window,document});
 return {nodes,calls,scrolls,classes,events,home:nodes.bar.children[0],admin:nodes.menu.children[0],setUser(user){current=user;events['wzos:session']();},setAllowed(value){accept=value;},resize(value){media.matches=value;change();}};
}
test('Core members start at Home with edition restrictions and no admin controls',()=>{
 const f=fixture();assert.deepEqual(f.calls,['home']);assert.equal(f.nodes.title.textContent,'Home');assert.equal(f.nodes.label.textContent,'Home');assert.equal(f.admin.hidden,true);assert.equal(f.nodes['report-nav'].dataset.mobileUnavailable,'true');assert.equal(f.nodes['assignments-nav'].dataset.mobileUnavailable,'true');
});
test('Enterprise admins use the same Home and retain authorized organization tools',()=>{
 const f=fixture();f.setUser({id:'admin',organization_id:'other-org',role:'admin',edition:'enterprise',can_prepare_atlas:true});
 assert.equal(f.admin.hidden,false);assert.equal(f.nodes['report-nav'].dataset.mobileUnavailable,'false');assert.equal(f.nodes['assignments-nav'].dataset.mobileUnavailable,'false');
 f.admin.onclick();assert.equal(f.calls.at(-1),'dashboard');assert.equal(f.nodes.title.textContent,'Organization management');f.home.onclick();assert.equal(f.calls.at(-1),'home');
 f.setUser(null);assert.equal(f.admin.hidden,true);assert.equal(f.home.hidden,true);assert.equal(f.classes.has('mobile-home-active'),false);
});
test('Home respects existing unsaved-work guards and the logo uses the same guarded return',()=>{
 const f=fixture({allowed:false});assert.equal(f.scrolls.length,0);f.home.onclick();assert.equal(f.scrolls.length,0);assert.equal(f.classes.has('mobile-home-active'),false);
 f.setAllowed(true);let prevented=false;f.nodes.brand.click({preventDefault(){prevented=true;}});assert.equal(prevented,true);assert.equal(f.classes.has('mobile-home-active'),true);assert.equal(f.scrolls.length,1);
});
test('desktop keeps its existing start view and a width change does not discard a module draft',()=>{
 const f=fixture({mobile:false});assert.deepEqual(f.calls,[]);assert.equal(f.nodes.label.textContent,'WORKSPACE');f.events['wzos:view']({detail:'forms'});f.resize(true);assert.deepEqual(f.calls,[]);
 f.home.onclick();assert.equal(f.calls.at(-1),'home');f.resize(false);assert.equal(f.calls.at(-1),'orders');
});
test('desktop admin dashboard transitions to mobile Home, then returns to dashboard',()=>{
 const f=fixture({mobile:false,user:{id:'a',role:'admin',edition:'enterprise',can_prepare_atlas:true}});f.events['wzos:view']({detail:'dashboard'});f.resize(true);assert.equal(f.calls.at(-1),'home');f.resize(false);assert.equal(f.calls.at(-1),'dashboard');
});
