-- Casino tournament: the whole run, the pot, a loss, sudden death, the clock, walking out,
-- the daily limit and privacy. Bots' answers are set by hand where a test needs them fixed.
\set ON_ERROR_STOP on
\pset pager off

create or replace function tt_bots(tid uuid, oks boolean[]) returns void language plpgsql as $$
declare b jsonb := '[]'::jsonb; k int;
begin
  for k in 1..array_length(oks, 1) loop b := b || jsonb_build_array(jsonb_build_object('ok', oks[k], 't', 30)); end loop;
  update public.tournaments set m_bot = b where id = tid;
end $$;
-- answer the question in play right (or wrong)
create or replace function tt_answer(tid uuid, right_one boolean) returns jsonb language plpgsql as $$
declare q int;
begin
  select m_q[jsonb_array_length(m_log) + 1] into q from public.tournaments where id = tid;
  return public.tourney_answer(tid, case when right_one then public.duel_answers(q) else array['Z'] end);
end $$;

do $$
declare
  A uuid := '11111111-1111-4111-8111-111111111111';
  B uuid := '22222222-2222-4222-8222-222222222222';
  r jsonb; v jsonb; tid uuid; k int; j int; chips0 bigint; t public.tournaments;
begin
  delete from public.tournaments;
  perform set_chips(A, 1000); perform set_chips(B, 100);
  perform as_user(A);

  -- ---- starting
  r := public.tourney_start(33);
  perform test_assert(not (r->>'ok')::boolean, 'a buy-in off the list is refused');
  perform set_chips(A, 20);
  r := public.tourney_start(50);
  perform test_assert(not (r->>'ok')::boolean and (select chips from public.wallets where user_id = A) = 20,
                      'a buy-in you cannot cover is refused and costs nothing');
  perform set_chips(A, 1000);
  r := public.tourney_start(50, 3);
  perform test_assert((r->>'ok')::boolean, 'a tournament starts');
  v := r->'t'; tid := (v->>'id')::uuid;
  perform test_assert((select chips from public.wallets where user_id = A) = 950, 'the buy-in is taken');
  perform test_assert(jsonb_array_length(v->'players') = 8, 'eight players');
  perform test_assert((v->>'pot')::int = 400, 'the pot is eight buy-ins');
  perform test_assert((v->>'round')::int = 1 and (v->>'n')::int = 5 and (v->>'i')::int = 0, 'round one, question one of five');
  perform test_assert((v->>'question')::int between 130 and 194, 'from the exam chosen (Exam 3)');
  perform test_assert((v->>'secondsLeft')::int between 118 and 120, 'two minutes on the clock');
  perform test_assert((v->>'oppAt')::int between 8 and 115, 'the bot answers at a human moment');
  perform test_assert(not (v::text ~ 'm_bot') and jsonb_array_length(v->'log') = 0,
                      'nothing about the bot''s answers is shown before you answer');
  r := public.tourney_start(100);
  perform test_assert((r->>'resumed')::boolean and (r->'t'->>'id')::uuid = tid, 'a second start hands back the open one');
  perform test_assert((select chips from public.wallets where user_id = A) = 950, 'and takes nothing more');

  -- ---- someone else cannot see or play it
  perform as_user(B);
  r := public.tourney_state(tid);
  perform test_assert(not (r->>'ok')::boolean, 'another player cannot read your tournament');
  r := public.tourney_answer(tid, array['A']);
  perform test_assert(not (r->>'ok')::boolean, 'or answer in it');
  perform as_user(A);

  -- ---- a won quarter-final: five right against a bot that gets two
  perform tt_bots(tid, array[true,false,true,false,false]);
  for k in 1..5 loop r := tt_answer(tid, true); end loop;
  v := r->'t';
  perform test_assert((v->>'status') = 'active' and (v->>'phase') = 'between' and (v->>'round')::int = 2,
                      'five against two wins the quarter-final, and the semi-final waits for you');
  perform test_assert(jsonb_array_length(v->'results') = 4, 'all four quarter-finals are played');
  perform test_assert(jsonb_array_length(v->'alive') = 4 and (v->'alive'->>0)::int = 0, 'four left, you among them');
  perform test_assert((v->'log'->0->>'ok')::boolean and (v->'log'->1->>'bot')::boolean = false,
                      'each answered question shows your result and the bot''s');
  r := public.tourney_next(tid); v := r->'t';
  perform test_assert((v->>'phase') = 'play' and (v->>'i')::int = 0 and (v->>'opp')::int = (v->'alive'->>1)::int,
                      'the semi-final is against the winner of the next quarter-final');
  select * into t from public.tournaments where id = tid;
  perform test_assert(not (t.m_q && (select array_agg(x) from unnest(t.used[1:5]) x)), 'no question comes up twice');

  -- ---- a tie goes to sudden death
  perform tt_bots(tid, array[true,true,true,false,false,false]);
  r := tt_answer(tid, true); r := tt_answer(tid, true); r := tt_answer(tid, true);
  r := tt_answer(tid, false); r := tt_answer(tid, false);
  v := r->'t';
  perform test_assert((v->>'n')::int = 6 and (v->>'phase') = 'play', 'three all: one more question, sudden death');
  r := tt_answer(tid, true); v := r->'t';
  perform test_assert((v->>'round')::int = 3, 'right when the bot is wrong wins it');
  perform test_assert(jsonb_array_length(v->'results') = 6, 'both semi-finals are played');

  -- ---- the final, and the pot
  r := public.tourney_next(tid);
  perform tt_bots(tid, array[false,false,false,false,false]);
  chips0 := (select chips from public.wallets where user_id = A);
  for k in 1..5 loop r := tt_answer(tid, true); end loop;
  v := r->'t';
  perform test_assert((v->>'status') = 'won', 'winning the final wins the tournament');
  perform test_assert((v->>'payout')::int = 400, 'the payout is the pot');
  perform test_assert((select chips from public.wallets where user_id = A) = chips0 + 400, 'and it lands in your wallet');
  perform test_assert(jsonb_array_length(v->'results') = 7, 'seven matches in all');
  r := public.tourney_answer(tid, array['A']);
  perform test_assert((select chips from public.wallets where user_id = A) = chips0 + 400, 'a finished tournament pays once');

  -- ---- knocked out: the bracket still finishes, nothing is paid
  r := public.tourney_start(10); tid := (r->'t'->>'id')::uuid;
  chips0 := (select chips from public.wallets where user_id = A);
  perform tt_bots(tid, array[true,true,true,true,true]);
  for k in 1..5 loop r := tt_answer(tid, false); end loop;
  v := r->'t';
  perform test_assert((v->>'status') = 'lost', 'none against five is out');
  perform test_assert(jsonb_array_length(v->'results') = 7 and jsonb_array_length(v->'alive') = 1,
                      'and the rest of the bracket is played out to a champion');
  perform test_assert((select chips from public.wallets where user_id = A) = chips0, 'nothing is paid');

  -- ---- the clock: a question left to run out counts as unanswered
  r := public.tourney_start(10); tid := (r->'t'->>'id')::uuid;
  update public.tournaments set m_start = now() - interval '130 seconds' where id = tid;
  r := public.tourney_state(tid); v := r->'t';
  perform test_assert(jsonb_array_length(v->'log') = 1 and not (v->'log'->0->>'ok')::boolean
                      and (v->'log'->0->>'late')::boolean, 'a question that runs out is marked unanswered');
  perform test_assert((v->>'secondsLeft')::int >= 118, 'and the next one starts with its full two minutes');
  update public.tournaments set m_start = now() - interval '125 seconds' where id = tid;
  r := tt_answer(tid, true); v := r->'t';
  perform test_assert(not (v->'log'->1->>'ok')::boolean, 'an answer after the clock ran out does not count');

  -- ---- walking out
  r := public.tourney_leave(tid); v := r->'t';
  perform test_assert((v->>'status') = 'lost' and jsonb_array_length(v->'results') = 7, 'leaving concedes, and the bracket finishes');

  -- ---- five a day
  r := public.tourney_start(10); perform public.tourney_leave((r->'t'->>'id')::uuid);
  r := public.tourney_start(10); perform public.tourney_leave((r->'t'->>'id')::uuid);
  r := public.tourney_start(10);
  perform test_assert(not (r->>'ok')::boolean and r->>'reason' ~ 'five', 'a sixth tournament in a day is refused');
  r := public.tourney_current();
  perform test_assert((r->>'left')::int = 0 and r->'t' = 'null'::jsonb, 'and the lobby is told none are left and none is open');

  -- ---- review fixes
  delete from public.tournaments; delete from public.casino_log where game = 'tourney';
  update public.wallets set lifetime_won = 0, lifetime_lost = 0 where user_id = A;
  perform set_chips(A, 1000);
  r := public.tourney_start(25); tid := (r->'t'->>'id')::uuid;
  perform test_assert((select lifetime_lost from public.wallets where user_id = A) = 0,
                      'nothing is booked as lost just for starting');
  -- an answer for a question that has closed does not become the next one's
  perform tt_bots(tid, array[false,false,false,false,false]);
  r := tt_answer(tid, true);
  r := public.tourney_answer(tid, array['A'], 0);                    -- a second tap, for question 0
  perform test_assert((r->>'stale')::boolean and jsonb_array_length(r->'t'->'log') = 1,
                      'a late answer for question 1 is turned away, not given to question 2');
  r := public.tourney_answer(tid, public.duel_answers((select m_q[2] from public.tournaments where id = tid)), 1);
  perform test_assert(jsonb_array_length(r->'t'->'log') = 2 and (r->'t'->'log'->1->>'ok')::boolean,
                      'the answer that names the open question counts');
  for k in 1..3 loop r := tt_answer(tid, true); end loop;
  -- walking out between rounds: a clean 0-1, not the match already won
  r := public.tourney_leave(tid); v := r->'t';
  perform test_assert((v->'results'->4->>'sa')::int = 0 and (v->'results'->4->>'sb')::int = 1
                      and (v->'results'->4->>'round')::int = 2,
                      'leaving between rounds concedes the next match 0-1');
  perform test_assert((select lifetime_lost from public.wallets where user_id = A) = 25,
                      'the lost buy-in is booked once, when it is lost');
  -- a win books the net, and the log adds up to what the wallet did
  delete from public.tournaments where user_id = A;
  chips0 := (select chips from public.wallets where user_id = A);
  r := public.tourney_start(10); tid := (r->'t'->>'id')::uuid;
  for k in 1..3 loop
    perform tt_bots(tid, array[false,false,false,false,false]);
    for j in 1..5 loop r := tt_answer(tid, true); end loop;
    if k < 3 then r := public.tourney_next(tid); end if;
  end loop;
  perform test_assert((r->'t'->>'status') = 'won', '(a won tournament)');
  perform test_assert((select chips from public.wallets where user_id = A) = chips0 + 70, 'the wallet gains seven buy-ins net');
  perform test_assert((select lifetime_won from public.wallets where user_id = A) = 70, 'booked as 70 won');
  perform test_assert((select sum(delta) from public.casino_log where user_id = A and game = 'tourney') = 70 - 25,
                      'and the log adds up to what the wallet did (+70 won, -25 lost)');
  -- one open tournament per player, even past the checks
  r := public.tourney_start(10);
  begin
    insert into public.tournaments (user_id, buyin, players) values (A, 10, '[]'::jsonb);
    perform test_assert(false, 'a second open tournament is refused by the table itself');
  exception when unique_violation then
    perform test_assert(true, 'a second open tournament is refused by the table itself');
  end;

  delete from public.tournaments;
  raise notice 'TOURNAMENT CHECKS PASSED';
end $$;
