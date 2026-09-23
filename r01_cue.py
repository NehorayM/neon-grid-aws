#!/usr/bin/env python3
"""Round 1: the exam cue named services the question never mentions, and was slow.

Measured on a sample: 23% of the cues shown under an answer named a service that appears
nowhere in the question, its options or its explanation. A Site-to-Site VPN question was
cued "restrict access to many private files for a session -> CloudFront Signed Cookies".

The scoring gave 2 points per cue answer-term found in the correct option, and 1 point per
cue word found in the stem, with a threshold of 3. Three generic stem words — "access",
"private", "session" — cleared the bar on their own, with no connection at all to the
answer. A cue is a claim about the ANSWER ("if it says X, think Y"), so it now has to share
at least one term with the correct option before the stem is allowed to count.

And every call rebuilt a RegExp per glossary term, for each of 216 cues, per question —
~18 ms each time an explanation opened. The patterns are compiled once, and each cue's
answer terms are worked out once.

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

sub("""  for(const term of EX_TERMS){
    if(hits.length>=limit) break;
    if(EX_STOP.has(term.t.toLowerCase())) continue;
    const hit=term.parts.some(pp=>{
      const esc=pp.toLowerCase().replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&');
      return new RegExp('(?<![a-z0-9])'+esc+'(?![a-z0-9])').test(low);
    });""",
"""  for(const term of EX_TERMS){
    if(hits.length>=limit) break;
    if(EX_STOP.has(term.t.toLowerCase())) continue;
    // Compiled once per term and kept. Building a RegExp per part on every call cost ~18 ms
    // per explanation, because exCue runs this for each of 216 cues.
    if(!term._re) term._re=term.parts.map(pp=>{
      const esc=pp.toLowerCase().replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&');
      return new RegExp('(?<![a-z0-9])'+esc+'(?![a-z0-9])');
    });
    const hit=term._re.some(re=>re.test(low));""")

sub("""  let best=null,bestScore=0;
  (EXPLAIN.cues||[]).forEach(c=>{
    const terms=exFind(c.a,3);
    if(!terms.length) return;
    let score=terms.reduce((s,t)=>s+(correct.indexOf(t.t.toLowerCase())>=0?2:0),0);
    const cueWords=(c.c||'').toLowerCase().replace(/[^a-z0-9 ]/g,' ').split(/\\s+/).filter(w=>w.length>4&&!EX_STOP.has(w));
    score+=cueWords.filter(w=>stem.indexOf(w)>=0).length;""",
"""  let best=null,bestScore=0;
  (EXPLAIN.cues||[]).forEach(c=>{
    if(!c._terms) c._terms=exFind(c.a,3);
    const terms=c._terms;
    if(!terms.length) return;
    const answerHits=terms.filter(t=>correct.indexOf(t.t.toLowerCase())>=0).length;
    // A cue is a claim about the ANSWER — "if it says X, think Y". Stem words alone cleared
    // the threshold ("access", "private", "session"), so a VPN question was cued with
    // CloudFront Signed Cookies. No overlap with the correct option, no cue.
    if(!answerHits) return;
    let score=answerHits*2;
    if(!c._words) c._words=(c.c||'').toLowerCase().replace(/[^a-z0-9 ]/g,' ').split(/\\s+/)
      .filter(w=>w.length>4&&!EX_STOP.has(w));
    score+=c._words.filter(w=>stem.indexOf(w)>=0).length;""")

PAGE.write_text(s, encoding="utf-8")
print("cue must match the answer; patterns compiled once")
