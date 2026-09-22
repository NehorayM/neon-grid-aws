#!/usr/bin/env python3
"""Three defects the audit surfaced once the big ones were out of the way.

1. "A has the direction backwards The write-up does not single this one out" — when a short
   line is supplemented, the join had no full stop, and worse, the supplement claimed the
   write-up says nothing about an option it had just quoted. The supplement now reads as a
   continuation rather than as an apology, and only the standalone case says the write-up
   is silent.

2. 500 options are shown a line identical to another option's, nearly all of the form
   "CloudFront (A, D) caches content". It is true of both, but printing the same string
   twice reads as filler. leadFirst already reordered a letter list at the START of a line;
   it now reorders one anywhere, so D is told "CloudFront (D, A) caches content" and the
   line is about the option it sits under.

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


# --- 1. the supplement must not contradict the line it is supplementing -------------
sub("""function noLine(q,ltr,txt,right,pivot){""",
    """function noLine(q,ltr,txt,right,pivot,supp){""")

sub("""  if(mine.length&&pivot)
    return 'The write-up does not name this one. It proposes '+mine.slice(0,2).join(' and ')+
           ', where the question turns on '+pivot+' instead.';
  if(mine.length)
    return 'The write-up does not name this one. Judge it by what it proposes \\u2014 '+
           mine.slice(0,2).join(' and ')+' \\u2014 against what the question asks for.';
  if(pivot) return 'The write-up does not name this one. It does not give you '+pivot+
                   ', which is what the question turns on.';
  return 'The write-up does not single this one out \\u2014 compare it against the correct answer above.';""",
"""  // When there IS a line and this only fills it out, saying the write-up is silent
  // contradicts the sentence directly above it.
  const lead=supp?'':'The write-up does not name this one. ';
  if(mine.length&&pivot)
    return lead+'It proposes '+mine.slice(0,2).join(' and ')+
           ', where the question turns on '+pivot+' instead.';
  if(mine.length)
    return lead+'Judge it by what it proposes \\u2014 '+mine.slice(0,2).join(' and ')+
           ' \\u2014 against what the question asks for.';
  if(pivot) return lead+'It does not give you '+pivot+', which is what the question turns on.';
  return supp?'':'The write-up does not single this one out \\u2014 compare it against the correct answer above.';""")

sub("""  if(!line) return {text:noLine(q,ltr,txt,right,pivot),dim:true};
  if(line.length<THIN){
    const add=noLine(q,ltr,txt,right,pivot);
    if(add) return {text:line+' '+add,dim:false};
  }""",
"""  if(!line) return {text:noLine(q,ltr,txt,right,pivot,false),dim:true};
  if(line.length<THIN){
    const add=noLine(q,ltr,txt,right,pivot,true);
    // the source line does not always end in punctuation, and "backwards The write-up" is
    // what that looks like on screen
    if(add) return {text:line.replace(/[\\s,;]*$/,'').replace(/([^.!?])$/,'$1.')+' '+add,dim:false};
  }""")

# --- 2. reorder a letter list wherever it sits, not only at the start ----------------
sub("""  const leadFirst=(line,L)=>{
    const m=/^(Both\\s+|Options?\\s+)?([A-E])((?:\\s*,\\s*[A-E])*)(?:\\s*,?\\s+and\\s+([A-E]))?\\b/.exec(line);
    if(!m) return line;
    const all=[m[2]];
    (m[3]||'').split(',').forEach(x=>{ x=x.trim(); if(x) all.push(x); });
    if(m[4]) all.push(m[4]);
    if(all.length<2||all.indexOf(L)<0||all[0]===L) return line;
    const ord=[L].concat(all.filter(x=>x!==L));
    const head=(m[1]||'')+(ord.length>2
      ? ord.slice(0,-1).join(', ')+', and '+ord[ord.length-1]
      : ord[0]+' and '+ord[1]);
    return head+line.slice(m[0].length);
  };""",
"""  // "B and D require Lambda" is true under both, but under D it names B first. Put the
  // option being read at the front of the list — still plural, still true, and it now reads
  // as a line about D. The list is not always at the start: "CloudFront (A, D) caches
  // content" needs the same treatment, so the first list ANYWHERE in the line is reordered.
  const LIST=/(\\b[A-E])((?:\\s*,\\s*[A-E])*)(?:(\\s*,?\\s+and\\s+)([A-E]))?(?![A-Za-z])/g;
  const leadFirst=(line,L)=>{
    LIST.lastIndex=0;
    let m;
    while((m=LIST.exec(line))){
      const all=[m[1]];
      (m[2]||'').split(',').forEach(x=>{ x=x.trim(); if(x) all.push(x); });
      if(m[4]) all.push(m[4]);
      if(all.length<2) continue;              // a lone letter is not a list
      if(all.indexOf(L)<0||all[0]===L) return line;  // already leads, or not ours to reorder
      const ord=[L].concat(all.filter(x=>x!==L));
      const joined=ord.length>2
        ? ord.slice(0,-1).join(', ')+(m[3]||', and ')+ord[ord.length-1]
        : ord[0]+(m[3]||' and ')+ord[1];
      return line.slice(0,m.index)+joined+line.slice(m.index+m[0].length);
    }
    return line;
  };""")

PAGE.write_text(s, encoding="utf-8")
print("supplement reads as one sentence · page %.2f MB" % (len(s) / 1e6))
