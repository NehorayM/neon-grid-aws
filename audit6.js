// Sixth pass: the arithmetic nobody has checked. Dates, formatting, scheduling, export —
// the quiet logic underneath the screens that has never been driven at its edges.
(function(){
const found=[]; const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const $=id=>document.getElementById(id);
const t=window.__t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

// ------------------------------------------------------- 1. clock formatting at the edges
function clockFormat(){
  const f=t.fmtClock;
  if(typeof f!=='function'){ F('LOW','harness','fmtClock is not exposed'); return; }
  const cases=[[0,'0:00'],[1000,'0:01'],[59000,'0:59'],[60000,'1:00'],
               [3599000,'59:59'],[3600000,'1:00:00'],[3661000,'1:01:01']];
  cases.forEach(([ms,want])=>{
    const got=f(ms);
    if(got!==want) F('MED','format','fmtClock('+ms+') is "'+got+'", expected "'+want+'"');
  });
  // the ones a caller can actually produce
  [[-1000,'negative'],[NaN,'NaN'],[Infinity,'Infinity'],[undefined,'undefined']].forEach(([v,nm])=>{
    let got; try{ got=f(v); }catch(e){ F('MED','format','fmtClock('+nm+') throws',e.message); return; }
    if(/NaN|Infinity|-/.test(String(got)))
      F('MED','format','fmtClock('+nm+') renders "'+got+'"');
  });
}

// ------------------------------------------------------- 2. the day key across boundaries
function dayKeys(){
  const k=t.dayKey;
  if(typeof k!=='function'){ F('LOW','harness','dayKey is not exposed'); return; }
  const now=k();
  if(!/^\d{4}-\d{1,2}-\d{1,2}$/.test(now)) F('MED','date','dayKey() is not a date: '+now);
  // the shape must sort and compare consistently; single-digit months break string compare
  const RealDate=Date;
  const at=iso=>{ const d=new RealDate(iso); window.Date=function(){ return d; };
                  window.Date.now=()=>d.getTime(); window.Date.prototype=RealDate.prototype; };
  try{
    at('2026-01-05T12:00:00'); const a=k();
    at('2026-01-12T12:00:00'); const b=k();
    at('2026-02-01T12:00:00'); const c=k();
    window.Date=RealDate;
    if(a===b||b===c) F('HIGH','date','different days produce the same key',a+' / '+b+' / '+c);
    if(!(a<b)) F('MED','date','day keys do not sort: "'+a+'" is not before "'+b+'"');
    if(!(b<c)) F('MED','date','day keys do not sort across months: "'+b+'" vs "'+c+'"',
                 'single-digit months make string comparison wrong');
  }catch(e){ window.Date=RealDate; F('LOW','harness','could not fake the clock: '+e.message); }
}

// ------------------------------------------- 3. spaced repetition must move in one direction
function scheduler(){
  if(typeof t.srSchedule!=='function'){ F('LOW','harness','srSchedule not exposed'); return; }
  const keep=JSON.parse(JSON.stringify(t.P.sr||{}));
  t.P.sr={};
  // srSchedule measures in questions answered, not in time — the first version of this check
  // called it twice without moving P.answered and then blamed the scheduler for standing still.
  const keepAns=t.P.answered;
  const i=7;
  t.P.answered=100; t.srSchedule(i,true);
  const a=t.P.sr[i];
  if(!a){ F('MED','sr','a right answer schedules nothing'); t.P.sr=keep; t.P.answered=keepAns; return; }
  const gapA=a.due-100;
  t.P.answered=110; t.srSchedule(i,true);
  const b=t.P.sr[i];
  if(b){
    const gapB=b.due-110;
    if(gapB<=gapA) F('MED','sr','a second right answer does not widen the gap',gapA+' -> '+gapB);
    t.P.answered=120; t.srSchedule(i,false);
    const c=t.P.sr[i];
    if(c&&(c.due-120)>=gapB) F('MED','sr','a wrong answer does not narrow the gap',gapB+' -> '+(c.due-120));
    if(c&&c.box!==0) F('MED','sr','a wrong answer does not reset the box',String(c.box));
  }
  t.P.answered=keepAns;
  Object.keys(t.P.sr).forEach(k=>{
    const v=t.P.sr[k];
    if(v&&(!isFinite(v.due)||v.due<0)) F('HIGH','sr','a review is scheduled at an impossible time',JSON.stringify(v));
  });
  t.P.sr=keep;
}

// ------------------------------------------------------- 4. export and import round trip
async function roundTrip(){
  if(typeof t.exportProfile!=='function'){ F('LOW','harness','exportProfile not exposed'); return; }
  const before=JSON.parse(JSON.stringify(t.P));
  let text=null;
  const realBlob=window.Blob, realURL=window.URL.createObjectURL;
  window.Blob=function(parts){ text=String(parts&&parts[0]||''); return new realBlob(parts); };
  window.URL.createObjectURL=()=>'blob:stub';
  try{ t.exportProfile(); }catch(e){ F('MED','export','exportProfile throws',e.message); }
  window.Blob=realBlob; window.URL.createObjectURL=realURL;
  if(!text){ F('MED','export','exporting produced nothing'); return; }
  let parsed=null;
  try{ parsed=JSON.parse(text); }catch(e){ F('HIGH','export','the exported file is not valid JSON',e.message); return; }
  ['xp','coins','answered','correct','seen','badges'].forEach(k=>{
    if(!(k in parsed)) F('MED','export','the export is missing '+k);
  });
  const normalised=t.normaliseProfile(JSON.parse(JSON.stringify(parsed)));
  ['xp','coins','answered','correct'].forEach(k=>{
    if(Number(normalised[k]||0)!==Number(before[k]||0))
      F('HIGH','export',k+' does not survive an export and normalise',before[k]+' -> '+normalised[k]);
  });
}

// ----------------------------------------------------- 5. the CSV must be well formed
function csv(){
  if(typeof t.csvRows!=='function'){ F('LOW','harness','csvRows not exposed'); return; }
  const list=[{i:0,why:'Flagged'},{i:1,why:'Missed'},{i:2,why:'Flagged + missed'}];
  const out=t.csvRows(list);
  const lines=String(out).split('\r\n');
  if(lines.length!==list.length+1) F('MED','csv','wrong row count: '+lines.length+' for '+list.length+' entries');
  const cols=l=>(l.match(/","/g)||[]).length+1;
  const head=cols(lines[0]);
  lines.forEach((l,k)=>{
    if(!l) return;
    if(cols(l)!==head) F('HIGH','csv','row '+k+' has '+cols(l)+' columns, the header has '+head);
    if(/[^"]\r|\n/.test(l)) F('HIGH','csv','row '+k+' contains a raw newline');
    const quotes=(l.match(/"/g)||[]).length;
    if(quotes%2) F('HIGH','csv','row '+k+' has an odd number of quotes — it will not parse');
  });
  // a question whose text contains a quote and a comma must survive
  const q=t.QS[0];
  const was=q.q;
  q.q='He said "yes, definitely" — then, later, no';
  const tricky=t.csvRows([{i:0,why:'Flagged'}]).split('\r\n')[1];
  q.q=was;
  if(cols(tricky)!==head) F('HIGH','csv','a quote and a comma in the stem break the column count');
  if(tricky.indexOf('""yes')<0) F('MED','csv','quotes in the stem are not doubled as CSV requires');
}

// ----------------------------------------------- 6. badge progress cannot exceed its goal
function badges(){
  if(typeof t.badgeProgress!=='function'||!t.BADGES){ F('LOW','harness','badges not exposed'); return; }
  const keep=JSON.parse(JSON.stringify(t.P));
  // values a real profile reaches, not 1e6 — the point is that progress cannot exceed a goal
  Object.assign(t.P,{answered:1200,correct:900,streak:40,bestStreak:40,gamesPlayed:60,
                     xp:90000,coins:9000,mocks:30,mocksPassed:20,sims:30,simsPassed:20,
                     studyOpened:80,examsPassed:19,bossesBeaten:20});
  t.BADGES.forEach(b=>{
    let pr=null;
    try{ pr=t.badgeProgress(b); }catch(e){ F('MED','badge',b.id+' progress throws',e.message); return; }
    if(!pr) return;
    if(!isFinite(pr[0])||!isFinite(pr[1])) F('MED','badge',b.id+' progress is not a number',JSON.stringify(pr));
    else if(pr[1]>0&&pr[0]/pr[1]>1.0001) F('MED','badge',b.id+' reports more progress than its goal',pr.join('/'));
  });
  Object.keys(t.P).forEach(k=>delete t.P[k]); Object.assign(t.P,keep);
}

// ------------------------------------------- 7. the daily state across a date change
function daily(){
  if(typeof t.dailyState!=='function'){ F('LOW','harness','dailyState not exposed'); return; }
  const keep=JSON.parse(JSON.stringify(t.P));
  const d0=t.dailyState();
  if(!d0||!isFinite(d0.n)) F('MED','daily','dailyState is not a count',JSON.stringify(d0));
  if(d0&&d0.n<0) F('MED','daily','a negative daily count',String(d0.n));
  // a stale day must reset rather than carry over
  t.P.day={date:'1999-1-1',n:999};
  const d1=t.dailyState();
  if(d1&&d1.n>=999) F('HIGH','daily',"yesterday's count carries into today",String(d1.n));
  Object.keys(t.P).forEach(k=>delete t.P[k]); Object.assign(t.P,keep);
}

window.AUDIT6=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface'); return {total:1,found}; }
  clockFormat(); dayKeys(); scheduler();
  await roundTrip();
  csv(); badges(); daily();
  t.go('homeScreen');
  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT6:',found.length,by);
  return {total:found.length,by,found};
};
console.log('AUDIT6 ready');
})();
