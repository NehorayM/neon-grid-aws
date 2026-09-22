#!/usr/bin/env python3
"""Split the verdict lists that key on service names rather than on letters.

q7 ends "C cannot push gp3 past its limit, RDS does not let you stripe two volumes (B), and
magnetic (A) is far slower." That is three verdicts, one per option, but only the first
begins with a letter, so the comma rule did not fire and all three options were handed the
whole sentence — the same string three times, and under A it opened by discussing C.

So a plain comma is a candidate split point too. The existing guards keep it honest: pieces
must name different options, must be long enough to be clauses, and a piece that starts
lowercase is still a continuation — UNLESS it names an option, which makes it a list item
("and magnetic (A) is far slower"). Those get their conjunction trimmed and a capital, so
they read as sentences rather than as tails.

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


sub("|;\\s+|,\\s+and\\s+(?=[A-Z])|,\\s+(?=[A-E]\\s+[a-z])/)",
    "|;\\s+|,\\s+(?:and\\s+)?/)")

sub("""    // A piece that starts lowercase continues the thought before it — "so the R&D account
    // must first leave the old organization". Splitting there files the conclusion under one
    // option and strands "C is impossible for that reason" under another.
    if(pieces.slice(1).some(x=>/^[a-z]/.test(x))) return [p];""",
"""    // A piece that starts lowercase continues the thought before it — "so the R&D account
    // must first leave the old organization". Splitting there files the conclusion under one
    // option and strands "C is impossible for that reason" under another. But a lowercase
    // piece that NAMES an option is a list item, not a continuation: "and magnetic (A) is
    // far slower" is A's verdict and belongs to A.
    if(pieces.slice(1).some(x=>/^[a-z]/.test(x)&&!names(x,p).length)) return [p];""")

sub("""    const sets=pieces.map(x=>names(x,p));""",
"""    // a list item reads as a sentence once its conjunction is trimmed and it gets a capital
    pieces=pieces.map((x,ix)=>{
      if(!ix) return x;
      const y=x.replace(/^(?:and|but|or|while)\\s+/i,'');
      return y.charAt(0).toUpperCase()+y.slice(1);
    });
    const sets=pieces.map(x=>names(x,p));""")

sub("""    const pieces=p.split(""", """    let pieces=p.split(""")

PAGE.write_text(s, encoding="utf-8")
print("verdict lists split by service name too · page %.2f MB" % (len(s) / 1e6))
