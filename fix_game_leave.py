#!/usr/bin/env python3
"""A mini-game must stop when you leave its screen.

Found by driving all nine games: navigating away from `gameScreen` leaves
`gRunning` true and the requestAnimationFrame loop alive. It keeps stepping
physics, ticking the timer and accumulating score against a canvas nobody is
looking at, and when the timer finally runs out it awards coins, XP, a high
score and quest progress for a game you walked out of.

Exactly the class of bug `leaveExam()` was written for, and the same fix: one
place that ends it, called from the router.

Leaving abandons the run rather than scoring it — you left. `endGame()` stays for
the honest ending, where the timer ran out or the player finished.

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


sub("""// Anything that takes over the question screen calls this first, so two engines can never
// both be driving it. It keeps the paper, which the Practice Exams screen offers back.
function leaveExam(){""",
"""// Walking away from a mini-game used to leave its animation loop running: still stepping
// physics, still ticking the clock, still adding score against a canvas nobody can see — and
// when the timer finally ran out it paid coins, XP, a high score and quest progress for a game
// that had been abandoned minutes earlier. Leaving abandons it; endGame() is for finishing it.
function leaveGame(){
  if(typeof gRunning==='undefined'||!gRunning) return;
  gRunning=false;
  try{ if(gRaf) cancelAnimationFrame(gRaf); }catch(e){}
  gRaf=null;
  const hp=$('bossHP'); if(hp) hp.classList.add('hidden');
}

// Anything that takes over the question screen calls this first, so two engines can never
// both be driving it. It keeps the paper, which the Practice Exams screen offers back.
function leaveExam(){""")

sub("""  if(id!=='quizScreen') stopQTimer();        // leaving the quiz freezes the countdown
  _go(id);""",
"""  if(id!=='quizScreen') stopQTimer();        // leaving the quiz freezes the countdown
  if(id!=='gameScreen'&&typeof leaveGame==='function') leaveGame();
  _go(id);""")

sub("""    syncQBar, leaveExam, pctW, plural, accPct, BUILD,""",
"""    syncQBar, leaveExam, leaveGame, pctW, plural, accPct, BUILD,""")

PAGE.write_text(s, encoding="utf-8")
print("a game now stops when you leave it · page %.2f MB" % (len(s) / 1e6))
