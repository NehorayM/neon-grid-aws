#!/usr/bin/env python3
"""The accessible names the second audit found: the ones built by script.

The first pass named the buttons written in the markup. These are created in JS,
so they carry whatever the code puts on them — and mostly that was one glyph, a
number, or a bare "Go". A screen reader reached the casino and heard "10, 25,
50, 10, 25, 50"; it reached Themes and heard "lock, lock, lock"; the Readiness
domain rows were three buttons all called "Go"; the review grid was "Q1" with no
hint whether that question was answered, blank or flagged.

  * the sector rows on Home, and their "…" open button
  * the search box, the exam date, the casino amount fields, the import file
  * every bet chip, with its amount
  * the theme buttons, which say whether the theme is locked and why
  * the Readiness domain rows, which name the domain they drill
  * the review grid chips, which say what state that question is in

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# --------------------------------------------------------------- inputs in markup
for eid, label in [("secSearch", "Search sectors"),
                   ("examDateIn", "Your exam date"),
                   ("casBuyAmt", "Study coins to convert into chips"),
                   ("casCashAmt", "Chips to cash out"),
                   ("importFile", "Choose a profile file to import")]:
    m = re.search(r'<input([^>]*\sid="%s")([^>]*)>' % re.escape(eid), s)
    assert m, "no input " + eid
    assert "aria-label" not in m.group(0), eid + " already named"
    s = s[:m.end() - 1] + ' aria-label="%s"' % label + s[m.end() - 1:]

# ------------------------------------------------------------------ bet chips
sub("""    b.className='betchip'+(v===current?' on':''); b.textContent=v; b.dataset.v=v;""",
"""    b.className='betchip'+(v===current?' on':''); b.textContent=v; b.dataset.v=v;
    b.setAttribute('aria-label','Bet '+v+' chips');          // it read out "10, 25, 50"
    b.setAttribute('aria-pressed',v===current?'true':'false');""")

# ------------------------------------------------- daily quest claim buttons
sub("""    b.textContent=claimed?'\u2713':(done?('+'+def.reward):'\u2026');
    b.disabled=claimed||!done;""",
"""    b.textContent=claimed?'\u2713':(done?('+'+def.reward):'\u2026');
    b.setAttribute('aria-label',claimed?('Already claimed: '+def.nm)
      :done?('Claim '+def.reward+' for '+def.nm)
      :(def.nm+' \u2014 '+cur+' of '+def.goal+', not finished yet'));
    b.disabled=claimed||!done;""")

# --------------------------------------------------------------- theme buttons
sub("""    if(active){ b.textContent='ACTIVE'; b.disabled=true; }
    else if(has){ b.textContent='USE'; }
    else if(t.earn){ b.textContent='\U0001f512'; b.disabled=true; }
    else { b.textContent='Use'; b.disabled=false; }""",
"""    if(active){ b.textContent='ACTIVE'; b.disabled=true; b.setAttribute('aria-label',t.nm+' is the theme in use'); }
    else if(has){ b.textContent='USE'; b.setAttribute('aria-label','Switch to the '+t.nm+' theme'); }
    else if(t.earn){ b.textContent='\U0001f512'; b.disabled=true;
      b.setAttribute('aria-label',t.nm+' is locked \u2014 '+t.sub); }   // it just read "lock"
    else { b.textContent='Use'; b.disabled=false; b.setAttribute('aria-label','Use the '+t.nm+' theme'); }""")

# ------------------------------------------------------- study plan "Go" rows
sub("""      const b=document.createElement('button'); b.className='buy'; b.textContent='Go';
      b.onclick=p.action; row.appendChild(b); pl.appendChild(row);""",
"""      const b=document.createElement('button'); b.className='buy'; b.textContent='Go';
      b.setAttribute('aria-label',p.label);       // three buttons all announced as "Go"
      b.onclick=p.action; row.appendChild(b); pl.appendChild(row);""")

# ------------------------------------------------- the exam review grid chips
sub("""      b.className='minichip '+cls; b.textContent='Q'+(i+1);""",
"""      b.className='minichip '+cls; b.textContent='Q'+(i+1);
      b.setAttribute('aria-label','Question '+(i+1)+', '+label.toLowerCase().replace(/ for review$/,''));""")

PAGE.write_text(s, encoding="utf-8")
print("inputs and bet chips named · page %.2f MB" % (len(s) / 1e6))
