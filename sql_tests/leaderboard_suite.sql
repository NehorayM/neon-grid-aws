-- Weekly leaderboard: order, privacy, bad data, the cap, other weeks, your own rank.
\set ON_ERROR_STOP on
\pset pager off

insert into auth.users (id, email) values
  ('33333333-3333-4333-8333-333333333333','c@test'),
  ('44444444-4444-4444-8444-444444444444','d@test'),
  ('55555555-5555-4555-8555-555555555555','e@test')
on conflict (id) do nothing;
insert into public.profiles (id, username) values
  ('33333333-3333-4333-8333-333333333333','carol'),
  ('44444444-4444-4444-8444-444444444444','dave'),
  ('55555555-5555-4555-8555-555555555555', null)
on conflict (id) do update set username = excluded.username;

do $$
declare
  A uuid := '11111111-1111-4111-8111-111111111111';
  B uuid := '22222222-2222-4222-8222-222222222222';
  C uuid := '33333333-3333-4333-8333-333333333333';
  D uuid := '44444444-4444-4444-8444-444444444444';
  E uuid := '55555555-5555-4555-8555-555555555555';
  r jsonb;
begin
  -- alice 30 (two devices 20 + 10), bob 45, carol a broken value and 7, dave last week, E 99999
  update public.profiles set profile = '{"wk":{"key":"2026-09-20","dev":{"phone":20,"pc":10}}, "coins":5}'::jsonb where id = A;
  update public.profiles set profile = '{"wk":{"key":"2026-09-20","dev":{"x":45}}}'::jsonb where id = B;
  update public.profiles set profile = '{"wk":{"key":"2026-09-20","dev":{"x":"abc","y":7}}}'::jsonb where id = C;
  update public.profiles set profile = '{"wk":{"key":"2026-09-13","dev":{"x":500}}}'::jsonb where id = D;
  update public.profiles set profile = '{"wk":{"key":"2026-09-20","dev":{"x":99999}}}'::jsonb where id = E;

  perform set_config('test.uid', '', false);
  r := public.leaderboard_week('2026-09-20');
  perform test_assert(not (r->>'ok')::boolean, 'signed out: no leaderboard');

  perform as_user(A);
  r := public.leaderboard_week('2026-09-20');
  perform test_assert((r->>'ok')::boolean, 'signed in: the board comes back');
  perform test_assert((r->>'players')::int = 4, 'four players this week (last week''s does not count)');
  perform test_assert(r->'top'->0->>'name' = 'player' and (r->'top'->0->>'c')::int = 5000,
                      'a count past 5000 is capped, and a player with no username is "player"');
  perform test_assert(r->'top'->1->>'name' = 'bob' and (r->'top'->1->>'c')::int = 45, 'bob second with 45');
  perform test_assert(r->'top'->2->>'name' = 'alice' and (r->'top'->2->>'c')::int = 30,
                      'alice third: her two devices add up to 30');
  perform test_assert((r->'top'->2->>'me')::boolean, 'and her row is marked as hers');
  perform test_assert(r->'top'->3->>'name' = 'carol' and (r->'top'->3->>'c')::int = 7,
                      'a value that is not a number counts as nothing, not as an error');
  perform test_assert((r->'me'->>'rank')::int = 3 and (r->'me'->>'c')::int = 30, 'your own rank and count');
  perform test_assert(not (r::text ~ '"coins"') and not (r::text ~ '1111'), 'no profile data and no ids leak');

  r := public.leaderboard_week('2026-09-20', 2);
  perform test_assert(jsonb_array_length(r->'top') = 2, 'the list stops at the limit asked for');
  perform test_assert((r->'me'->>'rank')::int = 3, 'and your rank still comes back when you are below it');

  r := public.leaderboard_week('2026-09-20', 100000);
  perform test_assert(jsonb_array_length(r->'top') <= 50, 'a huge limit is held to 50');

  r := public.leaderboard_week('2026-w39');
  perform test_assert(not (r->>'ok')::boolean, 'the old week format is refused');
  r := public.leaderboard_week('''; drop table public.profiles; --');
  perform test_assert(not (r->>'ok')::boolean, 'a week that is not a week is refused');
  perform test_assert((select count(*) from public.profiles) >= 5, 'and nothing happened to the table');

  perform as_user(D);
  r := public.leaderboard_week('2026-09-20');
  perform test_assert(r->'me' = 'null'::jsonb or r->'me' is null, 'no answers this week: no rank for you');

  raise notice 'LEADERBOARD CHECKS PASSED';
end $$;
