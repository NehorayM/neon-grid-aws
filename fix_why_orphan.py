#!/usr/bin/env python3
"""Stop the splitter orphaning back-references, and keep a comma list a comma list.

q68 showed the cost of splitting too eagerly. "An AWS account can belong to only one
organization at a time, so the R&D account must first leave the old organization" was cut
at the comma, and option C was left holding "C is impossible for that reason" — with the
reason itself filed under another option. A clause that starts lowercase is a continuation,
not a statement about an option, so a split that produces one is refused. The splits that
mattered survive it: "…, and A controls console access" starts uppercase, and so does
"- Direct Connect (D) alone is private but not encrypted".

Also, reordering "CloudFront (A, D)" for option D produced "(D and A)" because the rejoin
always used "and". A list written with commas stays written with commas.

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


sub("""    if(pieces.some(x=>x.split(/\\s+/).length<4)) return [p];""",
"""    if(pieces.some(x=>x.split(/\\s+/).length<4)) return [p];
    // A piece that starts lowercase continues the thought before it — "so the R&D account
    // must first leave the old organization". Splitting there files the conclusion under one
    // option and strands "C is impossible for that reason" under another.
    if(pieces.slice(1).some(x=>/^[a-z]/.test(x))) return [p];""")

sub("""      const joined=ord.length>2
        ? ord.slice(0,-1).join(', ')+(m[3]||', and ')+ord[ord.length-1]
        : ord[0]+(m[3]||' and ')+ord[1];""",
"""      // "(A, D)" rejoined with "and" became "(D and A)" — keep whichever form was written
      const tail=m[3]||(m[2]?', ':' and ');
      const joined=ord.length>2
        ? ord.slice(0,-1).join(', ')+(m[3]?m[3]:', ')+ord[ord.length-1]
        : ord[0]+tail+ord[1];""")

PAGE.write_text(s, encoding="utf-8")
print("back-references stay with their reason · page %.2f MB" % (len(s) / 1e6))
