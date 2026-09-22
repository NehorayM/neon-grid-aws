#!/usr/bin/env python3
"""Stop choosing the voice. The probe says that is what broke it.

Measured on the reporter's machine (ChromeOS, Chrome 152, 34 voices installed):

    1. short text, default voice              FAILED canceled
    2. short text, right after cancel()       631 ms
    3. LONG text in one go                    710 ms
    4. short text again                       477 ms
    5. short text, LOCAL voice                FAILED never started within 15s
    6. short text, NETWORK voice              353 ms
    7. silent warm-up utterance               307 ms
    8. short text right after the warm-up     319 ms

Two things fall out of that.

**Line 5 is the bug I introduced.** The eight "Chrome OS US English" voices report
localService: true and never produce a sound. `ttsVoice()` preferred exactly
those, on the theory that a local voice starts faster than a network one. On this
machine a local voice never starts at all — which is why Read went silent. The
voice override is gone: the engine's own default works, in 477-710ms, and it is
the one thing here that was never measured as failing.

**Line 1 confirms the cancel/speak race.** The very first utterance, spoken
immediately after a cancel, came back `canceled` — the browser killed the new
utterance with the old one. Speaking on the next tick instead, which is already
in place, is the right shape for that.

What the numbers do NOT show is a five-second delay anywhere, so the original
report is most likely the same race: a first attempt cancelled out from under
itself, and sound only on whatever retried afterwards. With the voice override
gone and the tick in place there is nothing left to cancel it.

The watchdog stays. It would have caught line 5 on its own — silent after 900ms,
cancel, retry plainly — which is why this is a delay to fix rather than a
silence to apologise for twice.

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


sub("""function ttsVoice(){
  const list=(ttsVoices&&ttsVoices.length)?ttsVoices:ttsLoadVoices();
  const en=list.filter(v=>/^en/i.test(v.lang||''));
  // A local voice speaks the moment it is asked. A network one fetches its audio from a
  // server first, which is where the several-second wait before any sound came from —
  // and on Chrome a Google network voice is usually first in the list.
  return en.find(v=>v.localService)||en.find(v=>/^en[-_]US/i.test(v.lang))||en[0]||null;
}""",
"""// This used to prefer a voice with localService:true, on the theory that a local voice
// starts speaking sooner than a network one that has to fetch its audio. Measured on a
// ChromeOS machine with 34 voices installed, the eight "Chrome OS US English" voices report
// localService:true and NEVER produce a sound — 15 seconds and nothing. The engine's own
// default spoke in 477ms on the same machine. So nothing is chosen any more: u.lang is set
// and the engine picks, which is the one path that has never been measured failing.
//
// Kept, and still exposed, because the probe uses it to report what is installed.
function ttsVoice(){ return null; }
function ttsVoicesEn(){
  const list=(ttsVoices&&ttsVoices.length)?ttsVoices:ttsLoadVoices();
  return list.filter(v=>/^en/i.test(v.lang||''));
}""")

sub("""    ttsChunks, ttsVoice, ttsLoadVoices, ttsWarm, ttsSend, get ttsVoices(){return ttsVoices;},""",
"""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend,
    get ttsVoices(){return ttsVoices;},""")

# the no-voices toast should look at English voices, not the whole list
sub("""          toast(ttsLoadVoices().length
            ? 'This browser will not play speech \\u2014 check the volume and the site sound setting'
            : 'No speech voices are installed in this browser');""",
"""          toast(ttsVoicesEn().length
            ? 'This browser will not play speech \\u2014 check the volume and the site sound setting'
            : 'No English speech voice is installed in this browser');""")

PAGE.write_text(s, encoding="utf-8")
print("the voice override is gone · page %.2f MB" % (len(s) / 1e6))
