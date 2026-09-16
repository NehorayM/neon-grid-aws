-- ============================================================================
--  Neon Grid — Casino v2
--   · shared roulette: one wheel for everyone, a new round every 25 seconds
--   · study coins → chips (capped, see the note below)
--   · retention: old rounds, bets, hands and logs delete themselves
--  Run after supabase_casino.sql. Safe to re-run.
-- ============================================================================

-- ---------------------------------------------------------------- house secret
-- Seeds the wheel. No policies, so no client can ever read it: without this a player
-- could compute the next pocket themselves, since the outcome is derived from the
-- round number rather than rolled at a random moment.
create table if not exists public.casino_secret (
  k text primary key,
  v text not null
);
alter table public.casino_secret enable row level security;

insert into public.casino_secret (k, v)
  values ('wheel', encode(gen_random_bytes(32), 'hex'))
  on conflict (k) do nothing;

-- ---------------------------------------------------------------- rounds & bets
create table if not exists public.roulette_rounds (
  id          bigint primary key,            -- floor(epoch / 25): the round IS the clock
  pocket      int,
  colour      text,
  resolved_at timestamptz,
  created_at  timestamptz not null default now()
);
alter table public.roulette_rounds enable row level security;
drop policy if exists "read rounds" on public.roulette_rounds;
create policy "read rounds" on public.roulette_rounds for select using (auth.uid() is not null);

create table if not exists public.roulette_bets (
  id         bigserial primary key,
  round_id   bigint not null,
  user_id    uuid   not null references auth.users (id) on delete cascade,
  username   text,                            -- denormalised so the live table needs no joins
  pick       text   not null check (pick in ('red','black','green')),
  amount     bigint not null check (amount > 0),
  payout     bigint,
  settled    boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists roulette_bets_round_idx on public.roulette_bets (round_id);
alter table public.roulette_bets enable row level security;

-- Everyone at the table sees the bets on the table - that is the point of playing together.
drop policy if exists "read table bets" on public.roulette_bets;
create policy "read table bets" on public.roulette_bets
  for select using (auth.uid() is not null);
-- but only the functions below may write one
drop policy if exists "no client writes" on public.roulette_bets;

-- ---------------------------------------------------------------- retention
-- The user was right that this fills up: a round every 25 seconds is ~3,500 rows a day
-- before anyone even bets. Nothing here needs a scheduler - each call sweeps a little.
create or replace function public.casino_sweep()
returns void
language plpgsql security definer set search_path = public
as $$
begin
  delete from public.roulette_bets   where created_at < now() - interval '2 hours';
  delete from public.roulette_rounds where created_at < now() - interval '2 hours';
  delete from public.casino_log      where created_at < now() - interval '7 days';
  delete from public.bj_hands        where state = 'done' and updated_at < now() - interval '1 day';
end $$;

-- ---------------------------------------------------------------- the wheel
create or replace function public.roulette_now()
returns bigint language sql stable as $$
  select floor(extract(epoch from now()) / 25)::bigint;
$$;

-- Outcome is a pure function of (round number, secret). Every player who asks gets the
-- same answer, so no background worker has to be running for the wheel to have spun.
create or replace function public.roulette_pocket(round bigint)
returns int
language plpgsql security definer set search_path = public
as $$
declare s text; h text;
begin
  select v into s from public.casino_secret where k = 'wheel';
  h := md5(s || ':' || round::text);
  return (('x' || substr(h, 1, 8))::bit(32)::bigint % 37)::int;
end $$;

create or replace function public.roulette_colour(pocket int)
returns text language sql immutable as $$
  select case when pocket = 0 then 'green'
              when pocket = any (array[1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36])
              then 'red' else 'black' end;
$$;

-- Settle every round whose 25 seconds are up but whose bets have not been paid.
create or replace function public.roulette_settle()
returns void
language plpgsql security definer set search_path = public
as $$
declare r record; p int; c text;
begin
  for r in
    select distinct b.round_id
      from public.roulette_bets b
     where b.settled = false and b.round_id < public.roulette_now()
  loop
    p := public.roulette_pocket(r.round_id);
    c := public.roulette_colour(p);

    insert into public.roulette_rounds (id, pocket, colour, resolved_at)
         values (r.round_id, p, c, now())
    on conflict (id) do update set pocket = excluded.pocket, colour = excluded.colour,
                                   resolved_at = excluded.resolved_at;

    -- winners are paid, losers already had the stake taken when they bet
    update public.wallets w
       set chips = w.chips + b.amount * (case when b.pick = 'green' then 36 else 2 end),
           lifetime_won = w.lifetime_won + b.amount * (case when b.pick = 'green' then 35 else 1 end),
           updated_at = now()
      from public.roulette_bets b
     where b.round_id = r.round_id and b.settled = false and b.pick = c and w.user_id = b.user_id;

    update public.roulette_bets b
       set settled = true,
           payout = case when b.pick = c
                         then b.amount * (case when b.pick = 'green' then 36 else 2 end)
                         else 0 end
     where b.round_id = r.round_id and b.settled = false;

    update public.wallets w
       set lifetime_lost = w.lifetime_lost + b.amount
      from public.roulette_bets b
     where b.round_id = r.round_id and b.pick <> c and w.user_id = b.user_id
       and b.payout = 0;
  end loop;
end $$;

-- One call the client can poll: settles what is due, sweeps old rows, and returns the
-- state of the table - the clock, this round's bets from everyone, and the last result.
create or replace function public.roulette_table()
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare cur bigint; ends timestamptz; last record; bets jsonb; mine jsonb; w public.wallets;
begin
  w   := public.wallet_row();
  cur := public.roulette_now();
  perform public.roulette_settle();
  if random() < 0.05 then perform public.casino_sweep(); end if;   -- amortised cleanup

  ends := to_timestamp((cur + 1) * 25);

  select * into last from public.roulette_rounds
   where resolved_at is not null order by id desc limit 1;

  select coalesce(jsonb_agg(jsonb_build_object(
           'who', coalesce(b.username, 'player'), 'pick', b.pick, 'amount', b.amount,
           'me', b.user_id = auth.uid()) order by b.id), '[]'::jsonb)
    into bets
    from public.roulette_bets b where b.round_id = cur;

  select coalesce(jsonb_agg(jsonb_build_object('pick', pick, 'amount', amount)), '[]'::jsonb)
    into mine
    from public.roulette_bets where round_id = cur and user_id = auth.uid();

  return jsonb_build_object(
    'round', cur,
    'endsAt', ends,
    'secondsLeft', greatest(0, round(extract(epoch from (ends - now()))))::int,
    'open', extract(epoch from (ends - now())) > 3,      -- no more bets in the last 3 seconds
    'bets', bets, 'mine', mine, 'chips', w.chips,
    'last', case when last is null then null else
      jsonb_build_object('round', last.id, 'pocket', last.pocket, 'colour', last.colour) end);
end $$;

create or replace function public.roulette_bet(pick text, amount bigint)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare w public.wallets; cur bigint; ends timestamptz; nm text;
begin
  w := public.wallet_row();
  if pick not in ('red','black','green') then raise exception 'bad pick'; end if;
  if amount <= 0 then raise exception 'bet must be positive'; end if;
  if w.chips < amount then
    return jsonb_build_object('ok', false, 'reason', 'not enough chips', 'chips', w.chips);
  end if;

  cur  := public.roulette_now();
  ends := to_timestamp((cur + 1) * 25);
  if extract(epoch from (ends - now())) <= 3 then
    return jsonb_build_object('ok', false, 'reason', 'no more bets — wait for the next round',
                              'chips', w.chips);
  end if;

  select username into nm from public.profiles where id = auth.uid();

  update public.wallets set chips = chips - amount, updated_at = now()
   where user_id = auth.uid() returning * into w;

  insert into public.roulette_bets (round_id, user_id, username, pick, amount)
       values (cur, auth.uid(), coalesce(nm, 'player'), pick, amount);

  return jsonb_build_object('ok', true, 'chips', w.chips, 'round', cur);
end $$;

-- ---------------------------------------------------------------- coins → chips
-- The reverse of cashing out, and the weaker half of the pair: study coins are written by
-- the browser, so the server cannot verify the player really had them. The daily cap is
-- what keeps a forged balance from becoming unlimited chips to take off someone in a duel.
create or replace function public.casino_buy_chips(coins bigint)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare w public.wallets; got bigint; used bigint; cap bigint := 1000;
begin
  w := public.wallet_row();
  if coins <= 0 then raise exception 'amount must be positive'; end if;
  got := coins * 5;                                   -- 1 study coin = 5 chips, the cash-out rate

  select coalesce(sum(delta), 0) into used
    from public.casino_log
   where user_id = auth.uid() and game = 'buyin' and created_at > now() - interval '24 hours';

  if used + got > cap then
    return jsonb_build_object('ok', false,
      'reason', 'daily buy-in limit reached (' || cap || ' chips per 24h)',
      'remaining', greatest(0, cap - used), 'chips', w.chips);
  end if;

  update public.wallets set chips = chips + got, updated_at = now()
   where user_id = auth.uid() returning * into w;
  insert into public.casino_log (user_id, game, bet, delta, detail)
       values (auth.uid(), 'buyin', 0, got, jsonb_build_object('coins', coins));

  return jsonb_build_object('ok', true, 'chips', w.chips, 'got', got,
                            'remaining', cap - used - got);
end $$;

-- ---------------------------------------------------------------- permissions
do $$
declare f text;
begin
  foreach f in array array['roulette_table()','roulette_bet(text,bigint)',
                           'casino_buy_chips(bigint)','roulette_now()']
  loop
    execute format('revoke all on function public.%s from public, anon;', f);
    execute format('grant execute on function public.%s to authenticated;', f);
  end loop;
end $$;
revoke all on function public.roulette_pocket(bigint) from public, anon, authenticated;
revoke all on function public.roulette_settle() from public, anon, authenticated;
revoke all on function public.casino_sweep() from public, anon, authenticated;

notify pgrst, 'reload schema';

-- ---------------------------------------------------------------- verify
select 'rounds' as t, count(*) from public.roulette_rounds
union all select 'bets', count(*) from public.roulette_bets
union all select 'secret set', count(*) from public.casino_secret where k = 'wheel';
