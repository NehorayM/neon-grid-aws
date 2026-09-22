#!/usr/bin/env python3
"""Two corrections to the pass I just added.

The keyword pass made blanks and thin right-answers WORSE (500->557, 426->494), and the
reason is that these write-ups open with the case for the correct answer and only then
name the losers. That opening names no letter, so it was in the orphan pile — and the
keyword pass handed it to whichever distractor happened to mention the same service,
leaving the correct option with nothing at all. The opening sentence is now reserved for
the answer, and the pass is undone entirely if it would strip the answer bare.

Second, "A installs an agent at boot (slows launches), B polls on a schedule" is a list
joined by commas, not by "and", so the splitter left it whole and filed the lot under A.
A comma followed by a letter and a verb is now a split point — but "A, B, and D fail" is
not, because there the letter is followed by another comma.

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


# comma-joined option lists split too — ", B polls on a schedule" but not ", B, and D fail"
sub("|;\\s+|,\\s+and\\s+(?=[A-Z])/).map(x=>x.trim()).filter(Boolean);",
    "|;\\s+|,\\s+and\\s+(?=[A-Z])|,\\s+(?=[A-E]\\s+[a-z])/)\n      .map(x=>x.trim()).filter(Boolean);")

sub("""    const orphan=rest.slice(); rest.length=0;
    orphan.forEach(p=>{
      const low=p.toLowerCase();
      let hit=null;
      opts.forEach(([L])=>{
        if(hit) return;
        keys[L].forEach(k=>{ if(!hit&&count[k]===1&&low.indexOf(k)>=0) hit=L; });
      });
      // never steal the sentence that makes the case for the right answer
      if(hit&&correct.indexOf(hit)<0) (out[hit]=out[hit]||[]).push(p);
      else rest.push(p);
    });""",
"""    const orphan=rest.slice(); rest.length=0;
    const taken=[];
    orphan.forEach((p,pi)=>{
      const low=p.toLowerCase();
      let hit=null;
      opts.forEach(([L])=>{
        if(hit) return;
        keys[L].forEach(k=>{ if(!hit&&count[k]===1&&low.indexOf(k)>=0) hit=L; });
      });
      // These write-ups open with the case FOR the answer before naming any loser, and that
      // opening names no letter. Diverting it to a distractor is how the right option ended
      // up with nothing, so the first orphan always stays with the answer.
      if(pi>0&&hit&&correct.indexOf(hit)<0){ taken.push([hit,p]); }
      else rest.push(p);
    });
    // and if the diversion would still leave the answer with nothing of its own, undo it
    const answerBare=!rest.length&&correct.every(L=>!(out[L]&&out[L].length));
    if(answerBare) taken.forEach(([,p])=>rest.push(p));
    else taken.forEach(([L,p])=>{ (out[L]=out[L]||[]).push(p); });""")

PAGE.write_text(s, encoding="utf-8")
print("the answer keeps its own case · page %.2f MB" % (len(s) / 1e6))
