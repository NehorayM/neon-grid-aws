-- ============================================================================
--  Neon Grid — add usernames to an existing project
--  Run this once in: Supabase dashboard → SQL Editor → New query → Run
--  Safe to run more than once. It does not touch your existing rows or policies.
-- ============================================================================

-- 1. the column itself
alter table public.profiles
  add column if not exists username text;

-- 2. case-insensitive uniqueness, so "GigaChad" and "gigachad" can't both exist.
--    The app never reads other people's rows to check availability — it just tries to
--    save and treats the error this index raises as "that name is taken", which keeps
--    row-level security strict.
create unique index if not exists profiles_username_lower_key
  on public.profiles (lower(username));

-- 3. shape: 3–20 characters, letters, numbers and underscore only
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'profiles_username_shape') then
    alter table public.profiles
      add constraint profiles_username_shape
      check (username is null or username ~ '^[A-Za-z0-9_]{3,20}$');
  end if;
end
$$;

-- 4. let PostgREST notice the new column straight away instead of waiting for its
--    schema cache to refresh on its own
notify pgrst, 'reload schema';

-- ============================================================================
--  Verify — this should return one row: username | text
-- ============================================================================
select column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name   = 'profiles'
  and column_name  = 'username';
