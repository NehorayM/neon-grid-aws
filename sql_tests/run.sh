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

for f in sql_tests/harness.sql supabase_casino.sql supabase_casino_v2.sql supabase_duel.sql sql_tests/suite.sql; do
  docker cp "$f" $NAME:/tmp/ >/dev/null
done

for f in harness.sql supabase_casino.sql supabase_casino_v2.sql supabase_duel.sql; do
  echo "--- installing $f"
  docker exec $NAME psql -U postgres -d neon -q -v ON_ERROR_STOP=1 -f /tmp/$f >/dev/null
done

echo "--- playing"
docker exec $NAME psql -U postgres -d neon -f /tmp/suite.sql 2>&1 \
  | grep -E "PASS|FAIL|ALL CHECKS" | sed 's/^psql:[^ ]* //;s/^NOTICE:  //'
