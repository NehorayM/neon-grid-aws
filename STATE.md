# Where this project stands

Live: **https://nehoraym.github.io/neon-grid-aws/** · repo `NehorayM/neon-grid-aws` (public, GitHub Pages from `main`)

`index.html` is the whole app — one self-contained file, ~3.2 MB, including the question bank.
Push to `main` and Pages redeploys in about a minute.

## What exists

| Part | State |
|---|---|
| Study guide `AWS-SAA-C03-Combined.md` | Two sources merged into one 24-topic guide |
| Practice, mock, exam, flashcards | Original app, untouched |
| **Subject Course** | 5 phases, 78 min: blueprint → drill (8/10 gate) → deep dive → 20-question sim → rationale recap. Resumes from `localStorage` |
| **Answer explanations** | After every answer: correct option, why it fits, why each distractor doesn't, exam cue. ~86% coverage, glossary-derived |
| **Accounts** | Supabase Auth, optional (guests still work). Username, cross-device sync, merge-best on first sign-in |
| **Casino** | Chips (server-owned). Shared roulette on a 25s clock, blackjack vs the house, question duel |

## Supabase

Project `rlbgbxgtaqvxwvskpblg`. The publishable key is in the `SUPA` block in `index.html` —
that is fine, it is meant to ship. **Row-level security is what makes it safe**; verified with
an anonymous insert returning `42501`.

SQL files, run in this order in the SQL editor:

1. `supabase_setup.sql` — profiles, RLS, username column
2. `supabase_casino.sql` — wallets, blackjack, cash-out
3. `supabase_casino_v2.sql` — shared roulette, chip buy-in, retention sweeps
4. `supabase_duel.sql` — duels + the server-side answer key (~47 KB)

All are idempotent. Never put the `sb_secret_` key in the page.

## Testing — use it, do not eyeball SQL

```bash
./sql_tests/run.sh          # docker Postgres, installs all SQL, plays the games, 39 assertions
```

Three SQL bugs reached the user before this existed, including one that could pay a duel pot
twice. Anything touching `supabase_*.sql` should run this first.

For the app itself: serve locally and drive it in a browser with `?test=1`, which exposes
`window.__t`. Check clicks with `document.elementFromPoint` rather than `.click()` — a whole
class of dead buttons hid behind programmatic clicks.

```bash
python3 -m http.server 8765      # then http://localhost:8765/index.html?test=1
```

## Content pipeline

`AWS-SAA-C03-Combined.md` is the source of truth for course text.

```bash
python3 build_course_data.py      # course reads + explanation data → injected into index.html
python3 build_subject_content.py  # blueprint/tradeoffs/traps/limits → injected into index.html
```

Both rewrite `index.html` in place. Coverage is deliberately honest: subjects with nothing
authored render "not yet authored" instead of invented AWS facts.

## Known gaps / next up

- **Multiplayer blackjack tables** — asked for, not built. Seats, turn order, a timer for an
  idle player, dealer acting after everyone. The largest remaining piece.
- **Per-question distractor rationale** — the schema and UI exist (`question.x` or
  `question_rationale.json`); no question has authored rationale yet, so it falls back to
  glossary-derived notes.
- **Hard limits** — 12 of 23 subjects have none, because the study guide states none.
- Study coins are still written by the browser. Chips are server-owned; the coins→chips
  buy-in is capped at 1,000/day precisely because the server cannot verify study coins.

## Things worth not relearning

- `.screen` has `z-index:10` and forms a stacking context, so a `.backbtn` inside it can never
  rise above `#topbar`. The bar passes clicks through its empty areas; do not undo that.
- A `<div>` left unclosed inside a `<button>` silently reparents everything after it — that is
  how the coins vanished from the top bar once.
- Supabase renamed the keys: **Publishable** (`sb_publishable_`) is the old anon key.
