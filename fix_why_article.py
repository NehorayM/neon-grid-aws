#!/usr/bin/env python3
"""The letter match was case-insensitive, so the article "a" was option A.

Tracing q4 showed option A being handed the entire write-up, including the sentences about
B, C and D. The cause: the regex that decides which options a sentence names carried an 'i'
flag, so the English article in "C and D use a single AZ" matched option A. Every sentence
in the bank containing the word "a" was filed under A — stealing other options' reasoning
when A was a distractor, and bloating A's line when A was the answer.

Option letters are written uppercase in these write-ups, so the bare letter is now matched
case-sensitively. "option a" in lower case still counts, because there the word "option"
disambiguates it.

Also: "B, C, and D all still involve keys" was being split into "B, C" and "D all still
involve keys" — the comma rule could not tell a list of subjects from a list of clauses. A
split is now rejected unless every piece has enough words to be a clause.

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


# the article bug: no 'i' flag on the bare letter; "option a" still matches either case
sub("""  const names=p=>{
    const got=[];
    letters.forEach(L=>{
      const re=new RegExp('(^|[^A-Za-z])(?:option\\\\s+)?'+L+
        "(?=['\\u2019]s\\\\b|[ ,.;:)]|$)",'i');
      if(re.test(p)) got.push(L);
    });
    return got;
  };""",
"""  const names=p=>{
    const got=[];
    letters.forEach(L=>{
      // Case-sensitive on purpose. With 'i', the article in "use a single AZ" matched option
      // A, and every sentence containing the word "a" was filed under A.
      const tail="(?=['\\u2019]s\\\\b|[ ,.;:)]|$)";
      const bare=new RegExp('(^|[^A-Za-z])'+L+tail);
      const named=new RegExp('(^|[^A-Za-z])[Oo]ptions?\\\\s+'+L+tail,'i');
      if(bare.test(p)||named.test(p)) got.push(L);
    });
    return got;
  };""")

# a split is only a split if both sides are clauses, not a list of subjects
sub("""    if(pieces.length<2) return [p];
    const sets=pieces.map(names);""",
"""    if(pieces.length<2) return [p];
    // "B, C, and D all still involve keys" is one clause with three subjects, not three
    // clauses. A piece too short to be a clause means the split point was inside a list.
    if(pieces.some(x=>x.split(/\\s+/).length<4)) return [p];
    const sets=pieces.map(names);""")

PAGE.write_text(s, encoding="utf-8")
print("the article is no longer option A · page %.2f MB" % (len(s) / 1e6))
