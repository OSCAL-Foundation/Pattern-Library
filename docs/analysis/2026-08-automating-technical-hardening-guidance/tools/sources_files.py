#!/usr/bin/env python3
"""
sources_files.py: build the per-file list behind the sources table.

The introduction lists one row per benchmark or guide. This walks sources/ and
records what is actually there, so a link on the page cannot point at a file that
is missing and a file cannot sit in the folder unlinked. Sizes and media types are
read from disk rather than typed, and each file names the row it belongs to.

Only the documents that were read as INPUT are listed. The OSCAL representations
derived from them are published separately, so sources/oscal/ is excluded here by
EXCLUDE rather than merely unlisted: an excluded path is stated and checked, while
an unlisted one would look like an oversight.

Material that is NOT copied is recorded too, with the reason and where to get it,
so a publisher with no files does not read as an oversight.

Terms differ by publisher and each file carries its own. The DISA material is a
work of the United States Government. The CIS Benchmarks are reproduced with the
publisher's participation in this review, and CIS's own Agreed Terms of Use
otherwise restrict redistribution, so the terms line points a reader back to the
publisher rather than implying a general grant.

Usage:
    python tools/sources_files.py
    python tools/sources_files.py --check     exit non-zero if data/ is stale
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(TOOLS_DIR)
DATA = os.path.join(SITE_ROOT, "data")
SOURCES = os.path.join(SITE_ROOT, "sources")

#  Media types the site links. The icon key drives which glyph site.js draws, and
#  the label is what a screen reader hears in place of the icon.
MEDIA = {
    ".xml":  {"key": "xml",  "label": "XML document",  "mime": "application/xml"},
    ".pdf":  {"key": "pdf",  "label": "PDF document",  "mime": "application/pdf"},
    ".json": {"key": "json", "label": "JSON document", "mime": "application/json"},
}

#  Where each folder's contents came from, and under what terms. A folder with no
#  entry here is a build error rather than an unlabelled link.
#  Paths under sources/ that are deliberately not listed, and why. Kept as data
#  so tools/verify.py can assert the same set rather than guessing.
#  Recorded but not shipped. CIS licenses its Benchmarks under Agreed Terms of
#  Use that do not grant redistribution, and a public repository is
#  redistribution, so the files are gitignored. The record still has to be
#  complete, and it has to be identical whether or not a given clone happens to
#  have the files on disk, or the generated data would differ between a
#  maintainer's machine and CI. So entries for these folders are carried forward
#  from the committed data rather than recomputed from the filesystem.
UNSHIPPED = {
    "cis": ("Held locally, not redistributed. Download the Benchmarks from "
            "cisecurity.org into sources/cis/ under the filenames recorded here "
            "to rebuild anything that reads them."),
}

EXCLUDE = {
    "oscal": ("The OSCAL representations of this guidance are published separately. "
              "This table lists the documents read as input, not what was written "
              "from them."),
}

#  Excluded by file rather than by folder, and for a different reason: the table
#  is one row per benchmark or guide, and this document is about the STIG and SRG
#  packages as a set. It had a row of its own for a while, which made the readme
#  look like a fifteenth piece of guidance. Filed into one of the nine STIG rows
#  it would be worse: it belongs to all of them or to none. So it stays on disk,
#  read as input, and unlisted with the reason stated here rather than silently
#  dropped.
EXCLUDE_FILES = {
    "disa/U_Readme_SRG_and_STIG.pdf": (
        "About the STIG and SRG packages as a set rather than about any one "
        "guide, so it has no row in a table of one row per guide."),
}

FOLDERS = {
    "cis": {
        "publisher": "cis",
        "kind": "source",
        "terms": ("Reproduced here with the publisher's participation in this "
                  "review. The Benchmarks carry CIS's own Agreed Terms of Use; "
                  "consult the publisher before reusing them elsewhere."),
    },
    "disa": {
        "publisher": "disa",
        "kind": "source",
        "terms": "Public domain. A work of the United States Government.",
    },
}

#  Which benchmark or guide each file belongs to. The table has one row per
#  benchmark, not one per publisher, so a file has to name its row rather than
#  only its publisher: a reader downloading the RHEL 9 STIG should not have to
#  pick it out of nine XML files sitting under DISA.
#
#  Matched on the filename, longest pattern first, and every file must match
#  exactly one. A new file that matches none is a build error, because the
#  alternative is a document that quietly lands in whichever row sorts first.
#
#  The keys are the row keys in data/sources.json, and verify.py checks the two
#  sets against each other, so a row cannot lose its files by being renamed.
GUIDANCE = [
    ("CIS_Ubuntu_Linux_24.04_LTS_Benchmark", "cis-ubuntu-24-04"),
    ("CIS_PostgreSQL_18_Benchmark",          "cis-postgresql-18"),
    ("U_CAN_Ubuntu_22-04",                   "disa-ubuntu-22-04"),
    ("U_CAN_Ubuntu_24-04",                   "disa-ubuntu-24-04"),
    ("U_RHEL_8_STIG",                        "disa-rhel-8"),
    ("U_RHEL_9_STIG",                        "disa-rhel-9"),
    ("U_MS_Windows_Server_2019_STIG",        "disa-windows-2019"),
    ("U_MS_Windows_Server_2022_STIG",        "disa-windows-2022"),
    ("U_MS_Windows_Server_2025_STIG",        "disa-windows-2025"),
    ("U_CD_Postgres_16_STIG",                "disa-postgres-16"),
    ("U_EPAS_STIG",                          "disa-epas"),
]

#  Named, not omitted. Each entry says what is missing, why, and where to get it.
NOT_COPIED = [
    {
        "publisher": "cisa",
        "what": "The SCuBA secure configuration baselines themselves",
        "why": ("The baselines are published by CISA and no copy of them is held "
                "here. What was read for this analysis was the baseline content as "
                "converted, and those conversions are published separately."),
        "where": None,
        "where_label": None,
    },
    {
        "publisher": "aws",
        "what": "The Security Hub controls, as published",
        "why": ("This publisher ships its guidance as OSCAL already, so there is no "
                "separate source document to hold. The published content is linked "
                "rather than copied, so there is one copy to keep current."),
        "where": "https://github.com/awslabs/oscal-content-for-aws-services",
        "where_label": "oscal-content-for-aws-services",
    },
]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def human(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.0f} kB"
    return f"{n} bytes"


def guidance_of(name: str) -> str | None:
    """Which row a file belongs to, by filename.

    Exactly one pattern must match. Zero means a new file nothing accounts for;
    two means the patterns overlap and the file would land in whichever row was
    written first. Both are ambiguities the caller turns into a build error
    rather than a silent choice.
    """
    hits = [key for pat, key in GUIDANCE if pat in name]
    return hits[0] if len(hits) == 1 else None


def _recorded() -> dict:
    """What the committed data already says, keyed by path.

    Read rather than recomputed for UNSHIPPED folders, so that a clone without
    those files produces byte-identical output to one that has them.
    """
    try:
        with open(os.path.join(DATA, "source-files.json"), encoding="utf-8") as fh:
            return {f["href"]: f for f in json.load(fh)["files"]}
    except (OSError, KeyError, ValueError):
        return {}


def build() -> dict:
    files: list[dict] = []
    carried = _recorded()
    unlabelled: list[str] = []
    unmatched: list[str] = []

    for path in sorted(glob.glob(os.path.join(SOURCES, "**", "*"), recursive=True)):
        if not os.path.isfile(path):
            continue
        rel = os.path.relpath(path, SOURCES).replace(os.sep, "/")
        if rel.split("/", 1)[0] in EXCLUDE:
            continue
        if rel in EXCLUDE_FILES:
            continue
        folder = os.path.dirname(rel)
        if folder in UNSHIPPED:
            continue          # taken from the record below, not from disk
        meta = FOLDERS.get(folder)
        if meta is None:
            unlabelled.append(rel)
            continue
        ext = os.path.splitext(path)[1].lower()
        media = MEDIA.get(ext)
        if media is None:
            unlabelled.append(rel)
            continue
        guidance = guidance_of(os.path.basename(rel))
        if guidance is None:
            unmatched.append(rel)
            continue
        size = os.path.getsize(path)
        files.append({
            "publisher": meta["publisher"],
            "guidance": guidance,
            "kind": meta["kind"],
            "terms": meta["terms"],
            "href": "sources/" + rel,
            "name": os.path.basename(rel),
            "media": media["key"],
            "media_label": media["label"],
            "mime": media["mime"],
            "bytes": size,
            "size": human(size),
            "sha256": sha256(path),
        })

    if unlabelled:
        raise SystemExit(
            "sources/ holds files this script cannot label, so they would appear "
            "on the page with no media type or terms:\n  "
            + "\n  ".join(unlabelled)
            + "\nAdd the folder to FOLDERS or the extension to MEDIA.")

    if unmatched:
        raise SystemExit(
            "sources/ holds files no row in data/sources.json accounts for, or "
            "that two rows would both claim:\n  "
            + "\n  ".join(unmatched)
            + "\nAdd a pattern to GUIDANCE, and a row to data/sources.json.")

    #  Merge the recorded entries for folders we do not ship, then sort so the
    #  output does not depend on which of the two sources an entry came from.
    for href, entry in carried.items():
        folder = href.split("sources/", 1)[-1].split("/", 1)[0]
        if folder in UNSHIPPED:
            files.append(entry)
    files.sort(key=lambda f: f["href"])

    return {
        "note": ("Every file under sources/, with its media type and size read from "
                 "disk, and the benchmark row it belongs to. Built by "
                 "tools/sources_files.py; verified by tools/verify.py --sources, "
                 "which fails if a link points at a missing file, a file sits in "
                 "the folder unlinked, or a file names a row that does not exist."),
        "media_types": {k: v for k, v in
                        ((m["key"], {"label": m["label"], "mime": m["mime"]})
                         for m in MEDIA.values())},
        "files": files,
        "excluded": [{"path": k, "why": v}
                     for k, v in sorted({**EXCLUDE, **EXCLUDE_FILES}.items())],
        "not_shipped": [{"path": k, "why": v} for k, v in sorted(UNSHIPPED.items())],
        "not_copied": NOT_COPIED,
        "totals": {
            "files": len(files),
            "bytes": sum(f["bytes"] for f in files),
            "size": human(sum(f["bytes"] for f in files)),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    fresh = build()
    out = os.path.join(DATA, "source-files.json")

    if a.check:
        if not os.path.exists(out):
            sys.exit("data/source-files.json is missing. Run tools/sources_files.py")
        have = json.load(open(out, encoding="utf-8"))
        if have.get("files") != fresh["files"]:
            sys.exit("data/source-files.json is stale. Run tools/sources_files.py")
        print("data/source-files.json is current")
        return

    with open(out, "w", encoding="utf-8") as fh:
        json.dump(fresh, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    if not a.quiet:
        by: dict[str, list] = {}
        for f in fresh["files"]:
            by.setdefault(f["publisher"], []).append(f)
        for pub in sorted(by):
            n = len(by[pub])
            tot = human(sum(x["bytes"] for x in by[pub]))
            kinds = ", ".join(sorted({x["media"] for x in by[pub]}))
            print(f"  {pub:6} {n:2} files  {tot:>9}  ({kinds})")
        print(f"  {'total':6} {fresh['totals']['files']:2} files  "
              f"{fresh['totals']['size']:>9}")
        rows = sorted({f["guidance"] for f in fresh["files"]})
        print(f"  across {len(rows)} rows: {', '.join(rows)}")
        print(f"  {len(fresh['not_copied'])} entries recorded as not copied, with reasons")


if __name__ == "__main__":
    main()
