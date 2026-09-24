#!/usr/bin/env python3
"""Explanations that talk about the question that was just asked.

Asked for (in Hebrew): more explanation text, things that actually relate to what happened in
the question. The written explanation for each question is specific — "requests run up to 20
minutes, which exceeds Lambda's 15-minute limit" — but the panel cut it into per-option lines,
padded them with generic filler, and printed the part that explains the answer itself (the
sentences that name no single option) at the very bottom, under the glossary.

A "What happened in this question" block now opens the explanation, built only from the
question itself:

  - The situation: the problem sentence, quoted from the stem.
  - What they asked for: the requirement sentence(s), with LEAST/MOST and the other deciding
    qualifiers in bold.
  - Why <answer> is the answer: the write-up's sentences about the answer, and the ones about no
    single option — in one paragraph, first.
  - Why your pick is not it: when you missed, the write-up's own sentence about the option you
    chose; on a multi-answer question, which ones you had and which you missed.

Measured over the bank: 1,165 of the 1,177 written-up questions have a specific answer paragraph
this way; 3,480 of 3,531 wrong options have a sentence of their own. The verified note (q.x),
where there is one, joins the block. The rest of the panel is unchanged, minus the remainder
paragraph at the bottom, which is now in the block — each thing is still said once.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

sub("""function renderExplain(q,picked,ok,timedOut){""",
"""// ---------- what happened in this question ----------
// The question's own words: the problem it describes and what it asks for. Nothing here is
// generic — every line is quoted from the stem or from the question's written explanation.
function qStory(q){
  const S=(String(q.q||'').replace(/\\s+/g,' ').match(/[^.?!]+(?:[.?!]+|$)/g)||[]).map(x=>x.trim()).filter(x=>x.length>3);
  const askRe=/\\b(wants?|needs?|must|requires?|requirements?|which (solution|combination|option|approach|actions?|steps?|strategy|design|architecture|services?|configuration|method)|what should|how should|should the (solutions architect|company)|MOST|LEAST)\\b/;
  const probRe=/\\b(reported|errors?|fail(s|ed|ure|ing)?|slow(er|ly)?|latency|too many|exceed(s|ed|ing)?|cannot|can't|unable|spikes?|outages?|downtime|bottleneck|throttl\\w*|time ?outs?|degrad\\w*|overload\\w*|increas(e|ed|es|ing)|grow(s|ing|th)?|expensive|costs? (are|have|has)|manual(ly)?|compliance|lost|loss|unpredictable|intermittent|sensitive)\\b/i;
  const ask=[];
  for(let i=S.length-1;i>=0&&ask.length<2;i--){
    if(askRe.test(S[i])) ask.unshift(S[i]); else if(ask.length) break;
  }
  const prob=S.find(x=>probRe.test(x)&&!ask.includes(x))||'';
  return {prob, ask};
}
// the words that decide between four plausible answers, in bold (input is already escaped)
function hiQual(s){
  return String(s).replace(/\\b((?:MOST|LEAST) [\\w-]+(?: [\\w-]+)?|cost[- ]effective(?:ly)?|operational overhead|highly available|high availability|fault[- ]toleran\\w+|lowest latency|minimal (?:changes|effort|downtime|cost)|least amount of \\w+|without [\\w-]+(?: [\\w-]+)?|in real time|near-real-time|serverless|durab\\w+|encrypt\\w*|automatically|scal(?:e|es|able|ing))\\b/g,'<b>$1</b>');
}
function renderStory(q,e,picked,ok){
  const st=qStory(q), rows=[];
  const ansL=e.correct.map(x=>x[0]).join(' + ');
  if(st.prob) rows.push(['The situation',hiQual(esc(st.prob))]);
  if(st.ask.length) rows.push(['What they asked for',hiQual(esc(st.ask.join(' ')))]);
  const right=q.a.map(l=>e.why.byLetter[l]).filter(Boolean);
  const lead=[...new Set([...right,e.why.rest||''])].join(' ').replace(/\\s+/g,' ').trim();
  if(lead) rows.push(['Why '+ansL+' is the answer',esc(lead)]);
  else if(e.full) rows.push(['Why '+ansL+' is the answer',esc(e.full)]);
  if(e.note) rows.push(['Worth knowing',esc(e.note)]);
  if(!ok&&picked&&picked.size){
    const wrong=[...picked].filter(l=>!q.a.includes(l));
    const missed=q.a.filter(l=>!picked.has(l));
    wrong.forEach(l=>{
      const o=q.o.find(x=>x[0]===l)||[l,''];
      let line=e.why.byLetter[l]||'';
      if(!line){ try{ line=optionLine(q,l,o[1],'',((e.correctTerms[0]||{}).t||''),false).text; }catch(err){} }
      rows.push(['Why '+l+' — your pick — is not it',esc(line||('It does not do what the question asks for: '+o[1]))]);
    });
    if(q.a.length>1&&missed.length&&missed.length<q.a.length)
      rows.push(['Half of it',esc('You had '+q.a.filter(l=>picked.has(l)).join(' + ')+' right; the answer also needs '+missed.join(' + ')+'.')]);
  }
  if(!rows.length) return '';
  return '<div class="exstory"><div class="exstoryh">\\u{1f50e} What happened in this question</div>'+
    rows.map(([k,v])=>'<div class="exsrow"><div class="exsk">'+k+'</div><div class="exsv">'+v+'</div></div>').join('')+'</div>';
}
function renderExplain(q,picked,ok,timedOut){""")

# the block opens the panel, and the verified note moves into it
sub("""  // the note written while this question's answer was verified beats anything derived
  if(e.note) bits.push('<div class="exnote"><b>Why</b> '+esc(e.note)+'</div>');""",
"""  // what happened in this question, in its own words — the note written while the answer was
  // verified is part of it now
  { const story=renderStory(q,e,picked instanceof Set?picked:new Set(picked||[]),ok);
    if(story) bits.push(story);
    else if(e.note) bits.push('<div class="exnote"><b>Why</b> '+esc(e.note)+'</div>'); }""")
# the remainder paragraph is in the block now: said once
sub("""    if(e.why.rest) bits.push('<div class="exnote exrest">'+esc(e.why.rest)+'</div>');""",
"""    // the remainder (the sentences about no single option) opens the panel now, in the story""")

sub(""".exnote{font-size:12.8px;line-height:1.62;color:#d3d9e2}""",
""".exnote{font-size:12.8px;line-height:1.62;color:#d3d9e2}
/* what happened in this question: the stem's own problem and ask, then why, then your pick */
.exstory{margin:12px 0 4px;border:1px solid var(--line);border-radius:12px;background:var(--surface);padding:11px 13px 5px}
.exstoryh{font-size:12.5px;font-weight:650;color:var(--dim);margin-bottom:6px}
.exsrow{padding:8px 0;border-top:1px solid var(--line)}
.exsrow:first-of-type{border-top:0}
.exsk{font-family:var(--mono);font-size:10.5px;letter-spacing:.5px;text-transform:uppercase;color:var(--cyan);margin-bottom:4px}
.exsv{font-size:13.5px;line-height:1.68;color:#e2e8f0;direction:ltr;unicode-bidi:isolate;text-align:left}
.exsv b{color:var(--gold);font-weight:650}""")

sub("""    VOICE_PRESETS, voicePreset,""","""    qStory, hiQual, renderStory,
    VOICE_PRESETS, voicePreset,""")
PAGE.write_text(s, encoding="utf-8"); print("explanation opens with what happened in this question")

# ---- second pass: said once — the list points up to the story; the pick row is the full line
s = PAGE.read_text(encoding="utf-8")
sub("""    wrong.forEach(l=>{
      const o=q.o.find(x=>x[0]===l)||[l,''];
      let line=e.why.byLetter[l]||'';
      if(!line){ try{ line=optionLine(q,l,o[1],'',((e.correctTerms[0]||{}).t||''),false).text; }catch(err){} }
      rows.push(['Why '+l+' — your pick — is not it',esc(line||('It does not do what the question asks for: '+o[1]))]);
    });""","""    const pk=(e.correctTerms[0]||{}).t||'';
    const pivot=pk?asWritten(e.correct.map(x=>x[1]).join(' '),pk):'';
    wrong.forEach(l=>{
      const o=q.o.find(x=>x[0]===l)||[l,''];
      let line='';
      try{ line=optionLine(q,l,o[1],e.why.byLetter[l]||'',pivot,false).text; }catch(err){ line=e.why.byLetter[l]||''; }
      rows.push(['Why '+l+' — your pick — is not it',esc(line||('It does not do what the question asks for: '+o[1]))]);
      renderStory.saidPick.add(l);
    });""")
sub("""function renderStory(q,e,picked,ok){
  const st=qStory(q), rows=[];""","""function renderStory(q,e,picked,ok){
  const st=qStory(q), rows=[];
  renderStory.saidLead=false; renderStory.saidPick=new Set();   // what the list below need not repeat""")
sub("""  if(lead) rows.push(['Why '+ansL+' is the answer',esc(lead)]);
  else if(e.full) rows.push(['Why '+ansL+' is the answer',esc(e.full)]);""",
"""  if(lead){ rows.push(['Why '+ansL+' is the answer',esc(lead)]); renderStory.saidLead=true; }
  else if(e.full) rows.push(['Why '+ansL+' is the answer',esc(e.full)]);""")
sub("""  if(!rows.length) return '';
  return '<div class="exstory">""","""  if(!rows.length){ renderStory.saidLead=false; renderStory.saidPick=new Set(); return ''; }
  return '<div class="exstory">""")
sub("""        (function(){ const s=optionLine(q,ltr,txt,line,pivot,lineCount[line]>1);
          return '<i'+(s.dim?' class="dim"':'')+'>'+esc(s.text)+'</i>'; })()+""",
"""        (function(){
          // the story above already said why the answer is right and why the pick is wrong
          if(right&&renderStory.saidLead) return '<i class="dim exup">\\u2191 Why this is the answer is above.</i>';
          if(!right&&renderStory.saidPick&&renderStory.saidPick.has(ltr)) return '<i class="dim exup">\\u2191 Why your pick is not it is above.</i>';
          const s=optionLine(q,ltr,txt,line,pivot,lineCount[line]>1);
          return '<i'+(s.dim?' class="dim"':'')+'>'+esc(s.text)+'</i>'; })()+""")
PAGE.write_text(s, encoding="utf-8"); print("said once: the list points up to the story")

# ---- third pass: an option the write-up covers by name of service, not by letter ----
# "both Lambda options fail on duration" is about A and D, but names neither letter, so both got
# "The write-up does not name this one". Find the write-up's sentence about what the option
# proposes — a service it names that the answer does not — and use that.
s = PAGE.read_text(encoding="utf-8")
sub("""function optionLine(q,ltr,txt,line,pivot,shared){
  const right=q.a.includes(ltr);""","""function optionLine(q,ltr,txt,line,pivot,shared){
  const right=q.a.includes(ltr);
  if(!line&&!right&&q.w){
    const corr=q.a.map(l=>(q.o.find(o=>o[0]===l)||['',''])[1]).join(' ').toLowerCase();
    const terms=exFind(txt,4).map(t=>String(t.t)).filter(t=>t&&corr.indexOf(t.toLowerCase())<0);
    if(terms.length){
      const sents=(String(q.w).match(/[^.!?]+(?:[.!?]+|$)/g)||[]).map(x=>x.trim()).filter(Boolean);
      const hit=sents.filter(x=>terms.some(t=>x.toLowerCase().indexOf(t.toLowerCase())>=0));
      if(hit.length) line=hit.slice(0,2).join(' ');
    }
  }""")
PAGE.write_text(s, encoding="utf-8"); print("options covered by service name get their sentence")

# ---- fourth pass: the situation includes the numbers that decide it ----
# Q700's deciding fact is "Processing time for each request varies from 5 minutes to 20
# minutes" (Lambda stops at 15) — no problem word in it, so the situation missed it. Sentences
# with a hard number and unit count too, up to two, in the order the question gives them.
s = PAGE.read_text(encoding="utf-8")
sub("""  const prob=S.find(x=>probRe.test(x)&&!ask.includes(x))||'';
  return {prob, ask};""","""  const numRe=/\\b\\d[\\d,.]*\\s?(ms|milliseconds?|seconds?|minutes?|hours?|days?|weeks?|months?|years?|[KMGTP]B|[KMGTP]iB|%|percent|IOPS|requests|users|transactions|messages|instances|Mbps|Gbps)\\b/i;
  const prob=S.filter(x=>(probRe.test(x)||numRe.test(x))&&!ask.includes(x)).slice(0,2).join(' ');
  return {prob, ask};""")
PAGE.write_text(s, encoding="utf-8"); print("situation keeps the deciding numbers")

# ---- fifth pass: requirements anywhere in the stem; every question gets a situation ----
# Q900's requirements ("must be available ... within several minutes", "must be immediately
# accessible") sit in the middle, and the ask stopped at the first sentence that was not one, so
# it showed only "Which solution will meet these requirements?". Two thirds of the bank had no
# situation line at all.
s = PAGE.read_text(encoding="utf-8")
sub("""  const ask=[];
  for(let i=S.length-1;i>=0&&ask.length<2;i--){
    if(askRe.test(S[i])) ask.unshift(S[i]); else if(ask.length) break;
  }
  const numRe=""","""  // the question itself is the last sentence (or two: "... (Select TWO.)"); the requirements are
  // every must/needs/requires/wants sentence before it, wherever they sit — the last three
  const reqRe=/\\b(wants?|needs?|must|requires?|required|should|has to|have to)\\b/i;
  let qi=S.length-1;
  while(qi>0&&/^\\(?select (two|three)/i.test(S[qi])) qi--;
  const tail=S.slice(qi);
  const reqs=S.slice(0,qi).filter(x=>reqRe.test(x)).slice(-3);
  const ask=[...reqs,...tail].filter(x=>!/^\\(?select (two|three)/i.test(x));
  const numRe=""")
sub("""  const prob=S.filter(x=>(probRe.test(x)||numRe.test(x))&&!ask.includes(x)).slice(0,2).join(' ');
  return {prob, ask};""","""  let prob=S.filter(x=>(probRe.test(x)||numRe.test(x))&&!ask.includes(x)).slice(0,2).join(' ');
  // nothing went wrong in it and no numbers: the setup is the situation
  if(!prob) prob=S.find(x=>!ask.includes(x))||'';
  return {prob, ask};""")
PAGE.write_text(s, encoding="utf-8"); print("requirements from anywhere; a situation for every question")

# ---- sixth pass: the requirements as a list, one per line ----
s = PAGE.read_text(encoding="utf-8")
sub("""  if(st.ask.length) rows.push(['What they asked for',hiQual(esc(st.ask.join(' ')))]);""",
"""  if(st.ask.length) rows.push(['What they asked for',st.ask.map(x=>'<div class="exsask">'+hiQual(esc(x))+'</div>').join('')]);""")
sub(""".exsv b{color:var(--gold);font-weight:650}""",""".exsv b{color:var(--gold);font-weight:650}
.exsask{position:relative;padding-left:15px}
.exsask+.exsask{margin-top:4px}
.exsask::before{content:'\\2192';position:absolute;left:0;color:var(--dim)}""")
PAGE.write_text(s, encoding="utf-8"); print("requirements listed")

# ---- seventh pass: bold marks what is asked for, not the background ----
s = PAGE.read_text(encoding="utf-8")
sub("""  if(st.prob) rows.push(['The situation',hiQual(esc(st.prob))]);""",
"""  if(st.prob) rows.push(['The situation',esc(st.prob)]);""")
PAGE.write_text(s, encoding="utf-8"); print("bold only in the ask")

# ---- eighth pass: nothing to tell without a question ----
s = PAGE.read_text(encoding="utf-8")
sub("""function renderStory(q,e,picked,ok){
  const st=qStory(q), rows=[];""","""function renderStory(q,e,picked,ok){
  if(!q||!e||!Array.isArray(q.a)){ renderStory.saidLead=false; renderStory.saidPick=new Set(); return ''; }
  const st=qStory(q), rows=[];""")
PAGE.write_text(s, encoding="utf-8"); print("renderStory guards a missing question")
