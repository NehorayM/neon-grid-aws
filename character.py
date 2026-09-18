#!/usr/bin/env python3
"""Third style pass: give the calm interface its character back.

The restyle fixed "too loud" and overshot into "too plain". This pass adds
meaning-carrying decoration rather than decoration for its own sake:

  * an emoji per sector, chosen for the AWS service it stands for
  * the four SAA-C03 exam domains each get a colour, and every sector card
    wears its domain's colour and says how much of the exam that domain is
  * Hebrew encouragement, placed where a learner actually pauses: the home
    screen, after an answer, at the end of an exam, at the end of a subject

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


# ---------------------------------------------------------------- 1. styles
sub("""/* ---------- home ---------- */""",
"""/* ---------- Hebrew encouragement ---------- */
/* isolate so the punctuation of an RTL line cannot reorder the Latin around it */
.heb{direction:rtl;unicode-bidi:isolate;font-size:13px;line-height:1.6}
.motiv{width:100%;max-width:var(--colw);margin:0 auto 14px;padding:12px 15px;border-radius:12px;
  background:var(--surface);border:1px solid var(--line);display:flex;align-items:center;gap:11px}
.motiv .mem{font-size:17px;flex:none;opacity:.9}
.motiv .heb{flex:1;color:var(--txt);text-align:right}
.vheb{margin-top:10px;color:var(--dim);max-width:300px}
.simheb{margin-top:10px;color:var(--dim)}

/* ---------- home ---------- */""")

sub("""h1.logo{font-size:clamp(21px,5.2vw,27px);font-weight:600;letter-spacing:6px;line-height:1.1;
  color:var(--txt);text-transform:uppercase}""",
"""h1.logo{font-size:clamp(22px,5.4vw,29px);font-weight:600;letter-spacing:6px;line-height:1.1;
  color:var(--txt);text-transform:uppercase}
h1.logo span{color:var(--cyan)}""")

# sector cards: a domain stripe, a service emoji, and what the domain is worth
sub(""".seccard .glow{display:none}
.seccard .nm{position:relative;font-size:12.5px;font-weight:650;line-height:1.35;min-height:32px}""",
""".seccard .glow{display:none}
.seccard::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--dcol,var(--cyan))}
.secrow{display:flex;align-items:flex-start;gap:9px}
.secem{font-size:16px;line-height:1.2;flex:none}
.seccard .nm{position:relative;font-size:12.5px;font-weight:650;line-height:1.35;min-height:32px;flex:1}
.secdom{position:relative;font-family:var(--mono);font-size:9.5px;letter-spacing:.4px;
  color:var(--dcol,var(--cyan));text-transform:uppercase}""")

# a touch of depth on cards, so a flat surface still reads as a surface
sub(""".card{width:100%;max-width:var(--colw);margin:0 auto 12px;padding:16px 18px;border-radius:14px;
  background:var(--surface);border:1px solid var(--line)}""",
""".card{width:100%;max-width:var(--colw);margin:0 auto 12px;padding:16px 18px;border-radius:14px;
  background:var(--surface);border:1px solid var(--line);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}""")
sub(""".tile .ic{font-size:17px;margin-bottom:6px;opacity:.75;filter:saturate(.7)}""",
    """.tile .ic{font-size:19px;margin-bottom:6px}""")
sub(""".item .em{font-size:17px;flex:none;opacity:.75;filter:saturate(.7)}""",
    """.item .em{font-size:19px;flex:none}""")
sub(""".mixcard .em{font-size:18px;opacity:.75;filter:saturate(.7)}""",
    """.mixcard .em{font-size:20px}""")

# ------------------------------------------------- 2. the data and the lines
sub("""// Sectors used to get a hue each, which turned the grid into a colour wheel.
// They now share the accent and are told apart by their name and their progress.
const hueOf=i=>(i*47)%360;
const secColor=()=>'var(--cyan)';""",
"""// Sectors used to get a hue each, which turned the grid into a colour wheel.
// They are coloured by exam domain instead: four colours that mean something.
const hueOf=i=>(i*47)%360;
const DOMAIN_COL=['#9691cc','#85c49b','#7ab6d6','#d4ae76'];   // Secure, Resilient, Performing, Cost
const secColor=i=>DOMAIN_COL[domainOf(i)]||'var(--cyan)';

// one emoji per sector, picked for the service it stands for
const SEC_EM=['\\u{1f511}','\\u{1f5a5}\\ufe0f','\\u2699\\ufe0f','\\u{1f4be}','\\u2696\\ufe0f','\\u{1f5c3}\\ufe0f',
  '\\u{1f9ed}','\\u{1faa3}','\\u{1f30d}','\\u{1f4e6}','\\u{1f4e8}','\\u{1f433}','\\u26a1','\\u{1f9ee}',
  '\\u{1f4ca}','\\u{1f916}','\\u{1f4c8}','\\u{1f3db}\\ufe0f','\\u{1f512}','\\u{1f578}\\ufe0f','\\u{1f69a}',
  '\\u{1f9f0}','\\u{1f4b0}'];
const secEm=i=>SEC_EM[i]||'\\u{1f4d8}';

// ---------- Hebrew encouragement ----------
// Short lines, placed where a learner actually stops: the home screen, the beat
// after an answer, the end of an exam, the end of a subject.
const HEB={
  daily:[
    'כל שאלה שאתה פותר היום היא אחוז שלא תצטרך לנחש בבחינה.',
    'אתה לא צריך לדעת הכול. אתה צריך לדעת להחליט.',
    '72% זה הרף. כל סשן מקרב אותך אליו.',
    'מי שפותר 65 שאלות באימון, לא נבהל מ-65 במבחן.',
    'ארכיטקט טוב לא זוכר הכול — הוא יודע מה לבחור.',
    'התמדה קטנה כל יום מנצחת יום אחד של לחץ.',
    'היום עוד נושא אחד. זה הכול.',
    'הבחינה בודקת שיקול דעת, לא שינון.',
    'מי שמתאמן על הקשה, מקבל את הקלה במתנה.',
    'עוד סשן, עוד צעד. אתה בכיוון הנכון.'
  ],
  right:[
    'יפה. עוד אחת בכיס.',
    'בדיוק. ככה זה ייראה בבחינה.',
    'מצוין — השיקול היה נכון.',
    'זהו. תמשיך ככה.',
    'תשובה של ארכיטקט.',
    'נכון, ובביטחון.'
  ],
  wrong:[
    'בסדר גמור. עכשיו זה נשאר לך בראש.',
    'טעות כאן שווה נקודה במבחן.',
    'תקרא את ההסבר — את זו כבר לא תפספס.',
    'גם ארכיטקטים טועים. פשוט לא פעמיים.',
    'זו בדיוק הסיבה שאתה מתאמן.'
  ],
  streak:[
    'רצף יפה. אל תעצור עכשיו.',
    'אתה בקצב. תשמור עליו.',
    'ככה נראה ביטחון ביום הבחינה.'
  ],
  pass:[
    'עברת. בדיוק ההרגשה שאתה רוצה ביום הבחינה.',
    'מעל הרף. עכשיו תעשה את זה שוב, ושוב.',
    'זה לא מזל. זו עבודה.'
  ],
  fail:[
    'עוד לא — אבל עכשיו אתה יודע בדיוק מה חסר.',
    'הציון הזה הוא מפה, לא גזר דין.',
    'תחזור לדומיין האדום. שם מחכים לך האחוזים.'
  ],
  learn:[
    'נושא שלם מאחוריך. זה כבר נשאר איתך.',
    'עוד אבן בקיר. הקיר הזה הוא התעודה.',
    'למדת, נבחנת, עברת. זה כל הסיפור.'
  ]
};
function hebLine(kind,seed){
  const pool=HEB[kind]||HEB.daily;
  const i=(seed==null)?Math.floor(Math.random()*pool.length)
                      :Math.abs(seed)%pool.length;
  return pool[i];
}
// the home line is the same all day, so it reads as today's line rather than noise
function hebToday(){
  const d=new Date(), n=d.getFullYear()*372+d.getMonth()*31+d.getDate();
  return hebLine('daily',n);
}
function hebHTML(kind,seed,cls){
  return '<span class="heb'+(cls?' '+cls:'')+'" dir="rtl">'+esc(hebLine(kind,seed))+'</span>';
}""")

# --------------------------------------------------- 3. the home screen line
sub("""      <h1 class="logo">NEON GRID</h1>
      <p class="tagline">AWS Solutions Architect training, wired into an arcade.</p>""",
"""      <h1 class="logo">NEON <span>GRID</span></h1>
      <p class="tagline">AWS Solutions Architect training, wired into an arcade.</p>""")
sub("""    <button class="card readycard" id="readyCard">""",
"""    <div class="motiv" id="motivBox"></div>

    <button class="card readycard" id="readyCard">""")
sub("""function renderHome(){
  if(typeof renderGoals==='function'){ renderGoals(); renderWeek(); renderTomorrow(); }""",
"""function renderHome(){
  if(typeof renderGoals==='function'){ renderGoals(); renderWeek(); renderTomorrow(); }
  const mb=$('motivBox');
  if(mb) mb.innerHTML='<span class="mem">\\u{1f331}</span>'+hebHTML('daily',
    (new Date().getFullYear()*372+new Date().getMonth()*31+new Date().getDate()));""")

# -------------------------------------------- 4. sector cards carry meaning
sub("""    const b=document.createElement('button'); b.className='seccard';
    b.dataset.nm=(SHORT[i]||name);
    const tier=tierOf(i);
    b.innerHTML='<div class="glow" style="background:'+col+'"></div>'+
      (tier.em?'<div class="mtier">'+tier.em+'</div>':'')+
      '<div class="nm">'+esc(SHORT[i]||name)+'</div>'+
      '<div class="cnt">'+n+' questions</div>'+
      '<div class="mbar"><i style="width:'+pct+'%;background:'+col+'"></i></div>'+
      '<div class="pct">'+((P.secStats[i]&&P.secStats[i].a)||0)+' seen · '+pct+'% correct</div>';""",
"""    const b=document.createElement('button'); b.className='seccard';
    b.dataset.nm=(SHORT[i]||name);
    b.style.setProperty('--dcol',col);
    const tier=tierOf(i), dom=DOMAINS[domainOf(i)];
    b.innerHTML=(tier.em?'<div class="mtier">'+tier.em+'</div>':'')+
      '<div class="secrow"><span class="secem">'+secEm(i)+'</span>'+
      '<div class="nm">'+esc(SHORT[i]||name)+'</div></div>'+
      '<div class="secdom">'+esc(dom.short)+' · '+dom.w+'%</div>'+
      '<div class="cnt">'+n+' questions</div>'+
      '<div class="mbar"><i style="width:'+pct+'%;background:'+col+'"></i></div>'+
      '<div class="pct">'+((P.secStats[i]&&P.secStats[i].a)||0)+' seen · '+pct+'% correct</div>';""")

# --------------------------------------- 5. a line in the beat after an answer
sub("""      <div class="vsub" id="vSub"></div>""",
    """      <div class="vsub" id="vSub"></div>
      <div class="vsub vheb" id="vHeb"></div>""")
sub("""  $('vSub').textContent=ok?'Streak '+P.streak+' — reward round unlocked':'Added to your review queue';""",
"""  $('vSub').textContent=ok?'Streak '+P.streak+' — reward round unlocked':'Added to your review queue';
  const vh=$('vHeb');
  if(vh) vh.innerHTML=hebHTML(ok?(P.streak>=5?'streak':'right'):'wrong');""")

# ------------------------------------------------ 6. a line on the exam result
sub("""      <div class="ch-note" id="simMeta"></div>""",
    """      <div class="ch-note" id="simMeta"></div>
      <div class="ch-note simheb" id="simHeb"></div>""")
sub("  $('simAgain').textContent=paper?(paper<PAPER_COUNT?",
    "  $('simHeb').innerHTML=hebHTML(passed?'pass':'fail');\n"
    "  $('simAgain').textContent=paper?(paper<PAPER_COUNT?")

# ------------------------------------------- 7. emoji on the Learn subject list
sub("""    b.innerHTML='<span class="cem">'+(rec&&rec.best>=LSIM_PASS?'🎓':done?'📗':'📘')+'</span>'+""",
    """    b.innerHTML='<span class="cem">'+(rec&&rec.best>=LSIM_PASS?'🎓':secEm(sec))+'</span>'+""")

# --------------------------------- 8. the sector emoji rides along in the quiz
sub("""  $('qSector').textContent=(SHORT[q.s]||SECTIONS[q.s]).slice(0,22);""",
    """  $('qSector').textContent=secEm(q.s)+' '+(SHORT[q.s]||SECTIONS[q.s]).slice(0,20);""")

# 9. the set summary is the other natural pause in a practice run
sub("""      <div class="vsub" id="sumSub"></div>\n      <div class="row" style="margin-top:18px">""",
    """      <div class="vsub" id="sumSub"></div>\n      <div class="vsub vheb" id="sumHeb"></div>\n      <div class="row" style="margin-top:18px">""")
sub("""  go('sumScreen');""",
    """  $('sumHeb').innerHTML=hebHTML(pct>=80?'streak':pct>=50?'right':'wrong');\n  go('sumScreen');""")

# 10. the new helpers need to be reachable from the test surface
sub("    QS, SECTIONS, SHORT, BANKV, bySec, BADGES, GAMES,",
    "    QS, SECTIONS, SHORT, BANKV, bySec, BADGES, GAMES,\n"
    "    HEB, hebLine, hebToday, hebHTML, SEC_EM, secEm, DOMAIN_COL, secColor,")

PAGE.write_text(s, encoding="utf-8")
print("character pass applied, page is %.2f MB" % (len(s) / 1e6))
