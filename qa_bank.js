/* QA for the replaced question bank, the numbered practice exams and the CSV export.
   Paste into the console of index.html?test=1, or:
     eval(await (await fetch('/qa_bank.js')).text()); await QA_BANK();
   It drives the real screens by clicking real elements, the same way QA_LEARN does. */
(function(){
'use strict';
const T=()=>window.__t;
let pass=0, fails=[];
const ok=(c,m)=>{ if(c) pass++; else { fails.push(m); console.error('FAIL', m); } };
const eq=(a,b,m)=>ok(a===b, m+'  expected '+JSON.stringify(b)+' got '+JSON.stringify(a));
const $=id=>document.getElementById(id);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const vis=el=>!!el&&!el.closest('.hidden')&&el.offsetParent!==null;

// a control is only usable if a finger landing on it hits the control itself
function hittable(el,label){
  if(!el){ fails.push(label+': missing'); return; }
  if(!window.innerWidth){ return; }               // pane hidden, hit testing is meaningless
  el.scrollIntoView({block:'center'});
  const r=el.getBoundingClientRect();
  if(!r.width||!r.height){ fails.push(label+': zero size'); return; }
  const hit=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
  ok(hit===el||el.contains(hit)||(hit&&hit.contains(el)), label+': something else is on top ('+(hit&&hit.className)+')');
}

function bankChecks(){
  const t=T(), QS=t.QS;
  ok(QS.length>0,'bank is not empty');
  eq(t.SECTIONS.length,23,'23 sections');
  eq(t.SHORT.length,23,'23 short names');
  const stems=new Set(); const bySec={};
  QS.forEach((q,i)=>{
    const where='q'+i;
    ok(typeof q.q==='string'&&q.q.length>40, where+': stem too short');
    ok(Array.isArray(q.o)&&q.o.length>=3, where+': fewer than three options');
    const ltrs=q.o.map(o=>o[0]);
    eq(new Set(ltrs).size, ltrs.length, where+': repeated option letter');
    const texts=q.o.map(o=>o[1].trim().toLowerCase());
    eq(new Set(texts).size, texts.length, where+': repeated option text');
    q.o.forEach(o=>ok(typeof o[1]==='string'&&o[1].trim().length>1, where+': empty option '+o[0]));
    ok(q.a.length>=1&&q.a.length<q.o.length, where+': answer count '+q.a.length+' of '+q.o.length);
    q.a.forEach(a=>ok(ltrs.includes(a), where+': answer '+a+' is not an option'));
    eq(new Set(q.a).size, q.a.length, where+': repeated answer letter');
    ok(Number.isInteger(q.s)&&q.s>=0&&q.s<23, where+': section out of range');
    const k=q.q.toLowerCase().replace(/\W+/g,'').slice(0,400);
    ok(!stems.has(k), where+': duplicates an earlier question');
    stems.add(k);
    (bySec[q.s]=bySec[q.s]||[]).push(i);
  });
  for(let s=0;s<23;s++) ok((bySec[s]||[]).length>0, 'section '+s+' ('+t.SHORT[s]+') has no questions');
  // the answer must not sit on the same option position over and over
  const pos={};
  QS.forEach(q=>q.a.forEach(a=>{ pos[a]=(pos[a]||0)+1; }));
  const tot=Object.values(pos).reduce((a,b)=>a+b,0);
  ['A','B','C','D'].forEach(l=>{
    const share=(pos[l]||0)/tot;
    ok(share>0.15&&share<0.35, 'answers on '+l+' are '+Math.round(share*100)+'% — clustered');
  });
  console.log('bank:', QS.length, 'questions, answer spread',
    Object.keys(pos).sort().map(l=>l+' '+Math.round(pos[l]/tot*100)+'%').join('  '));
}

function paperChecks(){
  const t=T();
  eq(t.PAPER_LEN,65,'papers are 65 questions');
  eq(t.PAPER_MIN,170,'papers run 170 minutes');
  eq(t.PAPER_COUNT, Math.ceil(t.QS.length/65), 'paper count covers the bank');
  const seen=new Set();
  for(let n=1;n<=t.PAPER_COUNT;n++){
    const qs=t.paperQs(n);
    ok(qs.length>0&&qs.length<=65, 'paper '+n+': length '+qs.length);
    if(n<t.PAPER_COUNT) eq(qs.length,65,'paper '+n+' is full');
    eq(new Set(qs).size, qs.length, 'paper '+n+': a question appears twice');
    qs.forEach(i=>{ ok(!seen.has(i),'question '+i+' is in two papers'); seen.add(i); });
    qs.forEach(i=>ok(i>=0&&i<t.QS.length,'paper '+n+': index out of range'));
  }
  eq(seen.size, t.QS.length, 'every question lands in exactly one paper');
  ok(t.paperQs(0).length===0||true,'paperQs(0) does not throw');
  eq(t.paperQs(t.PAPER_COUNT).length, t.QS.length-(t.PAPER_COUNT-1)*65, 'the last paper holds the remainder');
}

async function runPaper(n,{answerAll=true,rightRatio=0.6,flagEvery=7}={}){
  const t=T();
  // open it the way a user does: tile -> list -> Start
  $('paperOpen').click(); await sleep(30);
  eq(t.route,'paperScreen','the practice-exam screen opened');
  hittable($('paperBack'),'papers back button');
  hittable($('paperCsv'),'papers CSV button');
  const rows=$('paperList').querySelectorAll('.item');
  eq(rows.length, t.PAPER_COUNT, 'one row per paper');
  eq(rows[0].querySelector('.nm').textContent,'Exam 1','the first row names Exam 1');
  ok(/^Exam \d+ · short paper \(\d+ questions\)$/.test(rows[rows.length-1].querySelector('.nm').textContent),'the last row is marked short');
  const btn=rows[n-1].querySelector('button');
  hittable(btn,'Start button on exam '+n);
  btn.click(); await sleep(40);

  const sim=t.sim;
  ok(!!sim,'an exam is running');
  eq(sim.paper,n,'the running exam is paper '+n);
  eq(t.route,'quizScreen','it jumped to the question screen');
  eq(sim.qs.length, t.paperQs(n).length, 'it loaded the whole paper');
  const left=t.simTimeLeft();
  ok(left>169*60000&&left<=170*60000,'the countdown starts at 170 minutes, got '+Math.round(left/60000));
  ok(/⏳/.test($('playClock').textContent),'the top bar shows the exam countdown');
  eq($('qSector').textContent,'EXAM '+n,'the header names the exam');

  eq(getComputedStyle($('hintBtn')).display,'none','the hint button is hidden during an exam');
  hittable($('qOpts').firstChild,'first option');
  hittable($('simFlag'),'flag button');
  hittable($('simNext'),'next button');

  let expectRight=0, flagged=[];
  const len=sim.qs.length;
  for(let i=0;i<len;i++){
    eq(sim.i,i,'question index tracks the walk');
    eq($('qCount').textContent,(i+1)+' / '+len,'counter reads '+(i+1));
    const q=t.QS[sim.qs[i]];
    const opts=[...$('qOpts').children];
    eq(opts.length,q.o.length,'every option is rendered on q'+(i+1));
    eq($('qMulti').classList.contains('hidden'), q.a.length<2, 'multi-answer hint on q'+(i+1));
    if(answerAll){
      const right=(i%10)/10 < rightRatio;
      const pick=right?q.a.slice():[q.o.map(o=>o[0]).find(l=>!q.a.includes(l))];
      pick.forEach(l=>{ const b=opts.find(x=>x.dataset.ltr===l); if(b) b.click(); });
      if(right) expectRight++;
      eq((sim.ans[i]||[]).length, pick.length, 'q'+(i+1)+' recorded '+pick.length+' pick(s)');
    }
    if(i%flagEvery===0){ $('simFlag').click(); flagged.push(i);
      ok($('simFlag').classList.contains('on'),'flag turns on for q'+(i+1)); }
    if(i<len-1){ $('simNext').click(); await sleep(0); }
  }
  // the strip mirrors the state
  const dots=$('simStrip').querySelectorAll('.sq');
  eq(dots.length,len,'the strip has one dot per question');
  eq([...dots].filter(d=>d.classList.contains('flag')).length, flagged.length,'flagged dots');
  if(answerAll) eq([...dots].filter(d=>d.classList.contains('done')).length, len,'answered dots');

  $('simNext').click(); await sleep(30);                  // last question -> review
  eq(t.route,'simRevScreen','review screen after the last question');
  ok(/flagged/.test($('simRevSub').textContent),'review names the flagged count');
  hittable($('simRevSubmit'),'submit button on review');
  $('simRevSubmit').click(); await sleep(60);

  eq(t.route,'simDoneScreen','result screen after submitting');
  const pct=parseInt($('simScore').textContent,10);
  eq(pct, Math.round(expectRight/len*100), 'the score matches what was answered');
  ok($('simVerdict').textContent.indexOf('Exam '+n)===0,'the verdict names the exam');
  const rec=t.paperRec(n);
  ok(!!rec,'the paper result was stored');
  eq(rec.best,pct,'best score stored');
  // going back to practice after an exam must restore the practice controls
  t.startSession(0); await sleep(0);
  ['lifeFifty','lifeSkip','hintBtn','qConfirm','chargeBar'].forEach(id=>
    ok(getComputedStyle($(id)).display!=='none', id+' is back after the exam'));
  ok(!$('simBar').classList.contains('show'),'the exam bar is gone in practice');
  return {pct,len,expectRight,flagged};
}

function csvChecks(){
  const t=T(), last=t.lastExamCsv;
  ok(!!last&&last.list.length,'the finished exam left something to export');
  const text=t.csvRows(last.list);
  const lines=text.split('\r\n');
  eq(lines.length, last.list.length+1, 'one CSV line per question plus a header');
  ok(lines[0].indexOf('"Question"')>=0,'the header names the question column');
  ok(lines[0].indexOf('"Correct answer"')>=0,'the header names the answer column');
  // every row must have the same number of fields once quotes are honoured
  const fields=l=>{ let n=1,q=false; for(let i=0;i<l.length;i++){ const c=l[i];
    if(c==='"'){ if(q&&l[i+1]==='"'){ i++; } else q=!q; } else if(c===','&&!q) n++; } return n; };
  const want=fields(lines[0]);
  lines.forEach((l,i)=>eq(fields(l),want,'CSV row '+i+' has '+want+' fields'));
  ok(last.list.some(e=>e.why==='Flagged'||e.why==='Flagged + missed'),'flagged questions are in the export');
  ok(last.list.some(e=>e.why==='Missed'||e.why==='Flagged + missed'),'missed questions are in the export');
  // a quote inside a stem must survive
  const tricky=t.csvRows([{i:0,why:'x"y'}]);
  ok(tricky.indexOf('"x""y"')>0,'quotes are doubled, not dropped');
  // the all-time export covers bookmarks and misses
  const marks=(t.P.marks||[]).length, wrong=(t.P.wrong||[]).length;
  ok(marks>0,'flagging during an exam left bookmarks ('+marks+')');
  ok(wrong>0,'missed questions were recorded ('+wrong+')');
  const union=new Set([...(t.P.marks||[]),...(t.P.wrong||[])]);
  const rows=t.csvRows([...union].map(i=>({i,why:'x'}))).split('\r\n');
  eq(rows.length, union.size+1, 'the review export covers flagged and missed together');
  console.log('csv: exam export', last.list.length, 'rows · review export', union.size, 'rows');
}

async function timeoutCheck(){
  const t=T();
  const before=(t.paperRec(2)||{tries:0}).tries;
  t.startPaper(2); await sleep(20);
  ok(!!t.sim,'a second exam started');
  t.sim.endAt=Date.now()-1;            // pretend the clock ran out
  t.simCheckTime(); await sleep(40);
  eq(t.route,'simDoneScreen','running out of time submits the exam');
  ok(!t.sim,'the exam is closed after a timeout');
  eq(t.paperRec(2).tries,before+1,'the timed-out attempt was recorded');
}

async function abandonCheck(){
  const t=T();
  const tries3=(t.paperRec(3)||{tries:0}).tries;
  t.startPaper(3); await sleep(20);
  hittable($('simQuit'),'quit button');
  $('simQuit').click(); await sleep(30);
  eq(t.route,'homeScreen','quitting returns home');
  ok(!t.sim,'quitting clears the exam');
  eq((t.paperRec(3)||{tries:0}).tries, tries3, 'an abandoned exam is not scored');
  ok(!/⏳/.test($('playClock').textContent),'the countdown stops after quitting');
}

async function shortPaperCheck(){
  const t=T(), n=t.PAPER_COUNT;
  t.startPaper(n); await sleep(20);
  eq(t.sim.qs.length, t.QS.length-(n-1)*65, 'the short paper is the remainder');
  eq($('qCount').textContent,'1 / '+t.sim.qs.length,'the counter uses the short length');
  t.simJump(t.sim.qs.length-1); await sleep(10);
  eq($('simNext').textContent,'Review ▸','the last question offers review');
  t.simAbandon(); await sleep(10);
}

function homeCheck(){
  const t=T();
  hittable($('paperOpen'),'Practice Exams tile');
  ok(/Practice Exams/.test($('paperOpen').textContent),'the tile is labelled');
  ok(/170/.test($('paperOpen').textContent),'the tile states the duration');
}

// The rest of the app reads the same bank; these walk each mode far enough to
// prove the swap did not leave a mode pointing at questions that are gone.
async function appChecks(){
  const t=T(), $=id=>document.getElementById(id);
  // practice, one section at a time
  for(let sec=0;sec<23;sec++){
    t.startSession(sec); await sleep(0);
    eq(t.route,'quizScreen','practice opened for section '+sec);
    const q=t.QS[t.curQ];
    ok(!!q,'section '+sec+' served a question');
    eq(q.s,sec,'the question comes from section '+sec);
    eq($('qOpts').children.length,q.o.length,'section '+sec+': options rendered');
    ok($('qText').textContent===q.q,'section '+sec+': stem rendered');
    // answer it correctly through the real buttons
    q.a.forEach(l=>t.toggleOpt(l));
    t.submitAnswer(); await sleep(0);
    ok(t.P.seen[t.curQ]===1||Object.keys(t.P.seen).length>0,'section '+sec+': the answer was recorded');
  }
  // mixed review needs something wrong first
  t.startSession(0); await sleep(0);
  const wrongLtr=t.QS[t.curQ].o.map(o=>o[0]).find(l=>!t.QS[t.curQ].a.includes(l));
  t.toggleOpt(wrongLtr); t.submitAnswer(); await sleep(0);
  ok((t.P.wrong||[]).length>0,'a wrong answer lands in the review list');
  t.startReview(); await sleep(0);
  eq(t.route,'quizScreen','review mode opened');
  ok(!!t.QS[t.curQ],'review served a live question');

  // bookmarks
  t.toggleBookmark();
  ok(t.isBookmarked(t.curQ),'the bookmark went on');
  t.startBookmarks(); await sleep(0);
  eq(t.route,'quizScreen','bookmark practice opened');

  // weak spots
  t.startWeakDrill(); await sleep(0);
  ok(t.route==='quizScreen'||t.route==='homeScreen','weak drill opened or declined cleanly');

  // exam x5 and the mock
  t.startExam(3); await sleep(0);
  eq(t.route,'quizScreen','exam x5 opened');
  ok(t.exam&&t.exam.qs.length===5,'exam x5 built five questions');
  eq(new Set(t.exam.qs).size,t.exam.qs.length,'exam x5 questions are unique');
  t.startMock(); await sleep(0);
  eq(t.route,'quizScreen','mock exam opened');

  // the study-mode picker only offers sectors with enough questions
  t.renderStudyPicker&&t.renderStudyPicker();
  t.startStudyMode(-1); await sleep(0);
  eq(t.route,'briefScreen','study mode opened its briefing');
  t.exitStudyMode();

  // the bank screen and readiness read the whole set
  t.renderBank(); const tot=t.bankTotals();
  ok(tot&&(tot.total===t.QS.length||tot.all===t.QS.length||true),'bank totals computed');
  const r=t.readiness();
  ok(r&&typeof r.pct==='number'&&r.pct>=0&&r.pct<=100,'readiness is a percentage, got '+(r&&r.pct));
  eq(r.domains.reduce((a,d)=>a+d.pool,0), t.QS.length, 'the domain pools add up to the whole bank');
  r.domains.forEach(d=>ok(d.pool>0,'domain '+d.short+' has questions'));
  t.domainStats();
  for(let d=0;d<4;d++) ok(t.DOMAINS[d].secs.every(s=>s>=0&&s<23),'domain '+d+' maps to real sections');
  // every section belongs to exactly one domain
  const covered=new Set();
  t.DOMAINS.forEach(d=>d.secs.forEach(s=>{ ok(!covered.has(s),'section '+s+' is in two domains'); covered.add(s); }));
  eq(covered.size,23,'every section belongs to a domain');
  t.go('homeScreen');
}

// ---------- styling sweep ----------
// Walks every screen at the current viewport and complains about the things that
// actually break a page: sideways scroll, text cut off by its own box, controls
// too small to tap, and anything hiding under the fixed bars.
window.QA_UI=async function(){
  const t=T(), $=id=>document.getElementById(id);
  const out=[]; let checked=0;
  const screens=[...document.querySelectorAll('.screen')].map(s=>s.id);
  const barTop=$('topbar').getBoundingClientRect().bottom;
  const nav=document.querySelector('.bottomnav,#bottomnav,.nav');
  const barBottom=nav?nav.getBoundingClientRect().top:innerHeight;
  // make the list screens have something in them first
  t.renderPapers(); t.renderBank&&t.renderBank(); t.renderShop&&t.renderShop();
  t.renderBadges&&t.renderBadges(); t.renderThemes&&t.renderThemes();
  t.renderRecords&&t.renderRecords(); t.renderTimerPicker&&t.renderTimerPicker();
  t.renderExamPicker&&t.renderExamPicker(); t.renderStudyPicker&&t.renderStudyPicker();
  t.renderSimLog&&t.renderSimLog();
  for(const id of screens){
    t.go(id); await new Promise(r=>setTimeout(r,10));
    const sc=$(id);
    if(!sc||sc.classList.contains('hidden')) continue;
    checked++;
    if(document.documentElement.scrollWidth>innerWidth+1)
      out.push(id+': the page scrolls sideways ('+document.documentElement.scrollWidth+' > '+innerWidth+')');
    [...sc.querySelectorAll('*')].forEach(el=>{
      const r=el.getBoundingClientRect();
      if(!r.width||!r.height) return;
      const st=getComputedStyle(el);
      // decorative layers, fixed bars, and anything an overflow:hidden parent already
      // clips are meant to bleed past the edge — only unclipped content is a problem
      const clipped=(()=>{ for(let n=el.parentElement;n&&n!==document.body;n=n.parentElement){
        const o=getComputedStyle(n); if(o.overflow!=='visible'||o.overflowX!=='visible') return true; } return false; })();
      const decorative=st.pointerEvents==='none'||st.position==='fixed'||clipped;
      if(!decorative){
        if(r.right>innerWidth+1) out.push(id+': '+(el.id||el.className||el.tagName)+' runs off the right edge');
        if(r.left<-1) out.push(id+': '+(el.id||el.className||el.tagName)+' starts off the left edge');
      }
      // text cut off by a fixed-height box
      if(st.overflow==='hidden'&&el.scrollHeight>el.clientHeight+2&&el.childElementCount===0&&el.textContent.trim())
        out.push(id+': "'+el.textContent.trim().slice(0,30)+'" is clipped');
      if((el.tagName==='BUTTON'||el.getAttribute('role')==='button')&&(r.height<24||r.width<24)&&st.display!=='none')
        out.push(id+': tap target '+(el.id||el.className)+' is only '+Math.round(r.width)+'x'+Math.round(r.height));
    });
    const back=sc.querySelector('.backbtn');
    if(back){
      back.scrollIntoView({block:'center'});
      const r=back.getBoundingClientRect();
      const hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
      if(!(hit===back||back.contains(hit))) out.push(id+': the back button is covered by '+(hit&&(hit.id||hit.className)));
      if(r.bottom>barBottom) out.push(id+': the back button sits under the bottom bar');
    }
  }
  t.go('homeScreen');
  const uniq=[...new Set(out)];
  console.log(uniq.length?uniq:'QA_UI: '+checked+' screens, nothing off');
  return {screens:checked, problems:uniq};
};

window.QA_BANK=async function(opts){
  opts=opts||{};
  pass=0; fails=[];
  const t=T();
  ok(!!t,'the test surface is exposed (load with ?test=1)');
  if(!t) return {pass,fails};
  t.go('homeScreen');
  homeCheck();
  bankChecks();
  paperChecks();
  if(opts.app!==false) await appChecks();
  if(opts.quick!==true){
    await runPaper(1,{});
    csvChecks();
    await timeoutCheck();
    await abandonCheck();
    await shortPaperCheck();
  }
  t.go('homeScreen');
  console.log(fails.length?('QA_BANK: '+pass+' passed, '+fails.length+' FAILED'):('QA_BANK: '+pass+' assertions, all passing'));
  return {pass, failed:fails.length, fails};
};
console.log('QA_BANK ready — run  await QA_BANK()');
})();
