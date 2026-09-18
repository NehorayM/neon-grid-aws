#!/usr/bin/env python3
"""One-shot restyle of index.html: quieter palette, flatter surfaces, more air.

The feedback was that the app looked dense, harsh and machine-made. Three things
caused most of that:

  1. Surfaces and borders were tinted with the accent colour (applyTheme derived
     --surface/--line/--panel from the theme's cyan), so every panel glowed.
  2. Six saturated neons competed on one screen, and the sector grid generated a
     different hue for all 23 sectors.
  3. Every box had a gradient, a coloured shadow and a tight padding.

This script fixes the cause rather than painting over it: neutral surfaces, one
accent with a few muted semantic colours, flat fills, and looser spacing.
Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re
import sys

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
edits = []


def sub(old, new, count=1):
    edits.append((old, new, count))


# --------------------------------------------------------------- A. tokens
sub("""  --bg:#05060f; --bg2:#0b0f22; --panel:rgba(255,255,255,.045);
  --line:var(--line); --line2:var(--line);
  --surface:rgba(255,255,255,.05); --surface2:rgba(255,255,255,.08);
  --grid:var(--line); --glow1:rgba(60,224,255,.16); --glow2:rgba(255,79,216,.13);
  --cyan:#3ce0ff; --mag:#ff4fd8; --lime:#6bff9e; --gold:#ffd75e; --red:#ff5d6c; --violet:#9b6bff;
  --txt:#eaf4ff; --dim:#8aa0bd;""",
"""  --bg:#0f1116; --bg2:#161a22; --panel:rgba(255,255,255,.028);
  /* surfaces stay neutral: colour belongs to the accents, not to every box */
  --line:rgba(255,255,255,.09); --line2:rgba(255,255,255,.2);
  --surface:rgba(255,255,255,.035); --surface2:rgba(255,255,255,.06);
  --grid:rgba(255,255,255,.028); --glow1:rgba(120,170,205,.07); --glow2:rgba(150,140,190,.05);
  --cyan:#7ab6d6; --mag:#c08ab4; --lime:#85c49b; --gold:#d4ae76; --red:#d4848e; --violet:#9691cc;
  --txt:#e7ebf1; --dim:#93a0b0;""")

# ------------------------------------------------------------ B. background
# the rotating conic sweep was the loudest thing on every screen
sub("""#grid-bg::before{content:"";position:absolute;inset:-30%;
  background:conic-gradient(from 0deg,transparent,var(--glow1),transparent 30%,var(--glow2),transparent 60%);
  animation:sweep 26s linear infinite}
@keyframes sweep{to{transform:rotate(360deg)}}
#grid-bg::after{content:"";position:absolute;inset:0;opacity:.32;
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),
                   linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:44px 44px;mask-image:linear-gradient(180deg,#000,transparent 78%)}""",
"""#grid-bg::after{content:"";position:absolute;inset:0;opacity:.5;
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),
                   linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:64px 64px;mask-image:linear-gradient(180deg,#000,transparent 55%)}""")
sub("""    radial-gradient(1200px 600px at 50% -10%, var(--glow1), transparent 60%),
    radial-gradient(900px 500px at 100% 110%, var(--glow2), transparent 60%),""",
    """    radial-gradient(1100px 520px at 50% -15%, var(--glow1), transparent 62%),
    radial-gradient(820px 460px at 100% 112%, var(--glow2), transparent 62%),""")

# --------------------------------------------------------- C. type and logo
sub("""h1.logo{font-size:clamp(26px,7.4vw,40px);font-weight:900;letter-spacing:2px;line-height:1.05;
  background:linear-gradient(96deg,var(--cyan),var(--mag) 60%,var(--violet));
  -webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 16px rgba(60,224,255,.3))}
.tagline{color:var(--dim);font-size:13px;margin-top:6px;max-width:330px;line-height:1.55}
h2.head{font-size:19px;font-weight:800;letter-spacing:.4px;margin-bottom:3px}""",
"""h1.logo{font-size:clamp(21px,5.2vw,27px);font-weight:600;letter-spacing:6px;line-height:1.1;
  color:var(--txt);text-transform:uppercase}
.tagline{color:var(--dim);font-size:12.5px;margin-top:9px;max-width:330px;line-height:1.55}
h2.head{font-size:18px;font-weight:650;letter-spacing:.2px;margin-bottom:4px}""")
sub(""".hero{display:flex;flex-direction:column;align-items:center;gap:3px;margin-bottom:14px;text-align:center}""",
    """.hero{display:flex;flex-direction:column;align-items:center;gap:3px;margin:8px 0 26px;text-align:center}""")

# --------------------------------------------------------------- D. buttons
sub("""  padding:14px 26px;border-radius:30px;font-weight:800;font-size:15px;color:#04101a;
  background:linear-gradient(120deg,var(--cyan),var(--violet));box-shadow:0 6px 26px rgba(60,224,255,.28)}
.btn:active{transform:scale(.96)}
.btn.ghost{background:none;border:1.5px solid var(--line);color:var(--txt);box-shadow:none}
.btn.gold{background:linear-gradient(120deg,var(--gold),#ff9d4f);box-shadow:0 6px 26px rgba(255,215,94,.26)}""",
"""  padding:13px 24px;border-radius:12px;font-weight:650;font-size:14.5px;color:#10161c;
  background:var(--cyan);transition:.15s}
.btn:hover{filter:brightness(1.07)}
.btn:active{transform:scale(.98)}
.btn.ghost{background:none;border:1px solid var(--line2);color:var(--txt)}
.btn.ghost:hover{background:var(--surface);filter:none}
.btn.gold{background:var(--gold);color:#1b1408}""")
sub(""".pillbtn{font-size:11.5px;font-weight:800;padding:7px 14px;border-radius:20px;white-space:nowrap;
  background:linear-gradient(120deg,var(--gold),#ff9d4f);color:#221600}""",
    """.pillbtn{font-size:11.5px;font-weight:650;padding:7px 14px;border-radius:9px;white-space:nowrap;
  background:var(--gold);color:#1b1408}""")
sub(""".buy{flex:none;font-family:var(--mono);font-size:12px;font-weight:800;padding:9px 13px;border-radius:12px;
  background:linear-gradient(120deg,var(--gold),#ff9d4f);color:#221600}""",
    """.buy{flex:none;font-size:12px;font-weight:650;padding:9px 14px;border-radius:9px;
  background:var(--surface2);border:1px solid var(--line2);color:var(--txt)}
.buy:hover{background:var(--cyan);border-color:var(--cyan);color:#10161c}""")
sub(""".unlockbtn{font-size:10.5px;font-weight:800;padding:6px 10px;border-radius:11px;white-space:nowrap;
  background:linear-gradient(120deg,var(--gold),#ff9d4f);color:#221600}""",
    """.unlockbtn{font-size:10.5px;font-weight:650;padding:6px 11px;border-radius:9px;white-space:nowrap;
  background:var(--gold);color:#1b1408}""")

# -------------------------------------------------- E. cards, tiles, items
sub(""".card{width:100%;max-width:var(--colw);margin:0 auto 10px;padding:14px 16px;border-radius:18px;
  background:var(--surface);border:1px solid var(--line);
  box-shadow:0 8px 26px rgba(0,0,0,.26)}
.card.accent-gold{border-color:rgba(255,215,94,.28);background:linear-gradient(168deg,rgba(255,215,94,.09),rgba(255,255,255,.03))}
.card.accent-cyan{border-color:rgba(60,224,255,.28);background:linear-gradient(168deg,rgba(60,224,255,.09),rgba(255,255,255,.03))}""",
""".card{width:100%;max-width:var(--colw);margin:0 auto 12px;padding:16px 18px;border-radius:14px;
  background:var(--surface);border:1px solid var(--line)}
/* accents mark a card without repainting it */
/* no overflow:hidden here — inside the screen's flex column it would let the card
   shrink below its own content */
.card.accent-gold,.card.accent-cyan{position:relative}
.card.accent-gold::before,.card.accent-cyan::before{content:"";position:absolute;
  left:0;top:12px;bottom:12px;width:2px;border-radius:2px}
.card.accent-gold::before{background:var(--gold)}
.card.accent-cyan::before{background:var(--cyan)}""")
sub(""".cardhead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}
.ch-t{font-size:13px;font-weight:700;color:#e4eefb;letter-spacing:.2px}""",
    """.cardhead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}
.ch-t{font-size:13px;font-weight:650;color:var(--txt);letter-spacing:.2px}""")
sub(""".sechead{width:100%;max-width:var(--colw);margin:18px auto 9px;font-size:11px;font-weight:800;letter-spacing:1.4px;
  text-transform:uppercase;color:var(--dim);display:flex;align-items:center;gap:10px}
.sechead::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--line),transparent)}""",
    """.sechead{width:100%;max-width:var(--colw);margin:30px auto 12px;font-size:10.5px;font-weight:600;letter-spacing:1.6px;
  text-transform:uppercase;color:var(--dim);display:flex;align-items:center;gap:10px}""")
sub(""".tiles{display:grid;grid-template-columns:1fr 1fr;gap:9px;width:100%;max-width:var(--colw);margin:0 auto}
.tile{display:flex;flex-direction:column;align-items:flex-start;gap:2px;padding:14px 14px 13px;border-radius:16px;
  background:var(--surface);border:1px solid var(--line);text-align:left;transition:.16s}
.tile:hover{border-color:var(--line2);background:var(--surface2);transform:translateY(-2px)}
.tile:active{transform:scale(.975)}
.tile .ic{font-size:21px;margin-bottom:3px}
.tile b{font-size:13.5px;font-weight:700}
.tile span:last-child{font-size:10.5px;color:var(--dim);line-height:1.35}
.tile.hero-tile{grid-column:1/-1;flex-direction:row;align-items:center;gap:13px;
  background:linear-gradient(110deg,rgba(60,224,255,.17),rgba(155,107,255,.13));
  border-color:rgba(60,224,255,.42)}
.tile.hero-tile .ic{font-size:27px;margin:0}
.tile.hero-tile b{font-size:15px}""",
""".tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;width:100%;max-width:var(--colw);margin:0 auto}
.tile{display:flex;flex-direction:column;align-items:flex-start;gap:3px;padding:15px 15px 14px;border-radius:12px;
  background:var(--surface);border:1px solid var(--line);text-align:left;transition:.15s}
.tile:hover{border-color:var(--line2);background:var(--surface2)}
.tile:active{transform:scale(.985)}
.tile .ic{font-size:17px;margin-bottom:6px;opacity:.75;filter:saturate(.7)}
.tile b{font-size:13.5px;font-weight:650}
.tile span:last-child{font-size:11px;color:var(--dim);line-height:1.45;margin-top:2px}
.tile.hero-tile{grid-column:1/-1;flex-direction:row;align-items:center;gap:14px;padding:17px 16px}
.tile.hero-tile .ic{font-size:20px;margin:0}
.tile.hero-tile b{font-size:14.5px}
.tile.hero-tile>div{min-width:0}""")
sub(""".item{display:flex;align-items:center;gap:12px;padding:13px 15px;border-radius:16px;
  background:linear-gradient(170deg,var(--surface2),var(--surface));
  border:1px solid var(--line);text-align:left;box-shadow:0 4px 16px rgba(0,0,0,.22)}""",
    """.item{display:flex;align-items:center;gap:13px;padding:14px 16px;border-radius:12px;
  background:var(--surface);border:1px solid var(--line);text-align:left}""")
sub(""".item .em{font-size:22px;flex:none}
.item .nm{font-size:13.5px;font-weight:700}""",
    """.item .em{font-size:17px;flex:none;opacity:.75;filter:saturate(.7)}
.item .nm{font-size:13.5px;font-weight:650}""")
sub(""".list{display:flex;flex-direction:column;gap:9px;width:100%;max-width:var(--colw);margin:0 auto}""",
    """.list{display:flex;flex-direction:column;gap:8px;width:100%;max-width:var(--colw);margin:0 auto}""")
sub(""".panel{width:100%;max-width:var(--colw);margin:10px auto 0;padding:12px 14px;border-radius:16px;
  background:linear-gradient(170deg,var(--surface2),var(--surface));
  border:1px solid var(--line)}""",
    """.panel{width:100%;max-width:var(--colw);margin:10px auto 0;padding:14px 16px;border-radius:12px;
  background:var(--surface);border:1px solid var(--line)}""")
sub(""".minichip{font-size:11.5px;font-weight:600;padding:8px 13px;border-radius:20px;
  background:var(--surface);border:1px solid var(--line);color:#cfe2f7;transition:.15s}""",
    """.minichip{font-size:11.5px;font-weight:550;padding:8px 13px;border-radius:9px;
  background:var(--surface);border:1px solid var(--line);color:var(--dim);transition:.15s}
.minichip:hover{color:var(--txt)}""")
sub(""".stat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:9px 6px;text-align:center}
.stat b{display:block;font-family:var(--mono);font-size:15px;font-weight:700}""",
    """.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 6px;text-align:center}
.stat b{display:block;font-family:var(--mono);font-size:16px;font-weight:600}""")

# ------------------------------------------------------- F. progress bars
# two-colour gradients on every bar read as decoration; one colour reads as data
for old, new in [
    (".qprog i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--mag));transition:width .4s}",
     ".qprog i{display:block;height:100%;background:var(--cyan);transition:width .4s}"),
    (".dt i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--lime));transition:width .5s}",
     ".dt i{display:block;height:100%;background:var(--cyan);transition:width .5s}"),
    (".goal .gt i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--lime));transition:width .45s}",
     ".goal .gt i{display:block;height:100%;background:var(--cyan);transition:width .45s}"),
    (".goal.close .gt i{background:linear-gradient(90deg,var(--gold),var(--mag))}",
     ".goal.close .gt i{background:var(--gold)}"),
    (".track i{display:block;height:100%;background:linear-gradient(90deg,var(--gold),var(--mag));transition:width .5s}",
     ".track i{display:block;height:100%;background:var(--gold);transition:width .5s}"),
    (".qtrack i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--lime));transition:width .4s}",
     ".qtrack i{display:block;height:100%;background:var(--cyan);transition:width .4s}"),
    (".daily .track i{display:block;height:100%;background:linear-gradient(90deg,var(--gold),var(--mag));transition:width .5s}",
     ".daily .track i{display:block;height:100%;background:var(--gold);transition:width .5s}"),
    (".cell.on{background:linear-gradient(90deg,var(--gold),var(--mag));box-shadow:0 0 10px rgba(255,215,94,.6)}",
     ".cell.on{background:var(--gold)}"),
    (".lcell.on{background:linear-gradient(135deg,var(--gold),#ff9d4f);color:#221600;font-weight:800}",
     ".lcell.on{background:var(--gold);color:#1b1408;font-weight:650}"),
    ("#gtimer{display:block;height:100%;width:100%;background:linear-gradient(90deg,var(--lime),var(--gold));transition:width .12s linear}",
     "#gtimer{display:block;height:100%;width:100%;background:var(--lime);transition:width .12s linear}"),
    ("#gtimer.low{background:linear-gradient(90deg,var(--red),var(--mag))}",
     "#gtimer.low{background:var(--red)}"),
    ("#qTimerFill{display:block;height:100%;width:100%;background:linear-gradient(90deg,var(--lime),var(--gold));transition:width .25s linear}",
     "#qTimerFill{display:block;height:100%;width:100%;background:var(--lime);transition:width .25s linear}"),
    ("#qTimerFill.low{background:linear-gradient(90deg,var(--red),var(--mag));animation:tick .6s ease-in-out infinite}",
     "#qTimerFill.low{background:var(--red);animation:tick .6s ease-in-out infinite}"),
]:
    sub(old, new)

# --------------------------------------------------------- G. sector cards
sub(""".seccard{position:relative;text-align:left;padding:13px 13px 12px;border-radius:18px;overflow:hidden;
  background:linear-gradient(170deg,var(--surface2),var(--surface));
  border:1px solid var(--line);min-height:100px;display:flex;flex-direction:column;gap:6px;
  box-shadow:0 6px 20px rgba(0,0,0,.3);transition:.18s}
.seccard:hover{border-color:var(--line2);transform:translateY(-2px)}
.seccard:active{transform:scale(.975)}
.seccard .glow{position:absolute;inset:-40% -20% auto;height:90px;filter:blur(28px);opacity:.5}
.seccard .nm{position:relative;font-size:12.5px;font-weight:700;line-height:1.3;min-height:32px}""",
""".seccard{position:relative;text-align:left;padding:14px;border-radius:12px;overflow:hidden;
  background:var(--surface);border:1px solid var(--line);min-height:96px;
  display:flex;flex-direction:column;gap:7px;transition:.15s}
.seccard:hover{border-color:var(--line2);background:var(--surface2)}
.seccard:active{transform:scale(.985)}
.seccard .glow{display:none}
.seccard .nm{position:relative;font-size:12.5px;font-weight:650;line-height:1.35;min-height:32px}""")
sub(""".mixcard{grid-column:1/-1;background:linear-gradient(110deg,rgba(60,224,255,.14),rgba(255,79,216,.14));
  border-color:rgba(60,224,255,.4);min-height:auto;flex-direction:row;align-items:center;gap:12px}
.mixcard .em{font-size:26px}""",
    """.mixcard{grid-column:1/-1;min-height:auto;flex-direction:row;align-items:center;gap:13px;padding:15px 14px}
.mixcard .em{font-size:18px;opacity:.75;filter:saturate(.7)}""")
sub(""".secgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:9px;""",
    """.secgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;""")

# -------------------------------------------------------- H. question card
sub(""".qcard{background:linear-gradient(180deg,var(--surface2),var(--surface));
  border:1px solid var(--line);border-radius:20px;padding:20px 18px 18px;
  box-shadow:0 10px 34px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.07)}
.qtext{font-size:17px;line-height:1.72;color:#f4f9ff;letter-spacing:.1px;font-weight:450;""",
    """.qcard{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px 18px}
.qtext{font-size:16.5px;line-height:1.7;color:var(--txt);letter-spacing:.1px;font-weight:400;""")
sub(""".opt{display:flex;gap:13px;align-items:flex-start;text-align:left;padding:15px 15px;border-radius:16px;
  background:var(--surface);border:1.5px solid var(--line);
  font-size:15px;line-height:1.6;color:#e9f3ff;transition:.15s;text-wrap:pretty}""",
    """.opt{display:flex;gap:13px;align-items:flex-start;text-align:left;padding:15px;border-radius:11px;
  background:var(--surface);border:1px solid var(--line);
  font-size:14.5px;line-height:1.6;color:var(--txt);transition:.15s;text-wrap:pretty}""")
sub(""".multi{margin-top:9px;display:inline-block;font-family:var(--mono);font-size:10.5px;color:var(--gold);
  border:1px dashed rgba(255,215,94,.45);padding:3px 9px;border-radius:8px}""",
    """.multi{margin-top:10px;display:inline-block;font-family:var(--mono);font-size:10.5px;color:var(--gold);
  border:1px solid var(--line);padding:3px 9px;border-radius:6px}""")
sub(""".tag{font-family:var(--mono);font-size:10px;letter-spacing:.6px;text-transform:uppercase;
  padding:5px 10px;border-radius:8px;background:var(--panel);border:1px solid var(--line);color:var(--dim)}""",
    """.tag{font-family:var(--mono);font-size:10px;letter-spacing:.6px;text-transform:uppercase;
  padding:5px 10px;border-radius:6px;background:var(--surface);border:1px solid var(--line);color:var(--dim)}""")

# ------------------------------------------------- I. remaining glow/shadow
for old, new in [
    ("#gCombo{font-family:var(--mono);font-size:13px;font-weight:800;color:var(--gold);\n  text-shadow:0 0 12px rgba(255,215,94,.6)}",
     "#gCombo{font-family:var(--mono);font-size:13px;font-weight:650;color:var(--gold)}"),
    ("#gCombo.hot{color:var(--mag);text-shadow:0 0 16px rgba(255,79,216,.8);animation:comboPulse .5s ease-in-out infinite}",
     "#gCombo.hot{color:var(--mag);animation:comboPulse .5s ease-in-out infinite}"),
    (".charge{display:flex;align-items:center;gap:8px;padding:9px 13px;border-radius:14px;\n  background:linear-gradient(100deg,rgba(255,215,94,.12),rgba(255,79,216,.1));\n  border:1px solid rgba(255,215,94,.35)}",
     ".charge{display:flex;align-items:center;gap:8px;padding:9px 13px;border-radius:10px;\n  background:var(--surface);border:1px solid var(--line)}"),
    (".charge.ready{border-color:var(--lime);background:linear-gradient(100deg,rgba(107,255,158,.18),rgba(60,224,255,.12));\n  animation:readyPulse 1.4s ease-in-out infinite}\n@keyframes readyPulse{50%{box-shadow:0 0 18px rgba(107,255,158,.35)}}",
     ".charge.ready{border-color:var(--lime)}"),
    (".crsrail i.now{background:var(--gold);box-shadow:0 0 10px rgba(255,215,94,.5)}",
     ".crsrail i.now{background:var(--gold)}"),
    (".lrndot.now{border-color:var(--gold);color:var(--gold);box-shadow:0 0 12px rgba(255,215,94,.22)}",
     ".lrndot.now{border-color:var(--gold);color:var(--gold)}"),
    ("  border-radius:50%;background:var(--lime);border:2px solid var(--bg);box-shadow:0 0 8px rgba(107,255,158,.6)}",
     "  border-radius:50%;background:var(--lime);border:2px solid var(--bg)}"),
    (".rankring.syncing::after{background:var(--gold);box-shadow:0 0 8px rgba(255,215,94,.6)}",
     ".rankring.syncing::after{background:var(--gold)}"),
]:
    sub(old, new)

# ------------------------------------------------------------ J. the search
sub(""".search{width:100%;max-width:var(--colw);margin:0 auto 10px;padding:11px 14px;border-radius:14px;
  background:rgba(255,255,255,.06);border:1px solid var(--line);color:var(--txt);font-size:13.5px}""",
    """.search{width:100%;max-width:var(--colw);margin:0 auto 12px;padding:12px 14px;border-radius:10px;
  background:var(--surface);border:1px solid var(--line);color:var(--txt);font-size:13.5px}
.search:focus{outline:none;border-color:var(--line2)}""")

# ------------------------------------- K. the theme no longer paints surfaces
sub("""    // surfaces, borders, grid and background glow all derive from the palette,
    // so a theme changes the whole artifact rather than just the accents
    set('--line',  rgba(t.c.cyan,.20));
    set('--line2', rgba(t.c.cyan,.45));
    set('--surface', rgba(t.c.cyan,.055));
    set('--surface2',rgba(t.c.cyan,.10));
    set('--grid',  t.grid);
    set('--glow1', rgba(t.c.cyan,.16));
    set('--glow2', rgba(t.c.mag,.13));
    set('--panel', rgba(t.c.cyan,.05));""",
"""    // surfaces and borders stay neutral whatever the theme — tinting every panel
    // with the accent is what made the whole interface look washed in colour.
    // A theme changes the accents and the faint background wash, nothing else.
    set('--line',  'rgba(255,255,255,.09)');
    set('--line2', 'rgba(255,255,255,.2)');
    set('--surface', 'rgba(255,255,255,.035)');
    set('--surface2','rgba(255,255,255,.06)');
    set('--panel', 'rgba(255,255,255,.028)');
    set('--grid',  'rgba(255,255,255,.028)');
    set('--glow1', rgba(t.c.cyan,.07));
    set('--glow2', rgba(t.c.mag,.05));""")

# ------------------------------------- L. one accent per sector, not twenty-three
sub("""const hueOf=i=>(i*47)%360;
const secColor=i=>'hsl('+hueOf(i)+' 90% 62%)';""",
"""// Sectors used to get a hue each, which turned the grid into a colour wheel.
// They now share the accent and are told apart by their name and their progress.
const hueOf=i=>(i*47)%360;
const secColor=()=>'var(--cyan)';""")

s = PAGE.read_text(encoding="utf-8")
missing = [old for old, _, _ in edits if s.count(old) < 1]
if missing:
    for m in missing:
        print("NOT FOUND:\n" + m[:200] + "\n", file=sys.stderr)
    sys.exit("%d edits did not match" % len(missing))
for old, new, count in edits:
    s = s.replace(old, new, count)
PAGE.write_text(s, encoding="utf-8")
print(f"applied {len(edits)} edits, page is {len(s)/1e6:.2f} MB")
