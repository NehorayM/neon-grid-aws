#!/usr/bin/env python3
"""Tests for the SAA-C03 score, and the two checks that read the headline as a raw %.

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

sub("""  const pct=parseInt($('simScore').textContent,10);
  eq(pct, Math.round(expectRight/len*100), 'the score matches what was answered');
  ok($('simVerdict').textContent.indexOf('Exam '+n)===0,'the verdict names the exam');
  const rec=t.paperRec(n);
  ok(!!rec,'the paper result was stored');
  eq(rec.best,pct,'best score stored');""",
"""  // the headline is the SAA scaled score; the raw count and the weighted % sit beneath it
  const scaled=parseInt($('simScore').textContent,10);
  ok(scaled>=100&&scaled<=1000,'the score is on the exam\\u2019s 100\\u20131000 scale ('+scaled+')');
  const meta=$('simMeta').textContent;
  ok(meta.indexOf(expectRight+' / '+len+' correct')===0,'and the raw count matches what was answered');
  const pct=parseInt((/(\\d+)% weighted/.exec(meta)||[])[1],10);
  ok(pct>=0&&pct<=100,'the weighted percentage is shown');
  eq(/PASS/.test($('simVerdict').textContent)&&!/BELOW/.test($('simVerdict').textContent),scaled>=720,
     'pass and fail follow the 720 line');
  ok($('simVerdict').textContent.indexOf('Exam '+n)===0,'the verdict names the exam');
  const rec=t.paperRec(n);
  ok(!!rec,'the paper result was stored');
  eq(rec.best,pct,'best score stored');""")

sub("""  const pct=parseInt($('simScore').textContent,10);
  eq(pct,Math.round(before.right/65*100),'the final score matches the running tally');""",
"""  ok($('simMeta').textContent.indexOf(before.right+' / 65 correct')===0,'the final count matches the running tally');""")

sub("""async function saveFlushChecks(){""",
"""// Scored like SAA-C03 (official exam guide): 100–1000, pass at 720, four domains weighted
// 30/26/24/20, blanks wrong. Questions are filed by what they ask, not by their service.
async function saaChecks(){
  const t=T(), $=id=>document.getElementById(id);
  eq(t.saaScaled(0),100,'0% is 100, the bottom of the scale');
  eq(t.saaScaled(0.72),720,'72% is 720, the pass mark');
  eq(t.saaScaled(1),1000,'100% is 1000');
  ok(t.saaScaled(0.5)<t.saaScaled(0.6)&&t.saaScaled(0.6)<t.saaScaled(0.72),'and it only goes up');
  // the domain a question tests comes from what it asks
  const ask=(txt,s)=>t.examDomainOf({q:txt,s:s||7});
  eq(ask('A company stores logs in S3. Which solution meets these requirements MOST cost-effectively?'),3,
     'an S3 question asking for the cheapest option is a Cost question');
  eq(ask('The data must be encrypted at rest. Which solution will meet these requirements?'),0,'encryption is Secure');
  eq(ask('The application must be highly available across AZs. What should the architect do?'),1,'high availability is Resilient');
  eq(ask('Users report high latency. What should the architect do to improve performance?'),2,'latency is Performing');
  eq(ask('Which option is MOST cost-effectively? (Select TWO.)'),3,'a Select-TWO requirement line is still read');
  const mix=[0,0,0,0]; t.QS.forEach((q,i)=>mix[t.qDom(i)]++);
  ok(mix[3]/t.QS.length>0.08,'Cost is no longer 3% of the bank ('+Math.round(mix[3]/t.QS.length*100)+'%)');
  ok(mix[0]/t.QS.length>0.2,'nor Secure 11% ('+Math.round(mix[0]/t.QS.length*100)+'%)');
  // weighting: the exam's mix, not the paper's
  const byDom=[[],[],[],[]]; t.QS.forEach((q,i)=>byDom[t.qDom(i)].push(i));
  const all=(ok)=>[0,1,2,3].flatMap(d=>byDom[d].slice(0,10).map(qi=>({qi,ok})));
  eq(t.saaScore(all(true)).scaled,1000,'everything right is 1000');
  eq(t.saaScore(all(false)).scaled,100,'everything wrong is 100');
  // perfect on 40 Performing questions, wrong on 10 each of the rest: raw 57%, but Performing
  // is 24% of the exam, not 57%
  const skew=[...byDom[2].slice(0,40).map(qi=>({qi,ok:true})),
              ...[0,1,3].flatMap(d=>byDom[d].slice(0,10).map(qi=>({qi,ok:false})))];
  const S=t.saaScore(skew);
  eq(S.raw,57,'a paper heavy in one strong domain reads 57% raw');
  ok(S.pct<45,'but weighted by the exam\\u2019s mix it is far lower ('+S.pct+'%)');
  // two questions cannot swing a 20%-weight domain by a hundred points
  const base=[0,1,2].flatMap(d=>byDom[d].slice(0,20).map(qi=>({qi,ok:true})));
  const a=t.saaScore([...base,...byDom[3].slice(0,2).map(qi=>({qi,ok:true}))]).scaled;
  const b=t.saaScore([...base,...byDom[3].slice(0,2).map(qi=>({qi,ok:false}))]).scaled;
  ok(a-b<80,'two Cost questions move the score by '+(a-b)+', not by a hundred or more');
  // live on a teaching paper, hidden on an exam-conditions one
  delete t.P.lastPaper; t.simClearSave(); t.startPaper(5,'exam'); await sleep(30);
  ok(!$('simLive').classList.contains('hidden'),'a teaching paper shows the score so far');
  for(let k=0;k<4;k++){ t.simJump(k); await sleep(2); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  const live=parseInt($('simLiveVal').textContent,10);
  eq(live,t.saaScore(t.sim.qs.slice(0,4).map(qi=>({qi,ok:true}))).scaled,'and it is the SAA score of what has been answered');
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(12,'exam'); await sleep(30);
  ok($('simLive').classList.contains('hidden'),'an exam-conditions paper hides it until you submit');
  t.simAbandon(); await sleep(20); t.simClearSave();
  t.startPaper(12,'practice'); await sleep(30);
  ok(!$('simLive').classList.contains('hidden'),'practice shows it');
  t.simAbandon(); await sleep(20); t.simClearSave(); delete t.P.lastPaper;
}
async function saveFlushChecks(){""")

sub("await oneClockChecks(); await continueChecks();", "await oneClockChecks(); await continueChecks(); await saaChecks();")

QA.write_text(s, encoding="utf-8")
print("SAA checks added")
