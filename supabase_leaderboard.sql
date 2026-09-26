-- ============================================================================
--  Skyforge — weekly leaderboard: correct answers this week, every player
--  Run after supabase_setup.sql. Safe to re-run.
--
--  Profiles are private (row-level security: you read your own row only), and that stays so.
--  This one function reads them with the owner's rights and hands back only what a leaderboard
--  shows: a rank, a username and a count — never a profile, an id or anyone's other numbers.
--
--  The count is profile.wk.dev: correct answers this week per device, written by the app. It is
--  the browser's own number, like the rest of the profile, so it is bounded here: a value that
--  is not a plain number counts as 0 (it cannot break the board for everyone), and a week is
--  capped at 5000 (more than a person answers in a week).
-- ============================================================================

create or replace function public.leaderboard_week(wk text, lim int default 10)
returns jsonb
language plpgsql stable security definer set search_path = public
as $$
declare me uuid := auth.uid(); n int; res jsonb;
begin
  if me is null then
    return jsonb_build_object('ok', false, 'reason', 'sign in to see the leaderboard');
  end if;
  if wk is null or wk !~ '^[0-9]{4}-w[0-9]{1,2}$' then
    return jsonb_build_object('ok', false, 'reason', 'bad week');
  end if;
  n := greatest(1, least(coalesce(lim, 10), 50));

  with s as (
    select p.id,
           coalesce(nullif(p.username, ''), 'player') as name,
           least(5000, coalesce((
             select sum(case when e.value ~ '^[0-9]{1,6}$' then e.value::int else 0 end)
               from jsonb_each_text(case when jsonb_typeof(p.profile -> 'wk' -> 'dev') = 'object'
                                         then p.profile -> 'wk' -> 'dev' else '{}'::jsonb end) e
           ), 0))::int as c
      from public.profiles p
     where p.profile -> 'wk' ->> 'key' = wk
  ), r as (
    select id, name, c, rank() over (order by c desc) as rk from s where c > 0
  )
  select jsonb_build_object(
           'ok', true, 'week', wk,
           'players', (select count(*) from r),
           'top', coalesce((select jsonb_agg(jsonb_build_object('rank', t.rk, 'name', t.name, 'c', t.c,
                                                                 'me', t.id = me) order by t.rk, t.name)
                              from (select * from r order by rk, name limit n) t), '[]'::jsonb),
           'me', (select jsonb_build_object('rank', rk, 'c', c) from r where id = me))
    into res;
  return res;
end $$;

revoke all on function public.leaderboard_week(text, int) from public, anon;
grant execute on function public.leaderboard_week(text, int) to authenticated;

notify pgrst, 'reload schema';

-- verify: expect one function
select count(*) as leaderboard_functions from pg_proc where proname = 'leaderboard_week';
