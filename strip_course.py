#!/usr/bin/env python3
"""One-shot removal of the old five-phase Subject Course.

The module-based Learn mode replaces it and brings its own quiz UI, so every hook the
old engine had in the shared question engine comes out too. The content renderers it
used (blueprintHTML, deepDiveHTML) are kept — the new final recap renders them.
"""
import pathlib, re, sys

p = pathlib.Path(__file__).resolve().parent / "index.html"
s = p.read_text()
orig = s
report = []


def cut(pattern, what, count=1, flags=0):
    global s
    new, n = re.subn(pattern, "", s, count=count, flags=flags)
    if n != count:
        print(f"FAILED to cut {what}: matched {n}, wanted {count}", file=sys.stderr)
        sys.exit(1)
    s = new
    report.append(f"cut {what}")


def sub(pattern, repl, what, count=1, flags=0):
    global s
    new, n = re.subn(pattern, repl, s, count=count, flags=flags)
    if n != count:
        print(f"FAILED to rewrite {what}: matched {n}, wanted {count}", file=sys.stderr)
        sys.exit(1)
    s = new
    report.append(f"rewrote {what}")


def cut_block(start_marker, what):
    """Remove a top-level `function f(){...}` / `const X=(...)` by brace matching."""
    global s
    i = s.find(start_marker)
    if i < 0:
        print(f"FAILED to find {what}", file=sys.stderr)
        sys.exit(1)
    i = s.rindex("\n", 0, i) + 1          # whole lines, and leave the newline before them alone
    j = s.index("{", i)
    depth, k = 0, j
    instr = None
    while k < len(s):
        c = s[k]
        if instr:
            if c == "\\":
                k += 2
                continue
            if c == instr:
                instr = None
        elif c in "\"'`":
            instr = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    end = s.find("\n", k) + 1
    s = s[:i] + s[end:]
    report.append(f"cut {what}")


FUNCS = ["stopCourseClock", "startCourseClock", "courseAbort", "courseTick", "saveCourseState",
         "clearCourseState", "readCourseState", "resumeCourse", "renderResumeCourse",
         "courseRecord", "subjectCoverage", "renderCoursePicker", "courseShape", "startCourse",
         "courseRail", "courseIntro", "courseBeginPhase", "courseReadBody", "courseRead",
         "courseGateTick", "coursePick", "courseStartQuestions", "courseList",
         "courseNextQuestion", "courseAnswer", "coursePhaseDone", "courseAdvance",
         "authoredRationale", "optionRationale", "recapCard", "courseRecap", "coursePayout",
         "courseFinish", "courseQuit"]

# --- hooks in the shared question engine -------------------------------------------
sub(r"const mult=1\+Math\.min\(course\?2:4,Math\.floor\(P\.streak/3\)\);\s*// damped inside a course",
    "const mult=1+Math.min(4,Math.floor(P.streak/3));", "streak multiplier damping")
sub(r"if\(P\.streak%5===0&&!course\) coinGain\+=4;", "if(P.streak%5===0) coinGain+=4;",
    "streak milestone bonus")
cut(r"\n *// the course drill comes straight after the briefing, so it is assisted in the same way\n"
    r" *if\(course&&CPHASES\[course\.step\]&&CPHASES\[course\.step\]\.k==='drill'\)\n"
    r" *coinGain=Math\.max\(1,Math\.round\(coinGain\*0\.5\)\);", "course drill coin damping")
cut(r"\n *if\(course\)\{ courseAnswer\(ok\);\n"
    r" *if\(explainMode\(\)\) explainThen\(\(\)=>\{ hideExplain\(\); if\(course\) courseNextQuestion\(\); \},ok\);\n"
    r" *return; \}", "recordAnswer course branch")
sub(r"if\(!secs\|\|exam\|\|course\)\{", "if(!secs||exam){", "question timer guard")
cut(r"\n *if\(course\) courseAbort\(\);", "courseAbort call", count=2)
sub(r"ensureAudio\(\); if\(course\) courseAbort\(\);", "ensureAudio();", "mock-start courseAbort")
cut(r"\n *if\(typeof course!=='undefined'&&course\) courseAbort\(\);", "guarded courseAbort call")
sub(r"ensureAudio\(\); exitStudyMode\(\); if\(course\) courseAbort\(\);",
    "ensureAudio(); exitStudyMode();", "sim-start courseAbort")
sub(r"\$\('quizBack'\)\.onclick=\(\)=>\{ if\(course\)\{ courseQuit\(\); return; \} go\('homeScreen'\); renderHome\(\); \};",
    "$('quizBack').onclick=()=>{ go('homeScreen'); renderHome(); };", "quiz back button")

# --- the engine itself --------------------------------------------------------------
cut(r"\nconst CPHASES=\[.*?\nconst IDX_DRILL=1, IDX_SIM=3;\n", "CPHASES config", flags=re.S)
cut(r"\n// ---------- state ----------\nlet course=null, crsTimer=null, crsGate=0, crsGateTimer=null, crsQuitArm=0;\n",
    "course state")
cut(r"\n// ---------- persistence ----------\n"
    r"// A course is over an hour long; a refresh must not throw it away\.\n"
    r"const CRS_KEY='academy_course';\n", "course persistence key")
cut_block("const QRATIONALE=(()=>{", "QRATIONALE")
for f in FUNCS:
    cut_block("function " + f + "(", f + "()")
cut(r"\n// ---------- wiring ----------\n\$\('courseOpen'\)\.onclick.*?\$\('crsDoneHome'\)\.onclick=\(\)=>\{ go\('homeScreen'\); renderHome\(\); \};\n",
    "course wiring", flags=re.S)

# --- markup ---------------------------------------------------------------------------
cut(r'\n *<div id="crsBar"><span id="crsBarPhase">PHASE</span><span id="crsBarProg"></span>'
    r'<span id="crsBarClock">0:00</span></div>', "course bar in the quiz screen")
cut(r'\n *<div id="coursePickScreen" class="screen hidden">.*?\n  <!-- LEARNING PATH -->',
    "the five course screens", flags=re.S)
s = s.replace("\n  <!-- COURSE: PHASE INTERSTITIAL -->", "")
sub(r"'coursePickScreen','coursePhaseScreen','courseReadScreen','courseRecapScreen','courseDoneScreen',",
    "'learnPickScreen','learnMapScreen','learnReadScreen','learnQuizScreen','learnRecapScreen','learnSimScreen','learnDoneScreen',",
    "screen registry")
sub(r"\$\('app'\)\.classList\.toggle\('reading',id==='courseReadScreen'\|\|id==='courseRecapScreen'\);",
    "$('app').classList.toggle('reading',id==='learnReadScreen'||id==='learnRecapScreen');",
    "reading layout class")
sub(r"#courseRecapScreen \.crswrap\{max-width:var\(--readw\)\}",
    "#learnRecapScreen .crswrap{max-width:var(--readw)}", "recap width rule")
sub(r'<button class="tile hero-tile" id="courseOpen">.*?</button>',
    '<button class="tile hero-tile" id="courseOpen"><span class="ic">🎓</span><b>Learn a Subject</b>'
    '<span>Module by module · read a part, prove you got it, then a 10-question exam on what you learned</span></button>',
    "home tile", flags=re.S)

sub(r"\$\('navHome'\)\.onclick=\(\)=>\{ if\(course\)\{ courseAbort\(\); toast\('Course ended'\); \}\n *go\('homeScreen'\);",
    "$('navHome').onclick=()=>{ if(L) learnLeave(true);\n  go('homeScreen');", "home nav button")
sub(r"\$\('navExam'\)\.onclick=\(\)=>\{ if\(course\)\{ courseAbort\(\); toast\('Course ended'\); \}\n *renderExamPicker\(\);",
    "$('navExam').onclick=()=>{ if(L) learnLeave(true);\n  renderExamPicker();", "exam nav button")
sub(r"\$\('navShop'\)\.onclick=\(\)=>\{ if\(course\) toast\('Course paused — tap Home to leave it'\);\n *renderShop\(\);",
    "$('navShop').onclick=()=>{ if(L) toast('Subject paused — tap Home to leave it');\n  renderShop();", "shop nav button")

# the test surface lists every course symbol; the Learn engine adds its own
cut(r"\n *COURSES, COURSE_BY_SEC, CPHASES, COURSE_MIN, COURSE_PASS, mdRender, mdInline,",
    "course symbols in the test export")
sub(r" *coursePayout, courseShape, SUBJECT, subjectData, subjectCoverage, TRIGGERS, PILLARS, pillarFor,\n"
    r" *blueprintHTML, deepDiveHTML, courseRecap, recapCard, optionRationale, authoredRationale,\n"
    r" *saveCourseState, readCourseState, clearCourseState, resumeCourse, renderResumeCourse,\n"
    r" *IDX_DRILL, IDX_SIM,\n"
    r" *startCourse, courseIntro, courseBeginPhase, courseRead, courseGateTick, courseNextQuestion,\n"
    r" *coursePhaseDone, courseAdvance, courseFinish, courseAbort, courseQuit, coursePick,\n"
    r" *renderCoursePicker, courseReadBody, courseTick, courseList, fmtMS,\n"
    r" *get course\(\)\{return course;\}, get crsGate\(\)\{return crsGate;\},\n",
    "    COURSES, COURSE_BY_SEC, SUBJECT, subjectData, TRIGGERS, PILLARS, pillarFor, mdRender, mdInline,\n"
    "    blueprintHTML, deepDiveHTML, fmtMS,\n"
    "    LEARN_T,\n",
    "course block in the test export")

# nothing named course* may survive outside a comment
leftovers = sorted(set(re.findall(r"\bcourse[A-Z]\w*", s)) - {"courseOpen"})
if leftovers:
    print("FAILED: still referenced: " + ", ".join(leftovers), file=sys.stderr)
    for n, line in enumerate(s.split("\n"), 1):
        if len(line) < 400 and any(x in line for x in leftovers):
            print(f"   {n}: {line.strip()[:150]}", file=sys.stderr)
    sys.exit(1)

p.write_text(s)
print(f"✓ old Subject Course removed — {len(orig)-len(s)} bytes")
for r in report:
    print("   " + r)
