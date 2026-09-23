-- Neon Grid — exam history, one row per exam
-- Run this once in the Supabase SQL editor (Dashboard → SQL Editor → New query). Safe to run
-- again: every statement is guarded.
--
-- Each exam you submit is kept as its own row: the questions, every answer, the score. A
-- change to one exam (a redo, an edit, finishing it later) updates that one row straight away,
-- instead of travelling inside the whole profile. The app still keeps a copy in the profile
-- too, so nothing is lost if this table has not been created yet.
--
-- Row-level security: a player can read and write only their own rows. The publishable key in
-- the page identifies the project, not a user, so do not skip the policies.

create table if not exists public.exam_history (
  user_id     uuid        not null references auth.users (id) on delete cascade,
  hid         text        not null,
  exam        jsonb       not null,
  updated_at  timestamptz not null default now(),
  primary key (user_id, hid)
);

comment on table public.exam_history is 'Per-user Neon Grid exam history. One row per submitted exam.';

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'exam_history_hid_shape') then
    alter table public.exam_history
      add constraint exam_history_hid_shape check (hid ~ '^[A-Za-z0-9_-]{1,40}$');
  end if;
  -- one exam is ~3 KB; anything near this is not an exam
  if not exists (select 1 from pg_constraint where conname = 'exam_history_size') then
    alter table public.exam_history
      add constraint exam_history_size check (pg_column_size(exam) < 32768);
  end if;
end
$$;

alter table public.exam_history enable row level security;

drop policy if exists "read own exams"   on public.exam_history;
drop policy if exists "insert own exams" on public.exam_history;
drop policy if exists "update own exams" on public.exam_history;
drop policy if exists "delete own exams" on public.exam_history;

create policy "read own exams"   on public.exam_history for select using (auth.uid() = user_id);
create policy "insert own exams" on public.exam_history for insert with check (auth.uid() = user_id);
create policy "update own exams" on public.exam_history for update
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "delete own exams" on public.exam_history for delete using (auth.uid() = user_id);

grant select, insert, update, delete on public.exam_history to authenticated;

drop trigger if exists exam_history_touch on public.exam_history;
create or replace function public.exam_history_touch() returns trigger
language plpgsql as $$ begin new.updated_at = now(); return new; end; $$;
create trigger exam_history_touch before update on public.exam_history
  for each row execute function public.exam_history_touch();

notify pgrst, 'reload schema';
