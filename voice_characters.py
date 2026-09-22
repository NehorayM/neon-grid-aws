#!/usr/bin/env python3
"""Make the eight presets sound like eight different people.

The screen reports what the device actually has. On the reporter's machine that
is three working voices and nine silent ones:

    Google US English          WORKS
    Google UK English Female   WORKS
    Google UK English Male     WORKS
    Chrome OS US English 1-8   SILENT
    Google US English 1 (Natural)  SILENT

Nothing here can install a voice — the browser owns that list. But until now all
eight presets used the same voice and differed only in speed, so they sounded
like one person in a hurry. Binding each preset to a particular working voice as
well as its own pitch gives eight genuinely different readers out of three
timbres.

  * each preset carries `want`, a list of name fragments in order of preference
  * voiceForPreset() takes the first one that matches a voice NOT known to be
    silent, then any working voice, then null (the browser's default, which is
    the one thing never measured failing)
  * "Chrome OS" is never matched, since those are the dud family here, and
    anything the liveness check marked dead is excluded outright
  * each preset row shows which voice it landed on, so it is not a mystery
  * probe results persist in P.voiceProbe, so the app remembers which voices work
    on this device between sessions instead of re-testing every time

If a preset does land on a voice that turns out silent, the 900ms watchdog drops
the voice and retries plainly — so the worst case is a stutter, not silence.

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


# ------------------------------------------- each preset wants a particular timbre
PRESETS = """const VOICE_PRESETS=[
  {id:'standard', em:'\U0001f399️', nm:'Standard',    rate:1.0,  pitch:1.0,
   want:[],
   ds:'The plain reading. What you get if you never come here.',
   heb:'הקריאה הרגילה.'},
  {id:'exam',     em:'\U0001f9d1‍⚖️', nm:'Invigilator', rate:0.85, pitch:0.88,
   want:['UK English Male','English Male','UK English'],
   ds:'Low, even and unhurried — the pace an exam is read at.',
   heb:'נמוך ואחיד, כמו משגיח בבחינה.'},
  {id:'review',   em:'⚡', nm:'Quick Review', rate:1.35, pitch:1.0,
   want:['US English','English Female'],
   ds:'Faster, for a second pass over something you have already read.',
   heb:'למעבר שני על חומר מוכר.'},
  {id:'sprint',   em:'\U0001f3c3', nm:'Sprint',      rate:1.8,  pitch:1.12,
   want:['US English','English Female'],
   ds:'As fast as it stays intelligible. For the night before.',
   heb:'מהר ככל שעוד אפשר להבין.'},
  {id:'focus',    em:'\U0001f9d8', nm:'Deep Focus',  rate:0.92, pitch:0.78,
   want:['UK English Male','English Male'],
   ds:'The deepest voice here, steady. Easier to sit with for a long paper.',
   heb:'הקול הנמוך כאן, למבחן ארוך.'},
  {id:'bright',   em:'☀️', nm:'Bright',      rate:1.1,  pitch:1.32,
   want:['UK English Female','English Female','US English'],
   ds:'Higher and lighter, if the others send you to sleep.',
   heb:'גבוה וערני יותר.'},
  {id:'night',    em:'\U0001f319', nm:'Night Study', rate:0.95, pitch:0.92, volume:0.55,
   want:['UK English Female','English Female'],
   ds:'Softer and quieter, for late sessions and headphones.',
   heb:'רך ושקט, ללמידה בלילה.'},
  {id:'dictation',em:'✍️', nm:'Dictation',   rate:0.7,  pitch:1.0, gap:true,
   want:['US English','UK English Male'],
   ds:'Slow, with a breath between sentences, so you can write along.',
   heb:'איטי עם הפסקות, כדי לכתוב תוך כדי כך.'}
];
// A preset asks for a timbre by name fragment. It never matches the Chrome OS family, which is
// the one that reports localService:true and never speaks, and it skips anything the liveness
// check has already caught being silent.
function voiceUsable(v){
  if(!v) return false;
  if(/Chrome OS/i.test(v.name||'')) return false;
  return voiceProbe[v.name]!=='dead';
}
function voiceForPreset(p){
  p=p||voicePreset();
  const en=ttsVoicesEn().filter(voiceUsable);
  if(!en.length) return null;
  for(const frag of (p.want||[])){
    const hit=en.find(v=>(v.name||'').toLowerCase().indexOf(frag.toLowerCase())>=0);
    if(hit) return hit;
  }
  // Standard deliberately asks for nothing, so it stays on the browser's own default
  if(!(p.want||[]).length) return null;
  return en.find(v=>voiceProbe[v.name]==='live')||en[0]||null;
}"""

start = s.index("const VOICE_PRESETS=[")
end = s.index("];", s.index("{id:'dictation'")) + 2
s = s[:start] + PRESETS + s[end:]

# ------------------------------------------------- the reading uses the preset's voice
sub("""function voiceChosen(){
  if(!P.ttsVoice) return null;
  return ttsVoicesEn().find(v=>v.name===P.ttsVoice)||null;
}""",
"""function voiceChosen(){
  // an explicitly picked voice wins; otherwise the preset's own timbre
  if(P.ttsVoice){
    const pick=ttsVoicesEn().find(v=>v.name===P.ttsVoice);
    if(pick&&voiceUsable(pick)) return pick;
  }
  return voiceForPreset();
}""")

# ------------------------------------ remember which voices work on this device
sub("""const voiceProbe={};          // name -> 'live' | 'dead' | 'testing'""",
"""// name -> 'live' | 'dead' | 'testing'. Seeded from the profile, so a device that has been
// checked once does not have to be checked again every session.
const voiceProbe=Object.assign({},(P&&P.voiceProbe)||{});""")

sub("""    const finish=ok=>{ if(done) return; done=true; voiceProbe[v.name]=ok?'live':'dead'; res(ok); };""",
"""    const finish=ok=>{
      if(done) return; done=true;
      voiceProbe[v.name]=ok?'live':'dead';
      P.voiceProbe=P.voiceProbe||{}; P.voiceProbe[v.name]=voiceProbe[v.name];
      res(ok);
    };""")

# ---------------------------------------- show which voice each preset landed on
sub("""      '<span class="vheb" dir="rtl">'+esc(p.heb)+'</span></span>'+""",
"""      '<span class="vheb" dir="rtl">'+esc(p.heb)+'</span>'+
      (()=>{ const v=voiceForPreset(p);
             return '<span class="vuses">'+esc(v?v.name:'the browser\\u2019s own voice')+
                    ' \\u00b7 '+p.rate+'\\u00d7 \\u00b7 pitch '+p.pitch+'</span>'; })()+
      '</span>'+""")

sub(""".vpre .vheb{font-size:11.5px;""",
""".vpre .vuses{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.3px;
  color:var(--cyan);opacity:.75;margin-top:3px;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.vpre .vheb{font-size:11.5px;""")

sub("""    VOICE_PRESETS, voicePreset, voiceRate, voicePitch, voiceVolume, voiceChosen,""",
"""    VOICE_PRESETS, voicePreset, voiceRate, voicePitch, voiceVolume, voiceChosen,
    voiceForPreset, voiceUsable,""")

PAGE.write_text(s, encoding="utf-8")
print("presets now pick their own working voice · page %.2f MB" % (len(s) / 1e6))
