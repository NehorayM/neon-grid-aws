#!/usr/bin/env python3
"""The engine behind the voice screen: presets, liveness testing, and wiring.

See voice_screen.py for why this tests voices rather than just listing them.

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


ENGINE = """
// ================= READING VOICE =================
// Eight characters rather than eight engine voices. Which engine voices exist differs wildly
// between machines and most are named things like "Chrome OS US English 6", so a preset is a
// rate, a pitch and a purpose, applied over whichever voice actually works here.
const VOICE_PRESETS=[
  {id:'standard', em:'\\U0001f399\\ufe0f', nm:'Standard',    rate:1.0,  pitch:1.0,
   ds:'The plain reading. What you get if you never come here.',
   heb:'\\u05d4\\u05e7\\u05e8\\u05d9\\u05d0\\u05d4 \\u05d4\\u05e8\\u05d2\\u05d9\\u05dc\\u05d4.'},
  {id:'exam',     em:'\\U0001f9d1\\u200d\\u2696\\ufe0f', nm:'Exam Room', rate:0.85, pitch:0.95,
   ds:'Even and unhurried, the pace an invigilator reads at.',
   heb:'\\u05e7\\u05e6\\u05d1 \\u05e9\\u05dc \\u05de\\u05e9\\u05d2\\u05d9\\u05d7 \\u05d1\\u05d1\\u05d7\\u05d9\\u05e0\\u05d4.'},
  {id:'review',   em:'\\u26a1', nm:'Quick Review', rate:1.35, pitch:1.0,
   ds:'Faster, for a second pass over something you have already read.',
   heb:'\\u05dc\\u05de\\u05e2\\u05d1\\u05e8 \\u05e9\\u05e0\\u05d9 \\u05e2\\u05dc \\u05d7\\u05d5\\u05de\\u05e8 \\u05de\\u05d5\\u05db\\u05e8.'},
  {id:'sprint',   em:'\\U0001f3c3', nm:'Sprint',      rate:1.8,  pitch:1.05,
   ds:'As fast as it stays intelligible. For the night before.',
   heb:'\\u05de\\u05d4\\u05e8 \\u05db\\u05db\\u05dc \\u05e9\\u05e2\\u05d5\\u05d3 \\u05d0\\u05e4\\u05e9\\u05e8 \\u05dc\\u05d4\\u05d1\\u05d9\\u05df.'},
  {id:'focus',    em:'\\U0001f9d8', nm:'Deep Focus',  rate:0.92, pitch:0.85,
   ds:'Low and steady. Easier to sit with for a long paper.',
   heb:'\\u05e0\\u05de\\u05d5\\u05da \\u05d5\\u05e8\\u05d2\\u05d5\\u05e2, \\u05dc\\u05de\\u05d1\\u05d7\\u05df \\u05d0\\u05e8\\u05d5\\u05da.'},
  {id:'bright',   em:'\\u2600\\ufe0f', nm:'Bright',      rate:1.1,  pitch:1.25,
   ds:'Higher and lighter, if the default sends you to sleep.',
   heb:'\\u05d2\\u05d1\\u05d5\\u05d4 \\u05d5\\u05e2\\u05e8\\u05e0\\u05d9 \\u05d9\\u05d5\\u05ea\\u05e8.'},
  {id:'night',    em:'\\U0001f319', nm:'Night Study', rate:0.95, pitch:0.9, volume:0.55,
   ds:'Quieter and gentler, for late sessions and headphones.',
   heb:'\\u05e9\\u05e7\\u05d8 \\u05d9\\u05d5\\u05ea\\u05e8, \\u05dc\\u05dc\\u05de\\u05d9\\u05d3\\u05d4 \\u05d1\\u05dc\\u05d9\\u05dc\\u05d4.'},
  {id:'dictation',em:'\\u270d\\ufe0f', nm:'Dictation',   rate:0.7,  pitch:1.0, gap:true,
   ds:'Slow, with a breath between sentences, so you can write along.',
   heb:'\\u05d0\\u05d9\\u05d8\\u05d9 \\u05e2\\u05dd \\u05d4\\u05e4\\u05e1\\u05e7\\u05d5\\u05ea, \\u05db\\u05d3\\u05d9 \\u05dc\\u05db\\u05ea\\u05d5\\u05d1 \\u05ea\\u05d5\\u05da \\u05db\\u05d3\\u05d9 \\u05db\\u05da.'}
];
const voicePreset=()=>VOICE_PRESETS.find(p=>p.id===(P.voicePreset||'standard'))||VOICE_PRESETS[0];
function voiceRate(){ const p=voicePreset(); return clamp01(P.ttsRate!=null?P.ttsRate:p.rate,0.5,2.2); }
function voicePitch(){ const p=voicePreset(); return clamp01(P.ttsPitch!=null?P.ttsPitch:p.pitch,0.4,2); }
function voiceVolume(){ const p=voicePreset(); return clamp01(p.volume==null?1:p.volume,0,1); }
function clamp01(n,lo,hi){ n=Number(n); return isFinite(n)?Math.min(hi,Math.max(lo,n)):lo; }

// ---------- which voices on this machine actually speak ----------
// Eight of the reporter's thirty-four report localService:true and never produce a sound.
// Offering a voice that cannot speak is worse than offering none, so each is tried once.
const voiceProbe={};          // name -> 'live' | 'dead' | 'testing'
function voiceTest(v){
  if(!v||!ttsOk()) return Promise.resolve(false);
  if(voiceProbe[v.name]==='live') return Promise.resolve(true);
  if(voiceProbe[v.name]==='dead') return Promise.resolve(false);
  voiceProbe[v.name]='testing';
  return new Promise(res=>{
    let done=false;
    const finish=ok=>{ if(done) return; done=true; voiceProbe[v.name]=ok?'live':'dead'; res(ok); };
    try{
      const u=new SpeechSynthesisUtterance('ok');
      u.voice=v; u.volume=0; u.rate=1.6; u.lang=v.lang||'en-US';
      u.onstart=()=>finish(true);
      u.onerror=()=>finish(false);
      u.onend=()=>finish(voiceProbe[v.name]==='live');
      window.speechSynthesis.speak(u);
      setTimeout(()=>finish(false),2000);      // silence for two seconds is a dead voice
    }catch(e){ finish(false); }
  });
}
function voiceChosen(){
  if(!P.ttsVoice) return null;
  return ttsVoicesEn().find(v=>v.name===P.ttsVoice)||null;
}

const VOICE_SAMPLE='Question 1 of 65. A company needs a storage solution that stays '+
  'available when one Availability Zone fails. Which service meets this requirement?';

function renderVoice(){
  const P1=voicePreset();
  const rate=voiceRate(), pitch=voicePitch();
  $('voiceSample').textContent=VOICE_SAMPLE;
  $('voiceRate').value=Math.round(rate*100);
  $('voiceRateVal').textContent=rate.toFixed(2).replace(/0$/,'')+'\\u00d7';
  $('voicePitch').value=Math.round(pitch*100);
  $('voicePitchVal').textContent=pitch.toFixed(2).replace(/0$/,'');

  const L=$('voicePresets'); L.innerHTML='';
  VOICE_PRESETS.forEach(p=>{
    const b=document.createElement('button');
    b.className='vpre'+(p.id===P1.id?' on':'');
    b.setAttribute('aria-pressed',p.id===P1.id?'true':'false');
    b.innerHTML='<span class="vem">'+p.em+'</span><span style="flex:1;min-width:0">'+
      '<span class="vnm">'+esc(p.nm)+'</span>'+
      '<span class="vds">'+esc(p.ds)+'</span>'+
      '<span class="vheb" dir="rtl">'+esc(p.heb)+'</span></span>'+
      '<span class="vtest">\\u25b6</span>';
    b.setAttribute('aria-label',p.nm+' \\u2014 '+p.ds);
    b.onclick=e=>{
      const onTest=e.target.classList&&e.target.classList.contains('vtest');
      P.voicePreset=p.id;
      if(!onTest){ delete P.ttsRate; delete P.ttsPitch; }   // a preset resets the sliders
      saveProfile(); renderVoice();
      voiceSay();
    };
    L.appendChild(b);
  });

  const VL=$('voiceList'); VL.innerHTML='';
  const en=ttsVoicesEn();
  if(!en.length){
    $('voiceCheckNote').textContent='This browser has no English voice installed, so nothing can be read aloud.';
  }
  const auto=document.createElement('button');
  auto.className='vvoice'+(P.ttsVoice?'':' on');
  auto.innerHTML='<span class="vn">Let the browser choose</span><span class="vtag good">SAFE</span>';
  auto.setAttribute('aria-label','Let the browser choose the voice');
  auto.onclick=()=>{ delete P.ttsVoice; saveProfile(); renderVoice(); voiceSay(); };
  VL.appendChild(auto);

  en.forEach(v=>{
    const st=voiceProbe[v.name];
    const b=document.createElement('button');
    b.className='vvoice'+(P.ttsVoice===v.name?' on':'')+(st==='dead'?' dead':'');
    b.innerHTML='<span class="vn">'+esc(v.name)+'</span>'+
      '<span class="vtag'+(st==='live'?' good':st==='dead'?' bad':'')+'">'+
      (st==='live'?'WORKS':st==='dead'?'SILENT':'\\u2026')+'</span>';
    b.setAttribute('aria-label',v.name+(st==='dead'?' \\u2014 does not speak on this device':''));
    b.disabled=(st==='dead');
    b.onclick=()=>{ P.ttsVoice=v.name; saveProfile(); renderVoice(); voiceSay(); };
    VL.appendChild(b);
  });

  const dead=en.filter(v=>voiceProbe[v.name]==='dead').length;
  const live=en.filter(v=>voiceProbe[v.name]==='live').length;
  $('voiceFoot').textContent=dead
    ? (dead+' of the '+en.length+' voices this device reports do not actually make a sound. '+
       'They are greyed out rather than hidden, so it is clear they were tried.')
    : (live?('All '+live+' voices here speak.'):'');
}

// speak the sample with whatever is selected right now
function voiceSay(){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return; }
  ttsStop();
  setTimeout(()=>{
    try{
      const ss=window.speechSynthesis;
      const p=voicePreset();
      const parts=p.gap?ttsChunks(VOICE_SAMPLE,80):[VOICE_SAMPLE];
      parts.forEach(txt=>{
        const u=new SpeechSynthesisUtterance(txt);
        u.rate=voiceRate(); u.pitch=voicePitch(); u.volume=voiceVolume(); u.lang='en-US';
        const v=voiceChosen(); if(v) u.voice=v;
        ss.speak(u);
      });
    }catch(e){}
  },0);
}

async function voiceCheckAll(){
  const en=ttsVoicesEn();
  const note=$('voiceCheckNote');
  if(!en.length) return;
  for(let i=0;i<en.length;i++){
    if(note) note.textContent='Checking which ones actually speak\\u2026 '+(i+1)+' of '+en.length;
    await voiceTest(en[i]);
    renderVoice();
  }
  if(note) note.textContent='Each one below was asked to speak. Anything that stayed silent is marked.';
  renderVoice();
}

function openVoice(){
  ttsLoadVoices();
  renderVoice();
  go('voiceScreen');
  if(!TEST) voiceCheckAll();
}
"""

sub("""// ================= FULL EXAM SIMULATION =================""",
    ENGINE + """
// ================= FULL EXAM SIMULATION =================""")

# --------------------------------------- the reading itself honours the choice
sub("""    const u=new SpeechSynthesisUtterance(part);
    u.rate=P.ttsRate||1; u.lang='en-US';
    if(voice) u.voice=voice;
    if(k===0) u.onstart=()=>{ started=true; if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); } };""",
"""    const u=new SpeechSynthesisUtterance(part);
    u.rate=typeof voiceRate==='function'?voiceRate():1;
    u.pitch=typeof voicePitch==='function'?voicePitch():1;
    u.volume=typeof voiceVolume==='function'?voiceVolume():1;
    u.lang='en-US';
    if(voice) u.voice=voice;
    if(k===0) u.onstart=()=>{ started=true; if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); } };""")

# the plain retry drops the chosen voice but keeps the speed, since speed never broke anything
sub("""  const voice=plain?null:ttsVoice();""",
"""  // A chosen voice is the thing most likely to be at fault when nothing speaks, so the
  // watchdog's retry drops it. Speed and pitch have never broken anything, so they stay.
  const voice=plain?null:(typeof voiceChosen==='function'?voiceChosen():null);""")

# Dictation gets its gaps by chunking smaller
sub("""  const chunks=plain?[String(text)]:ttsChunks(text);""",
"""  const p=(typeof voicePreset==='function')?voicePreset():null;
  const chunks=plain?[String(text)]:ttsChunks(text,p&&p.gap?80:160);""")

sub("""$('themeOpen').onclick=""", """$('voiceOpen').onclick=()=>openVoice();
$('voiceBack').onclick=()=>{ ttsStop(); go('homeScreen'); renderHome(); };
$('voiceTry').onclick=()=>voiceSay();
$('voiceRate').oninput=e=>{ P.ttsRate=clamp01(Number(e.target.value)/100,0.5,2.2); renderVoice(); };
$('voiceRate').onchange=()=>{ saveProfile(); voiceSay(); };
$('voicePitch').oninput=e=>{ P.ttsPitch=clamp01(Number(e.target.value)/100,0.4,2); renderVoice(); };
$('voicePitch').onchange=()=>{ saveProfile(); voiceSay(); };
$('themeOpen').onclick=""")

sub("""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend,""",
"""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend,
    VOICE_PRESETS, voicePreset, voiceRate, voicePitch, voiceVolume, voiceChosen,
    voiceTest, voiceProbe, renderVoice, voiceSay, voiceCheckAll, openVoice, VOICE_SAMPLE,""")

PAGE.write_text(s, encoding="utf-8")
print("voice engine wired \u00b7 page %.2f MB" % (len(s) / 1e6))
