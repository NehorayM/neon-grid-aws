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

for f in sql_tests/harness.sql supabase_casino.sql supabase_casino_v2.sql supabase_duel.sql supabase_duel_v2.sql supabase_exam_history.sql sql_tests/suite.sql sql_tests/exam_history_suite.sql sql_tests/duel_v2_suite.sql; do
  docker cp "$f" $NAME:/tmp/ >/dev/null
done

for f in harness.sql supabase_casino.sql supabase_casino_v2.sql supabase_duel.sql supabase_duel_v2.sql supabase_exam_history.sql; do
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
