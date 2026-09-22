#!/usr/bin/env python3
"""Progress bars that go past 100%.

The chest bar was the one that showed: with an ordinary profile it was rendering
`width: 1104%`, because chestProgress() computes `25 - (nextChest - answered)`
and never clamped it — finish a 65-question paper, or merge a profile from
another device, and `answered` overshoots `nextChest` by more than the span.
The parent's overflow:hidden was the only thing hiding it.

Rather than patch that one sum, every percentage width in the file now goes
through pctW(), which clamps to 0..100 and turns NaN into 0. Eleven of the
twenty-eight were already clamped by hand at their call site; the rest relied on
their inputs being well behaved, and three of them are fed by values that come
back from the server (the roulette and duel countdowns) or from a merged profile.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# ------------------------------------------------------------ the helper
sub("""const reduced=typeof window.matchMedia==='function'""",
"""// Every bar in the app is an <i> whose width is a percentage. Most of the sums feeding them
// are ratios that cannot exceed 1 — but not all, and the ones that can were rendering widths
// like 1104% behind an overflow:hidden that happened to hide the damage.
const pctW=n=>{ n=Number(n); return (isFinite(n)?Math.max(0,Math.min(100,n)):0)+'%'; };
const reduced=typeof window.matchMedia==='function'""")

# ----------------------------------------------------- the root of the chest one
sub("""  const span=25, into=span-(P.nextChest-P.answered);
  return {into:Math.max(0,into),span,left:Math.max(0,P.nextChest-P.answered)};""",
"""  // answered overshoots nextChest by more than the span after a long paper or a merge
  const span=25, into=span-(P.nextChest-P.answered);
  return {into:Math.max(0,Math.min(span,into)),span,left:Math.max(0,P.nextChest-P.answered)};""")

# ------------------------------------------------------------ every bar
REPL = [
    ("""  $('qProg').style.width=Math.min(100,sessionCount*10)+'%';""",
     """  $('qProg').style.width=pctW(sessionCount*10);"""),
    ("""  $('gtimer').style.width=(frac*100)+'%';""",
     """  $('gtimer').style.width=pctW(frac*100);"""),
    ("""  $('qTimerFill').style.width=(f*100)+'%';""",
     """  $('qTimerFill').style.width=pctW(f*100);"""),
    ("""    $('bossHPFill').style.width=Math.max(0,boss.hp/boss.maxHp*100)+'%';""",
     """    $('bossHPFill').style.width=pctW(boss.hp/boss.maxHp*100);"""),
    ("""  const el=$('dailyFill'); if(el) el.style.width=pct+'%';""",
     """  const el=$('dailyFill'); if(el) el.style.width=pctW(pct);"""),
    ("""      '<div class="qtrack"><i style="width:'+(cur/def.goal*100)+'%"></i></div>'+""",
     """      '<div class="qtrack"><i style="width:'+pctW(cur/def.goal*100)+'"></i></div>'+"""),
    ("""  f.style.width=Math.round(c.into/c.span*100)+'%';""",
     """  f.style.width=pctW(Math.round(c.into/c.span*100));"""),
    ("""  $('qProg').style.width=Math.round(mock.i/MOCK_LEN*100)+'%';""",
     """  $('qProg').style.width=pctW(Math.round(mock.i/MOCK_LEN*100));"""),
    ("""        '<div class="dt"><i style="width:'+acc+'%"></i></div>'+""",
     """        '<div class="dt"><i style="width:'+pctW(acc)+'"></i></div>'+"""),
    ("""  if(f) f.style.width=Math.round((s-1)/(SKILL_MAX-1)*100)+'%';""",
     """  if(f) f.style.width=pctW(Math.round((s-1)/(SKILL_MAX-1)*100));"""),
    ("""      '<div class="bprog"><i style="width:'+Math.round(seen/Math.max(1,pool.length)*100)+'%;background:'+col+'"></i></div></div>';""",
     """      '<div class="bprog"><i style="width:'+pctW(Math.round(seen/Math.max(1,pool.length)*100))+';background:'+col+'"></i></div></div>';"""),
    ("""  fill.style.width=(f*100)+'%';""",
     """  fill.style.width=pctW(f*100);"""),
    ("""  $('qProg').style.width=Math.round((sim.i+1)/simLen()*100)+'%';""",
     """  $('qProg').style.width=pctW(Math.round((sim.i+1)/simLen()*100));"""),
    ("""      '<div class="dt"><i style="width:'+p+'%;background:'+(p>=72?'var(--lime)':'var(--red)')+'"></i></div>'+""",
     """      '<div class="dt"><i style="width:'+pctW(p)+';background:'+(p>=72?'var(--lime)':'var(--red)')+'"></i></div>'+"""),
    ("""      '<div class="bsbar"><i style="width:'+Math.min(100,r.pct*8)+'%"></i></div>'+""",
     """      '<div class="bsbar"><i style="width:'+pctW(r.pct*8)+'"></i></div>'+"""),
    ("""      (rec?'<div class="pbar"><i style="width:'+rec.best+'%;background:'+col+'"></i></div>':'')+""",
     """      (rec?'<div class="pbar"><i style="width:'+pctW(rec.best)+';background:'+col+'"></i></div>':'')+"""),
    ("""  f.style.width=Math.min(100,Math.round(w.n/WEEK_TARGET*100))+'%';""",
     """  f.style.width=pctW(Math.round(w.n/WEEK_TARGET*100));"""),
    ("""      (pr?'<div class="bprog"><i style="width:'+Math.min(100,Math.round(pr[0]/pr[1]*100))+'%"></i></div>':'')+""",
     """      (pr?'<div class="bprog"><i style="width:'+pctW(Math.round(pr[0]/pr[1]*100))+'"></i></div>':'')+"""),
    ("""  $('rouBarFill').style.width=Math.max(0,Math.min(100,(s.secondsLeft/25)*100))+'%';""",
     """  $('rouBarFill').style.width=pctW((s.secondsLeft/25)*100);"""),
    ("""      $('rouBarFill').style.width=Math.max(0,(rouLocalLeft/25)*100)+'%';""",
     """      $('rouBarFill').style.width=pctW((rouLocalLeft/25)*100);"""),
    ("""      $('duelBarFill').style.width=Math.max(0,(duelLeft/duelTotal)*100)+'%';""",
     """      $('duelBarFill').style.width=pctW((duelLeft/duelTotal)*100);"""),
    ("""  $('lrnQuizProg').style.width=Math.round(Q.i/Q.items.length*100)+'%';""",
     """  $('lrnQuizProg').style.width=pctW(Math.round(Q.i/Q.items.length*100));"""),
    ("""    '<div class="wbar"><i style="width:'+Math.min(100,w.pct*6)+'%"></i></div>'+""",
     """    '<div class="wbar"><i style="width:'+pctW(w.pct*6)+'"></i></div>'+"""),
    ("""      '<div class="mbar"><i style="width:'+pct+'%;background:'+col+'"></i></div>'+""",
     """      '<div class="mbar"><i style="width:'+pctW(pct)+';background:'+col+'"></i></div>'+"""),
    ("""  f.style.width=Math.round(c.into/c.span*100)+'%';""",
     """  f.style.width=pctW(Math.round(c.into/c.span*100));"""),
]
done = 0
for old, new in REPL:
    if old in s:
        s = s.replace(old, new, 1)
        done += 1

# the two goal bars share their line shape
for old, new in [
    ("""      '<div class="gt"><i style="width:'+pct+'%"></i></div>'+""",
     """      '<div class="gt"><i style="width:'+pctW(pct)+'"></i></div>'+"""),
]:
    while old in s:
        s = s.replace(old, new, 1)
        done += 1

sub("""    syncQBar, leaveExam, timerClamp,""", """    syncQBar, leaveExam, pctW, chestProgress, timerClamp,""")

left = [m.group(0) for m in re.finditer(r"style\.width=[^;\n]*'%'", s)]
assert not left, "still unclamped: %s" % left[:3]

PAGE.write_text(s, encoding="utf-8")
print("clamped %d bars · page %.2f MB" % (done, len(s) / 1e6))
