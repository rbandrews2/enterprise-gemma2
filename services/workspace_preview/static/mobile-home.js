'use strict';
// Mobile Home reuses the authorized module navigation; module pages stay unchanged.
(()=>{
 const media=window.matchMedia('(max-width:760px)'),side=document.querySelector('.sidebar');
 const bar=document.querySelector('.topbar'),menu=document.querySelector('nav[aria-label="Workspace navigation"]');
 if(!side||!bar||!menu)return;
 const session=()=>window.wzosClock?.getSession();
 let view=document.body.classList.contains('landing-active')?'dashboard':'orders';
 const home=document.createElement('button');home.type='button';home.id='mobile-home-return';home.className='secondary';home.textContent='⌂ Home';bar.prepend(home);
 const admin=document.createElement('button');admin.type='button';admin.id='mobile-admin-tools';admin.className='nav-item';admin.textContent='Organization management';admin.hidden=true;menu.append(admin);
 function goHome(){
  if(!media.matches||!session())return false;
  const accepted=window.showWzosView('home');
  if(accepted)window.scrollTo({top:0,behavior:'auto'});
  return accepted;
 }
 home.onclick=goHome;admin.onclick=()=>window.showWzosView('dashboard');
 function update(){
  const user=session();home.hidden=!user;admin.hidden=!user||user.role!=='admin';
  const controls=document.querySelector('.preview-bar');
  if(controls){
   if(media.matches&&view==='home')side.querySelector('.org-card')?.after(controls);
   else bar.after(controls);
  }
  for(const [id,unavailable] of [['report-nav',!user?.can_prepare_atlas],['assignments-nav',user?.edition!=='enterprise']]){
   const card=document.getElementById(id);if(card)card.dataset.mobileUnavailable=String(unavailable);
  }
  const title=document.querySelector('.breadcrumb + strong');
  const label=side.querySelector('.nav-label');if(label){label.textContent=media.matches?'':'WORKSPACE';label.hidden=media.matches;}
  if(title){if(media.matches&&view==='home')title.textContent='Home';else if(view==='dashboard')title.textContent=media.matches?'Organization management':'Dashboard';}
 }
 const brand=side.querySelector('.brand');brand?.addEventListener('click',event=>{if(media.matches&&session()){event.preventDefault();goHome();}});
 document.addEventListener('wzos:view',event=>{view=event.detail;update();});
 document.addEventListener('wzos:session',()=>{update();if(session()&&media.matches)goHome();else if(!session())document.body.classList.remove('mobile-home-active');});
 media.addEventListener('change',()=>{
  update();if(media.matches&&view==='dashboard')goHome();
  else if(!media.matches&&view==='home')window.showWzosView(session()?.role==='admin'?'dashboard':'orders');
 });
 update();if(session()&&media.matches)goHome();
})();
