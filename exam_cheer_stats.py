#!/usr/bin/env python3
"""Two additions to the exam.

  1. A line after every answer that knows where you are. Sixty-five of them, one
     per position in a paper, each naming the number you just reached. They never
     hint at whether you were right, so they are safe on the silent papers too.
  2. A statistical overview of what the papers actually contain: how many
     questions each subject has, what share of the bank that is, how many of the
     19 papers it turns up in, and how you are doing on it.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import sys

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:100])
    s = s.replace(old, new, count)


CHEER = [
 "שאלה 1. הכי קל להיות אופטימי עכשיו.",
 "שתיים. כבר יש לך רצף. טכנית.",
 "שלוש שאלות. זה כבר הרגל.",
 "ארבע. S3 עדיין עומד, וגם אתה.",
 "חמש. אחוז אחד מהדרך. תרגיש בבית.",
 "שש. הטיימר בקושי שם לב אליך.",
 "שבע. מספר מזל — אבל התשובה לא הייתה מזל.",
 "שמונה. עדיין נשאר לך יותר זמן ממה שיש ל-Lambda.",
 "תשע. עוד אחת ואתה בספרות כפולות.",
 "עשר! ספרות כפולות. מי אמר שלא תגיע.",
 "אחת עשרה. בקצב הזה תסיים לפני ש-EBS מסיים snapshot.",
 "שתים עשרה. תריסר שלם. אפשר לארוז אותך.",
 "שלוש עשרה. מזל רע? לא במבחן הזה.",
 "ארבע עשרה. שבועיים, במטבע של שאלות.",
 "חמש עשרה. בדיוק כמה דקות ש-Lambda מוכנה לעבוד.",
 "שש עשרה. רבע? כמעט. אל תבדוק במחשבון.",
 "שבע עשרה. אתה כבר יודע יותר ממה שידעת הבוקר.",
 "שמונה עשרה. גיל הבגרות — גם של הידע שלך.",
 "תשע עשרה. כמספר המבחנים כאן. צירוף מקרים מוחלט.",
 "עשרים. שליש. כן, בדקתי בשבילך.",
 "עשרים ואחת. בלאק ג'ק. בקזינו היית מרוויח.",
 "עשרים ושתיים. הזמן עף כשכיף. או כשלוחצים.",
 "עשרים ושלוש. קצב יפה. אל תספר לטיימר.",
 "עשרים וארבע. שעה שלמה, בשאלות.",
 "עשרים וחמש. רבע מהמבחן. עכשיו זה רציני.",
 "עשרים ושש. כמספר האותיות באנגלית. סיימת את כולן.",
 "עשרים ושבע. עדיין מהיר יותר מ-Glacier.",
 "עשרים ושמונה. פברואר שלם מאחוריך.",
 "עשרים ותשע. שנה מעוברת. גם אתה מיוחד.",
 "שלושים. המינימום של Standard-IA — אתה כבר לא זמני.",
 "שלושים ואחת. חודש שלם של שאלות.",
 "שלושים ושתיים. עוד אחת ואתה בחצי.",
 "שלושים ושלוש. יותר מחצי! מכאן זה במורד.",
 "שלושים וארבע. הצד השני של ההר.",
 "שלושים וחמש. עוד יש לך יותר תשובות מ-AZ-ים באזור.",
 "שלושים ושש. קצב של מישהו שעובר.",
 "שלושים ושבע. אף אחד לא סופר חוץ ממך. וממני.",
 "שלושים ושמונה. הריכוז שלך היום מרשים.",
 "שלושים ותשע. עוד רגע ארבעים.",
 "ארבעים. גיל החוכמה. או לפחות של הארכיטקטורה.",
 "ארבעים ואחת. כמעט התשובה לכל השאלות.",
 "ארבעים ושתיים. התשובה לחיים, ליקום ולכל השאר. ולשאלה הזאת.",
 "ארבעים ושלוש. אחרי 42 הכול בונוס.",
 "ארבעים וארבע. עוד 21 ואתה בבית.",
 "ארבעים וחמש. כמעט שלושה רבעים. תנשום.",
 "ארבעים ושש. השעון עדיין בצד שלך.",
 "ארבעים ושבע. נשאר פחות ממה שכבר עשית.",
 "ארבעים ושמונה. שעתיים, בדקות. גם אתה עמיד.",
 "ארבעים ותשע. שבע בריבוע. אלגנטי.",
 "חמישים! החלק הקשה מאחוריך.",
 "חמישים ואחת. ארבע עשרה נשארו. אפשר לספור על האצבעות.",
 "חמישים ושתיים. שבועות בשנה. סגרת שנה.",
 "חמישים ושלוש. כמו Route 53. במקרה? לא נראה לי.",
 "חמישים וארבע. הסוף כבר נראה מכאן.",
 "חמישים וחמש. עשר נשארו. זה כלום.",
 "חמישים ושש. רוב האנשים כבר קמו לקפה. אתה לא.",
 "חמישים ושבע. שמונה. מתחילים לספור לאחור.",
 "חמישים ושמונה. שבע. תחזיק.",
 "חמישים ותשע. שש. ממש קרוב.",
 "שישים. חמש נשארו. אתה כבר שם.",
 "שישים ואחת. ארבע. אפשר להתחיל לחייך.",
 "שישים ושתיים. שלוש. כמעט.",
 "שישים ושלוש. שתיים. אל תתרשל עכשיו.",
 "שישים וארבע. אחרונה אחת. תן הכול.",
 "שישים וחמש. זהו. עברת את כל המבחן.",
]

JS_CHEER = "const EXAM_CHEER=[\n" + ",\n".join(
    "  " + repr(line).replace("'", '"', 2) if False else "  '" + line.replace("'", "\\'") + "'"
    for line in CHEER) + "\n];"


# ------------------------------------------------------- 1. the positional line
sub("""// ---------- the first ten papers teach rather than test ----------""",
JS_CHEER + """
// One line per position in a paper. They name the number you just reached and never
// hint at whether you got it right, so they are safe on the silent papers too.
function examCheer(i,total){
  const n=i+1;
  if(i<EXAM_CHEER.length) return EXAM_CHEER[i];
  if(n===total) return 'שאלה '+n+'. זהו, סיימת את המבחן.';
  return 'שאלה '+n+' מתוך '+total+'. עוד '+(total-n)+' ואתה בבית.';
}
function cheerHTML(i,total){
  return '<div class="excheer"><span class="cem">\\u{1f680}</span>'+
    '<span class="heb" dir="rtl">'+esc(examCheer(i,total))+'</span></div>';
}

// ---------- the first ten papers teach rather than test ----------""")

sub("""  if(simTeaches()){
    bits.push('<div class="exfoot">Papers 1–'+EXPLAIN_PAPERS+' explain as you go. '+""",
"""  if(simTeaches()){
    if(sim) bits.push(cheerHTML(sim.i,sim.qs.length));
    bits.push('<div class="exfoot">Papers 1–'+EXPLAIN_PAPERS+' explain as you go. '+""")

# on a silent paper there is no panel, so the line arrives as a toast
sub("""  // on a teaching paper, committing the last required pick settles the question
  if(simTeaches()&&cur.size===need) simReveal();""",
"""  // on a teaching paper, committing the last required pick settles the question
  if(cur.size===need){
    if(simTeaches()) simReveal();
    else toast('\\u{1f680} '+examCheer(sim.i,sim.qs.length));
  }""")

# ------------------------------------------- 2. what the papers actually contain
sub("""function paperRec(n){ return (P.papers||{})[n]||null; }""",
"""function paperRec(n){ return (P.papers||{})[n]||null; }

// ---------- what is actually in these papers ----------
// Walks every question in the bank once and reports, per subject: how many there are,
// what share of a paper that works out as, how many of the papers it turns up in, and
// how you are doing on it. Computed once \u2014 the bank does not change at runtime.
const BANK_STATS=(()=>{
  const n=QS.length, per={};
  for(let s=0;s<SECTIONS.length;s++) per[s]={sec:s, n:0, papers:0};
  QS.forEach(q=>{ per[q.s].n++; });
  for(let p=1;p<=PAPER_COUNT;p++){
    const seen=new Set(paperQs(p).map(i=>QS[i].s));
    seen.forEach(sec=>per[sec].papers++);
  }
  const rows=Object.values(per).filter(r=>r.n).map(r=>({
    sec:r.sec, n:r.n, papers:r.papers,
    pct:Math.round(r.n/n*1000)/10,
    perPaper:Math.round(r.n/n*PAPER_LEN*10)/10
  }));
  rows.sort((a,b)=>b.n-a.n);
  return {total:n, papers:PAPER_COUNT, rows,
          everyPaper:rows.filter(r=>r.papers===PAPER_COUNT).length};
})();
function renderBankStats(){
  const box=$('paperStatsBody'); if(!box) return;
  const S=BANK_STATS;
  $('paperStatsTitle').textContent='What is in these papers \u2014 '+
    S.everyPaper+' subjects appear in all '+S.papers;
  box.innerHTML=S.rows.map(r=>{
    const st=(P.secStats||{})[r.sec], acc=st&&st.a?Math.round(st.c/st.a*100):null;
    const col=DOMAIN_COL[domainOf(r.sec)]||'var(--cyan)';
    return '<div class="bsrow" style="--dcol:'+col+'">'+
      '<div class="bshead"><span class="bsnm">'+secEm(r.sec)+' '+esc(SHORT[r.sec]||SECTIONS[r.sec])+'</span>'+
      '<span class="bspct">'+r.pct+'%</span></div>'+
      '<div class="bsbar"><i style="width:'+Math.min(100,r.pct*8)+'%"></i></div>'+
      '<div class="bsmeta">'+r.n+' questions \u00b7 about '+r.perPaper+' per paper \u00b7 '+
      'in '+r.papers+'/'+S.papers+' papers'+
      (acc===null?' \u00b7 not attempted':' \u00b7 you are '+acc+'% right')+'</div></div>';
  }).join('');
}""")

sub("""    <button class="exresume hidden" id="exResume"></button>""",
"""    <button class="exresume hidden" id="exResume"></button>
    <details class="exbrief" id="paperStatsBox"><summary><span>\U0001f4ca</span>
      <span id="paperStatsTitle">What is in these papers</span><span class="chev">\u203a</span></summary>
      <div class="bb" id="paperStatsBody"></div></details>""")

sub("""  $('paperStats').innerHTML=
    '<div class="stat"><b>'+done+' / '+PAPER_COUNT+'</b><span>Attempted</span></div>'+""",
"""  renderBankStats();
  $('paperStats').innerHTML=
    '<div class="stat"><b>'+done+' / '+PAPER_COUNT+'</b><span>Attempted</span></div>'+""")

# ---- all the exam CSS in one block, ABOVE the STUDY markers ----------------
# exam_extras.py originally anchored these on a selector inside STUDY:CSS, so the next
# inject_study.py run wiped them. They live in their own marked block now.
EXAM_CSS = """/* EXAM:CSS:BEGIN */
/* flex:none matters: overflow:hidden zeroes a flex item's automatic minimum size,
   and inside a .screen column that collapses the whole panel to nothing */
.exbrief{border:1px solid var(--line);background:var(--surface);border-radius:12px;
  margin-bottom:12px;overflow:hidden;flex:none}
.exbrief > summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:9px;
  padding:12px 14px;font-size:12.5px;font-weight:650;color:var(--txt)}
.exbrief > summary::-webkit-details-marker{display:none}
.exbrief > summary .chev{margin-left:auto;color:var(--dim);font-size:11px;transition:.15s}
.exbrief[open] > summary .chev{transform:rotate(90deg)}
.exbrief .bb{padding:0 14px 14px}
.exbrief .lbl{font-family:var(--mono);font-size:9.5px;letter-spacing:.8px;text-transform:uppercase;
  color:var(--dim);margin:10px 0 6px}
.exbrief .lbl:first-child{margin-top:0}
.exbrief .tip{font-size:12px;line-height:1.5;color:var(--txt);opacity:.9;margin-bottom:5px}
.exbrief .tip.warn{color:var(--gold)}
.exresume{position:relative;display:flex;align-items:center;gap:13px;width:100%;
  padding:15px 16px;border-radius:12px;background:var(--surface2);border:1px solid var(--line2);
  text-align:left;margin-bottom:14px;overflow:hidden;flex:none}
.exresume::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--gold)}
.exresume .rem{font-size:20px;flex:none}
.exresume .rnm{font-size:13.5px;font-weight:650}
.exresume .rds{font-size:11.5px;color:var(--dim);margin-top:3px}
.simbtn.tts.on{border-color:var(--cyan);color:var(--cyan)}
.explain .exnote{font-size:12.5px;line-height:1.6;padding:11px 13px;border-radius:10px;
  background:color-mix(in srgb, var(--cyan) 9%, transparent);
  border:1px solid color-mix(in srgb, var(--cyan) 26%, transparent);color:var(--txt)}
.explain .exnote b{color:var(--cyan);font-weight:650;margin-right:5px}
.excheer{display:flex;align-items:center;gap:10px;padding:11px 13px;border-radius:10px;
  background:var(--surface2);border:1px solid var(--line)}
.excheer .cem{font-size:16px;flex:none}
.excheer .heb{flex:1;text-align:right;color:var(--txt);font-size:12.5px}
#paperStatsBox{margin-bottom:14px}
.bsrow{padding:10px 0;border-top:1px solid var(--line)}
.bsrow:first-child{border-top:0;padding-top:2px}
.bshead{display:flex;align-items:baseline;gap:10px}
.bsnm{font-size:12.5px;font-weight:650;flex:1;min-width:0}
.bspct{font-family:var(--mono);font-size:12px;font-weight:650;color:var(--dcol,var(--cyan))}
.bsbar{height:4px;border-radius:3px;background:rgba(255,255,255,.08);overflow:hidden;margin:6px 0 5px}
.bsbar i{display:block;height:100%;border-radius:3px;background:var(--dcol,var(--cyan))}
.bsmeta{font-family:var(--mono);font-size:9.5px;color:var(--dim);letter-spacing:.2px}
/* EXAM:CSS:END */
"""
import re as _re
_pat = _re.compile(r"/\* EXAM:CSS:BEGIN \*/.*?/\* EXAM:CSS:END \*/\n", _re.S)
if _pat.search(s):
    s = _pat.sub(lambda _: EXAM_CSS, s, count=1)
else:
    sub("/* STUDY:CSS:BEGIN */", EXAM_CSS + "/* STUDY:CSS:BEGIN */")

sub("""    EXPLAIN_PAPERS, simTeaches, simReveal, simRevealed, simScore, simPaintRevealed,""",
    """    EXAM_CHEER, examCheer, BANK_STATS, renderBankStats,
    EXPLAIN_PAPERS, simTeaches, simReveal, simRevealed, simScore, simPaintRevealed,""")

PAGE.write_text(s, encoding="utf-8")
print("cheer + stats applied · %d lines · page %.2f MB" % (len(CHEER), len(s) / 1e6))
sys.exit(0)
