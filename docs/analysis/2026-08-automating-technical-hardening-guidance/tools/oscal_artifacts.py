#!/usr/bin/env python3
"""
tools/oscal_artifacts.py: author data/oscal-artifacts.json.

WHY THIS EXISTS. The walkthrough encodes two rules ourselves, so the pages argue
from content nobody published. That is the right trade for comparing modelling,
but it leaves a reader with no way to see what the three groups have actually
shipped. This inventory is that: every OSCAL document in the three corpora, what
model it is, and what is in it, counted from the file rather than described.

Nothing here is authored. Every number is read off disk.
"""

import json, os, sys, glob, collections, urllib.parse

import source_inputs        # same directory

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
OUT = os.path.join(ROOT, "data", "oscal-artifacts.json")

#  Labelled by approach, not by publisher.
#
#  This page named the three groups, and was the one page on the site exempt
#  from the rule that no proponent organization appears in any prose, on the
#  argument that an inventory redacting the publisher would be useless. The
#  exemption is gone: an inventory of what each approach ships is just as
#  useful, and every other page has been talking about approaches for weeks
#  while this one talked about companies.
#
#  The repository link stays. It is a reference to a public location rather than
#  an attribution in prose, and without it a reader cannot go and check the
#  counts on this page against the files.
#
#  The directory each corpus is read from keeps its real name, because it is a
#  path on disk. It is not rendered.
PUBLISHERS = [
    ("catalog-first", "Catalog-first", "Option A",
     "AWS/oscal-content-for-aws-services-main",
     "https://github.com/awslabs/oscal-content-for-aws-services",
     "Option A"),
    ("component-first", "Component-first", "Option B", "IBM", None, "Option B"),
    ("assessment-first", "Assessment-first", "Option C", "Easy Dynamics", None,
     "Option C"),
]

MODEL_LABEL = {
    "catalog": "Catalog",
    "profile": "Profile",
    "component-definition": "Component definition",
    "system-security-plan": "System security plan",
    "assessment-plan": "Assessment plan",
    "assessment-results": "Assessment results",
    "plan-of-action-and-milestones": "POA&M",
    "mapping-collection": "Mapping collection",
}


def summarise(model, body):
    """What is in the document, counted. One short phrase, never a judgement."""
    n = collections.OrderedDict()
    if model == "catalog":
        groups = body.get("groups", [])
        n["groups"] = len(groups)
        n["controls"] = sum(len(g.get("controls", [])) for g in groups)
    elif model == "component-definition":
        comps = body.get("components", [])
        n["components"] = len(comps)
        by = collections.Counter(c.get("type", "?") for c in comps)
        for k in sorted(by):
            n[k] = by[k]
        rules = sum(len(c.get("rules", [])) for c in comps)
        if rules:
            n["rules"] = rules
        irs = sum(len(ci.get("implemented-requirements", []))
                  for c in comps for ci in c.get("control-implementations", []))
        if irs:
            n["implemented requirements"] = irs
    elif model == "assessment-plan":
        ld = body.get("local-definitions", {}) or {}
        n["activities"] = len(ld.get("activities", []))
        n["tasks"] = len(body.get("tasks", []))
        steps = sum(len(a.get("steps", [])) for a in ld.get("activities", []))
        if steps:
            n["steps"] = steps
    elif model == "assessment-results":
        res = body.get("results", [])
        n["results"] = len(res)
        n["observations"] = sum(len(r.get("observations", [])) for r in res)
        n["findings"] = sum(len(r.get("findings", [])) for r in res)
    return n


def title_of(body):
    return ((body.get("metadata") or {}).get("title") or "").strip()


#  Where a reader can open the document a row names. Two source sets are already
#  committed in examples/ and validated by tools/copy_examples.py; the third is
#  published in a public repository and links to its locked revision, which is
#  the rule that an online document gets an online link.
#
#  Built here rather than in the renderer so the inventory carries the address
#  of every file it counts, and so a link that stops resolving is a data
#  difference the build can see rather than a click a reader has to try.
LINK_BASE = {
    "catalog-first": source_inputs.public_file_base("catalog-first"),
    "component-first": "examples/component-first/",
    "assessment-first": "examples/assessment-first/",
}


def scan(rel_root):
    base = source_inputs.source_path(rel_root)
    paths = sorted(glob.glob(os.path.join(base, "**", "*.json"), recursive=True))
    if not paths:
        raise source_inputs.SourceInputError(f"No JSON source files found for {rel_root}: {base}")
    out = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise source_inputs.SourceInputError(f"Cannot read JSON source {path}: {error}") from error
        if not isinstance(doc, dict) or not doc:
            continue
        model = next(iter(doc))
        if model not in MODEL_LABEL:
            continue          # not an OSCAL document; the XCCDF-derived JSON
        body = doc[model]
        out.append({
            "file": os.path.relpath(path, base).replace(os.sep, "/"),
            "model": model,
            "model_label": MODEL_LABEL[model],
            "title": title_of(body),
            "counts": summarise(model, body),
            "bytes": os.path.getsize(path),
            "href": None,          # filled in by build(), which knows the key
        })
    return out


def build():
    pubs = []
    for key, name, full, rel, repo, option in PUBLISHERS:
        files = scan(rel)
        base = LINK_BASE[key]
        for f in files:
            #  A path in this repository, or a URL. quote() leaves the slashes
            #  alone and escapes the rest, which matters because two of these
            #  directories have spaces in their names.
            f["href"] = base + urllib.parse.quote(f["file"])
            f["href_external"] = base.startswith("http")
        by_model = collections.Counter(f["model"] for f in files)
        #  This corpus ships 230 component definitions, one per service.
        #  Listing every
        #  one would bury the catalog, which is the document the approach turns
        #  on, so the long tail is counted and a few are named.
        roll = None
        if key == "catalog-first":
            cdefs = [f for f in files if f["model"] == "component-definition"]
            keep = {"component-definitions/acm.oscal.json",
                    "component-definitions/cloudtrail.oscal.json",
                    "component-definitions/config.oscal.json",
                    "component-definitions/iam.oscal.json"}
            shown = [f for f in files if f["model"] != "component-definition"
                     or f["file"] in keep]
            roll = {
                "model_label": "Component definition",
                "count": len(cdefs),
                "components": sum(f["counts"].get("components", 0) for f in cdefs),
                "software": sum(f["counts"].get("software", 0) for f in cdefs),
                "note": ("One per service. Four are listed above as examples; "
                         "the rest follow the same shape."),
            }
            files = shown
        pubs.append({
            "key": key, "name": name, "full_name": full, "option": option,
            "repo": repo, "root": rel,
            "totals": {MODEL_LABEL[m]: c for m, c in sorted(by_model.items())},
            "files": files,
            "rollup": roll,
        })
    return {
        "note": (__doc__ or "").strip().splitlines()[0],
        "publishers": pubs,
    }


def main():
    try:
        doc = build()
    except source_inputs.SourceInputError as error:
        sys.exit(f"OSCAL inventory: {error}")
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv:
        if not os.path.exists(OUT):
            sys.exit("data/oscal-artifacts.json is missing. Run tools/oscal_artifacts.py")
        if open(OUT, encoding="utf-8").read() != text:
            sys.exit("data/oscal-artifacts.json is stale. Run tools/oscal_artifacts.py")
        print("data/oscal-artifacts.json is current")
        return
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    for p in doc["publishers"]:
        print(f"  {p['name']:<16} {dict(p['totals'])}")


if __name__ == "__main__":
    main()
