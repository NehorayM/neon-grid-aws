// Eighth pass: the nine mini-games, which nothing has ever driven.
(function(){
const found=[]; const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const $=id=>document.getElementById(id);
const t=window.__t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const scr=()=>{const e=document.querySelector('.screen:not(.hidden)');return e?e.id:'(none)';};

async function playOne(g){
  const id=g.id, nm=g.nm||id;
  // launching
  try{ t.launchGame(id); }catch(e){ F('HIGH','game',nm+' will not launch',e.message); return; }
  await sleep(30);
  if(scr()!=='gameScreen'){ F('HIGH','game',nm+' did not open the game screen',scr()); }
  if(!t.gRunning){ F('MED','game',nm+' launched but is not running'); }

  // run it for a while, in steps, watching for anything impossible
  let bad=null;
  for(let i=0;i<120;i++){
    try{ t.gStep(1/30); }catch(e){ bad=e.message; break; }
    const s=t.gScore;
    if(!isFinite(s)){ F('HIGH','game',nm+' score became '+s); break; }
    if(s<0){ F('MED','game',nm+' score went negative',String(s)); break; }
    const fill=$('gtimer');
    if(fill){
      const w=parseFloat(fill.style.width);
      if(isFinite(w)&&(w>100.5||w<-0.5)){ F('MED','game',nm+' timer bar out of range',fill.style.width); break; }
    }
    if(!t.gRunning) break;         // it finished on its own, which is fine
  }
  if(bad) F('HIGH','game',nm+' throws while running',bad);

  // ending
  try{ t.endGame(); }catch(e){ F('HIGH','game',nm+' throws on end',e.message); }
  await sleep(40);
  if(t.gRunning) F('HIGH','game',nm+' is still running after endGame()');
  if(scr()==='gameScreen') F('MED','game',nm+' left you on the game screen after it ended',scr());
  // the score it recorded has to be a number
  const hi=(t.P.highs||{})[id];
  if(hi!==undefined&&(!isFinite(hi)||hi<0)) F('HIGH','game',nm+' wrote an impossible high score',String(hi));
  t.go('homeScreen'); await sleep(15);
}

async function games(){
  if(!t.GAMES||typeof t.launchGame!=='function'||typeof t.gStep!=='function'){
    F('HIGH','harness','the games are not exposed — this probe would do nothing'); return; }
  const keep=JSON.parse(JSON.stringify(t.P.highs||{}));
  for(const g of t.GAMES) await playOne(g);
  t.P.highs=keep;
}

// launching one game straight after another must not leave the first running
async function backToBack(){
  if(!t.GAMES||t.GAMES.length<2) return;
  try{
    t.launchGame(t.GAMES[0].id); await sleep(20);
    t.launchGame(t.GAMES[1].id); await sleep(20);
    for(let i=0;i<20;i++) t.gStep(1/30);
    if(!isFinite(t.gScore)) F('HIGH','game','starting a second game corrupts the score',String(t.gScore));
    t.endGame(); await sleep(30);
    if(t.gRunning) F('HIGH','game','a game survives starting another and ending it');
  }catch(e){ F('HIGH','game','starting one game after another throws',e.message); }
  t.go('homeScreen'); await sleep(15);
}

// a game must not survive being navigated away from
async function leaveMidGame(){
  if(!t.GAMES) return;
  try{
    t.launchGame(t.GAMES[0].id); await sleep(20);
    t.go('homeScreen'); await sleep(30);
    if(t.gRunning) F('HIGH','game','a game keeps running after you leave its screen');
  }catch(e){ F('MED','game','leaving a game throws',e.message); }
  try{ t.endGame(); }catch(e){}
  t.go('homeScreen'); await sleep(15);
}

window.AUDIT8=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface'); return {total:1,found}; }
  await games();
  await backToBack();
  await leaveMidGame();
  t.go('homeScreen');
  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT8:',found.length,by);
  return {total:found.length,by,found};
};
console.log('AUDIT8 ready');
})();
