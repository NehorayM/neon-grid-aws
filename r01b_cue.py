#!/usr/bin/env python3
"""Round 1, second half: a cue must match on the service it RECOMMENDS.

After requiring any overlap with the correct option, 10% of cues were still off. The worst
kind: "Global Accelerator (not CloudFront)" qualified under a CloudFront answer by matching
on CloudFront — the very thing the cue says not to pick. "Lambda in VPC (+ NAT Gateway)"
qualified on "VPC", a word half the networking bank contains.

A cue's answer names one service first and qualifies it after. That leading service is what
the cue recommends, so it is the one the correct option has to contain. exFind returns terms
in glossary order, not text order, so the leading one is found by position.

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

sub("""    if(!c._terms) c._terms=exFind(c.a,3);
    const terms=c._terms;
    if(!terms.length) return;
    const answerHits=terms.filter(t=>correct.indexOf(t.t.toLowerCase())>=0).length;
    // A cue is a claim about the ANSWER — "if it says X, think Y". Stem words alone cleared
    // the threshold ("access", "private", "session"), so a VPN question was cued with
    // CloudFront Signed Cookies. No overlap with the correct option, no cue.
    if(!answerHits) return;""",
"""    if(!c._terms){
      c._terms=exFind(c.a,3);
      // The service the cue RECOMMENDS is the one it names first; the rest qualify it —
      // "Global Accelerator (not CloudFront)", "Lambda in VPC (+ NAT Gateway)". exFind hands
      // terms back in glossary order, so the leading one is found by where it sits in the text.
      const low=String(c.a||'').toLowerCase();
      let at=1e9; c._lead=null;
      c._terms.forEach(t=>{
        t.parts.forEach(pp=>{ const k=low.indexOf(pp.toLowerCase()); if(k>=0&&k<at){ at=k; c._lead=t; } });
      });
    }
    const terms=c._terms;
    if(!terms.length||!c._lead) return;
    // A cue is a claim about the ANSWER — "if it says X, think Y". Stem words alone cleared
    // the old threshold, and matching ANY named service let "Global Accelerator (not
    // CloudFront)" qualify under a CloudFront answer. The recommended service must be there.
    if(!c._lead._re.some(re=>re.test(' '+correct+' '))) return;
    const answerHits=terms.filter(t=>correct.indexOf(t.t.toLowerCase())>=0).length;""")

PAGE.write_text(s, encoding="utf-8")
print("cue must contain the service it recommends")
