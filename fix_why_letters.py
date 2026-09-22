#!/usr/bin/env python3
"""Two more things that are not option letters: "R&D" and a sentence-initial article.

q68's explanation opens "An AWS account ... so the R&D account must first leave the old
organization". The D in "R&D" was matched as option D, so the case for the correct answer
was filed under a distractor. Requiring the letter to be preceded by whitespace, an opening
bracket or a quote fixes that whole class: "(B)", ", D" and "B and D" all still match,
"R&D" and "A/B" no longer do.

q7 opens "A gp3 volume tops out at 16,000 IOPS" — a capitalised article at the start of a
sentence, matched as option A, which is why the correct answer was left holding only "io2
supports up to 64,000 IOPS." An option reference and an article look identical in isolation
("A controls console access" versus "A gp3 volume tops out"), so the decision is made from
the whole sentence: these write-ups list their verdicts together ("C is impossible..., A has
the direction backwards, and D means..."), so a leading A with no other option letter
anywhere in the sentence is the article.

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


sub("""  const names=p=>{
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
  };""",
"""  // Case-sensitive on purpose. With 'i', the article in "use a single AZ" matched option A,
  // and every sentence containing the word "a" was filed under A. The lead-in is restricted
  // to whitespace or an opening bracket so that "R&D", "A/B" and "gp3-D" are not letters.
  const TAIL="(?=['\\u2019]s\\\\b|[ ,.;:)]|$)";
  const bareRe=L=>new RegExp('(^|[\\\\s("\\u2018\\u201c\\\\[])'+L+TAIL);
  const namedRe=L=>new RegExp('(^|[^A-Za-z])[Oo]ptions?\\\\s+'+L+TAIL,'i');
  const names=(p,ctx)=>{
    const got=[];
    // "A gp3 volume tops out at 16,000 IOPS" opens with an article, not with option A. The
    // two are identical in isolation, so the sentence decides: these write-ups group their
    // verdicts ("C is impossible..., A has the direction backwards, and D means..."), so a
    // leading A with no other option letter in the sentence is the article.
    const scope=ctx||p;
    const articleA=/^A\\s+[a-z]/.test(scope)&&
      !letters.some(L=>L!=='A'&&(bareRe(L).test(scope)||namedRe(L).test(scope)));
    letters.forEach(L=>{
      if(L==='A'&&articleA){
        // still count A if it is referenced somewhere other than that opening word
        if(namedRe('A').test(p)||bareRe('A').test(p.replace(/^A\\b/,' '))) got.push('A');
        return;
      }
      if(bareRe(L).test(p)||namedRe(L).test(p)) got.push(L);
    });
    return got;
  };""")

# the clause splitter and the attribution loop both judge a piece in its sentence's context
sub("""    const sets=pieces.map(names);""",
    """    const sets=pieces.map(x=>names(x,p));""")

sub("""  const parts=[];
  String(text).split(/(?<=[.;])\\s+/).filter(Boolean).forEach(sent=>{
    split(sent).forEach(x=>parts.push(x));
  });
  parts.forEach(p=>{
    const named=names(p);""",
"""  const parts=[];
  String(text).split(/(?<=[.;])\\s+/).filter(Boolean).forEach(sent=>{
    split(sent).forEach(x=>parts.push([x,sent]));
  });
  parts.forEach(pair=>{
    const p=pair[0], named=names(p,pair[1]);""")

PAGE.write_text(s, encoding="utf-8")
print("R&D and the article are not options · page %.2f MB" % (len(s) / 1e6))
