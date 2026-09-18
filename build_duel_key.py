#!/usr/bin/env python3
"""Rewrite the duel's server-side answer key from the current question bank.

The duel never sends answers to the browser — the client posts a letter and the
Postgres function checks it against public.answer_key. That table therefore has
to hold the same indices as the #data blob in index.html, so this regenerates
the one INSERT line whenever the bank changes.
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SQL = HERE / "supabase_duel.sql"
PAGE = HERE / "index.html"

LINE = re.compile(
    r"insert into public\.answer_key \(id, ans\) values \(1, '.*?'::jsonb\)", re.S)


def main():
    page = PAGE.read_text(encoding="utf-8")
    blob = re.search(r'<script id="data" type="application/json">(.*?)</script>',
                     page, re.S).group(1).replace("<\\/", "</")
    qs = json.loads(blob)["questions"]
    key = {str(i): q["a"] for i, q in enumerate(qs)}
    # the SQL literal is single-quoted, so a stray quote would end it early
    payload = json.dumps(key, separators=(",", ":"))
    assert "'" not in payload, "an answer letter contains a quote"

    s = SQL.read_text(encoding="utf-8")
    assert LINE.search(s), "the answer_key INSERT was not found"
    s = LINE.sub(lambda _:
                 "insert into public.answer_key (id, ans) values (1, '%s'::jsonb)" % payload,
                 s, count=1)
    SQL.write_text(s, encoding="utf-8")

    # the self-check at the bottom of the file states the expected count
    note = re.compile(r"-- expect: 1 key row, \d+ questions in it")
    assert note.search(s), "the verify comment was not found"
    s2 = note.sub("-- expect: 1 key row, %d questions in it" % len(key), s, count=1)
    SQL.write_text(s2, encoding="utf-8")

    print(f"answer_key now holds {len(key)} questions ({len(payload)/1024:.1f} KB of JSON)")


if __name__ == "__main__":
    main()
