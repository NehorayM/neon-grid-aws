#!/usr/bin/env python3
"""Get the text-size and bookmark buttons out of the question's way.

They sat in the sticky bar at the foot of the quiz, which meant that during an
exam — where the lifelines, the hint and Lock in are all hidden — those two
buttons were the only thing in the bar, and it still reserved a full row above
the navigation for them. They belong with the other question chrome at the top.

  * fsBtn and markBtn move into .qtop, next to the sector and the counter
  * .qtop wraps rather than overflowing on a narrow phone
  * the foot bar now hides itself whenever nothing inside it is visible

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


# ------------------------------------------------- 1. move the two buttons up
sub("""      <div class="qtop">
        <span class="tag" id="qSector">SECTOR</span>
        <span class="tag" id="qBadge">EASY</span>
        <span class="tag" id="qCount">1</span>
      </div>""",
"""      <div class="qtop">
        <span class="tag" id="qSector">SECTOR</span>
        <div class="qprog"><i id="qProg"></i></div>
        <span class="tag" id="qBadge">EASY</span>
        <span class="tag" id="qCount">1</span>
        <button class="fsbtn qtool" id="fsBtn" title="Text size" aria-label="Text size">Aa</button>
        <button class="fsbtn qtool" id="markBtn" title="Bookmark this question"
          aria-label="Bookmark this question">☆</button>
      </div>""")

sub("""      <div class="qbar">
        <button class="life" id="lifeFifty">✂️ 50/50 <b>30</b></button>
        <button class="life" id="lifeSkip">⏭ Skip <b>20</b></button>
        <button class="fsbtn" id="fsBtn" title="Text size">Aa</button>
        <button class="fsbtn" id="markBtn" title="Bookmark">☆</button>
        <button class="fsbtn" id="hintBtn" title="Hint">\U0001f4a1</button>""",
"""      <div class="qbar" id="qBar">
        <button class="life" id="lifeFifty">✂️ 50/50 <b>30</b></button>
        <button class="life" id="lifeSkip">⏭ Skip <b>20</b></button>
        <button class="fsbtn" id="hintBtn" title="Hint" aria-label="Use a hint">\U0001f4a1</button>""")

# ------------------------------------------------------------- 2. styling
sub(""".fsbtn{font-family:var(--mono);font-size:12px;font-weight:600;padding:9px 11px;border-radius:9px;
  background:var(--surface);border:1px solid var(--line);color:var(--dim)}""",
""".fsbtn{font-family:var(--mono);font-size:12px;font-weight:600;padding:9px 11px;border-radius:9px;
  background:var(--surface);border:1px solid var(--line);color:var(--dim)}
/* the compact pair that rides in the question header instead of the foot bar */
.qtop .qtool{flex:none;padding:5px 9px;font-size:11px;border-radius:7px;line-height:1.35}
.qtop .qtool.on{color:var(--gold);border-color:var(--gold)}
/* The progress bar moved out of the header and onto its own full-width line:
   four pixels tall, and it buys the row enough space to stay on one line at
   375px with the two tools in it. */
.qtop{flex-wrap:wrap;gap:6px}
.qtop .tag{padding:5px 8px}
.qtop #qSector{flex:1 1 auto;min-width:0;max-width:none}
.qtop #qCount{margin-left:0}
.qprog.wide{width:100%;margin:-4px 0 2px}
.qtop #qSector{max-width:46%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}""")

# ------------------------------------- 3. the foot bar disappears when empty
# the progress bar gets its own full-width line under the header
sub("""      </div>\n      <div id="qTimerWrap" class="hidden">""",
    """      </div>\n      <div class="qprog wide"><i id="qProg"></i></div>\n      <div id="qTimerWrap" class="hidden">""")

sub("""function loadQuestionInto(qi){""",
"""// The foot bar holds the lifelines, the hint and Lock in. An exam hides all of
// them, so without this it would reserve an empty row above the navigation.
function syncQBar(){
  const bar=$('qBar'); if(!bar) return;
  const live=[...bar.children].some(el=>
    !el.classList.contains('hidden') && getComputedStyle(el).display!=='none');
  bar.classList.toggle('hidden',!live);
}
function loadQuestionInto(qi){""")

sub("""  renderCharge(); startQTimer(); renderMarkBtn(); renderQBadge(); markQStart();""",
    """  renderCharge(); startQTimer(); renderMarkBtn(); renderQBadge(); markQStart(); syncQBar();""")

sub("""  } else hideExplain();
  renderExamBrief(qi);""",
    """  } else hideExplain();
  renderMarkBtn(); syncQBar();
  renderExamBrief(qi);""")

# the mock hides the same controls, so it needs the same sync
sub("""  $('examBar').classList.add('show');
  $('examProg').textContent='mock exam · no help';
  go('quizScreen');""",
"""  $('examBar').classList.add('show');
  $('examProg').textContent='mock exam · no help';
  renderMarkBtn(); syncQBar();
  go('quizScreen');""")

sub("""    simPersist, simClearSave, simSaved, simResume, ttsOk, ttsStop, ttsText, ttsSpeak,""",
    """    syncQBar,
    simPersist, simClearSave, simSaved, simResume, ttsOk, ttsStop, ttsText, ttsSpeak,""")

PAGE.write_text(s, encoding="utf-8")
print("question tools moved · page %.2f MB" % (len(s) / 1e6))
sys.exit(0)
