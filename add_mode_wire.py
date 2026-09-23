#!/usr/bin/env python3
"""Hook the picker to every place a paper begins, and show which kind a saved one is.

Start, Retake and the restart-from-scratch arrow all ask. Resume does not. The "next paper"
button at the end of a run inherits the mode you were just sitting in, because being asked
again between paper 3 and paper 4 of the same sitting is noise.

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


# the sheet's own buttons
sub("""$('brkAskNo').onclick=()=>brkAskClose();""",
"""$('modeAskExam').onclick=()=>modePick('exam');
$('modeAskPractice').onclick=()=>modePick('practice');
$('modeAskNo').onclick=()=>modeAskClose();
$('modeAsk').onclick=e=>{ if(e.target&&e.target.id==='modeAsk') modeAskClose(); };
$('brkAskNo').onclick=()=>brkAskClose();""")

# restart-from-scratch arrow on the row you are part way through
sub("""      again.onclick=()=>armed(again,
        'Delete your progress on Exam '+n+' and start again?',
        ()=>{ simClearSave(); startPaper(n); });""",
"""      again.onclick=()=>armed(again,
        'Delete your progress on Exam '+n+' and start again?',
        ()=>{ simClearSave(); modeAsk('Exam '+n,m=>startPaper(n,m)); });""")

# Start / Retake
sub("""        armed(b,'Delete your progress on '+what+'?',()=>startPaper(n));
        return;
      }
      startPaper(n);""",
"""        armed(b,'Delete your progress on '+what+'?',
          ()=>modeAsk('Exam '+n,m=>startPaper(n,m)));
        return;
      }
      modeAsk('Exam '+n,m=>startPaper(n,m));""")

# the next paper at the end of a run keeps the mode you were already sitting in
sub("""  if(n&&n<PAPER_COUNT) startPaper(n+1);""",
"""  if(n&&n<PAPER_COUNT) startPaper(n+1,(sim&&sim.mode)||'exam');""")

# and the row says which kind the saved paper is, so Resume is not a surprise
sub("""    b.textContent=savedHere?'Resume':(rec?'Retake':'Start');""",
"""    b.textContent=savedHere?'Resume':(rec?'Retake':'Start');
    if(savedHere&&sv.mode==='practice') b.title='Resume \\u2014 practice run, pauses freely';""")

PAGE.write_text(s, encoding="utf-8")
print("every start asks · page %.2f MB" % (len(s) / 1e6))
