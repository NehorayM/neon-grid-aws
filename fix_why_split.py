#!/usr/bin/env python3
"""Attribute clauses, not whole sentences.

audit9.js measures the explanations rather than counting them, and the numbers
matched the complaint:

    1,922 option lines (40%)  open by discussing a DIFFERENT option
    1,241 lines      (26%)  are a copy of another option's line
      451 of 1,177 correct answers get less than a sentence of their own

All three are one mistake. These write-ups pack two options into one sentence —
"Transit Gateway (B) is not itself a connection to on premises, and A controls
console access rather than network traffic" — and attributing the whole sentence
put B's half under A and A's half under B. The same sentence then appeared under
both, and where a sentence explained the right answer before naming a loser
("Site-to-Site VPN uses IPsec ... - Direct Connect (D) alone is private but not
encrypted"), the case FOR the answer went to D and the correct option was left
with whatever fragment remained.

So a sentence is now split at its clause joins — semicolon, dash, ", and " — but
**only when the halves name different options**. Splitting that does not improve
attribution is not done, because it only makes fragments.

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


sub("""  // split on sentence ends, keeping short clauses joined to what they qualify
  const parts=String(text).split(/(?<=[.;])\\s+/).filter(Boolean);
  parts.forEach(p=>{""",
"""  const names=p=>{
    const got=[];
    letters.forEach(L=>{
      const re=new RegExp('(^|[^A-Za-z])(?:option\\\\s+)?'+L+
        "(?=['\\u2019]s\\\\b|[ ,.;:)]|$)",'i');
      if(re.test(p)) got.push(L);
    });
    return got;
  };
  // These write-ups routinely pack two options into one sentence — "Transit Gateway (B) is not
  // a connection to on premises, and A controls console access". Taking the sentence whole put
  // B's half under A and A's under B. Split at the clause joins, but ONLY where the halves talk
  // about different options: splitting that does not improve attribution just makes fragments.
  const split=p=>{
    const pieces=p.split(/\\s+(?:-|\\u2014)\\s+|;\\s+|,\\s+and\\s+(?=[A-Z])/).map(x=>x.trim()).filter(Boolean);
    if(pieces.length<2) return [p];
    const sets=pieces.map(names);
    const distinct=new Set();
    sets.forEach(a=>a.forEach(L=>distinct.add(L)));
    // worth splitting only if the pieces do not all describe the same option(s)
    const key=a=>a.slice().sort().join('');
    const same=sets.every(a=>key(a)===key(sets[0]));
    if(same||distinct.size<2) return [p];
    return pieces;
  };
  const parts=[];
  String(text).split(/(?<=[.;])\\s+/).filter(Boolean).forEach(sent=>{
    split(sent).forEach(x=>parts.push(x));
  });
  parts.forEach(p=>{""")

# the per-clause naming now reuses the helper
sub("""    // which letters does this sentence talk about? "A adds", "Option B's", "B and D require"
    const named=[];
    letters.forEach(L=>{
      const re=new RegExp('(^|[^A-Za-z])(?:option\\\\s+)?'+L+
        "(?=['\\u2019]s\\\\b|[ ,.;:)]|$)",'i');
      if(re.test(p)) named.push(L);
    });""",
"""    const named=names(p);""")

PAGE.write_text(s, encoding="utf-8")
print("clauses are attributed now, not sentences · page %.2f MB" % (len(s) / 1e6))
