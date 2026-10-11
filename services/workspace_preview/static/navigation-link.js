"use strict";
// Address actions enter the authorized WZOS Navigation workspace.
(() => {
 const url=destination=>{
  if(typeof destination!=='string'||!destination.trim()||destination.length>500)return null;
  try{
   const href='https://www.google.com/maps/dir/?api=1&travelmode=driving&dir_action=navigate&destination='+encodeURIComponent(destination.trim());
   return href.length<=2048?href:null;
  }catch(error){return null;}
 };
 let pending=null;
 const scope=()=>{const s=window.wzosClock?.getSession();return JSON.stringify([s?.organization_id,s?.id,s?.edition]);};
 const link=(destination,target)=>{
  const href=url(destination);if(!href)return null;
  if(!target?.id&&!target?.assignment_id)return null;
  const a=document.createElement('button');a.type='button';a.textContent='Open in Navigation';a.className='navigation-link secondary';
  a.onclick=()=>{pending={id:target.id,assignment_id:target.assignment_id,scope:scope()};if(!window.showWzosView('navigation'))pending=null;};return a;
 };
 const take=()=>{const target=pending;pending=null;return target?.scope===scope()?target:null;};
 document.addEventListener('wzos:session',()=>{pending=null;});
 window.WzosNavigation={url,link,take};
})();
