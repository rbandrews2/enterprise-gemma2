"use strict";
// Deterministic distance/uncertainty helpers; device proximity is never verified attendance.
function weatherDistance(a,b){const r=Math.PI/180,dlat=(b.latitude-a.latitude)*r,dlon=(b.longitude-a.longitude)*r;
 const x=Math.min(1,Math.max(0,Math.sin(dlat/2)**2+Math.cos(a.latitude*r)*Math.cos(b.latitude*r)*Math.sin(dlon/2)**2));return 6371000*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}
function weatherProximity(fix,site,time=Date.now()){
 if(!fix||![fix.latitude,fix.longitude,fix.accuracy,fix.timestamp,site.latitude,site.longitude,site.radius_meters].every(Number.isFinite)||Math.abs(fix.latitude)>90||Math.abs(fix.longitude)>180||Math.abs(site.latitude)>90||Math.abs(site.longitude)>180||fix.accuracy<0||site.radius_meters<50||time-fix.timestamp>120000||fix.timestamp>time+5000)return 'unavailable';
 const distance=weatherDistance(fix,site);return distance+fix.accuracy<=site.radius_meters?'inside':distance-fix.accuracy>site.radius_meters+30?'outside':'uncertain';
}
function weatherStale(data,time=Date.now()){const until=Date.parse(data.valid_until);return data.status==='stale'||data.status==='unavailable'||(Number.isFinite(until)?time>=until:!Number.isFinite(Date.parse(data.source_time))||time-Date.parse(data.source_time)>3600000);}
if(typeof module!=='undefined')module.exports={weatherDistance,weatherProximity,weatherStale};
if(typeof document!=='undefined')(()=>{
 const root=document.getElementById('weather-card');if(!root)return;
 const make=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;};
 const button=text=>{const b=make('button',text,'secondary');b.type='button';return b;};
 const api=(path,options)=>window.wzosClock.api(path,options),send=(path,body,method='POST')=>api(path,{method,body:JSON.stringify(body)});
 const label=(text,input)=>{const l=make('label',text);l.append(input);return l;};
 const field=(type,value='')=>{const n=make('input');n.type=type;n.value=value;return n;};
 const session=()=>window.wzosClock?.getSession(),scope=()=>{const s=session();return s?s.organization_id+':'+s.id:'';};
 let watchGeneration=0;
 let owner='',epoch=0,sites=[],following=false,watch=null,fix=null,lastWeather=null,lastPoint=null,lastFetch=0,fetching=false,fetchPoint=null,queuedPoint=null,weatherEpoch=0,nearSince={},dismissed=new Set(),lastNotices=0,noticesBusy=false,backgroundEnabled=false;
 const heading=make('div','','weather-heading'),title=make('h2','Weather'),location=make('p','Choose your location','weather-location');
 const follow=button('Use location'),stop=button('Stop'),refresh=button('↻');refresh.setAttribute('aria-label','Refresh weather');refresh.title='Refresh weather';stop.hidden=true;
 heading.append(make('span','☀','weather-symbol'),title,follow,stop,refresh);
 const summary=make('div','','weather-summary'),status=make('p','','fine'),hazards=make('div','','weather-hazards'),arrival=make('div','','weather-arrival'),notices=make('details'),noticeList=make('div');
 notices.append(make('summary','Job-site weather alerts'),noticeList);
 const config=make('details'),configBody=make('div','','weather-settings');config.append(make('summary','Job weather & arrival settings'),configBody);
 root.append(heading,location,summary,status,hazards);
 const jobTools=make('section','','weather-card weather-job-tools');jobTools.append(arrival,notices,config);root.after(jobTools);
 function stopWatch(){watchGeneration++;if(watch!==null)navigator.geolocation?.clearWatch(watch);watch=null;fix=null;nearSince={};arrival.replaceChildren();}
 function stopFollow(){following=false;stopWatch();weatherEpoch++;queuedPoint=null;follow.hidden=false;stop.hidden=true;location.textContent=lastWeather?'Last location · following stopped':'Location following stopped';}
 function clear(){epoch++;weatherEpoch++;stopFollow();owner=scope();sites=[];backgroundEnabled=false;lastWeather=null;lastPoint=null;lastFetch=0;queuedPoint=null;nearSince={};dismissed.clear();summary.replaceChildren();hazards.replaceChildren();noticeList.replaceChildren();configBody.replaceChildren();root.querySelector('[data-weather-chooser]')?.remove();status.textContent='';location.textContent='Choose your location';root.hidden=!owner;jobTools.hidden=!owner;config.hidden=session()?.role!=='admin';}
 function render(data,point){
  lastWeather=data;lastPoint=point;summary.replaceChildren();hazards.replaceChildren();
  location.textContent=point.title||data.location||'Selected location';
  const fmt=(n,suffix)=>Number.isFinite(n)?n+suffix:'—';
  const outlook=make('div','','weather-outlook');
  for(const day of (data.daily_forecast||[]).slice(0,4)){
   const row=make('div','','weather-day');row.append(make('strong',day.label),make('span',day.condition||'Forecast unavailable'),make('strong',`${fmt(day.high_f,'°')} / ${fmt(day.low_f,'°')}`));outlook.append(row);
  }
  if(outlook.children.length)summary.append(outlook);
 for(const [name,value] of [['Temperature',fmt(data.temperature_f,'°F')],['Feels like',fmt(data.feels_like_f,'°F')],['Wind',Number.isFinite(data.wind_mph)?fmt(data.wind_mph,' mph'):(data.wind_text||'—')],['Gusts',fmt(data.gust_mph,' mph')],['Rain · past hour',fmt(data.precipitation_inches,' in')]]){
   const item=make('div');item.append(make('span',name),make('strong',value));summary.append(item);
  }
  summary.append(make('p',data.condition||'Conditions unavailable'));
  const sourceDate=new Date(data.source_time),old=weatherStale(data);
  status.textContent=data.status==='unavailable'?'Weather unavailable. No current all-clear is available.':`${data.status==='stale'||!navigator.onLine||old?'Stale · ':''}${data.source||'National Weather Service'} · ${data.basis==='forecast'?'Forecast':'Observation'} · ${Number.isFinite(sourceDate.getTime())?sourceDate.toLocaleString():'source time unavailable'}`;
  for(const alert of data.alerts||[]){if(Date.parse(alert.expires)<=Date.now())continue;const d=make('details','','weather-hazard');d.dataset.severity=alert.severity;
   d.append(make('summary',`${alert.severity} · ${alert.headline}`),make('p',alert.description),make('p',alert.instruction),make('p','Valid until '+new Date(alert.expires).toLocaleString(),'fine'));hazards.append(d);}
 }
 async function loadWeather(point){
  if(!owner||document.hidden)return;if(fetching){if(!fetchPoint||weatherDistance(fetchPoint,point)>=1000||point.title!==fetchPoint.title){queuedPoint=point;weatherEpoch++;}return;}
  if(!navigator.onLine){if(lastWeather)render({...lastWeather,status:'stale'},lastPoint);else status.textContent='Offline · weather unavailable';return;}
  const current=owner,request=++weatherEpoch;fetching=true;fetchPoint=point;refresh.disabled=true;status.textContent='Updating weather…';
  if(lastPoint&&weatherDistance(lastPoint,point)>1000)location.textContent='Updating location · readings below are for the previous location';
  try{const data=await send('/api/weather/current',{latitude:point.latitude,longitude:point.longitude});if(owner===current&&request===weatherEpoch){lastFetch=Date.now();render(data,point);}}
  catch(error){if(owner===current&&request===weatherEpoch){if(lastWeather)render({...lastWeather,status:'stale'},lastPoint);status.textContent='Weather update unavailable · '+(error.message||'try again');}}
  finally{fetching=false;refresh.disabled=false;if(queuedPoint){const next=queuedPoint;queuedPoint=null;if(owner===current)loadWeather(next);}}
 }
 function proximity(){
  arrival.replaceChildren();if(!fix||!following)return;
  const time=Date.now();const ordered=[...sites].sort((a,b)=>weatherDistance(fix,a)-weatherDistance(fix,b));
  for(const site of ordered){const state=weatherProximity(fix,site,time);
   if(state==='outside'){delete nearSince[site.order_id];dismissed.delete(site.order_id);continue;}
   if(state!=='inside'){delete nearSince[site.order_id];continue;}
   nearSince[site.order_id]??={since:time,count:0,last:null};const dwell=nearSince[site.order_id];
   if(dwell.last!==fix.timestamp){dwell.last=fix.timestamp;dwell.count++;}
   if(time-dwell.since<5000||dwell.count<2||dismissed.has(site.order_id))continue;
   arrival.append(make('strong','You appear near '+site.title),make('p','Device GPS is approximate. Review your job before clocking in or changing tasks.'));
   const review=button('Review in Time Tracker'),dismiss=button('Dismiss');review.onclick=()=>{if(window.showWzosView('clock'))document.dispatchEvent(new CustomEvent('wzos:arrival-select',{detail:{order_id:site.order_id}}));};
   dismiss.onclick=()=>{dismissed.add(site.order_id);arrival.replaceChildren();};arrival.append(review,dismiss);break;
  }
 }
 async function startWatch(){
  stopWatch();const current=owner,turn=epoch,watchTurn=watchGeneration;
  let permission='unknown';try{permission=window.wzosDeviceSetup?await window.wzosDeviceSetup.status('geolocation'):(await navigator.permissions.query({name:'geolocation'})).state;}catch{}
  if(owner!==current||turn!==epoch||watchTurn!==watchGeneration||document.hidden)return;
  if(permission!=='granted'){following=false;follow.hidden=false;stop.hidden=true;status.textContent='Enable location in device setup or browser settings for local weather.';return;}
  if(!navigator.geolocation){status.textContent='Location is unavailable on this device.';return;}
  following=true;follow.hidden=true;stop.hidden=false;
  watch=navigator.geolocation.watchPosition(position=>{
   if(owner!==current||!following||document.hidden)return;
   fix={latitude:position.coords.latitude,longitude:position.coords.longitude,accuracy:position.coords.accuracy,timestamp:position.timestamp};
   proximity();if(!lastPoint||weatherDistance(fix,lastPoint)>=1000||Date.now()-lastFetch>15*60000)loadWeather(fix);else if(lastWeather)render(lastWeather,lastPoint);
  },error=>{if(owner===current){fix=null;nearSince={};arrival.replaceChildren();if(error.code===1)stopFollow();status.textContent=error.code===1?'Location permission changed. Enable it in browser settings.':'Location fix unavailable. Previous weather may be stale.';}}, {enableHighAccuracy:false,maximumAge:30000,timeout:15000});
 }
 follow.onclick=async()=>{await startWatch();if(!following)window.wzosDeviceSetup?.open();};stop.onclick=stopFollow;
 refresh.onclick=()=>{if(fix)loadWeather(fix);else if(lastPoint)loadWeather(lastPoint);else startWatch();};
 async function loadSites(){
  const current=owner,turn=epoch;try{const data=await api('/api/weather/sites');if(owner!==current||turn!==epoch)return;sites=data.items;renderSettings();proximity();}catch(error){if(owner===current)status.textContent=error.message;}
 }
 function renderSettings(){
  configBody.replaceChildren();
  if(session()?.role!=='admin')return;
  const order=make('select');order.append(Object.assign(make('option','Select work order'),{value:''}));for(const job of window.wzosClock.getOrders())order.append(Object.assign(make('option',job.title),{value:job.id}));
  const lat=field('number'),lon=field('number'),radius=field('number','350'),enabled=field('checkbox'),start=field('datetime-local'),end=field('datetime-local'),save=button('Save site settings'),check=button('Check monitored job weather');
  lat.step=lon.step='any';lat.min='-90';lat.max='90';lon.min='-180';lon.max='180';radius.min='50';radius.max='2000';
  const local=value=>value?new Date(Date.parse(value)-new Date(value).getTimezoneOffset()*60000).toISOString().slice(0,16):'';
  order.onchange=()=>{const s=sites.find(s=>s.order_id===order.value);lat.value=s?.latitude??'';lon.value=s?.longitude??'';radius.value=s?.radius_meters??350;enabled.checked=s?.monitoring??false;start.value=local(s?.starts_at);end.value=local(s?.ends_at);};
  save.onclick=async()=>{if(!order.value||!lat.value||!lon.value){status.textContent='Select a work order and enter its reviewed coordinates.';return;}if(enabled.checked&&(!start.value||!end.value)){status.textContent='Set the monitoring start and finish.';return;}
   const s=sites.find(s=>s.order_id===order.value),current=owner;save.disabled=true;
   try{await send('/api/weather/sites/'+encodeURIComponent(order.value),{expected_version:s?.version||0,latitude:Number(lat.value),longitude:Number(lon.value),radius_meters:Number(radius.value),monitoring:enabled.checked,starts_at:start.value?new Date(start.value).toISOString():null,ends_at:end.value?new Date(end.value).toISOString():null},'PUT');if(owner===current){await loadSites();status.textContent=backgroundEnabled?'Site settings saved for the configured monitoring window.':'Site settings saved. Background monitoring has not been activated.';}}
   catch(error){if(owner===current)status.textContent=error.message;}finally{save.disabled=false;}};
  check.onclick=async()=>{check.disabled=true;const current=owner;try{await send('/api/weather/poll',{});if(owner===current)status.textContent='Job weather check scheduled. Refresh job alerts shortly.';}catch(error){if(owner===current)status.textContent=error.message;}finally{check.disabled=false;}};
  configBody.append(label('Work order',order),label('Site latitude',lat),label('Site longitude',lon),label('Arrival radius (meters)',radius),label('Monitor this site',enabled),label('Monitoring starts',start),label('Monitoring ends',end),save,check,make('p','Site coordinates are reviewed job references. Background monitoring and SMS are controlled separately.','fine'));
 }
 async function loadNotices(){
  if(!owner||noticesBusy||document.hidden||!navigator.onLine)return;const current=owner,turn=epoch;noticesBusy=true;
  try{const data=await api('/api/weather/notices');if(owner!==current||turn!==epoch)return;backgroundEnabled=data.background_monitoring===true;noticeList.replaceChildren();lastNotices=Date.now();
   for(const n of data.items.filter(n=>!n.superseded).slice(0,30)){const details=make('details','','weather-hazard');details.append(make('summary',n.body),make('p',n.alert.description),make('p',n.alert.instruction));
    const b=button(n.acknowledged_at?'Acknowledged':'Acknowledge');b.disabled=!!n.acknowledged_at;b.onclick=async()=>{b.disabled=true;try{await send('/api/weather/notices/'+n.id+'/ack',{});if(owner===current)loadNotices();}catch(error){if(owner===current)status.textContent=error.message;b.disabled=false;}};details.append(b);
    if(session()?.edition==='enterprise'){const open=button('Open My jobs');open.onclick=()=>window.showWzosView('assignments');details.append(open);}
    noticeList.append(details);}
   if(!noticeList.children.length)noticeList.append(make('p',backgroundEnabled?'No job-site weather notices.':'No job-site weather notices. Automatic monitoring is not active.'));
  }catch(error){if(owner===current)noticeList.replaceChildren(make('p','Job alerts unavailable.'));}finally{noticesBusy=false;}
 }
 document.addEventListener('wzos:session',()=>{if(scope()!==owner){clear();if(owner){loadSites();loadNotices();startWatch();}}});
 document.addEventListener('wzos:view',()=>{if(owner)loadSites();});
 document.addEventListener('wzos:device-permissions',()=>{if(owner)startWatch();});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stopWatch();else if(owner){if(following){status.textContent='Finding your current location…';startWatch();}else if(lastPoint)loadWeather(lastPoint);loadSites();loadNotices();}});
 window.addEventListener('offline',()=>{if(lastWeather)render({...lastWeather,status:'stale'},lastPoint);});
 window.addEventListener('online',()=>{if(owner){loadSites();loadNotices();if(lastPoint)loadWeather(lastPoint);}});
 setInterval(()=>{if(!owner||document.hidden)return;proximity();if(lastWeather&&lastWeather.status!=='stale'&&(weatherStale(lastWeather)||!navigator.onLine))render({...lastWeather,status:'stale'},lastPoint);if(Date.now()-lastFetch>=15*60000&&lastPoint&&(!following||fix))loadWeather(fix||lastPoint);if(Date.now()-lastNotices>=60000)loadNotices();},10000);
 clear();if(owner){loadSites();loadNotices();startWatch();}
})();
