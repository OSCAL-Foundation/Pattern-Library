#!/usr/bin/env python3
"""Validate and index the committed OSCAL examples without copying them.

The filename is retained for compatibility. IBM and Easy Dynamics resolve to
the curated example sets already in examples/; source and destination are the
same files. Nothing is fetched or copied.

data/examples.json is the trust baseline. A standard run and --check verify
every path, byte count and SHA-256 against it and refuse to record new
fingerprints, so an unnoticed edit to an example fails the build. The examples
are curated, not verbatim third-party originals: when one is deliberately
repaired, replaced or added, run --rebaseline to record the new fingerprints,
then update expected_files in tools/source-lock.json if the count changed, and
say what changed and why in BUILD-LOG.md.

Catalog-first remains link-only, at the revision pinned in the source lock.
A standard run refreshes the index note, pinned links and record ordering;
--check verifies the local inventory and pinned link_only without writing.

ON REDISTRIBUTION. Two of the assessment files are CIS Benchmark content: the
Benchmark itself, and an assessment plan derived from it. This repository used
to exclude them, and that exclusion was lifted deliberately. If that decision is
ever revisited, the two paths are named in CIS_DERIVED so the argument does not
have to be reconstructed from filenames.

Usage:
    python tools/copy_examples.py
    python tools/copy_examples.py --check
    python tools/copy_examples.py --rebaseline
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

import source_inputs        # same directory

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DEST = os.path.join(ROOT, "examples")
OUT = os.path.join(ROOT, "data", "examples.json")

#  Approach key -> resolver prefix for the committed examples directory.
SOURCES = {
    "component-first": "IBM",
    "assessment-first": "Easy Dynamics",
}

#  Published online, so linked rather than copied. The value is the base a file
#  path is appended to.
LINK_ONLY = {
    "catalog-first": source_inputs.public_file_base("catalog-first"),
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


def wanted(verify: bool = True) -> list[tuple[str, str, str]]:
    """(approach, local path, examples-relative path) for each example file."""
    out = []
    for key, rel in sorted(SOURCES.items()):
        if verify:
            base = source_inputs.source_path(rel)
            if base != os.path.join(DEST, key):
                raise source_inputs.SourceInputError(
                    f"{rel} must resolve to committed examples/{key}, not {base}")
        else:
            base = os.path.join(DEST, key)
        for dirpath, _dirs, names in os.walk(base):
            for name in sorted(names):
                if not name.lower().endswith(".json"):
                    continue
                src = os.path.join(dirpath, name)
                sub = os.path.relpath(src, base).replace(os.sep, "/")
                out.append((key, src, f"{key}/{sub}"))
    return sorted(out, key=lambda t: t[2])


NOTE = ("The curated OSCAL examples committed in this repository, indexed by "
        "tools/copy_examples.py with the path, byte count and SHA-256 of each. "
        "Every build re-verifies the files against this index, so an edit is "
        "only accepted through an explicit --rebaseline run recorded in "
        "BUILD-LOG.md. Catalog-first is not here: it is published in a public "
        "repository and linked at the locked revision instead.")


def fingerprints(verify: bool) -> list[dict]:
    return [{"approach": key, "path": rel, "bytes": os.path.getsize(src),
             "sha256": sha(src)} for key, src, rel in wanted(verify)]


def shared() -> list[dict]:
    """Reference documents at the examples root, resolved by more than one set."""
    out = []
    for name in sorted(os.listdir(DEST)):
        path = os.path.join(DEST, name)
        if name.lower().endswith(".json") and os.path.isfile(path):
            out.append({"path": name, "bytes": os.path.getsize(path), "sha256": sha(path)})
    return out


def rebaseline() -> dict:
    """Record the current files as the new baseline; the lock count must agree."""
    files = fingerprints(verify=False)
    counts = {}
    for row in files:
        counts[row["approach"]] = counts.get(row["approach"], 0) + 1
    for source in source_inputs.source_metadata()["sources"]:
        if "expected_files" in source and counts.get(source["approach"], 0) != source["expected_files"]:
            raise source_inputs.SourceInputError(
                f"examples/{source['approach']} holds {counts.get(source['approach'], 0)} JSON files "
                f"but tools/source-lock.json expects {source['expected_files']}; "
                "update expected_files deliberately before rebaselining.")
    return {"note": NOTE, "link_only": LINK_ONLY, "cis_derived": CIS_DERIVED,
            "shared": shared(), "files": files}


def build() -> dict:
    """Validate originals against the existing index before refreshing metadata."""
    try:
        with open(OUT, encoding="utf-8") as fh:
            baseline = json.load(fh)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise source_inputs.SourceInputError(
            f"Cannot read committed example index {OUT}: {error}. "
            "Restore the committed index; it must not be recreated from originals.") from error
    if (not isinstance(baseline, dict)
            or not isinstance(baseline.get("files"), list)
            or any(not isinstance(row, dict) or not isinstance(row.get("path"), str)
                   for row in baseline["files"])):
        raise source_inputs.SourceInputError(
            "Invalid data/examples.json inventory; restore the committed index.")
    if baseline.get("cis_derived") != CIS_DERIVED:
        raise source_inputs.SourceInputError(
            "data/examples.json cis_derived differs; restore the committed licensing metadata.")
    files = fingerprints(verify=True)
    if files != sorted(baseline["files"], key=lambda row: row["path"]):
        raise source_inputs.SourceInputError(
            "Committed example inventory differs from data/examples.json "
            "(paths, sizes or SHA-256). Restore the committed examples/index, "
            "or run --rebaseline for a deliberate change; refusing to record "
            "new fingerprints implicitly.")
    reference = shared()
    if reference != baseline.get("shared", []):
        raise source_inputs.SourceInputError(
            "Shared reference documents at examples/ differ from data/examples.json; "
            "restore them or run --rebaseline for a deliberate change.")
    return {
        "note": NOTE,
        "link_only": LINK_ONLY,
        "cis_derived": CIS_DERIVED,
        "shared": reference,
        "files": files,
    }


def main() -> int:
    check = "--check" in sys.argv
    try:
        doc = rebaseline() if "--rebaseline" in sys.argv else build()
        if check:
            with open(OUT, encoding="utf-8") as fh:
                have = json.load(fh)
            if have.get("link_only") != LINK_ONLY:
                raise source_inputs.SourceInputError(
                    "data/examples.json link_only is stale; run tools/copy_examples.py "
                    "to refresh pinned link metadata without changing originals.")
            print(f"examples/ verified, {len(doc['files'])} files; pinned links current")
            return 0
        text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(text)
    except (source_inputs.SourceInputError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Example validation/indexing failed: {error}", file=sys.stderr)
        return 1
    total = sum(f["bytes"] for f in doc["files"])
    verb = "rebaselined" if "--rebaseline" in sys.argv else "refreshed"
    print(f"data/examples.json {verb}: {len(doc['files'])} files, "
          f"{total / 1e6:.1f} MB; examples/ not written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
