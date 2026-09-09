#!/usr/bin/env python3
"""Cut the deployable copy of the site: what a browser reads, and nothing else.

The rule is one sentence. A file ships if the browser asks for it. Everything
else in this repository is input to the build or evidence for the harness, and
neither of those is part of a static site.

assets/bundle.js mirrors all of data/, so it is rebuilt here over the shipped
subset rather than copied. This keeps the folder-based fallback aligned with
the files included in the package.
"""
import json, os, re, shutil, subprocess, sys

SRC = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.abspath(sys.argv[2])
if os.path.isdir(DST):
    shutil.rmtree(DST)
os.makedirs(DST)

pages = sorted(f for f in os.listdir(SRC) if f.endswith(".html"))
html = "".join(open(os.path.join(SRC, p), encoding="utf-8").read() for p in pages)
js = open(os.path.join(SRC, "assets", "site.js"), encoding="utf-8").read()

want = set()
for m in re.findall(r'load\("([^"+]+\.json)"\)', js):
    want.add("data/" + m)
sq = json.load(open(os.path.join(SRC, "data", "six-questions.json"), encoding="utf-8"))
for s in {s for c in sq["matrix"] for s in c.get("snippet_ids", [])}:
    want.add(f"data/snippets/{s}.json")
for d in set(re.findall(r'data-diagram="([^"]+)"', html)):
    want.add(f"assets/diagrams/{d}.svg")
for r in re.findall(r'(?:href|src)="\./([^"#]+)"', html):
    if not r.endswith(".html"):
        want.add(r)

#  The documents the artifacts page links to, and the licence.
for d, _, fs in os.walk(os.path.join(SRC, "examples")):
    for f in fs:
        want.add(os.path.relpath(os.path.join(d, f), SRC).replace(os.sep, "/"))
want |= {"LICENSE", ".nojekyll"}
want |= set(pages)

for rel in sorted(want):
    s = os.path.join(SRC, rel.replace("/", os.sep))
    if not os.path.isfile(s):
        raise SystemExit(f"the site asks for {rel} and it is not there")
    t = os.path.join(DST, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(t) or DST, exist_ok=True)
    shutil.copy2(s, t)

#  Rebuild the file:// mirror over the shipped subset only.
sys.path.insert(0, os.path.join(SRC, "tools"))
import bundle as B
B.SITE_ROOT, B.DATA = DST, os.path.join(DST, "data")
B.DIAGRAMS = os.path.join(DST, "assets", "diagrams")
B.OUT = os.path.join(DST, "assets", "bundle.js")
try:
    B.main([])
except TypeError:
    _argv = sys.argv[:]
    sys.argv = [sys.argv[0]]
    try:
        B.main()
    finally:
        sys.argv = _argv

n = sum(len(f) for _, _, f in os.walk(DST))
mb = sum(os.path.getsize(os.path.join(d, f))
         for d, _, fs in os.walk(DST) for f in fs) / 1e6
print(f"\n{n} files, {mb:.1f} MB")
