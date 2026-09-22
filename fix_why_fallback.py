#!/usr/bin/env python3
"""Say something useful when the write-up names no letter.

477 options still get no line, and what the panel printed for them was "Wrong, but the
write-up does not single this one out" — which tells the reader nothing they can use on
the next question. The panel already knows what the option proposes (the glossary terms
in its text) and what the answer turns on (the terms in the correct option), so it can
state the contrast instead of apologising. That is the thing worth learning: not that D
is wrong, but that D proposes a queue where the question turns on a stream.

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


# the contrast needs the answer's own service, found once for the whole panel
sub("""    bits.push('<div class="exlbl">Why each answer</div>');
    const seenTerm=new Set();""",
"""    bits.push('<div class="exlbl">Why each answer</div>');
    const seenTerm=new Set();
    // What the answer actually turns on — used to say what an unnamed option is being
    // contrasted against, instead of just declaring it wrong.
    const pivot=(e.correctTerms[0]||{}).t||'';""")

sub("""        (line?'<i>'+esc(line)+'</i>'
             :'<i class="dim">'+(right?'The answer this question is testing.'
                                      :'Wrong, but the write-up does not single this one out.')+'</i>')+""",
"""        (line?'<i>'+esc(line)+'</i>'
             :'<i class="dim">'+esc(noLine(ltr,txt,right,pivot))+'</i>')+""")

# the fallback itself, next to the renderer that uses it
sub("""function renderExplain(q,picked,ok){""",
"""// The write-up does not name every option by letter. Rather than tell the reader an option
// is "not singled out", say what it proposes and what the answer turns on instead — the
// comparison is the transferable part, and both halves are already known here.
function noLine(ltr,txt,right,pivot){
  const mine=exFind(txt,4).map(t=>t.t).filter(t=>t.toLowerCase()!==pivot.toLowerCase());
  if(right) return pivot? 'This is the answer: the question turns on '+pivot+'.'
                        : 'This is the answer this question is testing.';
  if(mine.length&&pivot)
    return 'The write-up does not name this one. It proposes '+mine.slice(0,2).join(' and ')+
           ', where the question turns on '+pivot+' instead.';
  if(mine.length)
    return 'The write-up does not name this one. Judge it by what it proposes \\u2014 '+
           mine.slice(0,2).join(' and ')+' \\u2014 against what the question asks for.';
  if(pivot) return 'The write-up does not name this one. It does not give you '+pivot+
                   ', which is what the question turns on.';
  return 'The write-up does not single this one out \\u2014 compare it against the correct answer above.';
}
function renderExplain(q,picked,ok){""")

PAGE.write_text(s, encoding="utf-8")
print("unnamed options now carry the contrast · page %.2f MB" % (len(s) / 1e6))
