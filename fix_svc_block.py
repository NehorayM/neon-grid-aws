#!/usr/bin/env python3
"""The "services in this question" block was one underlined, back-to-front paragraph.

Reported with a screenshot, in no uncertain terms. When the service definitions moved out of
the options into their own folded block (exam rounds 1-2), two things came with them that only
worked where they had been:

  - the container was a <u> (b and i were taken inside an option) — it underlines by default,
    and the rule that removed the underline was scoped to `.exeach .exopt`;
  - every rule that put a service on its own line — the name as a small LTR tag, the Hebrew as
    its own right-aligned block — was scoped to `.exeach .exopt` too.

In the new block none of it matched, so the names ("RDS", "DynamoDB") ran straight into the
Hebrew around them with no break, bidi reordered the lot, and all of it was underlined.

Now it is a <div>, and each service is its own row: the name on the left, left-to-right; the
Hebrew under it, right-to-left and isolated so the two never reorder each other.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

sub("""      '<u class="exsvc">'+defs.join('')+'</u></details>');""",
"""      '<div class="exsvc">'+defs.join('')+'</div></details>');""")
sub("""      terms.forEach(t=>defs.push('<span class="svcline"><b>'+esc(asWritten(txt,t.t))+'</b><span dir="rtl">'+esc(t.d)+'</span></span>'));""",
"""      terms.forEach(t=>defs.push('<div class="svcline"><b dir="ltr">'+esc(asWritten(txt,t.t))+'</b><span dir="rtl" lang="he">'+esc(t.d)+'</span></div>'));""")

sub(""".exmore>.exwhy,.exmore>.exsvc{display:block;padding:0 12px 10px}""",
""".exmore>.exwhy,.exmore>.exsvc{display:block;padding:0 12px 10px}
/* the services block: one row per service — the name as a tag, the Hebrew under it, right to left */
.exmore>.exsvc{display:flex;flex-direction:column;gap:0;padding:0 12px 6px;text-decoration:none}
.exmore .svcline{display:flex;flex-direction:column;align-items:stretch;gap:4px;padding:9px 0;
  border-top:1px solid var(--line)}
.exmore .svcline:first-child{border-top:0;padding-top:2px}
.exmore .svcline>b{align-self:flex-start;direction:ltr;unicode-bidi:isolate;font-family:var(--mono);
  font-size:11px;font-weight:650;letter-spacing:.3px;color:var(--cyan);padding:2px 8px;border-radius:6px;
  background:color-mix(in srgb, var(--cyan) 10%, transparent);border:1px solid color-mix(in srgb, var(--cyan) 28%, transparent)}
.exmore .svcline>span{display:block;direction:rtl;unicode-bidi:isolate;text-align:right;
  font-size:13px;line-height:1.65;color:#d3d9e2}""")
PAGE.write_text(s, encoding="utf-8"); print("services block: one row per service, no underline, bidi isolated")
