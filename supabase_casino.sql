-- ============================================================================
--  Neon Grid — Casino (server-authoritative)
--  Run once in: Supabase dashboard → SQL Editor → New query → Run
--  Safe to re-run.
--
--  The whole point of this file: the browser never decides an outcome. Every spin,
--  card and payout happens inside these functions, on the database, where the player
--  cannot reach. The chips table has NO client write policy at all - the only way a
--  balance changes is through a security-definer function below.
-- ============================================================================

-- ---------------------------------------------------------------- wallet
create table if not exists public.wallets (
  user_id        uuid primary key references auth.users (id) on delete cascade,
  chips          bigint      not null default 0 check (chips >= 0),
  last_grant_at  timestamptz,
  lifetime_won   bigint      not null default 0,
  lifetime_lost  bigint      not null default 0,
  updated_at     timestamptz not null default now()
);

alter table public.wallets enable row level security;

-- Read your own balance. Deliberately NO insert/update/delete policy: a client that
-- tries to write its own chips gets nothing, whatever it sends.
drop policy if exists "read own wallet" on public.wallets;
create policy "read own wallet" on public.wallets
  for select using (auth.uid() = user_id);

-- ---------------------------------------------------------------- blackjack hands
-- The shoe and the dealer's hole card live here and are never exposed: there is no
-- select policy, so only the functions below can see them.
create table if not exists public.bj_hands (
  user_id     uuid primary key references auth.users (id) on delete cascade,
  bet         bigint      not null,
  deck        int[]       not null,       -- remaining cards, 1..52, server eyes only
  player      int[]       not null,
  dealer      int[]       not null,
  state       text        not null default 'active',   -- active | done
  outcome     text,
  updated_at  timestamptz not null default now()
);
alter table public.bj_hands enable row level security;   -- no policies at all = no client access

-- ---------------------------------------------------------------- house log
create table if not exists public.casino_log (
  id         bigserial primary key,
  user_id    uuid not null references auth.users (id) on delete cascade,
  game       text not null,
  bet        bigint not null,
  delta      bigint not null,
  detail     jsonb,
  created_at timestamptz not null default now()
);
alter table public.casino_log enable row level security;
drop policy if exists "read own log" on public.casino_log;
create policy "read own log" on public.casino_log
  for select using (auth.uid() = user_id);

-- ============================================================================
--  helpers
-- ============================================================================
create or replace function public.wallet_row()
returns public.wallets
language plpgsql security definer set search_path = public
as $$
declare w public.wallets;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  insert into public.wallets (user_id, chips, last_grant_at)
    values (auth.uid(), 0, null)
    on conflict (user_id) do nothing;
  select * into w from public.wallets where user_id = auth.uid();
  return w;
end $$;

-- Balance + whether today's free chips are available.
create or replace function public.casino_state()
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare w public.wallets; ready boolean;
begin
  w := public.wallet_row();
  ready := (w.last_grant_at is null or now() - w.last_grant_at > interval '20 hours');
  return jsonb_build_object(
    'chips', w.chips,
    'grantReady', ready,
    'nextGrant', case when ready then null else w.last_grant_at + interval '20 hours' end,
    'won', w.lifetime_won, 'lost', w.lifetime_lost);
end $$;

-- Free daily chips, so an empty wallet is never a dead end.
create or replace function public.casino_grant()
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare w public.wallets; amount bigint := 250;
begin
  w := public.wallet_row();
  if w.last_grant_at is not null and now() - w.last_grant_at <= interval '20 hours' then
    return jsonb_build_object('ok', false, 'reason', 'already claimed',
                              'nextGrant', w.last_grant_at + interval '20 hours', 'chips', w.chips);
  end if;
  update public.wallets
     set chips = chips + amount, last_grant_at = now(), updated_at = now()
   where user_id = auth.uid()
  returning * into w;
  insert into public.casino_log (user_id, game, bet, delta, detail)
       values (auth.uid(), 'grant', 0, amount, '{}'::jsonb);
  return jsonb_build_object('ok', true, 'granted', amount, 'chips', w.chips);
end $$;

-- ============================================================================
--  roulette - single zero, 37 pockets
--  red/black pay 1:1, green pays 35:1
-- ============================================================================
create or replace function public.casino_roulette(bet bigint, pick text)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare
  w public.wallets;
  pocket int;
  colour text;
  payout bigint := 0;
  won boolean := false;
  reds int[] := array[1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
begin
  w := public.wallet_row();
  if pick not in ('red','black','green') then raise exception 'bad pick'; end if;
  if bet <= 0 then raise exception 'bet must be positive'; end if;
  if w.chips < bet then
    return jsonb_build_object('ok', false, 'reason', 'not enough chips', 'chips', w.chips);
  end if;

  -- the spin happens here, on the server, after the bet is locked in
  pocket := floor(random() * 37)::int;                    -- 0..36
  colour := case when pocket = 0 then 'green'
                 when pocket = any(reds) then 'red' else 'black' end;

  if colour = pick then
    won := true;
    payout := case when pick = 'green' then bet * 35 else bet end;
  end if;

  update public.wallets
     set chips = chips + (case when won then payout else -bet end),
         lifetime_won  = lifetime_won  + (case when won then payout else 0 end),
         lifetime_lost = lifetime_lost + (case when won then 0 else bet end),
         updated_at = now()
   where user_id = auth.uid()
  returning * into w;

  insert into public.casino_log (user_id, game, bet, delta, detail)
       values (auth.uid(), 'roulette', bet,
               case when won then payout else -bet end,
               jsonb_build_object('pocket', pocket, 'colour', colour, 'pick', pick));

  return jsonb_build_object('ok', true, 'pocket', pocket, 'colour', colour,
                            'won', won, 'payout', payout, 'chips', w.chips);
end $$;

-- ============================================================================
--  blackjack - dealer stands on 17, blackjack pays 3:2
--  cards are 1..52; rank = ((c - 1) % 13) + 1, suit = (c - 1) / 13
-- ============================================================================
create or replace function public.bj_value(cards int[])
returns int language plpgsql immutable as $$
declare c int; r int; total int := 0; aces int := 0;
begin
  foreach c in array cards loop
    r := ((c - 1) % 13) + 1;
    if r = 1 then aces := aces + 1; total := total + 11;
    elsif r >= 10 then total := total + 10;
    else total := total + r; end if;
  end loop;
  while total > 21 and aces > 0 loop total := total - 10; aces := aces - 1; end loop;
  return total;
end $$;

create or replace function public.bj_public(h public.bj_hands, reveal boolean)
returns jsonb language plpgsql stable set search_path = public as $$
begin
  return jsonb_build_object(
    'state', h.state, 'bet', h.bet, 'outcome', h.outcome,
    'player', h.player, 'playerValue', public.bj_value(h.player),
    -- the hole card stays hidden until the hand is settled
    'dealer', case when reveal then h.dealer else h.dealer[1:1] end,
    'dealerValue', case when reveal then public.bj_value(h.dealer)
                        else public.bj_value(h.dealer[1:1]) end);
end $$;

create or replace function public.bj_start(bet bigint)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare w public.wallets; deck int[]; h public.bj_hands; pv int; dv int;
begin
  w := public.wallet_row();
  if bet <= 0 then raise exception 'bet must be positive'; end if;
  if w.chips < bet then
    return jsonb_build_object('ok', false, 'reason', 'not enough chips', 'chips', w.chips);
  end if;
  delete from public.bj_hands where user_id = auth.uid();

  select array_agg(c order by random()) into deck
    from generate_series(1, 52) c;                       -- shuffled, server side only

  update public.wallets set chips = chips - bet, updated_at = now()
   where user_id = auth.uid() returning * into w;        -- stake is taken up front

  insert into public.bj_hands (user_id, bet, deck, player, dealer)
       values (auth.uid(), bet, deck[5:52],
               array[deck[1], deck[3]], array[deck[2], deck[4]])
  returning * into h;

  pv := public.bj_value(h.player); dv := public.bj_value(h.dealer);
  if pv = 21 or dv = 21 then                             -- naturals settle immediately
    if pv = 21 and dv = 21 then
      update public.wallets set chips = chips + h.bet where user_id = auth.uid();
      h.outcome := 'push';
    elsif pv = 21 then
      update public.wallets set chips = chips + h.bet + (h.bet * 3 / 2),
             lifetime_won = lifetime_won + (h.bet * 3 / 2) where user_id = auth.uid();
      h.outcome := 'blackjack';
    else
      update public.wallets set lifetime_lost = lifetime_lost + h.bet where user_id = auth.uid();
      h.outcome := 'dealer blackjack';
    end if;
    update public.bj_hands set state = 'done', outcome = h.outcome where user_id = auth.uid()
    returning * into h;
    insert into public.casino_log (user_id, game, bet, delta, detail)
      values (auth.uid(), 'blackjack', h.bet,
              case h.outcome when 'blackjack' then (h.bet * 3 / 2) when 'push' then 0 else -h.bet end,
              jsonb_build_object('outcome', h.outcome));
  end if;

  select * into w from public.wallets where user_id = auth.uid();
  return public.bj_public(h, h.state = 'done') || jsonb_build_object('ok', true, 'chips', w.chips);
end $$;

create or replace function public.bj_hit()
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare h public.bj_hands; w public.wallets;
begin
  select * into h from public.bj_hands where user_id = auth.uid();
  if h is null or h.state <> 'active' then raise exception 'no hand in play'; end if;

  h.player := h.player || h.deck[1];
  h.deck := h.deck[2:array_length(h.deck, 1)];

  if public.bj_value(h.player) > 21 then
    h.state := 'done'; h.outcome := 'bust';
    update public.wallets set lifetime_lost = lifetime_lost + h.bet, updated_at = now()
     where user_id = auth.uid();
    insert into public.casino_log (user_id, game, bet, delta, detail)
      values (auth.uid(), 'blackjack', h.bet, -h.bet, '{"outcome":"bust"}'::jsonb);
  end if;

  update public.bj_hands set player = h.player, deck = h.deck, state = h.state,
         outcome = h.outcome, updated_at = now()
   where user_id = auth.uid() returning * into h;

  select * into w from public.wallets where user_id = auth.uid();
  return public.bj_public(h, h.state = 'done') || jsonb_build_object('ok', true, 'chips', w.chips);
end $$;

create or replace function public.bj_stand()
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare h public.bj_hands; w public.wallets; pv int; dv int; delta bigint := 0;
begin
  select * into h from public.bj_hands where user_id = auth.uid();
  if h is null or h.state <> 'active' then raise exception 'no hand in play'; end if;

  while public.bj_value(h.dealer) < 17 loop                -- dealer draws to 17
    h.dealer := h.dealer || h.deck[1];
    h.deck := h.deck[2:array_length(h.deck, 1)];
  end loop;

  pv := public.bj_value(h.player); dv := public.bj_value(h.dealer);
  if dv > 21 or pv > dv then
    h.outcome := case when dv > 21 then 'dealer bust' else 'win' end;
    delta := h.bet;
    update public.wallets set chips = chips + h.bet * 2, lifetime_won = lifetime_won + h.bet,
           updated_at = now() where user_id = auth.uid();
  elsif pv = dv then
    h.outcome := 'push';
    update public.wallets set chips = chips + h.bet, updated_at = now() where user_id = auth.uid();
  else
    h.outcome := 'lose'; delta := -h.bet;
    update public.wallets set lifetime_lost = lifetime_lost + h.bet, updated_at = now()
     where user_id = auth.uid();
  end if;

  update public.bj_hands set dealer = h.dealer, deck = h.deck, state = 'done',
         outcome = h.outcome, updated_at = now()
   where user_id = auth.uid() returning * into h;

  insert into public.casino_log (user_id, game, bet, delta, detail)
    values (auth.uid(), 'blackjack', h.bet, delta, jsonb_build_object('outcome', h.outcome));

  select * into w from public.wallets where user_id = auth.uid();
  return public.bj_public(h, true) || jsonb_build_object('ok', true, 'chips', w.chips);
end $$;

create or replace function public.bj_current()
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare h public.bj_hands;
begin
  select * into h from public.bj_hands where user_id = auth.uid();
  if h is null then return jsonb_build_object('ok', true, 'state', 'none'); end if;
  return public.bj_public(h, h.state = 'done') || jsonb_build_object('ok', true);
end $$;

-- ============================================================================
--  cash out - chips become study coins
--  Only this direction exists. Study coins are written by the browser, so letting
--  them buy chips would let anyone mint chips and then take them off another player.
-- ============================================================================
create or replace function public.casino_cash_out(amount bigint)
returns jsonb
language plpgsql security definer set search_path = public
as $$
declare w public.wallets; coins bigint;
begin
  w := public.wallet_row();
  if amount <= 0 then raise exception 'amount must be positive'; end if;
  if w.chips < amount then
    return jsonb_build_object('ok', false, 'reason', 'not enough chips', 'chips', w.chips);
  end if;
  coins := amount / 5;                                    -- 5 chips = 1 study coin
  if coins <= 0 then
    return jsonb_build_object('ok', false, 'reason', 'need at least 5 chips', 'chips', w.chips);
  end if;
  update public.wallets set chips = chips - (coins * 5), updated_at = now()
   where user_id = auth.uid() returning * into w;
  insert into public.casino_log (user_id, game, bet, delta, detail)
    values (auth.uid(), 'cashout', 0, -(coins * 5), jsonb_build_object('coins', coins));
  return jsonb_build_object('ok', true, 'coins', coins, 'chips', w.chips);
end $$;

-- ============================================================================
--  permissions - only signed-in users, and only through these functions
-- ============================================================================
revoke all on function public.wallet_row() from public, anon;
do $$
declare f text;
begin
  foreach f in array array['casino_state()','casino_grant()','casino_roulette(bigint,text)',
                           'bj_start(bigint)','bj_hit()','bj_stand()','bj_current()',
                           'casino_cash_out(bigint)']
  loop
    execute format('revoke all on function public.%s from public, anon;', f);
    execute format('grant execute on function public.%s to authenticated;', f);
  end loop;
end $$;

notify pgrst, 'reload schema';

-- ============================================================================
--  verify - expect wallets/bj_hands/casino_log with rowsecurity = true,
--  and bj_hands with zero policies (nobody reads the shoe)
-- ============================================================================
select tablename, rowsecurity,
       (select count(*) from pg_policies p where p.tablename = t.tablename) as policies
  from pg_tables t
 where schemaname = 'public' and tablename in ('wallets','bj_hands','casino_log')
 order by tablename;
