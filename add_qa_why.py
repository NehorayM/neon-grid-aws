#!/usr/bin/env python3
"""Turn the explanation audit into standing assertions.

audit9 was a one-off measurement. Every defect it found is now a check that runs with the
suite, so the splitter cannot quietly regress: the article that was matching option A, the
"R&D" that was matching option D, the answer losing its own evidence to a distractor, and
the verdict lists that were handed whole to three options at once.

The thresholds are set just above where the bank sits now, so a regression trips them while
normal variation does not.

Run once; qa_bank.js is the source of truth afterwards.
"""
import pathlib

QA = pathlib.Path(__file__).resolve().parent / "qa_bank.js"
s = QA.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# leadFirst now puts the option being read at the front of a shared verdict
sub("""  ok(/B and D/.test(w.byLetter.B),'one naming two goes to both');
  eq(w.byLetter.B,w.byLetter.D,'the same line, against each of them');""",
"""  ok(/B and D/.test(w.byLetter.B),'one naming two goes to both');
  eq(w.byLetter.D,'D and B require Lambda to poll the logs.',
     'and each is named first in its own copy, so the line is about the option it sits under');""")

sub("""function whyChecks(){""",
"""// Every defect the ninth audit measured, as a standing check. These are the ways the
// splitter went wrong, and each one was live in the bank before it was found.
function whyQualityChecks(){
  const t=T();
  const L4=['A','B','C','D'];

  // "A gp3 volume tops out at 16,000 IOPS" opens with an article. Matched as option A, it
  // took the case for the answer away from the answer.
  const art=t.whyByOption(
    'A gp3 volume tops out at 16,000 IOPS, so the workload has hit a ceiling. '+
    'io2 supports up to 64,000 IOPS.',L4,['D'],
    [['A','Magnetic volume'],['B','RDS storage'],['C','gp3 volume'],['D','io2 volume']]);
  ok(!art.byLetter.A,'a capitalised article is not option A');
  ok(/tops out/.test(art.byLetter.D||''),'so the answer keeps the case for itself');
  // but a real reference to A in the same shape still counts
  const ref=t.whyByOption('A controls console access, and B is a network path.',L4,['C']);
  ok(/controls console access/.test(ref.byLetter.A||''),'a real reference to A still counts');

  // "the R&D account" is not option D
  const amp=t.whyByOption(
    'An account can belong to one organization, so the R&D account must leave it first. '+
    'D means rebuilding every resource.',L4,['B']);
  ok(!/R&D account must leave/.test(amp.byLetter.D||''),'"R&D" is not option D');
  ok(/R&D account must leave/.test(amp.byLetter.B||''),'that sentence stays with the answer');

  // a verdict list keyed on service names, not letters, is split per option
  const list=t.whyByOption(
    'C cannot push gp3 past its limit, RDS does not let you stripe two volumes (B), '+
    'and magnetic (A) is far slower.',L4,['D'],
    [['A','Magnetic'],['B','RDS'],['C','gp3'],['D','io2']]);
  ok(list.byLetter.A!==list.byLetter.B,'each option gets its own verdict, not the whole list');
  ok(/magnetic/i.test(list.byLetter.A||''),'A is told about magnetic');
  ok(/stripe/.test(list.byLetter.B||''),'B is told about striping');

  // an enumeration of subjects is one clause, not three
  const enu=t.whyByOption('B, C, and D all still involve keys to maintain.',L4,['A']);
  ok((enu.byLetter.B||'').split(/\\s+/).length>4,'"B, C, and D all ..." is not split into "B, C"');

  // a clause that continues the thought before it keeps its antecedent
  const anaph=t.whyByOption(
    'An account belongs to one organization at a time, so it must leave the old one; '+
    'C is impossible for that reason.',L4,['A']);
  ok(!/^C is impossible/.test(anaph.byLetter.A||''),'the reason is not stranded from its clause');

  // two clauses joined against one option read as two sentences
  const join=t.whyByOption('C cannot push gp3 past its limit, and C is also slower.',L4,['D']);
  ok(!/limit and/.test(join.byLetter.C||''),'joined clauses are punctuated, not run together');

  // and across the whole bank, measured the way the panel shows it
  let misled=0,dupe=0,blank=0,thin=0,ocr=0,opts=0;
  const lead=(txt)=>{
    let best=null,at=1e9;
    const other=L4.some(L=>L!=='A'&&new RegExp('(^|[\\\\s("\\\\[])'+L+'(?=[ ,.;:)]|$)').test(txt));
    const artA=/^A\\s+[a-z]/.test(txt)&&!other;
    L4.forEach(L=>{
      if(L==='A'&&artA) return;
      const m=new RegExp('(^|[\\\\s("\\\\[])'+L+'(?=[ ,.;:)]|$)').exec(txt);
      if(m&&m.index<at){ at=m.index; best=L; }
    });
    return best;
  };
  t.QS.forEach(q=>{
    if(!q.w) return;
    const letters=q.o.map(x=>x[0]);
    const w=t.whyByOption(q.w,letters,q.a,q.o);
    const ctxt=q.o.filter(x=>q.a.includes(x[0])).map(x=>x[1]).join(' ');
    const pk=(t.exFind(ctxt,3)[0]||{}).t||'';
    const pivot=pk?t.asWritten(ctxt,pk):'';
    const seen={};
    q.o.forEach(([L,txt])=>{
      opts++;
      const line=w.byLetter[L]||'';
      if(!line) blank++;
      const dup=letters.filter(o=>(w.byLetter[o]||'')&&w.byLetter[o]===line).length>1;
      const shown=(t.optionLine(q,L,txt,line,pivot,dup)||{}).text||'';
      if(!shown) thin++;
      if(seen[shown]) dupe++; else seen[shown]=1;
      if(line){ const l=lead(line); if(l&&l!==L&&line.indexOf(L)<0) misled++; }
      if(/\\b[a-z]{2,}\\.\\s+[a-z]/.test(txt)) ocr++;
    });
  });
  ok(thin===0,'every option in the bank is shown something ('+opts+' options)');
  ok(misled<120,'few lines open by discussing a different option ('+misled+')');
  ok(dupe<450,'few options are shown a line identical to another\\'s ('+dupe+')');
  ok(blank<200,'most options get a line from the write-up itself ('+blank+' without)');
  ok(ocr<20,'the OCR damage in the option text is repaired ('+ocr+' left)');
}
function whyChecks(){""")

sub("  if(opts.extras!==false){ whyChecks();",
    "  if(opts.extras!==false){ whyChecks(); whyQualityChecks();")

QA.write_text(s, encoding="utf-8")
print("explanation quality is a standing check now")
