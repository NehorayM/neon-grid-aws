/* QA harness for the Learn mode. Load the app with ?test=1, then:
     eval(await (await fetch('/qa_learn.js')).text()); await QA_LEARN();
   It drives the real screens — clicking real elements, not calling functions behind their
   backs — because the bugs this app has actually had were dead buttons that a programmatic
   .click() would have sailed straight through. */
window.QA_LEARN = async function (opts) {
  opts = opts || {};
  const T = window.__t, LT = T.LEARN_T;
  const fails = [], notes = [];
  let checks = 0;
  const ok = (cond, what) => { checks++; if (!cond) fails.push(what); return !!cond; };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const $ = id => document.getElementById(id);


  // an element is only really clickable if it is what the user's finger would land on
  let hitSkipped = false;
  function hittable(el) {
    if (!el) return false;
    if (!innerWidth || !innerHeight) { hitSkipped = true; return true; }   // pane not rendered
    try { el.scrollIntoView({ block: 'center' }); } catch (e) {}   // a user scrolls to it first
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return false;
    if (r.bottom < 0 || r.top > innerHeight) return false;
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + Math.min(r.height / 2, 14));
    return !!top && (top === el || el.contains(top) || top.contains(el));
  }
  function tap(el, what) {
    if (!ok(el, what + ' exists')) return false;
    if (!ok(hittable(el), what + ' is reachable by a tap')) return false;
    el.click();
    return true;
  }
  const visible = id => { const e = $(id); return e && !e.classList.contains('hidden'); };

  function openGate(btnId) {
    const b = $(btnId);
    if (!ok(b, btnId + ' exists')) return false;
    ok(hittable(b), btnId + ' is reachable by a tap');
    if (!b.dataset.ready) LT.forceGate(btnId);         // skip the read timer in a test run
    ok(!b.disabled, btnId + ' opens after the read gate');
    b.click();
    return true;
  }

  async function runSubject(sec, mode) {
    const d = LT.learnData(sec);
    const name = (T.SECTIONS[sec] || sec) + ' [' + mode + ']';
    LT.startLearn(sec);
    ok(T.route === 'learnMapScreen', name + ': starts on the module map');
    ok($('lrnMapList').children.length === d.modules.length + 2,
       name + ': the map lists every part plus the summary and the exam');

    tap($('lrnMapGo'), name + ': the map continue button');
    ok(T.route === 'learnReadScreen', name + ': the first part opens for reading');

    let failedOnce = false, guard = 0;
    for (let i = 0; i < d.modules.length; i++) {
      if (++guard > d.modules.length * 3) { fails.push(name + ': the part loop never terminated'); break; }
      const m = d.modules[i];
      ok(T.route === 'learnReadScreen', name + ' part ' + (i + 1) + ': is on the reading screen');
      const body = $('lrnReadBody');
      ok(body.innerHTML.length > 600, name + ' part ' + (i + 1) + ': the part has real content');
      ok(!/undefined|\[object/.test(body.innerHTML), name + ' part ' + (i + 1) + ': renders no undefined');
      ok($('lrnReadTitle').textContent === m.nm, name + ' part ' + (i + 1) + ': shows its own title');
      ok(hittable($('lrnReadBack')), name + ' part ' + (i + 1) + ': the back button is reachable');

      // deliberately fail the first part once, to prove the gate holds
      const failFirst = (mode === 'fail' && i === 0 && !failedOnce);
      if (failFirst) failedOnce = true;
      openGate('lrnReadGo');
      ok(T.route === 'learnQuizScreen', name + ' part ' + (i + 1) + ': the check questions open');

      const n = m.checks.length;
      for (let q = 0; q < n; q++) {
        const item = LT.L.quiz.items[LT.L.quiz.i];
        const qq = m.checks[item.src];
        ok($('lrnQuizQ').textContent === qq.q, name + ' q' + (q + 1) + ': the question text is on screen');
        const optEls = [...$('lrnQuizOpts').children];
        ok(optEls.length === qq.o.length, name + ' q' + (q + 1) + ': every option is rendered');
        if (q === 0) ok(optEls.every(hittable), name + ' q' + (q + 1) + ': the options are tappable');
        ok($('lrnQuizSubmit').disabled, name + ' q' + (q + 1) + ': cannot submit before choosing');

        const want = failFirst
          ? qq.o.map((_, oi) => oi).filter(oi => !qq.a.includes(oi)).slice(0, qq.a.length)
          : qq.a;
        want.forEach(oi => optEls.find(e => Number(e.dataset.oi) === oi).click());
        ok(!$('lrnQuizSubmit').disabled, name + ' q' + (q + 1) + ': submit opens once an option is chosen');
        $('lrnQuizSubmit').click();

        ok(visible('lrnQuizFeed'), name + ' q' + (q + 1) + ': an explanation is shown either way');
        ok($('lrnQuizFeed').textContent.includes(qq.x.slice(0, 30)),
           name + ' q' + (q + 1) + ': the explanation is the authored one');
        const marked = [...$('lrnQuizOpts').children].filter(e => e.classList.contains('ok'));
        ok(marked.length === qq.a.length, name + ' q' + (q + 1) + ': the correct option is marked');
        $('lrnQuizSubmit').click();                       // next question / see result
      }

      ok(visible('lrnQuizResult'), name + ' part ' + (i + 1) + ': a score is shown after the last question');
      const st = LT.L.mods[m.id];
      if (failFirst) {
        ok(!st.passed, name + ' part ' + (i + 1) + ': a failing score does not pass the part');
        ok(LT.L.mi === i, name + ' part ' + (i + 1) + ': a failing score does not advance');
        ok($('lrnQuizAfter').textContent.includes('again'), name + ' part ' + (i + 1) + ': it offers a re-read');
        tap($('lrnQuizAfter'), name + ' part ' + (i + 1) + ': the re-read button');
        ok(T.route === 'learnReadScreen', name + ' part ' + (i + 1) + ': the re-read reopens the same part');
        ok(visible('lrnReadRedo'), name + ' part ' + (i + 1) + ': the re-read says what was missed');
        i--;                                              // same part again, this time properly
        continue;
      }
      ok(st.passed, name + ' part ' + (i + 1) + ': a clean score passes the part');
      ok(st.best === n, name + ' part ' + (i + 1) + ': the score is recorded');
      tap($('lrnQuizAfter'), name + ' part ' + (i + 1) + ': the continue button');
    }

    ok(T.route === 'learnRecapScreen', name + ': the full summary comes after the last part');
    const recap = $('lrnRecapBody');
    ok(recap.innerHTML.length > 3000, name + ': the summary is long-form, not a stub');
    ok(recap.querySelectorAll('table').length >= 2, name + ': the summary has comparison tables');
    ok(!/undefined|\[object/.test(recap.innerHTML), name + ': the summary renders no undefined');

    openGate('lrnRecapGo');
    ok(T.route === 'learnSimScreen', name + ': the exam starts straight after the summary');
    ok(LT.L.sim.qs.length === 10, name + ': the exam is ten questions');

    // every exam question must belong to a part of this subject
    const ids = d.modules.map(m => m.id);
    ok(d.final.every(q => ids.includes(q.m)), name + ': no exam question comes from outside the parts');

    ok(hittable($('lrnSimStrip').children[0]), name + ': the question strip is tappable');
    for (let i = 0; i < 10; i++) {
      const it = LT.L.sim.qs[LT.L.sim.i], q = d.final[it.src];
      ok($('lrnSimQ').textContent === q.q, name + ' exam q' + (i + 1) + ': shows the question');
      const optEls = [...$('lrnSimOpts').children];
      ok(optEls.length === q.o.length, name + ' exam q' + (i + 1) + ': shows every option');
      const want = (mode === 'half' && i % 2) ? [it.order[0]].filter(oi => !q.a.includes(oi)) : q.a;
      (want.length ? want : [q.o.findIndex((_, oi) => !q.a.includes(oi))]).forEach(oi =>
        optEls.find(e => Number(e.dataset.oi) === oi).click());
      ok(!!(LT.L.sim.ans[LT.L.sim.i] || []).length, name + ' exam q' + (i + 1) + ': the answer is kept');
      if (i < 9) tap($('lrnSimNext'), name + ' exam: next');
    }
    ok(!$('lrnSimSubmit').textContent.includes('/'), name + ': submit stops nagging once all are answered');
    tap($('lrnSimSubmit'), name + ': submit');
    ok(T.route === 'learnDoneScreen', name + ': submitting ends on the result screen');

    const pct = Number($('lrnDoneScore').textContent.replace('%', ''));
    if (mode !== 'half') ok(pct === 100, name + ': answering correctly scores 100% (got ' + pct + '%)');
    else ok(pct > 0 && pct < 100, name + ': a mixed run scores between 0 and 100 (got ' + pct + '%)');
    const cards = $('lrnDoneReview').querySelectorAll('.rcard');
    ok(cards.length === 10, name + ': every exam question is reviewed afterwards');
    const why = $('lrnDoneReview').querySelectorAll('.rcwhy');
    ok(why.length >= 30, name + ': each option carries its own why (' + why.length + ' notes)');
    ok(!!$('lrnDoneReview').querySelector('.rcopt.good b'), name + ': the correct option is called out');
    ok(!localStorage.getItem('academy_learn'), name + ': finishing clears the saved run');
    const rec = (T.P.courses || {})[sec];
    ok(rec && rec.runs >= 1 && rec.mods.length === d.modules.length,
       name + ': the run is recorded against the subject');
    notes.push(name + ' → ' + pct + '%');
  }

  // ---- data invariants, checked in the browser as well as in the builder ----
  Object.keys(LT.LEARN).forEach(k => {
    const d = LT.LEARN[k], nm = T.SECTIONS[d.sec];
    ok(d.modules.length >= 3, nm + ': has at least three parts');
    d.modules.forEach(m => {
      m.checks.forEach((q, i) => {
        ok(q.a.length >= 1 && q.a.every(a => q.o[a]), nm + '/' + m.id + ' check' + i + ': the answer exists');
        ok(new Set(q.o.map(o => o.t)).size === q.o.length, nm + '/' + m.id + ' check' + i + ': options are distinct');
      });
    });
    d.final.forEach((q, i) => {
      ok(q.o.every(o => o.w && o.w.length > 10), nm + ' final' + i + ': every option explains itself');
      ok(q.x.length > 60, nm + ' final' + i + ': the question has a full explanation');
    });
  });

  // ---- resume across a reload ----
  if (opts.extra !== false) {
  const sec0 = LT.LEARN_SECS[0];
  LT.startLearn(sec0);
  $('lrnMapGo').click();
  LT.forceGate('lrnReadGo'); $('lrnReadGo').click();
  LT.learnLeave(true);
  ok(!!LT.learnStored(), 'leaving mid-part saves the run');
  ok(LT.learnResume(), 'a saved run can be resumed');
  ok(LT.L && LT.L.sec === sec0, 'the resumed run is the same subject');
  LT.learnLeave(true);
  localStorage.removeItem('academy_learn');
  }

  const secs = opts.secs || LT.LEARN_SECS;
  for (const sec of secs) await runSubject(sec, 'clean');
  if (opts.extra !== false) {
    await runSubject(secs[0], 'fail');
    await runSubject(secs[0], 'half');
  }

  return { checks, failed: fails.length, fails: fails.slice(0, 40), notes,
           hitTesting: hitSkipped ? 'skipped — run QA_TAPS() with the pane visible' : 'included' };
};


/* Reachability pass: every control the Learn mode puts on screen must be the thing a finger
   would actually land on. Run this with the browser pane visible. */
window.QA_TAPS = function () {
  const T = window.__t, LT = T.LEARN_T, $ = id => document.getElementById(id);
  const out = [], fails = [];
  if (!innerWidth) return { error: 'the pane is hidden — nothing to hit-test' };
  const probe = (id, where) => {
    const el = $(id);
    if (!el) { fails.push(where + ': #' + id + ' is missing'); return; }
    if (el.classList.contains('hidden') || el.offsetParent === null) return;
    try { el.scrollIntoView({ block: 'center' }); } catch (e) {}
    const r = el.getBoundingClientRect();
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + Math.min(r.height / 2, 14));
    const good = top && (top === el || el.contains(top) || top.contains(el));
    out.push(where + ' #' + id + (good ? ' ok' : ' BLOCKED by ' + (top ? (top.id || top.className) : 'nothing')));
    if (!good) fails.push(where + ': #' + id + ' is not tappable');
  };
  const sec = LT.LEARN_SECS[0];
  LT.startLearn(sec);
  ['lrnMapBack', 'lrnMapGo', 'lrnMapQuit'].forEach(id => probe(id, 'map'));
  $('lrnMapGo').click();
  ['lrnReadBack', 'lrnReadGo'].forEach(id => probe(id, 'read'));
  LT.forceGate('lrnReadGo'); $('lrnReadGo').click();
  ['lrnQuizBack', 'lrnQuizSubmit'].forEach(id => probe(id, 'quiz'));
  [...$('lrnQuizOpts').children].forEach((el, i) => {
    try { el.scrollIntoView({ block: 'center' }); } catch (e) {}
    const r = el.getBoundingClientRect();
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + 14);
    const good = top && (top === el || el.contains(top));
    out.push('quiz option ' + (i + 1) + (good ? ' ok' : ' BLOCKED'));
    if (!good) fails.push('quiz: option ' + (i + 1) + ' is not tappable');
  });
  // straight to the exam, to reach the screens at the end
  const d = LT.learnData(sec);
  d.modules.forEach(m => { LT.L.mods[m.id] = { attempts: 1, best: m.checks.length, passed: true, paid: true }; });
  LT.L.mi = d.modules.length - 1;
  LT.learnRecap();
  ['lrnRecapBack', 'lrnRecapGo'].forEach(id => probe(id, 'summary'));
  LT.forceGate('lrnRecapGo'); $('lrnRecapGo').click();
  ['lrnSimBack', 'lrnSimPrev', 'lrnSimNext', 'lrnSimSubmit'].forEach(id => probe(id, 'exam'));
  [...$('lrnSimStrip').children].slice(0, 3).forEach((el, i) => {
    try { el.scrollIntoView({ block: 'center' }); } catch (e) {}
    const r = el.getBoundingClientRect();
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (!(top && (top === el || el.contains(top)))) fails.push('exam: strip button ' + (i + 1) + ' is not tappable');
  });
  d.final.forEach((q, i) => { LT.L.sim.ans[i] = LT.L.sim.qs[i] ? [q.a[0]] : [q.a[0]]; });
  LT.learnSimSubmit(true);
  ['lrnDoneBack', 'lrnDoneNext', 'lrnDonePractice', 'lrnDoneHome'].forEach(id => probe(id, 'result'));
  T.go('homeScreen');
  localStorage.removeItem('academy_learn');
  return { probed: out.length, failed: fails.length, fails, detail: out };
};
