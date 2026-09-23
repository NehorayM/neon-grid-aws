#!/usr/bin/env python3
"""Round 6: the exam countdown was a day short west of UTC.

examDaysLeft() parsed the date input with new Date('2026-10-01'). A date-only ISO string
is read as UTC midnight, and setHours(0) then moves it to midnight of whatever LOCAL day
that instant falls on. East of UTC (Israel, UTC+3) that is still 1 October, so it looked
right here. West of UTC it is 30 September — the countdown ran a day short everywhere in the
Americas, and on the exam day itself the app said "Your exam date has passed".

The input is always YYYY-MM-DD, so it is read as a local calendar date instead.

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

sub("""  const now=new Date(); now.setHours(0,0,0,0);
  const d=new Date(P.examDate);
  if(isNaN(d.getTime())) return null;
  d.setHours(0,0,0,0);""",
"""  const now=new Date(); now.setHours(0,0,0,0);
  const d=localDate(P.examDate);
  if(!d) return null;""")

sub("""const EXAM_MAX_DAYS=730;""",
"""const EXAM_MAX_DAYS=730;
// new Date('2026-10-01') is UTC midnight, which west of UTC is the evening before — the
// countdown ran a day short across the Americas and called exam day "passed". The date input
// hands back YYYY-MM-DD, so build it as a local calendar date.
function localDate(iso){
  const m=/^(\\d{4})-(\\d{1,2})-(\\d{1,2})$/.exec(String(iso||'').trim());
  if(!m) return null;
  const d=new Date(+m[1],+m[2]-1,+m[3]);
  // reject 2026-02-31 rolling over to March rather than being refused
  if(d.getFullYear()!==+m[1]||d.getMonth()!==+m[2]-1||d.getDate()!==+m[3]) return null;
  return d;
}""")

sub("    isPractice, brkOpen, brkElapsed,", "    isPractice, brkOpen, brkElapsed, localDate, examDaysLeft,")

PAGE.write_text(s, encoding="utf-8")
print("exam date read as a local calendar day")
