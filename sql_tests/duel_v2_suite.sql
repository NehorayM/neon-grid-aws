-- Duel v2: exam questions, the answer after every question, one advance per question.
\set ON_ERROR_STOP on
\pset pager off

do $$
declare
  A uuid := '11111111-1111-4111-8111-111111111111';
  B uuid := '22222222-2222-4222-8222-222222222222';
  r jsonb; v jsonb; d public.duels; stale public.duels; did uuid; right_ans text[]; q int;
begin
  delete from public.duels;

  -- ============ the key is the bank ============
  perform test_assert((select count(*) from jsonb_object_keys((select ans from public.answer_key where id = 1))) = 1201,
                      'v2 key holds every question in the bank');
  perform test_assert(public.duel_answers(862) = array['B','D'], 'question 862 has its corrected answer (B + D)');
  perform test_assert(public.duel_answers(1046) = array['C'], 'question 1046 has its corrected answer (C)');
  perform test_assert(public.duel_exam_count() = 19, 'the bank cuts into 19 exams');
  perform test_assert((select count(*) from pg_proc where proname = 'duel_find') = 1,
                      'one duel_find, so PostgREST is never left choosing between two');

  -- ============ one exam: every question comes from it ============
  perform set_chips(A, 500); perform set_chips(B, 500);
  perform as_user(A); r := public.duel_find(50, 3);
  perform test_assert((r->'duel'->>'exam')::int = 3, 'a seat remembers the exam it was opened for');
  perform as_user(B); r := public.duel_find(50, 0);
  perform test_assert(r->'duel'->>'status' = 'active', '"any exam" sits down with an exam-3 seat');
  perform test_assert((r->'duel'->>'exam')::int = 3, 'and the exam wins');
  select * into d from public.duels order by created_at desc limit 1; did := d.id;
  perform test_assert(array_length(d.q_ids, 1) = 5, 'five questions');
  perform test_assert((select bool_and(x between 130 and 194) from unnest(d.q_ids) x),
                      'all five from exam 3 (questions 130-194)');
  perform test_assert((select count(distinct x) from unnest(d.q_ids) x) = 5, 'no question twice');
  perform test_assert(jsonb_array_length(r->'duel'->'hist') = 0, 'nothing revealed before a question is over');

  -- ============ the answer after each question ============
  q := d.q_ids[1];
  right_ans := public.duel_answers(q);
  perform as_user(A); r := public.duel_answer(did, right_ans);
  perform test_assert(jsonb_array_length(r->'duel'->'hist') = 0,
                      'answering alone reveals nothing: the other player is still on it');
  perform as_user(B); r := public.duel_answer(did, right_ans);
  v := r->'duel';
  perform test_assert((v->>'turn')::int = 1, 'both right moves the duel on');
  perform test_assert(jsonb_array_length(v->'hist') = 1, 'and the finished question is in the history');
  perform test_assert((v->'hist'->0->>'q')::int = q, 'the right question');
  perform test_assert(v->'hist'->0->'answer' = to_jsonb(right_ans), 'with its answer');
  perform test_assert((v->'hist'->0->>'youOk')::boolean and (v->'hist'->0->>'themOk')::boolean,
                      'and both players marked right');
  perform test_assert(v->'hist'->0->'you' = to_jsonb(right_ans), 'each side sees its own pick as "you"');

  -- ============ two polls that both saw the clock run out advance once ============
  update public.duels set turn_start = now() - interval '10 minutes' where id = did;
  select * into stale from public.duels where id = did;
  perform public.duel_next(stale);
  perform public.duel_next(stale);                       -- the second poll, same stale row
  select * into d from public.duels where id = did;
  perform test_assert(d.turn = 2, 'a question nobody answered is skipped once, not twice');
  perform test_assert(jsonb_array_length(d.hist) = 2, 'and logged once');
  perform test_assert((d.hist->1->>'aok') is null and (d.hist->1->>'bok') is null,
                      'as unanswered by both');

  -- ============ the deciding question is in the history too ============
  right_ans := public.duel_answers(d.q_ids[3]);
  perform as_user(A); r := public.duel_answer(did, right_ans);
  perform as_user(B); r := public.duel_answer(did, array['Z']);
  v := r->'duel';
  perform test_assert(v->>'status' = 'done', 'right against wrong ends it');
  perform test_assert(jsonb_array_length(v->'hist') = 3, 'with the question that decided it in the history');
  perform test_assert(not (v->'hist'->2->>'youOk')::boolean and (v->'hist'->2->>'themOk')::boolean,
                      'from the loser''s side: they were wrong and the winner right');
  perform test_assert(v->'hist'->2->'you' = '["Z"]'::jsonb, 'and their own pick is shown back to them');
  perform test_assert((select chips from public.wallets where user_id = A) = 550, 'the winner is paid the pot');
  perform test_assert((select sum(chips) from public.wallets where user_id in (A, B)) = 1000,
                      'no chips minted');

  -- ============ different exams do not meet ============
  delete from public.duels;
  perform set_chips(A, 500); perform set_chips(B, 500);
  perform as_user(A); r := public.duel_find(50, 3); did := (r->'duel'->>'id')::uuid;
  perform as_user(B); r := public.duel_find(50, 4);
  perform test_assert(r->'duel'->>'status' = 'waiting', 'exam 3 and exam 4 wait at their own tables');
  perform test_assert((select count(*) from public.duels where status = 'waiting') = 2, 'two seats open');
  perform public.duel_leave((r->'duel'->>'id')::uuid);
  perform as_user(A); perform public.duel_leave(did);
  perform test_assert((select sum(chips) from public.wallets where user_id in (A, B)) = 1000,
                      'both refunded');

  -- ============ an exam that does not exist is "any" ============
  perform as_user(A); r := public.duel_find(50, 99);
  perform test_assert((r->'duel'->>'exam')::int = 0, 'exam 99 is treated as any exam');
  perform public.duel_leave((r->'duel'->>'id')::uuid);

  -- ============ the last exam is the short one ============
  perform as_user(A); r := public.duel_find(25, 19);
  perform as_user(B); r := public.duel_find(25, 19);
  select * into d from public.duels order by created_at desc limit 1;
  perform test_assert((select bool_and(x between 1170 and 1200) from unnest(d.q_ids) x),
                      'exam 19 draws from its 31 questions only');

  -- ============ an old page, sending the stake alone ============
  delete from public.duels;
  perform set_chips(A, 500);
  perform as_user(A); r := public.duel_find(stake => 40::bigint);
  perform test_assert((r->>'ok')::boolean and (r->'duel'->>'exam')::int = 0,
                      'a call with the stake alone still works, on any exam');
  perform public.duel_leave((r->'duel'->>'id')::uuid);

  -- ============ roulette lands even when nobody bet ============
  delete from public.roulette_bets; delete from public.roulette_rounds;
  perform as_user(A);
  r := public.roulette_table();
  perform test_assert(jsonb_typeof(r->'last') = 'object', 'the table has a result to land on when nobody bet');
  perform test_assert((r->'last'->>'round')::bigint = (r->>'round')::bigint - 1, 'the round that just finished');
  perform test_assert((r->'last'->>'colour') in ('red','black','green'), 'with a colour');
  r := public.roulette_table();
  perform test_assert((select count(*) from public.roulette_rounds where id = (r->>'round')::bigint - 1) = 1,
                      'written down once, however many times the table is read');

  delete from public.duels;
  raise notice 'DUEL V2 CHECKS PASSED';
end $$;
