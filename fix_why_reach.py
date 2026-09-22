#!/usr/bin/env python3
"""Two more things audit9 measured, after clause-splitting took the first bite.

1. A shared reason — "B and D require Lambda or Athena to poll CloudTrail logs" — is true
   of both options, but filed under D it OPENS by naming B, so the reader's eye lands on
   the wrong option. Rewriting the grammar would be guesswork; reordering the letter list
   so the option being read comes first is not. The sentence stays plural and stays true.

2. 500 options got no line at all, and the panel filled them with "the write-up does not
   single this one out" — which teaches nothing. Many of those write-ups DO discuss the
   option, they just name the service instead of the letter ("Kinesis Data Firehose cannot
   do X" rather than "C cannot do X"). So a second pass attributes an orphan sentence by
   the service it names, and only a service named by exactly ONE option counts, so a
   sentence about the right answer can never be filed under a distractor.

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


# whyByOption gains the option TEXTS, so it can attribute by service name as well as letter
sub("function whyByOption(text,letters,correct){\n  const out={}, rest=[];",
    "function whyByOption(text,letters,correct,opts){\n  const out={}, rest=[];")

sub("""  const byLetter={};
  Object.keys(out).forEach(L=>{ byLetter[L]=out[L].join(' ').replace(/[;,]\\s*$/,'.'); });""",
"""  // Second pass: these write-ups do not always use letters. "Kinesis Data Firehose cannot
  // replay a stream" is plainly about whichever option proposes Firehose. Attribute an
  // orphan sentence by the service it names — but only a service named by exactly ONE
  // option, so a sentence about the winner is never filed under a loser.
  if(opts&&opts.length){
    const keyOf=t=>{
      const set=new Set();
      (String(t).match(/\\b(?:Amazon|AWS)\\s+[A-Z][A-Za-z0-9]*(?:\\s+[A-Z][A-Za-z0-9]*)?|\\b[A-Z][A-Za-z0-9]{3,}(?:\\s+[A-Z][A-Za-z0-9]+)?/g)||[])
        .forEach(x=>{ const k=x.replace(/^(?:Amazon|AWS)\\s+/,'').trim().toLowerCase();
                      if(k.length>3) set.add(k); });
      return set;
    };
    const keys={}, count={};
    opts.forEach(([L,txt])=>{
      keys[L]=keyOf(txt);
      keys[L].forEach(k=>{ count[k]=(count[k]||0)+1; });
    });
    const orphan=rest.slice(); rest.length=0;
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
    });
  }
  // "B and D require Lambda to poll CloudTrail" is true under both, but under D it opens by
  // naming B. Put the option being read first: still plural, still accurate, and the reader
  // sees their own option named at the front instead of hunting for it.
  const leadFirst=(line,L)=>{
    const m=/^(Both\\s+|Options?\\s+)?([A-E])((?:\\s*,\\s*[A-E])*)(?:\\s*,?\\s+and\\s+([A-E]))?\\b/.exec(line);
    if(!m) return line;
    const all=[m[2]];
    (m[3]||'').split(',').forEach(x=>{ x=x.trim(); if(x) all.push(x); });
    if(m[4]) all.push(m[4]);
    if(all.length<2||all.indexOf(L)<0||all[0]===L) return line;
    const ord=[L].concat(all.filter(x=>x!==L));
    const head=(m[1]||'')+(ord.length>2
      ? ord.slice(0,-1).join(', ')+', and '+ord[ord.length-1]
      : ord[0]+' and '+ord[1]);
    return head+line.slice(m[0].length);
  };
  const byLetter={};
  Object.keys(out).forEach(L=>{
    byLetter[L]=leadFirst(out[L].join(' ').replace(/[;,]\\s*$/,'.'),L);
  });""")

# the app's own caller passes the option texts through
sub("  const why=whyByOption(q.w||'',q.o.map(x=>x[0]),q.a);",
    "  const why=whyByOption(q.w||'',q.o.map(x=>x[0]),q.a,q.o);")

PAGE.write_text(s, encoding="utf-8")
print("attribution reaches further · page %.2f MB" % (len(s) / 1e6))
