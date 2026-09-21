#!/usr/bin/env python3
"""Label the Hebrew sections in Hebrew, and stop the panel repeating itself.

Two small things left over once the definitions themselves were translated:

  * "Why it fits" and "Why the others don't" now head three Hebrew sentences
    each, and the trade-off table's benefit column and the service cards above
    it are Hebrew too. Their headings follow the content.
    The verified-answer note keeps its English "Why" — that note is still
    English, so an English label over it is the honest pairing.

  * buildExplain() already refuses to explain a distractor with a service the
    correct answer uses, but not with one another distractor already used. On a
    question where A and B are both CloudTrail the panel printed the same
    sentence twice in a row. The same `used` set now grows as it goes.

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


# ------------------------------------------- 1. no two distractors, one service
sub("""  const distractors=q.o.filter(x=>!q.a.includes(x[0])).map(x=>({
    ltr:x[0], txt:x[1], picked:picked.has(x[0]),
    terms:exFind(x[1],4).filter(t=>!used.has(t.t.toLowerCase())).slice(0,1)
  }));""",
"""  const distractors=q.o.filter(x=>!q.a.includes(x[0])).map(x=>{
    // ...and not with one a previous distractor already claimed, or the panel
    // prints the identical sentence twice under two different letters
    const t=exFind(x[1],4).filter(t=>!used.has(t.t.toLowerCase())).slice(0,1);
    if(t.length) used.add(t[0].t.toLowerCase());
    return {ltr:x[0], txt:x[1], picked:picked.has(x[0]), terms:t};
  });""")

# --------------------------------------------- 2. Hebrew heads Hebrew content
sub("""    bits.push('<div class="exlbl">Why it fits</div>');""",
    """    bits.push('<div class="exlbl heb" dir="rtl">למה זו התשובה</div>');""")
sub("""    bits.push('<div class="exlbl">Why the others don\\'t</div>');""",
    """    bits.push('<div class="exlbl heb" dir="rtl">למה האחרות לא</div>');""")

sub("""  out.push('<h3>Core services in this subject</h3>');""",
    """  out.push('<h3>Core services in this subject <span class="heb" dir="rtl">· '
           +'השירותים המרכזיים בנושא</span></h3>');""")
sub("""      '<th>Service</th><th>Primary benefit</th><th>Limitation</th><th>Cost model</th><th>Never choose when</th>'+""",
    """      '<th>Service</th><th>מה זה עושה</th><th>Limitation</th><th>Cost model</th><th>Never choose when</th>'+""")

# the two Hebrew labels need their own alignment; .exlbl is a plain small caption
sub(""".exwhy .exitem.ltr span{direction:ltr;text-align:left}""",
    """.exwhy .exitem.ltr span{direction:ltr;text-align:left}
.exlbl.heb{direction:rtl;unicode-bidi:isolate;text-align:right}
h3 .heb{direction:rtl;unicode-bidi:isolate;font-weight:500;opacity:.8}""")

PAGE.write_text(s, encoding="utf-8")
print("labels aligned with their content · page %.2f MB" % (len(s) / 1e6))
