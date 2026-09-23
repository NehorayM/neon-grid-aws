#!/usr/bin/env python3
"""Score the papers the way SAA-C03 is scored: by domain, on the 100–1000 scale, pass at 720.

From the official exam guide (docs.aws.amazon.com, SAA-C03):
  - results are a scaled score of 100–1,000; the minimum passing score is 720
  - four content domains weighted 30 / 26 / 24 / 20 % of scored content (Secure, Resilient,
    High-Performing, Cost-Optimized) — the weighting is done by how many questions each
    domain gets on a real form
  - compensatory: only the overall score has to pass, not each domain
  - unanswered questions are scored as incorrect
  - the raw-to-scaled conversion is not published (it is equated per exam form)

Two problems made "weight by subject" impossible as the app stood.

1. Every question's domain came from its SERVICE, not from what it asks. Every EC2, S3,
   database, container and networking question counted as High-Performing, so the bank read
   Secure 11 / Resilient 31 / Performing 55 / Cost 3 — and several papers had no Cost
   questions at all. The real exam classifies by the task being tested, and SAA questions
   state it in their requirement line ("MOST cost-effectively", "MOST secure", "highly
   available"). Classifying on that, with the service as the fallback when a question states
   nothing, gives 27 / 16 / 41 / 15 — much nearer 30 / 26 / 24 / 20. The rest of the skew is
   the bank's own (it is a dump, not a balanced form), and is exactly what weighting corrects.

2. A paper's raw percentage reflects the paper's mix, not the exam's. The score is now
   30% x Secure accuracy + 26% x Resilient + 24% x Performing + 20% x Cost. A domain with only
   a couple of questions on a paper is blended with the overall accuracy (six questions'
   worth), so two Cost questions cannot swing the score by a hundred points either way.

The weighted fraction goes onto 100–1000 through three anchors — 0% -> 100, 72% -> 720,
100% -> 1000 — keeping the app's 72% pass line at AWS's 720. AWS does not publish its
conversion; this is an estimate, and the stricter one of the two common readings.

Shown live as "Score so far" on the teaching papers and in practice, where each answer is
already revealed. On an exam-conditions paper it stays hidden until you submit, because a
running score would tell you whether each answer was right.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")

def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)

# ---- classification and scoring, next to the domain table ----------------------------
sub("""function domainOf(sec){ const d=DOMAINS.find(x=>x.secs.includes(sec)); return d?d.id:2; }""",
"""function domainOf(sec){ const d=DOMAINS.find(x=>x.secs.includes(sec)); return d?d.id:2; }
// ---------- the SAA-C03 domain a QUESTION tests ----------
// domainOf() files a question by its service, so every EC2, S3, database and networking
// question counted as High-Performing and the bank read 11/31/55/3 against the exam's
// 30/26/24/20. The exam classifies by the task being tested, and these questions state it in
// their requirement line. The service is the fallback when a question states nothing.
const DOM_CUE=[
  /\\bsecur(e|ely|ity)\\b|encrypt|least[- ]privilege|unauthori[sz]ed|permissions?\\b|access control|complian(ce|t)|credentials?|\\bIAM\\b|\\bKMS\\b|protect|attack|DDoS|vulnerab|audit|\\bMFA\\b|sensitive|restrict(ed)? access|private(ly)? (connect|access)|in transit|at rest|intrusion|malicious/i,
  /highly available|high availability|fault[- ]toleran|disaster recovery|\\bRPO\\b|\\bRTO\\b|fail ?over|resilien|durab|decoupl|loosely coupled|data loss|outage|redundan|multi-AZ|Availability Zone (failure|outage)|recover|single point of failure|retry|survive/i,
  /performance|latency|throughput|\\bscal(e|es|able|ability|ing)\\b|\\bIOPS\\b|faster|real[- ]time|cach(e|ing)|high-performing|response time|concurrent|burst|milliseconds?|speed|bottleneck/i,
  /cost[- ]effective|lowest cost|least (expensive|costly|cost)|minimi[sz]e (the )?costs?|reduce (the )?costs?|economical|cost[- ]optimi|cheapest|lower (the )?costs?|costs? (savings|less)|without (additional|incurring) costs?|\\bbudget|pay (only )?for|spend/i,
];
function examDomainOf(q){
  // the requirement line, with a trailing "(Select TWO.)" taken off so it can be found
  const x=String(q.q||'').replace(/\\(\\s*(select|choose)[^)]*\\)\\s*$/i,'').trim();
  const m=x.match(/[^.?!]*\\?\\s*$/), tail=m?m[0]:'';
  const sc=[0,0,0,0];
  DOM_CUE.forEach((re,d)=>{ if(re.test(tail)) sc[d]+=3; if(re.test(x)) sc[d]+=1; });
  const best=Math.max(...sc), svc=domainOf(q.s);
  if(!best) return svc;
  const tops=sc.map((v,i)=>v===best?i:-1).filter(i=>i>=0);
  return tops.includes(svc)?svc:tops[0];
}
let EXAM_DOM=null;
function qDom(qi){ if(!EXAM_DOM) EXAM_DOM=QS.map(examDomainOf); return EXAM_DOM[qi]; }
// ---------- the SAA-C03 score ----------
// Weighted by the exam's own domain mix, not the paper's; a domain with few questions on the
// paper is blended with the overall accuracy so two questions cannot swing it by 100 points.
const SAA_PASS=720, SAA_SHRINK=4;
function saaScaled(f){
  f=Math.max(0,Math.min(1,Number(f)||0));
  const P=SIM_PASS/100;       // 72% -> 720; 0% -> 100; 100% -> 1000 (AWS does not publish theirs)
  return Math.round(f<=P ? 100+(f/P)*(SAA_PASS-100) : SAA_PASS+((f-P)/(1-P))*(1000-SAA_PASS));
}
function saaScore(pairs){
  const n=[0,0,0,0], c=[0,0,0,0]; let N=0, C=0;
  (pairs||[]).forEach(p=>{ const d=qDom(p.qi); n[d]++; N++; if(p.ok){ c[d]++; C++; } });
  if(!N) return null;
  const overall=C/N;
  let f=0, W=0;
  DOMAINS.forEach(d=>{ const acc=(c[d.id]+SAA_SHRINK*overall)/(n[d.id]+SAA_SHRINK); f+=d.w*acc; W+=d.w; });
  f/=W;
  const scaled=saaScaled(f);
  return {frac:f, pct:Math.round(f*100), scaled, passed:scaled>=SAA_PASS, n, c, N, C,
          raw:Math.round(overall*100)};
}""")

# ---- live score in the paper strip ------------------------------------------------------
sub("""        <div class="stsub" id="simTotalSub"></div>
      </div>""",
"""        <div class="stsub" id="simTotalSub"></div>
        <div class="stlive hidden" id="simLive">
          <span class="stlbl">Score so far</span>
          <span class="stval" id="simLiveVal">—</span>
          <span class="stlivesub" id="simLiveSub"></span>
        </div>
      </div>""")

sub(""".simtotal.tight .stval{color:var(--gold)}""",
""".simtotal.tight .stval{color:var(--gold)}
.stlive{display:flex;align-items:baseline;gap:8px;margin-top:7px;padding-top:7px;
  border-top:1px dashed color-mix(in srgb, var(--cyan) 22%, var(--line))}
.stlive.hidden{display:none}
.stlive .stval.pass{color:var(--lime)}
.stlive .stval.fail{color:var(--red)}
.stlivesub{font-size:10.5px;color:var(--dim);font-family:var(--mono)}""")

sub("""  // Amber in the last five minutes, while there is still something unanswered to spend it on.""",
"""  renderSimLive();
  // Amber in the last five minutes, while there is still something unanswered to spend it on.""")

sub("""function renderSimQ(){""",
"""// Where the paper stands on the SAA scale, over what has been answered. Only where each answer
// is already revealed — a teaching paper, or practice — because on an exam-conditions paper a
// running score would say whether every answer was right.
function renderSimLive(){
  const box=$('simLive'); if(!box) return;
  const show=!!(sim&&sim.running&&(simTeaches()||isPractice()));
  box.classList.toggle('hidden',!show);
  if(!show) return;
  const pairs=[];
  sim.qs.forEach((qi,i)=>{
    const picked=sim.ans[i]||[];
    if(!picked.length) return;
    if(simTeaches()&&!simRevealed(i)) return;
    const q=QS[qi], set=new Set(picked);
    pairs.push({qi, ok:q.a.length===set.size&&q.a.every(a=>set.has(a))});
  });
  const S=saaScore(pairs), v=$('simLiveVal');
  v.classList.remove('pass','fail');
  if(!S){ v.textContent='\\u2014'; $('simLiveSub').textContent='answer one to start'; return; }
  v.textContent=S.scaled;
  v.classList.add(S.passed?'pass':'fail');
  $('simLiveSub').textContent='/ 1000 \\u00b7 pass '+SAA_PASS+' \\u00b7 '+S.C+'/'+S.N+' right';
}
function renderSimQ(){""")

# an answer changes it straight away, not on the next tick
sub("""  simPersist(); renderSimStrip();
}
// ---------- feedback during a teaching paper ----------""",
"""  simPersist(); renderSimStrip(); renderSimLive();
}
// ---------- feedback during a teaching paper ----------""")

# ---- the result is the SAA score -------------------------------------------------------
sub("""    const d=domainOf(q.s);
    byDom[d][1]++; if(ok){ byDom[d][0]++; correct++; } else missed.push(qi);""",
"""    const d=qDom(qi);
    byDom[d][1]++; if(ok){ byDom[d][0]++; correct++; } else missed.push(qi);
    scored.push({qi,ok});""")

sub("""  let correct=0, gain=0; const byDom={0:[0,0],1:[0,0],2:[0,0],3:[0,0]}; const missed=[];""",
    """  let correct=0, gain=0; const byDom={0:[0,0],1:[0,0],2:[0,0],3:[0,0]}; const missed=[], scored=[];""")

sub("""  const len=simLen();
  const pct=Math.round(correct/len*100);
  const passed=pct>=SIM_PASS;""",
"""  const len=simLen();
  // Scored like SAA-C03: weighted by the exam's domain mix, on 100–1000, pass at 720. Blanks
  // count as wrong, as they do on the real exam. `pct` is the weighted percentage now.
  const S=saaScore(scored)||{pct:0,scaled:100,passed:false,raw:0};
  const pct=S.pct;
  const passed=S.passed;""")

sub("""  P.simLog.unshift({d:dayKey(),p:pct,pass:passed?1:0,mins,pr:isPractice()?1:0,ct:cont?1:0,""",
    """  P.simLog.unshift({d:dayKey(),p:pct,sc:S.scaled,pass:passed?1:0,mins,pr:isPractice()?1:0,ct:cont?1:0,""")

sub("""  $('simScore').textContent=pct+'%';
  $('simScore').style.color=passed?'var(--lime)':'var(--red)';
  $('simVerdict').textContent=(paper?'Exam '+paper+' — ':'')+
    (passed?'PASS — above the 72% line':'BELOW PASS — 72% needed');
  $('simMeta').textContent=correct+' / '+len+' correct · '+mins+' min · +'+coins+' 🪙'+""",
"""  $('simScore').textContent=S.scaled;
  $('simScore').style.color=passed?'var(--lime)':'var(--red)';
  $('simVerdict').textContent=(paper?'Exam '+paper+' — ':'')+
    (passed?'PASS':'BELOW PASS')+' \\u00b7 '+S.scaled+' / 1000, '+SAA_PASS+' needed';
  $('simMeta').textContent=correct+' / '+len+' correct ('+S.raw+'%) \\u00b7 '+
    pct+'% weighted by the exam\\u2019s domain mix \\u00b7 '+mins+' min · +'+coins+' 🪙'+""")

# ---- history and rows speak the same scale ---------------------------------------------------
sub("""      '<div class="nm">'+num(m.p)+'% '+(m.pass?'— pass':'— below 72%')+(m.ct?' · finished later':m.pr?' · practice':'')+'</div>'+""",
"""      '<div class="nm">'+(m.sc?num(m.sc)+' / 1000 ':num(m.p)+'% ')+(m.pass?'— pass':(m.sc?'— below 720':'— below 72%'))+
        (m.ct?' · finished later':m.pr?' · practice':'')+'</div>'+""")

sub("""    d:dstr(m.d), p:n0(m.p), pass:m.pass?1:0, mins:n0(m.mins), pr:m.pr?1:0, ct:m.ct?1:0,""",
    """    d:dstr(m.d), p:n0(m.p), sc:m.sc!==undefined?Math.max(100,Math.min(1000,n0(m.sc))):undefined,
    pass:m.pass?1:0, mins:n0(m.mins), pr:m.pr?1:0, ct:m.ct?1:0,""")

sub("""      ((rec&&!here)?'<div class="pscore" style="color:'+col+'">'+(Number(rec.best)|0)+'%'+""",
    """      ((rec&&!here)?'<div class="pscore" style="color:'+col+'">'+saaScaled((Number(rec.best)||0)/100)+""")

# expose for the harness
sub("    isPractice, brkOpen, brkElapsed,",
    "    isPractice, brkOpen, brkElapsed, saaScore, saaScaled, qDom, examDomainOf, renderSimLive, SAA_PASS,")

PAGE.write_text(s, encoding="utf-8")
print("SAA-C03 scoring in")
