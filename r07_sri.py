#!/usr/bin/env python3
"""Round 7: pin the auth library and make the browser check it.

Performance was reviewed first and is clean: 132 ms to interactive, ~9 ms for every JSON
blob combined, every render under 1 ms, an exam tick costs 0.07 ms and 8 DOM writes, and an
idle home screen does nothing at all. Nothing there worth changing.

What this round does change: supabase-js was loaded as `@2`, which is whatever 2.x the CDN
serves on the day, with no integrity check — and it runs with access to the signed-in
session. A bad release or a compromised publish under @2 would run in this page unchecked.
It is now pinned to 2.117.0 (byte-identical to what @2 serves today, so nothing changes in
behaviour) with a sha384 SRI hash, and the browser refuses a file that does not match. The
existing onerror path already turns a refused or unreachable script into "you are still
playing offline", so a mismatch degrades exactly like no network.

To upgrade later: bump the version, recompute the hash with
  curl -sSL <url> | openssl dgst -sha384 -binary | openssl base64 -A

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

sub("""    const s=document.createElement('script');
    s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js';
    s.onload=done;""",
"""    const s=document.createElement('script');
    // Pinned, and checked by the browser. `@2` meant whatever 2.x the CDN served that day,
    // running unchecked with access to the signed-in session. A file that does not match the
    // hash is refused, and onerror below turns that into offline play, same as no network.
    s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.0/dist/umd/supabase.js';
    s.integrity='sha384-xPW3QHswsICVC2mW6BFNwMbhpLkbZ133fKOhxNx3QGGgAOJfL3O9t8r2aWn1aez6';
    s.crossOrigin='anonymous';
    s.onload=done;""")

PAGE.write_text(s, encoding="utf-8")
print("supabase-js pinned with SRI")
