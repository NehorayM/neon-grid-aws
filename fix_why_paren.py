#!/usr/bin/env python3
"""Never split inside brackets, and never mistake a relative clause for a list item.

Two faults the audit caught after the split became hierarchical.

"ALB and NLB (C, D) are load balancers" was cut at the comma INSIDE the bracket, leaving
option C holding the string "ALB and NLB (C." — a split that breaks the text rather than
dividing it. A split is now refused if it leaves a piece with unbalanced brackets.

And "…, which is why A and B are wrong" was split off as its own clause. The guard against
stranding continuations lets a lowercase piece through when it names an option, because
"and magnetic (A) is far slower" is a genuine list item. But a piece opening with a
relative pronoun or a conjunction of consequence — which, so, because, therefore — refers
back to what came before it, and separating it leaves "Which is why A and B are wrong"
with nothing to point at. Those are never list items.

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


sub("""    const stranded=raw.slice(1).some(x=>/^[a-z]/.test(x)&&!names(x,p).length);""",
"""    // "and magnetic (A) is far slower" is a list item and belongs to A. "which is why A and
    // B are wrong" only looks like one: it points back at the clause before it, and split off
    // it points at nothing. A relative pronoun or a conjunction of consequence is the tell.
    const BACKREF=/^(which|who|whose|so|because|since|therefore|thus|hence|that|where|when|after|before|if|though|although|unless|whereas)\\b/i;
    const stranded=raw.slice(1).some(x=>/^[a-z]/.test(x)&&(BACKREF.test(x)||!names(x,p).length));
    // "ALB and NLB (C, D) are load balancers" must not be cut inside the bracket
    const bal=x=>{ const o=(x.match(/[([]/g)||[]).length, c=(x.match(/[)\\]]/g)||[]).length; return o===c; };
    const broken=raw.some(x=>!bal(x));""")

sub("""    if(tooShort||stranded||same) return splitAt(p,si+1);""",
    """    if(tooShort||stranded||broken||same) return splitAt(p,si+1);""")

PAGE.write_text(s, encoding="utf-8")
print("brackets stay whole, back-references stay put · page %.2f MB" % (len(s) / 1e6))
