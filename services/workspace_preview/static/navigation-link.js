"use strict";
// Google's documented cross-platform Maps URL; no API key or app location read.
(() => {
 const url=destination=>{
  if(typeof destination!=='string'||!destination.trim()||destination.length>500)return null;
  return 'https://www.google.com/maps/dir/?api=1&travelmode=driving&dir_action=navigate&destination='+encodeURIComponent(destination.trim());
 };
 const link=destination=>{
  const href=url(destination);if(!href)return null;
  const a=document.createElement('a');a.textContent='Open in Navigation';a.className='navigation-link';
  a.href=href;a.target='_blank';a.rel='noopener noreferrer';return a;
 };
 window.WzosNavigation={url,link};
})();
