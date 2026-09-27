-- ============================================================================
--  Skyforge — Casino tournament: you and seven bots, three knockout rounds
--  Run after supabase_casino.sql, supabase_duel.sql and supabase_duel_v2.sql. Safe to re-run.
--
--  Eight seats: you and seven bots with people's names. Quarter-final, semi-final, final. Each
--  match is five practice-exam questions, two minutes each; more right answers wins, a tie
--  goes to sudden-death questions. Bots answer at human-looking moments and are right about
--  two times in three. Win the final and the pot is yours: eight times the buy-in.
--
--  Everything that decides chips happens here, not in the browser: which questions, whether an
--  answer is right (the duel's answer key), the clock, the bots' answers and the payout. The
--  browser is told a bot's answer only after it has answered that question itself.
--
--  The bots' seven buy-ins are the house's, so a win makes chips. Starts are held to five a day
--  to keep that from being farmed.
-- ============================================================================

create table if not exists public.tournaments (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users (id) on delete cascade,
  buyin      bigint not null check (buyin > 0),
  exam       int not null default 0,                      -- 0 = any exam
  status     text not null default 'active',              -- active | won | lost
  phase      text not null default 'play',                -- play | between (after a won round)
  round      int  not null default 1,                     -- 1 quarter-final, 2 semi-final, 3 final
  players    jsonb not null,                              -- 8 seats [{name, bot}]; seat 0 is you
  alive      int[] not null default '{0,1,2,3,4,5,6,7}',  -- seats still in, in bracket order
  results    jsonb not null default '[]'::jsonb,          -- every match: {round, a, b, sa, sb, w}
  used       int[] not null default '{}',                 -- questions already asked
  opp        int,                                         -- seat you are playing now
  m_q        int[] not null default '{}',                 -- this match's questions
  m_bot      jsonb not null default '[]'::jsonb,          -- per question {ok, t}: secret until you answer it
  m_log      jsonb not null default '[]'::jsonb,          -- per answered question {q, ans, pick, ok, bot}
  m_start    timestamptz,                                 -- when the question in play opened
  payout     bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists tournaments_user_idx on public.tournaments (user_id, created_at desc);
-- one open tournament per player, whatever races past the checks
create unique index if not exists tournaments_one_active on public.tournaments (user_id) where status = 'active';
alter table public.tournaments enable row level security;
-- No policies on purpose: the bots' answers are in the row, so only the functions below read it.

-- ---------------------------------------------------------------- constants
create or replace function public.tourney_seconds() returns int language sql immutable as $$ select 120; $$;
create or replace function public.tourney_daily() returns int language sql immutable as $$ select 5; $$;

-- A bot's answer to one question: right about two times in three, at a moment a person might
-- answer — mostly half a minute to a minute and a half in, now and then quick, now and then
-- close to the wire.
create or replace function public.tourney_bot_answer()
returns jsonb language plpgsql volatile as $$
declare r float := random(); t int;
begin
  t := case when r < 0.15 then 8 + floor(random() * 15)::int
            when r < 0.85 then 25 + floor(random() * 65)::int
            else 90 + floor(random() * 25)::int end;
  return jsonb_build_object('ok', random() < 2.0/3.0, 't', t);
end $$;

-- n questions from the exam (or any), none asked before in this tournament
create or replace function public.tourney_pick(ex int, used int[], n int)
returns int[] language plpgsql security definer set search_path = public as $$
declare ids int[];
begin
  select array_agg(k) into ids from (
    select key::int as k from jsonb_object_keys((select ans from public.answer_key where id = 1)) as key
     where (ex = 0 or key::int between (ex - 1) * public.duel_exam_len() and ex * public.duel_exam_len() - 1)
       and not (key::int = any(coalesce(used, '{}')))
     order by random() limit n) s;
  if coalesce(array_length(ids, 1), 0) < n and ex <> 0 then
    return public.tourney_pick(0, used, n);             -- an exam run dry: any exam
  end if;
  return ids;
end $$;

-- two bots play a match: five questions each at two in three, sudden death on a tie
create or replace function public.tourney_botmatch()
returns int[] language plpgsql volatile as $$
declare sa int := 0; sb int := 0; k int;
begin
  for k in 1..5 loop
    if random() < 2.0/3.0 then sa := sa + 1; end if;
    if random() < 2.0/3.0 then sb := sb + 1; end if;
  end loop;
  while sa = sb loop
    if random() < 2.0/3.0 then sa := sa + 1; end if;
    if random() < 2.0/3.0 then sb := sb + 1; end if;
  end loop;
  return array[sa, sb];
end $$;

-- ---------------------------------------------------------------- the view the browser gets
create or replace function public.tourney_view(t public.tournaments)
returns jsonb language plpgsql stable set search_path = public as $$
declare i int; n int; el int; b jsonb; w public.wallets;
begin
  if t.id is null then return null; end if;
  i := jsonb_array_length(t.m_log);
  n := coalesce(array_length(t.m_q, 1), 0);
  el := case when t.m_start is null then 0 else floor(extract(epoch from (now() - t.m_start)))::int end;
  b := case when t.status = 'active' and t.phase = 'play' and i < n then t.m_bot -> i else null end;
  select * into w from public.wallets where user_id = t.user_id;
  return jsonb_build_object(
    'id', t.id, 'status', t.status, 'phase', t.phase, 'round', t.round, 'buyin', t.buyin,
    'pot', t.buyin * 8, 'payout', t.payout, 'exam', t.exam,
    'players', (select jsonb_agg(p -> 'name' order by n2) from jsonb_array_elements(t.players) with ordinality as x(p, n2)),
    'alive', to_jsonb(t.alive), 'results', t.results, 'opp', t.opp,
    'question', case when b is not null then to_jsonb(t.m_q[i + 1]) else null end,
    'i', i, 'n', n,
    'secondsTotal', public.tourney_seconds(),
    'secondsLeft', case when b is not null then greatest(0, public.tourney_seconds() - el) else null end,
    -- when the bot will have answered the question in play — not whether it is right
    'oppAt', case when b is not null then (b ->> 't')::int else null end,
    'you', (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'ok')::boolean),
    'them', (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'bot')::boolean),
    'log', t.m_log,
    'chips', coalesce(w.chips, 0));
end $$;

-- ---------------------------------------------------------------- bracket bookkeeping
-- Play every other match of the round, then (if you are out) every round after, so the
-- bracket always ends with a champion.
create or replace function public.tourney_rest(t public.tournaments, from_pair int, to_end boolean)
returns public.tournaments language plpgsql security definer set search_path = public as $$
declare k int; a int; b int; sc int[]; nxt int[]; res jsonb := t.results; al int[] := t.alive; rd int := t.round;
begin
  loop
    nxt := '{}';
    for k in 0 .. (coalesce(array_length(al, 1), 0) / 2) - 1 loop
      a := al[k * 2 + 1]; b := al[k * 2 + 2];
      if k < from_pair then
        -- already played (yours): its winner is recorded last for this round
        nxt := nxt || (select (e ->> 'w')::int from jsonb_array_elements(res) e
                        where (e ->> 'round')::int = rd and ((e ->> 'a')::int = a or (e ->> 'b')::int = a)
                        order by 1 limit 1);
      else
        sc := public.tourney_botmatch();
        res := res || jsonb_build_array(jsonb_build_object('round', rd, 'a', a, 'b', b, 'sa', sc[1], 'sb', sc[2],
                                                           'w', case when sc[1] > sc[2] then a else b end));
        nxt := nxt || case when sc[1] > sc[2] then a else b end;
      end if;
    end loop;
    al := nxt;
    exit when not to_end or coalesce(array_length(al, 1), 0) <= 1;
    rd := rd + 1; from_pair := 0;
  end loop;
  t.results := res; t.alive := al;
  return t;
end $$;

-- a new match against t.opp: five questions, the bot's five answers
create or replace function public.tourney_new_match(t public.tournaments)
returns public.tournaments language plpgsql security definer set search_path = public as $$
declare qs int[]; bots jsonb := '[]'::jsonb; k int;
begin
  qs := public.tourney_pick(t.exam, t.used, 5);
  for k in 1..coalesce(array_length(qs, 1), 0) loop bots := bots || jsonb_build_array(public.tourney_bot_answer()); end loop;
  t.m_q := qs; t.m_bot := bots; t.m_log := '[]'::jsonb; t.used := t.used || qs;
  t.m_start := now(); t.phase := 'play';
  return t;
end $$;

-- a lost tournament: the buy-in is booked as lost, once
create or replace function public.tourney_book_loss(t public.tournaments)
returns void language sql security definer set search_path = public as $$
  update public.wallets set lifetime_lost = lifetime_lost + t.buyin, updated_at = now() where user_id = t.user_id;
  insert into public.casino_log (user_id, game, bet, delta, detail)
       values (t.user_id, 'tourney', t.buyin, -t.buyin, jsonb_build_object('lost', true, 'round', t.round));
$$;

-- After an answered (or timed-out) question: the next one, sudden death, or the end of the match.
create or replace function public.tourney_after(t public.tournaments)
returns public.tournaments language plpgsql security definer set search_path = public as $$
declare i int; n int; you int; them int; extra int[]; won boolean;
begin
  i := jsonb_array_length(t.m_log); n := coalesce(array_length(t.m_q, 1), 0);
  if i < n then t.m_start := now(); return t; end if;
  you  := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'ok')::boolean);
  them := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'bot')::boolean);
  if you = them and n < 8 then                                   -- sudden death: one more each
    extra := public.tourney_pick(t.exam, t.used, 1);
    t.m_q := t.m_q || extra; t.used := t.used || extra;
    t.m_bot := t.m_bot || jsonb_build_array(public.tourney_bot_answer());
    t.m_start := now();
    return t;
  end if;
  won := case when you = them then random() < 0.5 else you > them end;   -- still level after 3: a coin
  t.results := t.results || jsonb_build_array(jsonb_build_object('round', t.round, 'a', 0, 'b', t.opp,
                 'sa', you, 'sb', them, 'w', case when won then 0 else t.opp end, 'you', true));
  if not won then
    t.status := 'lost'; t.phase := 'between'; t.m_start := null;
    perform public.tourney_book_loss(t);
    t := public.tourney_rest(t, 1, true);                          -- the bracket still finishes
    return t;
  end if;
  t := public.tourney_rest(t, 1, false);                           -- the other matches of this round
  if t.round >= 3 then
    t.status := 'won'; t.phase := 'between'; t.m_start := null; t.payout := t.buyin * 8;
    update public.wallets set chips = chips + t.payout,
           lifetime_won = lifetime_won + (t.payout - t.buyin), updated_at = now()
     where user_id = t.user_id;
    insert into public.casino_log (user_id, game, bet, delta, detail)
         values (t.user_id, 'tourney', t.buyin, t.payout - t.buyin, jsonb_build_object('won', true));
    return t;
  end if;
  t.round := t.round + 1; t.phase := 'between'; t.m_start := null;
  t.opp := t.alive[2];                                             -- you are always first in your pair
  return t;
end $$;

-- ---------------------------------------------------------------- what the browser calls
create or replace function public.tourney_start(buyin bigint, exam int default 0)
returns jsonb language plpgsql security definer set search_path = public as $$
declare w public.wallets; t public.tournaments; ex int; nm text; names text[]; pool text[] :=
  array['Maya','Omer','Noa','Daniel','Lior','Yael','Amit','Tamar','Ethan','Sarah','Priya','Kenji',
        'Lucas','Ava','Mateo','Zoe','Aarav','Hana','Ilan','Mika','Rafael','Chloe','Yuki','Nadia',
        'Oren','Leah','Sam','Dana','Eitan','Roni','Itai','Shira','Gal','Ben','Adi','Tom'];
begin
  w := public.wallet_row();
  -- Take the wallet row first. Starts fired at once all read "none open, fewer than five today"
  -- before any had committed; holding the row makes the next one wait and then see this one.
  select * into w from public.wallets where user_id = auth.uid() for update;
  -- one at a time: an open tournament comes back instead of a second
  select * into t from public.tournaments where user_id = auth.uid() and status = 'active'
   order by created_at desc limit 1;
  if t.id is not null then return jsonb_build_object('ok', true, 'resumed', true, 't', public.tourney_view(t), 'chips', w.chips); end if;
  if tourney_start.buyin not in (10, 25, 50, 100, 250) then
    return jsonb_build_object('ok', false, 'reason', 'pick a buy-in of 10, 25, 50, 100 or 250 chips', 'chips', w.chips);
  end if;
  if (select count(*) from public.tournaments where user_id = auth.uid()
        and created_at > now() - interval '1 day') >= public.tourney_daily() then
    return jsonb_build_object('ok', false, 'reason', 'five tournaments a day — come back tomorrow', 'chips', w.chips);
  end if;
  if w.chips < tourney_start.buyin then
    return jsonb_build_object('ok', false, 'reason', 'not enough chips', 'chips', w.chips);
  end if;
  ex := coalesce(tourney_start.exam, 0);
  if ex < 0 or ex > public.duel_exam_count() then ex := 0; end if;
  select username into nm from public.profiles where id = auth.uid();
  select array_agg(x) into names from (select x from unnest(pool) x order by random() limit 7) s;
  -- the buy-in leaves the wallet now; it is booked as won or lost when the tournament ends
  update public.wallets set chips = chips - tourney_start.buyin, updated_at = now()
   where user_id = auth.uid();
  delete from public.tournaments where user_id = auth.uid() and created_at < now() - interval '7 days';
  insert into public.tournaments (user_id, buyin, exam, players, opp)
       values (auth.uid(), tourney_start.buyin, ex,
               jsonb_build_array(jsonb_build_object('name', coalesce(nm, 'you'), 'bot', false)) ||
               (select jsonb_agg(jsonb_build_object('name', x, 'bot', true)) from unnest(names) x),
               1)
    returning * into t;
  t := public.tourney_new_match(t);
  update public.tournaments set m_q = t.m_q, m_bot = t.m_bot, m_log = t.m_log, used = t.used,
         m_start = t.m_start, phase = t.phase, updated_at = now() where id = t.id;
  select * into w from public.wallets where user_id = auth.uid();
  return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips);
end $$;

-- save every field the helpers may have changed
create or replace function public.tourney_save(t public.tournaments)
returns void language sql security definer set search_path = public as $$
  update public.tournaments set status = t.status, phase = t.phase, round = t.round, alive = t.alive,
         results = t.results, used = t.used, opp = t.opp, m_q = t.m_q, m_bot = t.m_bot, m_log = t.m_log,
         m_start = t.m_start, payout = t.payout, updated_at = now()
   where id = t.id;
$$;

-- The question in play ran out: it counts as unanswered (wrong), and the match moves on.
create or replace function public.tourney_timeout(t public.tournaments)
returns public.tournaments language plpgsql security definer set search_path = public as $$
declare i int := jsonb_array_length(t.m_log);
begin
  t.m_log := t.m_log || jsonb_build_array(jsonb_build_object(
    'q', t.m_q[i + 1], 'ans', to_jsonb(public.duel_answers(t.m_q[i + 1])), 'pick', null,
    'ok', false, 'bot', (t.m_bot -> i ->> 'ok')::boolean, 'late', true));
  return public.tourney_after(t);
end $$;

create or replace function public.tourney_state(tid uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare t public.tournaments; w public.wallets;
begin
  w := public.wallet_row();
  select * into t from public.tournaments where id = tid and user_id = auth.uid() for update;
  if t.id is null then return jsonb_build_object('ok', false, 'reason', 'no such tournament'); end if;
  -- out of time at the clock's own two minutes: the page shows 0:00 then, and asks. (The two
  -- seconds of grace are for an answer already on its way, in tourney_answer.)
  if t.status = 'active' and t.phase = 'play' and t.m_start is not null
     and jsonb_array_length(t.m_log) < coalesce(array_length(t.m_q, 1), 0)
     and now() - t.m_start >= (public.tourney_seconds() || ' seconds')::interval then
    t := public.tourney_timeout(t);
    perform public.tourney_save(t);
  end if;
  select * into w from public.wallets where user_id = auth.uid();
  return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips);
end $$;

-- The one-argument-less version is dropped rather than overloaded: PostgREST picks a function by
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
  end if;
  if now() - t.m_start > ((public.tourney_seconds() + 2) || ' seconds')::interval then
    t := public.tourney_timeout(t);                               -- too late: it counts as unanswered
  else
    q := t.m_q[i + 1];
    correct := public.duel_answers(q);
    ok := correct is not null and picks is not null
          and array_length(picks, 1) = array_length(correct, 1) and picks @> correct and correct @> picks;
    t.m_log := t.m_log || jsonb_build_array(jsonb_build_object(
      'q', q, 'ans', to_jsonb(correct), 'pick', to_jsonb(picks), 'ok', ok, 'bot', (t.m_bot -> i ->> 'ok')::boolean));
    t := public.tourney_after(t);
  end if;
  perform public.tourney_save(t);
  select * into w from public.wallets where user_id = auth.uid();
  return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips);
end $$;

-- after a won round, when you are ready: the next match
create or replace function public.tourney_next(tid uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare t public.tournaments; w public.wallets;
begin
  w := public.wallet_row();
  select * into t from public.tournaments where id = tid and user_id = auth.uid() for update;
  if t.id is null then return jsonb_build_object('ok', false, 'reason', 'no such tournament'); end if;
  if t.status = 'active' and t.phase = 'between' then
    t := public.tourney_new_match(t);
    perform public.tourney_save(t);
  end if;
  return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips);
end $$;

-- walking out concedes: the buy-in stays in the pot
create or replace function public.tourney_leave(tid uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare t public.tournaments; w public.wallets; you int; them int;
begin
  w := public.wallet_row();
  select * into t from public.tournaments where id = tid and user_id = auth.uid() for update;
  if t.id is null then return jsonb_build_object('ok', false, 'reason', 'no such tournament'); end if;
  if t.status = 'active' then
    you  := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'ok')::boolean);
    them := (select count(*) from jsonb_array_elements(t.m_log) e where (e ->> 'bot')::boolean);
    -- between rounds m_log is the match already won, not the one being walked out of
    if t.phase = 'between' then you := 0; them := 0; end if;
    t.results := t.results || jsonb_build_array(jsonb_build_object('round', t.round, 'a', 0, 'b', t.opp,
                   'sa', you, 'sb', greatest(them, you + 1), 'w', t.opp, 'you', true, 'left', true));
    t.status := 'lost'; t.phase := 'between'; t.m_start := null;
    perform public.tourney_book_loss(t);
    t := public.tourney_rest(t, 1, true);
    perform public.tourney_save(t);
  end if;
  return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips);
end $$;

-- the tournament you have open, if any — for picking it up after a reload
create or replace function public.tourney_current()
returns jsonb language plpgsql security definer set search_path = public as $$
declare t public.tournaments; w public.wallets; left_today int;
begin
  w := public.wallet_row();
  select * into t from public.tournaments where user_id = auth.uid() and status = 'active'
   order by created_at desc limit 1;
  left_today := greatest(0, public.tourney_daily() - (select count(*)::int from public.tournaments
                  where user_id = auth.uid() and created_at > now() - interval '1 day'));
  return jsonb_build_object('ok', true, 't', public.tourney_view(t), 'chips', w.chips, 'left', left_today);
end $$;

-- ---------------------------------------------------------------- permissions
do $$
declare f text;
begin
  foreach f in array array['tourney_start(bigint,int)','tourney_state(uuid)','tourney_answer(uuid,text[],int)',
                           'tourney_next(uuid)','tourney_leave(uuid)','tourney_current()']
  loop
    execute format('revoke all on function public.%s from public, anon;', f);
    execute format('grant execute on function public.%s to authenticated;', f);
  end loop;
  foreach f in array array['tourney_pick(int,int[],int)','tourney_rest(public.tournaments,int,boolean)',
                           'tourney_new_match(public.tournaments)','tourney_after(public.tournaments)',
                           'tourney_save(public.tournaments)','tourney_timeout(public.tournaments)',
                           'tourney_view(public.tournaments)','tourney_bot_answer()','tourney_botmatch()',
                           'tourney_book_loss(public.tournaments)']
  loop
    execute format('revoke all on function public.%s from public, anon, authenticated;', f);
  end loop;
end $$;

notify pgrst, 'reload schema';

-- verify: expect the table and six callable functions
select (select count(*) from information_schema.tables where table_name = 'tournaments') as tables,
       (select count(*) from pg_proc where proname in ('tourney_start','tourney_state','tourney_answer',
          'tourney_next','tourney_leave','tourney_current')) as functions;
