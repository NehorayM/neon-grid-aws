#!/usr/bin/env python3
"""A voice screen for the read-aloud, with eight presets and a liveness check.

Two things shaped this. The reader asked for voice settings and "8 different
voices". And the read-aloud investigation turned up something a plain voice
picker would walk straight into: on the reporter's ChromeOS machine, eight of
the thirty-four installed voices report `localService: true` and never make a
sound — fifteen seconds and nothing. A list of every voice the browser offers
would let someone pick one of those and get silence with no explanation.

So the screen does three things a list would not:

  * **Eight presets**, which is what was actually asked for. They are characters
    rather than engine voices — a rate, a pitch and a purpose — because the
    engine voices available differ wildly between machines and most are named
    things like "Chrome OS US English 6". Exam Room reads at the pace an
    invigilator would; Sprint runs at 1.8x for revision; Dictation crawls with
    gaps for writing things down.
  * **It tests every voice before offering it.** Opening the screen speaks a
    silent word through each English voice and watches for onstart. Anything that
    does not answer within two seconds is shown greyed out and marked, and cannot
    be chosen. Results are cached for the session.
  * **A Test button** on every row, so nothing has to be taken on trust.

Also here: a speed slider (P.ttsRate has been read by ttsSend since the start and
nothing ever set it), pitch, and a sample of real exam wording to try them on.

Deliberately NOT here: auto-read. That was removed on request, and a settings
screen is exactly where it would creep back in.

Run once; index.html is the source of truth afterwards.
"""
import pathlib

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# --------------------------------------------------------------- the screen
sub("""  <div id="themeScreen" class="screen hidden">""",
"""  <!-- READ-ALOUD VOICE -->
  <div id="voiceScreen" class="screen hidden">
    <button class="backbtn" id="voiceBack" aria-label="Back from voice settings">‹</button>
    <div style="text-align:center;margin-bottom:10px">
      <h2 class="head">\U0001f5e3️ Reading Voice</h2>
      <p class="sub" id="voiceSub">How the \U0001f50a Read button sounds in an exam</p>
    </div>
    <div class="vsample" id="voiceSample"></div>
    <div class="sechead">Presets</div>
    <div class="list" id="voicePresets"></div>
    <div class="sechead">Speed</div>
    <div class="vrow">
      <input type="range" id="voiceRate" min="60" max="200" step="5" class="vslide"
             aria-label="Reading speed">
      <span class="vval" id="voiceRateVal">1.0×</span>
    </div>
    <div class="sechead">Pitch</div>
    <div class="vrow">
      <input type="range" id="voicePitch" min="50" max="180" step="5" class="vslide"
             aria-label="Reading pitch">
      <span class="vval" id="voicePitchVal">1.0</span>
    </div>
    <button class="btn wide" id="voiceTry" style="margin-top:12px">\U0001f50a Try it</button>
    <div class="sechead">Voices on this device</div>
    <p class="sub" id="voiceCheckNote" style="margin:0 0 8px">Checking which ones actually speak…</p>
    <div class="list" id="voiceList"></div>
    <p class="exfoot" id="voiceFoot"></p>
  </div>

  <div id="themeScreen" class="screen hidden">""")

sub("""      <button class="minichip" id="themeOpen">\U0001f3a8 Themes</button>""",
"""      <button class="minichip" id="themeOpen">\U0001f3a8 Themes</button>
      <button class="minichip" id="voiceOpen">\U0001f5e3️ Voice</button>""")

sub("""'themeScreen','pathScreen'""", """'themeScreen','voiceScreen','pathScreen'""")

# ------------------------------------------------------------------ styling
sub(""".elsewhere{font-family:var(--mono);""",
""".vsample{background:var(--surface);border:1px solid var(--line);border-radius:12px;
  padding:12px 14px;font-size:13px;line-height:1.55;color:var(--dim);margin-bottom:6px}
.vrow{display:flex;align-items:center;gap:12px;padding:2px 2px 6px}
.vslide{flex:1;min-width:0;accent-color:var(--cyan);height:26px}
.vval{font-family:var(--mono);font-size:12px;color:var(--cyan);min-width:46px;text-align:right}
.vpre{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;
  background:var(--surface);border:1px solid var(--line);text-align:left;width:100%}
.vpre.on{border-color:var(--cyan);background:color-mix(in srgb, var(--cyan) 9%, var(--surface))}
.vpre .vem{font-size:19px;flex:none}
.vpre .vnm{font-size:14px;font-weight:600}
.vpre .vds{font-size:11.5px;color:var(--dim);line-height:1.45}
.vpre .vheb{font-size:11.5px;color:var(--dim);direction:rtl;unicode-bidi:isolate;text-align:right;
  display:block;margin-top:1px}
.vpre .vtest{flex:none;font-size:11px;font-weight:650;padding:7px 11px;border-radius:8px;
  background:var(--surface2);border:1px solid var(--line2);color:var(--txt)}
.vvoice{display:flex;align-items:center;gap:10px;padding:11px 13px;border-radius:11px;
  background:var(--surface);border:1px solid var(--line);width:100%;text-align:left}
.vvoice.on{border-color:var(--cyan)}
.vvoice.dead{opacity:.45}
.vvoice .vn{flex:1;min-width:0;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.vvoice .vtag{font-family:var(--mono);font-size:9.5px;letter-spacing:.4px;padding:2px 6px;
  border-radius:5px;border:1px solid var(--line2);color:var(--dim);flex:none}
.vvoice .vtag.bad{color:var(--red);border-color:var(--red)}
.vvoice .vtag.good{color:var(--lime);border-color:var(--lime)}
.elsewhere{font-family:var(--mono);""")

PAGE.write_text(s, encoding="utf-8")
print("voice screen markup and styling in · page %.2f MB" % (len(s) / 1e6))
