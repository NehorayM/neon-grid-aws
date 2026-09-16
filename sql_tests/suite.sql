-- Assertion suite: every check raises on failure, so a clean run means a clean run.
\set ON_ERROR_STOP on
\pset pager off

create or replace function test_assert(cond boolean, what text) returns void
language plpgsql as $$
begin
  if cond then raise notice 'PASS  %', what;
  else raise exception 'FAIL  %', what; end if;
end $$;

create or replace function as_user(u uuid) returns void
language plpgsql as $$ begin perform set_config('test.uid', u::text, false); end $$;

create or replace function set_chips(u uuid, n bigint) returns void
language plpgsql as $$
begin
  insert into public.wallets (user_id, chips) values (u, n)
    on conflict (user_id) do update set chips = n;
end $$;

-- self-contained: create the players this suite plays as
insert into auth.users (id, email) values
  ('11111111-1111-4111-8111-111111111111','a@test'),
  ('22222222-2222-4222-8222-222222222222','b@test')
on conflict (id) do nothing;
insert into public.profiles (id, username) values
  ('11111111-1111-4111-8111-111111111111','alice'),
  ('22222222-2222-4222-8222-222222222222','bob')
on conflict (id) do update set username = excluded.username;

do $$
declare
  A uuid := '11111111-1111-4111-8111-111111111111';
  B uuid := '22222222-2222-4222-8222-222222222222';
  r jsonb; d public.duels; did uuid; total_before bigint; total_after bigint;
  right_ans text[]; res jsonb;
begin
  delete from public.duels;
  delete from public.roulette_bets;

  -- ============ duel: chips must be conserved ============
  perform set_chips(A, 100); perform set_chips(B, 100);
  total_before := (select sum(chips) from public.wallets where user_id in (A,B));

  perform as_user(A);
  r := public.duel_find(50);
  perform test_assert((r->>'ok')::boolean, 'alice can open a duel');
  perform test_assert(r->'duel'->>'status' = 'waiting', 'duel starts in waiting');
  perform test_assert((select chips from public.wallets where user_id=A) = 50,
                      'opening a duel takes the stake up front');

  perform as_user(B);
  r := public.duel_find(50);
  perform test_assert(r->'duel'->>'status' = 'active', 'joining makes it active');
  perform test_assert((r->'duel'->>'question') is not null, 'an active duel serves a question');

  select * into d from public.duels order by created_at desc limit 1;
  did := d.id;
  perform test_assert(array_length(d.q_ids,1) = 5, 'five questions are chosen');
  perform test_assert((select count(distinct x) from unnest(d.q_ids) x) = 5,
                      'the five questions are distinct');

  -- alice right, bob wrong
  right_ans := public.duel_answers(d.q_ids[1]);
  perform as_user(A); r := public.duel_answer(did, right_ans);
  perform as_user(B); r := public.duel_answer(did, array['Z']);

  select * into d from public.duels where id = did;
  perform test_assert(d.status = 'done', 'one right and one wrong ends the duel');
  perform test_assert(d.winner = A, 'the player who answered correctly wins');
  perform test_assert(d.reason = 'opponent answered wrong', 'the reason is recorded');
  perform test_assert((select chips from public.wallets where user_id=A) = 150,
                      'winner takes the whole pot');
  perform test_assert((select chips from public.wallets where user_id=B) = 50,
                      'loser is down exactly the stake');

  total_after := (select sum(chips) from public.wallets where user_id in (A,B));
  perform test_assert(total_before = total_after, 'chips are conserved: a duel mints nothing');

  -- ============ both correct -> the duel continues ============
  delete from public.duels;
  perform set_chips(A, 100); perform set_chips(B, 100);
  perform as_user(A); r := public.duel_find(25);
  perform as_user(B); r := public.duel_find(25);
  select * into d from public.duels order by created_at desc limit 1; did := d.id;
  right_ans := public.duel_answers(d.q_ids[1]);
  perform as_user(A); r := public.duel_answer(did, right_ans);
  perform as_user(B); r := public.duel_answer(did, right_ans);
  select * into d from public.duels where id = did;
  perform test_assert(d.status = 'active', 'both correct keeps the duel alive');
  perform test_assert(d.turn = 1, 'both correct advances to the next question');
  perform test_assert(d.a_pick is null and d.b_pick is null, 'picks reset for the new question');

  -- ============ both wrong -> also continues ============
  perform as_user(A); r := public.duel_answer(did, array['Z']);
  perform as_user(B); r := public.duel_answer(did, array['Z']);
  select * into d from public.duels where id = did;
  perform test_assert(d.turn = 2, 'both wrong also advances');
  perform test_assert(d.a_score = 1 and d.b_score = 1, 'scores only count correct answers');

  -- ============ leaving a live duel concedes ============
  perform as_user(A); r := public.duel_leave(did);
  select * into d from public.duels where id = did;
  perform test_assert(d.status = 'done' and d.winner = B, 'walking out hands the pot over');
  perform test_assert((select chips from public.wallets where user_id=B) = 125,
                      'the player who stayed is paid');

  -- ============ a lobby nobody joins refunds ============
  delete from public.duels;
  perform set_chips(A, 100);
  perform as_user(A); r := public.duel_find(40);
  perform test_assert((select chips from public.wallets where user_id=A) = 60, 'lobby holds the stake');
  r := public.duel_leave((r->'duel'->>'id')::uuid);
  perform test_assert((select chips from public.wallets where user_id=A) = 100,
                      'cancelling a lobby refunds in full');

  -- ============ you cannot duel yourself ============
  delete from public.duels;
  perform set_chips(A, 500);
  perform as_user(A); r := public.duel_find(50);
  r := public.duel_find(50);
  perform test_assert((select count(*) from public.duels) = 1,
                      'a second search returns your existing duel rather than a new one');

  -- ============ stake you cannot afford ============
  perform set_chips(B, 10);
  perform as_user(B); r := public.duel_find(250);
  perform test_assert((r->>'ok')::boolean = false, 'you cannot stake chips you do not have');

  -- ============ a finished duel cannot be paid out twice ============
  delete from public.duels;
  perform set_chips(A, 100); perform set_chips(B, 100);
  perform as_user(A); r := public.duel_find(50);
  perform as_user(B); r := public.duel_find(50);
  select * into d from public.duels order by created_at desc limit 1; did := d.id;
  right_ans := public.duel_answers(d.q_ids[1]);
  perform as_user(A); r := public.duel_answer(did, right_ans);
  perform as_user(B); r := public.duel_answer(did, array['Z']);
  perform test_assert((select chips from public.wallets where user_id=A) = 150,
                      'winner paid once');
  -- calling finish again on the settled duel must be a no-op, not a second pot
  select * into d from public.duels where id = did;
  perform public.duel_finish(d, A, 'replay');
  perform public.duel_finish(d, A, 'replay');
  perform test_assert((select chips from public.wallets where user_id=A) = 150,
                      'settling an already finished duel pays nothing extra');
  perform test_assert((select sum(chips) from public.wallets where user_id in (A,B)) = 200,
                      'no chips are minted by a repeated settle');

  -- ============ the question clock ============
  perform test_assert(public.duel_seconds() >= 60,
                      'a question stays open long enough to read it');
  delete from public.duels;
  perform set_chips(A, 100); perform set_chips(B, 100);
  perform as_user(A); r := public.duel_find(50);
  perform as_user(B); r := public.duel_find(50);
  perform test_assert((r->'duel'->>'secondsLeft')::int between public.duel_seconds() - 2
                      and public.duel_seconds(),
                      'the clock the client sees matches the server constant');

  -- ============ running out of time forfeits ============
  select * into d from public.duels order by created_at desc limit 1; did := d.id;
  right_ans := public.duel_answers(d.q_ids[1]);
  perform as_user(A); r := public.duel_answer(did, right_ans);   -- alice answers, bob does not
  update public.duels set turn_start = now() - (public.duel_seconds() + 5 || ' seconds')::interval
   where id = did;
  perform as_user(B); r := public.duel_state(did);
  select * into d from public.duels where id = did;
  perform test_assert(d.status = 'done' and d.winner = A,
                      'a player who runs out the clock forfeits to the one who answered');

  -- ============ roulette: payouts and conservation ============
  delete from public.duels; delete from public.roulette_bets;
  perform set_chips(A, 1000);
  perform as_user(A);
  r := public.roulette_bet('red', 100);
  perform test_assert((r->>'ok')::boolean, 'a roulette bet is accepted');
  perform test_assert((select chips from public.wallets where user_id=A) = 900,
                      'the stake leaves the wallet when the bet is placed');
  -- age the bet into a finished round and settle
  update public.roulette_bets set round_id = public.roulette_now() - 1 where settled = false;
  perform public.roulette_settle();
  perform test_assert((select bool_and(settled) from public.roulette_bets), 'every bet settles');
  perform test_assert(
    (select chips from public.wallets where user_id=A) in (900, 1100),
    'a red bet either loses the stake or pays even money');

  -- ============ blackjack basics ============
  perform set_chips(A, 500);
  r := public.bj_start(100);
  perform test_assert((r->>'ok')::boolean, 'a hand can be dealt');
  perform test_assert(jsonb_array_length(r->'player') = 2, 'the player gets two cards');
  perform test_assert(jsonb_array_length(r->'dealer') = 1,
                      'only one dealer card is visible while the hand is live');
  perform test_assert((select chips from public.wallets where user_id=A) <= 400,
                      'the bet is taken when the hand starts');

  raise notice '--------------------------------------------';
  raise notice 'ALL CHECKS PASSED';
end $$;
