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
  eq(t.SIM_QSEC,90,'a question gets 90 seconds');
  eq(t.PAPER_MIN,98,'a 65-question paper is budgeted at 90s each');
  eq(t.simBudget(65),98,'65 questions, 98 minutes');
  eq(t.simBudget(31),47,'the short paper is budgeted the same way');
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
  const bud=t.simBudget(sim.qs.length);
  ok(left>(bud-1)*60000&&left<=bud*60000,
     'the paper budget starts at '+bud+' minutes, got '+Math.round(left/60000));
  eq(t.simQLeft,t.SIM_QSEC,'and the question starts on a full 90 seconds');
  eq($('playClock').textContent,'⏳ 1:30','the top bar counts this question down');
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
  ok(/90 seconds a question/.test($('paperOpen').textContent),'the tile states the per-question limit');
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
  const setup=async()=>{ t.simClearSave(); t.startPaper(2); await sleep(30);
                         t.simQTick(20); await sleep(10); };

  // a closed tab is charged for
  await setup();
  const q0=t.simQLeft, w0=Math.round(t.simTimeLeft()/1000);
  t.P.simSave.at-=10*60*1000;
  eq(t.simAwayCost(t.P.simSave),600,'ten minutes away is measured in seconds, not milliseconds');
  t.simResume(); await sleep(40);
  eq(t.simQLeft,0,'the question it was on is spent — it only had '+q0+' seconds');
  const charged=w0-Math.round(t.simTimeLeft()/1000);
  ok(Math.abs(charged-600)<5,'and the paper is charged the ten minutes ('+charged+'s)');
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
  ok(Math.abs(c2-360)<5,'and that is what the paper loses ('+c2+'s)');
  t.simAbandon(); await sleep(30); t.simClearSave();

  // away long enough and the paper is simply over
  await setup();
  t.P.simSave.paused=0; t.P.simSave.at-=3*60*60*1000;
  ok(!t.simSaved(),'a paper whose budget ran out while away is not offered back');
  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave();

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

  // the shape the whole thing rests on
  eq(t.simAwayCost(null),0,'no save, no charge');
  eq(t.simAwayCost({paused:1,at:1}),0,'a paused save is never charged');
  eq(t.simAwayCost({at:0}),0,'nor one with no timestamp');
  eq(t.simAwayCost({at:Date.now()+9999}),0,'nor one stamped in the future');
}

// ---------- two six-minute breaks per paper ----------
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
  ok(Math.abs((wallAfter-wallBefore)-360)<5,
     'the paper budget is paid back the full six minutes ('+(wallAfter-wallBefore)+'s)');

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
  const other=rows()[5].querySelector('button');
  const wasLabel=other.textContent.trim();
  other.click(); await sleep(20);
  ok(/Delete your progress on Exam 4/.test(other.textContent),'starting elsewhere warns first');
  ok(/question 3 of 65/.test(other.textContent),'and names what would be lost');
  eq(t.simSaved().paper,4,'and the save is untouched');
  await sleep(4200);
  eq(other.textContent.trim(),wasLabel,'an unanswered warning lapses');
  eq(t.simSaved().paper,4,'still untouched');
  other.click(); await sleep(20); other.click(); await sleep(40);
  eq(t.sim.paper,6,'the second tap starts the other paper');
  t.simAbandon(); await sleep(40);

  // the restart button warns too
  t.simClearSave(); t.startPaper(4); await sleep(30);
  t.simGo(1); await sleep(10); t.simAbandon(); await sleep(40);
  const again=rows()[3].querySelectorAll('button')[0];
  again.click(); await sleep(20);
  ok(/start again/.test(again.textContent),'restarting warns first');
  eq(t.simSaved().i,1,'and has not reset anything yet');
  again.click(); await sleep(40);
  eq(t.sim.i,0,'the second tap starts it from question one');
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
  eq(t.simQLeft,90,'a fresh question has the full 90 seconds');
  eq($('qTimerFill').style.width,'100%','and a full bar');

  t.simQTick(60); await sleep(5);
  eq(t.simQLeft,30,'it counts down');
  eq($('playClock').textContent,'⏳ 0:30','the clock follows');
  ok($('playClock').classList.contains('warn'),'it warns at 30 seconds');
  ok(!$('playClock').classList.contains('crit'),'but is not critical yet');
  t.simQTick(21); await sleep(5);
  ok($('playClock').classList.contains('crit'),'it goes critical at 9 seconds');
  ok($('qTimerFill').classList.contains('low'),'and the bar turns');

  // running out moves to the next question, answered or not
  eq(t.sim.i,0,'still on the first question');
  const blank=(t.sim.ans[0]||[]).length;
  t.simQTick(9); await sleep(20);
  eq(t.sim.i,1,'running out moves to the next question');
  eq(t.simQLeft,90,'which starts on a full 90 seconds');
  eq((t.sim.ans[0]||[]).length,blank,'the question it left stays blank');
  eq(t.simAnsweredCount(),0,'so it counts as unanswered, which scores as wrong');

  // what is left is remembered per question
  t.simQTick(40); await sleep(5);
  eq(t.simQLeft,50,'question two is down to 50');
  t.simJump(2); await sleep(20);
  eq(t.simQLeft,90,'a question never opened is still on 90');
  t.simJump(1); await sleep(20);
  eq(t.simQLeft,50,'and coming back to question two gives back its 50');

  // a spent question can be reopened without being thrown out of it again
  t.simJump(0); await sleep(20);
  eq(t.simQLeft,0,'a spent question shows an empty clock');
  t.simQTick(5); await sleep(20);
  eq(t.sim.i,0,'and ticking it does not bounce you forward again');
  const opt=$('qOpts').firstChild.dataset.ltr;
  t.simPick(opt); await sleep(10);
  eq((t.sim.ans[0]||[]).join(''),opt,'you can still answer it from the review list');

  // it does not burn seconds where you cannot see the question
  t.simJump(3); await sleep(20);
  t.simReview(); await sleep(20);
  const held=t.simQLeft;
  t.simQTick(30); await sleep(5);
  eq(t.simQLeft,held,'the review screen does not spend the question clock');

  // the last question runs out into the review, not into nothing
  t.simJump(t.simLen()-1); await sleep(20);
  t.simQTick(90); await sleep(20);
  eq(t.route,'simRevScreen','running out of the last question lands on the review');

  // and it survives walking away
  t.simJump(4); await sleep(20);
  t.simQTick(25); await sleep(5);
  eq(t.simQLeft,65,'question five is down to 65');
  t.simAbandon(); await sleep(20);
  const sv=t.simSaved();
  ok(!!sv,'the paper was saved');
  eq(sv.qt[4],65,'the save kept what was left of that question');
  t.simResume(); await sleep(20);
  eq(t.sim.i,4,'it resumed on the same question');
  eq(t.simQLeft,65,'with the same time left');

  // ---- the clock is a deadline, not a count of ticks
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1); await sleep(30);
  ok(t.sim.qEndAt>Date.now(),'a question carries a deadline, not just a counter');
  const dl=t.sim.qEndAt;
  t.simQTick(20); await sleep(10);
  eq(t.simQLeft,70,'ticking by hand still works for the harness');
  ok(t.sim.qEndAt<dl,'and the deadline moves with it, so the two cannot disagree');
  ok(Math.abs((t.sim.qEndAt-Date.now())/1000-70)<2,'the deadline agrees with the counter');
  // time away is not spent on the question
  t.simAway();
  const deadlineWhenAway=t.sim.qEndAt;
  await sleep(120);
  t.simBack();
  ok(t.sim.qEndAt>deadlineWhenAway,'coming back pushes the deadline out by the time away');
  ok(typeof t.clockEnsure==='function','there is a way to revive a dead clock');
  t.clockEnsure();
  ok(true,'and calling it under TEST does nothing rather than throwing');
  t.simAbandon(); await sleep(20); t.simClearSave();

  // ---- what the whole paper has left, not just this question
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1); await sleep(30);
  eq(t.simTotalLeft(),65*90,'a fresh 65-question paper has 65 x 90 seconds');
  eq(t.simTotalFull(),65*90,'which is also its full budget');
  eq(t.simQsLeft(),65,'and 65 questions with time on them');
  eq($('simTotalVal').textContent,'1:37:30','shown as 1:37:30');
  eq($('simTotalFill').style.width,'100%','with a full bar');
  ok(/65 questions still open/.test($('simTotalSub').textContent),'and the count beneath it');
  ok(/1:37:30 left/.test($('clockSub').textContent),'the top clock carries it too');

  t.simQTick(90); await sleep(20);
  eq(t.simTotalLeft(),64*90,'one question spent leaves 64 x 90');
  eq($('simTotalVal').textContent,'1:36:00','which reads 1:36:00');
  eq(t.simQsLeft(),64,'and 64 questions still open');

  t.simQTick(30); await sleep(10);
  eq(t.simTotalLeft(),63*90+60,'it is a real sum, not questions-left times ninety');
  t.simJump(5); await sleep(20); t.simQTick(40); await sleep(10);
  const totBefore=t.simTotalLeft();
  t.simJump(9); await sleep(20);
  eq(t.simTotalLeft(),totBefore,'moving between questions does not change the total');
  t.simJump(5); await sleep(20);
  eq(t.simQLeft,50,'and a half-used question still holds its remainder');

  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(t.PAPER_COUNT); await sleep(30);
  ok(t.simLen()<65,'the last paper is shorter ('+t.simLen()+')');
  eq(t.simTotalLeft(),t.simLen()*90,'and totals its own question count');

  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(1); await sleep(30);
  const totBox=$('simTotal');
  t.simQTick(30); t.renderSimTotal();
  ok(!totBox.classList.contains('tight'),'ordinary play does not cry wolf');
  t.sim.endAt=Date.now()+60*1000; t.renderSimTotal();
  ok(totBox.classList.contains('tight'),'it warns when the paper clock becomes the binding one');
  ok(/paper clock runs out first/.test($('simTotalSub').textContent),'and says why');
  t.sim.endAt=Date.now()+99*60*1000; t.renderSimTotal();
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
  eq(t.simQLeft,90,'and the clock did not stop for it');
  t.simQTick(89); await sleep(5);
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

  t.startPaper(8); await sleep(20);
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
    ok($('exBrief').open,'exam '+n+': it starts open');
    ok(/Before you answer/.test($('exBriefTitle').textContent),'exam '+n+': it is labelled');
    ok($('exBriefBody').children.length>0,'exam '+n+': the briefing has content');
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
  ok(/Correct answer|Your answer/.test($('explain').textContent),'it names the answer');
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
  ok(/You picked/.test($('explain').textContent),'it shows what was picked');
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
  const pct=parseInt($('simScore').textContent,10);
  eq(pct,Math.round(before.right/65*100),'the final score matches the running tally');

  // a later paper stays silent
  t.startPaper(12); await sleep(20);
  ok(!t.simTeaches(),'paper 12 does not teach');
  const q2=t.QS[t.sim.qs[0]];
  q2.a.forEach(l=>t.simPick(l)); await sleep(20);
  ok(!t.simRevealed(),'answering does not reveal on paper 12');
  ok(!$('explain').classList.contains('show'),'and nothing is explained');
  ok($('exBrief').classList.contains('hidden'),'nor briefed');
  // and the answer can still be changed, as in a real exam
  const alt=q2.o.map(o=>o[0]).find(l=>!q2.a.includes(l));
  t.simPick(alt); await sleep(10);
  ok((t.sim.ans[0]||[]).indexOf(alt)>=0,'an unrevealed answer can still be changed');
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
    const items=[...box.querySelectorAll('.exwhy .exitem')];
    ok(items.length>0,'the panel renders its explanation rows');
    items.forEach((el,i)=>{
      const sp=[...el.querySelectorAll('span')].pop();
      ok(getComputedStyle(sp).direction==='rtl','explanation row '+i+' reads right to left');
      const b=el.querySelector('b');
      if(b) ok(getComputedStyle(b).unicodeBidi==='isolate',
               'row '+i+' isolates its Latin service name');
    });
    const labels=[...box.querySelectorAll('.exlbl')].map(e=>e.textContent);
    ok(labels.some(l=>HEB.test(l)),'the Hebrew sections carry Hebrew headings');
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

  t.startPaper(11); await sleep(30);
  $('simTts').click(); await sleep(30);
  eq($('simTts').textContent,'\u23f9 Stop','reading aloud mid-exam');
  ok(spoken.length>=1,'it spoke');
  ok(spoken[0].length<=160,'starting with a short piece, so sound is immediate');
  ok(spoken.join(' ').indexOf('Option')<0,'and did not read the options');
  const c0=cancels;
  t.simQTick(90); await sleep(30);
  eq(t.sim.i,1,'the 90 seconds ran out and moved on');
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
  const rows=[...$('explain').querySelectorAll('.exwhy .exitem span')]
    .filter(e=>!e.classList.contains('k'));
  ok(rows.length>0,'the explanation has reasoning rows');
  ok(rows.some(e=>HEB.test(e.textContent)),'which are in Hebrew');
  rows.forEach((e,i)=>{ if(HEB.test(e.textContent))
    eq(getComputedStyle(e).direction,'rtl','Hebrew row '+i+' reads right to left'); });
  eq(t.simQLeft,90,'and the clock did not pause to let us read');
  t.simQTick(90); await sleep(30);
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
  t.simQTick(90); await sleep(30);          // let one time out, so it exports as blank
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
  if(opts.extras!==false){ arithmeticChecks(); await refreshChecks(); await breakChecks(); await paperRowChecks(); await voiceChecks(); await hardeningChecks(); await deviceChecks(); await qClockChecks(); await resumeChecks(); await ttsChecks(); await briefChecks();
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
