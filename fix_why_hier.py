#!/usr/bin/env python3
"""Split at the strongest separator first, then inside the pieces.

q226 is the question from the complaint. Its explanation reads:

  "Site-to-Site VPN uses IPsec, which encrypts at the network layer, and the tunnel also
   protects the session layer - Direct Connect (D) alone is private but not encrypted..."

The dash separates the case for the answer from the verdict on D. But the splitter offered
every separator at once, so the candidate pieces included ", which encrypts at the network
layer" — a lowercase continuation — and the guard against stranding continuations then
vetoed the whole split. The sentence stayed whole, went to D because D is the only letter in
it, and the correct answer was left with "Security groups and network ACLs then supply the
access controls."

Separators are not equal. A dash or a semicolon divides a sentence into clauses that stand
alone; a comma usually does not. So they are tried strongest first, and each accepted piece
is then offered the weaker ones. A comma failing inside one piece no longer prevents the
dash from doing its job.

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


start = s.index("  const split=p=>{")
end = s.index("  const parts=[];", start)
old = s[start:end]

new = '''  // Separators are not equal. A dash or a semicolon divides a sentence into clauses that
  // stand alone; a comma usually does not. Offering them all at once meant one bad comma
  // candidate vetoed a good dash split, so they are tried strongest first and each accepted
  // piece is then offered the weaker ones.
  const SEPS=[/\\s+(?:-|\\u2014)\\s+/, /;\\s+/, /,\\s+(?:and\\s+)?/];
  const tidy=list=>list.map((x,ix)=>{
    if(!ix) return x.trim();
    // a list item reads as a sentence once its conjunction is trimmed and it gets a capital
    const y=x.trim().replace(/^(?:and|but|or|while)\\s+/i,'');
    return y.charAt(0).toUpperCase()+y.slice(1);
  }).filter(Boolean);
  const splitAt=(p,si)=>{
    if(si>=SEPS.length) return [p];
    const raw=p.split(SEPS[si]).map(x=>x.trim()).filter(Boolean);
    if(raw.length<2) return splitAt(p,si+1);
    const pieces=tidy(raw);
    // "B, C, and D all still involve keys" is one clause with three subjects, not three
    // clauses. A piece too short to be a clause means the split landed inside a list.
    const tooShort=pieces.some(x=>x.split(/\\s+/).length<4);
    // A piece that starts lowercase continues the thought before it. Splitting there strands
    // "C is impossible for that reason" from the reason. A lowercase piece that NAMES an
    // option is a list item, though, not a continuation.
    const stranded=raw.slice(1).some(x=>/^[a-z]/.test(x)&&!names(x,p).length);
    const sets=pieces.map(x=>names(x,p));
    const distinct=new Set(); sets.forEach(a=>a.forEach(L=>distinct.add(L)));
    const key=a=>a.slice().sort().join('');
    const same=sets.every(a=>key(a)===key(sets[0]));
    // worth splitting only if the pieces do not all describe the same option(s)
    if(tooShort||stranded||same||distinct.size<2) return splitAt(p,si+1);
    const out=[];
    pieces.forEach(x=>{ splitAt(x,si+1).forEach(y=>out.push(y)); });
    return out;
  };
  const split=p=>splitAt(p,0);
'''
s = s[:start] + new + s[end:]
PAGE.write_text(s, encoding="utf-8")
print("strongest separator wins · page %.2f MB" % (len(s) / 1e6))
