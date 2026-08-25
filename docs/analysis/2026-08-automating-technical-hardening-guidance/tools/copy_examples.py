#!/usr/bin/env python3
"""Copy the published OSCAL corpora into examples/ so the artifacts page links.

The inventory on oscal-artifacts.html names every document each approach ships
and counts what is in it. Until now a reader could see the counts and not the
files: the corpora sit beside this directory, outside anything the site
publishes, so a row named a document nobody visiting the site could open.

WHAT IS COPIED, AND WHAT IS NOT.

Two of the three are copied. The third, catalog-first, is published in a public
repository under a licence, so its rows link there instead: an online document
gets an online link, and 231 files and 4.8 MB of it do not need a second home.
That is a decision recorded in BUILD-LOG.md, not a rule of this tool, and
LINK_ONLY below is where it is expressed.

Copied, never moved. The corpora are the input this site reads and recomputes
its figures from, and a tool that moved them would break every count on the
worked scenario and the artifacts page at once.

ON REDISTRIBUTION. Two of the assessment files are CIS Benchmark content: the
Benchmark itself, and an assessment plan derived from it. This repository used
to exclude them, and that exclusion was lifted deliberately. If that decision is
ever revisited, the two paths are named in CIS_DERIVED so the argument does not
have to be reconstructed from filenames.

Usage:
    python tools/copy_examples.py
    python tools/copy_examples.py --check
"""

from __future__ import annotations

import filecmp
import hashlib
import json
import os
import shutil
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
CORPORA = os.path.normpath(os.path.join(TOOLS, "..", "..", "tfg-automated-assessments"))
DEST = os.path.join(ROOT, "examples")
OUT = os.path.join(ROOT, "data", "examples.json")

#  approach key -> the directory its corpus is read from.
SOURCES = {
    "component-first": "IBM",
    "assessment-first": "Easy Dynamics",
}

#  Published online, so linked rather than copied. The value is the base a file
#  path is appended to.
LINK_ONLY = {
    "catalog-first":
        "https://github.com/awslabs/oscal-content-for-aws-services/blob/main/",
}

#  Named so the licensing question stays legible. Both are CIS Benchmark
#  content and both are shipped here on the call recorded in BUILD-LOG.md.
CIS_DERIVED = [
    "assessment-first/Center for Internet Security/"
    "CIS_Ubuntu_Linux_24.04_LTS_Benchmark_v1.0.0.json",
    "assessment-first/Center for Internet Security/"
    "CIS_Ubuntu_Linux_24_04_LTS_Benchmark_v2_OSCAL_AP.json",
]


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wanted() -> list[tuple[str, str, str]]:
    """(approach, source path, destination path) for every file to copy."""
    out = []
    for key, rel in sorted(SOURCES.items()):
        base = os.path.join(CORPORA, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, names in os.walk(base):
            for name in sorted(names):
                if not name.lower().endswith(".json"):
                    continue
                src = os.path.join(dirpath, name)
                sub = os.path.relpath(src, base).replace(os.sep, "/")
                out.append((key, src, f"{key}/{sub}"))
    return sorted(out, key=lambda t: t[2])


def build() -> dict:
    files = []
    for key, src, rel in wanted():
        files.append({
            "approach": key,
            "path": rel,
            "bytes": os.path.getsize(src),
            "sha256": sha(src),
        })
    return {
        "note": ("The published OSCAL held in this repository, copied from the "
                 "corpora by tools/copy_examples.py so the inventory can link "
                 "to a document rather than only count it. Catalog-first is not "
                 "here: it is published in a public repository and is linked "
                 "there instead."),
        "link_only": LINK_ONLY,
        "cis_derived": CIS_DERIVED,
        "files": files,
    }


def main() -> int:
    check = "--check" in sys.argv
    todo = wanted()
    if not todo and not os.path.isdir(CORPORA):
        print(f"corpora not found at {CORPORA}; nothing to copy")
        return 0

    changed, missing = [], []
    for _key, src, rel in todo:
        dst = os.path.join(DEST, rel.replace("/", os.sep))
        if not os.path.isfile(dst):
            missing.append(rel)
            if not check:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        elif not filecmp.cmp(src, dst, shallow=False):
            changed.append(rel)
            if not check:
                shutil.copy2(src, dst)

    doc = build()
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if check:
        have = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        stale = missing or changed or have != text
        if stale:
            print(f"examples/ is stale: {len(missing)} missing, "
                  f"{len(changed)} differing; run python tools/copy_examples.py")
            return 1
        print(f"examples/ is current, {len(doc['files'])} files")
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    total = sum(f["bytes"] for f in doc["files"])
    print(f"examples/  {len(doc['files'])} files, {total / 1e6:.1f} MB "
          f"({len(missing)} copied, {len(changed)} updated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
