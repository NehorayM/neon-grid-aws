-- Neon Grid — Supabase setup
-- Run this once in your project's SQL editor (Supabase dashboard → SQL Editor → New query).
--
-- Passwords are never stored here. Supabase Auth owns them in auth.users, hashed with
-- bcrypt, along with sessions and password resets. This table only holds game progress.
--
-- The anon key shipped in the page is a PUBLISHABLE key: it identifies the project, not a
-- user. Everything below depends on row-level security to keep one player out of another
-- player's row, so do not skip the policies.

-- ---------------------------------------------------------------- progress table
create table if not exists public.profiles (
  id          uuid primary key references auth.users (id) on delete cascade,
  profile     jsonb       not null default '{}'::jsonb,   -- the P object (xp, coins, seen, badges…)
  course      jsonb,                                      -- an in-flight Subject Course, or null
  updated_at  timestamptz not null default now(),
  created_at  timestamptz not null default now()
);

comment on table public.profiles is 'Per-user Neon Grid progress. One row per auth user.';

-- ---------------------------------------------------------------- row level security
-- Without this, the publishable key would let anyone read every row.
alter table public.profiles enable row level security;

drop policy if exists "read own profile"   on public.profiles;
drop policy if exists "insert own profile" on public.profiles;
drop policy if exists "update own profile" on public.profiles;
drop policy if exists "delete own profile" on public.profiles;

create policy "read own profile"   on public.profiles
  for select using (auth.uid() = id);

create policy "insert own profile" on public.profiles
  for insert with check (auth.uid() = id);

create policy "update own profile" on public.profiles
  for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "delete own profile" on public.profiles
  for delete using (auth.uid() = id);

-- ---------------------------------------------------------------- housekeeping
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_touch_updated_at on public.profiles;
create trigger profiles_touch_updated_at
  before update on public.profiles
  for each row execute function public.touch_updated_at();

-- Give every new account an empty row so the client never has to special-case "first save".
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, profile)
  values (new.id, '{}'::jsonb)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------- verify
-- Expect four policies and rowsecurity = true.
-- select tablename, rowsecurity from pg_tables where tablename = 'profiles';
-- select policyname, cmd from pg_policies where tablename = 'profiles';
