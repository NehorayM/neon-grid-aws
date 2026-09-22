#!/usr/bin/env python3
"""Resume from the exam's own row, and warn before throwing a run away.

Two things were wrong with the Practice Exams screen.

  1. A saved run was only offered by one bar at the top. If you were part way
     through Exam 7 and went looking for Exam 7 in the list, its row said
     "Retake" like every other — and pressing it silently deleted what you had
     done. The row for the paper you are part way through now says **Resume**,
     shows where you got to, and has a separate ↻ to start it over.

  2. Pressing Start or Retake on any *other* paper also destroyed the saved run
     without asking. It only warned when the run belonged to another device,
     which was the narrow case. It now warns whenever there is progress to lose,
     naming the exam and how far in you were, using the app's own two-tap.

Nothing is deleted on the first tap. The button changes to the question and
reverts after four seconds if it is not answered.

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


sub("""    const b=document.createElement('button');
    b.className='buy'; b.textContent=rec?'Retake':'Start';
    // startPaper clears the saved run, which would delete an exam still open elsewhere
    b.onclick=()=>{
      const open=simSaved();
      if(open&&!simOwns(open)){
        armed(b,'Discard the exam on '+otherDevice(open)+'?',()=>startPaper(n));
        return;
      }
      startPaper(n);
    };
    row.appendChild(b); L.appendChild(row);""",
"""    // The row for the paper you are part way through offers to continue it, rather than
    // making you find the bar at the top — and rather than saying "Retake" over a run you
    // have not finished, which is what used to quietly delete it.
    const savedHere=sv&&(sv.paper||0)===n;
    if(savedHere){
      const again=document.createElement('button');
      again.className='buy pstart';
      again.textContent='\\u21bb';
      again.title='Start Exam '+n+' again from the beginning';
      again.setAttribute('aria-label','Start Exam '+n+' again from the beginning, '+
        'discarding question '+((sv.i||0)+1)+' of '+sv.qs.length);
      again.onclick=()=>armed(again,
        'Delete your progress on Exam '+n+' and start again?',
        ()=>{ simClearSave(); startPaper(n); });
      row.appendChild(again);
    }
    const b=document.createElement('button');
    b.className='buy';
    b.textContent=savedHere?'Resume':(rec?'Retake':'Start');
    if(savedHere) b.setAttribute('aria-label',
      'Resume Exam '+n+' at question '+((sv.i||0)+1)+' of '+sv.qs.length);
    b.onclick=()=>{
      const open=simSaved();
      if(savedHere){ simResumeHere(open||sv); return; }
      // Starting anything else throws the saved run away. Say so, and say what is being lost.
      if(open){
        const where=simOwns(open)?'':(' on '+otherDevice(open));
        const what=(open.paper?'Exam '+open.paper:'the mock exam')+where+
          ' \\u2014 question '+((open.i||0)+1)+' of '+open.qs.length;
        armed(b,'Delete your progress on '+what+'?',()=>startPaper(n));
        return;
      }
      startPaper(n);
    };
    row.appendChild(b); L.appendChild(row);""")

# the row for a saved paper says where you got to, instead of the attempt count
sub("""    const meta=rec
      ? rec.tries+' attempt'+(rec.tries>1?'s':'')+' · last '+rec.last
      : len+' questions · '+SIM_QSEC+'s each · '+simBudget(len)+' min';""",
"""    const here=sv&&(sv.paper||0)===n;
    const meta=here
      ? ('in progress \\u00b7 question '+((sv.i||0)+1)+' of '+sv.qs.length+' \\u00b7 '+
         simAnsweredIn(sv)+' answered \\u00b7 '+fmtClock(sv.left)+' left')
      : rec
      ? rec.tries+' attempt'+(rec.tries>1?'s':'')+' \\u00b7 last '+rec.last
      : len+' questions \\u00b7 '+SIM_QSEC+'s each \\u00b7 '+simBudget(len)+' min';""")

sub("""    const em=rec?(rec.best>=SIM_PASS?'\U0001f393':'\U0001f4dd'):'\U0001f4c4';""",
"""    const em=(sv&&(sv.paper||0)===n)?'⏸':rec?(rec.best>=SIM_PASS?'\U0001f393':'\U0001f4dd'):'\U0001f4c4';""")

# the in-progress row is marked so it reads as unfinished rather than scored
sub("""    const col=rec?(rec.best>=SIM_PASS?'var(--lime)':'var(--gold)'):'var(--line2)';
    row.style.setProperty('--dcol',col);""",
"""    const col=(sv&&(sv.paper||0)===n)?'var(--cyan)'
      :rec?(rec.best>=SIM_PASS?'var(--lime)':'var(--gold)'):'var(--line2)';
    row.style.setProperty('--dcol',col);
    if(sv&&(sv.paper||0)===n) row.classList.add('resuming');""")

sub(""".paperrow{position:relative;overflow:hidden}""",
""".paperrow{position:relative;overflow:hidden}
.paperrow.resuming{border-color:color-mix(in srgb, var(--cyan) 45%, var(--line));
  background:color-mix(in srgb, var(--cyan) 7%, var(--surface))}
.buy.pstart{flex:none;padding:9px 11px;font-size:13px;line-height:1;margin-right:-4px}""")

PAGE.write_text(s, encoding="utf-8")
print("resume moved onto the paper's own row · page %.2f MB" % (len(s) / 1e6))
