const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function setup(){const window={};vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/navigation-link.js','utf8'),{window,document:{createElement:()=>({})}});return window.WzosNavigation;}
test('navigation uses documented directions parameters and encodes addresses safely',()=>{
 const nav=setup(),a=nav.link('  12 Main St & East, Norfolk VA  '),u=new URL(a.href);
 assert.equal(u.origin,'https://www.google.com');assert.equal(u.pathname,'/maps/dir/');
 assert.equal(u.searchParams.get('destination'),'12 Main St & East, Norfolk VA');
 assert.equal(u.searchParams.get('api'),'1');assert.equal(u.searchParams.get('dir_action'),'navigate');
 assert.equal(a.target,'_blank');assert.equal(a.rel,'noopener noreferrer');
});
test('coordinate destinations are preserved; unusable destinations produce no link',()=>{
 const nav=setup();assert.equal(new URL(nav.url('36.85,-76.28')).searchParams.get('destination'),'36.85,-76.28');
 for(const value of ['', '   ',null,undefined,{},'x'.repeat(501),'界'.repeat(500),'\ud800'])assert.equal(nav.link(value),null);
 assert.equal(new URL(nav.url('javascript:alert(1)')).origin,'https://www.google.com');
});
