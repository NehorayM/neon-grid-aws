#!/usr/bin/env python3
"""Start a line with a capital, unless the first word is a service name.

A handful of lines open lowercase because the source sentence did: "the console (C) shows
no access data", "and D's SNS retries eventually exhaust and drop the message". Sitting
under an option as its own line, they read as if something were missing.

Capitalising blindly would be worse: "io2 supports up to 64,000 IOPS" must not become "Io2".
So only a leading ordinary English word — a determiner, pronoun or conjunction — is
capitalised, and a leading conjunction is dropped first. Anything else is left exactly as
the source wrote it.

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


sub("""  const stop=x=>x.replace(/[\\s,;]+$/,'').replace(/([^.!?])$/,'$1.');""",
"""  const stop=x=>x.replace(/[\\s,;]+$/,'').replace(/([^.!?])$/,'$1.');
  // Only an ordinary English opener is capitalised. "io2 supports up to 64,000 IOPS" and
  // "gp3 tops out" are service names and are left exactly as written.
  const OPENER=/^(the|this|that|these|those|it|its|they|their|a|an|all|both|each|every|only|most|many|some|no|not|none|neither|either)\\b/;
  const CONJ=/^(and|but|or|so)\\s+/i;
  const open=x=>{
    const y=x.replace(CONJ,'');
    return OPENER.test(y)||/^[a-z]/.test(y)&&CONJ.test(x)
      ? y.charAt(0).toUpperCase()+y.slice(1) : x;
  };""")

sub("""    byLetter[L]=leadFirst(out[L].map(stop).join(' '),L);""",
    """    byLetter[L]=open(leadFirst(out[L].map(stop).join(' '),L));""")

sub("""  const leftover=rest.map(stop).join(' ').trim();""",
    """  const leftover=open(rest.map(stop).join(' ').trim());""")

PAGE.write_text(s, encoding="utf-8")
print("lines open with a capital, service names untouched · page %.2f MB" % (len(s) / 1e6))
