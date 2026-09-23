// Round 1 measurement: how often does the exam cue name something the question never
// mentions, and how long does picking a cue take?
window.CUECHECK=function(limit){
  const t=window.__t;
  const step=Math.max(1,Math.floor(t.QS.length/(limit||120)));
  let cued=0, off=0, n=0; const ex=[];
  const t0=performance.now();
  for(let i=0;i<t.QS.length;i+=step){
    const q=t.QS[i]; n++;
    const c=t.exCue(q); if(!c) continue;
    cued++;
    const hay=(q.q+' '+q.o.map(x=>x[1]).join(' ')+' '+(q.w||'')).toLowerCase();
    const a=String(c.a||'').toLowerCase().replace(/^(amazon|aws)\s+/,'').split(/[\s(\/]/)[0];
    if(a&&hay.indexOf(a)<0){ off++; if(ex.length<5) ex.push('q'+i+' -> '+c.a); }
  }
  const ms=performance.now()-t0;
  return {questions:n, cued, off, offPct:Math.round(off/Math.max(1,cued)*100)+'%',
          msPerQuestion:Math.round(ms/n*10)/10, ex};
};
