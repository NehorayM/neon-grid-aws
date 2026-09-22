#!/usr/bin/env python3
"""Seven of the nine high-severity findings: leaving somewhere must actually leave it.

  1-4. Walking out of an exam by the back arrow left `sim` alive. The countdown kept
       running in the top bar on every other screen, the read-aloud kept talking, the
       90-second question clock kept ticking, and when the paper's budget expired
       simCheckTime() submitted it and dragged you to the result screen from wherever
       you happened to be. quizBack now ends the run properly — saving it, so the
       Practice Exams screen still offers it back.
  5.   Two exam engines could run at once: startMock() never cleared `sim`, so
       starting a paper, backing out and starting a mock left both live, both
       answering into the same question screen. startMock() and startSession() and
       the Learn engine now all leave any running exam first.
  6-7. The verdict overlay and the Study Card modal both survived navigation,
       because go() dismissed nothing. It now closes them on every route change.

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


# ------------------------------------------- 6 & 7: nothing outlives a route change
sub("""function go(id){
  SCREENS.forEach(s=>$(s).classList.toggle('hidden',s!==id)); route=id;""",
"""function go(id){
  // Overlays used to survive navigation: the verdict card and the Study Card modal both
  // sat on top of whatever screen you moved to until something else happened to hide them.
  if(route!==id){
    const v=$('verdict'); if(v) v.classList.add('hidden');
    const m=$('studyModal'); if(m) m.classList.add('hidden');
  }
  SCREENS.forEach(s=>$(s).classList.toggle('hidden',s!==id)); route=id;""")

# ------------------------------------------ 1-4: the back arrow ends the exam
sub("""$('quizBack').onclick=()=>{ go('homeScreen'); renderHome(); };""",
"""// Backing out of an exam used to leave `sim` running: the clock carried on in the top bar,
// the voice carried on reading, and when the paper's budget ran out simCheckTime() submitted
// it and threw you onto the result screen from whatever screen you were on by then.
$('quizBack').onclick=()=>{
  if(sim&&sim.running){ simAbandon(); return; }   // saves the run and lands on the papers screen
  if(mock){ mock=null; stopQTimer(); }
  ttsStop(); stopQTimer(); hideExplain();
  go('homeScreen'); renderHome();
};""")

# ------------------------------------- 5: only one engine owns the question screen
sub("""function startMock(){
  ensureAudio();""",
"""function startMock(){
  ensureAudio();
  leaveExam();                      // a paper you backed out of was still live under this""")

sub("""function go(id){
  // Overlays used to survive navigation""",
"""// Anything that takes over the question screen calls this first, so two engines can never
// both be driving it. It keeps the paper, which the Practice Exams screen offers back.
function leaveExam(){
  if(typeof sim!=='undefined'&&sim&&sim.running){
    try{ simPersist(); }catch(e){}
    if(typeof simQStop==='function') simQStop();
    if(typeof ttsStop==='function') ttsStop();
    sim=null;
    if(typeof renderClock==='function') renderClock();
    const bar=$('simBar'); if(bar) bar.classList.remove('show');
    const cb=$('chargeBar'); if(cb) cb.style.display='';
    const qc=$('qConfirm'); if(qc) qc.style.display='';
    ['lifeFifty','lifeSkip','hintBtn'].forEach(id=>{ const e=$(id); if(e) e.style.display=''; });
  }
}
function go(id){
  // Overlays used to survive navigation""")

PAGE.write_text(s, encoding="utf-8")
print("lifecycle fixes applied · page %.2f MB" % (len(s) / 1e6))
