'use strict';
(()=>{
 const get=id=>document.getElementById(id),frame=get('app'),shell=get('shell'),stage=get('stage'),space=get('device-space');
 let width=390,height=844;
 function render(){
  frame.style.width=width+'px';frame.style.height=height+'px';shell.style.width=(width+26)+'px';
  const scale=get('fit').checked?Math.max(.1,Math.min(1,(stage.clientWidth-40)/(width+26),(stage.clientHeight-40)/(height+74))):1;
  shell.style.transform='scale('+scale+')';space.style.width=(width+26)*scale+'px';space.style.height=(height+74)*scale+'px';
  get('dimensions').value=width+' × '+height+' CSS px · '+Math.round(scale*100)+'% · '+(width>height?'Landscape':'Portrait');
  get('width').value=width;get('height').value=height;
 }
 get('device').onchange=()=>{if(get('device').value!=='custom'){[width,height]=get('device').value.split(',').map(Number);render();}};
 get('apply').onclick=()=>{if(!get('width').reportValidity()||!get('height').reportValidity())return;width=Number(get('width').value);height=Number(get('height').value);get('device').value='custom';render();};
 get('rotate').onclick=()=>{[width,height]=[height,width];render();};
 get('reload').onclick=()=>frame.contentWindow.location.reload();get('fit').onchange=render;
 window.addEventListener('resize',render);render();
})();
