"use strict";
// No provider SDK, API key or media request until the learner opens a player.
(() => {
 const el=(tag,text='')=>{const n=document.createElement(tag);n.textContent=text;return n;};
 const button=text=>{const b=el('button',text);b.type='button';b.className='secondary';return b;};
 function safeURL(value){
  try{const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password||u.port)return null;
   const host=u.hostname.toLowerCase();
   if(!host.includes('.')||host.endsWith('.local')||host.endsWith('.localhost')||host==='localhost'||host.startsWith('[')||/^\d+(\.\d+){3}$/.test(host))return null;
   return u;
  }catch{return null;}
 }
 function descriptor(value){
  const u=safeURL(value);if(!u)return null;
  const host=u.hostname.toLowerCase();let id;
  if(['youtube.com','www.youtube.com','m.youtube.com','www.youtube-nocookie.com'].includes(host)){
   id=u.pathname==='/watch'?u.searchParams.get('v'):u.pathname.match(/^\/(?:embed|shorts)\/([\w-]{11})\/?$/)?.[1];
  }else if(host==='youtu.be')id=u.pathname.slice(1);
  if(id&&/^[\w-]{11}$/.test(id))return {kind:'iframe',url:'https://www.youtube-nocookie.com/embed/'+id+'?playsinline=1&rel=0'};
  if(['vimeo.com','www.vimeo.com','player.vimeo.com'].includes(host)){
   const match=u.pathname.match(/^\/(?:video\/)?(\d+)(?:\/([a-f0-9]+))?\/?$/i);
   if(match){const result=new URL('https://player.vimeo.com/video/'+match[1]);const hash=u.searchParams.get('h')||match[2];if(hash&&/^[a-f0-9]+$/i.test(hash))result.searchParams.set('h',hash);result.searchParams.set('dnt','1');return {kind:'iframe',url:result.href};}
  }
  if(/\.(mp4|webm|ogv)$/i.test(u.pathname))return {kind:'video',url:u.href};
  return {kind:'link',url:u.href};
 }
 const active=new Set();
 function stopAll(){for(const stop of [...active])stop();}
 function render(media){
  const card=el('section');card.className='training-video';card.append(el('h4',media.title));
  const info=descriptor(media.url);if(!info){card.append(el('p','This video link is unavailable. Ask your admin to replace it.'));return card;}
  const link=el('a','Open original link');link.href=media.url;link.target='_blank';link.rel='noopener noreferrer';
  if(info.kind==='link'){card.append(link);return card;}
  const screen=el('div');screen.className='training-video-screen';screen.hidden=true;
  const load=button('Open video player'),close=button('Close player');close.hidden=true;let player=null;
  function stop(){if(player?.tagName==='VIDEO'){player.pause();player.removeAttribute('src');player.load();}screen.replaceChildren();screen.hidden=true;player=null;close.hidden=true;load.hidden=false;active.delete(stop);}
  load.onclick=()=>{if(player)return;player=el(info.kind);player.title=media.title;
   if(info.kind==='iframe'){player.allow='fullscreen; picture-in-picture';player.allowFullscreen=true;player.referrerPolicy='strict-origin-when-cross-origin';}
   else{player.controls=true;player.playsInline=true;player.preload='none';player.onerror=()=>{screen.replaceChildren(el('p','This video could not load. Try the original link or ask your admin to replace it.'));};}
   player.src=info.url;screen.replaceChildren(player);screen.hidden=false;load.hidden=true;close.hidden=false;active.add(stop);
  };
  close.onclick=stop;
  card.append(el('p','Load the video here, or open the original link.'),load,close,screen,link);return card;
 }
 function editor(initial,onchange){
  const details=el('details');details.className='training-media-editor';const summary=el('summary','Video links');details.append(summary);
  const rows=el('div'),add=button('Add video link');details.append(el('p','Paste a YouTube, Vimeo or direct video link. Save the draft, then publish to update the training.'),rows,add);
  const entries=[];
  function refresh(){summary.textContent='Video links ('+entries.length+')';add.disabled=entries.length>=10;}
  function row(media={}){
   const card=el('section');card.className='training-media-row';
   const input=(label,value,type='text')=>{const n=el('input');n.type=type;n.value=value||'';const l=el('label',label);l.append(n);card.append(l);return n;};
   const title=input('Link title',media.title),url=input('Video or document link (https)',media.url,'url');url.placeholder='Paste the video link';
   const rights=input('Our organization owns or is licensed to use this media',null,'checkbox');rights.checked=!!media.rights_confirmed;
   const note=input('Source, license or owner',media.rights_note),remove=button('Remove link');
   const entry={card,value:()=>({title:title.value.trim()||'Training video',url:url.value.trim(),rights_confirmed:rights.checked,rights_note:note.value.trim()})};entries.push(entry);
   remove.onclick=()=>{entries.splice(entries.indexOf(entry),1);card.remove();refresh();onchange();};card.append(remove);rows.append(card);refresh();
  }
  initial.forEach(row);add.onclick=()=>{if(entries.length>=10)return;row();onchange();};
  details.oninput=onchange;refresh();
  return {element:details,value:()=>entries.map(e=>e.value()).filter(m=>m.url)};
 }
 const exported={descriptor,safeURL,render,editor,stopAll};
 if(typeof module!=='undefined'&&module.exports)module.exports=exported;
 if(typeof window!=='undefined')window.WzosTrainingMedia=exported;
 if(typeof document!=='undefined')for(const name of ['wzos:view','wzos:session'])document.addEventListener(name,stopAll);
})();
