-- exam_history: each player sees and changes only their own exams
\set ON_ERROR_STOP 0
insert into auth.users(id,email) values
  ('00000000-0000-0000-0000-00000000000a','a@x'),('00000000-0000-0000-0000-00000000000b','b@x')
  on conflict do nothing;
set role authenticated;
select set_config('test.uid','00000000-0000-0000-0000-00000000000a',false);
insert into public.exam_history(user_id,hid,exam) values ('00000000-0000-0000-0000-00000000000a','h1','{"sc":700}');
do $$ begin
  if (select count(*) from public.exam_history)=1 then raise notice 'PASS a can write and read its own exam';
  else raise notice 'FAIL a cannot see its own exam'; end if;
end $$;
-- a cannot write a row for b
do $$ begin
  begin
    insert into public.exam_history(user_id,hid,exam) values ('00000000-0000-0000-0000-00000000000b','h2','{}');
    raise notice 'FAIL a wrote a row for b';
  exception when others then raise notice 'PASS a cannot write a row for b';
  end;
end $$;
-- upsert updates in place
insert into public.exam_history(user_id,hid,exam) values ('00000000-0000-0000-0000-00000000000a','h1','{"sc":820}')
  on conflict (user_id,hid) do update set exam=excluded.exam;
do $$ begin
  if (select (exam->>'sc')::int from public.exam_history where hid='h1')=820 then raise notice 'PASS an edit updates the same row';
  else raise notice 'FAIL the edit did not land'; end if;
end $$;
-- b sees nothing of a's
select set_config('test.uid','00000000-0000-0000-0000-00000000000b',false);
do $$ begin
  if (select count(*) from public.exam_history)=0 then raise notice 'PASS b cannot see a''s exams';
  else raise notice 'FAIL b can see a''s exams'; end if;
end $$;
do $$ declare n int; begin
  update public.exam_history set exam='{"sc":100}' where hid='h1';
  get diagnostics n = row_count;
  if n=0 then raise notice 'PASS b cannot change a''s exam'; else raise notice 'FAIL b changed a''s exam'; end if;
end $$;
-- shape guards
select set_config('test.uid','00000000-0000-0000-0000-00000000000a',false);
do $$ begin
  begin
    insert into public.exam_history(user_id,hid,exam) values ('00000000-0000-0000-0000-00000000000a','bad id!','{}');
    raise notice 'FAIL a malformed id was accepted';
  exception when others then raise notice 'PASS a malformed id is refused';
  end;
end $$;
reset role;
