#!/usr/bin/env python3
"""Stop the keyword pass stealing the answer's own evidence, and punctuate the joins.

q7 showed option C being told "C cannot push gp3 past its limit io2 supports up to 64,000
IOPS." Two faults in one line.

First, "io2 supports up to 64,000 IOPS" is the evidence FOR option D, the correct answer.
The keyword pass refused to file a sentence under a correct option but happily filed one
under a distractor, so a sentence about io2 was diverted to C and the answer lost its
supporting fact. A sentence that mentions a service the correct option names is about the
correct option, and now stays with it.

Second, two attributed clauses were joined with a space and no full stop, so they ran
together into one unreadable sentence. Each clause is punctuated before joining.

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


sub("""      // These write-ups open with the case FOR the answer before naming any loser, and that
      // opening names no letter. Diverting it to a distractor is how the right option ended
      // up with nothing, so the first orphan always stays with the answer.
      if(pi>0&&hit&&correct.indexOf(hit)<0){ taken.push([hit,p]); }""",
"""      // "io2 supports up to 64,000 IOPS" is the evidence for the option that proposes io2.
      // Diverting it to a distractor that happens to share a keyword takes the answer's own
      // support away from it, so anything naming a service the answer names stays put.
      const answers=correct.some(L=>Array.from(keys[L]||[]).some(k=>low.indexOf(k)>=0));
      // These write-ups open with the case FOR the answer before naming any loser, and that
      // opening names no letter, so the first orphan always stays with the answer too.
      if(pi>0&&hit&&!answers&&correct.indexOf(hit)<0){ taken.push([hit,p]); }""")

sub("""  Object.keys(out).forEach(L=>{
    byLetter[L]=leadFirst(out[L].join(' ').replace(/[;,]\\s*$/,'.'),L);
  });""",
"""  // Two clauses joined with a space and no stop read as one broken sentence: "C cannot push
  // gp3 past its limit io2 supports up to 64,000 IOPS."
  const stop=x=>x.replace(/[\\s,;]+$/,'').replace(/([^.!?])$/,'$1.');
  Object.keys(out).forEach(L=>{
    byLetter[L]=leadFirst(out[L].map(stop).join(' '),L);
  });""")

sub("""  const leftover=rest.join(' ').replace(/[;,]\\s*$/,'.').trim();""",
    """  const leftover=rest.map(stop).join(' ').trim();""")

PAGE.write_text(s, encoding="utf-8")
print("the answer keeps its own evidence · page %.2f MB" % (len(s) / 1e6))
