# Where this project stands

Live: **https://nehoraym.github.io/neon-grid-aws/** · repo `NehorayM/neon-grid-aws` (public, GitHub Pages from `main`)

`index.html` is the whole app — one self-contained file, ~2.9 MB (well under 1 MB gzipped over the wire),
including the question bank and every subject's teaching material.
Push to `main` and Pages redeploys in about a minute.

## What exists

| Part | State |
|---|---|
| Study guide `AWS-SAA-C03-Combined.md` | Two sources merged into one 24-topic guide |
| **Question bank** | 1,201 questions, every answer read and verified one by one. The old 2,502-question bank is gone |
| **Practice Exams** | The bank cut into 19 numbered papers — 65 questions each (the last holds the remaining 31), 170 minutes, countdown, score, CSV export |
| Practice, mock, exam, flashcards | Original app, still running on the new bank |
| **Learn a Subject** | The main mode. 23 subjects, 97 parts, 388 check questions, 230 exam questions — all authored, none drawn from the bank |
| **Answer explanations** | Bank questions: glossary-derived. Learn mode: authored per option |
| **Accounts** | Supabase Auth, optional (guests still work). Username, cross-device sync, merge-best on first sign-in |
| **Casino** | Chips (server-owned). Shared roulette on a 25s clock, blackjack vs the house, question duel |

## The look

Feedback in September 2026 was that the interface read as dense, harsh and machine-made.
`restyle.py` and `restyle2.py` were the one-shot passes that fixed it; `index.html` is the
source of truth now, so change the CSS there rather than re-running them.

The rules the design follows:

- **Surfaces are neutral.** `--surface`, `--line` and `--panel` are white at 3–9% alpha and
  never tinted with the accent. `applyTheme` used to derive them from the theme's cyan, which
  washed every panel in colour — that is why it looked synthetic.
- **One accent does the work.** `--cyan` is the primary; `--lime`, `--gold` and `--red` only
  carry meaning (pass, attention, fail). Sector cards share the accent instead of generating
  a hue each, which had turned the grid into a colour wheel.
- **Every palette sits in the same register** — mid lightness, low saturation. That holds for
  the ten shop themes too, so buying one changes the mood, not the volume.
- **No glow.** No text-shadow, no coloured box-shadow, no rotating background sweep. Progress
  bars are one flat colour, not a two-colour gradient.
- **Weights stop at 650.** 800 and 900 everywhere is what made the type shout.
- **Sticky footers are opaque** with a short fade above them; they used to fade from
  transparent and let the next paragraph read straight through the button.

The reaction to that pass was "too clean, not interesting". `character.py` put the personality
back without putting the noise back — decoration that carries meaning:

- **An emoji per sector**, chosen for the service (`SEC_EM`): 🔑 IAM, 🪣 S3, 🐳 containers,
  🕸️ VPC. It rides along in the sector grid, the Learn subject list and the quiz header.
- **The four exam domains each own a colour** (`DOMAIN_COL`). Every sector card wears its
  domain's stripe and states its weight — "PERFORMING · 24%" — so the grid teaches the
  blueprint instead of just listing topics.
- **Practice Exams** shows attempted/passed/best, and each paper gets its score, a bar and
  green-or-amber depending on whether it cleared 72%.
- **Hebrew encouragement** (`HEB`, `hebLine`, `hebHTML`) at the four places a learner stops:
  today's line on the home screen (the same all day, seeded by the date), the beat after an
  answer, the end of a set, the end of an exam or a subject. Lines are wrapped in
  `.heb[dir=rtl]` with `unicode-bidi:isolate` so their punctuation cannot reorder the Latin
  text around them.

**Anything under the `LEARN:` markers must be changed in `learn_engine.js`, `learn_screens.html`
or `learn_styles.css`, not in `index.html`** — the next `inject_learn.py` run overwrites it.
That caught this pass twice: the subject emoji and the palette conversion both had to be
redone in the source files.

`QA_UI()` guards the layout side of this: 32 screens at 375px and 1024px, no sideways scroll,
no clipped text, no covered back buttons, no tap target under 24px.

## The question bank

Every question comes from `qsrc/aws_saa_questions_full.csv`, an OCR'd exam dump kept in the repo
so the pipeline reruns without the original download. Nothing else feeds the bank.

```bash
python3 clean_csv.py      # CSV  -> qsrc/questions_clean.json   (repairs the OCR damage)
python3 build_bank.py     # + qsrc/answers.py -> qsrc/bank.json (assigns each question a sector)
python3 inject_bank.py    # qsrc/bank.json -> the #data blob in index.html
python3 build_duel_key.py # the same answers -> the server-side key in supabase_duel.sql
```

`clean_csv.py` undoes what the scan did to the text: glyph lookalikes (`©`→C, `£`/`€`/`3`→E),
options merged into one cell because their letter marker was lost, hyphens inside words. What it
cannot repair it refuses to guess at — 20 items are dropped by number with the reason written
next to them, including three CompTIA Security+ questions the source had mixed in.

`qsrc/answers.py` is the answer key: `V` maps item number to answer letters, `NOTES` says why an
entry differs from the file or why a close call went the way it did. Every one of the 1,201
questions was read against its options. 863 arrived with an answer in the CSV and **64 of those
were wrong** — those carry a note starting "Changed from the file's …". The other 338 had no
answer in the source at all.

The bank is index-keyed, so `index.html` carries a `BANKV` stamp; when it changes the page clears
`seen`, `wrong`, `marks` and the spaced-repetition schedule, and keeps XP, coins, badges and the
readiness history.

**Deploy the page and the SQL together.** The duel picks question ids server-side, so pushing a
new bank without re-running `supabase_duel.sql` leaves duels handing out ids that no longer exist.

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

eval(await (await fetch('/qa_bank.js')).text());
await QA_BANK();      // the bank, the 19 papers, a full 65-question exam, the CSV, every other mode
await QA_UI();        // all 32 screens: sideways scroll, clipped text, tap size, covered back buttons
```

`QA_BANK` last ran at 19,003 assertions, all passing — it answers a whole paper through the real
option buttons, flags as it goes, lets one exam run out of time, abandons another, and checks the
practice controls come back afterwards. `QA_UI` reports nothing at 375px and at 1024px.

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

- `supabase_duel.sql` must be re-run in the SQL editor whenever the bank changes; the page alone
  is not enough (see above).
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
