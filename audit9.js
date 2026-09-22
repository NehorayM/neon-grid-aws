// Ninth pass: are the explanations any GOOD? Not "is there text" — is what each option
// gets actually about that option, and does the right answer get the case for itself.
(function(){
const found=[]; const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const t=window.__t;

// the services named by exactly one option — a line mentioning one of these is about that
// option whether or not it uses the letter
function exclusiveKeys(q,L){
  const keyOf=t=>{
    const set=new Set();
    (String(t).match(/\b(?:Amazon|AWS)\s+[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)?|\b[A-Z][A-Za-z0-9]{3,}(?:\s+[A-Z][A-Za-z0-9]+)?/g)||[])
      .forEach(x=>{ const k=x.replace(/^(?:Amazon|AWS)\s+/,'').trim().toLowerCase();
                    if(k.length>3) set.add(k); });
    return set;
  };
  const per={}, count={};
  q.o.forEach(([ltr,txt])=>{ per[ltr]=keyOf(txt); per[ltr].forEach(k=>{count[k]=(count[k]||0)+1;}); });
  return Array.from(per[L]||[]).filter(k=>count[k]===1);
}
// the service the answer turns on — the panel contrasts an unnamed option against this
function pivotOf(q){
  const t=window.__t, correct=q.o.filter(x=>q.a.includes(x[0])).map(x=>x[1]).join(' ');
  const terms=t.exFind?t.exFind(correct,3):[];
  return (terms[0]||{}).t||'';
}
function leadLetter(txt,letters){
  // which option does this line talk about FIRST? A line filed under A that opens by
  // discussing B is worse than no line at all.
  let best=null,at=1e9;
  // "A gp3 volume tops out at 16,000 IOPS" opens with an article, not with option A. Judge
  // it the way whyByOption does, or the audit reports a defect the splitter does not have.
  const other=letters.some(L=>L!=='A'&&
    new RegExp('(^|[\\s("\u2018\u201c\\[])'+L+"(?=['\u2019]s\\b|[ ,.;:)]|$)").test(txt));
  const nx=/^A\s+([A-Za-z][A-Za-z0-9-]*)/.exec(txt);
  const verby=nx&&(/s$/i.test(nx[1])||/^(cannot|can|could|will|would|should|must|may|might|do|did|only|still|never|also|again|both|alone|then|just|simply|merely)$/i.test(nx[1]));
  const articleA=!!nx&&!verby&&!other;
  letters.forEach(L=>{
    if(L==='A'&&articleA) return;
    const re=new RegExp('(^|[\\s("‘“\\[])'+L+"(?=['\\u2019]s\\b|[ ,.;:)]|$)");
    const m=re.exec(txt);
    if(m&&m.index<at){ at=m.index; best=L; }
  });
  return best;
}

window.AUDIT9=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface'); return {total:1,found}; }
  const stats={q:0,opts:0,blank:0,dupe:0,misled:0,frag:0,rightThin:0,ocr:0,
               shownBlank:0,shownGeneric:0};
  const examples={};
  const keep=(k,ev)=>{ if(!examples[k]) examples[k]=ev; };

  for(let i=0;i<t.QS.length;i++){
    const q=t.QS[i]; if(!q.w) continue;
    stats.q++;
    const letters=q.o.map(x=>x[0]);
    const w=t.whyByOption(q.w,letters,q.a,q.o);
    const seen={};
    letters.forEach(L=>{
      stats.opts++;
      const line=w.byLetter[L]||'';
      if(!line){ stats.blank++; return; }
      // the same sentence handed to two options reads as filler
      const dupLine=letters.filter(o=>(w.byLetter[o]||'')&&w.byLetter[o]===line).length>1;
      const asShown=(t.optionLine(q,L,q.o.find(x=>x[0]===L)[1],line,pivotOf(q),dupLine)||{}).text||line;
      if(seen[asShown]){ stats.dupe++; keep('dupe','q'+i+' '+seen[asShown]+'+'+L+': '+asShown.slice(0,80)); }
      seen[asShown]=L;
      // A line filed under L that opens by talking about a different option. But a line that
      // discusses L by NAME rather than by letter ("Aurora with a read replica...") is about
      // L and is fine, so it only counts when the line never identifies L at all.
      const lead=leadLetter(line,letters);
      const namesMe=new RegExp('(^|[\\s("‘“\\[])'+L+
        "(?=['\u2019]s\\b|[ ,.;:)]|$)").test(line)
        || exclusiveKeys(q,L).some(k=>line.toLowerCase().indexOf(k)>=0);
      if(lead&&lead!==L&&!namesMe){
        stats.misled++; keep('misled','q'+i+' '+L+' opens about '+lead+': '+line.slice(0,90));
      }
      // A fragment: starting mid-thought, or so short it cannot be a reason. Short-but-whole
      // ("B and A delete nothing.") is a fine reason, so length alone does not count.
      if(/^(then|and|so|but|which|while|because)\b/i.test(line)||/^[a-z]/.test(line)||line.length<22){
        stats.frag++; keep('frag','q'+i+' '+L+': '+line);
      }
    });
    // What the reader is actually shown, which is the attributed line supplemented where it
    // is too thin. Measuring byLetter alone measured an intermediate the panel never prints.
    q.o.forEach(([L,txt])=>{
      const dup=letters.filter(o=>(w.byLetter[o]||'')&&w.byLetter[o]===w.byLetter[L]).length>1;
      const shown=(t.optionLine(q,L,txt,w.byLetter[L]||'',pivotOf(q),dup)||{}).text||'';
      if(!shown){ stats.shownBlank++; keep('shownBlank','q'+i+' '+L); return; }
      if(/compare it against the correct answer above/.test(shown)){
        stats.shownGeneric++; keep('shownGeneric','q'+i+' '+L+': '+shown.slice(0,70));
      }
      if(q.a.includes(L)&&shown.length<60){
        stats.rightThin++; keep('rightThin','q'+i+' '+L+': '+shown);
      }
    });
    // and the option text itself has to be readable
    q.o.forEach(([L,txt])=>{
      if(/\b[a-z]{1,3}\.\s+[a-z]/.test(txt)||/\s[a-z]\.\s/.test(txt)){
        stats.ocr++; keep('ocr','q'+i+' '+L+': '+txt.slice(0,90));
      }
    });
  }

  const pc=n=>Math.round(n/Math.max(1,stats.opts)*100)+'%';
  if(stats.misled) F('HIGH','explain',stats.misled+' option lines ('+pc(stats.misled)+
    ') open by discussing a different option',examples.misled);
  if(stats.dupe) F('MED','explain',stats.dupe+' option lines ('+pc(stats.dupe)+
    ') are a copy of another option\'s line',examples.dupe);
  if(stats.frag) F('MED','explain',stats.frag+' option lines ('+pc(stats.frag)+
    ') are fragments or start mid-thought',examples.frag);
  if(stats.rightThin) F('HIGH','explain',stats.rightThin+' of '+stats.q+
    ' correct answers are SHOWN less than a sentence',examples.rightThin);
  if(stats.shownBlank) F('HIGH','explain',stats.shownBlank+
    ' options are shown nothing at all',examples.shownBlank);
  if(stats.shownGeneric) F('MED','explain',stats.shownGeneric+' options ('+pc(stats.shownGeneric)+
    ') fall all the way through to the generic line',examples.shownGeneric);
  if(stats.blank) F('LOW','explain',stats.blank+' option lines ('+pc(stats.blank)+
    ') get nothing from the write-up itself (the panel supplements these)');
  if(stats.ocr) F('MED','bank',stats.ocr+' option texts still carry OCR damage',examples.ocr);

  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT9:',found.length,by,stats);
  return {total:found.length,by,found,stats};
};
console.log('AUDIT9 ready');
})();
