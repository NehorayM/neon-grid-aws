#!/usr/bin/env python3
"""Tell "A adds a queue" from "A gp3 volume tops out".

The article rule was too blunt: a sentence-initial A followed by a lowercase word was read
as the article whenever no other option letter appeared. But "A adds a queue for no
benefit" is option A, and the suite caught it.

What separates them is the word that follows. An option letter is a subject, so the next
word is its verb — "adds", "controls", "means", "requires", "is", "has", "lacks", "fails" —
or a modal, "cannot", "only", "still". An article introduces a noun phrase, so the next
word is a modifier: "gp3 volume", "single AZ", "read replica". Third-person singular verbs
end in s, which does most of the work, and the modals that do not are listed.

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


sub("""    const scope=ctx||p;
    const articleA=/^A\\s+[a-z]/.test(scope)&&
      !letters.some(L=>L!=='A'&&(bareRe(L).test(scope)||namedRe(L).test(scope)));""",
"""    const scope=ctx||p;
    const articleA=isArticleA(scope)&&
      !letters.some(L=>L!=='A'&&(bareRe(L).test(scope)||namedRe(L).test(scope)));""")

sub("""// The written explanation names options by letter.""",
"""// A leading "A" is the option when the next word is its verb ("A adds a queue", "A cannot
// scale") and the article when the next word modifies a noun ("A gp3 volume tops out", "A
// single AZ fails"). Third-person singular verbs end in s; the modals that do not are named.
const A_VERBY=/^(cannot|can|could|will|would|should|must|may|might|do|did|only|still|never|also|again|both|alone|then|just|simply|merely)$/i;
function isArticleA(text){
  const m=/^A\\s+([A-Za-z][A-Za-z0-9-]*)/.exec(String(text||''));
  if(!m) return false;
  const next=m[1];
  return !(/s$/i.test(next)||A_VERBY.test(next));
}
// The written explanation names options by letter.""")

PAGE.write_text(s, encoding="utf-8")
print("verb or noun decides it · page %.2f MB" % (len(s) / 1e6))
