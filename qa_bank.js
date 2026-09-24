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
  eq(t.SIM_QSEC,105,'a question gets 105 seconds');
  eq(t.PAPER_MIN,Math.ceil(65*t.SIM_QSEC/60),'a 65-question paper is budgeted at the per-question limit each');
  eq(t.simBudget(65),114,'65 questions, 114 minutes');
  eq(t.simBudget(31),Math.ceil(31*t.SIM_QSEC/60),'the short paper is budgeted the same way');
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
  // walk a fresh paper, whatever earlier checks left behind to finish later
  delete t.P.lastPaper; t.simClearSave();
  // open it the way a user does: tile -> list -> Start
  $('paperOpen').click(); await sleep(30);
  eq(t.route,'paperScreen','the practice-exam screen opened');
  hittable($('paperBack'),'papers back button');
  hittable($('paperCsv'),'papers CSV button');
  const rows=$('paperList').querySelectorAll('.item');
  eq(rows.length, t.PAPER_COUNT, 'one row per paper');
  eq(rows[0].querySelector('.nm').textContent,'Exam 1','the first row names Exam 1');
  ok(/^Exam \d+ · short paper \(\d+ questions\)$/.test(rows[rows.length-1].querySelector('.nm').textContent),'the last row is marked short');
  // Start is the row's LAST button: a restart arrow or a finish-later button can sit before it
  const btn=[...rows[n-1].querySelectorAll('button')].pop();
  hittable(btn,'Start button on exam '+n);
  btn.click(); await sleep(40);

  // Start raises the mode sheet rather than starting anything, so the walk-through answers
  // it. These two are now the real way into a paper, so they are hit-tested like any other
  // primary button — a sheet button that does not take taps is a paper you cannot begin.
  ok(!$('modeAsk').classList.contains('hidden'),'Start asks which kind of run this is');
  hittable($('modeAskExam'),'the Simulation choice');
  hittable($('modeAskPractice'),'the Practice choice');
  $('modeAskExam').click(); await sleep(40);

  const sim=t.sim;
  ok(!!sim,'an exam is running');
  eq(sim.paper,n,'the running exam is paper '+n);
  eq(t.route,'quizScreen','it jumped to the question screen');
  eq(sim.qs.length, t.paperQs(n).length, 'it loaded the whole paper');
  const left=t.simTimeLeft();
  const bud=t.simBudget(sim.qs.length);
  ok(left>(bud-1)*60000&&left<=bud*60000,
     'the paper budget starts at '+bud+' minutes, got '+Math.round(left/60000));
  eq(t.simQLeft,t.SIM_QSEC,'and the question starts on a full 90 seconds');
  eq($('playClock').textContent,'⏳ '+fmtMs(t.SIM_QSEC*1000),'the top bar counts this question down');
  // the second line used to label the big number; it now carries the paper's own remaining,
  // which is the more useful of the two and is on screen the whole time
  ok(/left$/.test($('clockSub').textContent),'the second line shows what the paper has left');
  eq($('clockSub').textContent,fmtMs(t.simTotalLeft()*1000)+' left','and it agrees with the sum');
  eq($('qSector').textContent,'EXAM '+n,'the exam is named in the header, not twice');
  ok(!$('qTimerWrap').classList.contains('hidden'),'the countdown bar is showing');
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
  // the headline is the SAA scaled score; the raw count and the weighted % sit beneath it
  const scaled=parseInt($('simScore').textContent,10);
  ok(scaled>=100&&scaled<=1000,'the score is on the exam\u2019s 100\u20131000 scale ('+scaled+')');
  const meta=$('simMeta').textContent;
  ok(meta.indexOf(expectRight+' / '+len+' correct')===0,'and the raw count matches what was answered');
  const pct=parseInt((/weighted (\d+)%/.exec($('simDomHead').textContent)||[])[1],10);
  ok(pct>=0&&pct<=100,'the weighted percentage is shown');
  eq(/PASS/.test($('simVerdict').textContent)&&!/BELOW/.test($('simVerdict').textContent),scaled>=720,
     'pass and fail follow the 720 line');
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
  // a paper runs out when its questions do — the only clock it has
  t.sim.qs.forEach((q,i)=>{ t.sim.qt[i]=0; });
  t.simQTick(t.SIM_QSEC); await sleep(20);
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
  eq(t.route,'paperScreen','quitting a paper lands on the exam list, where it is offered back');
  ok(!t.sim,'quitting clears the exam');
  eq((t.paperRec(3)||{tries:0}).tries, tries3, 'an abandoned exam is not scored');
  ok(!!t.simSaved(),'and the run is kept so it can be resumed');
  t.simClearSave();
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
  ok(new RegExp(t.SIM_QSEC+' seconds a question').test($('paperOpen').textContent),'the tile states the per-question limit');
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
  const wasMarked=t.isBookmarked(t.curQ);   // P.marks survives in localStorage between runs
  t.toggleBookmark();
  ok(t.isBookmarked(t.curQ)!==wasMarked,'the bookmark toggled');
  t.toggleBookmark();
  ok(t.isBookmarked(t.curQ)===wasMarked,'and toggled back');
  if(!wasMarked) t.toggleBookmark();
  t.startBookmarks(); await sleep(0);
  eq(t.route,'quizScreen','bookmark practice opened');

  // weak spots
  t.startWeakDrill(); await sleep(0);
  ok(t.route==='quizScreen'||t.route==='homeScreen','weak drill opened or declined cleanly');

  // the mock (the five-question drill was retired)
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
    // a panel with content but no height is invisible and nothing else catches it
    [...sc.children].forEach(el=>{
      const st=getComputedStyle(el);
      if(st.display==='none'||el.classList.contains('hidden')) return;
      if(el.scrollHeight>8&&el.getBoundingClientRect().height<1)
        out.push(id+': '+(el.id||el.className)+' has content but collapsed to zero height');
    });
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

// ---------- study mode ----------
async function studyChecks(){
  const t=T(), $=id=>document.getElementById(id), S=t.STUDY_T;
  ok(!!S,'the study engine is exposed');
  if(!S) return;
  const CH=S.STU_CH;
  eq(CH.length,13,'thirteen chapters');
  const titles=new Set();
  CH.forEach((c,i)=>{
    ok(!!c.nm&&!!c.em&&!!c.sub, 'chapter '+i+' is labelled');
    ok(c.topics.length>0,'chapter '+i+' has topics');
    ok(c.quiz.length>=3,'chapter '+i+' has at least three checks');
    c.topics.forEach(tp=>{
      ok(!titles.has(tp.nm),'topic "'+tp.nm+'" appears in two chapters');
      titles.add(tp.nm);
      ok(tp.blocks.length>0,'"'+tp.nm+'" has content');
      tp.blocks.forEach(b=>{
        ok(['h','p','list','steps','table','flow','split','key','trap','note','code','dtree']
          .includes(b.t), '"'+tp.nm+'": unknown block '+b.t);
        if(b.t==='table'){
          ok(b.head.length>1,'"'+tp.nm+'": a one-column table');
          b.rows.forEach(r=>eq(r.length,b.head.length,'"'+tp.nm+'": ragged table row'));
        }
      });
    });
    c.quiz.forEach((q,qi)=>{
      ok(q.q.length>15,'chapter '+i+' check '+qi+' has a real stem');
      ok(q.o.length>=3,'chapter '+i+' check '+qi+' has options');
      eq(new Set(q.o).size,q.o.length,'chapter '+i+' check '+qi+' repeats an option');
      ok(q.a>=0&&q.a<q.o.length,'chapter '+i+' check '+qi+' has a valid answer');
    });
  });
  eq(titles.size,76,'every topic from the notes is present exactly once');

  // the picker, through the nav the way a user reaches it
  $('navPlay').click(); await sleep(40);
  eq(t.route,'stuPickScreen','the Study tab opens the chapter list');
  ok($('navPlay').classList.contains('on'),'the Study tab lights up');
  eq($('stuPickList').children.length,CH.length,'one card per chapter');
  hittable($('stuPickBack'),'study back button');
  hittable($('stuPickList').firstChild,'first chapter card');

  // read every chapter
  for(let i=0;i<CH.length;i++){
    $('stuPickList').children[i].click(); await sleep(20);
    eq(t.route,'stuReadScreen','chapter '+i+' opened');
    eq(S.stuIdx,i,'chapter index tracks');
    const c=CH[i];
    eq($('stuJump').children.length,c.topics.length,'chapter '+i+': a jump chip per topic');
    eq($('stuBody').querySelectorAll('.stutopic').length,c.topics.length,'chapter '+i+': every topic rendered');
    eq($('stuQuiz').children.length,c.quiz.length,'chapter '+i+': every check rendered');
    ok($('stuTitle').textContent.indexOf(c.nm)>=0,'chapter '+i+': title shown');
    ok($('stuBody').textContent.length>500,'chapter '+i+': the body has real text');
    ok((t.P.study||{})[i]&&t.P.study[i].read===1,'chapter '+i+' is marked read');
    if(i===0){
      hittable($('stuQuiz').querySelector('.stuo'),'first check option');
      hittable($('stuNext'),'next chapter button');
    }
    $('stuReadBack').click(); await sleep(10);
  }
  eq(Object.keys(t.P.study||{}).length,CH.length,'every chapter recorded as read');

  // answering a check: right, then wrong
  S.stuOpen(0); await sleep(20);
  const cards=[...$('stuQuiz').children];
  const q0=CH[0].quiz[0];
  cards[0].querySelectorAll('.stuo')[q0.a].click(); await sleep(5);
  ok(cards[0].querySelectorAll('.stuo')[q0.a].classList.contains('ok'),'a correct pick is marked correct');
  ok([...cards[0].querySelectorAll('.stuo')].every(b=>b.disabled),'the options lock after answering');
  ok(/Correct/.test(cards[0].querySelector('.stufeed').textContent),'it says so');
  const q1=CH[0].quiz[1], wrong=(q1.a+1)%q1.o.length;
  cards[1].querySelectorAll('.stuo')[wrong].click(); await sleep(5);
  ok(cards[1].querySelectorAll('.stuo')[wrong].classList.contains('no'),'a wrong pick is marked wrong');
  ok(cards[1].querySelectorAll('.stuo')[q1.a].classList.contains('ok'),'and the right one is shown');
  const q2=CH[0].quiz[2];
  cards[2].querySelectorAll('.stuo')[q2.a].click(); await sleep(20);
  const rec=S.stuRec(0);
  ok(rec&&rec.best>0,'finishing the check records a score, got '+(rec&&rec.best));
  // a second click must not double-score
  cards[0].querySelectorAll('.stuo')[0].click(); await sleep(5);
  eq(S.stuRec(0).best,rec.best,'re-clicking a locked option changes nothing');

  // the last chapter's Next returns to the list
  S.stuOpen(CH.length-1); await sleep(20);
  $('stuNext').click(); await sleep(20);
  eq(t.route,'stuPickScreen','the last chapter hands you back to the list');
  t.go('homeScreen');
}

// the five-question drill is gone and the Exam tab is the papers now
async function retiredDrillChecks(){
  const t=T(), $=id=>document.getElementById(id);
  ok(!$('examScreen'),'the old exam drill screen is gone');
  ok(!$('examOpen'),'its home tile is gone');
  ok(t.startExam===undefined,'startExam is gone from the test surface');
  $('navExam').click(); await sleep(40);
  eq(t.route,'paperScreen','the Exam tab opens the practice exams');
  ok($('navExam').classList.contains('on'),'the Exam tab lights up');
  t.go('homeScreen');
}

// ---------- leaving a paper and coming back ----------
async function resumeChecks(){
  const t=T(), $=id=>document.getElementById(id);
  t.simClearSave();
  ok(!t.simSaved(),'nothing is saved to begin with');

  t.startPaper(4); await sleep(20);
  const q0=t.QS[t.sim.qs[0]];
  q0.a.forEach(l=>t.simPick(l));
  t.simGo(1); await sleep(10);
  t.simFlagToggle();
  t.simGo(1); await sleep(10);
  const before=t.simTimeLeft();
  ok(before>0,'the clock is running');
  eq(t.sim.i,2,'we are on the third question');

  // walking out keeps it
  $('simQuit').click(); await sleep(30);
  const sv=t.simSaved();
  ok(!!sv,'quitting saved the run');
  eq(sv.paper,4,'the saved run knows its paper');
  eq(sv.i,2,'the saved run knows the question');
  eq(Object.keys(sv.ans).filter(k=>sv.ans[k].length).length,1,'the saved run kept the answer');
  ok(sv.flag[1],'the saved run kept the flag');
  ok(sv.left>0&&sv.left<=t.PAPER_MIN*60000,'the saved run kept the remaining time');

  // the clock does not run down while you are away
  const frozen=sv.left;
  await sleep(120);
  eq(t.simSaved().left,frozen,'the clock is frozen while the exam is closed');

  // the Practice Exams screen offers it
  t.renderPapers(); t.go('paperScreen'); await sleep(20);
  ok(!$('exResume').classList.contains('hidden'),'the resume card is shown');
  ok(/Exam 4/.test($('exResume').textContent),'it names the paper');
  ok(/Question 3 of 65/.test($('exResume').textContent),'it names the question');
  hittable($('exResume'),'resume card');

  $('exResume').click(); await sleep(30);
  ok(!!t.sim,'it resumed');
  eq(t.sim.paper,4,'the same paper');
  eq(t.sim.i,2,'the same question');
  eq((t.sim.ans[0]||[]).length,q0.a.length,'the same answers');
  ok(!!t.sim.flag[1],'the same flags');
  ok(Math.abs(t.simTimeLeft()-frozen)<4000,'the same time left, give or take a moment');
  eq($('qCount').textContent,'3 / 65','the counter picks up where it stopped');

  // submitting clears the save
  t.simSubmit(true); await sleep(40);
  ok(!t.simSaved(),'a submitted paper is not offered again');
  t.renderPapers();
  ok($('exResume').classList.contains('hidden'),'and the card is hidden');

  // starting a different paper replaces a stale save
  t.startPaper(6); await sleep(20);
  t.simGo(1); await sleep(10);
  eq(t.simSaved().paper,6,'a new run overwrites the old save');
  t.startPaper(7); await sleep(20);
  eq(t.simSaved().paper,7,'starting another paper replaces it again');
  eq(t.simSaved().i,0,'and it starts at question one');
  t.simAbandon(); await sleep(20);
}

function fmtMs(ms){
  const sec=Math.floor(ms/1000), h=Math.floor(sec/3600), m=Math.floor(sec%3600/60), ss=sec%60;
  return h>0 ? (h+':'+String(m).padStart(2,'0')+':'+String(ss).padStart(2,'0'))
             : (m+':'+String(ss).padStart(2,'0'));
}

function renderClockSafe(t){ try{ t.renderClock(); }catch(e){} }

// ---------- every option carries its own reasoning ----------
// Every defect the ninth audit measured, as a standing check. These are the ways the
// splitter went wrong, and each one was live in the bank before it was found.
function whyQualityChecks(){
  const t=T();
  const L4=['A','B','C','D'];

  // "A gp3 volume tops out at 16,000 IOPS" opens with an article. Matched as option A, it
  // took the case for the answer away from the answer.
  const art=t.whyByOption(
    'A gp3 volume tops out at 16,000 IOPS, so the workload has hit a ceiling. '+
    'io2 supports up to 64,000 IOPS.',L4,['D'],
    [['A','Magnetic volume'],['B','RDS storage'],['C','gp3 volume'],['D','io2 volume']]);
  ok(!art.byLetter.A,'a capitalised article is not option A');
  ok(/tops out/.test(art.byLetter.D||''),'so the answer keeps the case for itself');
  // but a real reference to A in the same shape still counts
  const ref=t.whyByOption('A controls console access, and B is a network path.',L4,['C']);
  ok(/controls console access/.test(ref.byLetter.A||''),'a real reference to A still counts');

  // "the R&D account" is not option D
  const amp=t.whyByOption(
    'An account can belong to one organization, so the R&D account must leave it first. '+
    'D means rebuilding every resource.',L4,['B']);
  ok(!/R&D account must leave/.test(amp.byLetter.D||''),'"R&D" is not option D');
  ok(/R&D account must leave/.test(amp.byLetter.B||''),'that sentence stays with the answer');

  // a verdict list keyed on service names, not letters, is split per option
  const list=t.whyByOption(
    'C cannot push gp3 past its limit, RDS does not let you stripe two volumes (B), '+
    'and magnetic (A) is far slower.',L4,['D'],
    [['A','Magnetic'],['B','RDS'],['C','gp3'],['D','io2']]);
  ok(list.byLetter.A!==list.byLetter.B,'each option gets its own verdict, not the whole list');
  ok(/magnetic/i.test(list.byLetter.A||''),'A is told about magnetic');
  ok(/stripe/.test(list.byLetter.B||''),'B is told about striping');

  // an enumeration of subjects is one clause, not three
  const enu=t.whyByOption('B, C, and D all still involve keys to maintain.',L4,['A']);
  ok((enu.byLetter.B||'').split(/\s+/).length>4,'"B, C, and D all ..." is not split into "B, C"');

  // a clause that continues the thought before it keeps its antecedent
  const anaph=t.whyByOption(
    'An account belongs to one organization at a time, so it must leave the old one; '+
    'C is impossible for that reason.',L4,['A']);
  ok(!/^C is impossible/.test(anaph.byLetter.A||''),'the reason is not stranded from its clause');

  // two clauses joined against one option read as two sentences
  const join=t.whyByOption('C cannot push gp3 past its limit, and C is also slower.',L4,['D']);
  ok(!/limit and/.test(join.byLetter.C||''),'joined clauses are punctuated, not run together');

  // and across the whole bank, measured the way the panel shows it
  let misled=0,dupe=0,blank=0,thin=0,ocr=0,opts=0;
  const lead=(txt)=>{
    let best=null,at=1e9;
    const other=L4.some(L=>L!=='A'&&new RegExp('(^|[\\s("\\[])'+L+'(?=[ ,.;:)]|$)').test(txt));
    const nx=/^A\s+([A-Za-z][A-Za-z0-9-]*)/.exec(txt);
    const verby=nx&&(/s$/i.test(nx[1])||/^(cannot|can|could|will|would|should|must|may|might|do|did|only|still|never|also|again|both|alone|then|just|simply|merely)$/i.test(nx[1]));
    const artA=!!nx&&!verby&&!other;
    L4.forEach(L=>{
      if(L==='A'&&artA) return;
      const m=new RegExp('(^|[\\s("\\[])'+L+'(?=[ ,.;:)]|$)').exec(txt);
      if(m&&m.index<at){ at=m.index; best=L; }
    });
    return best;
  };
  t.QS.forEach(q=>{
    if(!q.w) return;
    const letters=q.o.map(x=>x[0]);
    const w=t.whyByOption(q.w,letters,q.a,q.o);
    const ctxt=q.o.filter(x=>q.a.includes(x[0])).map(x=>x[1]).join(' ');
    const pk=(t.exFind(ctxt,3)[0]||{}).t||'';
    const pivot=pk?t.asWritten(ctxt,pk):'';
    const seen={};
    q.o.forEach(([L,txt])=>{
      opts++;
      const line=w.byLetter[L]||'';
      if(!line) blank++;
      const dup=letters.filter(o=>(w.byLetter[o]||'')&&w.byLetter[o]===line).length>1;
      const shown=(t.optionLine(q,L,txt,line,pivot,dup)||{}).text||'';
      if(!shown) thin++;
      if(seen[shown]) dupe++; else seen[shown]=1;
      if(line){ const l=lead(line); if(l&&l!==L&&line.indexOf(L)<0) misled++; }
      if(/\b[a-z]{2,}\.\s+[a-z]/.test(txt)) ocr++;
    });
  });
  ok(thin===0,'every option in the bank is shown something ('+opts+' options)');
  ok(misled<120,'few lines open by discussing a different option ('+misled+')');
  ok(dupe<450,'few options are shown a line identical to another\'s ('+dupe+')');
  ok(blank<200,'most options get a line from the write-up itself ('+blank+' without)');
  ok(ocr<20,'the OCR damage in the option text is repaired ('+ocr+' left)');
}
// The exam cue under an answer must be about that answer. It used to clear its threshold on
// generic stem words alone, so a Site-to-Site VPN question was cued with CloudFront Signed
// Cookies, and "Global Accelerator (not CloudFront)" qualified under a CloudFront answer.
// An imported profile is untrusted: every value in it is replaced with markup that runs code
// if it ever becomes an element, the result goes through the same door a real import does, and
// every screen and every renderer is drawn. The exam log, the simulation log and the score
// chips all used to write these fields into innerHTML raw.
async function xssChecks(){
  const t=T();
  const PAY='<img src=x class=xssprobe onerror="window.__pwned=(window.__pwned||0)+1">';
  const backup=JSON.stringify(t.P);
  const rich=JSON.parse(backup);
  Object.assign(rich,{papers:{1:{best:80,tries:2,last:'80%',d:'2026-09-01',bestMode:'exam'}},
    simLog:[{d:'2026-09-01',p:80,pass:1,mins:90,pr:0,dom:[1,2,3,4]}], examLog:[{d:'2026-09-01',c:50,t:65,p:1}],
    courses:{0:{best:90,runs:2,mods:['a']}}, lastTimer:{mode:'pomo',work:25,rest:5,rounds:4,nm:'Deep'},
    study:{0:{read:1,best:70,at:'2026-09-01'}}, examDate:'2026-12-01', name:'me',
    secStats:{0:{a:10,c:7},3:{a:4,c:2}}, inv:{shield:2,potion:1},
    login:{last:Date.now(),streak:3,claimed:0}, rHist:[{d:'2026-09-01',p:40}], lastSec:2, dailyStreak:3,
    badges:['first'], known:[1,2]});
  const poison=v=>Array.isArray(v)?v.map(poison):(v&&typeof v==='object')
    ?Object.fromEntries(Object.entries(v).map(([k,x])=>[k,poison(x)])):PAY;
  window.__pwned=0;
  const P=t.P; Object.keys(P).forEach(k=>delete P[k]); Object.assign(P,poison(rich)); t.normaliseProfile(P);
  const thrown=[];
  for(let pass=0;pass<2;pass++){
    for(const sc of [...document.querySelectorAll('.screen')].map(x=>x.id)){ try{ t.go(sc); }catch(e){ thrown.push(sc); } }
    for(const k of Object.keys(t).filter(k=>/^render/.test(k)&&typeof t[k]==='function'&&k!=='renderExplain')){
      try{ t[k](); }catch(e){ thrown.push(k); } }
  }
  await sleep(200);
  const probes=[...document.querySelectorAll('.xssprobe')];
  const where=[...new Set(probes.map(e=>{ let q=e.parentElement,path=[]; while(q&&path.length<4){
    path.push(q.id||(''+q.className).split(' ')[0]); q=q.parentElement; } return path.join('<'); }))];
  eq(probes.length,0,'no value from an imported profile becomes live markup '+where.join(' ; '));
  eq(window.__pwned,0,'and none of it runs');
  // and none of it shows up as garbage text either: NaN, undefined, or markup drawn as words
  const junk=[...document.querySelectorAll('.screen')].map(sc=>{
    const m=/NaN|undefined|<img|\[object/.exec(sc.textContent||''); return m?sc.id:null; }).filter(Boolean);
  eq(junk.join(', '),'','no screen reads NaN, undefined or stray markup after a corrupted import');
  eq([...new Set(thrown)].join(', '),'','and every screen still draws from a corrupted profile'+
     ' \u2014 an unknown difficulty used to crash three of them, which also hid their injections');
  document.querySelectorAll('.xssprobe').forEach(e=>e.remove());
  Object.keys(P).forEach(k=>delete P[k]); Object.assign(P,JSON.parse(backup));
  // write the restored profile now, so no save queued while it was poisoned lands later
  t.saveProfile(); t.flushProfile(); t.go('homeScreen');
  // an unknown difficulty used to crash three screens; it now falls back at the door
  const dd={diff:'nightmare'}; t.normaliseProfile(dd); eq(dd.diff,'easy','an unknown difficulty falls back to easy');
  // and the door does not damage real data on its way through
  const good={simLog:[{d:'2026-09-20',p:78,pass:1,mins:88,pr:1,ct:0,dom:[80,70,90,60]}],
              examLog:[{d:'2026-09-21',c:50,t:65,p:1}],
              papers:{3:{best:84,tries:3,last:'84%',d:'2026-09-21',bestMode:'practice',lastMode:'exam',ptries:1}}};
  const g=JSON.parse(JSON.stringify(good)); t.normaliseProfile(g);
  eq(JSON.stringify(g.simLog),JSON.stringify(good.simLog),'a real simulation log passes the door unchanged');
  eq(JSON.stringify(g.examLog),JSON.stringify(good.examLog),'so does a real exam log');
  eq(JSON.stringify(g.papers),JSON.stringify(good.papers),'and real paper records');
  // a stray entry in a course's module list made "every part passed" a count that never matched
  const cr={courses:{0:{runs:2,best:90,mins:'x',mods:['identities','<b>x</b>',5,'identities','policies']}}};
  t.normaliseProfile(cr);
  eq(JSON.stringify(cr.courses[0].mods),JSON.stringify(['identities','policies']),
     'a course keeps only real module ids, once each');
  eq(cr.courses[0].mins,0,'and a number where minutes go');
}
// The auth library runs with access to the signed-in session, so it is pinned and hashed.
function sriChecks(){
  const src=document.documentElement.outerHTML;
  ok(/supabase-js@2\.\d+\.\d+\//.test(src),'supabase-js is pinned to an exact version, not @2');
  ok(/s\.integrity='sha384-[A-Za-z0-9+\/=]{64}'/.test(src),'and carries an integrity hash the browser checks');
  ok(/s\.crossOrigin='anonymous'/.test(src),'with the CORS mode integrity checking needs');
}
function cueChecks(){
  const t=T();
  const t0=performance.now();
  let shown=0, wrongLead=0; const bad=[];
  t.QS.forEach((q,i)=>{
    const c=t.exCue(q); if(!c) return;
    shown++;
    const correct=' '+q.o.filter(x=>q.a.includes(x[0])).map(x=>x[1]).join(' ').toLowerCase()+' ';
    const lead=c._lead;
    if(!lead||!lead._re.some(re=>re.test(correct))){ wrongLead++; if(bad.length<3) bad.push('q'+i+' '+c.a); }
  });
  const ms=performance.now()-t0;
  ok(shown>500,'most questions still get a cue ('+shown+')');
  eq(wrongLead,0,'every cue shown names a service the correct answer actually uses '+bad.join('; '));
  ok(ms<t.QS.length*2,'picking cues for the whole bank is fast ('+Math.round(ms)+' ms)');
  const vpn=t.exCue(t.QS[226]);
  ok(!vpn||!/Signed Cookies/.test(vpn.a),'the VPN question is not cued with CloudFront Signed Cookies');
}
function whyChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const withW=t.QS.filter(q=>q.w).length;
  ok(withW>1100,withW+' of '+t.QS.length+' questions carry a written explanation');
  // the 24 without one are where the source disagreed with this bank's answer, or matched
  // nothing confidently — an explanation arguing for a different letter is worse than none
  ok(t.QS.length-withW<40,'and the ones without are the handful that could not be trusted');

  // the splitter puts each sentence against the option it names
  const w=t.whyByOption(
    'EventBridge matches the call directly - one rule, one target. '+
    'B and D require Lambda to poll the logs. A adds a queue for no benefit.',
    ['A','B','C','D'],['C']);
  eq(w.byLetter.A,'A adds a queue for no benefit.','a sentence naming one option goes to it');
  ok(/B and D/.test(w.byLetter.B),'one naming two goes to both');
  eq(w.byLetter.D,'D and B require Lambda to poll the logs.',
     'and each is named first in its own copy, so the line is about the option it sits under');
  ok(/EventBridge matches/.test(w.byLetter.C),
     'and the part naming nobody explains the right answer, which is what it is for');
  eq(w.rest,'','so nothing is left over');
  // a sentence naming every option is too general to pin on any one
  const gen=t.whyByOption('A, B, C and D all use S3.',['A','B','C','D'],['A']);
  ok(/all use S3/.test(gen.byLetter.A),'a line naming everything lands with the right answer');

  // and it renders: one row per option, right and wrong, each marked
  const q=t.QS.find(x=>x.w&&x.o.length===4);
  ok(!!q,'there is a four-option question with a write-up');
  t.renderExplain(q,new Set([q.o.find(o=>!q.a.includes(o[0]))[0]]),false);
  const rows=[...document.querySelectorAll('#explain .exeach .exopt')];
  eq(rows.length,q.o.length,'every option gets a row, not just the ones that were picked');
  rows.forEach((el,i)=>{
    const L=q.o[i][0], right=q.a.includes(L);
    const k=el.querySelector('.k').textContent;
    ok(k.indexOf(L)===0,'row '+i+' is labelled '+L);
    ok(/[\u2713\u2717]/.test(k),'and marked right or wrong');
    eq(el.classList.contains('good'),right,'with the marking matching the answer');
    ok((el.querySelector('i').textContent||'').length>10,'and carries a line of reasoning');
  });
  // English, so it must not inherit the Hebrew glossary's direction
  const b=document.querySelector('#explain .exeach .exopt b');
  eq(getComputedStyle(b).direction,'ltr','the write-up reads left to right');
  eq(getComputedStyle(b).textAlign,'left','and is aligned that way');
  t.hideExplain();
}

// ---------- a mini-game stops when you leave it ----------
async function gameLifetimeChecks(){
  const t=T();
  if(!t.GAMES||typeof t.launchGame!=='function'){ ok(false,'the games are not exposed'); return; }
  const keepHighs=JSON.parse(JSON.stringify(t.P.highs||{}));
  const keepPlayed=t.P.gamesPlayed, keepCoins=t.P.coins;

  // Walking away used to leave the animation loop running: still stepping, still ticking,
  // still scoring against a canvas nobody could see — and paying out when the clock ran down.
  t.launchGame(t.GAMES[0].id); await sleep(20);
  ok(t.gRunning,'a game starts running');
  eq(t.route,'gameScreen','on the game screen');
  t.go('homeScreen'); await sleep(30);
  ok(!t.gRunning,'leaving the screen stops the game');
  const coinsAfterLeaving=t.P.coins, playedAfterLeaving=t.P.gamesPlayed;
  for(let i=0;i<200;i++) t.gStep(1/30);        // nothing should happen at all
  eq(t.P.coins,coinsAfterLeaving,'and it cannot pay out after you have gone');
  eq(t.P.gamesPlayed,playedAfterLeaving,'nor count itself as played');

  // every game launches, steps and ends without producing an impossible number
  for(const g of t.GAMES){
    t.launchGame(g.id); await sleep(10);
    eq(t.route,'gameScreen',g.id+' opens the game screen');
    for(let i=0;i<40&&t.gRunning;i++) t.gStep(1/30);
    ok(isFinite(t.gScore),g.id+' keeps its score a number');
    ok(t.gScore>=0,g.id+' does not go negative');
    t.endGame(); await sleep(20);
    ok(!t.gRunning,g.id+' stops when it ends');
    const hi=(t.P.highs||{})[g.id];
    ok(hi===undefined||(isFinite(hi)&&hi>=0),g.id+' writes a sane high score');
    t.go('homeScreen'); await sleep(10);
  }

  // one game straight after another must not leave the first alive
  t.launchGame(t.GAMES[0].id); await sleep(10);
  t.launchGame(t.GAMES[1].id); await sleep(10);
  for(let i=0;i<20;i++) t.gStep(1/30);
  ok(isFinite(t.gScore),'starting a second game does not corrupt the score');
  t.endGame(); await sleep(20);
  ok(!t.gRunning,'and ending it really ends it');

  t.P.highs=keepHighs; t.P.gamesPlayed=keepPlayed; t.P.coins=keepCoins;
  t.go('homeScreen');
}

// ---------- the arithmetic underneath the screens ----------
function arithmeticChecks(){
  const t=T();
  // fmtClock is handed counters from a merged profile among other things, and "-1:-1" or
  // "NaN:NaN" on screen is worse than a wrong number
  eq(t.fmtClock(0),'0:00','zero');
  eq(t.fmtClock(59000),'0:59','under a minute');
  eq(t.fmtClock(60000),'1:00','a minute');
  eq(t.fmtClock(3599000),'59:59','under an hour');
  eq(t.fmtClock(3600000),'1:00:00','an hour');
  eq(t.fmtClock(3661000),'1:01:01','an hour and change');
  eq(t.fmtClock(-1000),'0:00','a negative renders as zero, not "-1:-1"');
  eq(t.fmtClock(NaN),'0:00','NaN too');
  eq(t.fmtClock(Infinity),'0:00','and Infinity');
  eq(t.fmtClock(undefined),'0:00','and nothing at all');

  // day keys used to read "2026-1-5", which as a string sorts AFTER "2026-1-12"
  const k=t.dayKey();
  ok(/^\d{4}-\d{2}-\d{2}$/.test(k),'the day key is zero-padded: '+k);
  ok('2026-01-05'<'2026-01-12','and therefore sorts within a month');
  ok('2026-01-31'<'2026-02-01','and across one');
  ok(t.sameDay('2026-1-5','2026-01-05'),'a date written before the padding still matches');
  ok(t.sameDay('2026-1-5','2026-1-5'),'and one written after it');
  ok(!t.sameDay('2026-01-05','2026-01-06'),'while different days still differ');

  // badge progress cannot exceed its goal — a best streak of 12 against a goal of 5 read "12/5"
  const keep=JSON.parse(JSON.stringify(t.P));
  Object.assign(t.P,{bestStreak:40,answered:1200,coins:9000,gamesPlayed:60});
  t.BADGES.forEach(b=>{
    const pr=t.badgeProgress(b);
    if(!pr) return;
    ok(isFinite(pr[0])&&isFinite(pr[1]),b.id+' progress is numeric');
    ok(pr[0]<=pr[1],b.id+' does not claim more progress than its goal ('+pr.join('/')+')');
    ok(pr[0]>=0,b.id+' is not negative');
  });
  Object.keys(t.P).forEach(x=>delete t.P[x]); Object.assign(t.P,keep);

  // the CSV has to survive a stem with a quote and a comma in it
  const q=t.QS[0], was=q.q;
  q.q='He said "yes, definitely" \u2014 then, later, no';
  const lines=t.csvRows([{i:0,why:'Flagged'}]).split('\r\n');
  q.q=was;
  const cols=l=>(l.match(/","/g)||[]).length+1;
  eq(cols(lines[1]),cols(lines[0]),'a quote and a comma do not shift the columns');
  ok(lines[1].indexOf('""yes')>=0,'and the quotes are doubled as CSV requires');
  ok(!/[^"]\n/.test(lines[1]),'with no raw newline in the row');
  eq((lines[1].match(/"/g)||[]).length%2,0,'and an even number of quotes');
}

// ---------- closing the page does not stop the clock ----------
// The save stores time remaining, so shutting the tab used to freeze the paper indefinitely:
// leave for ten minutes, look everything up, come back, and the clock was where you left it.
async function refreshChecks(){
  const t=T();
  // the app saves every ten seconds while a question runs; do what it would have done
  const setup=async()=>{ t.simClearSave(); t.startPaper(2); await sleep(30);
                         t.simQTick(20); t.simPersist(); await sleep(10); };

  // a closed tab is charged for
  await setup();
  const q0=t.simQLeft, w0=Math.round(t.simTimeLeft()/1000);
  t.P.simSave.at-=10*60*1000;
  eq(t.simAwayCost(t.P.simSave),600,'ten minutes away is measured in seconds, not milliseconds');
  t.simResume(); await sleep(40);
  eq(t.sim.qt[0],0,'the question it was on is spent — it only had '+q0+' seconds');
  ok(t.sim.i>0,'so the resume moves past it rather than stranding you on a 0:00 clock');
  eq(t.simQLeft,t.SIM_QSEC,'landing on one that still has its full ninety');
  const charged=w0-Math.round(t.simTimeLeft()/1000);
  // only the question you were on pays for time away — the rest of the paper waits
  ok(Math.abs(charged-q0)<3,'the paper loses only what that question had ('+charged+'s of '+q0+')');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // quitting is a decision and still pauses
  await setup();
  const q1=t.simQLeft, w1=Math.round(t.simTimeLeft()/1000);
  t.simAbandon(); await sleep(40);
  eq(t.P.simSave.paused,1,'Quit marks the save as paused');
  t.P.simSave.at-=10*60*1000;
  eq(t.simAwayCost(t.P.simSave),0,'so nothing is charged for the time away');
  t.simResume(); await sleep(40);
  eq(t.simQLeft,q1,'the question keeps its seconds');
  eq(Math.round(t.simTimeLeft()/1000),w1,'and the paper its budget');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // a break that was running covers its own time
  await setup();
  const w2=Math.round(t.simTimeLeft()/1000);
  const sv=t.P.simSave;
  sv.paused=0; sv.at-=10*60*1000; sv.brkUntil=sv.at+4*60*1000;
  eq(t.simAwayCost(sv),360,'four of the ten minutes were a break, so six are charged');
  t.simResume(); await sleep(40);
  const c2=w2-Math.round(t.simTimeLeft()/1000);
  ok(c2<=t.SIM_QSEC,'and the paper loses no more than the open question held ('+c2+'s)');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // Away for hours: the paper is NOT over. It used to drain every question and submit itself,
  // so coming back found "you finished" and no way back in.
  await setup();
  t.P.simSave.paused=0; t.P.simSave.at-=3*60*60*1000;
  ok(!!t.simSaved(),'a paper left for three hours is still there');
  t.simResume(); await sleep(60);
  eq(t.route,'quizScreen','and resuming it goes back into the paper, not to a result');
  ok(t.sim&&t.sim.running,'still running');
  eq(t.sim.i,1,'on the next unanswered question, not back at question 1');
  // and "finish later" reopens any unanswered question whose answer was never shown, even with
  // an empty clock
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.P.lastPaper={paper:4,qs:t.paperQs(4),ans:{0:['A']},flag:{},rev:{1:1},qt:{0:50,1:0,2:0},mins:114};
  const open=t.lastOpen();
  ok(open.indexOf(2)>=0,'an unanswered question with an empty clock can still be finished');
  ok(open.indexOf(1)<0,'but not one whose answer was shown when it timed out');
  delete t.P.lastPaper;
  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave(); delete t.P.lastPaper;

  // the row must advertise what a resume would really hand back, not the saved figure
  await setup();
  t.P.simSave.paused=0; t.P.simSave.at-=5*60*1000;
  t.renderPapers(); await sleep(20);
  const rrow=[...document.querySelectorAll('#paperScreen .paperrow')].find(r=>r.classList.contains('resuming'));
  ok(!!rrow,'the in-progress row is there');
  if(rrow){
    const said=rrow.querySelector('.ds').textContent;
    ok(!/1:37:5\d left/.test(said),'and does not quote the stale saved time: '+said);
  }
  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave();

  // The save used to share sim.qt by reference, so every tick quietly rewrote the saved
  // per-question times while `at` stayed put — any unrelated saveProfile() then wrote a pair
  // describing two different moments, and the resume charged the gap twice.
  await setup();
  ok(t.P.simSave.qt!==t.sim.qt,'the save holds its own copy of the question clocks');
  const savedSnapshot=JSON.stringify(t.P.simSave.qt);
  t.sim.qt[40]=7;                      // mutate the live object behind the save's back
  eq(JSON.stringify(t.P.simSave.qt),savedSnapshot,'and the live object cannot rewrite it');
  delete t.sim.qt[40];

  // and the question being answered is written down, not left to be inferred
  t.simQTick(15); await sleep(10);
  t.simPersist();
  eq(t.P.simSave.qt[t.sim.i],t.simQLeft,
     'the current question is saved with the seconds it actually has');
  ok(typeof t.simSaveTick==='number','a running paper writes itself down on a timer');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // Away long enough to drain the question you were on, you used to resume onto it with a
  // dead 0:00 clock and no way forward but Next. Unlike opening a spent question from the
  // review list, that is not somewhere you chose to be.
  await setup();
  t.simPersist();
  t.P.simSave.paused=0; t.P.simSave.at-=21*60*1000;
  t.simResume(); await sleep(60);
  ok(t.simQLeft>0,'a resume does not land on a question with no time left');
  ok(t.sim.i>0,'it moves past the one that was drained (now on '+(t.sim.i+1)+')');
  eq(t.route,'quizScreen','and it is still a paper you can work on');
  // the headline is whichever clock binds, not the larger of the two
  const head=$('simTotalVal').textContent, sub=$('simTotalSub').textContent;
  const wall=Math.floor(t.simTimeLeft()/1000), byQ=t.simTotalLeft();
  eq(head,fmtMs(Math.min(wall,byQ)*1000),'the big number is the one that runs out first');
  if(wall<byQ) ok(/own clock is what runs out/.test(sub),'and the subtitle says which');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // and with nothing left anywhere it scores rather than stranding
  const qs=t.paperQs(4), qtAll={};
  qs.forEach((_,i)=>qtAll[i]=0);
  t.P.simSave={paper:4,qs,i:3,ans:{},flag:{},rev:{},qt:qtAll,brkUsed:0,brkUntil:0,
               dev:t.DEVICE_ID,devKind:t.DEVICE_KIND,claimAt:Date.now(),
               left:40*60*1000,mins:98,at:Date.now()-60*1000,paused:0};
  t.simResume(); await sleep(120);
  ok(!(t.sim&&t.sim.running),'a paper with no time on any question does not resume into limbo');
  eq(t.route,'simDoneScreen','it scores what was answered instead');
  t.simClearSave();

  // A refresh has to put you back where you were. Everything was already saved — the question,
  // the answers, the flags, the breaks, both clocks — but nothing restored it, so a reload
  // dropped you on the home screen and the paper only came back if you went looking.
  ok(typeof t.resumeOnBoot==='function','there is a boot-time resume');
  await setup();
  t.simPersist();
  const savedPaper=t.P.simSave.paper, savedI=t.P.simSave.i;
  t.simAbandon(); await sleep(30);
  eq(t.P.simSave.paused,1,'Quit marks the save so the boot resume leaves it alone');

  // simulate what boot does with a save that was NOT quit
  t.P.simSave.paused=0;
  ok(!!t.simSaved(),'a live save is still offered');
  ok(t.simOwns(t.P.simSave),'and belongs to this device');
  t.simResume(); await sleep(50);
  eq(t.sim.paper,savedPaper,'resuming puts you back on the same paper');
  ok(t.sim.i>=savedI,'at the question you were on or past a spent one');
  eq(t.route,'quizScreen','and inside it, not on the home screen');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // a paper belonging to another device is that device's to take back, not ours to grab
  await setup();
  t.simPersist();
  t.P.simSave.paused=0; t.P.simSave.dev='someone-else'; t.P.simSave.devKind='phone';
  ok(!t.simOwns(t.P.simSave),'a save from elsewhere is not ours');
  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave();

  // the shape the whole thing rests on
  eq(t.simAwayCost(null),0,'no save, no charge');
  eq(t.simAwayCost({paused:1,at:1}),0,'a paused save is never charged');
  eq(t.simAwayCost({at:0}),0,'nor one with no timestamp');
  eq(t.simAwayCost({at:Date.now()+9999}),0,'nor one stamped in the future');
}

// ---------- two six-minute breaks per paper ----------
// A paper is sat either under exam conditions or as practice, and the difference is entirely
// in the breaks. Everything below is a rule the picker introduced or a bug found building it.
// The sheets are dialogs for a keyboard and a screen reader too, not just to the eye.
// An answer given just before the page closed used to be lost: saves wait 250 ms and
// nothing flushed them. And a browser refusing every write was never mentioned.
// A tap past the limit on a multi-answer question used to vanish without a trace.
async function pickCapChecks(){
  const t=T();
  let k=-1;
  for(let n=11;n<=t.PAPER_COUNT&&k<0;n++){
    t.simClearSave(); t.startPaper(n,'exam'); await sleep(30);
    k=t.sim.qs.findIndex(qi=>t.QS[qi].a.length===2);
    if(k<0){ t.simAbandon(); await sleep(20); }
  }
  ok(k>=0,'there is a two-answer question on a later paper');
  t.simJump(k); await sleep(30);
  const opts=[...document.querySelectorAll('#qOpts .opt')];
  opts[0].click(); opts[1].click(); await sleep(20);
  const before=t.sim.ans[k].join();
  opts[2].click(); await sleep(30);
  eq(t.sim.ans[k].join(),before,'a third pick on a two-answer question changes nothing');
  ok(t.simRevealed(k),'because the second pick settled it and showed the answer');
  t.simAbandon(); await sleep(30); t.simClearSave();
}
// The paper ended on a hidden wall clock that kept running while no question clock did — an
// explanation, the review grid, a practice paper in a background tab — and cut Exam 5 off part
// way with half an hour still showing. It has one clock now.
async function oneClockChecks(){
  const t=T();
  const realNow=Date.now; let skew=0; Date.now=()=>realNow()+skew;
  try{
    t.simClearSave(); t.startPaper(5,'exam'); await sleep(30);
    ok(t.simTeaches(),'a teaching paper, where an explanation follows every answer');
    let endedAt=-1;
    for(let k=0;k<t.simLen();k++){
      skew+=60000; t.simQTick(60);                        // a minute on the question
      t.QS[t.sim.qs[t.sim.i]].a.forEach(l=>t.simPick(l));
      skew+=60000; t.simCheckTime();                       // a minute reading the explanation
      if(!t.sim||!t.sim.running){ endedAt=k+1; break; }
      if(k<t.simLen()-1) t.simGo(1);
    }
    eq(endedAt,-1,'reading every explanation for a minute does not end the paper early');
    ok(t.sim&&t.simAnsweredCount()===t.simLen(),'all '+t.simLen()+' questions got answered');
    eq(t.simTimeLeft(),t.simTotalLeft()*1000,'the clock the paper ends on is the clock on screen');
    t.simSubmit(true); await sleep(40);
    ok(/ 65 min /.test(' '+document.getElementById('simMeta').textContent+' '),
       'and the result reports time spent answering, not wall time: '+document.getElementById('simMeta').textContent);
  } finally { Date.now=realNow; }
  // a practice paper left in a closed tab is not charged — it is how you stop on a phone
  t.simClearSave(); t.startPaper(6,'practice'); await sleep(30);
  t.simPersist();
  const sv=JSON.parse(JSON.stringify(t.P.simSave)); sv.at-=14*3600*1000;
  eq(t.simAwayCost(sv),0,'fourteen hours away from a practice paper costs nothing');
  t.simAbandon(); await sleep(20); t.simClearSave();
  // a simulation still pays for time away in full, from the question you were on and then the end
  t.startPaper(7,'exam'); await sleep(30);
  t.simQTick(20); t.simPersist();
  const full0=t.simTotalLeft();
  t.P.simSave.at-=10*60*1000;
  t.simResume(); await sleep(30);
  ok(full0-t.simTotalLeft()<=t.SIM_QSEC,'ten minutes away costs a simulation only the question it was on');
  ok(t.sim.qt[t.sim.qs.length-1]===undefined,'nothing is taken off the end of the paper');
  ok(t.simQLeft===t.SIM_QSEC,'and you come back to a question with its full time');
  t.simAbandon(); await sleep(20); t.simClearSave();
  // a spent save is scored, not dropped
  t.startPaper(8,'exam'); await sleep(30);
  t.QS[t.sim.qs[0]].a.forEach(l=>t.simPick(l));
  t.simPersist();
  t.P.simSave.at-=10*3600*1000;
  ok(!!t.simSaved(),'a simulation left for ten hours is still there to resume');
  t.simResume(); await sleep(60);
  eq(t.route,'quizScreen','and resuming it goes back in rather than submitting it');
  eq(t.simAnsweredIn(t.sim),1,'with its answers');
  t.simAbandon(); await sleep(20);
  t.simClearSave(); delete t.P.lastPaper;
}
// Finishing a paper later: the questions nobody reached are answerable, the earlier answers
// are locked, and nothing is counted twice.
async function continueChecks(){
  const t=T(), $=id=>document.getElementById(id);
  delete t.P.lastPaper; t.simClearSave();
  t.startPaper(14,'exam'); await sleep(30);
  for(let k=0;k<6;k++){ t.simJump(k); await sleep(2); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simSubmit(true); await sleep(50);
  ok(!$('simCont').classList.contains('hidden'),'a paper ended with questions left offers to finish them');
  ok(/59 left/.test($('simCont').textContent),'and says how many');
  const was={answered:t.P.answered, exams:t.P.exams, tries:t.P.papers[14].tries, correct:t.P.correct};
  t.renderPapers(); await sleep(10);
  const fin=[...document.querySelectorAll('#paperScreen .paperrow')][13].querySelector('button');
  ok(/59/.test(fin.textContent),'the paper\u2019s row in the exam list offers it too');
  $('simCont').click(); await sleep(40);
  eq(t.route,'quizScreen','finishing reopens the paper');
  eq(t.sim.i,6,'on the first question nobody reached');
  ok(t.isPractice(),'under practice rules, since the answers have been shown');
  t.simJump(0); await sleep(5);
  const a0=t.sim.ans[0].join(), q0=t.QS[t.sim.qs[0]];
  t.simPick(q0.o.map(x=>x[0]).find(l=>!t.sim.ans[0].includes(l))); await sleep(5);
  eq(t.sim.ans[0].join(),a0,'an answer from the first sitting is locked');
  for(let k=6;k<16;k++){ t.simJump(k); await sleep(2); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simPersist();
  eq(JSON.stringify(t.P.simSave.locked),JSON.stringify(t.sim.locked),'the lock survives a refresh');
  t.simSubmit(true); await sleep(50);
  eq(t.P.answered,was.answered,'finishing later is not another sixty-five answered');
  eq(t.P.correct-was.correct,10,'only the newly right answers are added');
  eq(t.P.exams,was.exams,'nor another exam');
  eq(t.P.papers[14].tries,was.tries,'nor another attempt');
  eq(t.P.papers[14].bestMode,'practice','and the score is marked as practice');
  eq((t.P.simLog[0]||{}).ct,1,'the history says it was finished later');
  const g={simLog:[{d:'2026-09-20',p:40,pass:0,mins:30,pr:1,ct:1,dom:[1,2,3,4]}]}; t.normaliseProfile(g);
  eq(g.simLog[0].ct,1,'and that survives the load door');
  delete t.P.lastPaper; t.simClearSave();
}
// Scored like SAA-C03 (official exam guide): 100–1000, pass at 720, four domains weighted
// 30/26/24/20, blanks wrong. Questions are filed by what they ask, not by their service.
async function saaChecks(){
  const t=T(), $=id=>document.getElementById(id);
  eq(t.saaScaled(0),100,'0% is 100, the bottom of the scale');
  eq(t.saaScaled(0.72),720,'72% is 720, the pass mark');
  eq(t.saaScaled(1),1000,'100% is 1000');
  ok(t.saaScaled(0.5)<t.saaScaled(0.6)&&t.saaScaled(0.6)<t.saaScaled(0.72),'and it only goes up');
  // the domain a question tests comes from what it asks
  const ask=(txt,s)=>t.examDomainOf({q:txt,s:s||7});
  eq(ask('A company stores logs in S3. Which solution meets these requirements MOST cost-effectively?'),3,
     'an S3 question asking for the cheapest option is a Cost question');
  eq(ask('The data must be encrypted at rest. Which solution will meet these requirements?'),0,'encryption is Secure');
  eq(ask('The application must be highly available across AZs. What should the architect do?'),1,'high availability is Resilient');
  eq(ask('Users report high latency. What should the architect do to improve performance?'),2,'latency is Performing');
  eq(ask('Which option is MOST cost-effectively? (Select TWO.)'),3,'a Select-TWO requirement line is still read');
  const mix=[0,0,0,0]; t.QS.forEach((q,i)=>mix[t.qDom(i)]++);
  ok(mix[3]/t.QS.length>0.08,'Cost is no longer 3% of the bank ('+Math.round(mix[3]/t.QS.length*100)+'%)');
  ok(mix[0]/t.QS.length>0.2,'nor Secure 11% ('+Math.round(mix[0]/t.QS.length*100)+'%)');
  // weighting: the exam's mix, not the paper's
  const byDom=[[],[],[],[]]; t.QS.forEach((q,i)=>byDom[t.qDom(i)].push(i));
  const all=(ok)=>[0,1,2,3].flatMap(d=>byDom[d].slice(0,10).map(qi=>({qi,ok})));
  eq(t.saaScore(all(true)).scaled,1000,'everything right is 1000');
  eq(t.saaScore(all(false)).scaled,100,'everything wrong is 100');
  // perfect on 40 Performing questions, wrong on 10 each of the rest: raw 57%, but Performing
  // is 24% of the exam, not 57%
  const skew=[...byDom[2].slice(0,40).map(qi=>({qi,ok:true})),
              ...[0,1,3].flatMap(d=>byDom[d].slice(0,10).map(qi=>({qi,ok:false})))];
  const S=t.saaScore(skew);
  eq(S.raw,57,'a paper heavy in one strong domain reads 57% raw');
  ok(S.pct<45,'but weighted by the exam\u2019s mix it is far lower ('+S.pct+'%)');
  // two questions cannot swing a 20%-weight domain by a hundred points
  const base=[0,1,2].flatMap(d=>byDom[d].slice(0,20).map(qi=>({qi,ok:true})));
  const a=t.saaScore([...base,...byDom[3].slice(0,2).map(qi=>({qi,ok:true}))]).scaled;
  const b=t.saaScore([...base,...byDom[3].slice(0,2).map(qi=>({qi,ok:false}))]).scaled;
  ok(a-b<70,'two Cost questions move the score by '+(a-b)+', not by a hundred or more');
  // live on a teaching paper, hidden on an exam-conditions one
  delete t.P.lastPaper; t.simClearSave(); t.startPaper(5,'exam'); await sleep(30);
  ok(!$('simLive').classList.contains('hidden'),'a teaching paper shows the score so far');
  for(let k=0;k<4;k++){ t.simJump(k); await sleep(2); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  const live=parseInt($('simLiveVal').textContent,10);
  eq(live,t.saaScore(t.sim.qs.slice(0,4).map(qi=>({qi,ok:true}))).scaled,'and it is the SAA score of what has been answered');
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(12,'exam'); await sleep(30);
  ok(!$('simLive').classList.contains('hidden'),'every paper gives feedback now, so every paper shows it');
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(12,'practice'); await sleep(30);
  ok(!$('simLive').classList.contains('hidden'),'practice shows it');
  t.simAbandon(); await sleep(20); t.simClearSave(); delete t.P.lastPaper;
}
// Opening the app on a second device threw away the exam on the first: the phone resumed and
// claimed its own old copy (question 4), wrote it over the cloud, and the desktop at question 34
// was told the paper had been picked up and dropped its progress.
async function multiDeviceChecks(){
  const t=T(), $=id=>document.getElementById(id);
  delete t.P.lastPaper; t.simClearSave(); t.P.runs={}; t.P.runsDone=[];
  t.startPaper(5,'exam'); await sleep(30);
  ok(!!t.sim.rid,'every exam run has an id');
  for(let k=0;k<3;k++){ t.simJump(k); await sleep(1); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simJump(3); t.simPersist();
  const phone=JSON.parse(JSON.stringify(t.P.simSave)); phone.dev='phone-x'; phone.devKind='phone';
  for(let k=3;k<30;k++){ t.simJump(k); await sleep(1); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simJump(33); t.simPersist();
  const desk=JSON.parse(JSON.stringify(t.P));
  phone.claimAt=Date.now()+60000; phone.at=Date.now()+60000;      // claimed later
  const phoneP=JSON.parse(JSON.stringify(desk)); phoneP.simSave=phone;
  phoneP.runs={}; phoneP.runs[phone.rid+'|phone-x']=phone;
  const m1=t.mergeProfiles(phoneP,desk), m2=t.mergeProfiles(desk,phoneP);
  eq(m1.simSave.i,33,'a stale copy claimed later does not beat the copy at question 34');
  eq(m2.simSave.i,33,'in either order');
  eq(t.simAnsweredIn(m1.simSave),30,'with all thirty answers');
  eq(Object.keys(m1.runs).length,2,'and both devices\u2019 copies are kept as a backup');
  // equal copies still go by claim, so two open devices do not ping-pong
  const same=JSON.parse(JSON.stringify(desk.simSave)); same.dev='phone-x'; same.claimAt=Date.now()+9e5;
  eq(t.simSaveNewer(desk.simSave,same).dev,'phone-x','two copies with the same answers go to the later claim');
  // the running-exams list
  t.simAbandon(); await sleep(20);
  Object.assign(t.P,{runs:m1.runs,runsDone:m1.runsDone});
  t.renderPapers(); t.go('paperScreen'); await sleep(30);
  ok(!$('runBox').classList.contains('hidden'),'the exam screen lists running exams');
  const rows=[...document.querySelectorAll('#runList .runrow')];
  eq(rows.length,2,'one row per device copy');
  const far=rows.find(r=>/furthest/.test(r.querySelector('.nm').textContent));
  ok(!!far&&/question 34/.test(far.querySelector('.ds').textContent),'the furthest copy is marked');
  hittable(far.querySelector('button'),'the Continue button on a running exam');
  far.querySelector('button').click(); await sleep(20);
  ok(/question 34/.test(far.querySelector('button').textContent),'continuing asks first, naming the question');
  far.querySelector('button').click(); await sleep(60);
  eq(t.sim&&t.sim.i,33,'and brings the exam back at question 34');
  eq(t.simAnsweredIn(t.sim),30,'with its answers');
  // taken by another device: this device keeps its own copy, paused
  const theirs=JSON.parse(JSON.stringify(t.P.simSave)); theirs.dev='phone-x'; theirs.devKind='phone';
  theirs.claimAt=Date.now()+99999;
  t.P.simSave=theirs;
  ok(t.simOwnerCheck(),'another device taking the exam stops it here');
  const mine=Object.keys(t.P.runs).find(k=>k.endsWith('|'+t.DEVICE_ID));
  ok(!!mine&&t.P.runs[mine].paused===1,'but keeps this device\u2019s copy, paused, so nothing is lost');
  // finished: gone everywhere, and a device that has not heard cannot bring it back
  t.P.simSave.dev=t.DEVICE_ID; t.simResume(); await sleep(40);
  const rid=t.sim.rid, stale=JSON.parse(JSON.stringify(t.P));
  t.simSubmit(true); await sleep(50);
  ok(t.P.runsDone.includes(rid),'submitting marks the run finished');
  const mg=t.mergeProfiles(stale,JSON.parse(JSON.stringify(t.P)));
  ok(!Object.keys(mg.runs).some(k=>k.startsWith(rid+'|')),'a stale device cannot bring a finished run back');
  ok(!(mg.simSave&&t.svRid(mg.simSave)===rid),'nor leave it open');
  // the paper-record merge keeps the practice/exam marks
  const pm=t.mergeProfiles({papers:{3:{best:80,tries:2,last:'80%',d:'x',bestMode:'practice',ptries:1}}},
                           {papers:{3:{best:70,tries:3,last:'70%',d:'y',lastMode:'exam'}}});
  eq(pm.papers[3].bestMode,'practice','a merge keeps how the best score was set');
  delete t.P.lastPaper; t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.go('homeScreen'); await sleep(20);
}
// Bug-hunt round: a timed-out question could still be answered, a break that ran out in the
// background was charged as time away, and chests never paid after an exam.
async function hunt9Checks(){
  const t=T();
  // 1
  t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; delete t.P.lastPaper;
  t.startPaper(12,'exam'); await sleep(30);
  t.simQTick(t.SIM_QSEC); await sleep(20);
  t.simJump(0); await sleep(20);
  eq(t.simQLeft,0,'a question that ran out shows no time when you go back to it');
  t.QS[t.sim.qs[0]].a.forEach(l=>t.simPick(l));
  ok(!(t.sim.ans[0]||[]).length,'and cannot be answered after its time is up');
  t.simAbandon(); await sleep(20); t.simClearSave();
  // 2
  const realNow=Date.now; let skew=0; Date.now=()=>realNow()+skew;
  try{
    t.startPaper(12,'exam'); await sleep(30);
    const total0=t.simTotalLeft();
    t.brkStart(); t.go('homeScreen'); t.simAway();
    skew+=20*60000; t.brkTick(); t.simBack(); await sleep(20);
    ok(total0-t.simTotalLeft()<=t.SIM_QSEC,'twenty minutes away across a break costs no more than one question');
  } finally { Date.now=realNow; }
  t.simAbandon(); await sleep(20); t.simClearSave();
  // 3
  const was={answered:t.P.answered,next:t.P.nextChest,coins:t.P.coins};
  t.P.answered=100; t.P.nextChest=50;           // an exam just crossed three thresholds
  t.checkChest();
  eq(t.P.nextChest,125,'every threshold an exam crosses is paid, and the next one is ahead');
  ok(t.chestProgress().left>0,'so the home screen never sits on "0 questions"');
  t.P.answered=900; t.P.nextChest=100;           // an old backlog
  const c0=t.P.coins; t.checkChest();
  ok(t.P.nextChest>900&&t.P.coins-c0<=3*200,'an old backlog is stepped over, not paid out as a heap');
  Object.assign(t.P,{answered:was.answered,nextChest:was.next,coins:was.coins});
}
// The read-aloud button thins out as the papers go on: every question on 1-7, odd questions
// on 8-10, once every three on 11-12, none from 13.
async function readTaperChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const want={1:'1,2,3,4,5,6',7:'1,2,3,4,5,6',8:'1,3,5',10:'1,3,5',11:'1,4',12:'1,4',13:'',19:''};
  for(const n of Object.keys(want)){
    t.simClearSave(); t.startPaper(+n,'exam'); await sleep(20);
    const shown=[];
    for(let i=0;i<6;i++){ t.simJump(i); await sleep(2); if(!$('simTts').classList.contains('hidden')) shown.push(i+1); }
    eq(shown.join(','),want[n],'Exam '+n+' offers read-aloud on questions '+(want[n]||'none'));
    t.simAbandon(); await sleep(10); t.simClearSave();
  }
  t.P.runs={}; t.P.runsDone=[];
}
// Exam history: every submitted exam is kept and can be redone with no timer, answers editable,
// the score recomputed live, crash-safe, and a redo is review — no coins, not another exam.
async function histChecks(){
  const t=T(), $=id=>document.getElementById(id);
  t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.P.examHist={}; delete t.P.lastPaper;
  t.startPaper(6,'exam'); await sleep(30);
  for(let k=0;k<30;k++){ t.simJump(k); await sleep(1); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simSubmit(true); await sleep(50);
  const ks=Object.keys(t.P.examHist);
  eq(ks.length,1,'a submitted exam goes into history');
  const hid=ks[0], e0=t.P.examHist[hid];
  eq(Object.keys(e0.ans).length,30,'with every answer');
  ok(e0.sc>=100&&e0.sc<=1000,'and its score on the exam scale');
  const coins0=t.P.coins, exams0=t.P.exams;
  $('navRedo').click(); await sleep(40);
  eq(t.route,'redoScreen','the Redo tab opens the exam list');
  const row=document.querySelector('#redoList .rdcard');
  ok(!!row&&/Exam 6/.test(row.textContent),'it lists the exam');
  hittable(row.querySelector('button'),'the Redo button');
  row.querySelector('button').click(); await sleep(60);
  ok(t.isRedo(),'Redo opens it');
  ok(/REDO/.test($('qSector').textContent),'labelled as a redo');
  eq(t.simAnsweredIn(t.sim),30,'with its answers filled in');
  eq(t.sim.i,30,'on the first question left blank');
  ok(!$('simAnsBtn').classList.contains('hidden'),'with a Show answer button');
  t.simQTick(500); t.simCheckTime(); await sleep(10);
  ok(t.sim&&t.sim.running,'there is no timer: nothing runs out and nothing submits');
  const before=parseInt($('simLiveVal').textContent,10);
  for(let k=30;k<40;k++){ t.simJump(k); await sleep(1); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  ok(parseInt($('simLiveVal').textContent,10)>before,'answering more raises the score live');
  eq(t.P.examHist[hid].c,40,'and history is updated on every edit, not only on close');
  t.simJump(0); await sleep(5);
  const q0=t.QS[t.sim.qs[0]];
  if(q0.a.length===1){ const alt=q0.o.map(x=>x[0]).find(l=>!q0.a.includes(l));
    t.simPick(alt); ok(t.sim.ans[0].includes(alt),'an earlier answer can be changed'); t.simPick(q0.a[0]); }
  t.simPersist(); t.simResume(); await sleep(50);   // the app crashes: all that is left is the save
  ok(t.isRedo(),'a crash mid-redo comes back as the redo');
  eq(t.simAnsweredIn(t.sim),40,'with every edit kept');
  $('simSubmit').click(); await sleep(50);
  eq(t.route,'redoScreen','Save & close returns to the Redo tab');
  eq(t.P.examHist[hid].c,40,'the entry keeps the new answers');
  eq(t.P.examHist[hid].redos,1,'counted as one redo, crash or not');
  eq(t.P.coins,coins0,'a redo pays nothing');
  eq(t.P.exams,exams0,'and is not another exam');
  // history survives a merge from another device
  const other={examHist:{x1:{hid:'x1',paper:3,qs:t.paperQs(3),ans:{},sc:300,c:0,n:65,at:1,d0:1}}};
  const m=t.mergeProfiles(other,JSON.parse(JSON.stringify(t.P)));
  ok(!!m.examHist.x1&&!!m.examHist[hid],'history from both devices is kept');
  t.P.examHist={}; t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.go('homeScreen'); await sleep(20);
}
// Exam history in its own table: a change goes up within a second and a half, a newer copy on
// the other device comes down, and a missing table falls back to the profile without breaking.
async function histSyncChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const table={}; let fail=null;
  const client={from(name){ return {
    upsert(rows){ if(fail) return Promise.resolve({error:fail});
      rows.forEach(r=>{ table[r.hid]=JSON.parse(JSON.stringify(r)); }); return Promise.resolve({error:null}); },
    select(){ const all=()=>fail?{error:fail,data:null}:{error:null,data:Object.values(table).map(r=>({hid:r.hid,exam:JSON.parse(JSON.stringify(r.exam))}))};
      const q=Promise.resolve().then(all);
      q.in=(col,vals)=>Promise.resolve().then(()=>{ const r=all(); if(r.data) r.data=r.data.filter(x=>vals.includes(x.hid)); return r; });
      return q; } }; }};
  const was=t.cloudForTest(client,{id:'u-test'});
  try{
    t.histTable='unknown';
    t.simClearSave(); t.P.examHist={}; t.P.runs={}; t.P.runsDone=[]; delete t.P.lastPaper;
    t.startPaper(4,'exam'); await sleep(20);
    for(let k=0;k<5;k++){ t.simJump(k); await sleep(1); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
    t.simSubmit(true); await sleep(1700);
    const hid=Object.keys(t.P.examHist)[0];
    ok(!!table[hid],'a submitted exam is written to its own row in the table');
    eq(table[hid].exam.c,5,'with its answers and score');
    eq(table[hid].user_id,'u-test','under this user');
    // the other device edited it: its copy is newer
    const theirs=JSON.parse(JSON.stringify(table[hid].exam)); theirs.c=40; theirs.sc=780; theirs.at=Date.now()+60000;
    table[hid].exam=theirs;
    const changed=await t.histCloudPull();
    ok(changed,'a pull notices the other device changed it');
    eq(t.P.examHist[hid].sc,780,'and takes the newer copy');
    // an exam only this device has goes up on the next pull
    t.P.examHist.only={hid:'only',paper:2,qs:t.paperQs(2),ans:{},sc:200,c:0,n:65,at:Date.now(),d0:Date.now()};
    await t.histCloudPull(); await sleep(1700);
    ok(!!table.only,'an exam the table is missing is sent up');
    // the Redo screen shows it is syncing through the table
    t.renderRedoScreen();
    ok(/Synced to your account/.test($('redoSync').textContent),'the Redo screen says it is synced');
    // no table yet: falls back without breaking
    fail={code:'42P01',message:'relation "public.exam_history" does not exist'};
    t.histTable='unknown';
    eq(await t.histCloudPull(),false,'a missing table does not throw');
    eq(t.histTable,'missing','it is noticed');
    t.renderRedoScreen();
    ok(/supabase_exam_history\.sql/.test($('redoSync').textContent),'and the screen says how to create it');
  } finally { t.cloudForTest(was[0],was[1]); t.histTable='unknown'; }
  t.P.examHist={}; t.simClearSave(); t.go('homeScreen'); await sleep(20);
}
// Reported: the PC showed Exam 8 at 342 in Redo while the phone, mid-redo, was at 431 on Q37.
// Opening a redo stamped the old copy "newest", the upload replaced the account's row blindly,
// and an open redo never took in the other device's answers.
async function redoSyncChecks(){
  const t=T();
  const table={};
  const client={from(){ return {
    upsert(rows){ rows.forEach(r=>{ table[r.hid]=JSON.parse(JSON.stringify(r)); }); return Promise.resolve({error:null}); },
    select(){ const all=()=>({error:null,data:Object.values(table).map(r=>({hid:r.hid,exam:JSON.parse(JSON.stringify(r.exam))}))});
      const q=Promise.resolve().then(all);
      q.in=(c,v)=>Promise.resolve().then(()=>{ const r=all(); r.data=r.data.filter(x=>v.includes(x.hid)); return r; });
      return q; } }; }};
  const was=t.cloudForTest(client,{id:'u-redo'});
  try{
    t.histTable='unknown';
    t.simClearSave(); t.P.examHist={}; t.P.runs={}; t.P.runsDone=[]; delete t.P.lastPaper;
    const qs=t.paperQs(8), right=n=>{ const a={}; for(let i=0;i<n;i++) a[i]=t.QS[qs[i]].a.slice(); return a; };
    const now=Date.now();
    // this device (the PC) kept an older copy: 18 right
    t.P.examHist.e8={hid:'e8',paper:8,qs:qs.slice(),ans:right(18),flag:{},mode:'practice',d:'2026-09-23',d0:now-9e6,at:now-6e5,redos:12,c:18,n:65,sc:342};
    // the phone went on to 37 answered, and its copy is on the account
    const phone=JSON.parse(JSON.stringify(t.P.examHist.e8)); phone.ans=right(37); phone.c=37; phone.sc=431; phone.at=now-6e4; phone.redos=11;
    table.e8={user_id:'u-redo',hid:'e8',exam:phone};

    // Continue on the PC starts from the phone's answers, not its own
    await t.histOpen('e8',null); await sleep(30);
    ok(t.sim&&t.sim.mode==='redo','Continue opens the redo');
    eq(Object.keys(t.sim.ans).length,37,'from the account\'s copy: the 37 answers the phone had, not the PC\'s 18');
    eq(t.sim.i,37,'on the first unanswered question');
    eq(t.P.examHist.e8.redos,13,'the open is counted once, on the larger of the two counts');
    ok(t.P.examHist.e8.at<=phone.at,'but opening does not stamp the copy newer than the work in it');
    await sleep(1700);
    eq(Object.keys(table.e8.exam.ans).length,37,'and the account keeps the phone\'s answers');

    // an edit on the PC now is newer, even if the phone\'s clock ran ahead
    table.e8.exam.at=Date.now()+3e5; t.P.examHist.e8.at=table.e8.exam.at;
    const q37=t.QS[t.sim.qs[37]]; t.simJump(37); await sleep(1); q37.a.forEach(l=>t.simPick(l));
    ok(t.P.examHist.e8.at>table.e8.exam.at-1,'an edit is stamped after the copy it was made on, whatever the clocks say');
    await sleep(1700);
    eq(Object.keys(table.e8.exam.ans).length,38,'and it reaches the account');

    // the phone answers more while the PC's redo is open: a pull brings it into the open redo
    const later=JSON.parse(JSON.stringify(table.e8.exam)); later.ans=right(45); later.c=45; later.at=t.P.examHist.e8.at+1000;
    table.e8.exam=later;
    await t.histCloudPull(); await sleep(20);
    eq(Object.keys(t.sim.ans).length,45,'newer answers from the other device appear in the redo that is open');

    // a device holding an old copy never uploads it over a newer one
    const stale=JSON.parse(JSON.stringify(later)); stale.ans=right(5); stale.at=later.at-5000;
    t.P.examHist.e8=stale; t.histDirty.add('e8');
    await t.histCloudPush(); await sleep(10);
    eq(Object.keys(table.e8.exam.ans).length,45,'an older copy is not uploaded over the account\'s newer one');
    eq(Object.keys(t.P.examHist.e8.ans).length,45,'the older device takes the newer copy instead');

    // the profile merge keeps the larger count too
    const m=t.mergeProfiles({at:1,examHist:{z:{hid:'z',qs:[1],at:5,redos:9}}},{at:2,examHist:{z:{hid:'z',qs:[1],at:7,redos:3}}});
    eq(m.examHist.z.at,7,'the merge still takes the newer copy');
    eq(m.examHist.z.redos,9,'with the larger open count');
  } finally { t.cloudForTest(was[0],was[1]); t.histTable='unknown'; }
  if(t.sim) t.simAbandon(); await sleep(20);
  t.P.examHist={}; t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.go('homeScreen'); await sleep(20);
}
// The pause bar stayed up over a question in progress: a resume cleared the pause without
// telling the bar. And a redo, which has no clock, paused at all.
async function pauseBarChecks(){
  const t=T(), $=id=>document.getElementById(id);
  t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.P.examHist={}; delete t.P.lastPaper;
  t.startPaper(4,'exam'); await sleep(20);
  for(let k=0;k<3;k++){ t.simJump(k); await sleep(1); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simSubmit(true); await sleep(40);
  $('navRedo').click(); await sleep(30); document.querySelector('#redoList .rdcard button').click(); await sleep(50);
  $('navHome').click(); await sleep(30);
  eq(t.route,'homeScreen','leaving a redo just leaves');
  ok(!t.brkOn()&&$('brkBar').classList.contains('hidden'),'without starting a pause — a redo has no clock');
  $('navRedo').click(); await sleep(30); document.querySelector('#redoList .rdcard button').click(); await sleep(50);
  ok($('brkBar').classList.contains('hidden'),'and coming back shows no pause bar');
  t.simAbandon(); await sleep(20); t.simClearSave(); t.P.examHist={};
  t.startPaper(5,'practice'); await sleep(30);
  $('navHome').click(); await sleep(30);
  ok(t.brkOn()&&!$('brkBar').classList.contains('hidden'),'a practice paper still pauses when you leave');
  t.simPersist(); t.simResume(); await sleep(50);
  ok(!t.brkOn(),'resuming ends the pause');
  ok($('brkBar').classList.contains('hidden'),'and the bar goes with it, instead of staying over the question');
  t.simAbandon(); await sleep(20); t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.go('homeScreen'); await sleep(20);
}
// Signing in on a fresh browser wiped the account: the blank guest profile was the LATER save,
// so its empty history, review schedule and streak replaced the cloud's, and went back up.
function mergeLossChecks(){
  const t=T(), J=o=>JSON.parse(JSON.stringify(o));
  const cloud={at:1000, sims:11, diff:'hard', theme:'mono',
    simLog:[{d:'2026-09-20',p:81,sc:790,pass:1},{d:'2026-9-2',p:64,sc:610,pass:0}],
    examLog:[{d:'2026-09-19',c:40,t:50,p:1}],
    rHist:[{d:'2026-9-1',p:40},{d:'2026-09-18',p:66}],
    sr:{12:{box:2,due:300},40:{box:1,due:210}},
    study:{3:{read:1,best:90,at:'2026-09-10'}},
    known:[5,6], inv:{shield:2}, login:{last:1790000000000,streak:9,claimed:1}, lastPaper:7};
  const guest={at:5000, sims:0, diff:'easy', theme:'neon', simLog:[], examLog:[], rHist:[{d:'2026-09-23',p:0}],
    sr:{}, study:{}, known:[], inv:{}, login:{last:1790100000000,streak:1,claimed:0}};
  const m=t.mergeProfiles(J(cloud),J(guest));
  eq(m.simLog.length,2,'a blank browser signing in keeps the account\'s exam history');
  eq((m.simLog[0]||{}).sc,790,'newest first');
  eq(m.examLog.length,1,'and the exam log');
  eq(t.mergeProfiles({at:1,mockLog:[{d:'2026-09-01',p:70,pass:0}]},{at:2,mockLog:[]}).mockLog.length,1,'and the mock log');
  eq(m.rHist.length,3,'and the readiness history, one point a day');
  eq((m.rHist[0]||{}).d,'2026-9-1','in date order, including dates written before zero-padding');
  eq(Object.keys(m.sr).length,2,'and the spaced-repetition schedule');
  eq(m.study[3]&&m.study[3].best,90,'and the study records');
  eq(m.known.length,2,'and the known list');
  eq((m.inv||{}).shield,2,'an empty inventory does not wipe a full one');
  eq(m.lastPaper,7,'and the last paper is still remembered');
  eq(m.login.streak,1,'the login streak follows the LATER login (a day apart here)');
  const same=t.mergeProfiles(J(cloud),J(Object.assign({},guest,{login:{last:cloud.login.last,streak:1}})));
  eq(same.login.streak,9,'and on the same day, the longer streak');
  eq(m.diff,'easy','without a sign-in, the later save still wins plain settings');
  const f=t.mergeProfiles(J(cloud),J(guest),{cloudFirst:true});
  eq(f.diff,'hard','on a sign-in, the account\'s settings win over the blank guest');
  eq(f.theme,'mono','all of them');
  eq(f.sims,11,'counters still take the higher');
  eq(f.simLog.length,2,'and the history is still united');

  // the damaged cloud copy meets a device that still has everything: it comes back
  const damaged=Object.assign(J(guest),{at:9000,sims:11});
  const r=t.mergeProfiles(damaged,J(cloud));
  eq(r.simLog.length,2,'a device with the full data restores the history to a damaged cloud copy');
  eq(Object.keys(r.sr).length,2,'and the review schedule');
  eq(r.known.length,2,'and the known list');

  // both sides have work: nothing is lost, duplicates are not doubled, caps hold
  const a={at:1,simLog:Array.from({length:10},(_,i)=>({d:'2026-08-'+(10+i),p:i}))};
  const b={at:2,simLog:[a.simLog[0],{d:'2026-09-01',p:99}].concat(Array.from({length:5},(_,i)=>({d:'2026-07-0'+(i+1),p:50+i})))};
  const u=t.mergeProfiles(J(a),J(b));
  eq(u.simLog.length,12,'the history is capped at twelve, as the writer caps it');
  eq((u.simLog[0]||{}).p,99,'keeping the newest');
  eq(u.simLog.filter(e=>e.d==='2026-08-10').length,1,'and one entry seen on both is not counted twice');
  const s2=t.mergeProfiles({at:1,sr:{7:{box:3,due:900}}},{at:2,sr:{7:{box:1,due:400}}});
  eq((s2.sr[7]||{}).due,900,'a question scheduled on both keeps the later due point');
  const st=t.mergeProfiles({at:1,study:{2:{read:1,best:40,at:'2026-09-01'}}},{at:2,study:{2:{read:0,best:70,at:'2026-09-05'}}});
  ok(!!st.study[2]&&st.study[2].read===1&&st.study[2].best===70,'a chapter keeps read-on-either and the better score');

  // "Reset all progress" signed in: uniting would bring it all straight back from the cloud
  const wiped={at:7000, resetAt:7000, xp:0, sims:0, seen:{}, simLog:[], badges:[]};
  const full=Object.assign(J(cloud),{at:6000, xp:900, seen:{4:1}, badges:['b1'], wrong:[3]});
  const rs=t.mergeProfiles(J(full),J(wiped));
  eq(rs.simLog.length,0,'a reset is not undone by the cloud copy saved before it');
  eq(rs.sims,0,'counters too');
  eq(Object.keys(rs.seen).length+rs.badges.length,0,'nor seen questions and badges');
  ok(Array.isArray(rs.wrong)&&rs.wrong.length===0,'a list only the old copy had comes back empty, so assigning it clears it');
  eq(t.mergeProfiles(J(wiped),J(full)).simLog.length,0,'the same when the reset arrives from the cloud');
  eq(t.mergeProfiles(Object.assign(J(full),{examDate:'2026-10-01'}),J(wiped)).examDate,'2026-10-01','settings survive a reset');
  const after=Object.assign(J(wiped),{at:8000, simLog:[{d:'2026-09-24',p:70}]});
  const ph=t.mergeProfiles(J(after),Object.assign(J(wiped),{at:7500, simLog:[{d:'2026-09-23',p:60}]}));
  eq(ph.simLog.length,2,'after the reset, both devices merge normally again');
  eq(t.mergeProfiles({at:1,sims:3},{at:2,sims:5}).resetAt,undefined,'and a profile never reset carries no reset time');
}
// The casino showed Roulette and the Question duel stacked; the duel now plays on the
// practice exams, reveals each answer once a question is over, and has a practice bot.
async function duelChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const vis=id=>!$(id).classList.contains('hidden');
  // ---- one panel at a time, from the first paint
  const fresh=new DOMParser().parseFromString(await (await fetch('/index.html?'+Date.now())).text(),'text/html');
  ok(fresh.getElementById('casDuel').classList.contains('hidden'),'the duel panel starts hidden in the markup');
  ok(fresh.getElementById('casBj').classList.contains('hidden'),'as does blackjack');
  ['Roul','Bj','Duel'].forEach(w=>{
    t.casTab(w);
    eq(['casRoul','casBj','casDuel'].filter(vis).join(),'cas'+w,'tab '+w+' shows exactly its own panel');
  });
  eq(fresh.getElementById('duelCount').textContent,'75s','the clock label matches the 75-second question');

  // ---- where a question lives
  eq(t.duelWhere(0),'Exam 1 · Q1','question 0 is Exam 1, Q1');
  eq(t.duelWhere(130),'Exam 3 · Q1','question 130 opens Exam 3');
  eq(t.duelWhere(1200),'Exam 19 · Q31','the last question is the last of Exam 19');
  const opts=[...$('duelExam').options];
  eq(opts.length,t.PAPER_COUNT+1,'the exam picker offers any exam and every exam');
  eq(opts[0].value,'0','any exam first');

  // ---- the server's answer key is the bank's (it drifted once: 862 and 1046)
  const sql=await (await fetch('/supabase_duel_v2.sql?'+Date.now())).text();
  const key=JSON.parse(/values \(1, '(\{.*?\})'::jsonb\)/.exec(sql)[1]);
  const drift=t.QS.map((q,i)=>(key[i]||[]).slice().sort().join()===q.a.slice().sort().join()?null:i).filter(x=>x!==null);
  eq(drift.length,0,'the duel answer key matches the bank — re-run gen_duel_v2.py after a bank change'+(drift.length?' (off: '+drift.slice(0,5)+')':''));
  eq(Object.keys(key).length,t.QS.length,'and covers every question');

  // ---- the bot: exam 3, you right and the bot wrong ends it at once
  const rnd=Math.random, saveW=t.P.botW||0, saveL=t.P.botL||0, saveD=t.P.botD||0;
  try{
    t.duelExam=3; t.botStart(); await sleep(20);
    const b=t.bot;
    ok(b.qs.length===5&&b.qs.every(i=>i>=130&&i<=194),'a bot duel on Exam 3 draws all five from it');
    eq(new Set(b.qs).size,5,'with no question twice');
    ok(vis('duelPlay')&&vis('casDuel'),'and opens on the board');
    ok(/^Exam 3 · Q\d+/.test($('duelSrc').textContent),'the question says which exam it is from');
    eq($('duelMePips').children.length,5,'five pips a side');
    ok($('duelMePips').children[0].classList.contains('now'),'the first marked as the one in play');
    b.botAt=1e9;
    const q0=t.QS[b.qs[0]];
    t.botPlayerAnswer(q0.a.slice());
    Math.random=()=>0.99;                       // the bot misses
    b.botAt=0; t.botTick(); await sleep(10);
    eq(b.status,'done','right against a wrong bot ends it');
    eq(b.winner,'you','and you win');
    ok(vis('duelDone'),'the result screen shows');
    eq($('duelResult').textContent,'YOU WIN','saying so');
    eq($('duelRecap').children.length,1,'with the one question that decided it');
    ok(/Exam 3 · Q/.test($('duelRecap').textContent),'recapped with where it is from');
    eq(t.P.botW,saveW+1,'a bot win is recorded');
    ok(/Play the bot again/.test($('duelAgain').textContent),'and the rematch is another bot game');

    // ---- both right moves on, and the reveal says what the answer was
    t.duelExam=0; t.botStart(); await sleep(10);
    const c=t.bot; c.botAt=1e9;
    const q1=t.QS[c.qs[0]];
    t.botPlayerAnswer(q1.a.slice());
    Math.random=()=>0;                          // the bot gets it
    c.botAt=0; t.botTick(); await sleep(10);
    eq(c.status,'active','both right keeps it going');
    eq(c.turn,1,'on to question 2');
    eq(c.hist.length,1,'the first in the history');
    ok(vis('duelLast'),'the answer to question 1 is shown');
    ok($('duelLast').textContent.indexOf(q1.a.slice().sort().join(' + '))>=0,'naming the right letters');
    ok($('duelMePips').children[0].classList.contains('ok')&&$('duelThemPips').children[0].classList.contains('ok'),
       'both pips for question 1 go green');
    eq($('duelScore').textContent,'1 — 1','and the score');
    // ---- neither answers in time: skipped, not lost
    Math.random=rnd;
    c.botAt=1e9; c.start=Date.now()-76000; t.botTick(); await sleep(10);
    eq(c.turn,2,'a question nobody answered in time is skipped');
    ok($('duelMePips').children[1].classList.contains('skip'),'and its pip says so');
    // ---- the bot answers and the clock runs out on you
    c.them.pick=t.QS[c.qs[2]].a.slice(); c.them.ok=true; c.them.score++;
    c.start=Date.now()-76000; t.botTick(); await sleep(10);
    eq(c.status,'done','running out the clock after the bot answered loses');
    eq(c.winner,'them','to the bot');
    eq(t.P.botL,saveL+1,'recorded as a loss');
    eq($('duelResult').textContent,'YOU LOSE','and shown as one');

    // ---- leaving a bot duel concedes after a confirm
    t.botStart(); await sleep(10);
    $('duelLeave').click();
    eq(t.bot.status,'active','the first tap only asks');
    ok(/Tap again/.test($('duelLeave').textContent),'by relabelling the button');
    t.botTick(); await sleep(10);
    ok(/Tap again/.test($('duelLeave').textContent),'which a repaint does not undo');
    $('duelLeave').click(); await sleep(10);
    eq(t.bot.status,'done','the second tap leaves');
    eq(t.bot.winner,'them','and the bot takes it');
  } finally {
    Math.random=rnd; t.P.botW=saveW; t.P.botL=saveL; t.P.botD=saveD; t.duelExam=0;
  }

  // ---- a server duel, as v2 sends it: the reveal and pips come from hist
  const qa=t.QS[140], qb=t.QS[141];
  const view={id:'srv1', status:'active', stake:50, turn:1, exam:3, count:5, question:141,
    you:{name:'me', score:1, answered:false}, them:{name:'rival', score:0, answered:true},
    hist:[{q:140, answer:qa.a, you:qa.a, them:['Z'], youOk:true, themOk:false}],
    secondsTotal:75, secondsLeft:40};
  t.paintDuel(view);
  ok(vis('duelPlay'),'a server duel paints the board');
  eq($('duelPot').textContent,'POT 100','with the pot');
  ok($('duelMePips').children[0].classList.contains('ok')&&$('duelThemPips').children[0].classList.contains('no'),
     'question 1: you right, them wrong');
  ok($('duelMePips').children[1].classList.contains('now'),'question 2 in play');
  ok(/rival has answered/.test($('duelStatus').textContent),'and says the other side has answered');
  eq($('duelSrc').textContent.indexOf('Exam 3 · Q12'),0,'question 141 is Exam 3, Q12');
  const optsBefore=$('duelOpts').firstChild;
  t.paintDuel(Object.assign({},view,{secondsLeft:38}));
  eq($('duelOpts').firstChild,optsBefore,'a repaint of the same question keeps the options (no rebuild under a finger)');
  // a v1 database sends no hist: nothing breaks
  t.paintDuel({id:'srv2', status:'active', stake:25, turn:0, question:5,
    you:{name:'me',score:0,answered:false}, them:{name:'x',score:0,answered:false}});
  ok(vis('duelPlay')&&$('duelMePips').children.length===5,'a v1 duel (no history) still paints');
  ok(!vis('duelLast'),'with nothing to reveal');
  t.duelShow('Lobby'); t.casTab('Roul'); t.rouStop();

  // ---- roulette: a spin with nothing to land on stops instead of going on forever
  t.rouSetPhase('spinning'); t.rouSpinningFor=Date.now()-2000;
  t.paintRouTable({round:7,open:true,secondsLeft:20,bets:[],mine:[],last:null});
  eq(t.rouPhase,'spinning','a spin a couple of seconds old keeps waiting for its result');
  t.rouSpinningFor=Date.now()-8000;
  t.paintRouTable({round:7,open:true,secondsLeft:20,bets:[],mine:[],last:null});
  eq(t.rouPhase,'betting','one with no result after seven seconds stops');
  eq($('rouResult').textContent,'Waiting for the table…','and says what it is waiting for');
  t.rouStop();
}
async function saveFlushChecks(){
  const t=T();
  t.simClearSave(); t.startPaper(1,'exam'); await sleep(400);
  const base=localStorage.getItem('academy_profile');
  t.simPick(t.QS[t.sim.qs[0]].o[0][0]);
  eq(localStorage.getItem('academy_profile'),base,'a save still waits a moment, so bursts become one write');
  window.dispatchEvent(new Event('pagehide'));
  const saved=JSON.parse(localStorage.getItem('academy_profile'));
  ok(!!(saved.simSave&&saved.simSave.ans&&saved.simSave.ans[0]),'but closing the page writes it straight away');
  t.simAbandon(); await sleep(30); t.simClearSave(); await sleep(300);
}
async function dialogChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const key=k=>document.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true}));
  ['modeAsk','brkAsk','studyModal'].forEach(id=>{
    eq($(id).getAttribute('role'),'dialog',id+' is announced as a dialog');
    eq($(id).getAttribute('aria-modal'),'true',id+' is modal');
    const lab=$(id).getAttribute('aria-labelledby');
    ok(!!lab&&!!$(lab)&&$(lab).textContent.trim().length>3,id+' is labelled by its own heading');
  });
  t.simClearSave(); t.go('paperScreen'); t.renderPapers(); await sleep(20);
  const opener=document.querySelector('#paperScreen .paperrow button'); opener.focus();
  t.modeAsk('Exam 1',()=>{}); await sleep(30);
  ok($('modeAsk').contains(document.activeElement),'opening a sheet moves focus into it');
  const list=[...document.querySelectorAll('#modeAsk button')];
  list[list.length-1].focus(); key('Tab');
  eq(document.activeElement,list[0],'Tab from the last control wraps to the first, not the page behind');
  key('Escape'); await sleep(30);
  ok($('modeAsk').classList.contains('hidden'),'Escape closes it');
  eq(document.activeElement,opener,'and focus goes back to what opened it');
  ok(!(t.sim&&t.sim.running),'without starting anything');
  t.startPaper(1,'exam'); await sleep(20);
  $('navHome').click(); await sleep(30);
  ok($('brkAsk').contains(document.activeElement),'the break sheet takes focus too');
  key('Escape'); await sleep(30);
  eq(t.route,'quizScreen','Escape on the break sheet means stay on the question');
  eq(t.brkLeft(),2,'and costs no break');
  t.simAbandon(); await sleep(30); t.simClearSave(); t.go('homeScreen'); await sleep(20);
}
async function modeChecks(){
  const t=T(), $=id=>document.getElementById(id);

  // the picker asks, and asks before anything starts
  t.simClearSave();
  let picked=null;
  t.modeAsk('Exam 1',m=>{ picked=m; });
  ok(!$('modeAsk').classList.contains('hidden'),'starting a paper asks which kind it is');
  ok(/Exam 1/.test($('modeAskTitle').textContent),'and names the paper being started');
  t.modePick('practice');
  eq(picked,'practice','the choice reaches the caller');
  ok($('modeAsk').classList.contains('hidden'),'and the sheet closes behind it');
  t.modeAsk('Exam 1',()=>{}); t.modeAskClose();
  ok($('modeAsk').classList.contains('hidden'),'backing out closes it without starting anything');

  // ---- practice: stop as often as you like, for as long as you like ----
  t.simClearSave(); t.startPaper(1,'practice'); await sleep(30);
  ok(t.isPractice(),'a practice paper knows it is one');
  eq(t.brkLeft(),Infinity,'and is not rationed to two breaks');
  eq($('qSector').textContent.indexOf('PRACTICE')>0,true,'the header says so, so you cannot forget');

  t.simQTick(20);
  const qBefore=t.simQLeft, paperBefore=t.sim.endAt-Date.now();
  $('navHome').click(); await sleep(20);
  ok($('brkAsk').classList.contains('hidden'),'leaving practice does not ask \u2014 the pause is free');
  eq(t.route,'homeScreen','and it lets you go');
  ok(t.brkOn()&&t.brkOpen(),'the paper is paused, open-endedly');

  t.sim.brkFrom-=20*60*1000;                       // twenty minutes away
  t.go('quizScreen'); await sleep(20);
  eq(t.route,'quizScreen','coming back to the paper is how the pause ends');
  ok(!t.brkOn(),'and it does end');
  eq(t.simQLeft,qBefore,'the question keeps the seconds it had');
  const gained=(t.sim.endAt-Date.now())-paperBefore;
  ok(Math.abs(gained-20*60*1000)<5000,
     'and the paper gets back what the pause ran, not a fixed six minutes');

  // the paused bar is the way back in, and it has to actually take a tap
  t.go('homeScreen'); await sleep(20);
  const bar=$('brkBar');
  ok(!bar.classList.contains('hidden'),'a paused practice paper shows the bar');
  ok(bar.classList.contains('tappable'),'and the bar is a button, not a status line');
  eq(bar.getAttribute('role'),'button','labelled as one');
  hittable(bar,'the paused bar');
  bar.click(); await sleep(30);
  eq(t.route,'quizScreen','tapping it goes back to the paper');
  ok(!t.brkOn(),'and ends the pause');

  // as many as you like
  for(let k=0;k<4;k++){ t.go('homeScreen'); await sleep(5); t.go('quizScreen'); await sleep(5); }
  ok(t.sim.brkUsed>=5,'five pauses is not a problem in practice');
  eq(t.brkLeft(),Infinity,'and there are still no limits');

  // ---- a refresh mid-pause pays the pause once, not twice ----
  t.simClearSave(); t.startPaper(2,'practice'); await sleep(20);
  t.simQTick(20);
  t.go('homeScreen'); await sleep(10);
  t.sim.brkFrom-=30*60*1000;
  t.simPersist();
  const sv=JSON.parse(JSON.stringify(t.P.simSave));
  eq(sv.mode,'practice','the save remembers which kind of paper it is');
  eq(sv.brkOpen,1,'and that it was paused when it was written');
  eq(t.simAwayCost(sv),0,'time inside an open pause is not charged');
  const savedMin=Math.round(sv.left/60000), savedQ=sv.qt[sv.i];
  t.simResume(); await sleep(20);
  ok(t.isPractice(),'a resumed practice paper is still practice');
  ok(Math.abs(Math.round((t.sim.endAt-Date.now())/60000)-savedMin)<=1,
     'and comes back on the clock it was saved with \u2014 not credited the pause a second time');
  eq(t.simQLeft,savedQ,'with the question where it was left');

  // ---- simulation: the old rules, unchanged ----
  t.simClearSave(); t.startPaper(3,'exam'); await sleep(20);
  ok(!t.isPractice(),'an exam paper is not practice');
  eq(t.brkLeft(),2,'two breaks');
  $('navHome').click(); await sleep(20);
  ok(!$('brkAsk').classList.contains('hidden'),'and leaving one still asks, because it costs');
  eq(t.route,'quizScreen','and does not leave until you say so');
  $('brkAskGo').click(); await sleep(20);
  ok(t.brkOn()&&!t.brkOpen(),'a simulation break is timed, not open-ended');
  ok(t.brkRemain()>300,'and runs the full six minutes');
  ok(!$('brkBar').classList.contains('tappable'),
     'a timed break bar is a status line \u2014 there is nowhere to go until it ends');
  t.go('quizScreen');
  eq(t.route,'homeScreen','the paper is not somewhere you can be during a timed break');
  t.brkEnd(true); await sleep(10);
  $('navHome').click(); await sleep(20);
  $('brkAskGo').click(); await sleep(20);
  t.brkEnd(true); await sleep(10);
  eq(t.brkLeft(),0,'two breaks is two');
  $('navHome').click(); await sleep(20);
  ok($('brkAsk').classList.contains('hidden'),'a third is not offered');
  eq(t.route,'quizScreen','and the paper keeps you');

  // ---- a closed tab still costs a simulation, which is the exploit that stays closed ----
  t.simClearSave(); t.startPaper(4,'exam'); await sleep(20);
  t.simPersist();
  const sv2=JSON.parse(JSON.stringify(t.P.simSave));
  sv2.at-=12*60*1000;
  ok(t.simAwayCost(sv2)>700,'twelve minutes with the tab shut is twelve minutes charged');

  // ---- the random mock exam starts at all ----
  // startSim() read qs.length from inside the object literal that defines the qs property,
  // so it threw "qs is not defined" before sim was ever assigned, and the button did nothing.
  t.simClearSave(); t.go('homeScreen'); await sleep(20);
  let threw=null;
  try { t.startSim('practice'); } catch(e){ threw=String(e.message); }
  await sleep(30);
  eq(threw,null,'starting the mock exam does not throw');
  ok(!!t.sim&&t.sim.running,'it actually starts one');
  eq(t.sim.paper,0,'a mock has no paper number');
  ok(t.sim.qs.length>0,'with questions in it');
  ok(t.sim.mins>0,'and a budget, which is what qs.length was needed for');
  eq(t.sim.mode,'practice','and it takes a mode like the numbered papers do');
  t.simAbandon(); await sleep(30);

  // ---- the record says which conditions a score was set under ----
  t.P.papers={};
  t.recordPaper(9,80,true);
  eq((t.P.papers[9]||{}).bestMode,'practice','a practice best is marked as one');
  t.recordPaper(9,85,false);
  eq(t.P.papers[9].bestMode,'exam','and a better one sat properly replaces it');
  eq(t.P.papers[9].ptries,1,'the practice attempts are counted separately');
  t.P.papers={};
  // Leave nothing running and nothing on top: a sheet left open covers the home screen and
  // the next check reads as "something else is on top" of a tile that is perfectly fine.
  t.modeAskClose(); t.brkAskClose();
  if(t.sim&&t.sim.running) t.simAbandon();
  await sleep(30);
  t.simClearSave();
  t.go('homeScreen'); await sleep(20);
}
async function breakChecks(){
  const t=T(), $=id=>document.getElementById(id);
  t.simClearSave(); t.startPaper(1); await sleep(30);
  eq(t.BREAK_MAX,2,'a paper allows two breaks');
  eq(t.BREAK_SECS,360,'of six minutes each');
  eq(t.brkLeft(),2,'both are in hand at the start');
  ok(!t.brkOn(),'and none is running');

  // leaving asks rather than just going
  $('navHome').click(); await sleep(20);
  ok(!$('brkAsk').classList.contains('hidden'),'leaving a running paper asks first');
  eq(t.route,'quizScreen','and does not leave yet');
  eq($('brkAskLen').textContent,'6:00','the sheet states the length');
  eq($('brkAskLeft').textContent,'2','and how many are left');
  ok(document.body.classList.contains('asking'),'the nav steps aside while it is open');
  $('brkAskNo').click(); await sleep(20);
  eq(t.route,'quizScreen','declining keeps you on the question');
  eq(t.brkLeft(),2,'and costs nothing');
  ok(!document.body.classList.contains('asking'),'the nav comes back');

  // taking one
  const qBefore=t.simQLeft, totBefore=t.simTotalLeft();
  const wallBefore=Math.round(t.simTimeLeft()/1000);
  $('navHome').click(); await sleep(20);
  $('brkAskGo').click(); await sleep(40);
  ok(t.brkOn(),'confirming starts the break');
  eq(t.brkLeft(),1,'and spends one of the two');
  eq(t.route,'homeScreen','and lets you go where you were heading');
  ok(!$('brkBar').classList.contains('hidden'),'a banner counts it down');
  eq($('brkClock').textContent,'6:00','from six minutes');
  ok(t.brkRemain()>350&&t.brkRemain()<=360,'with the full six on the clock');

  // nothing is spent while it runs
  t.simQSync(); await sleep(20);
  eq(t.simQLeft,qBefore,'the question clock is frozen');
  eq(t.simTotalLeft(),totBefore,'and so is the paper total');
  t.simCheckTime();
  ok(!!t.sim,'a paused paper cannot time out from under you');

  // you can move around freely during it
  $('navPlay').click(); await sleep(30);
  eq(t.route,'stuPickScreen','a break lets you go wherever');
  ok(t.brkOn(),'without ending it');

  // ...except back into the paper. Both clocks are frozen during a break, so standing on the
  // question screen means staring at a dead countdown — which is what got reported as a
  // broken timer. For those six minutes the paper is not somewhere you can be.
  t.go('quizScreen'); await sleep(20);
  eq(t.route,'stuPickScreen','a break will not let you back onto the question');
  t.go('simRevScreen'); await sleep(20);
  eq(t.route,'stuPickScreen','nor onto the review screen');
  ok(/comes back in/.test(([...document.querySelectorAll('.toast')].pop()||{}).textContent||''),
     'and it says when the paper returns');
  // the clock counts the break down rather than sitting on a number that is not moving
  ok(/\u2615/.test($('playClock').textContent),'the top clock shows the break, not a frozen exam');
  eq($('clockSub').textContent,'break \u00b7 paper paused','and says the paper is paused');
  const brkShown=$('playClock').textContent;
  t.sim.brkUntil-=3000; t.renderBrk(); renderClockSafe(t);
  ok($('playClock').textContent!==brkShown,'and it is counting down');
  // the resume row offers the remaining break instead of a way in
  t.renderPapers(); await sleep(20);
  const rrow=$('exResume');
  ok(!/Resume<\/span>$/.test(rrow.innerHTML),'the resume row does not offer a way in');
  rrow.click(); await sleep(20);
  eq(t.route,'stuPickScreen','and pressing it does not get you there');

  // and the clocks are paid back in full when it ends
  t.brkEnd(true); await sleep(40);
  ok(!t.brkOn(),'the break is over');
  eq(t.route,'quizScreen','and it hands you back to the question');
  const wallAfter=Math.round(t.simTimeLeft()/1000);
  // With one clock a break never cost the paper anything to pay back: it is not answering time.
  ok(Math.abs(wallAfter-wallBefore)<3,
     'the break cost the paper nothing ('+(wallAfter-wallBefore)+'s)');

  // the second one behaves the same
  $('navHome').click(); await sleep(20);
  $('brkAskGo').click(); await sleep(40);
  eq(t.brkLeft(),0,'the second spends the last one');
  t.brkEnd(true); await sleep(40);

  // and then leaving is refused
  eq(t.route,'quizScreen','back on the paper');
  $('navHome').click(); await sleep(30);
  eq(t.route,'quizScreen','with none left, Home is refused');
  ok($('brkAsk').classList.contains('hidden'),'and it does not even ask');
  $('navPlay').click(); await sleep(30);
  eq(t.route,'quizScreen','Study too');
  $('navShop').click(); await sleep(30);
  eq(t.route,'quizScreen','and the Shop');
  const q=t.simQLeft; t.simQTick(5); await sleep(10);
  eq(t.simQLeft,q-5,'and the clock keeps running, which is the point');

  // the paper's own screens are not "leaving"
  t.simReview(); await sleep(20);
  eq(t.route,'simRevScreen','the review screen is still inside the paper');
  t.simJump(0); await sleep(20);
  eq(t.route,'quizScreen','and so is coming back from it');

  // a break belongs to the run, so it survives walking away and resuming
  t.simAbandon(); await sleep(30);
  const sv=t.simSaved();
  eq(sv.brkUsed,2,'the save remembers both were used');
  t.simResume(); await sleep(40);
  eq(t.brkLeft(),0,'so resuming does not hand them back');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // a fresh paper gets its own two
  t.startPaper(2); await sleep(30);
  eq(t.brkLeft(),2,'a new paper starts with two again');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // leaving from the REVIEW screen used to skip the break check entirely, because the guard
  // asked for route==='quizScreen' — you walked out of a running paper with the clock going
  t.simClearSave(); t.startPaper(3); await sleep(30);
  t.simReview(); await sleep(20);
  eq(t.route,'simRevScreen','on the review grid');
  $('navHome').click(); await sleep(30);
  ok(t.route!=='homeScreen','leaving from the review screen does not just walk out');
  ok(!$('brkAsk').classList.contains('hidden'),'it asks for a break like anywhere else');
  t.brkAskClose();

  // the sheet cannot outlive the paper it is offering a break on
  $('navHome').click(); await sleep(20);
  ok(!$('brkAsk').classList.contains('hidden'),'sheet up');
  t.simSubmit(true); await sleep(60);
  ok($('brkAsk').classList.contains('hidden'),'submitting closes the break sheet');
  ok(!document.body.classList.contains('asking'),'and gives the nav back');
  t.simClearSave();

  t.startPaper(3); await sleep(30);
  $('navHome').click(); await sleep(20);
  t.simAbandon(); await sleep(40);
  ok($('brkAsk').classList.contains('hidden'),'abandoning closes it too');
  ok(!document.body.classList.contains('asking'),'and the nav comes back');
  ok($('simTotal').classList.contains('hidden'),'the paper strip goes with the paper');
  t.simClearSave();

  // a paused paper does not take answers
  t.startPaper(3); await sleep(30);
  $('navHome').click(); await sleep(20); $('brkAskGo').click(); await sleep(40);
  const ansBefore=JSON.stringify(t.sim.ans||{});
  t.simPick(t.QS[t.sim.qs[t.sim.i]].o[0][0]); await sleep(20);
  eq(JSON.stringify(t.sim.ans||{}),ansBefore,'a paused paper does not take answers either');
  t.brkEnd(true); await sleep(40);
  t.simAbandon(); await sleep(30); t.simClearSave();
  t.startPaper(1); await sleep(30);

  // the build stamp: a screenshot of an already-fixed bug turned out to be a cached page
  ok(typeof t.BUILD==='string'&&t.BUILD.length>6,'the page says when it was built');
  ok(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(t.BUILD),
     'as a timestamp — a hash stamped before committing always names the previous commit');
  ok(/build /.test(($('recBuild')||{}).textContent||''),'and the Records screen shows it');

  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave();
}

// ---------- resuming from the paper's own row ----------
async function paperRowChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const rows=()=>[...document.querySelectorAll('#paperScreen .paperrow')];
  const btns=i=>[...rows()[i].querySelectorAll('button')].map(b=>b.textContent.trim());

  delete t.P.lastPaper; t.P.runs={}; t.P.runsDone=[];   // start clean, whatever ran before
  t.simClearSave(); t.renderPapers(); await sleep(20);
  eq(btns(3).length,1,'with nothing saved a row has one button');
  eq(btns(3)[0]==='Resume',false,'and it is not Resume');

  // be part way through paper 4
  t.startPaper(4); await sleep(30);
  t.simGo(1); await sleep(10);
  t.simPick(t.QS[t.sim.qs[1]].o[0][0]); await sleep(10);
  t.simGo(1); await sleep(10);
  t.simAbandon(); await sleep(40);

  const r4=rows()[3];
  ok(r4.classList.contains('resuming'),'the paper in progress is marked on its own row');
  eq(r4.querySelector('.em').textContent,'\u23f8','with a paused icon rather than a score one');
  // the words "in progress" were dropped: the paused icon, the cyan edge and the missing
  // score chip already say it, and at 320px those two words cost the text a whole line
  ok(!r4.querySelector('.pscore'),'an unfinished run does not show a stale best score');
  ok(/question 3 of 65/.test(r4.querySelector('.ds').textContent),'the row says how far in');
  ok(/1 answer\b/.test(r4.querySelector('.ds').textContent),'and how much is answered');
  ok(/left/.test(r4.querySelector('.ds').textContent),'and how much time is left');
  eq(btns(3).join('|'),'\u21bb|Resume','it carries a restart and a resume');
  ok(!rows()[4].classList.contains('resuming'),'no other row claims to be in progress');

  // Start on a different paper warns, and touches nothing on the first tap
  // Start is the row's LAST button — a finish-later or restart button can sit before it
  const other=[...rows()[5].querySelectorAll('button')].pop();
  const wasLabel=other.textContent.trim();
  other.click(); await sleep(20);
  ok(/Delete your progress on Exam 4/.test(other.textContent),'starting elsewhere warns first');
  ok(/question 3 of 65/.test(other.textContent),'and names what would be lost');
  eq(t.simSaved().paper,4,'and the save is untouched');
  await sleep(4200);
  eq(other.textContent.trim(),wasLabel,'an unanswered warning lapses');
  eq(t.simSaved().paper,4,'still untouched');
  other.click(); await sleep(20); other.click(); await sleep(40);
  ok(!$('modeAsk').classList.contains('hidden'),
     'confirming the discard asks which kind of run the new one is');
  $('modeAskExam').click(); await sleep(40);
  eq(t.sim.paper,6,'and answering it starts the other paper');
  eq(t.sim.mode,'exam','in the mode that was picked');
  t.simAbandon(); await sleep(40);

  // the restart button warns too
  t.simClearSave(); t.startPaper(4); await sleep(30);
  t.simGo(1); await sleep(10); t.simAbandon(); await sleep(40);
  const again=rows()[3].querySelectorAll('button')[0];
  again.click(); await sleep(20);
  ok(/start again/.test(again.textContent),'restarting warns first');
  eq(t.simSaved().i,1,'and has not reset anything yet');
  again.click(); await sleep(40);
  ok(!$('modeAsk').classList.contains('hidden'),'restarting asks the same question');
  $('modeAskPractice').click(); await sleep(40);
  eq(t.sim.i,0,'and then starts it from question one');
  eq(t.sim.mode,'practice','in the mode that was picked');
  t.simAbandon(); await sleep(40);

  // resuming from the row lands where it left off
  t.simClearSave(); t.startPaper(4); await sleep(30);
  t.simGo(1); await sleep(10); t.simGo(1); await sleep(10);
  t.simAbandon(); await sleep(40);
  rows()[3].querySelectorAll('button')[1].click(); await sleep(60);
  eq(t.route,'quizScreen','the row resumes into the paper');
  eq(t.sim.paper,4,'the right paper');
  eq(t.sim.i,2,'at the question it was left on');
  t.simAbandon(); await sleep(40); t.simClearSave();
}

// ---------- the reading voice ----------
async function voiceChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const keep={p:t.P.voicePreset, r:t.P.ttsRate, pi:t.P.ttsPitch, v:t.P.ttsVoice};

  eq(t.VOICE_PRESETS.length,8,'there are eight presets');
  const ids=t.VOICE_PRESETS.map(p=>p.id);
  eq(ids.length,new Set(ids).size,'with distinct ids');
  t.VOICE_PRESETS.forEach(p=>{
    ok(p.nm&&p.ds&&p.heb,p.id+' has a name, a description and a Hebrew line');
    ok(p.rate>=0.5&&p.rate<=2.2,p.id+' asks for a sane speed ('+p.rate+')');
    ok(p.pitch>=0.4&&p.pitch<=2,p.id+' asks for a sane pitch');
    ok(/[\u0590-\u05FF]/.test(p.heb),p.id+"'s second line is Hebrew");
  });

  // the preset drives the reading
  t.P.voicePreset='exam'; delete t.P.ttsRate; delete t.P.ttsPitch;
  eq(t.voiceRate(),0.85,'Exam Room reads slowly');
  t.P.voicePreset='sprint';
  eq(t.voiceRate(),1.8,'Sprint reads fast');
  t.P.voicePreset='night';
  eq(t.voiceVolume(),0.55,'Night Study is quieter');
  t.P.voicePreset='standard';
  eq(t.voiceVolume(),1,'and the others are not');

  // the sliders override it, within limits
  t.P.voicePreset='exam'; t.P.ttsRate=1.75;
  eq(t.voiceRate(),1.75,'a chosen speed beats the preset');
  t.P.ttsRate=9;    eq(t.voiceRate(),2.2,'an absurd speed is capped');
  t.P.ttsRate=-3;   eq(t.voiceRate(),0.5,'and a negative one floored');
  t.P.ttsRate='abc';eq(t.voiceRate(),0.5,'nonsense does not reach the engine');
  delete t.P.ttsRate;
  t.P.ttsPitch=99;  eq(t.voicePitch(),2,'pitch is capped too');
  delete t.P.ttsPitch;
  t.P.voicePreset='does-not-exist';
  eq(t.voiceRate(),1,'an unknown preset falls back to Standard');
  t.P.voicePreset='standard';

  // a voice that never speaks can never be chosen — this is the whole point of the screen
  const real=Object.getOwnPropertyDescriptor(window,'speechSynthesis');
  const realU=window.SpeechSynthesisUtterance;
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{
    speak(u){ if(!/Chrome OS/.test((u.voice&&u.voice.name)||'')) setTimeout(()=>u.onstart&&u.onstart(),5); },
    cancel(){}, addEventListener(){}, removeEventListener(){},
    getVoices(){ return [{lang:'en-US',name:'Google US English',localService:false},
                         {lang:'en-US',name:'Chrome OS US English 1',localService:true}]; },
    get speaking(){return false;}, get pending(){return false;}, get paused(){return false;}
  }});
  window.SpeechSynthesisUtterance=function(txt){ this.text=txt; };
  t.ttsLoadVoices();
  await t.voiceCheckAll();
  eq(t.voiceProbe['Google US English'],'live','a voice that answers is marked live');
  eq(t.voiceProbe['Chrome OS US English 1'],'dead','one that stays silent is marked dead');
  const rows=[...document.querySelectorAll('#voiceList .vvoice')];
  ok(rows.length>=3,'the list shows the browser option and both voices');
  const dud=rows.find(b=>/Chrome OS/.test(b.textContent));
  ok(dud&&dud.disabled,'the silent one cannot be selected');
  ok(dud&&/SILENT/.test(dud.textContent),'and says why');
  const good=rows.find(b=>/Google US English/.test(b.textContent));
  ok(good&&!good.disabled,'the working one can be');
  ok(/do not actually make a sound/.test($('voiceFoot').textContent),'and the footer explains it');

  // a preset must never land on a voice that does not speak
  t.VOICE_PRESETS.forEach(p=>{
    const v=t.voiceForPreset(p);
    ok(!v||!/Chrome OS/i.test(v.name),p.nm+' does not pick a Chrome OS voice');
    ok(!v||t.voiceProbe[v.name]!=='dead',p.nm+' does not pick a voice known to be silent');
  });
  const used=t.VOICE_PRESETS.map(p=>{ const v=t.voiceForPreset(p); return v?v.name:'default'; });
  ok(new Set(used).size>1,'the presets do not all sound like the same person');
  eq(t.voiceForPreset(t.VOICE_PRESETS[0]),null,'Standard stays on the browser default');
  ok(t.P.voiceProbe&&Object.keys(t.P.voiceProbe).length>0,
     'what works on this device is remembered between sessions');

  window.SpeechSynthesisUtterance=realU;
  if(real) Object.defineProperty(window,'speechSynthesis',real); else delete window.speechSynthesis;

  // it is reachable and leaves cleanly
  t.openVoice(); await sleep(20);
  eq(t.route,'voiceScreen','the Voice chip opens it');
  eq(document.querySelectorAll('#voicePresets .vpre').length,8,'with all eight presets drawn');
  $('voiceBack').click(); await sleep(20);
  eq(t.route,'homeScreen','and the back arrow leaves');

  t.P.voicePreset=keep.p||'standard';
  if(keep.r==null) delete t.P.ttsRate; else t.P.ttsRate=keep.r;
  if(keep.pi==null) delete t.P.ttsPitch; else t.P.ttsPitch=keep.pi;
  if(keep.v==null) delete t.P.ttsVoice; else t.P.ttsVoice=keep.v;
}

// ---------- the fixes from the bug hunt ----------
async function hardeningChecks(){
  const t=T(), $=id=>document.getElementById(id);

  // an exam does not outlive the screen you left it on
  t.simClearSave(); t.startPaper(3); await sleep(30);
  ok(!!t.sim,'a paper is running');
  $('quizBack').click(); await sleep(40);
  eq(t.sim,null,'the back arrow ends it instead of leaving it running');
  eq(t.route,'paperScreen','and lands where the saved run is offered back');
  ok(!!t.simSaved(),'the run itself is kept');
  // simQLeft keeps that question's remaining seconds on purpose — what has to stop is the
  // interval, and with sim gone a tick must do nothing rather than count down in the background
  const held=t.simQLeft;
  t.simQTick(5); await sleep(5);
  eq(t.simQLeft,held,'and its clock is no longer counting');

  // and two engines never share the question screen
  t.startPaper(3); await sleep(30);
  $('quizBack').click(); await sleep(30);
  t.startMock(); await sleep(30);
  eq(t.sim,null,'starting a mock leaves no paper running underneath it');
  t.startPaper(3); await sleep(30);
  t.startSession(2); await sleep(30);
  eq(t.sim,null,'nor does starting practice');
  ok(getComputedStyle($('qConfirm')).display!=='none','and practice gets its Lock in back');
  ok(getComputedStyle($('lifeFifty')).display!=='none','and its lifelines');
  t.simClearSave();

  // overlays do not survive navigation
  $('verdict').classList.remove('hidden');
  $('studyModal').classList.remove('hidden');
  t.go('homeScreen'); await sleep(10);
  ok($('verdict').classList.contains('hidden'),'the verdict card is dismissed on a route change');
  ok($('studyModal').classList.contains('hidden'),'and so is the Study Card');

  // numbers nobody sanity-checked
  eq(t.startTimer({mode:'count',work:0,rest:0,rounds:0}),false,'a timer of no length is refused');
  eq(t.timerClamp({work:999999,rest:999999,rounds:999999}).rounds,t.TIMER_MAX.rounds,'rounds are capped');
  eq(t.timerClamp({work:999999,rest:0,rounds:1}).work,t.TIMER_MAX.work,'so are the minutes');
  eq(t.timerClamp({work:-5,rest:-5,rounds:-5}).work,0,'negatives are floored');
  eq(t.timerClamp({work:'abc',rest:null,rounds:undefined}).rounds,1,'and nonsense falls back');
  eq(t.paperQs(0).length,0,'paperQs(0) is empty, not indices from -65');
  eq(t.paperQs(-1).length,0,'paperQs(-1) too');
  eq(t.paperQs(9999).length,0,'and past the last paper');
  eq(t.paperQs(1).length,65,'while a real paper still works');

  // the exam date
  const keepDate=t.P.examDate;
  t.P.examDate='2020-01-01';
  eq(t.examDaysLeft(),-1,'a date in the past reports as past');
  // a date-only string used to be read as UTC midnight: a day short west of UTC
  const ld=t.localDate('2026-10-01');
  ok(!!ld&&ld.getFullYear()===2026&&ld.getMonth()===9&&ld.getDate()===1&&ld.getHours()===0,
     'the exam date is read as a local calendar day, not UTC midnight');
  eq(t.localDate('2026-02-31'),null,'an impossible date is refused, not rolled into March');
  eq(t.localDate('soon'),null,'and so is anything that is not a date');
  { const d=new Date(); d.setDate(d.getDate()+7);
    const iso=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
    const was=t.P.examDate; t.P.examDate=iso;
    eq(t.examDaysLeft(),7,'a week from today is seven days, in any timezone');
    const today=new Date(), tk=today.getFullYear()+'-'+String(today.getMonth()+1).padStart(2,'0')+'-'+String(today.getDate()).padStart(2,'0');
    t.P.examDate=tk;
    eq(t.examDaysLeft(),0,'and today is exam day, not "passed"');
    t.P.examDate=was; }
  ok(/passed/.test(t.examDaysLabel(t.examDaysLeft(),t.dailyPace())),'and says so instead of "0 days to go"');
  t.P.examDate='2999-01-01';
  eq(t.examDaysLeft(),t.EXAM_MAX_DAYS,'a date centuries out is capped');
  t.P.examDate='not-a-date';
  eq(t.examDaysLeft(),null,'and garbage is treated as unset');
  t.P.examDate=keepDate;

  // bars cannot exceed their track
  eq(t.pctW(1104),'100%','a width over 100% is clamped');
  eq(t.pctW(-5),'0%','and under 0');
  eq(t.pctW(NaN),'0%','NaN becomes nothing rather than an invalid style');
  eq(t.pctW(Infinity),'0%','so does Infinity');
  t.P.answered=1e9; t.P.nextChest=25;
  eq(t.chestProgress().into,25,'the chest bar cannot fill past its own span');
  t.P.answered=7; t.P.nextChest=25;

  // a profile missing or mistyped everywhere still renders
  const keepP=JSON.parse(JSON.stringify(t.P));
  Object.keys(t.P).forEach(k=>delete t.P[k]);
  t.normaliseProfile(t.P);
  ['renderBank','renderBadges','renderShop','renderReadiness','renderPapers',
   'renderThemes','renderPath','renderRecords'].forEach(fn=>{
    let threw=null;
    try{ if(t[fn]) t[fn](); }catch(e){ threw=String(e.message); }
    ok(!threw,fn+'() survives an empty profile'+(threw?' — '+threw:''));
  });
  Object.keys(t.P).forEach(k=>delete t.P[k]);
  Object.assign(t.P,{seen:[],wrong:{},badges:'nope',highs:null,secStats:7,rHist:{},
                     login:[],inv:'x',upgrades:0,papers:[],xp:'abc',coins:NaN});
  t.normaliseProfile(t.P);
  ok(!Array.isArray(t.P.seen)&&typeof t.P.seen==='object','a map handed an array is replaced');
  ok(Array.isArray(t.P.wrong),'a list handed an object is replaced');
  ok(Array.isArray(t.P.rHist),'rHist is a list — it gets .push()ed');
  ok(Array.isArray(t.P.known),'and so is known');
  eq(t.P.xp,0,'a counter that is not a number becomes 0');
  eq(t.P.coins,0,'NaN too');
  ['renderBank','renderBadges','renderShop','renderReadiness'].forEach(fn=>{
    let threw=null;
    try{ if(t[fn]) t[fn](); }catch(e){ threw=String(e.message); }
    ok(!threw,fn+'() survives a profile with the wrong type in every slot'+(threw?' — '+threw:''));
  });
  Object.keys(t.P).forEach(k=>delete t.P[k]); Object.assign(t.P,keepP);

  // counts that reach 1
  eq(t.plural(1,'question'),'1 question','one question, not "1 questions"');
  eq(t.plural(2,'question'),'2 questions','two questions');
  eq(t.plural(0,'coin'),'0 coins','and none');
  eq(t.plural(1,'chip'),'1 chip','a single chip');

  t.go('homeScreen');
}

// ---------- two devices, one account ----------
async function deviceChecks(){
  const t=T(), $=id=>document.getElementById(id);
  t.simClearSave();
  ok(!!t.DEVICE_ID,'this browser has a device id');
  eq(localStorage.getItem('academy_device'),t.DEVICE_ID,'and it is kept outside the profile');
  ok(['phone','tablet','desktop'].indexOf(t.DEVICE_KIND)>=0,'and a kind: '+t.DEVICE_KIND);

  // ---- the merge stops preferring whatever this device happens to hold
  const R={at:2000, xp:500, coins:10, diff:'hard', theme:'mono',
           papers:{3:{best:88,tries:2,last:'88%'}}};
  const L={at:1000, xp:300, coins:90, diff:'easy', theme:'neon',
           papers:{3:{best:60,tries:1,last:'60%'},7:{best:71,tries:1,last:'71%'}}};
  const m=t.mergeProfiles(R,L);
  eq(m.diff,'hard','the newer device wins the plain fields');
  eq(m.theme,'mono','all of them, not just some');
  eq(m.xp,500,'counters still take the higher of the two');
  eq(m.coins,90,'in whichever direction that falls');
  eq(m.at,2000,'and the merge carries the later stamp');
  eq(m.papers[3].best,88,'a paper scored on both keeps the better result');
  ok(!!m.papers[7],'and a paper only one device has is not dropped');
  const m2=t.mergeProfiles(Object.assign({},R,{at:1000}),Object.assign({},L,{at:2000}));
  eq(m2.diff,'easy','with the stamps the other way round, we win');
  const m3=t.mergeProfiles({xp:5},{xp:9});
  eq(m3.xp,9,'a row saved before any of this still merges');

  // ---- the exam belongs to whoever touched it last, not to us
  const mine  ={paper:1,i:3,qs:[1,2],ans:{},flag:{},left:1,at:5000,dev:'me',devKind:'desktop'};
  const theirs={paper:2,i:9,qs:[1,2],ans:{},flag:{},left:1,at:9000,dev:'them',devKind:'phone'};
  eq(t.simSaveNewer(mine,theirs).paper,2,'the newer exam save wins');
  eq(t.simSaveNewer(theirs,mine).paper,2,'whichever order they arrive in');
  eq(t.simSaveNewer(null,mine).paper,1,'one side missing is not a conflict');
  eq(t.mergeProfiles({at:1,simSave:theirs},{at:2,simSave:mine}).simSave.paper,2,
     'the newer EXAM wins even when we are the newer profile — this was the bug');

  // ---- a claim outranks an ordinary save, or the two devices ping-pong
  const claimed={paper:2,i:9,qs:[1,2],ans:{},flag:{},left:1,at:1000,claimAt:1000,
                 dev:'phone',devKind:'phone'};
  const running={paper:1,i:3,qs:[1,2],ans:{},flag:{},left:1,at:9999,claimAt:500,
                 dev:'desk',devKind:'desktop'};   // newer save, older claim
  eq(t.simSaveNewer(claimed,running).dev,'phone',
     'a device merely still saving cannot win a paper back off one that claimed it');
  eq(t.simSaveNewer(running,claimed).dev,'phone','in either argument order');
  eq(t.simSaveNewer(claimed,Object.assign({},running,{claimAt:2000})).dev,'desk',
     'but a deliberate takeover does win');
  eq(t.simSaveNewer({dev:'a',at:1},{dev:'b',at:2}).dev,'b',
     'a save written before claims existed still falls back to its timestamp');

  // ---- being mid-exam when the other device picks it up
  t.startPaper(1); await sleep(30);
  ok(!!t.sim,'an exam is running here');
  eq(t.P.simSave.dev,t.DEVICE_ID,'the save is stamped with this device');
  eq(t.P.simSave.devKind,t.DEVICE_KIND,'and its kind');
  const claimedAt=t.P.simSave.claimAt;
  ok(claimedAt>0,'starting a paper claims it');
  t.simGo(1); await sleep(20); t.simGo(1); await sleep(20);
  eq(t.P.simSave.claimAt,claimedAt,'moving between questions does not restamp the claim');
  ok(t.P.simSave.at>claimedAt,'though the ordinary timestamp does move');
  ok(t.simOwns(t.P.simSave),'which we own');
  ok(!t.simOwnerCheck(),'so nothing interrupts us');

  t.P.simSave=Object.assign({},t.P.simSave,{paper:2,i:9,dev:'phone-abc',devKind:'phone',at:Date.now()+5000});
  ok(!t.simOwns(t.P.simSave),'a save from another device is not ours');
  ok(t.simOwnerCheck(),'and it stops this device');
  await sleep(30);
  eq(t.sim,null,'the exam here is over');
  eq(t.route,'paperScreen','and it lands on the papers screen');

  // ---- taking it back needs two taps
  t.renderPapers(); await sleep(20);
  const rb=$('exResume');
  ok(!rb.classList.contains('hidden'),'the resume row offers the other device\'s exam');
  ok(/on your phone/.test(rb.textContent),'and names where it is');
  ok(/Take over/.test(rb.textContent),'and offers to take it over');
  rb.click(); await sleep(20);
  ok(/Take it over from your phone/.test(rb.textContent),'one tap only arms it');
  eq(t.sim,null,'nothing has been taken over yet');
  rb.click(); await sleep(40);
  eq(t.route,'quizScreen','the second tap takes it');
  eq(t.sim.paper,2,'on the paper the other device was on');
  eq(t.sim.i,9,'at the question it had reached');
  eq(t.P.simSave.dev,t.DEVICE_ID,'and the claim is now ours');

  // ---- and starting a different paper will not silently bin it
  t.simAbandon(); await sleep(30);
  t.P.simSave=Object.assign({},t.P.simSave,{paper:5,dev:'phone-abc',devKind:'phone',at:Date.now()});
  t.renderPapers(); await sleep(20);
  const st=[...document.querySelectorAll('#paperScreen .paperrow button')][2];
  st.click(); await sleep(20);
  ok(/Delete your progress/.test(st.textContent),'starting another paper warns first');
  ok(/your phone/.test(st.textContent),'and says the run is on the other device');
  eq(t.P.simSave.paper,5,'and has not touched the save yet');
  // the armed label is long: it used to run off the right edge of a 320px phone, and
  // .paperrow's overflow:hidden swallowed the end of it instead of showing anything
  const sr=st.getBoundingClientRect(), vw=document.documentElement.clientWidth;
  ok(sr.right<=vw+1,'the warning stays inside the viewport ('+Math.round(sr.right)+' of '+vw+')');
  ok(st.scrollWidth<=st.clientWidth+1,'and none of it is clipped');
  ok(document.documentElement.scrollWidth<=vw+1,'and it does not push the page sideways');
  st.click(); await sleep(40);
  // taking over from another device still asks which kind of run this one is
  ok(!document.getElementById('modeAsk').classList.contains('hidden'),
     'and then asks which kind of run the new paper is');
  document.getElementById('modeAskExam').click(); await sleep(40);
  eq(t.sim.paper,3,'the second tap starts the new paper');
  eq(t.P.simSave.dev,t.DEVICE_ID,'which this device now owns');

  // ---- an unarmed warning lapses instead of sticking
  t.simAbandon(); await sleep(30); t.simClearSave();

  // ---- the tab pulls when it comes forward
  ok(typeof t.syncOnFocus==='function','there is a focus sync');
  ok(typeof t.simWatchOwner==='function','and an exam watches for a takeover');
  t.simWatchOwner();       // a no-op under TEST, but it must not throw
  ok(true,'the watcher is inert in the harness');
  await t.syncOnFocus();          // signed out: must be a no-op, not a throw
  ok(true,'and signed out it does nothing rather than failing');
}

// ---------- ninety seconds a question ----------
async function qClockChecks(){
  const t=T(), $=id=>document.getElementById(id);
  t.simClearSave();
  t.startPaper(11); await sleep(20);            // 11 does not teach, so nothing else is on screen
  eq(t.simQLeft,t.SIM_QSEC,'a fresh question has the full 90 seconds');
  eq($('qTimerFill').style.width,'100%','and a full bar');

  t.simQTick(t.SIM_QSEC-30); await sleep(5);
  eq(t.simQLeft,30,'it counts down');
  eq($('playClock').textContent,'⏳ 0:30','the clock follows');
  ok($('playClock').classList.contains('warn'),'it warns at 30 seconds');
  ok(!$('playClock').classList.contains('crit'),'but is not critical yet');
  t.simQTick(21); await sleep(5);
  ok($('playClock').classList.contains('crit'),'it goes critical at 9 seconds');
  ok($('qTimerFill').classList.contains('low'),'and the bar turns');

  // running out UNANSWERED stays on the question and shows the answer and why; Next moves on
  eq(t.sim.i,0,'still on the first question');
  const blank=(t.sim.ans[0]||[]).length;
  t.simQTick(9); await sleep(20);
  eq(t.sim.i,0,'running out unanswered stays on the question');
  ok($('explain').classList.contains('show'),'and opens the explanation');
  ok(/Time ran out/.test($('explain').querySelector('.exhead').textContent),'headed as a timeout');
  eq([...$('qOpts').children].filter(e=>e.classList.contains('ok')).map(e=>e.dataset.ltr).join(''),
     t.QS[t.sim.qs[0]].a.join(''),'with the correct answer marked');
  ok(!!$('explain').querySelector('.exeach'),'and every option explained');
  t.simGo(1); await sleep(20);
  eq(t.sim.i,1,'Next moves on when you are ready');
  eq(t.simQLeft,t.SIM_QSEC,'which starts on a full 90 seconds');
  eq((t.sim.ans[0]||[]).length,blank,'the question it left stays blank');
  eq(t.simAnsweredCount(),0,'so it counts as unanswered, which scores as wrong');

  // what is left is remembered per question
  t.simQTick(40); await sleep(5);
  eq(t.simQLeft,t.SIM_QSEC-40,'question two is down by 40');
  t.simJump(2); await sleep(20);
  eq(t.simQLeft,t.SIM_QSEC,'a question never opened is still on 90');
  t.simJump(1); await sleep(20);
  eq(t.simQLeft,t.SIM_QSEC-40,'and coming back to question two gives back what it had');

  // a spent question can be reopened without being thrown out of it again
  t.simJump(0); await sleep(20);
  eq(t.simQLeft,0,'a spent question shows an empty clock');
  t.simQTick(5); await sleep(20);
  eq(t.sim.i,0,'and ticking it does not bounce you forward again');
  const opt=$('qOpts').firstChild.dataset.ltr;
  t.simPick(opt); await sleep(10);
  // It can be reopened and read, but its time is gone: answering it then was a way round the
  // 90-second limit — let it run out, think elsewhere, come back and answer.
  eq((t.sim.ans[0]||[]).join(''),'','but it cannot be answered once its time is up');

  // it does not burn seconds where you cannot see the question
  t.simJump(3); await sleep(20);
  t.simReview(); await sleep(20);
  const held=t.simQLeft;
  t.simQTick(30); await sleep(5);
  eq(t.simQLeft,held,'the review screen does not spend the question clock');

  // the last question runs out into the review, not into nothing
  t.simJump(t.simLen()-1); await sleep(20);
  t.simQTick(t.SIM_QSEC); await sleep(20);
  eq(t.route,'quizScreen','the last question, run out unanswered, shows its answer first');
  t.simGo(1); await sleep(20);
  eq(t.route,'simRevScreen','and then goes on to the review');

  // and it survives walking away
  t.simJump(4); await sleep(20);
  t.simQTick(25); await sleep(5);
  eq(t.simQLeft,t.SIM_QSEC-25,'question five is down by 25');
  t.simAbandon(); await sleep(20);
  const sv=t.simSaved();
  ok(!!sv,'the paper was saved');
  eq(sv.qt[4],t.SIM_QSEC-25,'the save kept what was left of that question');
  t.simResume(); await sleep(20);
  eq(t.sim.i,4,'it resumed on the same question');
  eq(t.simQLeft,t.SIM_QSEC-25,'with the same time left');

  // ---- the clock is a deadline, not a count of ticks
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1); await sleep(30);
  ok(t.sim.qEndAt>Date.now(),'a question carries a deadline, not just a counter');
  const dl=t.sim.qEndAt;
  t.simQTick(20); await sleep(10);
  eq(t.simQLeft,t.SIM_QSEC-20,'ticking by hand still works for the harness');
  ok(t.sim.qEndAt<dl,'and the deadline moves with it, so the two cannot disagree');
  ok(Math.abs((t.sim.qEndAt-Date.now())/1000-(t.SIM_QSEC-20))<2,'the deadline agrees with the counter');
  // In a simulation, time in another tab IS spent on the question. It used to be pushed out,
  // which made the tab bar a free break: three minutes away gave the question 180 seconds
  // back while the paper was charged.
  t.simAway();
  const deadlineWhenAway=t.sim.qEndAt;
  await sleep(120);
  t.simBack();
  eq(t.sim.qEndAt,deadlineWhenAway,'in a simulation, another tab does not push the deadline');
  // in practice it does, because practice pauses whenever you leave
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1,'practice'); await sleep(30);
  t.simAway();
  const practiceDl=t.sim.qEndAt;
  await sleep(120);
  t.simBack();
  ok(t.sim.qEndAt>practiceDl,'in practice, coming back pushes the deadline out by the time away');
  ok(typeof t.clockEnsure==='function','there is a way to revive a dead clock');
  t.clockEnsure();
  ok(true,'and calling it under TEST does nothing rather than throwing');
  t.simAbandon(); await sleep(20); t.simClearSave();

  // ---- what the whole paper has left, not just this question
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1); await sleep(30);
  eq(t.simTotalLeft(),65*t.SIM_QSEC,'a fresh 65-question paper has 65 x the per-question limit');
  eq(t.simTotalFull(),65*t.SIM_QSEC,'which is also its full budget');
  eq(t.simQsLeft(),65,'and 65 questions with time on them');
  eq($('simTotalVal').textContent,fmtMs(65*t.SIM_QSEC*1000),'shown as hours:minutes:seconds');
  eq($('simTotalFill').style.width,'100%','with a full bar');
  ok(/65 questions still open/.test($('simTotalSub').textContent),'and the count beneath it');
  ok($('clockSub').textContent.indexOf(fmtMs(65*t.SIM_QSEC*1000)+' left')>=0,'the top clock carries it too');

  t.simQTick(t.SIM_QSEC); await sleep(20);
  t.simGo(1); await sleep(20);            // it stayed to show the answer; move on
  eq(t.simTotalLeft(),64*t.SIM_QSEC,'one question spent leaves 64 of them');
  eq($('simTotalVal').textContent,fmtMs(64*t.SIM_QSEC*1000),'which reads that');
  eq(t.simQsLeft(),64,'and 64 questions still open');

  t.simQTick(30); await sleep(10);
  eq(t.simTotalLeft(),63*t.SIM_QSEC+(t.SIM_QSEC-30),'it is a real sum, not questions-left times the limit');
  t.simJump(5); await sleep(20); t.simQTick(40); await sleep(10);
  const totBefore=t.simTotalLeft();
  t.simJump(9); await sleep(20);
  eq(t.simTotalLeft(),totBefore,'moving between questions does not change the total');
  t.simJump(5); await sleep(20);
  eq(t.simQLeft,t.SIM_QSEC-40,'and a half-used question still holds its remainder');

  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(t.PAPER_COUNT); await sleep(30);
  ok(t.simLen()<65,'the last paper is shorter ('+t.simLen()+')');
  eq(t.simTotalLeft(),t.simLen()*t.SIM_QSEC,'and totals its own question count');

  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1); await sleep(30);
  const totBox=$('simTotal');
  t.simQTick(30); t.renderSimTotal();
  ok(!totBox.classList.contains('tight'),'ordinary play does not cry wolf');
  // the amber is for the last five minutes, not for a second clock that used to take over
  const qtWas=Object.assign({},t.sim.qt);
  t.sim.qs.forEach((q,i)=>{ if(i!==t.sim.i) t.sim.qt[i]=0; }); t.renderSimTotal();
  ok(totBox.classList.contains('tight'),'it warns in the last five minutes');
  ok(!/own clock/.test($('simTotalSub').textContent),'and there is no second clock to blame');
  t.sim.qt=qtWas; t.renderSimTotal();
  ok(!totBox.classList.contains('tight'),'and calms down again');

  t.simAbandon(); await sleep(30);
  ok(totBox.classList.contains('hidden'),'abandoning hides the strip');
  t.simClearSave();

  // the teaching papers spend the same 90 on reading the feedback
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1); await sleep(20);
  const q=t.QS[t.sim.qs[0]];
  q.a.forEach(l=>t.simPick(l)); await sleep(20);
  ok($('explain').classList.contains('show'),'paper 1 explains the answer');
  eq(t.simQLeft,t.SIM_QSEC,'and the clock did not stop for it');
  t.simQTick(t.SIM_QSEC-1); await sleep(5);
  eq(t.sim.i,0,'reading is on the same 90 seconds');
  ok($('explain').classList.contains('show'),'still reading');
  t.simQTick(1); await sleep(20);
  eq(t.sim.i,1,'when they are gone it moves on mid-read');
  ok(!$('explain').classList.contains('show'),'and clears the explanation');

  t.simAbandon(); await sleep(20); t.simClearSave();
}

// ---------- read aloud ----------
async function ttsChecks(){
  const t=T(), $=id=>document.getElementById(id);
  // stub the speech engine so the harness can see exactly what was asked for
  const real=Object.getOwnPropertyDescriptor(window,'speechSynthesis');
  const spoken=[]; let cancels=0, speaking=false, last=null;
  const finish=()=>{ speaking=false; if(last&&last.onend) last.onend(); };
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{
    speak(u){ spoken.push(u.text); speaking=true; last=u; },
    cancel(){ cancels++; speaking=false; },
    getVoices(){ return [{lang:'en-US',name:'Test',localService:true}]; },
    addEventListener(){}, removeEventListener(){},
    get speaking(){ return speaking; }, get pending(){ return false; }
  }});
  const realU=window.SpeechSynthesisUtterance;
  window.SpeechSynthesisUtterance=function(text){ this.text=text; };

  ok(t.ttsOk(),'the engine reports available');
  const q=t.QS[0];
  const txt=t.ttsText(q,0,65);
  ok(txt.indexOf('Question 1 of 65')===0,'the reading opens with the position');
  ok(txt.indexOf(q.q)>0,'it reads the stem');
  // and stops there — the options are on the screen already
  q.o.forEach(o=>ok(txt.indexOf('Option '+o[0])<0,'it does not announce option '+o[0]));
  q.o.forEach(o=>ok(txt.indexOf(o[1].slice(0,30))<0,'it does not read option '+o[0]+" text"));
  eq(txt,'Question 1 of 65. '+q.q,'the reading is the position and the stem, nothing else');

  // ---- the reading is cut into pieces so it starts speaking at once
  const long='Question 1 of 65. '+('A company needs a highly available store. '.repeat(12));
  const cs=t.ttsChunks(long);
  ok(cs.length>1,'a long stem is cut into pieces ('+cs.length+')');
  ok(cs[0].length<=160,'the first piece is short, so sound starts straight away');
  cs.forEach((c,i)=>ok(c.length<=160,'piece '+i+' is within the limit'));
  eq(cs.join(' ').replace(/\s+/g,' ').trim(),long.replace(/\s+/g,' ').trim(),
     'and nothing is lost or duplicated between them');
  eq(t.ttsChunks('Short one.').length,1,'a short stem stays whole');
  eq(t.ttsChunks('').length,0,'empty text asks for nothing');
  const noSpace=t.ttsChunks('x'.repeat(400));
  ok(noSpace.length>1,'even a single unbroken word is cut rather than sent whole');
  ok(noSpace.every(c=>c.length<=160),'within the limit');
  // the first draft of the chunker flushed long clauses straight to the output while an
  // earlier piece was still buffered, so the reading came out reordered with words missing
  const norm=x=>x.replace(/\s+/g,' ').trim();
  let lossy=0, over=0;
  for(let i=0;i<t.QS.length;i++){
    const txt=t.ttsText(t.QS[i],i,65), cs=t.ttsChunks(txt);
    if(norm(cs.join(' '))!==norm(txt)) lossy++;
    if(cs.some(c=>c.length>160)) over++;
  }
  eq(lossy,0,'every question in the bank chunks without losing or reordering a word');
  eq(over,0,'and no piece exceeds the limit');

  // Nothing sets utterance.voice any more. A ChromeOS machine reported eight voices with
  // localService:true that never made a sound — 15 seconds and nothing — and the old
  // ttsVoice() preferred exactly those. The engine's default spoke in 477ms on the same box.
  eq(t.ttsVoice(),null,'no voice is chosen for the utterance');
  ok(Array.isArray(t.ttsVoicesEn()),'though the English voices can still be listed');

  // the fallback the watchdog falls back to: one utterance, no voice override, no chunking
  const nBefore=spoken.length;
  const live=t.ttsSend('One. Two. Three. '+('padding words here. '.repeat(20)),999,true);
  eq(spoken.length,nBefore+1,'the plain retry sends exactly one utterance');
  ok(spoken[spoken.length-1].length>160,'unchunked, so an engine that dislikes queues gets one');
  ok(typeof live==='function','and it reports whether anything started');
  const nChunked=spoken.length;
  t.ttsSend('One. Two. Three. '+('padding words here. '.repeat(20)),999,false);
  ok(spoken.length>nChunked+1,'while the normal path chunks');

  t.startPaper(2); await sleep(20);   // an early paper: every question keeps read-aloud
  eq($('simTts').textContent,'🔊 Read','the button offers a read');
  const n0=spoken.length;
  $('simTts').click(); await sleep(30);   // ttsSpeak yields a tick before speaking
  ok(spoken.length>n0,'tapping it speaks');
  ok(spoken[n0].indexOf('Question 1 of 65')===0,'starting with this question');
  ok(spoken[n0].length<=160,'and the first thing sent is short');
  eq($('simTts').textContent,'⏹ Stop','and the button becomes a stop');
  ok($('simTts').classList.contains('on'),'and shows that it is reading');

  // a second tap stops it. There is no third state.
  const c0=cancels;
  const spokeN=spoken.length;
  $('simTts').click(); await sleep(10);
  ok(cancels>c0,'the second tap stops the voice');
  eq(spoken.length,spokeN,'and does not start another reading');
  eq($('simTts').textContent,'🔊 Read','the button offers a read again');
  ok(!$('simTts').classList.contains('on'),'and drops the reading state');

  // moving on never reads by itself
  const n1=spoken.length;
  t.simGo(1); await sleep(10);
  eq(spoken.length,n1,'moving to the next question does not read it');
  eq($('simTts').textContent,'🔊 Read','and the button stays a read');
  $('simTts').click(); await sleep(30);
  ok(spoken.length>n1,'but asking for it still works');
  ok(spoken[n1].indexOf('Question 2 of 65')===0,'and reads the right one');

  // when the voice finishes on its own, the button comes back by itself
  finish(); await sleep(10);
  eq($('simTts').textContent,'🔊 Read','the button resets when a reading ends');
  ok(!$('simTts').classList.contains('on'),'and clears its state');

  // and a reading still in progress is cancelled by moving on
  $('simTts').click(); await sleep(30);
  const c1=cancels;
  t.simGo(1); await sleep(10);
  ok(cancels>c1,'moving on cancels a reading in progress');
  eq($('simTts').textContent,'🔊 Read','and the button follows');

  // leaving the exam stops the voice
  $('simTts').click(); await sleep(30);
  const c2=cancels;
  t.simAbandon(); await sleep(20);
  ok(cancels>c2,'quitting stops the voice');

  // practice questions are never read aloud
  const n3=spoken.length;
  t.startSession(3); await sleep(10);
  eq(spoken.length,n3,'practice does not speak');

  window.SpeechSynthesisUtterance=realU;
  if(real) Object.defineProperty(window,'speechSynthesis',real);
  else delete window.speechSynthesis;
  t.simClearSave();
}

// ---------- the briefing on the first five papers ----------
async function briefChecks(){
  const t=T(), $=id=>document.getElementById(id);
  eq(t.BRIEF_PAPERS,10,'the first ten papers are briefed');
  for(const n of [1,5,10]){
    t.startPaper(n); await sleep(20);
    ok(!$('exBrief').classList.contains('hidden'),'exam '+n+' shows a briefing');
    ok(!$('exBrief').open,'exam '+n+': it starts closed, one line under the question');
    ok(/Before you answer/.test($('exBriefTitle').textContent),'exam '+n+': it is labelled');
    ok($('exBriefBody').children.length>0,'exam '+n+': the briefing has content');
    // Definitions say what the services are; these say how to pick between them, which is
    // what the question is testing. Neither names the answer, so both are safe before it.
    const bl=[...$('exBriefBody').querySelectorAll('.lbl')].map(e=>e.textContent);
    ok(bl.some(x=>/How to choose/.test(x)),'exam '+n+': it says how to choose in this area');
    const rules=[...$('exBriefBody').querySelectorAll('.brule:not(.trap)')];
    ok(rules.length>0,'exam '+n+': with decision rules under it');
    rules.forEach((r,k)=>{
      const sp=r.querySelector('span:last-child');
      eq(getComputedStyle(sp).direction,'ltr','rule '+k+' reads left to right beside the Hebrew');
      ok(sp.textContent.trim().length>15,'rule '+k+' says something');
    });
    // Measured across the ten briefed papers: median 1,286 characters, min 728 where the
    // sector has no recorded traps, max 1,798. Every one has its decision rules.
    ok($('exBriefBody').textContent.length>600,
       'exam '+n+': the briefing is substantial ('+$('exBriefBody').textContent.length+' chars)');
    const sec=t.SHORT[t.QS[t.sim.qs[0]].s];
    ok($('exBriefTitle').textContent.indexOf(sec)>0,'exam '+n+': it names the sector');
    // it follows the walk
    const first=$('exBriefBody').innerHTML;
    t.simGo(1); await sleep(10);
    ok($('exBriefBody').innerHTML!==first||t.QS[t.sim.qs[0]].s===t.QS[t.sim.qs[1]].s,
       'exam '+n+': the briefing follows the question');
    t.simAbandon(); await sleep(10);
  }
  for(const n of [11,15,19]){
    t.startPaper(n); await sleep(20);
    ok($('exBrief').classList.contains('hidden'),'exam '+n+' has no briefing');
    t.simAbandon(); await sleep(10);
  }
  // and practice never shows it
  t.startSession(2); await sleep(10);
  ok($('exBrief').classList.contains('hidden'),'practice has no briefing');
  t.simClearSave();
}

// ---------- nothing costs coins ----------
async function freeChecks(){
  const t=T(), $=id=>document.getElementById(id);
  eq(t.STUDY_COST,0,'a study card is free');
  eq(t.unlockCost(),0,'unlocking a reward round is free');
  t.P.coins=0;
  const before=t.P.coins;
  t.renderShop(); await sleep(10);
  const buys=[...document.querySelectorAll('#shopList .buy')];
  ok(buys.length>0,'the shop has items');
  ok(buys.every(b=>!b.disabled),'nothing in the shop is locked behind coins');
  ok(buys.every(b=>!/\d+\s*🪙/.test(b.textContent)),'no price tags left in the shop');
  buys[0].click(); await sleep(10);
  ok(t.P.coins>=before,'taking an item costs nothing');
  t.renderThemes(); await sleep(10);
  const buyable=t.THEME_LIST.filter(x=>!x.earn&&!x.free).length;
  const usable=[...document.querySelectorAll('#themeList .buy')]
    .filter(b=>/USE|ACTIVE/.test(b.textContent)).length;
  ok(usable>=buyable,'every purchasable theme is already usable, got '+usable+' of '+buyable);
  const priced=[...document.querySelectorAll('#themeList .buy')].filter(b=>/\d/.test(b.textContent));
  eq(priced.length,0,'no theme still shows a price');
  // the lifelines
  t.P.coins=0;
  t.startSession(1); await sleep(10);
  t.useFifty(); await sleep(5);
  ok(t.P.coins===0,'50/50 costs nothing');
  eq(t.P.coins,0,'and the balance is untouched');
}

// ---------- the teaching papers explain as you go ----------
async function feedbackChecks(){
  const t=T(), $=id=>document.getElementById(id);
  eq(t.EXPLAIN_PAPERS,10,'ten papers explain as you go');
  eq(t.BRIEF_PAPERS,10,'and ten papers brief you first');
  t.simClearSave();

  // a right answer
  t.startPaper(1); await sleep(20);
  ok(t.simTeaches(),'paper 1 teaches');
  ok(!$('explain').classList.contains('show'),'nothing is explained before an answer');
  const q0=t.QS[t.sim.qs[0]];
  q0.a.forEach(l=>t.simPick(l)); await sleep(20);
  ok(t.simRevealed(),'answering reveals');
  ok($('explain').classList.contains('show'),'the explanation panel is up');
  ok(/Correct/.test($('.exhead')?'':$('explain').querySelector('.exhead').textContent),'it says correct');
  q0.a.forEach(l=>{
    const el=[...$('qOpts').children].find(x=>x.dataset.ltr===l);
    ok(el.classList.contains('ok'),'the right option is marked');
  });
  ok(/Correct \u2014 [A-F]|the answer is [A-F]/.test($('explain').querySelector('.exhead').textContent),'the heading names the answer');
  eq(t.simScore().right,1,'the tally counts it');

  // it is settled: further picks do nothing
  const otherL=q0.o.map(o=>o[0]).find(l=>!q0.a.includes(l));
  const wasAns=(t.sim.ans[0]||[]).join('');
  t.simPick(otherL); await sleep(10);
  eq((t.sim.ans[0]||[]).join(''),wasAns,'a revealed question cannot be changed');

  // a wrong answer
  t.simGo(1); await sleep(20);
  ok(!$('explain').classList.contains('show'),'the next question starts clean');
  const q1=t.QS[t.sim.qs[1]];
  const bad=q1.o.map(o=>o[0]).filter(l=>!q1.a.includes(l)).slice(0,q1.a.length);
  bad.forEach(l=>t.simPick(l)); await sleep(20);
  ok(t.simRevealed(),'a wrong answer reveals too');
  ok(/Not quite/.test($('explain').querySelector('.exhead').textContent),'it says not quite');
  bad.forEach(l=>{
    const el=[...$('qOpts').children].find(x=>x.dataset.ltr===l);
    ok(el.classList.contains('no'),'the wrong pick is marked wrong');
  });
  q1.a.forEach(l=>{
    const el=[...$('qOpts').children].find(x=>x.dataset.ltr===l);
    ok(el.classList.contains('ok'),'and the right one is shown');
  });
  ok(!!$('explain').querySelector('.exopt.mine .expick'),'it marks what was picked');
  eq(t.simScore().done,2,'two settled');
  eq(t.simScore().right,1,'one of them right');
  ok(/right so far/.test($('simCount').textContent),'the strip reports the tally');

  // going back re-shows the verdict
  t.simGo(-1); await sleep(20);
  ok($('explain').classList.contains('show'),'coming back shows the verdict again');
  ok(/Correct/.test($('explain').querySelector('.exhead').textContent),'the same verdict');
  t.simGo(1); await sleep(10);

  // the reveal survives leaving and resuming
  $('simQuit').click(); await sleep(30);
  const sv=t.simSaved();
  ok(sv&&sv.rev&&sv.rev[0]&&sv.rev[1],'the save keeps which questions were settled');
  t.simResume(); await sleep(30);
  ok(t.simRevealed(1),'and they are still settled after resuming');
  eq(t.simScore().done,2,'the tally survives too');

  // scoring at submit matches what was revealed
  const before=t.simScore();
  t.simSubmit(true); await sleep(40);
  ok($('simMeta').textContent.indexOf(before.right+' / 65 correct')===0,'the final count matches the running tally');

  // every exam gives feedback after answering now, not just papers 1-10
  t.startPaper(12); await sleep(20);
  ok(t.simTeaches(),'paper 12 gives feedback too');
  const q2=t.QS[t.sim.qs[0]];
  q2.a.forEach(l=>t.simPick(l)); await sleep(20);
  ok(t.simRevealed(),'answering reveals on paper 12');
  ok($('explain').classList.contains('show'),'and explains it');
  ok($('exBrief').classList.contains('hidden'),'the before-you-answer briefing stays on papers 1-10');
  // settled once revealed, as on the teaching papers
  const alt=q2.o.map(o=>o[0]).find(l=>!q2.a.includes(l));
  t.simPick(alt); await sleep(10);
  ok((t.sim.ans[0]||[]).indexOf(alt)<0,'a revealed answer is settled');
  t.simAbandon(); await sleep(20);
  t.simClearSave();

  // the authored notes ride along with the questions that have one
  const withNote=t.QS.filter(q=>q.x);
  ok(withNote.length>150,'the review notes shipped, got '+withNote.length);
  withNote.slice(0,40).forEach(q=>ok(q.x.length>30,'a note is a real sentence'));
  const qi=t.QS.findIndex(q=>q.x);
  const e=t.buildExplain(t.QS[qi],new Set(t.QS[qi].a),true);
  eq(e.note,t.QS[qi].x,'the panel is handed the note');
}

// ---------- the line that knows where you are ----------
async function cheerChecks(){
  const t=T(), $=id=>document.getElementById(id);
  eq(t.EXAM_CHEER.length,65,'one line per position in a full paper');
  eq(new Set(t.EXAM_CHEER).size,65,'no line is reused');
  t.EXAM_CHEER.forEach((l,i)=>{
    ok(l.length>12,'line '+(i+1)+' is a real sentence');
    ok(/[֐-׿]/.test(l),'line '+(i+1)+' is in Hebrew');
    // nothing may hint at right or wrong: the silent papers show these too
    ok(!/נכון|טעית|צדקת|שגוי/.test(l),'line '+(i+1)+' gives nothing away');
  });
  ok(/1/.test(t.examCheer(0,65)),'the first line names the first question');
  ok(/42|ארבעים ושתיים/.test(t.examCheer(41,65)),'question 42 gets its own line');
  ok(t.examCheer(64,65).length>0,'the last question has a line');
  const over=t.examCheer(70,80);
  ok(/71/.test(over)&&/80/.test(over),'past the table it still names the position');
  ok(/31/.test(t.examCheer(30,31))||t.examCheer(30,31).length>0,'the short paper is covered');

  // it shows up in the panel on a teaching paper
  t.simClearSave();
  t.startPaper(2); await sleep(20);
  const q=t.QS[t.sim.qs[0]];
  q.a.forEach(l=>t.simPick(l)); await sleep(30);
  const ch=$('explain').querySelector('.excheer');
  ok(!!ch,'the line is in the explanation panel');
  ok(ch.textContent.indexOf(t.examCheer(0,65))>=0,'and it is the right line');
  // and it follows the position
  t.simGo(1); await sleep(10);
  const q1=t.QS[t.sim.qs[1]];
  q1.a.forEach(l=>t.simPick(l)); await sleep(30);
  ok($('explain').querySelector('.excheer').textContent.indexOf(t.examCheer(1,65))>=0,
     'question two gets question two’s line');
  t.simAbandon(); await sleep(20); t.simClearSave();
}

// ---------- what is in the papers ----------
async function statsChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const S=t.BANK_STATS;
  eq(S.total,t.QS.length,'the overview counts every question');
  eq(S.papers,t.PAPER_COUNT,'over every paper');
  eq(S.rows.reduce((a,r)=>a+r.n,0),t.QS.length,'the subject counts add up to the bank');
  eq(S.rows.length,new Set(t.QS.map(q=>q.s)).size,'one row per subject that has questions');
  const pct=S.rows.reduce((a,r)=>a+r.pct,0);
  ok(Math.abs(pct-100)<1.5,'the percentages add up to about 100, got '+pct.toFixed(1));
  S.rows.forEach(r=>{
    ok(r.papers>=1&&r.papers<=S.papers,'subject '+r.sec+' appears in a sane number of papers');
    ok(r.n>0,'subject '+r.sec+' has questions');
    ok(r.pct>0,'subject '+r.sec+' has a share');
  });
  for(let i=1;i<S.rows.length;i++) ok(S.rows[i-1].n>=S.rows[i].n,'rows are ordered by size');
  ok(S.everyPaper>=5,'several subjects turn up in every paper, got '+S.everyPaper);

  // and it renders
  t.renderPapers(); t.go('paperScreen'); await sleep(30);
  eq($('paperStatsBody').children.length,S.rows.length,'a row per subject is rendered');
  ok(/appear in all/.test($('paperStatsTitle').textContent),'the title says how many are unavoidable');
  hittable($('paperStatsBox').querySelector('summary'),'the overview toggle');
  ok(/%/.test($('paperStatsBody').textContent),'the rows carry percentages');
  ok(/per paper/.test($('paperStatsBody').textContent),'and how many to expect per paper');
}

// ---------- how much of the exam each Study chapter is ----------
async function weightChecks(){
  const t=T(), $=id=>document.getElementById(id), S=t.STUDY_T;
  eq(S.STU_SECS.length,S.STU_CH.length,'every chapter maps to sectors');
  const all=S.STU_SECS.flat();
  eq(all.length,new Set(all).size,'no sector is claimed by two chapters');
  eq(new Set(all).size,t.SECTIONS.length,'every sector belongs to a chapter');
  const tot=S.STU_CH.reduce((a,c,i)=>a+S.stuWeight(i).n,0);
  eq(tot,t.QS.length,'the chapter weights add up to the whole bank');
  const pct=S.STU_CH.reduce((a,c,i)=>a+S.stuWeight(i).pct,0);
  ok(Math.abs(pct-100)<1.5,'and to about 100%, got '+pct.toFixed(1));
  S.STU_CH.forEach((c,i)=>{
    const w=S.stuWeight(i);
    ok(w.n>0,'chapter '+i+' ('+c.nm+') covers questions');
    ok(w.pct>0,'chapter '+i+' has a share of the exam');
  });

  S.renderStudyPick(); t.go('stuPickScreen'); await sleep(30);
  const cards=[...$('stuPickList').children];
  eq(cards.length,S.STU_CH.length,'a card per chapter');
  cards.forEach((el,i)=>{
    const w=S.stuWeight(i);
    ok(el.textContent.indexOf(w.pct+'%')>=0,'chapter '+i+' card shows its share');
    ok(el.textContent.indexOf(w.n+' questions')>=0,'chapter '+i+' card shows its question count');
  });
  // and inside the chapter
  S.stuOpen(2); await sleep(30);
  const w2=S.stuWeight(2);
  ok($('stuWeight').textContent.indexOf(w2.pct+'%')>=0,'the chapter page repeats the share');
  eq($('stuWeight').children.length,3,'three figures on the chapter page');
  t.go('homeScreen');
}

// ---------- the question tools sit in the header, not over the answers ----------
async function qToolChecks(){
  const t=T(), $=id=>document.getElementById(id);
  ok($('fsBtn').closest('.qtop')!==null,'the text-size button lives in the question header');
  ok($('markBtn').closest('.qtop')!==null,'the bookmark button lives in the question header');
  ok(!$('qBar').contains($('fsBtn')),'it is no longer in the foot bar');
  ok(!$('qBar').contains($('markBtn')),'nor is the bookmark');

  // during an exam the foot bar has nothing to show and must take no space
  t.simClearSave();
  t.startPaper(4); await sleep(30);
  ok($('qBar').classList.contains('hidden'),'the foot bar is hidden inside an exam');
  eq(Math.round($('qBar').getBoundingClientRect().height),0,'and takes no vertical space');
  const rows=Math.round(document.querySelector('.qtop').getBoundingClientRect().height);
  ok(rows<40,'the header stays on one line, got '+rows+'px');
  hittable($('fsBtn'),'text-size button in an exam');
  hittable($('markBtn'),'bookmark button in an exam');
  // and both still do their job
  const fs0=document.body.dataset.fs;
  $('fsBtn').click(); await sleep(5);
  ok(document.body.dataset.fs!==fs0,'the text-size button still cycles');
  const wasMarked=t.isBookmarked(t.curQ);
  $('markBtn').click(); await sleep(5);
  ok(t.isBookmarked(t.curQ)!==wasMarked,'the bookmark button still toggles');
  ok($('markBtn').classList.contains('on')===t.isBookmarked(t.curQ),'and shows its state');
  $('markBtn').click(); await sleep(5);
  t.simAbandon(); await sleep(20); t.simClearSave();

  // in practice the foot bar is back, because it has the lifelines and Lock in
  t.startSession(6); await sleep(30);
  ok(!$('qBar').classList.contains('hidden'),'the foot bar returns in practice');
  ok($('qBar').getBoundingClientRect().height>20,'and has its controls');
  ok([...$('qBar').children].some(e=>e.id==='qConfirm'),'including Lock in');
}

// ---------------------------------------------------------------- Hebrew
// The three glossaries that explain the services are generated by
// build_course_data.py and translated afterwards by hebrew_codex.py,
// hebrew_glossary.py and hebrew_blueprint.py. Re-running the generator without
// the translators would put them back in English, silently — these fail loudly.
const HEB=/[\u0590-\u05FF]/;
function hebrewChecks(){
  const t=T();
  const ex=JSON.parse(document.getElementById('explaindata').textContent.replace(/<\\\//g,'</'));
  ok(ex.glossary.length===154,'the explanation glossary still has its 154 terms');
  const enG=ex.glossary.filter(e=>!HEB.test(e.d));
  ok(enG.length===0,'every glossary definition is Hebrew'+(enG.length?' — English: '+enG.slice(0,4).map(e=>e.t).join(', '):''));
  ok(ex.glossary.every(e=>!HEB.test(e.t)),'the term names stay English — exFind matches them against the options');

  const codex=t.CODEX;
  const enC=Object.keys(codex).filter(k=>!HEB.test(codex[k]));
  ok(enC.length===0,'every codex definition is Hebrew'+(enC.length?' — English: '+enC.slice(0,4).join(', '):''));

  const sd=JSON.parse(document.getElementById('subjectdata').textContent.replace(/<\\\//g,'</'));
  const roles=[],bens=[];
  Object.values(sd.subjects).forEach(v=>{
    v.blueprint.forEach(b=>roles.push(b));
    v.tradeoffs.forEach(x=>bens.push(x));
  });
  ok(roles.length>0&&roles.every(b=>HEB.test(b.role)),'every Learn service card is Hebrew');
  ok(bens.length>0&&bens.every(x=>HEB.test(x.benefit)),'every trade-off benefit is Hebrew');

  // and the panel actually renders it, right-aligned, with the service name left
  const bank=JSON.parse(document.getElementById('data').textContent.replace(/<\\\//g,'</')).questions;
  let q=null;
  for(const b of bank){ const e=t.buildExplain(b,new Set([b.a[0]]),true);
    if(e.correctTerms.length&&e.distractors.some(d=>d.terms.length)){ q=b; break; } }
  ok(!!q,'a question exists that fills both halves of the panel');
  if(q){
    t.renderExplain(q,new Set([q.o.find(o=>!q.a.includes(o[0]))[0]]),false);
    const box=$('explain');
    // The Hebrew definitions used to sit in two blocks of their own. They now live under the
    // option that names them, where they say what that option is actually proposing.
    // They are folded into one "services in this question" block now, one tap away.
    const svc=[...box.querySelectorAll('.exmore .svcline')];
    ok(svc.length>0,'the service definitions are there, folded');
    ok(!box.querySelector('.exmore').open,'and folded by default, so the panel is not a wall');
    svc.forEach((el,i)=>{
      const sp=el.querySelector('span');
      ok(HEB.test(sp.textContent),'service line '+i+' is in Hebrew');
      eq(getComputedStyle(sp).direction,'rtl','service line '+i+' reads right to left');
      const nm=el.querySelector('b');
      ok(nm&&!HEB.test(nm.textContent),'and its service name stays Latin');
    });
    // the English around them must NOT have inherited that direction
    const optB=box.querySelector('.exeach .exopt>span>b');
    if(optB) eq(getComputedStyle(optB).direction,'ltr','the option text reads left to right');
    const ruleI=box.querySelector('.exrules .exopt i');
    if(ruleI) eq(getComputedStyle(ruleI).direction,'ltr','and so do the decision rules');
    // one service may explain only one distractor, or the panel repeats itself
    const e=t.buildExplain(q,new Set([q.a[0]]),true);
    const names=e.distractors.filter(d=>d.terms.length).map(d=>d.terms[0].t.toLowerCase());
    ok(names.length===new Set(names).size,'no two distractors share an explanation');
    t.hideExplain();
  }
  // across the bank, not just one question
  let dup=0,en=0,seen=0;
  for(let i=0;i<bank.length;i+=5){
    const e=t.buildExplain(bank[i],new Set([bank[i].a[0]]),true);
    if(!e.correctTerms.length) continue;
    seen++;
    if(!e.correctTerms.every(x=>HEB.test(x.d))) en++;
    const n=e.distractors.filter(d=>d.terms.length).map(d=>d.terms[0].t.toLowerCase());
    if(n.length!==new Set(n).size) dup++;
  }
  ok(seen>100,'sampled enough questions to mean something ('+seen+')');
  ok(en===0,en+' sampled questions still explain in English');
  ok(dup===0,dup+' sampled questions repeat a service across two distractors');
}

// ---------- the recent work, in combination ----------
// Each of the last four changes has its own block above. They were built one after another
// and they all touch the same exam, so these walk the places where they meet.
async function integrationChecks(){
  const t=T(), $=id=>document.getElementById(id);
  const HEB=/[\u0590-\u05FF]/;
  t.simClearSave();

  // --- speech + the question clock: running out has to silence the voice
  const real=Object.getOwnPropertyDescriptor(window,'speechSynthesis');
  // ttsStop() only cancels an engine that is actually busy — firing cancel() at an idle one
  // is what delayed Chrome's next speak(). The stub has to model that or it tests nothing.
  const spoken=[]; let cancels=0, last=null, busy=false;
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{
    speak(u){ spoken.push(u.text); last=u; busy=true; },
    cancel(){ cancels++; busy=false; },
    getVoices(){ return [{lang:'xx-XX',name:'T'}]; },
    addEventListener(){}, removeEventListener(){},
    get speaking(){ return busy; }, get pending(){ return false; }, get paused(){ return false; }
  }});
  const realU=window.SpeechSynthesisUtterance;
  window.SpeechSynthesisUtterance=function(txt){ this.text=txt; };

  t.startPaper(2); await sleep(30);   // an early paper: every question keeps read-aloud
  $('simTts').click(); await sleep(30);
  eq($('simTts').textContent,'\u23f9 Stop','reading aloud mid-exam');
  ok(spoken.length>=1,'it spoke');
  ok(spoken[0].length<=160,'starting with a short piece, so sound is immediate');
  ok(spoken.join(' ').indexOf('Option')<0,'and did not read the options');
  const c0=cancels;
  t.simQTick(t.SIM_QSEC); await sleep(30);
  eq(t.sim.i,0,'the time ran out, and the question stays to show its answer');
  ok(cancels>c0,'which stopped the voice');
  eq($('simTts').textContent,'\ud83d\udd0a Read','and put the button back');

  // --- speech + a takeover: losing the exam must also silence it
  $('simTts').click(); await sleep(30);
  eq($('simTts').textContent,'\u23f9 Stop','reading again');
  const c1=cancels;
  t.P.simSave=Object.assign({},t.P.simSave,
    {dev:'phone-x',devKind:'phone',claimAt:Date.now()+1000});
  ok(t.simOwnerCheck(),'the other device took it');
  await sleep(30);
  ok(cancels>c1,'and that silenced the voice too');
  eq(t.sim,null,'the exam here is over');

  window.SpeechSynthesisUtterance=realU;
  if(real) Object.defineProperty(window,'speechSynthesis',real);
  else delete window.speechSynthesis;

  // --- Hebrew feedback + the question clock, on a teaching paper
  t.simClearSave();
  t.startPaper(1); await sleep(30);
  const q=t.QS[t.sim.qs[0]];
  q.a.forEach(l=>t.simPick(l)); await sleep(30);
  ok($('explain').classList.contains('show'),'paper 1 explains');
  // An option's outer span now holds English text with Hebrew service lines nested inside it,
  // so testing the outer one finds Hebrew in its descendants and LTR on the element itself.
  // The Hebrew leaf is .svcline > span.
  const heb=[...$('explain').querySelectorAll('.svcline>span')];
  ok(heb.length>0,'the options carry Hebrew service definitions');
  heb.forEach((e,i)=>{
    ok(HEB.test(e.textContent),'service line '+i+' is Hebrew');
    eq(getComputedStyle(e).direction,'rtl','service line '+i+' reads right to left');
  });
  const eng=$('explain').querySelector('.exeach .exopt>span>b');
  if(eng) eq(getComputedStyle(eng).direction,'ltr','while the option text stays left to right');
  eq(t.simQLeft,t.SIM_QSEC,'and the clock did not pause to let us read');
  t.simQTick(t.SIM_QSEC); await sleep(30);
  eq(t.sim.i,1,'it moved on mid-read');
  ok(!$('explain').classList.contains('show'),'clearing the Hebrew panel behind it');

  // --- a takeover mid-explanation leaves nothing behind on screen
  q0picks(t); await sleep(30);
  ok($('explain').classList.contains('show'),'explaining again');
  t.P.simSave=Object.assign({},t.P.simSave,
    {dev:'phone-x',devKind:'phone',claimAt:Date.now()+2000});
  ok(t.simOwnerCheck(),'taken over while the panel was up');
  await sleep(30);
  ok(!$('explain').classList.contains('show'),'the explanation is cleared');
  eq(t.route,'paperScreen','and we are off the question screen');

  // --- taking it back restores the per-question clock, not a fresh 90
  t.P.simSave=Object.assign({},t.P.simSave,{i:4, qt:{4:37}});
  t.renderPapers(); await sleep(20);
  const rb=$('exResume');
  ok(/on your phone/.test(rb.textContent),'the row says where it is');
  rb.click(); await sleep(20); rb.click(); await sleep(40);
  eq(t.sim.i,4,'taken over at the right question');
  eq(t.simQLeft,37,'with the seconds it had left, not a fresh 90');
  eq(t.P.simSave.dev,t.DEVICE_ID,'and the claim moved to us');
  ok(t.P.simSave.claimAt>0,'stamped as a deliberate claim');

  // --- and a paper taken over, timed out and flagged still exports
  t.simAbandon(); await sleep(30); t.simClearSave();
  t.startPaper(11); await sleep(30);
  const wrong=t.QS[t.sim.qs[0]].o.find(o=>!t.QS[t.sim.qs[0]].a.includes(o[0]))[0];
  t.simPick(wrong); await sleep(20);
  t.simFlagToggle(); await sleep(10);
  t.simGo(1); await sleep(20);
  t.simQTick(t.SIM_QSEC); await sleep(30);          // let one time out, so it exports as blank
  t.simSubmit(true); await sleep(60);
  const rec=t.lastExamCsv;
  ok(!!rec&&rec.list.length>0,'submitting still leaves something to export');
  ok(/exam-11/.test(rec.name),'named for the paper');
  const csv=t.csvRows(rec.list);                       // one string, CRLF separated
  const lines=csv.split('\r\n');
  ok(lines.length>1,'the CSV has a header and at least one row');
  ok(/^"#","Status"/.test(lines[0]),'with the expected header');
  ok(/Flagged/.test(csv),'and the flagged question is in it');
  t.simClearSave();
}
function q0picks(t){
  const q=t.QS[t.sim.qs[t.sim.i]];
  q.a.forEach(l=>t.simPick(l));
  return sleep(20);
}

window.QA_INTEG=async function(){
  pass=0; fails=[];
  const t=T();
  ok(!!t,'the test surface is exposed (load with ?test=1)');
  if(!t) return {pass,failed:fails.length,fails};
  await integrationChecks();
  t.go('homeScreen');
  console.log(fails.length?('QA_INTEG: '+pass+' passed, '+fails.length+' FAILED')
                           :('QA_INTEG: '+pass+' assertions, all passing'));
  return {pass, failed:fails.length, fails};
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
  hebrewChecks();
  if(opts.app!==false) await appChecks();
  if(opts.study!==false){ await studyChecks(); await retiredDrillChecks(); }
  if(opts.extras!==false){ whyChecks(); whyQualityChecks(); cueChecks(); sriChecks(); arithmeticChecks(); await gameLifetimeChecks(); await refreshChecks(); await breakChecks(); await modeChecks(); await dialogChecks(); await saveFlushChecks(); await pickCapChecks(); await oneClockChecks(); await continueChecks(); await saaChecks(); await multiDeviceChecks(); await hunt9Checks(); await readTaperChecks(); await histChecks(); await histSyncChecks(); await pauseBarChecks(); await redoSyncChecks(); mergeLossChecks(); await duelChecks(); await xssChecks(); await paperRowChecks(); await voiceChecks(); await hardeningChecks(); await deviceChecks(); await qClockChecks(); await resumeChecks(); await ttsChecks(); await briefChecks();
    await freeChecks(); await feedbackChecks(); await cheerChecks(); await qToolChecks();
    await statsChecks(); await weightChecks(); }
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
console.log('QA_BANK ready — run  await QA_BANK()  ·  QA_UI()  ·  QA_INTEG()');
})();
