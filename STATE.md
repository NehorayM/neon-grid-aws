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
  On papers 1–10 the same per-question time (SIM_QSEC, now 105 s) covers reading the feedback, so it can move on mid-read.
  **There is one clock** — see "One clock" below. `simTimeLeft()` is the sum of the question
  clocks, and `simCheckTime` ends the paper when that reaches zero. `simBudget(n)` survives
  only as the headline figure.
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

## Why each answer, and the splitter that builds it

`q.w` is the written explanation the CSV carries for 1,177 of the questions. It is one
paragraph covering every option, so `whyByOption()` pulls it apart and files each clause
against the option it is about; `optionLine()` then decides what an option is actually shown,
and both the panel and `audit9.js` call it, so the audit measures what is read rather than an
intermediate.

`audit9.js` measured the first version and the paragraph-splitting showed up as three numbers:
**1,922 option lines (40%) opened by discussing a different option**, 1,241 (26%) were a copy of
another option's line, and **451 of 1,177 correct answers were shown less than a sentence**. All
three were the same mistake — attributing whole sentences to options when these write-ups pack
two or three options into one.

Four bugs underneath that were each producing wrong attributions across the whole bank:

- **The letter match was case-insensitive**, so the article in "C and D use a single AZ" matched
  option A. Every sentence in the bank containing the word "a" was filed under A.
- **A capitalised article at the start of a sentence.** "A gp3 volume tops out at 16,000 IOPS" is
  not option A, but "A adds a queue for no benefit" is. The word after the letter decides: a
  third-person verb or a modal means the option, a modifier means the article.
- **"the R&D account" matched option D.** The lead-in is now restricted to whitespace or an
  opening bracket, which also rules out "A/B" and "gp3-D".
- **The keyword pass stole the answer's own evidence.** "io2 supports up to 64,000 IOPS" was
  diverted to a distractor sharing a keyword, leaving the correct option with a fragment.

Separators are tried **strongest first** — dash, then semicolon, then comma — and each accepted
piece is offered the weaker ones. Offering them all at once meant one bad comma candidate vetoed
a good dash split, which is how q226 (the one in the complaint) had the case for its answer filed
under D. A split is refused if a piece is too short to be a clause ("B, C, and D all still involve
keys" is one clause with three subjects), if it strands a continuation ("so the R&D account must
leave it first", "which is why A and B are wrong"), or if it would leave unbalanced brackets
("ALB and NLB (C, D)" must not be cut at that comma).

Where a verdict genuinely covers two options, `leadFirst()` puts the option being read at the
front of the letter list — D is shown "D and B require Lambda to poll the logs" — so the line
reads as being about the option it sits under. It keeps the list's own punctuation, so "(A, D)"
becomes "(D, A)" and not "(D and A)".

`whyQualityChecks()` in `qa_bank.js` holds all of this as standing assertions, including
bank-wide thresholds. **Verify the thresholds can fail before trusting a zero** — replacing
`whyByOption` with one that hands every option the whole write-up takes misled from 14 to 555 and
duplicates from 371 to 1,399, which is what makes the passing numbers mean anything.

The OCR repair is in `fix_ocr.py` and `fix_ocr2.py`. In these option texts a sentence never begins
with a lowercase word, so a period followed by one is always damage ("the put. item method",
"prevent tag. modification"). The exception that the general rule would wreck is a domain:
"events. amazonaws. com" was split at every dot, and there the period is real and the space is the
damage — domains are reassembled first. `BANKV` is a written constant and not a hash of the bank,
so repairing the text does not reset anyone's progress.

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

## The build stamp, and cached pages

A screenshot arrived showing a bug that was already fixed **and deployed** — byte-for-byte
identical on GitHub Pages and locally. The page in the screenshot was a cached copy, and
nothing on it said so, which cost a round of hunting for a bug that no longer existed.

`BUILD` carries the **build time**, and the Records screen shows it. A timestamp rather than a
commit hash on purpose: the stamp cannot contain the hash of the commit that carries it, so
stamping before committing always names the *previous* commit — exactly the wrong answer to
"is this page stale?". A timestamp cannot be wrong that way. **When a fixed bug
reappears, check that first.** A hard reload is the fix; the app is one file on GitHub Pages,
so there is no cache-busting to reach for.

`audit4.js` and `audit5.js` join the other audits: AUDIT4 walks a paper through every
transition checking clock invariants (the clock never shows a frozen number, you cannot stand
inside a paused paper, the strip agrees with the sum, an interval exists exactly when wanted);
AUDIT5 drives the new surfaces sideways (sheets outliving their context, rapid taps, the short
paper, every question spent, the voice screen opened mid-paper).

## A mini-game stops when you leave it

`audit8.js` drives all nine games — launch, step, end — and found that navigating away from
`gameScreen` left `gRunning` true with the requestAnimationFrame loop alive. It kept stepping
physics, ticking the clock and adding score against a canvas nobody could see, and when the
timer finally ran out it paid coins, XP, a high score and quest progress for a game abandoned
minutes earlier. Same class as the exam that survived the back arrow, same fix: `leaveGame()`,
called from the router. Leaving abandons the run; `endGame()` is for finishing it.

**`audit7.js`** covers the modes around the paper — booting back into a paper that is on a
break, six start/quit cycles checked for leaked intervals, the shop and inventory at their
bounds, every mode entering and leaving the question screen coherently, all ten themes for
readable contrast, and the boot resume against the other modes. It reports zero, and that zero
was checked with a negative control: breaking an item count and a theme's contrast on purpose
both get caught.

**Verify an audit can fail before trusting that it passed.** Two of audit7's probes were
silently doing nothing because `buyCons`, `usePotion` and `THEME_LIST` were not on the test
surface — a clean result from a probe that never ran is worth nothing.

## The arithmetic underneath the screens

`audit6.js` drives the quiet logic that no screen test reaches: clock formatting, day keys,
the spaced-repetition scheduler, export, CSV, badge progress, the daily reset.

- **`fmtClock` guards its input.** It rendered `-1:-1` for a negative, `NaN:NaN` for NaN and
  `Infinity:NaN:NaN` for Infinity. Most callers clamp; `P.playMs` and `sessMs` come from a
  merged profile and do not. One guard in the formatter beats auditing every caller forever.
- **Day keys are zero-padded.** They read `2026-1-5`, which as a string sorts *after*
  `2026-1-12`. Nothing orders them today — every use is `!==` — so it was a trap rather than a
  live bug, and precisely the one that bites whoever first writes `logs.sort()`. `sameDay()`
  compares loosely so dates already stored unpadded still match and no daily counter resets.
- **`badgeProgress` clamps to its goal.** A best streak of 12 against a goal of 5 read `12/5`.

Two of the audit's fifteen findings were the audit's own fault and the audit was fixed instead:
`srSchedule` measures in **questions answered**, not time, and the check called it twice without
moving `P.answered`; and the badge checks used 1e6 values no profile reaches. Worth remembering
when reading audit output — a finding is a hypothesis until the code is read.

## Closing the page does not stop the clock

Reported as an exploit, and it was one. The save stores time **remaining** rather than a
deadline, so shutting the tab froze the paper indefinitely: leave for ten minutes, look
everything up, come back, resume, and the clock was exactly where you left it. Measured before
the fix: ten minutes away cost **0 seconds**.

The remaining-time design stays — it is right for the Quit button. What was missing is the
difference between the two ways of leaving:

- **Quit** is a decision. `simPauseSave()` stamps `paused:1` and the paper pauses, as always.
- **Closing, refreshing or crashing** is not — in a simulation. `simAwayCost(sv)` measures
  everything since `sv.at`; the question that was open is charged first and the rest comes off
  the END of the paper (`simChargeEnd`). A practice paper is not charged at all.

`sv.at` was already in the save and had never been read. Time covered by a break in progress is
not charged — `brkUntil` is an absolute moment, so the overlap is exact.

**`simAwayCost` returns seconds.** The first version returned milliseconds and the callers
treated it as seconds, which made the charge a thousand times too big — and that read as the
save being unresumable rather than as a wrong number, which is a much harder symptom to trace.

**The per-question clocks are written down, not inferred.** Measured across a real reload, the
save's `qt` was `{}` after 25 seconds on question one — the resume still landed near the right
number, but only because `at` happened to be stamped when the question loaded, so "time since
`at`" and "time on this question" were the same figure. A coincidence, not a design. Worse,
`P.simSave.qt` was assigned `sim.qt` **by reference**, so every tick rewrote the save while
`at` stayed put, and any unrelated `saveProfile()` (answering awards XP, which saves) wrote a
pair describing two different moments — the resume then charged the gap twice. The save takes a
copy now, always including the current question, and a running paper persists every ten seconds.

If the charge empties the paper it is not lost: the run resumes with no time left and
`simCheckTime()` submits it, so the score for what was answered lands. `simSaved()` used to
DROP such a save, answers and all — it now keeps it on offer so resuming can score it.

## Simulation or practice, asked at the start

Two breaks of exactly six minutes is the real exam's rule and the right default when the
point is to find out whether you would pass. It is the wrong rule when the point is to learn,
because stopping to read something costs one of two breaks and then the clock runs anyway.

So every Start, Retake and restart raises `modeAsk()` and the paper carries a `sim.mode`:

| | breaks | length | how one ends |
|---|---|---|---|
| `exam` (default) | two | exactly six minutes | on its own, and the paper is off-limits until then |
| `practice` | unlimited | as long as you like | by going back into the paper |

Resume never asks — a paper already under way was answered for when it began — and the
"next paper" button inherits the mode you are already sitting in.

An open-ended pause is a separate state from a timed one. `sim.brkOpen` marks it and
`sim.brkFrom` records when it started, because the break machinery is built around
`brkUntil` as a deadline and an open pause has no deadline to hold. `brkEnd()` pays the
clocks back `brkElapsed()` rather than a fixed `BREAK_SECS`.

Two things that are easy to get wrong here:

- **Coming back is how a practice pause ends.** The guard that keeps you out of the paper
  during a timed break would otherwise lock you out of your own paper forever. In practice
  it calls `brkEnd()` and returns, because `simLoad()` has already navigated there — going
  on to `_go(id)` as well just renders it twice.
- **A refresh mid-pause must pay the pause once.** `simResume()` deliberately does NOT carry
  `brkOpen`/`brkFrom` across. It did at first, and thirty minutes paused came back as thirty
  minutes *gained*: `simAwayCost` correctly charges nothing for time inside an open pause,
  and then walking into the paper ran `brkEnd` and credited the same thirty minutes again —
  a 98-minute paper resumed with 128 minutes on it. The saved `left` already has the pause
  excluded, so the resume is where the pause ends, and it ends free.

A closed tab still costs a simulation its time. That is the exploit closed earlier and
`modeChecks()` keeps a check on it, because "the clock does not run while I am away" is
exactly what practice mode is allowed to do and a simulation is not.

The mode is on screen in the paper header (`EXAM 3 · PRACTICE`) and a best score set in
practice is marked as such on its row, because a 78% you paused your way through is not the
same evidence as a 78% you sat straight through. Scores still count the same otherwise.

**`startSim()` — the random mock exam — was dead until this went in.** It read `qs.length`
while building the object literal that *defines* the `qs` property, which is a plain
ReferenceError, thrown before `sim` was ever assigned. The handler is an inline arrow so
nothing reported it: a 470x70 button that did nothing at all, on every tap. If you add
another entry point, build the questions first and measure them after, the way `startPaper`
does.

## Two six-minute breaks per paper

Leaving the question screen mid-paper used to keep both clocks running, so a glance at Study
cost exam time. Now it is a decision: `BREAK_MAX=2` breaks of `BREAK_SECS=360`, and the paper
is frozen for the whole of one.

`go()` is the interception point — it already wrapped the router, and it now refuses to leave a
running paper except through a break. `IN_PAPER` lists the screens that are still part of it
(`quizScreen`, `simRevScreen`, `simDoneScreen`), so moving between them is not leaving.

- **With a break in hand:** a sheet opens saying what it costs and how many are left. It is the
  only real yes/no sheet in the app — the arm-then-confirm buttons used everywhere else are too
  easy to trip for something that spends one of two breaks and freezes a running exam.
- **During a break:** both clocks stop. Because they are deadlines, the break is paid for by
  pushing `sim.endAt` and `sim.qEndAt` out by the full 360s when it ends, so nothing is spent
  while you are away. `simCheckTime()` also refuses to expire a paused paper.
- **Six minutes, not five, not seven.** Coming back early is not a way to bank one; the break
  runs its length and then calls `simLoad()` to hand you back to the question you were on.
- **With both spent:** leaving is refused and the clock keeps running. That is the point of
  having exactly two.

**A break keeps you out of the paper.** This is the fix for "the timer isn't working": both
clocks are frozen during a break, so standing on the question screen meant looking at a dead
1:30 for up to six minutes, which is indistinguishable from a broken clock. `go()` refuses any
`IN_PAPER` screen while `brkOn()`, the resume row offers the remaining break instead of a way
in, and `renderClock()` shows `☕ 5:57 · break · paper paused` rather than the exam's frozen
number. `brkStart()`, `brkEnd()` and `brkTick()` all repaint the clock, so it never sits on a
stale value waiting for the next tick.

`brkUsed` and `brkUntil` live on the run and go into `P.simSave`, so walking away and resuming
does not hand the breaks back. `body.asking` hides the nav while the sheet is open — the sheet
is taller than a padding-bottom can allow for, and nothing under a modal should be competing
for the same taps.

## A refresh puts you back in the paper

Everything was already being saved — the question, the answers, the flags, the breaks, both
clocks — and nothing ever restored it. A reload landed on the home screen and the paper only
came back if you went looking for it on the Exam tab, which reads as "the refresh reset
everything".

`resumeOnBoot()` runs after `loadProfile()` resolves and walks straight back in, but only when
all three hold:

- the save exists and its budget has not run out (`simSaved()` already subtracts the away cost)
- it is **not** `paused` — Quit is a decision and is not undone by a reload
- it belongs to **this** device — another device's paper is that device's to take back, through
  the takeover flow, not something to grab silently

It is skipped under `TEST`, where the harness drives resumes itself.

## A resume has to land somewhere you can work

Away long enough for the away-charge to drain the question you were on, you used to resume
straight back onto it — a dead `0:00` clock, question 1 of 65, and no way forward but Next.
`simQStart()` deliberately does not bounce you out of a spent question, which is right when you
open one from the review list and wrong here, because this is not somewhere you chose to be.
A resume now moves to the first question that still has time, and if none do it submits and
scores what was answered rather than resuming into limbo.

**The headline is the only clock.** It once quoted `min(question sum, wall clock)` and the
subtitle explained which was binding — a careful description of a trap. The wall clock is gone.

## Two devices, one exam — and the running-exams backup

**The bug.** Opening the app on a second device threw away the exam on the first. `resumeOnBoot()`
resumed the phone's own saved copy (question 4) before looking at the cloud; resuming claims the
paper, and `pushCloud()` then wrote the phone's whole profile over the cloud's — a plain upsert.
`cloudTouch()` did the same after every save, so the cloud was last-writer-wins and merged only when
a device pulled. `simSaveNewer()` picked the copy claimed LAST, the phone's stale one, and the
desktop's 30-second owner check stopped and discarded question 34.

**Now.**
- Every run has an id (`sim.rid`, `svRid(sv)` falls back to paper + questions for old saves). For
  two copies of the same run, `simSaveNewer` keeps the one with MORE ANSWERS, whoever claimed last.
  Equal copies still go by claim — answers only change when you act, so the stale copy loses and
  two open devices do not ping-pong. Different runs still go by claim.
- `resumeOnBoot` waits for the first cloud sync (`authFirst`, up to 6 s) before resuming, and does
  not resume a paper another device owns — it says where it is running instead.
- `simClaim` and `cloudTouch` call `syncNow(true)` (pull, merge, push). No blind upserts remain on
  the exam path.
- **Running exams** (`P.runs`, keyed `rid|device`): every save leaves this device's copy of the run;
  merged by union so no merge loses a copy; a device whose exam is taken keeps its copy, paused (so
  continuing it does not charge the gap). Listed on the Exam screen with question, answers, time
  left, device and age; "furthest" marks a copy genuinely ahead. `runRestore` continues any of them
  here (it arms first). A run is dropped on submit or deliberate discard (`simClearSave` →
  `runDone`), and `P.runsDone` is merged too, so a device that has not heard cannot resurrect it.
  Kept: 8 most recent, 14 days.
- The paper-record merge now keeps `bestMode`/`lastMode`/`ptries`.

`multiDeviceChecks()` reproduces the report (stale copy claimed later vs the copy at question 34)
and covers the list, the restore, the taken-away copy and a finished run. **Not yet exercised with
two real signed-in devices against Supabase** — the merge is tested; the network round trip is not.

## Exam screens — measured, not eyeballed

Five rounds on the exam screens, each measured on a 375px and a 320px phone:
- question screen: the briefing sits between question and options, closed on every question (it
  was 1,081px, open, above the question); the paper box is one row. Question starts at 220px.
- explanation: each option's text once — heading names the answer, no You picked/Correct answer
  boxes when there is a write-up, a reminder line per option that skips the words all options
  share, service definitions and decision rules folded. 1,744px -> 763px.
- result screen: actions under the score, short meta line, last three history entries. 1,827 -> 1,116px.
- exam list: short subtitle, "Not started" rows, CSV below the list, Best on the /1000 scale.
- narrow phones: the exam buttons go two rows under 420px (Prev/Next on top) — in a redo the six
  buttons pushed Next off a 320px screen. `--topH` keeps every screen below the top bar, which grew
  past 64px when the name/XP line wrapped.
`fuzz_exam.js` random-walks every exam flow with invariants; run it with `await FUZZ_EXAM(500,seed)`.
Negative control: against build 1452c21 it finds the stale pause bar and the paused redo.

## Exam history and redo

**Its own tab and its own table.** The list is the **Redo** tab (`redoScreen`, `renderRedoScreen`):
summary, a recent-scores chart against 720, a card per exam. The data is also in its own table,
`exam_history` (`supabase_exam_history.sql`, RLS own-rows-only, tested in `sql_tests/`): any change
to an exam upserts its row within 1.5 s (`histCloudQueue`/`histCloudPush`); every `syncNow` and
opening the tab pull it (`histCloudPull`, newer `at` wins, local-only entries sent up). **The SQL
must be run once in the Supabase SQL editor** — until then `histTable==='missing'` and history
syncs through the profile copy only, which the Redo screen says. `cloudForTest()` on the test
surface lets the harness plug in a fake client.

Every submit calls `histWrite()`, keeping the exam in `P.examHist[hid]` (hid = the run id; 30
most recent): paper, date, every answer, flags, SAA score, right/total. Finishing later carries
the hid and updates the same entry. The Exam screen lists them (`renderHist`); **Redo**
(`histOpen`) starts `sim.mode==='redo'`: no clock anywhere (simQStart/Sync/Tick, simCheckTime,
the strip and the top clock all check `isRedo()`), answers editable (`simTeaches()` is false, so
nothing locks), live score over the whole paper with blanks wrong, and a 💡 Answer button that
shows the explanation without locking. Every edit also writes the entry, so it is current even
if the redo never closes; the redo itself is a normal save (Running exams, resumes on reload).
Save & close (`redoFinish`) updates the entry only — no coins, XP, stats or exam count. Redos are
counted when one starts, not on save (a crash-resume counted twice). Merged per entry, later `at`
wins. Exams from before this build are not listed: their answers were never kept.

## The SAA-C03 score

From the official exam guide: a scaled score of 100–1,000, 720 to pass; four domains weighted
30 / 26 / 24 / 20 % of scored content (Secure, Resilient, High-Performing, Cost-Optimized);
compensatory (only the overall must pass); blanks scored wrong; the raw-to-scaled conversion is
not published.

- **A question's exam domain is what it asks** (`examDomainOf`, cached in `qDom(qi)`): its
  requirement line — "MOST cost-effectively", "MOST secure", "highly available" — weighted 3x,
  the whole stem 1x, the service-based `domainOf(q.s)` breaking ties and filling in when the
  question states nothing. The service labels read 11/31/55/3; these read 27/16/41/15. The rest
  of the skew is the bank's own. `domainOf(sec)` is still what readiness and the study views use.
- **`saaScore(pairs)`** weights each domain's accuracy by the exam's mix, not the paper's. A
  domain with few questions on a paper is blended with the overall accuracy (`SAA_SHRINK` = 6
  questions' worth), so two Cost questions move the score by ~60 — about what 2 of 50 scored
  questions are worth on the real exam — instead of ~200.
- **`saaScaled(f)`** anchors 0% -> 100, 72% -> 720, 100% -> 1000. It is an estimate, kept at
  the app's existing 72% line (the stricter of the two common readings).
- The result headline is the scaled score; the meta line keeps the raw count and the weighted
  %. `P.papers[n].best` and simLog `p` now hold the weighted %, simLog `sc` the scaled score;
  entries from before carry only a raw `p` and are shown as a percentage.
- **"Score so far"** (`renderSimLive`) shows on teaching papers and in practice only. On an
  exam-conditions paper it would say whether each answer was right, so it waits for Submit.

`saaChecks()` holds the scale anchors, the classification of each kind of requirement line, the
weighting against a skewed paper, the small-domain blend, and where the live score shows.

## One clock — and finishing a paper later

**The bug.** A paper ran two clocks with the same 97.5-minute budget. The big PAPER REMAINING
number was the sum of the 65 question clocks, but the paper ended on a separate wall clock
(`sim.endAt`) that kept running whenever no question clock did — reading the explanation after
answering on a teaching paper, the review grid, a practice paper in a background tab. Reproduced
on the previous build: every answer right, a minute on each question and a minute reading, and
the paper was cut off after question **49** with half an hour still showing ("49 / 65 correct ·
98 min · 16 to export"). A practice paper left in a background tab submitted itself overnight —
the "2% — 872 min" entry in the history.

**The rule now.**
- `simTimeLeft()` is `simTotalLeft()*1000`. The paper ends when its questions are out of time, or
  when it is submitted. In-app time off a question — an explanation, the review grid, a break,
  a practice pause — is not answering time and costs nothing.
- (Superseded: time away used to be charged in full, overflow off the end of the paper; a few hours away drained every question and the paper submitted itself. Now only the question you were on pays for time away, and a paper never submits because you were gone.) Previously: a simulation paid for time AWAY from the app in full: the question you were on runs
  down, and the overflow comes off the end, unanswered questions last-first (`simChargeEnd`),
  the way a real exam's clock leaves you short at the end rather than draining the question you
  come back to. That applies to a closed tab (`simResume`) and to a background tab (`simBack`,
  which remembers the open question's seconds in `simAwayQ`).
- A practice paper is never charged for time away — closing the app is how you stop on a phone.
- The result's minutes are `(simTotalFull() - simTotalLeft())/60`: time spent answering.
- `sim.endAt` is still written because brkEnd and a few old readers touch it. Nothing ends on it.

**Finishing later.** Submitting keeps `P.lastPaper` (questions, answers, flags, per-question
clocks) while anything is unanswered with time left. `simContinue()` reopens it from the result
screen (`#simCont`) or the paper's row (↩ N). Earlier answers are **locked** (`sim.locked`),
because the result screen and the CSV show correct answers for missed questions; for the same
reason the continuation runs as practice and its score is recorded as practice, as the same
attempt (`recordPaper(..., continued)`). The accounting counts only what is new: the first submit
already counted every blank as attempted and wrong, so a continuation credits only blanks now
answered right, pays coins/XP for those alone, is not another exam in the counters, and pays a
pass bonus only if it is the sitting that crosses 72%. Papers submitted before this build cannot
be reopened — that build kept no per-question answers after submitting.

`oneClockChecks()` and `continueChecks()` hold all of it. The negative control is the old build
itself: the same run stops at question 49.

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

**The amber state is the last five minutes** with something still unanswered. It used to mean
"the hidden wall clock will bite first" — the exact way papers were being cut off.

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

### Signing in on a fresh browser wiped the account (fixed 2026-09-23)

Found the first time the app was tested signed in. "The later save wins the plain fields" was
applied to **everything** outside `MAX_KEYS` and the hand-merged collections — including
`simLog`, `examLog`, `mockLog`, `rHist`, `sr`, `study`, `known`, `inv` and `login`. A browser
that has never been used holds a guest profile created seconds ago, so it is always the later
save: its empty lists replaced the account's, and `syncNow` pushed the result. The account read
"sims: 11" over an empty history, an empty review schedule and a one-day streak.

- **Collections are combined, never replaced.** Logs are united (dedupe by content, newest
  first, the writer's own cap), `rHist` one point per day, `sr` keeps each question's later
  `due`, `study` read-on-either and best-of, `known` union, `login` follows the later *login*
  (same day: longer streak), `inv` takes the later side unless it is empty. Dates are compared
  through `dayNorm`, since older entries were written without zero-padding.
- **A sign-in takes the cloud's settings.** `doSignIn` sets `freshSignIn`; the next `syncNow`
  passes `{cloudFirst:true}`. Deliberately *not* a "first time this device saw the account"
  flag in localStorage: every device signed in before the fix would lack it too, and would
  then hand its own settings to the cloud's.
- **Recovery comes from the other devices.** The damage reached the cloud, but each device that
  was not opened since still holds the full data locally; with the union merge its next sync
  puts the history back. A device running the OLD code would instead take the cloud's empty
  lists — so it must load the new build first (open a fresh URL, e.g. `?v=<anything>`, rather
  than switching to an old tab, whose focus handler syncs before any reload).
- `mergeLossChecks` in `qa_bank.js` replays it: blank guest + full cloud, the damaged cloud +
  a full device, caps, dedupe, `cloudFirst`, and a reset on either side. Against the old merge
  the sign-in part fails 20 of 25.

**Reset all progress, signed in.** Uniting collections would have made the reset undo itself
at the next sync (it already half-did, for `seen`, `badges` and the counters). `resetProfile()`
now stamps `P.resetAt`; a copy whose `at` and `resetAt` are both older than the newest reset is
dropped rather than merged — its lists come back empty, its numbers 0, its settings kept — so
the reset reaches the cloud and every device that syncs after it. The separate `exam_history`
table is not touched by a reset; `histCloudPull` brings those rows back, by design.

## Supabase

Project `rlbgbxgtaqvxwvskpblg`. The publishable key is in the `SUPA` block in `index.html` —
that is fine, it is meant to ship. **Row-level security is what makes it safe**; verified with
an anonymous insert returning `42501`.

SQL files, run in this order in the SQL editor:

1. `supabase_setup.sql` — profiles, RLS, username column
2. `supabase_casino.sql` — wallets, blackjack, cash-out
3. `supabase_casino_v2.sql` — shared roulette, chip buy-in, retention sweeps
4. `supabase_duel.sql` — duels + the server-side answer key (~47 KB)
5. `supabase_duel_v2.sql` — exam choice, per-question history, a rebuilt key, the roulette fix
6. `supabase_exam_history.sql` — the exam list behind the Redo tab

All are idempotent. Never put the `sb_secret_` key in the page.

## The casino duel (and the wheel that never landed)

Reported with a screenshot: Roulette selected, the Question duel underneath it. `#casDuel` was
the one casino panel without `hidden` in the markup, so both showed until a tab was tapped.

- **Exam questions.** The duel always drew from the bank; now a player picks *Any exam* or
  *Exam 1–19* and every question says where it lives ("Exam 7 · Q23"). The exams are the bank
  in 65s, so the server needs no list: exam n is ids `(n-1)*65 .. n*65-1`. `duel_find(stake,
  exam default 0)` sits "any" down with a specific exam and the exam wins; different exams do
  not meet. The one-argument `duel_find(bigint)` is **dropped**, not overloaded — PostgREST
  picks by argument names and two candidates for `{stake}` would make every call ambiguous. A
  database still on v1 answers `{stake, exam}` with "function not found"; the client
  (`casRpc(..., {missingOk:true})`) falls back to `{stake}` and says what to run.
- **The answer key drifted.** It was generated once by hand; questions 862 and 1046 were
  corrected in the bank afterwards, so a duel marked the right answer wrong. `gen_duel_v2.py`
  writes `supabase_duel_v2.sql` from the page, and `duelChecks` compares the key to `QS` — a
  bank edit without re-running it fails QA_BANK.
- **The answer after each question.** `duels.hist` gets one entry per finished question (the
  answer, both picks, both verdicts) via `duel_log_turn`, guarded so it is written once.
  `duel_view` returns it from the caller's side. Nothing about the question in play is
  revealed. The client draws the reveal card, the pips and the result recap from it; "Why" is
  the question's own write-up (`q.w`), which covers every option.
- **`duel_next` takes the row first.** Both players poll `duel_state`; two polls that saw the
  same clock run out used to advance the duel twice, skipping a question.
- **The practice bot** ("Byte", 62%, answers in 6–36 s, hurries once you have answered) plays
  the server's rules entirely in the page, with no chips. `P.botW/L/D` are in `MAX_KEYS`.
- **A duel survives the screen.** Leaving the casino stopped polling and a reload lost
  `duelId`, so the clock ran out unseen. Entering the casino calls `duelResume()`, which finds
  an open duel through the `duels` RLS read policy.
- **Roulette spun forever.** Found testing signed in: `supabase_duel.sql` defined
  `roulette_mark()` to write down a finished round nobody bet on, but nothing called it — with
  no bets there were no rounds (and the sweep deletes old ones), `last` stayed null and every
  client spun indefinitely. v2's `roulette_table()` marks `cur - 1`; the client also gives up
  a spin after 7 s with no result.

`sql_tests/duel_v2_suite.sql` (run by `run.sh`, which also installs v2 twice to prove it is
re-runnable). `suite.sql` now starts outside roulette's closing window: `now()` is fixed for a
whole `do` block, and a run that began in the last 3 s of a round failed "a roulette bet is
accepted" at random.

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

## The briefing says how to choose, not just what things are

"Before you answer" listed the services in play with their Hebrew definitions and a note on the
exam's phrasing — all vocabulary, nothing about how to pick between them, which is the skill the
question tests. Two sections added, both from material already in the page:

- **How to choose in this area** — the sector's decision rules, from `exFallback(sec)`. Every
  one of the 23 sectors has them.
- **What people get wrong here** — the traps in `#subjectdata`, already phrased as mistakes.
  18 of 23 sectors have them.

Neither names the correct option: they describe the family of questions, which is what makes
them safe in a panel shown *before* answering. Measured over the ten briefed papers, the
briefing is now median 1,286 characters, minimum 728 (a sector with no recorded traps), maximum
1,798 — the assertion floor is set from that measurement rather than guessed.

Both also go into the briefed-drill panel, which shares `buildBriefing()`.

## Every option says why it stands or falls

The panel used to explain the right answer by naming the services in it, and the wrong ones
only when they happened to name a service the right answer did not — so most distractors got
nothing. Now every option gets a row, marked ✓ or ✗, with the reasoning for that specific
option.

The text comes from the `explanation` column of `aws_saa_questions_explained_FIXED_FINAL.csv`,
attached to each question as `q.w` by `attach_why.py`. 1,177 of 1,201 carry one; the other 24
are where the CSV disagrees with this bank's recorded answer (22) or matched nothing
confidently (2). **An explanation arguing for C under a question this app marks D is worse than
no explanation**, so those keep the sections they had.

**Each option is a block, not a line.** "More than a few sentences" — so an option now shows
its full text (no truncation), the sentence saying why it stands or falls, and the Hebrew
definition of every service it names, printed against the first option that names it so nothing
repeats down the list. Below them, the sector's **decision rules** from the course recap, which
were only ever shown as a fallback when nothing else matched and are the most transferable thing
on the page. The panel went from roughly 700 characters to about 2,800.

The two standalone Hebrew blocks are gone — their content is what now sits under each option.
They still render when a question has no written explanation to hang them from.

`whyByOption()` splits the write-up and puts each sentence against the option it names —
"B and D require Lambda to poll the logs" lands on both B and D. Sentences naming **no** option
are the case for the right answer (these write-ups open by saying why the winner wins, then name
the losers), so they go there rather than into a leftover block. One naming *every* option is
too general to pin on one and goes to the right answer too. Result: 83% of options across the
bank get their own line, 52% of questions have every option covered; the rest fall back to an
honest "the write-up does not single this one out".

**BANKV is not bumped** — it hashes stem, options, answer and sector, none of which changed, so
adding prose does not invalidate anybody's progress. The page went from 3.11 MB to 3.62 MB.

**Watch the direction.** These rows live inside `.exwhy`, which is RTL for the Hebrew glossary,
and inherit it — the option text, then the decision rules, each rendered right-aligned with
their full stops on the wrong side until given `direction:ltr` explicitly. Any English block
added under `.exwhy` needs the same, and the Hebrew service lines nested inside an option need
it put back. The assertions look at `.svcline>span` for the Hebrew and at the option's own `<b>`
for the English: an option's outer span holds both, so testing it finds Hebrew in its
descendants and LTR on the element itself.

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

## The review loop (branch `review-loop`)

Eight review-then-fix rounds, each committed separately so any one can be reverted:

1. Exam cues were off-topic 23% of the time (scored on generic stem words) — now must name the
   service the answer uses; 2%. Cue lookup 18 ms → 0.1 ms (patterns compiled once).
2. The sheets were dialogs to the eye only — role/aria-modal, focus in and back, Escape, Tab kept.
3. In a simulation, switching tabs was a free break (the question deadline was pushed out).
4. An answer given just before the page closed was lost (250 ms save debounce, no flush).
5. A tap past the limit on "Select 2" did nothing — now shakes and explains.
6. The exam countdown was a day short west of UTC (`new Date('YYYY-MM-DD')` is UTC midnight).
7. Performance reviewed and clean; supabase-js pinned to 2.117.0 with an SRI hash.
8. An imported progress file could run script: several renderers wrote profile fields into
   innerHTML raw. Fixed at render and at the load door (`normaliseProfile` now types nearly
   everything). A crash on an unknown difficulty had been hiding half of these.

**Test-profile hygiene:** the fuzz in `xssChecks()` restores and flushes the profile when done.
Manual fuzzing without that polluted the preview browser's stored profile for several runs.

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
