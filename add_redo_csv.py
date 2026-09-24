#!/usr/bin/env python3
"""CSV download from the Redo list.

Asked for: a CSV file download from the redo exams. The exam results screen already exported a
CSV, but only of the questions flagged or missed, and only for the exam just submitted. The
Redo list keeps up to thirty exams with every answer, so each card gets a ⬇ CSV button and the
list gets "⬇ All exams (CSV)".

One row per question: exam, question number, Right / Wrong / Unanswered, flagged, sector, the
question, options A-F, your answer, the correct answer, and the question's written explanation —
so the file stands on its own for study. Same writer as the other exports (UTF-8 with a BOM, so
Excel reads it), file named after the exam, its score and the date.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

# ---- the rows
sub("""function downloadCsv(name,text){""","""// ---------- CSV of a kept exam: every question, how it went, and why ----------
const HIST_CSV_HEAD=['Exam','#','Result','Flagged','Sector','Question','A','B','C','D','E','F',
                     'Your answer','Correct answer','Explanation'];
function histCsvLines(r){
  const exam=r.paper?'Exam '+(Number(r.paper)|0):'Mock exam';
  return (r.qs||[]).map((qi,i)=>{
    const q=QS[qi]; if(!q) return null;
    const byLtr={}; q.o.forEach(([l,t])=>{ byLtr[l]=t; });
    const mine=((r.ans||{})[i]||[]).slice().sort();
    const res=!mine.length?'Unanswered':(mine.length===q.a.length&&q.a.every(l=>mine.includes(l))?'Right':'Wrong');
    const cells=[exam,i+1,res,(r.flag||{})[i]?'Yes':'',SHORT[q.s]||SECTIONS[q.s]||'',q.q];
    ['A','B','C','D','E','F'].forEach(l=>cells.push(byLtr[l]||''));
    cells.push(mine.map(l=>l+') '+(byLtr[l]||'')).join('  |  '));
    cells.push(q.a.map(l=>l+') '+(byLtr[l]||'')).join('  |  '));
    cells.push(q.w||q.x||'');
    return cells.map(csvCell).join(',');
  }).filter(Boolean);
}
function histCsvName(r){
  return 'skyforge-'+(r.paper?'exam-'+(Number(r.paper)|0):'mock')+'-'+(Number(r.sc)||100)+'-'+
    String(r.d||dayKey()).replace(/[^0-9-]/g,'')+'.csv';
}
function histCsv(hid){
  const r=(P.examHist||{})[hid]; if(!r) return false;
  const lines=histCsvLines(r);
  const ok=lines.length&&downloadCsv(histCsvName(r),[HIST_CSV_HEAD.map(csvCell).join(','),...lines].join('\\r\\n'));
  toast(ok?'\\u2b07 '+(r.paper?'Exam '+(Number(r.paper)|0):'Mock exam')+' \\u2014 '+plural(lines.length,'question')+' exported':'Export blocked by the browser');
  return !!ok;
}
function histCsvAll(){
  const h=P.examHist||{};
  const ks=Object.keys(h).filter(k=>Array.isArray(h[k].qs)&&h[k].qs.every(i=>!!QS[i]))
    .sort((a,b)=>(Number(h[b].d0)||0)-(Number(h[a].d0)||0));
  if(!ks.length){ toast('No exams to export yet'); return false; }
  const lines=[]; ks.forEach(k=>lines.push(...histCsvLines(h[k])));
  const ok=downloadCsv('skyforge-all-exams-'+dayKey()+'.csv',[HIST_CSV_HEAD.map(csvCell).join(','),...lines].join('\\r\\n'));
  toast(ok?'\\u2b07 '+plural(ks.length,'exam')+' exported':'Export blocked by the browser');
  return !!ok;
}
function downloadCsv(name,text){""")

# ---- the buttons
sub("""    b.onclick=()=>live?(simSaved()&&simResume(),histCloudPull()):histOpen(k,b);
    card.appendChild(b); L.appendChild(card);""","""    b.onclick=()=>live?(simSaved()&&simResume(),histCloudPull()):histOpen(k,b);
    const c=document.createElement('button'); c.className='rdcsv';
    c.textContent='\\u2b07 CSV';
    c.setAttribute('aria-label','Download '+card.querySelector('.nm').textContent+' as a CSV file');
    c.onclick=()=>histCsv(k);
    const acts=document.createElement('div'); acts.className='rdacts';
    acts.appendChild(b); acts.appendChild(c);
    card.appendChild(acts); L.appendChild(card);""")
sub("""  $('redoEmpty').classList.toggle('hidden',!!ks.length);""","""  $('redoEmpty').classList.toggle('hidden',!!ks.length);
  $('redoCsvAll').classList.toggle('hidden',!ks.length);""")
sub("""    <div class="list" id="redoList"></div>
    <div class="rdempty hidden" id="redoEmpty">""","""    <div class="rdtools"><button class="btn ghost sm hidden" id="redoCsvAll">⬇ All exams (CSV)</button></div>
    <div class="list" id="redoList"></div>
    <div class="rdempty hidden" id="redoEmpty">""")
sub(""".rdcard .buy{flex:none}""",""".rdcard .buy{flex:none}
.rdacts{flex:none;display:flex;flex-direction:column;gap:6px;align-items:stretch}
.rdcsv{font-size:11.5px;font-weight:650;min-height:32px;padding:5px 10px;border-radius:9px;
  background:transparent;border:1px solid var(--line2);color:var(--dim)}
.rdcsv:hover{color:var(--txt);border-color:var(--cyan)}
.rdtools{display:flex;justify-content:flex-end;margin:2px 0 8px}
.rdtools .hidden{display:none}""")
sub("""$('simCsv').onclick=exportLastExam;""","""$('simCsv').onclick=exportLastExam;
$('redoCsvAll').onclick=()=>histCsvAll();""")
sub("""    qStory, hiQual, renderStory,""","""    histCsvLines, histCsvName, histCsv, histCsvAll, HIST_CSV_HEAD,
    qStory, hiQual, renderStory,""")
PAGE.write_text(s, encoding="utf-8"); print("Redo list: CSV per exam and for all")
