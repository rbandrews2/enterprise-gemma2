const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function setup(){
 class Node{constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.textContent='';this.hidden=false;this.value='';this.checked=false;this.paused=0;this.loaded=0;}
  append(...items){for(const item of items){this.children.push(item);if(typeof item==='object')item.parent=this;}}
  replaceChildren(...items){this.children=[];this.append(...items);}
  remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}
  removeAttribute(name){delete this[name];}pause(){this.paused++;}load(){this.loaded++;}}
 const events={},window={};vm.runInNewContext(fs.readFileSync('services/workspace_preview/static/training-media.js','utf8'),{window,URL,document:{createElement:tag=>new Node(tag),addEventListener:(name,fn)=>events[name]=fn}});
 const all=(n,tag)=>[...(n.tagName===tag?[n]:[]),...n.children.filter(x=>typeof x==='object').flatMap(x=>all(x,tag))];return {media:window.WzosTrainingMedia,events,all};
}
const clip={title:'Crew video',url:'https://youtu.be/M7lc1UVf-VE',rights_confirmed:true,rights_note:'Organization licensed video'};
test('known watch/share/embed URLs become fixed trusted player URLs, others remain links',()=>{
 const {media}=setup();for(const url of [clip.url,'https://www.youtube.com/watch?v=M7lc1UVf-VE','https://www.youtube.com/embed/M7lc1UVf-VE'])assert.equal(media.descriptor(url).url,'https://www.youtube-nocookie.com/embed/M7lc1UVf-VE?playsinline=1&rel=0');
 assert.equal(media.descriptor('https://vimeo.com/123456789/abc123').url,'https://player.vimeo.com/video/123456789?h=abc123&dnt=1');
 assert.equal(media.descriptor('https://media.example.org/course.mp4?signature=test').kind,'video');assert.equal(media.descriptor('https://docs.example.org/training.pdf').kind,'link');assert.equal(media.descriptor('https://youtube.com.evil.example/watch?v=M7lc1UVf-VE').kind,'link');
});
test('unsafe schemes, embedded credentials and local network literals are not loaded',()=>{
 const {media}=setup();for(const value of ['javascript:alert(1)','http://example.org/a.mp4','https://user:password@example.org/a.mp4','https://localhost/a.mp4','https://127.0.0.1/a.mp4','https://[::1]/a.mp4','https://machine.local/a.mp4','https://example.org:8443/a.mp4'])assert.equal(media.descriptor(value),null,value);
});
test('player is click-to-load, supports closing, and unloads when session/view changes',()=>{
 const {media,events,all}=setup(),card=media.render(clip),buttons=all(card,'BUTTON');assert.equal(all(card,'IFRAME').length,0);buttons[0].onclick();const frame=all(card,'IFRAME')[0];assert.match(frame.src,/youtube-nocookie/);assert.equal(frame.allowFullscreen,true);assert.equal(frame.src.includes('autoplay=1'),false);
 buttons[1].onclick();assert.equal(all(card,'IFRAME').length,0);buttons[0].onclick();events['wzos:session']();assert.equal(all(card,'IFRAME').length,0);buttons[0].onclick();events['wzos:view']();assert.equal(all(card,'IFRAME').length,0);
});
test('native player stops and removes its source rather than continuing hidden playback',()=>{
 const {media,all}=setup(),card=media.render({...clip,url:'https://media.example.org/course.webm'});all(card,'BUTTON')[0].onclick();const video=all(card,'VIDEO')[0];assert.equal(video.controls,true);assert.equal(video.playsInline,true);assert.equal(video.preload,'none');media.stopAll();assert.equal(video.src,undefined);assert.equal(video.paused,1);assert.equal(video.loaded,1);assert.equal(all(card,'VIDEO').length,0);
});
test('link controls start collapsed, preserve every existing link and support replacement/removal',()=>{
 const {media,all}=setup();let edits=0;const e=media.editor([clip,{...clip,title:'Second video',url:'https://example.org/two.mp4'}],()=>edits++);assert.equal(!!e.element.open,false);assert.equal(e.value().length,2);const inputs=all(e.element,'INPUT');inputs[1].value='https://example.org/replacement.mp4';e.element.oninput();assert.equal(e.value()[0].url,'https://example.org/replacement.mp4');assert.equal(e.value()[1].title,'Second video');all(e.element,'BUTTON').find(b=>b.textContent==='Remove link').onclick();assert.equal(e.value().length,1);assert.equal(e.value()[0].title,'Second video');assert.equal(edits,2);
});
test('editor bounds links at ten and never treats titles as HTML',()=>{
 const {media,all}=setup(),e=media.editor(Array.from({length:10},()=>clip),()=>{}),add=all(e.element,'BUTTON').find(b=>b.textContent==='Add video link');assert.equal(add.disabled,true);add.onclick();assert.equal(e.value().length,10);const card=media.render({...clip,title:'<img src=x onerror=alert(1)>'});assert.equal(all(card,'IMG').length,0);assert.equal(all(card,'H4')[0].textContent,'<img src=x onerror=alert(1)>');
});

test('add-video editor exposes a blank URL immediately without marking unchanged data dirty',()=>{
 const {media,all}=setup();let edits=0;const e=media.editor([],()=>edits++,{open:true,emptyRow:true});assert.equal(e.element.open,true);const url=all(e.element,'INPUT').find(n=>n.type==='url');assert.ok(url);assert.equal(url.value,'');assert.deepEqual(Array.from(e.value()),[]);assert.equal(edits,0);url.value='https://example.org/video.mp4';e.element.oninput();assert.equal(edits,1);assert.equal(e.value().length,1);
});
