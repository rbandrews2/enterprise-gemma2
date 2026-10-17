/* Normalize formatting only; the server still verifies ownership and consent. */
(function(root){
 function normalize(value){
  const raw=String(value||'').trim();if(!/^[+0-9().\s-]+$/.test(raw))return null;
  let number=raw.replace(/[().\s-]/g,'');
  if(/^[2-9][0-9]{9}$/.test(number))number='+1'+number;
  else if(/^1[2-9][0-9]{9}$/.test(number))number='+'+number;
  return /^\+[1-9][0-9]{7,14}$/.test(number)?number:null;
 }
 if(typeof module!=='undefined'&&module.exports)module.exports={normalize};
 else root.WzosPhone={normalize};
})(typeof window==='undefined'?{}:window);
