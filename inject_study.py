#!/usr/bin/env python3
"""Add the Study mode to index.html: screens, styles and engine.

Study mode is the reference half of the app. Learn mode gates you part by part;
Study mode just lets you read. One chapter is one page: every topic in it, the
authored tables and diagrams inline, a jump bar at the top, and a handful of
multiple-choice checks at the bottom to prove the page went in.

It reuses the Learn mode's block renderer (`blocksHTML`), so both modes speak
one visual language and there is only one renderer to maintain.

Idempotent: re-running replaces the STUDY blocks rather than duplicating them.
"""
import pathlib
import re
import sys

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"

CSS = """
/* ---------- study mode ---------- */
.stucard{position:relative;display:flex;align-items:flex-start;gap:13px;width:100%;
  padding:15px 16px;border-radius:12px;background:var(--surface);border:1px solid var(--line);
  text-align:left;transition:.15s;overflow:hidden}
.stucard:hover{border-color:var(--line2);background:var(--surface2)}
.stucard:active{transform:scale(.99)}
.stucard::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--dcol,var(--cyan))}
.stucard .sem{font-size:20px;flex:none;line-height:1.2}
.stucard .snm{font-size:14px;font-weight:650}
.stucard .ssub{font-size:11.5px;color:var(--dim);line-height:1.45;margin-top:3px}
.stucard .smeta{font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:7px;letter-spacing:.3px}
.studone{flex:none;font-size:11px;font-weight:650;color:var(--lime);white-space:nowrap}
.stujump{display:flex;gap:6px;overflow-x:auto;padding:2px 0 10px;margin-bottom:4px;
  scrollbar-width:none;-webkit-overflow-scrolling:touch}
.stujump::-webkit-scrollbar{display:none}
.stujump button{flex:none;font-size:11px;font-weight:550;padding:7px 12px;border-radius:8px;
  background:var(--surface);border:1px solid var(--line);color:var(--dim);white-space:nowrap}
.stujump button:hover,.stujump button.on{color:var(--txt);border-color:var(--line2)}
.stutopic{scroll-margin-top:86px;padding-top:6px}
.stutopic h2{font-size:17px;font-weight:650;letter-spacing:.2px;margin:22px 0 10px;
  padding-bottom:9px;border-bottom:1px solid var(--line)}
.stutopic:first-of-type h2{margin-top:6px}
.stuq{border:1px solid var(--line);background:var(--surface);border-radius:12px;
  padding:15px 16px;margin-bottom:10px}
.stuq .qq{font-size:14px;line-height:1.55;font-weight:650;margin-bottom:11px}
.stuo{display:block;width:100%;text-align:left;font-size:13.5px;line-height:1.5;
  padding:11px 13px;border-radius:9px;background:var(--panel);border:1px solid var(--line);
  color:var(--txt);margin-bottom:7px;transition:.14s}
.stuo:hover{border-color:var(--line2)}
.stuo.ok{border-color:var(--lime);background:color-mix(in srgb, var(--lime) 11%, transparent)}
.stuo.no{border-color:var(--red);background:color-mix(in srgb, var(--red) 11%, transparent)}
.stuo:disabled{cursor:default}
.stufeed{font-size:12px;margin-top:4px;color:var(--dim)}
.stuprog{font-family:var(--mono);font-size:10.5px;color:var(--dim)}
.stuw{margin-top:9px}
.stuw .wbar{height:4px;border-radius:3px;background:rgba(255,255,255,.08);overflow:hidden}
.stuw .wbar i{display:block;height:100%;border-radius:3px;background:var(--dcol,var(--cyan))}
.stuw .wtxt{font-family:var(--mono);font-size:9.5px;color:var(--dim);margin-top:5px;letter-spacing:.2px}
.stuw .wtxt b{color:var(--txt);font-size:11px}
.stuw.heavy .wtxt b{color:var(--gold)}
/* the chapter body is long; give the sticky footer room to breathe */
#stuReadScreen .crsfoot{margin-top:18px}
"""

SCREENS = """
  <!-- STUDY: CHAPTER PICKER -->
  <div id="stuPickScreen" class="screen hidden">
    <button class="backbtn" id="stuPickBack">‹</button>
    <div style="text-align:center;margin-bottom:14px">
      <h2 class="head">\U0001f4d6 Study</h2>
      <p class="sub">The whole syllabus written out, chapter by chapter — with the comparison
        tables and decision trees the prose cannot carry. Read in any order, nothing is locked.</p>
    </div>
    <div class="motiv" id="stuMotiv"></div>
    <div class="statstrip" id="stuStats" style="margin-bottom:14px"></div>
    <div class="list" id="stuPickList"></div>
  </div>

  <!-- STUDY: READING A CHAPTER -->
  <div id="stuReadScreen" class="screen hidden">
    <button class="backbtn" id="stuReadBack">‹</button>
    <div class="crswrap">
      <div class="qtop" style="margin-bottom:10px">
        <span class="tag" id="stuTag">CHAPTER</span>
        <span class="stuprog" id="stuCount"></span>
      </div>
      <h2 class="head" id="stuTitle"></h2>
      <p class="sub" id="stuSub" style="margin-bottom:12px"></p>
      <div class="statstrip" id="stuWeight" style="margin-bottom:14px"></div>
      <div class="stujump" id="stuJump"></div>
      <div class="mdx" id="stuBody"></div>
      <div class="sechead">Quick check</div>
      <div id="stuQuiz"></div>
      <div class="crsfoot">
        <div class="row" style="justify-content:center">
          <button class="btn" id="stuNext">Next chapter ▸</button>
          <button class="btn ghost sm" id="stuPractise">Practise these questions</button>
        </div>
      </div>
    </div>
  </div>
"""

JS = r"""
// ================= STUDY =================
// The reference half of the app: the syllabus as pages you can read in any order.
// Learn mode teaches and gates; this one just explains, and checks at the end that
// the page went in. Blocks render through the Learn mode's renderer.
const STUDY=(()=>{ const el=$('studydata'); if(!el) return {chapters:[]};
  try{ return JSON.parse(el.textContent); }catch(e){ return {chapters:[]}; } })();
const STU_CH=STUDY.chapters||[];
// a chapter maps onto the exam domains through the sectors it covers, so the
// colour on its card means the same thing as everywhere else in the app
const STU_DOM=[0,0,2,2,2,1,1,2,1,2,0,2,3];
// Which question sectors each chapter covers. Every sector belongs to exactly one
// chapter, so the weights below add up to the whole bank and a chapter can honestly
// say how much of the exam it is worth.
const STU_SECS=[[21,22],[0,17],[7,8,9],[1,2],[3],[5,13],[6],[19],[4],[10],[18],[11,12],[14,15,16,20]];
function stuWeight(i){
  const secs=STU_SECS[i]||[];
  const n=secs.reduce((a,s)=>a+((bySec[s]||[]).length),0);
  return {n, pct:QS.length?Math.round(n/QS.length*1000)/10:0, secs};
}
// how well you have done on the sectors a chapter covers, and how much of it you have seen
function stuMastery(i){
  let a=0,c=0,pool=0;
  (STU_SECS[i]||[]).forEach(s=>{
    const st=(P.secStats||{})[s]; if(st){ a+=st.a; c+=st.c; }
    pool+=(bySec[s]||[]).length;
  });
  return {a, c, pool, acc:a?Math.round(c/a*100):0, seen:pool?Math.round(Math.min(1,a/pool)*100):0};
}
let stuIdx=-1;

function stuRec(i){ return (P.study||{})[i]||null; }
function stuMarkRead(i){
  P.study=P.study||{};
  const r=P.study[i]||{read:0,best:0};
  r.read=1; r.at=dayKey(); P.study[i]=r; saveProfile();
}
function stuMarkQuiz(i,pct){
  P.study=P.study||{};
  const r=P.study[i]||{read:0,best:0};
  r.read=1; r.best=Math.max(r.best||0,pct); r.at=dayKey(); P.study[i]=r; saveProfile();
}
function renderStudyPick(){
  const L=$('stuPickList'); if(!L) return;
  L.innerHTML='';
  const read=STU_CH.filter((c,i)=>stuRec(i)&&stuRec(i).read).length;
  const aced=STU_CH.filter((c,i)=>stuRec(i)&&stuRec(i).best>=100).length;
  const mins=STU_CH.reduce((a,c)=>a+c.min,0);
  $('stuStats').innerHTML=
    '<div class="stat"><b>'+read+' / '+STU_CH.length+'</b><span>Chapters read</span></div>'+
    '<div class="stat"><b>'+aced+'</b><span>Checks aced</span></div>'+
    '<div class="stat"><b>'+mins+'m</b><span>Whole syllabus</span></div>';
  const mb=$('stuMotiv');
  if(mb) mb.innerHTML='<span class="mem">\u{1f4da}</span>'+hebHTML('daily',read+3);
  STU_CH.forEach((c,i)=>{
    const rec=stuRec(i);
    const b=document.createElement('button'); b.className='stucard';
    b.style.setProperty('--dcol',DOMAIN_COL[STU_DOM[i]]||'var(--cyan)');
    b.innerHTML='<span class="sem">'+c.em+'</span>'+
      '<span style="flex:1;min-width:0"><span class="snm">'+esc(c.nm)+'</span>'+
      '<div class="ssub">'+esc(c.sub)+'</div>'+
      '<div class="smeta">'+c.topics.length+' topics · '+c.min+' min read · '+
      c.quiz.length+' checks'+(rec&&rec.best?' · check '+rec.best+'%':'')+'</div>'+
      stuWeightHTML(i)+'</span>'+
      (rec&&rec.read?'<span class="studone">✓ read</span>':'');
    b.onclick=()=>stuOpen(i);
    L.appendChild(b);
  });
}
// The number a learner actually wants: how much of the exam this chapter is, and
// how much of it they have already proved they know.
function stuWeightHTML(i){
  const w=stuWeight(i), m=stuMastery(i);
  if(!w.n) return '';
  const band=w.pct>=10?'heavy':w.pct>=5?'mid':'light';
  return '<div class="stuw '+band+'">'+
    '<div class="wbar"><i style="width:'+Math.min(100,w.pct*6)+'%"></i></div>'+
    '<div class="wtxt"><b>'+w.pct+'%</b> of the exam · '+w.n+' questions'+
    (m.a?' · you are '+m.acc+'% right on '+m.a+' of them':' · none attempted yet')+
    '</div></div>';
}
function stuOpen(i){
  if(i<0||i>=STU_CH.length) return;
  stuIdx=i;
  const c=STU_CH[i];
  $('stuTag').textContent='CHAPTER '+(i+1)+' / '+STU_CH.length;
  $('stuCount').textContent=c.topics.length+' topics · '+c.min+' min';
  $('stuTitle').textContent=c.em+'  '+c.nm;
  $('stuSub').textContent=c.sub;
  const w=stuWeight(i), m=stuMastery(i);
  $('stuWeight').innerHTML=w.n
    ? '<div class="stat"><b>'+w.pct+'%</b><span>Of the exam</span></div>'+
      '<div class="stat"><b>'+w.n+'</b><span>Questions</span></div>'+
      '<div class="stat"><b>'+(m.a?m.acc+'%':'—')+'</b><span>You are right</span></div>'
    : '';
  const jump=$('stuJump'); jump.innerHTML='';
  c.topics.forEach((t,k)=>{
    const b=document.createElement('button'); b.textContent=t.nm;
    b.onclick=()=>{ const el=$('stuT'+k); if(el) el.scrollIntoView({behavior:'smooth',block:'start'}); };
    jump.appendChild(b);
  });
  $('stuBody').innerHTML=c.topics.map((t,k)=>
    '<section class="stutopic" id="stuT'+k+'"><h2>'+esc(t.nm)+'</h2>'+blocksHTML(t.blocks)+'</section>'
  ).join('');
  stuRenderQuiz(c);
  $('stuNext').textContent=i<STU_CH.length-1?('Next: '+STU_CH[i+1].nm+' ▸'):'Back to chapters';
  stuMarkRead(i);
  go('stuReadScreen');
  const sc=$('stuReadScreen'); if(sc) sc.scrollTop=0;
}
function stuRenderQuiz(c){
  const box=$('stuQuiz'); box.innerHTML='';
  const state={done:0,right:0};
  c.quiz.forEach((q,qi)=>{
    const card=document.createElement('div'); card.className='stuq';
    const opts=q.o.map((o,oi)=>'<button class="stuo" data-i="'+oi+'">'+esc(o)+'</button>').join('');
    card.innerHTML='<div class="qq">'+esc(q.q)+'</div>'+opts+'<div class="stufeed"></div>';
    const feed=card.querySelector('.stufeed');
    [...card.querySelectorAll('.stuo')].forEach(btn=>{
      btn.onclick=()=>{
        if(card.dataset.done) return;
        card.dataset.done='1';
        const picked=+btn.dataset.i, ok=picked===q.a;
        [...card.querySelectorAll('.stuo')].forEach((b2,i2)=>{
          b2.disabled=true;
          if(i2===q.a) b2.classList.add('ok');
          else if(i2===picked) b2.classList.add('no');
        });
        feed.innerHTML=(ok?'✓ Correct. ':'✗ The answer is '+esc(q.o[q.a])+'. ')+
          hebHTML(ok?'right':'wrong');
        state.done++; if(ok){ state.right++; sfx.right(); } else sfx.wrong();
        if(state.done===c.quiz.length){
          const pct=Math.round(state.right/c.quiz.length*100);
          stuMarkQuiz(stuIdx,pct);
          addXP(state.right*8); addCoins(state.right*2);
          toast('Quick check — '+state.right+' / '+c.quiz.length);
          checkBadges();
        }
      };
    });
    box.appendChild(card);
  });
}
function stuNext(){
  if(stuIdx<STU_CH.length-1) stuOpen(stuIdx+1);
  else { renderStudyPick(); go('stuPickScreen'); }
}
function stuPractise(){
  // the sectors a chapter covers, so "practise this" lands on relevant questions
  const map=[0,0,7,1,3,5,6,19,4,10,18,12,16];
  startSession(map[stuIdx]!=null?map[stuIdx]:-1);
}
function openStudy2(){ renderStudyPick(); go('stuPickScreen'); }
$('stuPickBack').onclick=()=>{ go('homeScreen'); renderHome(); };
$('stuReadBack').onclick=()=>{ renderStudyPick(); go('stuPickScreen'); };
$('stuNext').onclick=stuNext;
$('stuPractise').onclick=stuPractise;
const STUDY_T={ STUDY, STU_CH, STU_SECS, get stuIdx(){return stuIdx;}, stuOpen, stuNext,
  stuPractise, renderStudyPick, stuRec, openStudy2, stuRenderQuiz, stuWeight, stuMastery,
  stuWeightHTML };
"""


def block(tag, body, comment="  "):
    return f"<!-- STUDY:{tag}:BEGIN -->\n{body.strip()}\n<!-- STUDY:{tag}:END -->\n"


def put(s, tag, body, anchor, css=False, js=False):
    open_, close = f"STUDY:{tag}:BEGIN", f"STUDY:{tag}:END"
    if css or js:
        wrapped = f"/* {open_} */\n{body.strip()}\n/* {close} */\n"
    else:
        wrapped = f"<!-- {open_} -->\n{body.strip()}\n<!-- {close} -->\n"
    pat = re.compile(re.escape(("/* " if (css or js) else "<!-- ") + open_) + r".*?"
                     + re.escape(close + (" */" if (css or js) else " -->")) + r"\n", re.S)
    if pat.search(s):
        return pat.sub(lambda _: wrapped, s, count=1)
    assert anchor in s, f"anchor for {tag} not found"
    return s.replace(anchor, wrapped + anchor, 1)


def main():
    s = PAGE.read_text(encoding="utf-8")
    s = put(s, "CSS", CSS, "/* ---------- home ---------- */", css=True)
    s = put(s, "SCREENS", SCREENS, "  <!-- NUMBERED PRACTICE EXAMS -->")
    s = put(s, "JS", JS, "const LEARN_T={", js=True)

    # the router has to know the new screens or they never lose .hidden
    for sid in ("stuPickScreen", "stuReadScreen"):
        if f"'{sid}'" not in s.split("function go(")[0].split("const SCREENS=")[1].split("];")[0]:
            s = s.replace("'simRevScreen','simDoneScreen','paperScreen','timerScreen',",
                          "'simRevScreen','simDoneScreen','paperScreen','stuPickScreen','stuReadScreen','timerScreen',", 1)
            break

    # every id the engine touches must exist in the markup
    ids = set(re.findall(r"\$\('([A-Za-z0-9_]+)'\)", CSS + SCREENS + JS))
    have = set(re.findall(r'id="([A-Za-z0-9_]+)"', s))
    missing = sorted(i for i in ids if i not in have)
    assert not missing, f"engine touches ids that do not exist: {missing}"

    PAGE.write_text(s, encoding="utf-8")
    print(f"study mode injected · {len(ids)} element ids checked · page {len(s)/1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
