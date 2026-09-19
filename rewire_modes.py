#!/usr/bin/env python3
"""Point the two main nav tabs at the modes that earn them.

  Practice tab -> Study  (the syllabus, readable, with checks)
  Exam tab     -> Practice Exams (the numbered 65-question papers)

The five-question Exam Drill goes: the papers are the real exams, and keeping a
second thing called "exam" only confused the navigation. Its badges, its quest
and its history log survive by being repointed at the papers, so "Certified"
and "Exam Machine" now mean something a candidate would recognise.

Sector practice itself is untouched — it is still reached from the sector grid,
Weak spots, Review and Bookmarks on the home screen.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re
import sys

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:100])
    s = s.replace(old, new, count)


def cut(pattern, label):
    """Remove a whole block, anchored at the start of its line."""
    global s
    m = re.search(pattern, s, re.S | re.M)
    assert m, "block not found: " + label
    s = s[:m.start()] + s[m.end():]


# ------------------------------------------------------------- 1. the nav
sub("""    <button class="navbtn" id="navPlay"><span class="ic">⚡</span>Practice</button>
    <button class="navbtn" id="navExam"><span class="ic">\U0001f393</span>Exam</button>""",
    """    <button class="navbtn" id="navPlay"><span class="ic">\U0001f4d6</span>Study</button>
    <button class="navbtn" id="navExam"><span class="ic">\U0001f393</span>Exam</button>""")

sub("""const NAVS=[['navHome','homeScreen'],['navPlay','quizScreen'],['navExam','examScreen'],
            ['navCasino','casinoScreen'],['navShop','shopScreen'],['navBadges','achScreen']];""",
    """const NAVS=[['navHome','homeScreen'],['navPlay','stuPickScreen'],['navExam','paperScreen'],
            ['navCasino','casinoScreen'],['navShop','shopScreen'],['navBadges','achScreen']];""")

sub("""$('navPlay').onclick=()=>{ if(route!=='quizScreen'||!QS[curQ]) startSession(curSec<0?-1:curSec); else go('quizScreen'); syncNav(); };
$('navExam').onclick=()=>{ if(L) learnLeave(true);
  renderExamPicker(); go('examScreen'); syncNav(); };""",
    """$('navPlay').onclick=()=>{ if(L) learnLeave(true);
  renderStudyPick(); go('stuPickScreen'); syncNav(); };
$('navExam').onclick=()=>{ if(L) learnLeave(true);
  renderPapers(); go('paperScreen'); syncNav(); };""")

# the reading screens are long; the nav highlight should follow them too
sub("""function syncNav(){
  const hide=(route==='gameScreen'||route==='reelScreen');
  $('nav').classList.toggle('hidden',hide);
  NAVS.forEach(([b,r])=>$(b).classList.toggle('on',route===r));
}""",
"""function syncNav(){
  const hide=(route==='gameScreen'||route==='reelScreen');
  $('nav').classList.toggle('hidden',hide);
  // a tab stays lit while you are anywhere inside the mode it opened
  const family={stuReadScreen:'stuPickScreen', simRevScreen:'paperScreen',
                simDoneScreen:'paperScreen'};
  const here=family[route]||route;
  NAVS.forEach(([b,r])=>$(b).classList.toggle('on',here===r));
}""")

# ------------------------------------------- 2. the badges now track the papers
sub("""  P.answered+=len; P.correct+=correct;
  if(paper) recordPaper(paper,pct);""",
"""  P.answered+=len; P.correct+=correct;
  // the papers are the exams now, so the exam badges, quest and history track them
  P.exams=(P.exams||0)+1; if(passed) P.examsPassed=(P.examsPassed||0)+1;
  logExam(correct,len,passed);
  if(passed) questProgress('exam',1);
  if(paper) recordPaper(paper,pct);""")

sub("""  {id:'exam1',  em:'\U0001f396', nm:'Certified',       ds:'Pass a 5-question exam',              test:()=>(P.examsPassed||0)>=1},
  {id:'exam5',  em:'\U0001f3c5', nm:'Exam Machine',    ds:'Pass 5 exams',                        test:()=>(P.examsPassed||0)>=5},""",
    """  {id:'exam1',  em:'\U0001f396', nm:'Certified',       ds:'Pass a practice exam',                test:()=>(P.examsPassed||0)>=1},
  {id:'exam5',  em:'\U0001f3c5', nm:'Exam Machine',    ds:'Pass 5 practice exams',               test:()=>(P.examsPassed||0)>=5},""")

# a badge for reading the syllabus, now that there is one to read
sub("""  {id:'marks10',em:'⭐', nm:'Curator',""",
    """  {id:'read13', em:'\U0001f4d6', nm:'Well Read',       ds:'Read every Study chapter',
   test:()=>Object.values(P.study||{}).filter(r=>r.read).length>=13},
  {id:'marks10',em:'⭐', nm:'Curator',""")

# ------------------------------------------------- 3. retire the Exam Drill
sub("""      <button class="tile" id="examOpen"><span class="ic">\U0001f393</span><b>Exam ×5</b><span>Pass mark 4/5</span></button>\n""", "")
sub("""      <button class="tile" id="studyModeOpen"><span class="ic">\U0001f4da</span><b>Study Mode</b><span>Briefing first</span></button>""",
    """      <button class="tile" id="studyModeOpen"><span class="ic">\U0001f9e0</span><b>Briefed drill</b><span>A briefing before each question</span></button>""")

cut(r'^  <div id="examScreen" class="screen hidden">.*?\n  </div>\n\n', "exam screen")
cut(r'^// ================= EXAM MODE \(5-question drill\) =================\n.*?^\}\n(?=\n// ================= STORE v2)',
    "exam engine")
cut(r'^function renderExamPicker\(\)\{.*?^\}\n', "exam picker")
sub("""$('examOpen').onclick=()=>{ renderExamPicker(); go('examScreen'); };\n""", "")
sub("""$('examBack').onclick=()=>{ go('homeScreen'); renderHome(); };\n""", "")
sub("""    startExam, examNext, renderExamPicker, openStudy, closeStudy, conceptsFor, CODEX,""",
    """    openStudy, closeStudy, conceptsFor, CODEX,""")
sub("""  dueForReview, srSchedule, get exam(){return exam;},""",
    """  dueForReview, srSchedule,""")
sub("""'examScreen',""", "")

# the exam variable is gone; the modes that cleared it no longer need to
sub("""  reviewMode=false; markMode=false; exam=null; mock=null;
  const qs=paperQs(n);""",
    """  reviewMode=false; markMode=false; mock=null;
  const qs=paperQs(n);""")
sub("""  reviewMode=false; markMode=false; exam=null; mock=null;
  sim={qs:simBuild(),""",
    """  reviewMode=false; markMode=false; mock=null;
  sim={qs:simBuild(),""")
sub("""  if(mock){ mockAnswer(ok); return; }
  if(exam){ examAnswer(ok); return; }""",
    """  if(mock){ mockAnswer(ok); return; }""")
sub("""  $('examBar').classList.remove('show');\n""", "")
# the last four places that reset or read the retired variable
sub("""  mock=null; exam=null;                 // an abandoned mock/exam must not capture practice answers""",
    """  mock=null;                            // an abandoned mock must not capture practice answers""")
sub("""function explainMode(){ return !exam&&!sim&&!mock; }""",
    """function explainMode(){ return !sim&&!mock; }""")
sub("""  ensureAudio(); exitStudyMode(); reviewMode=false; markMode=false; exam=null; mock=null; sim=null;""",
    """  ensureAudio(); exitStudyMode(); reviewMode=false; markMode=false; mock=null; sim=null;""")
sub("""  exitStudyMode(); reviewMode=false; markMode=false; exam=null; mock=null; sim=null;""",
    """  exitStudyMode(); reviewMode=false; markMode=false; mock=null; sim=null;""")

# 4. the Study engine needs to be reachable from the test surface
sub("""    HEB, hebLine, hebToday, hebHTML, SEC_EM, secEm, DOMAIN_COL, secColor,""",
    """    HEB, hebLine, hebToday, hebHTML, SEC_EM, secEm, DOMAIN_COL, secColor, STUDY_T,""")

# two things called "exam" side by side was the confusion in the first place
sub("""<b>Full Exam Simulation</b><span>65 questions · 130 minutes · real blueprint</span>""",
    """<b>Random mock exam</b><span>65 drawn fresh to the real domain weights · 130 minutes</span>""")

PAGE.write_text(s, encoding="utf-8")
leftovers = [w for w in ("startExam", "examNext(", "examAnswer", "renderExamPicker",
                         "examScreen", "EXAM_LEN") if w in s]
print("rewired · page %.2f MB" % (len(s) / 1e6))
print("leftover references to the retired drill:", leftovers or "none")
sys.exit(1 if leftovers else 0)
