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
| **Practice Exams** | The **Exam** tab. 19 numbered papers — 65 questions each (the last holds 31), **90 seconds a question**, score, CSV export. A paper you leave is kept and offered back; exams 1–10 brief you before each question and explain every answer; any question's stem can be read aloud on request |
| **Study** | The **Study** tab. The whole syllabus as 13 readable chapters, 76 topics, with authored comparison tables, decision trees and flows, and 3 checks per chapter |
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

**Anything under a `LEARN:` or `STUDY:` marker must be changed in its source file, not in
`index.html`** — the next `inject_learn.py` / `inject_study.py` run overwrites it. This has bitten
three times now: the subject emoji, the palette conversion, and a whole block of exam CSS that
`exam_extras.py` had anchored on a selector inside `STUDY:CSS`. Exam styling lives in its own
`EXAM:CSS` block above the STUDY markers for exactly that reason.

**`overflow:hidden` on a direct child of `.screen` needs `flex:none`.** It zeroes the flex item's
automatic minimum size, so the panel collapses to nothing while still containing its content.
It has happened twice — the accent cards and the exam statistics panel. `QA_UI()` now fails on
any screen child that has content but no height.

`QA_UI()` guards the layout side of this: 32 screens at 375px and 1024px, no sideways scroll,
no clipped text, no covered back buttons, no tap target under 24px.

## Study mode

The **Study** tab is the reference half of the app: read the syllabus, in any order, nothing
locked. Learn mode teaches and gates; Study mode just explains.

```bash
python3 build_study.py    # qsrc/aws-saa-study-notes-english.md -> the #studydata blob
python3 inject_study.py   # screens, styles and engine into index.html (idempotent)
```

`build_study.py` carries the prose across untouched and adds what prose cannot: 81 authored
comparison tables, decision trees, flows and must-know / exam-trap callouts, keyed by topic in
`EXTRAS`, plus three multiple-choice checks per chapter in `QUIZ`. Every `##` in the notes must
appear in `SECTION_CH` or the build refuses, so a topic can never quietly go missing.

Blocks render through the Learn mode's `blocksHTML`, so both modes share one renderer and one
visual language. Chapters are coloured by the exam domain they mostly serve.

## Inside an exam

- **Leaving keeps it.** `simPersist()` writes the question, the answers, the flags and the
  *remaining* time to `P.simSave` on every pick, flag and move. The clock is stored as time
  left rather than as a deadline, so an exam you come back to tomorrow resumes where it
  stopped instead of having expired overnight. The Practice Exams screen shows a Resume card;
  submitting or starting another paper clears the save. Quitting a paper now lands on that
  screen rather than on Home, so the save is where you left off.
- **Read aloud.** 🔊 Read reads the current question; while it is talking the button is
  ⏹ Stop and a tap stops it. That is the whole button — no auto-read, no remembered
  preference, and nothing ever reads itself. Moving on cancels a reading in progress.
  **It reads the stem only**, not the options: they are on the screen, and a reader asked
  for them not to be spoken.
  The button follows an internal `ttsOn` flag rather than `speechSynthesis.speaking`, which
  lags behind `cancel()` in some browsers, and `u.onend`/`u.onerror` put it back. A browser
  with no voices installed fires `onerror: synthesis-failed`, so the button never lies about
  reading; it also accepts `speak()` silently in some builds, so the page checks 400ms later
  and says so rather than leaving you wondering.
- **Ninety seconds a question.** `SIM_QSEC=90`. The top clock counts the current question
  down, not the whole paper, and the bar above the question drains with it. When it reaches
  zero the paper moves to the next question whether or not anything was answered — a blank
  question scores as wrong, and the clock never waits for a right answer. On the last question
  it lands on the review screen instead.
  What is left is kept per question in `sim.qt`, so going back to a question gives back the
  time it had and the save survives leaving and resuming. It does not run while the app is in
  the background or while you are on the review screen. A question whose time is gone can
  still be opened and answered from the review list — it shows an empty clock rather than
  bouncing you straight back out, which is what `if(simQLeft<=0){ simQStop(); return; }` at
  the top of `simQTick` is for.
  On papers 1–10 the same 90 seconds covers reading the feedback, so it can move on mid-read.
  The whole-paper budget is `simBudget(n) = ceil(n * 90 / 60)` — 98 minutes for 65 questions,
  47 for the short one — so the two clocks agree instead of contradicting each other. It is
  still enforced by `simCheckTime`, and the review screen is where it is shown.
- **Papers 1–10 teach; 11–19 test.** On the first ten, a collapsible panel above each question
  (`buildBriefing()`) names the services it turns on, the ones it name-drops as distractors and
  how the exam phrases the ask — capped at four concepts and three distractors. And the moment
  you commit the required number of picks, the question **settles**: the options lock, right and
  wrong are marked, and `renderExplain()` opens underneath with what you picked, the correct
  answer, why it fits and what each other option actually does. The strip then reads
  "12 / 65 answered · 9/12 right so far". Papers 11–19 say nothing until you submit, and you can
  still change an answer there — that is what a real exam feels like.
- **A line that knows where you are.** Sixty-five Hebrew one-liners, one per position in a
  paper, each naming the number you just reached ("ארבעים ושתיים. התשובה לחיים, ליקום ולכל
  השאר. ולשאלה הזאת."). None of them hints at whether you were right, so the silent papers show
  them too — in the explanation panel on 1–10, as a toast on 11–19. Past 65 it falls back to a
  generated line.
- **174 questions carry the note written when their answer was verified**, and that note leads
  the explanation panel. `build_bank.py` copies `NOTES` from `qsrc/answers.py` into the question
  as `x`; `BANKV` deliberately hashes only stems, options, answers and sections, so adding an
  explanation never throws away anyone's progress.

## Knowing how much to learn

`BANK_STATS` walks the bank once at load and reports, per subject: how many questions there
are, what share of the bank that is, roughly how many to expect in a 65-question paper, how
many of the 19 papers it turns up in, and your accuracy on it. Eight subjects appear in **all
19 papers** — RDS/Aurora/ElastiCache, S3, ELB & ASG, Serverless, VPC, SQS/SNS/Kinesis,
Containers and EBS/EFS. The Practice Exams screen carries it as a collapsible panel.

Study chapters carry the same arithmetic. `STU_SECS` maps each of the 13 chapters to the
question sectors it covers — every sector belongs to exactly one chapter, so the weights add up
to the whole bank — and each chapter card says **"16% of the exam · 192 questions · you are 64%
right on 40 of them"**. That is the number that tells you how hard to study a subject.

## Nothing costs coins

Coins still accumulate as a score, and the daily and weekly targets still pay them, but no
feature is behind a price: study cards, 50/50, skip, reward-round unlocks, every shop
consumable and upgrade, every purchasable theme and every mini-game are free. `themeOwned()`
returns true for anything without an `earn` condition — the earned themes (Crimson Core,
Platinum, Midnight Mono) are still earned by playing, because a badge is not a price.

The casino is untouched: chips are server-owned and stay that way.

## What happened to the old modes

- The **Exam ×5** drill is gone. The 65-question papers are the real exams, and two things
  called "exam" in one navigation bar was the confusion. Its badges (`Certified`,
  `Exam Machine`), its daily quest and its history log were repointed at the papers, so they
  now mean something a candidate would recognise. The Exam Pass shop item went with it.
- The **Practice** nav tab became **Study**. Sector practice itself is untouched — it is still
  reached from the sector grid, Weak spots, Review, Bookmarks and the Practice tile on home.
- A new badge, **Well Read**, lands when all 13 Study chapters have been opened.

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

`QA_BANK` last ran at 20,429 assertions, all passing — it answers a whole paper through the real
option buttons, flags as it goes, lets one exam run out of time, abandons another, and checks the
practice controls come back afterwards. `QA_UI` reports nothing at 375px and at 1024px.

`QA_LEARN` drives the real screens by clicking real elements — 11,536 assertions across the 23
subjects at the last full run, all passing. It includes a deliberate failure run to prove the
gate holds, and a partial run to prove scoring is not always 100%.

`QA_INTEG()` is the cross-feature pass. The blocks above each test one change on its own;
this one walks where the last four meet — running out of time silences the voice, a takeover
silences it too and clears the Hebrew panel behind it, taking a paper back restores the
seconds that question had left rather than a fresh 90, and a paper that was flagged, timed
out and taken over still exports. 37 assertions.

**Syntax-check a harness file before loading it.** A duplicate `const` inside one function
stopped the whole of `qa_bank.js` defining anything, and a `<script src>` fails silently — it
looked exactly like the new suite not existing. Fetch the text and `new Function(txt)` first;
it names the line.

`QA_BANK` stubs `window.speechSynthesis` to prove the read-aloud wiring — that the reading is
the position and the stem and nothing else, that the button toggles Read/Stop and resets on
`onend`, that moving on cancels it and never starts one, that practice never speaks. It cannot
prove audible output, and the preview browser has no voices installed, so the sound itself has
only been verified by reading the code path. Try it on a real phone.
Careful when faking a voice by hand: assigning a plain object to `utterance.voice` throws, the
`catch` in `ttsSpeak` swallows it, and it looks exactly like the button being broken. Give the
fake a non-`en` lang so the app leaves `voice` alone. Batch it with
`QA_LEARN({secs:[0,1,2], extra:false})` to stay under the tool timeout.

Three SQL bugs reached the user before `sql_tests` existed, including one that could pay a duel
pot twice. Anything touching `supabase_*.sql` should run it first.

## The clock is a deadline, not a count of ticks

Reported as frozen — neither the question countdown nor the paper total moving — while it
ticked correctly here. Counting interval fires is the fragile part: a throttled or suspended
timer means fewer fires, so the clock runs slow or stops while the page sits there looking
alive, and if the interval is lost nothing brings it back.

`sim.qEndAt` is now when the question runs out and `simQSync()` computes the remainder from it,
so a missed fire shows up late rather than costing a second that never returns. Time in the
background or on the review screen still must not count, so `simAway()`/`simBack()` push the
deadline out by however long that lasted instead of skipping ticks.

`clockEnsure()` replaces a dead interval. `startClock()` refuses to act while `clockIv` holds an
id, which is right until that interval stops firing — then the id is a corpse and every clock on
the page is frozen. `clockTick()` stamps `clockLast` on every fire, so a stamp older than four
seconds is proof it is not running. It is checked on focus, on visibility, and on the first tap
or key — the moments a frozen clock would be noticed anyway.

Verified by clearing every interval on the page: the clock freezes, and one tap brings it back
having caught up the time that really passed.

## What the whole paper has left

The clock showed 1:30 for the question and nothing about the paper. `simTotalLeft()` adds up
every question's own remaining seconds — 65 × 90s = **1:37:30** at the start, 64 × 90s =
**1:36:00** once the first is spent. It is a real sum, not questions-left × 90: a question you
left with thirty seconds on it still has thirty, and going back to it gives them back.

Two places show it: the top clock's second line, and a strip under the question with the time,
how many questions it covers, and a track ticked once per question (`--tick` set from
`100/simLen()`, floored at 1.6% so the ticks never collapse into a solid block) so "65 × 90
seconds" is something you can see rather than work out.

**The amber state means the paper's wall clock will bite first** — `simTimeLeft() < simTotalLeft()`
— which is the only way you get cut off with question time still on the board. The first version
compared against `questionsLeft × 90`, which goes amber the moment you spend a single second and
therefore said nothing.

## Resuming a paper

A saved run used to be offered only by one bar at the top of Practice Exams. Its own row in the
list said "Retake" like every other, and pressing it deleted the run without a word.

The row for the paper you are part way through now carries it: a ⏸ icon, a cyan edge, where you
got to, and two buttons — **↻** to start over and **Resume** to continue. It drops the stale
best-score chip while a run is open, and the words "in progress" were cut because the icon and
the colour already say it and those two words cost the text a whole line at 320px.

**Starting anything else warns first**, naming the exam and the question you were on. Nothing is
deleted on the first tap; the button reverts after four seconds if it is not answered. This used
to warn only when the run belonged to another device, which was the narrow case.

`armed()` puts `.wide` on the **button**, not on a span inside it. It was on the span, which
meant the button simply grew to fit the sentence and ran off a 320px screen — the button is the
flex child of the row, so it is the thing that has to wrap.

## The reading voice

`🗣️ Voice` on the home screen's chip row opens `voiceScreen`.

**Eight presets, not eight engine voices.** Which voices a machine has differs wildly and most
are named things like "Chrome OS US English 6", so a preset is a rate, a pitch and a purpose:
Standard, Exam Room (0.85×, an invigilator's pace), Quick Review (1.35×), Sprint (1.8×), Deep
Focus (low and steady), Bright, Night Study (quieter), Dictation (0.7× and chunked at 80 chars
so there are gaps to write in). Each carries a Hebrew second line, like the rest of the app.

**It tests every voice before offering it.** This is the point of the screen. On the reporter's
ChromeOS machine, eight of thirty-four voices report `localService: true` and never make a
sound — a plain picker would let someone choose one and get silence with no explanation.
`voiceCheckAll()` speaks a silent word through each English voice and watches for `onstart`;
anything quiet for two seconds is marked SILENT, greyed and disabled. Results cache in
`voiceProbe` for the session. "Let the browser choose" is the default and is marked SAFE.

**Each preset binds to a working voice, not just a speed.** They used to share one voice and
differ only in rate, which made them sound like one person in a hurry. Each now carries `want`,
a list of name fragments in preference order, and `voiceForPreset()` takes the first match that
is not in the Chrome OS family and not marked dead — so Invigilator and Deep Focus land on the
UK male voice, Bright and Night Study on the UK female, Sprint and Dictation on US, and Standard
deliberately asks for nothing and stays on the browser's own default. Each row shows which voice
it resolved to. Probe results persist in `P.voiceProbe`, so a device only gets tested once.

Speed and pitch sliders sit over the preset — `P.ttsRate` had been read by the speech path
since the beginning and nothing ever set it. Both are clamped (`voiceRate` 0.5–2.2,
`voicePitch` 0.4–2) and an unknown preset falls back to Standard.

**Not here, on purpose: auto-read.** It was removed on request, and a settings screen is exactly
where it would creep back in.

The watchdog's plain retry deliberately drops the chosen voice but keeps the speed — a voice is
the thing most likely to be at fault when nothing speaks; speed has never broken anything.

## Two devices, one account

The reported symptom was a desktop on Exam 1 and a phone on Exam 2. Three causes, all fixed:

1. **It only ever pushed.** `pullCloud()` ran at boot, after sign-in and on the Sync now
   button, and nowhere else. It now also pulls on `visibilitychange` and `focus`, throttled to
   one round trip per 5s.
2. **The merge always preferred this device.** `mergeProfiles(remote, local)` began
   `Object.assign({}, a, b)` with `b` = local, so every field outside `MAX_KEYS` and the
   hand-merged collections took the local value — including `simSave`, which is why the two
   could never converge. `P.at` is now stamped on every save and the later side wins the plain
   fields. `P.papers` merges too; a paper passed on the phone used to vanish on the desktop.
3. **`updated_at` was written but never compared.** Still is not — `P.at` inside the blob is
   what the merge uses, so it works without a schema change.

**An exam is owned by one device at a time.** `DEVICE_ID` lives in its own localStorage key
(`academy_device`) and deliberately **not** in `P`, because `P` is merged across devices and an
id stored there would be overwritten by the other device's copy. Every `simSave` carries
`dev`, `devKind` and `claimAt`.

The subtle part: `simSaveNewer` compares **`claimAt` first, `at` second**. `at` moves on every
ordinary save, so comparing it alone let a desktop that was merely still running win a paper
straight back off a phone that had just taken it over, and the two ping-ponged. `claimAt` is
stamped only by `simClaim()` — starting, resuming or taking over a paper — never by a routine
save. A save with no `claimAt` falls back to `at`, so rows written before this still merge.

`simOwnerCheck()` runs after every merge: if we are mid-exam and the save is no longer ours,
it stops the clock, drops `sim` and says so. Taking over uses the app's arm-then-confirm idiom
(`armed()`), as does starting a paper that would discard one open elsewhere.

While an exam is actually running, `simWatchOwner()` re-checks every 30s. Focus is the right
trigger in general but useless for the reported case — both devices awake, neither losing
focus. It is inert under `TEST`.

**Deliberately not built:** live mirroring of an exam between devices. `sim.qt` (the per-question
90s) and `left` (the paper deadline) are wall-clock state measured on one device; two devices
ticking and pushing them corrupt each other, and mirroring the question index drags a reader
out of the question they are on.

**Not verified end to end.** Everything above is tested against a simulated second device — the
real Supabase round trip with two signed-in browsers has not been exercised, because signing in
is the user's to do.

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
python3 hebrew_glossary.py        # ...then put #explaindata back into Hebrew
python3 hebrew_blueprint.py       # ...and the Learn service cards with it
```

**Those last two are not optional.** Both generators write English, and the service
explanations are meant to be Hebrew. Run them or the panel reverts silently — `QA_BANK()`
will fail with the name of the first term that slipped back.

## The service explanations are Hebrew

The same AWS services are defined in three places, and all three now answer in Hebrew:

| where | how many | translated by |
| --- | --- | --- |
| `CODEX` in the page — the briefing and the flashcards | 90 | `hebrew_codex.py` |
| `#explaindata.glossary` — "למה זו התשובה" in the explanation panel | 154 | `hebrew_glossary.py` |
| `#subjectdata` blueprint + trade-offs — the Learn service cards | 163 + 84 | `hebrew_blueprint.py` |

`hebrew_blueprint.py` imports its wording straight from `hebrew_glossary.py`, so the two never
drift; every service the blueprint names is in that glossary and every wording matched, which is
why one dictionary can drive both.

Things deliberately left in English:

- **The term names** (`t`). `exFind()` matches them against the literal text of the options —
  translate a key and it simply stops matching.
- **The 216 `cues`.** A cue quotes the exam's own phrasing ("if a question says …"); the point is
  to recognise those words on the real paper.
- **The `q.x` verified-answer notes** under "Why". Those are per-question reasoning, not service
  definitions, and they are still English — so the label above them stays English too.

Hebrew and Latin on one line need `direction:rtl; unicode-bidi:isolate` on the Hebrew and
`direction:ltr; unicode-bidi:isolate` on the service name inside it, or a term like
`` `maxReceiveCount` `` loses its backticks to the far end of the line. The English fallback
("Decision rules for this sector", pulled from the course recap) opts out with `.exitem.ltr`.

## The bug hunt — what was found and fixed

`python3 audit_static.py`, and in the browser `AUDIT2()` and `AUDIT3()` (load `audit2.js`
and `audit3.js` with `?test=1`). All three, plus every QA suite, are clean as of this pass.

**All twenty-six findings from the first audit are fixed**, including the nine high severity
ones. The three audits between them now report zero.

What the first audit got wrong, and is fixed in the auditor itself:

- It reported four questions as missing "(Select TWO.)". Three of them say "(Choose two.)"
  and were perfectly healthy — the check only looked for the word "Select".
- It never checked that option letters run A, B, C… with no gap, which is how three questions
  sat in the bank missing an option outright.

Bug classes worth knowing about, because each was more than one instance:

| class | what it was |
| --- | --- |
| **Lifecycle** | Leaving a screen did not end what was running on it. An exam survived the back arrow — clock, voice, auto-submit and all — and two engines could drive the question screen at once. `leaveExam()` is now the single door, and `go()` dismisses overlays. |
| **Unclamped percentages** | 26 progress bars set `width` from a raw ratio. The chest bar was rendering `width: 1104%` in ordinary use, hidden only by its parent's `overflow:hidden`. All of them go through `pctW()`. |
| **Profile shape** | Nineteen profile fields were dereferenced somewhere without a guard. Rather than patch a hundred read sites, `normaliseProfile()` fixes the shape at the three doors a profile comes in by: load, cloud merge, import. |
| **Unclamped accuracy** | `correct` and `answered` merge across devices independently, so `correct > answered` is reachable. The home screen read "577% accuracy". `accPct()` and a clamp in `domainStats()`. |
| **Accessible names** | 56 controls announced nothing or announced a bare digit — every back arrow, every bet chip, the theme locks, three "Go" buttons, the review grid, the Learn exam dots. |
| **Pluralisation** | 33 counts interpolated into a hard plural. Each reaches 1 in normal use. `plural(n, word)`. |
| **Input validation** | The custom timer took 0/0/0 and 999999; `paperQs(0)` returned indices from −65; a past exam date read "0 days to go · 900 questions/day". |

**Read-aloud latency.** Three things stacked between the tap and the first sound: the voice was
picked as the first `en` voice in the list, which on Chrome is usually a *network* voice that
fetches its audio before speaking; the whole stem went as one utterance and the median question
is 411 characters; and `cancel()` was called straight into `speak()`, a Chrome race that delays
or drops the utterance. Now: a local voice is preferred, the text is cut into sentence-sized
pieces so the first one is short, the cancel only happens when something is speaking, and the
voice list is warmed at boot instead of asked for at the tap.
Watch `ttsChunks()` — its first version flushed a long clause straight to the output while an
earlier piece was still buffered, so the reading came out reordered with words missing. There is
an assertion that every question in the bank chunks losslessly.

**That first pass did not fix it.** A second round found what it had missed:

- `ttsStop()` was still calling `cancel()` unconditionally, and `simLoad()` calls `ttsStop()` on
  every question load. Guarding the cancel inside `ttsSpeak()` was pointless while the other
  caller kept firing it at an idle engine, which is the state that delays Chrome's next
  `speak()`. Both are guarded now.
- The engine is cold until something asks it for audio, and waking Android's TTS takes seconds.
  `ttsWarm()` speaks a zero-volume utterance on the first user gesture, hooked into
  `ensureAudio()` — the same gesture that already wakes the Web Audio context.
- If the voice list was still empty at the tap, `ttsVoice()` returned null and the engine used
  its own default, which on Chrome is usually the network voice this was meant to avoid. It now
  polls briefly as well as listening for `voiceschanged`.
- Chrome can leave synthesis paused, which queues `speak()` in silence. `resume()` first.

**The second pass made it worse — no sound at all.** Two things in it could do that, and both
were reasoning about a browser that cannot be tested here:

- The zero-volume warm-up utterance. Some engines never emit a silent utterance but still hold
  it in the queue, and everything spoken afterwards queues behind it. Removed.
- `ttsStop()` cancelling only when `speaking || pending`. An utterance the engine has lost track
  of reports neither, which is the whole reason this is a known Chrome bug — so nothing ever
  cleared the queue and everything after it was silent.

**What replaced the guessing.** Pressing Read always cancels first and speaks on the next tick;
yielding a tick is what avoids the cancel/speak race, rather than skipping the cancel and hoping
the queue is empty. Then a watchdog: if no sound has started after 900ms it cancels, drops the
voice override and the chunking, and sends one plain utterance. If that is silent too it says so
and puts the button back. The worst case is a stutter, never a button that does nothing.
`ttsStop()` still avoids cancelling an idle engine on every question load — the one part of the
second pass that is safe, and the likeliest cause of the original delay.

**Then the probe was run, twice, and settled it.** Same ChromeOS machine, 34 voices:

| | run 1 | run 2 (fresh load) |
| --- | --- | --- |
| short text, default voice | FAILED `canceled` | **4591 ms** |
| short, right after `cancel()` | 631 ms | 425 ms |
| LONG text in one go | 710 ms | 438 ms |
| short again | 477 ms | 331 ms |
| short, **local** voice | **never started in 15s** | — |
| short, network voice | 353 ms | — |

Two separate faults, and each of the two guesses above had caught one of them:

1. **The delay is a cold engine.** The first utterance after a page load costs
   four and a half seconds; every one after costs about a third of a second.
   Nothing about the text, the length or the cancel. The warm-up was right — so
   it is back, hooked to the **first touch anywhere in the app**, not to
   `ensureAudio()`, which only runs when a paper starts and is therefore the same
   moment the reader reaches the Read button. It speaks a real word ("ok") at
   volume 0, with `onend`/`onerror` attached and **no tidy-up cancel**, which is
   what could jam a queue.
2. **The silence was the voice override.** The eight `Chrome OS US English`
   voices report `localService: true` and never make a sound. `ttsVoice()`
   preferred exactly those, on the theory that local beats network. Nothing sets
   `utterance.voice` any more — the engine's own default is the one path never
   measured failing. `ttsVoice()` returns null and there is an assertion on it.

Run 1 could not show the cold start, because six lines had already woken the
engine before it reached the warm-up line. Run 2 was a fresh load. If this ever
comes back, run the probe twice and compare the first line.

**Both diagnostics have been removed** now that it is fixed — `tts_probe.html` (the standalone
latency probe, eight strategies timed to first sound) and the `?ttsdebug=1` readout that toasted
the time from the tap to the first sound inside the app. They are in git history if this comes
back: the probe at `10bd287`, the in-app readout at `81803b3`. Bring one back rather than
guessing — the preview browser has no voices installed, so none of this can be measured here,
which is exactly why the first two attempts were wrong.

**Careful when probing `speechSynthesis` by hand.** Redefining `speaking` or `pending` with
`Object.defineProperty` and forgetting to restore it poisons the page: `ttsStop()` then reads a
frozen value and fifteen unrelated exam-clock assertions fail in a way that looks like a real
regression. Reload before believing a failing run that follows a manual probe.

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
- Generated blobs are the same trap as the `LEARN:`/`STUDY:` markers: anything hand-edited into
  `#explaindata` or `#subjectdata` is gone the next time its generator runs. Put the edit in a
  script that runs after the generator, and add a QA assertion that fails when it has not.
- `direction:rtl` on a shared selector will quietly mangle any English still rendering through it
  — trailing full stops jump to the left. Check what else uses the selector before adding it.
- Driving the app with `submitAnswer()` or `qConfirm.click()` runs the **practice** path even
  during an exam, because `.click()` fires on a hidden button. It looks exactly like the exam
  falling apart mid-run. Tap a real `.opt` instead; on a teaching paper that is what settles the
  question.
