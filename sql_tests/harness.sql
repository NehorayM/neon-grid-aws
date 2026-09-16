-- Minimal stand-in for the parts of Supabase the casino SQL depends on, so the real
-- files can be executed unmodified against a plain Postgres.
create extension if not exists pgcrypto;

create schema if not exists auth;

create table if not exists auth.users (
  id uuid primary key default gen_random_uuid(),
  email text
);

-- auth.uid() reads a session GUC, which is how we impersonate each player in tests
create or replace function auth.uid() returns uuid
language plpgsql stable as $$
begin
  return nullif(current_setting('test.uid', true), '')::uuid;
exception when others then return null;
end $$;

do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated; end if;
end $$;

-- the app's own profiles table (created by supabase_setup.sql in production)
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  profile jsonb not null default '{}'::jsonb,
  course jsonb,
  username text,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

-- 'notify pgrst' is a no-op outside Supabase but the files issue it; nothing to stub.
