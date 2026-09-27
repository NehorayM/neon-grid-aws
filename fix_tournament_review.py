#!/usr/bin/env python3
"""Casino tournament: what the four-lens review confirmed (16 of 17 findings, 11 distinct).

Server (supabase_tournament.sql)
  1. Starts raced past both limits. Ten tourney_start calls fired at once all read "none open,
     fewer than five today" before any had committed, and all ten went through — with the
     answers in the page, a scripted player wins ~94% of tournaments, so the pot could be farmed
     without limit. A start now takes the player's wallet row first (FOR UPDATE), so the next one
     waits and then sees the one just made; and a partial unique index allows one open
     tournament per player whatever happens.
  2. An answer could land on the next question. Lock in at 0:00, or twice quickly, was recorded
     against whichever question was open when it arrived — a question not yet seen. An answer now
     says which question it is for (qi) and is turned away if that is not the one open.
  3. The clock and the server disagreed by two seconds at 0:00 (the server only timed a question
     out at 122 s), so the page asked again and again. tourney_state times out at 120 s; the two
     seconds of grace stay on answers only, for the network.
  4. Leaving between rounds recorded the previous match's score as the conceded next match.
  5. A won tournament was booked one buy-in short in the lifetime stats and the casino log. Like
     the duel, nothing is booked at the start; a loss books the buy-in, a win books the net.
Page
  6. Coming back to the casino through the bottom bar left the Tourney clock frozen at whatever it
     showed when you left. Entering the casino with the Tourney tab up now fetches the state.
  7. Opening the tab was treated as a droppable background poll, so a tap during a roulette poll
     showed the lobby instead of the match. It waits now, like any tap.
  8. "Back to your tournament" repainted the view it had cached, clock and all. It fetches.
  9. A response still in flight when you left the tab restarted the clock out of sight, which then
     timed questions out in the background. The clock only runs while the tournament is on screen.
 10. At 0:00: one request, retried calmly (and after a failure) instead of a burst; a Lock in while
     an answer is on its way does nothing; a failed Lock in shows the button again.
 11. Errors went to the lobby's message line, which is hidden during a match. Each panel has its
     own. And "not installed — run supabase_tournament.sql" is said only when it is the
     tournament's own function that is missing; a missing duel function names the duel files.

Run once, after add_tournament.py; index.html and the SQL file are the source of truth afterwards.
"""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent

def patch(path, subs):
    p = ROOT / path; s = p.read_text(encoding="utf-8")
    for old, new in subs:
        assert s.count(old) == 1, (path, s.count(old), old[:100])
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")

# ============================================================================ SQL
patch("supabase_tournament.sql", [
("""create index if not exists tournaments_user_idx on public.tournaments (user_id, created_at desc);""",
"""create index if not exists tournaments_user_idx on public.tournaments (user_id, created_at desc);
-- one open tournament per player, whatever races past the checks
create unique index if not exists tournaments_one_active on public.tournaments (user_id) where status = 'active';"""),
# 1. starts wait in line
("""  w := public.wallet_row();
  -- one at a time: an open tournament comes back instead of a second""",
"""  w := public.wallet_row();
  -- Take the wallet row first. Starts fired at once all read "none open, fewer than five today"
  -- before any had committed; holding the row makes the next one wait and then see this one.
  select * into w from public.wallets where user_id = auth.uid() for update;
  -- one at a time: an open tournament comes back instead of a second"""),
# 5. nothing booked at the start
("""  update public.wallets set chips = chips - tourney_start.buyin,
         lifetime_lost = lifetime_lost + tourney_start.buyin, updated_at = now()
   where user_id = auth.uid();
  insert into public.casino_log (user_id, game, bet, delta, detail)
       values (auth.uid(), 'tourney', tourney_start.buyin, -tourney_start.buyin, jsonb_build_object('start', true));""",
"""  -- the buy-in leaves the wallet now; it is booked as won or lost when the tournament ends
  update public.wallets set chips = chips - tourney_start.buyin, updated_at = now()
   where user_id = auth.uid();"""),
("""  if not won then
    t.status := 'lost'; t.phase := 'between'; t.m_start := null;
    t := public.tourney_rest(t, 1, true);                          -- the bracket still finishes
    return t;
  end if;""","""  if not won then
    t.status := 'lost'; t.phase := 'between'; t.m_start := null;
    perform public.tourney_book_loss(t);
    t := public.tourney_rest(t, 1, true);                          -- the bracket still finishes
    return t;
  end if;"""),
("""-- After an answered (or timed-out) question: the next one, sudden death, or the end of the match.""",
"""-- a lost tournament: the buy-in is booked as lost, once
create or replace function public.tourney_book_loss(t public.tournaments)
returns void language sql security definer set search_path = public as $$
  update public.wallets set lifetime_lost = lifetime_lost + t.buyin, updated_at = now() where user_id = t.user_id;
  insert into public.casino_log (user_id, game, bet, delta, detail)
       values (t.user_id, 'tourney', t.buyin, -t.buyin, jsonb_build_object('lost', true, 'round', t.round));
$$;

-- After an answered (or timed-out) question: the next one, sudden death, or the end of the match."""),
# 3. the state times out at the clock's own 120 s
("""  if t.status = 'active' and t.phase = 'play' and t.m_start is not null
     and jsonb_array_length(t.m_log) < coalesce(array_length(t.m_q, 1), 0)
     and now() - t.m_start > ((public.tourney_seconds() + 2) || ' seconds')::interval then""",
"""  -- out of time at the clock's own two minutes: the page shows 0:00 then, and asks. (The two
  -- seconds of grace are for an answer already on its way, in tourney_answer.)
  if t.status = 'active' and t.phase = 'play' and t.m_start is not null
     and jsonb_array_length(t.m_log) < coalesce(array_length(t.m_q, 1), 0)
     and now() - t.m_start >= (public.tourney_seconds() || ' seconds')::interval then"""),
# 2. an answer names its question
("""create or replace function public.tourney_answer(tid uuid, picks text[])
returns jsonb language plpgsql security definer set search_path = public as $$
declare t public.tournaments; w public.wallets; i int; q int; correct text[]; ok boolean;
begin
  w := public.wallet_row();
  select * into t from public.tournaments where id = tid and user_id = auth.uid() for update;
  if t.id is null then return jsonb_build_object('ok', false, 'reason', 'no such tournament'); end if;
  i := jsonb_array_length(t.m_log);
  if t.status <> 'active' or t.phase <> 'play' or i >= coalesce(array_length(t.m_q, 1), 0) then
    return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips);
  end if;""",
"""-- The one-argument-less version is dropped rather than overloaded: PostgREST picks a function by
-- its argument names, and two candidates would make every call ambiguous.
drop function if exists public.tourney_answer(uuid, text[]);
create or replace function public.tourney_answer(tid uuid, picks text[], qi int default null)
returns jsonb language plpgsql security definer set search_path = public as $$
declare t public.tournaments; w public.wallets; i int; q int; correct text[]; ok boolean;
begin
  w := public.wallet_row();
  select * into t from public.tournaments where id = tid and user_id = auth.uid() for update;
  if t.id is null then return jsonb_build_object('ok', false, 'reason', 'no such tournament'); end if;
  i := jsonb_array_length(t.m_log);
  if t.status <> 'active' or t.phase <> 'play' or i >= coalesce(array_length(t.m_q, 1), 0) then
    return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips);
  end if;
  -- an answer is for the question it was given on: one that arrives after that question has
  -- closed (0:00, a second tap) must not become the answer to the next, unseen one
  if qi is not null and qi <> i then
    return jsonb_build_object('ok', true, 'stale', true, 't', public.tourney_view(t), 'chips', w.chips);
  end if;"""),
# 4 + 5. leaving: a clean 0–1 between rounds; the loss is booked
("""  if t.status = 'active' then
    you  := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'ok')::boolean);
    them := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'bot')::boolean);""",
"""  if t.status = 'active' then
    you  := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'ok')::boolean);
    them := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'bot')::boolean);
    -- between rounds m_log is the match already won, not the one being walked out of
    if t.phase = 'between' then you := 0; them := 0; end if;"""),
("""    t.status := 'lost'; t.phase := 'between'; t.m_start := null;
    t := public.tourney_rest(t, 1, true);
    perform public.tourney_save(t);""","""    t.status := 'lost'; t.phase := 'between'; t.m_start := null;
    perform public.tourney_book_loss(t);
    t := public.tourney_rest(t, 1, true);
    perform public.tourney_save(t);"""),
("""  foreach f in array array['tourney_start(bigint,int)','tourney_state(uuid)','tourney_answer(uuid,text[])',""",
"""  foreach f in array array['tourney_start(bigint,int)','tourney_state(uuid)','tourney_answer(uuid,text[],int)',"""),
("""                           'tourney_view(public.tournaments)','tourney_bot_answer()','tourney_botmatch()']""",
"""                           'tourney_view(public.tournaments)','tourney_bot_answer()','tourney_botmatch()',
                           'tourney_book_loss(public.tournaments)']"""),
])

# ============================================================================ page
patch("index.html", [
# 7. opening the tab waits like a tap
("""const CAS_POLLS=new Set(['roulette_table','duel_state','casino_state','bj_current','tourney_current']);""",
 """const CAS_POLLS=new Set(['roulette_table','duel_state','casino_state','bj_current']);"""),
# 11b. "missing" only when it is the function called
("""      if(/could not find the function|schema cache|does not exist/i.test(error.message||'')){
        if(opts&&opts.missingOk) return 'missing';
        tell('This part is not installed on your database yet — run '+rpcFile(fn)+' in the Supabase SQL editor.','bad');
      }""","""      if(/could not find the function|schema cache|does not exist/i.test(error.message||'')){
        // which function is missing: the one called, or one it depends on (a duel function
        // behind a tournament) — and so which file to run
        const m=/function public\\.(\\w+)/i.exec(error.message||''), gone=m?m[1]:fn;
        if(opts&&opts.missingOk&&gone===fn) return 'missing';
        tell('This part is not installed on your database yet — run '+rpcFile(gone)+' in the Supabase SQL editor.','bad');
      }"""),
# 6. entering the casino with the Tourney tab up fetches it
("""  renderDuelLobby();
  if(duelId||sbUser) duelResume();
};""","""  renderDuelLobby();
  if(duelId||sbUser) duelResume();
  // the Tourney tab stayed up while you were away, clock stopped: ask the server where it is now
  if(sbUser&&!$('casTour').classList.contains('hidden')&&typeof tourLoad==='function') tourLoad();
};"""),
# 11a. a message line on every panel
("""          <div class="ch-note" id="tourStatus" style="text-align:center;min-height:20px;margin-top:8px" aria-live="polite"></div>
          <button class="btn wide hidden" id="tourLock" style="margin-top:10px">Lock in</button>""",
"""          <div class="ch-note" id="tourStatus" style="text-align:center;min-height:20px;margin-top:8px" aria-live="polite"></div>
          <div class="authnote" id="tourPlayMsg"></div>
          <button class="btn wide hidden" id="tourLock" style="margin-top:10px">Lock in</button>"""),
("""          <div class="duelrecap" id="tourRecap"></div>
          <div class="duelacts">
            <button class="btn hidden" id="tourNext">Next round ▸</button>""",
"""          <div class="duelrecap" id="tourRecap"></div>
          <div class="authnote" id="tourBrMsg"></div>
          <div class="duelacts">
            <button class="btn hidden" id="tourNext">Next round ▸</button>"""),
("""function tourMsg(t,kind){ const e=$('tourMsg'); if(!e) return; e.textContent=t||''; e.className='authnote'+(kind?' '+kind:''); }""",
"""// every panel has its own message line: an error during a match went to the hidden lobby's
function tourMsg(t,kind){ ['tourMsg','tourPlayMsg','tourBrMsg'].forEach(id=>{ const e=$(id); if(!e) return;
  e.textContent=t||''; e.className='authnote'+(kind?' '+kind:''); }); }"""),
("""let tourBase=0, tourBaseLeft=0, tourKey='', tourMissingSQL=false;""",
"""let tourBase=0, tourBaseLeft=0, tourKey='', tourMissingSQL=false, tourAnswering=false, tourSyncT=null, tourSyncTries=0;"""),
("""function tourStop(){ if(tourTick){ clearInterval(tourTick); tourTick=null; } }""",
"""function tourStop(){ if(tourTick){ clearInterval(tourTick); tourTick=null; } if(tourSyncT){ clearTimeout(tourSyncT); tourSyncT=null; } }
const tourOnScreen=()=>route==='casinoScreen'&&!$('casTour').classList.contains('hidden');
// a different user (or nobody): nothing of the last one's tournament stays on screen
function tourReset(){ tourStop(); tourView=null; tourKey=''; tourAnswering=false; tourLeftToday=null; tourMsg('');
  tourShow('Lobby'); renderTourLobby(); }"""),
# 9. the clock runs only while the tournament is on screen
("""  tourBase=Date.now(); tourBaseLeft=Number(v.secondsLeft)||0;
  tourClock();
  tourTick=setInterval(tourClock,500);""","""  tourBase=Date.now(); tourBaseLeft=Number(v.secondsLeft)||0;
  // a response that lands after you left the tab must not start the clock out of sight
  if(!tourOnScreen()) return;
  tourClock();
  if(!tourTick&&tourView&&tourView.phase==='play') tourTick=setInterval(tourClock,500);"""),
# 10. at 0:00: one request, retried calmly
("""  if(left<=0){ tourStop(); tourSync(); }            // out of time: the server marks it and moves on
}
async function tourSync(){
  if(!tourView) return;
  const r=await casRpc('tourney_state',{tid:tourView.id},tourMsg);
  if(r&&r.ok&&r.t) tourPaint(r.t);
}""","""  if(!tourOnScreen()){ tourStop(); return; }
  if(left<=0){ tourStop(); tourSyncSoon(900); }     // out of time: ask the server once, it moves on
}
function tourSyncSoon(ms){
  if(tourSyncT) return;
  tourSyncT=setTimeout(()=>{ tourSyncT=null; tourSync(); },ms);
}
async function tourSync(){
  if(!tourView||tourAnswering) return;
  const key=tourView.id+':'+tourView.round+':'+tourView.i;
  const r=await casRpc('tourney_state',{tid:tourView.id},tourMsg);
  if(!(r&&r.ok&&r.t)){ if(tourOnScreen()&&tourSyncTries++<20) tourSyncSoon(2000); return; }
  const v=r.t, same=v.id+':'+v.round+':'+v.i===key;
  // still the same question at 0:00 (the clocks are a moment apart): ask again shortly, calmly
  if(same&&v.status==='active'&&v.phase==='play'&&!(Number(v.secondsLeft)>0)){
    tourView=v; if(tourOnScreen()&&tourSyncTries++<20) tourSyncSoon(1200); return; }
  tourSyncTries=0;
  tourPaint(v);
}"""),
# 2 + 10. an answer names its question; one at a time; a failure brings Lock back
("""async function tourLockIn(){
  if(!tourView||!tourPicked.size) return;
  $('tourLock').classList.add('hidden');
  const r=await casRpc('tourney_answer',{tid:tourView.id,picks:[...tourPicked]},tourMsg);
  if(r&&r.ok&&r.t){""","""async function tourLockIn(){
  if(!tourView||!tourPicked.size||tourAnswering) return;
  if(tourElapsedLeft()<=0) return;                  // 0:00: the question is closed
  tourAnswering=true;
  $('tourLock').classList.add('hidden');
  const q=QS[tourView.question], key=tourKey;
  let r=null;
  try{ r=await casRpc('tourney_answer',{tid:tourView.id,picks:[...tourPicked],qi:tourView.i},tourMsg); }
  finally{ tourAnswering=false; }
  if(!(r&&r.ok&&r.t)){
    // it did not go: the picks are still there, so is the way to send them
    if(key===tourKey&&q&&tourPicked.size===q.a.length&&tourElapsedLeft()>0) $('tourLock').classList.remove('hidden');
    return;
  }
  if(r&&r.ok&&r.t){"""),
("""        b.onclick=()=>{
          if(tourPicked.has(ltr)) tourPicked.delete(ltr);""","""        b.onclick=()=>{
          if(tourAnswering||tourElapsedLeft()<=0) return;       // on its way, or out of time
          if(tourPicked.has(ltr)) tourPicked.delete(ltr);"""),
# 8. Resume fetches
("""$('tourResume').onclick=()=>{ if(tourView) tourPaint(tourView); };""",
 """$('tourResume').onclick=()=>tourLoad();          // what the server has now, not what was cached"""),
# a leave that fails puts the clock back
("""  const r=await casRpc('tourney_leave',{tid:tourView.id},tourMsg);
  if(r&&r.ok&&r.t) tourPaint(r.t);
}""","""  const r=await casRpc('tourney_leave',{tid:tourView.id},tourMsg);
  if(r&&r.ok&&r.t) tourPaint(r.t); else tourSync();
}"""),
# a different user: reset
("""  sbUser=null; lastSync=0; myName=null;
  lbAuthChanged();""","""  sbUser=null; lastSync=0; myName=null;
  lbAuthChanged(); if(typeof tourReset==='function') tourReset();"""),
("""    if((sbUser?sbUser.id:null)!==before) lbAuthChanged();""",
 """    if((sbUser?sbUser.id:null)!==before){ lbAuthChanged(); if(typeof tourReset==='function') tourReset(); }"""),
("""    tourLoad, tourPaint, tourStart, tourLockIn, tourNext, tourQuit, tourSync, renderTourLobby, tourStop,""",
 """    tourLoad, tourPaint, tourStart, tourLockIn, tourNext, tourQuit, tourSync, renderTourLobby, tourStop, tourReset,
    get tourTick(){return tourTick;}, get tourAnswering(){return tourAnswering;},"""),
])
print("tournament review fixes: starts in line, answers name their question, clock, tab, accounting")
