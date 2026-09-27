#!/usr/bin/env bash
# Run the casino SQL against a throwaway Postgres and assert the games behave.
# Needs docker. Usage: ./sql_tests/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
NAME=ngsqltest

cleanup(){ docker rm -f $NAME >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup

docker run -d --rm --name $NAME -e POSTGRES_PASSWORD=test -e POSTGRES_DB=neon \
  postgres:15-alpine >/dev/null
until docker exec $NAME pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done

for f in sql_tests/harness.sql supabase_casino.sql supabase_casino_v2.sql supabase_duel.sql supabase_duel_v2.sql supabase_exam_history.sql supabase_leaderboard.sql supabase_tournament.sql sql_tests/suite.sql sql_tests/exam_history_suite.sql sql_tests/duel_v2_suite.sql sql_tests/leaderboard_suite.sql sql_tests/tournament_suite.sql; do
  docker cp "$f" $NAME:/tmp/ >/dev/null
done

for f in harness.sql supabase_casino.sql supabase_casino_v2.sql supabase_duel.sql supabase_duel_v2.sql supabase_exam_history.sql supabase_leaderboard.sql supabase_tournament.sql; do
  echo "--- installing $f"
  docker exec $NAME psql -U postgres -d neon -q -v ON_ERROR_STOP=1 -f /tmp/$f >/dev/null
done

echo "--- installing supabase_duel_v2.sql again (it says it is safe to re-run)"
docker exec $NAME psql -U postgres -d neon -q -v ON_ERROR_STOP=1 -f /tmp/supabase_duel_v2.sql >/dev/null

echo "--- playing"
docker exec $NAME psql -U postgres -d neon -f /tmp/suite.sql 2>&1 \
  | grep -E "PASS|FAIL|ALL CHECKS" | sed 's/^psql:[^ ]* //;s/^NOTICE:  //'
echo "--- exam history"
docker exec $NAME psql -U postgres -d neon -f /tmp/exam_history_suite.sql 2>&1 \
  | grep -E "PASS|FAIL" | sed 's/^psql:[^ ]* //;s/^NOTICE:  //'
echo "--- duel v2"
docker exec $NAME psql -U postgres -d neon -f /tmp/duel_v2_suite.sql 2>&1 \
  | grep -E "PASS|FAIL|ERROR" | sed 's/^psql:[^ ]* //;s/^NOTICE:  //'
echo "--- leaderboard"
docker exec $NAME psql -U postgres -d neon -f /tmp/leaderboard_suite.sql 2>&1 \
  | grep -E "PASS|FAIL|ERROR" | sed 's/^psql:[^ ]* //;s/^NOTICE:  //'
echo "--- tournament"
docker exec $NAME psql -U postgres -d neon -f /tmp/tournament_suite.sql 2>&1 \
  | grep -E "PASS|FAIL|ERROR" | sed 's/^psql:[^ ]* //;s/^NOTICE:  //'
echo "--- tournament: two starts at the same instant"
docker exec $NAME psql -U postgres -d neon -qAt -c "delete from public.tournaments; insert into public.wallets (user_id, chips) values ('11111111-1111-4111-8111-111111111111', 1000) on conflict (user_id) do update set chips = 1000;" >/dev/null
for n in 1 2 3 4; do
  docker exec $NAME psql -U postgres -d neon -qAt -c "select set_config('test.uid','11111111-1111-4111-8111-111111111111',false); select pg_sleep(0.3); select public.tourney_start(250)->>'ok';" >/dev/null 2>&1 &
done
wait
OPEN=$(docker exec $NAME psql -U postgres -d neon -qAt -c "select count(*) from public.tournaments where status='active';")
CHIPS=$(docker exec $NAME psql -U postgres -d neon -qAt -c "select chips from public.wallets where user_id='11111111-1111-4111-8111-111111111111';")
if [ "$OPEN" = "1" ] && [ "$CHIPS" = "750" ]; then echo "PASS  four starts at once: one tournament, one buy-in taken"; else echo "FAIL  four starts at once: $OPEN open, $CHIPS chips left"; fi
