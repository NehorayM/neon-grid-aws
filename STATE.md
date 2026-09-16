# Where this project stands

Live: **https://nehoraym.github.io/neon-grid-aws/** · repo `NehorayM/neon-grid-aws` (public, GitHub Pages from `main`)

`index.html` is the whole app — one self-contained file, ~3.9 MB (about 1 MB gzipped over the wire),
including the question bank and every subject's teaching material.
Push to `main` and Pages redeploys in about a minute.

## What exists

| Part | State |
|---|---|
| Study guide `AWS-SAA-C03-Combined.md` | Two sources merged into one 24-topic guide |
| Practice, mock, exam, flashcards | Original app, untouched |
| **Learn a Subject** | The main mode. 23 subjects, 97 parts, 388 check questions, 230 exam questions — all authored, none drawn from the bank |
| **Answer explanations** | Bank questions: glossary-derived. Learn mode: authored per option |
| **Accounts** | Supabase Auth, optional (guests still work). Username, cross-device sync, merge-best on first sign-in |
| **Casino** | Chips (server-owned). Shared roulette on a 25s clock, blackjack vs the house, question duel |

## How the Learn mode works

For each subject: read a part → answer 4 questions written for that part → below 75% the part is
read again with the missed points listed, above it the next part opens → after the last part, the
full written summary of the subject → then a ten-question exam built only from those parts, every
question explained option by option. Everything is timed: a per-part clock against a target, a
total subject clock, and a 15-minute countdown on the exam.

## Changing the content

Authoring lives in `learn_src/s??_*.py`, one file per subject, each exporting `SUBJECT`.

```bash
python3 build_learn.py      # validates every subject, then injects it into index.html
```

The build **refuses** to write anything that would reach a learner broken:

- a question with no correct answer, duplicate options, or every option marked correct
- a check question whose key terms never appear in the part it claims to test
- an exam question not tagged to a part of that subject, or a part the exam never touches
- a part with no table, flow, split or decision tree, or with no key/trap callout
- a recap with fewer than two tables, a body under 900 characters, unbalanced `**`, placeholder text
- answers clustering on one option position — it cycles them deterministically at build time

Block types available to an author: `h p list steps table flow split key trap note code dtree`.

## Changing the engine

The Learn mode's source is kept outside the big file and stitched in:

```bash
python3 inject_learn.py     # learn_styles.css + learn_screens.html + learn_engine.js -> index.html
```

It also checks that every `$('id')` the engine touches exists in the markup.
The CSS is injected last in the stylesheet on purpose — source order decides ties.

## Testing — use it, do not eyeball

```bash
./sql_tests/run.sh          # docker Postgres, installs all SQL, plays the games, 39 assertions
python3 -m http.server 8765 # then http://localhost:8765/index.html?test=1
```

In the browser, with the page visible:

```js
eval(await (await fetch('/qa_learn.js')).text());
await QA_LEARN();     // walks every subject: read, answer, fail, re-read, pass, summary, exam, result
QA_TAPS();            // every control is what a finger would actually land on
```

`QA_LEARN` drives the real screens by clicking real elements — 11,536 assertions across the 23
subjects at the last full run, all passing. It includes a deliberate failure run to prove the
gate holds, and a partial run to prove scoring is not always 100%. Batch it with
`QA_LEARN({secs:[0,1,2], extra:false})` to stay under the tool timeout.

Three SQL bugs reached the user before `sql_tests` existed, including one that could pay a duel
pot twice. Anything touching `supabase_*.sql` should run it first.

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

## Older content pipeline

`AWS-SAA-C03-Combined.md` still feeds the reference material shown inside the Learn mode's final
summary (the two collapsible sections at the bottom of it).

```bash
python3 build_course_data.py      # subject briefings and explanation data
python3 build_subject_content.py  # blueprint, trade-offs, traps, limits
```

## Known gaps / next up

- **Multiplayer blackjack tables** — asked for, not built. Seats, turn order, a timer for an
  idle player, dealer acting after everyone. The largest remaining piece.
- Hard limits are authored for 11 of 23 subjects in `subject_content.json`; the rest render
  "not yet authored" in the reference section rather than inventing AWS facts.
- Study coins are still written by the browser. Chips are server-owned; the coins→chips
  buy-in is capped at 1,000/day precisely because the server cannot verify study coins.

## Things worth not relearning

- `.screen` has `z-index:10` and forms a stacking context, so a `.backbtn` inside it can never
  rise above `#topbar`. The bar passes clicks through its empty areas; do not undo that.
- A `<div>` left unclosed inside a `<button>` silently reparents everything after it — that is
  how the coins vanished from the top bar once.
- A local `const` named the same as a global function shadows it for the whole function body,
  including lines above the declaration. `const go = $('lrnMapGo')` broke `go('learnMapScreen')`.
- Programmatic `.click()` sails through dead buttons. Hit-test with `document.elementFromPoint`
  after `scrollIntoView`, which is what `QA_TAPS` does.
- Supabase renamed the keys: **Publishable** (`sb_publishable_`) is the old anon key.
