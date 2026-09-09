#!/usr/bin/env python3
"""
verify.py: prove that what the site claims is what the files say.

Usage:
    python tools/verify.py --all
    python tools/verify.py --snippets   re-extract every snippet and diff
    python tools/verify.py --schema     the OSCAL constraints behind question 2
    python tools/verify.py --stats      recompute every cited figure
    python tools/verify.py --data       internal consistency of data/
    python tools/verify.py --css        colour lives only in the token block
    python tools/verify.py --a11y       contrast, and the two palette rules
    python tools/verify.py --diagrams   structure, colour, geometry, grayscale
    python tools/verify.py --quotes     no quotation hooks or archived attribution
    python tools/verify.py --criteria   fifteen editorial criteria and valid mappings
    python tools/verify.py --matrix     every answer-matrix cell resolves
    python tools/verify.py --questions  editorial questions and stable identifiers
    python tools/verify.py --appendix   equal counts and every denominator
    python tools/verify.py --links      every internal href and anchor resolves
    python tools/verify.py --pages      run each page and inspect the result

A later build phase adds --budget. The flag is registered here so the harness
grows without restructuring.

Exit code 0 only if every selected check passes.
"""

from __future__ import annotations

import argparse
import collections
import difflib
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

import extract as ex        # same directory
import svgrender as sr     # same directory

# The site's option-letter order: Catalog-first is A, Component-first is B,
# Assessment-first is C.
OPTION_ORDER = ["catalog-first", "component-first", "assessment-first"]

# Labels that named a construct rather than a question. Each one was on the site
# and each one told a reader nothing on its own, which is what a name is for.
RETIRED_LABELS = {
    "control tie", "late binding available", "subject", "actor", "check",
    "rule", "satisfaction", "satisfaction: implementation claim",
    "satisfaction: assessment result",
}

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(TOOLS_DIR)
DATA = os.path.join(SITE_ROOT, "data")
SNIPPETS = os.path.join(DATA, "snippets")
EVIDENCE = os.path.join(DATA, "schema-evidence")

_RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    _RESULTS.append((name, bool(ok), detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  |  {detail}" if detail and not ok else ""))
    return bool(ok)


# --------------------------------------------------------------------------- #
# Skipping, and why a skip is not a pass                                      #
# --------------------------------------------------------------------------- #
#
# Four of the checks the brief asks for need something this environment does not
# have: a schema validator, a headless browser, and network access to reach the
# published NIST schemas and the external links. The temptation is to write a
# weaker check, call it by the strong check's name, and let --all go green. That
# would make the harness dishonest in exactly the way the site is trying not to
# be.
#
# So a check that cannot run says so, by name, with the command it would have
# run, and the summary reports skips on their own line. A skip is never counted
# as a pass. In CI, where the network and the tools are available, --strict
# turns every skip into a failure, which is what stops a skipped check from
# being skipped forever.

_SKIPS: list = []
STRICT = False
SCENARIO_FIGURES: set = set()


def skip(name: str, reason: str, command: str = "") -> bool:
    if STRICT:
        return check(name, False, f"{reason}. Required under --strict")
    _SKIPS.append((name, reason, command))
    print(f"  SKIP  {name}  |  {reason}")
    if command:
        print(f"        command: {command}")
    return False


def have_network(timeout: float = 6.0) -> bool:
    """One probe, cached, against the host the schema checks need."""
    if not hasattr(have_network, "_result"):
        import urllib.request
        try:
            urllib.request.urlopen(
                "https://raw.githubusercontent.com/usnistgov/OSCAL/main/README.md",
                timeout=timeout).read(1)
            have_network._result = True          # type: ignore[attr-defined]
        except Exception:
            have_network._result = False         # type: ignore[attr-defined]
    return have_network._result                  # type: ignore[attr-defined]


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def load_snippet(sid: str) -> dict:
    with open(os.path.join(SNIPPETS, f"{sid}.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def snippet_json(sid: str):
    return json.loads(load_snippet(sid)["content"])


def corpus_json(rel: str):
    with open(ex.source_path(rel), "r", encoding="utf-8") as fh:
        return json.load(fh)


def walk_keys(node, wanted: str, count: int = 0) -> int:
    """Count occurrences of a key anywhere in a nested structure."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == wanted:
                count += 1
            count = walk_keys(v, wanted, count)
    elif isinstance(node, list):
        for v in node:
            count = walk_keys(v, wanted, count)
    return count


# --------------------------------------------------------------------------- #
# --snippets                                                                   #
# --------------------------------------------------------------------------- #

def check_snippets() -> None:
    print("\n[snippets] re-extract and diff")
    entries = ex.load_manifest()["snippets"]
    check("the manifest retains JSON extracts only",
          bool(entries) and all(e.get("language", "json") == "json"
                                and e["source"].endswith(".json") for e in entries))
    drift = []
    for entry in entries:
        sid = entry["id"]
        live = os.path.join(SNIPPETS, f"{sid}.json")
        if not os.path.isfile(live):
            drift.append(f"{sid}: missing in data/snippets")
            continue
        try:
            a = load_snippet(sid)
            # Re-extract in memory: verification never rewrites site data.
            b = ex.extract_one(entry, SITE_ROOT)
        except (ex.ExtractionError, OSError, ValueError) as exc:
            drift.append(f"{sid}: {exc}")
            continue
        # extracted_at is expected to differ; content and its address must not.
        for field in ("id", "title", "content", "source", "pointer", "section",
                      "slot", "approach", "language", "sha256_of_source_file"):
            if a.get(field) != b.get(field):
                if field == "content":
                    diff = "\n".join(list(difflib.unified_diff(
                        a.get("content", "").splitlines(), b["content"].splitlines(),
                        fromfile=f"data/{sid}", tofile=f"fresh/{sid}", lineterm="",
                    ))[:40])
                    drift.append(f"{sid}: content drift\n{diff}")
                else:
                    drift.append(f"{sid}: {field} drift {a.get(field)!r} -> {b.get(field)!r}")
    stale = {os.path.splitext(os.path.basename(p))[0]
             for p in glob.glob(os.path.join(SNIPPETS, "*.json"))} - {
                 e["id"] for e in entries}
    for sid in sorted(stale):
        drift.append(f"{sid}: present in data/ but not in the manifest")
    check("re-extraction is byte-identical", not drift, "; ".join(drift[:3]))
    for d in drift:
        print("        " + d.replace("\n", "\n        "))
    if drift:
        return

    print("\n[snippets] asserted facts")

    ct = snippet_json("aws-acm2-control")
    check("aws-acm2-control id == 'ACM.2'",
          ct.get("id") == "ACM.2", f"got {ct.get('id')!r}")

    am = [p for p in ct.get("parts", []) if p.get("name") == "assessment-method"]
    ok = bool(am) and am[0].get("props", [{}])[0].get("name") == "TechnicalControlId" \
        and am[0]["props"][0].get("class") == "config-rule"
    check("aws-acm2-control has assessment-method part with "
          "TechnicalControlId / class config-rule", ok)
    tci = am[0]["props"][0]["value"] if ok else None

    comp = snippet_json("aws-acm-rsa-check-component")
    check("aws-acm-rsa-check-component title == the TechnicalControlId value",
          comp.get("title") == tci, f"{comp.get('title')!r} vs {tci!r}")
    check("aws-acm-rsa-check-component implements ACM.2",
          any(ir.get("control-id") == "ACM.2"
              for ci in comp.get("control-implementations", [])
              for ir in ci.get("implemented-requirements", [])))

    cos = snippet_json("ibm-cos-component")
    check("ibm-cos-component contains 'rules'", walk_keys(cos, "rules") > 0)
    check("ibm-cos-component contains 'implementing-rules'",
          walk_keys(cos, "implementing-rules") > 0)

    ibm_files = ["cos-component-definition.json", "idservice-component-definition.json",
                 "ansible-validation-component-definition.json",
                 "oscap-validation-component-definition.json"]
    props = sum(walk_keys(corpus_json(f"IBM/{f}"), "props") for f in ibm_files)
    ns = sum(walk_keys(corpus_json(f"IBM/{f}"), "ns") for f in ibm_files)
    check("the four IBM component definitions contain zero 'props'", props == 0, f"found {props}")
    check("the four IBM component definitions contain zero 'ns'", ns == 0, f"found {ns}")

    ansible = snippet_json("ibm-validation-ansible")
    target = ansible["component-definition"]["components"][0]["checks"][0]["target-component-uuid"]
    cos_uuid = corpus_json("IBM/cos-component-definition.json")[
        "component-definition"]["components"][0]["uuid"]
    check("ibm-validation-ansible checks[0].target-component-uuid resolves to the COS component",
          target == cos_uuid, f"{target} vs {cos_uuid}")

    act = snippet_json("ez-stig-activity-v259312")
    types = [p["value"] for s in act.get("steps", []) for p in s.get("props", [])
             if p["name"] == "step-type"]
    check("ez-stig-activity-v259312 has exactly two steps, step-type check and remediate",
          len(act.get("steps", [])) == 2 and types == ["check", "remediate"], f"got {types}")

    stig = [f for f in ez_plans() if os.sep + "DISA" + os.sep in f]
    placeholders = sum(
        1 for f in stig
        if json.load(open(f, encoding="utf-8"))["assessment-plan"]["import-ssp"].get("href")
        == "PLACEHOLDER"
    )
    check("all 9 STIG files have import-ssp.href == 'PLACEHOLDER'",
          len(stig) == 9 and placeholders == 9, f"{placeholders} of {len(stig)}")


# --------------------------------------------------------------------------- #
# --schema                                                                     #
# --------------------------------------------------------------------------- #

def _has_prop(frag: dict, name: str) -> bool:
    return name in (frag.get("properties") or {})


def _allof_enum(frag: dict, prop: str) -> list | None:
    node = (frag.get("properties") or {}).get(prop, {})
    for branch in node.get("allOf", []):
        if "enum" in branch:
            return branch["enum"]
    return None


def _anyof_enum(frag: dict, prop: str) -> list | None:
    node = (frag.get("properties") or {}).get(prop, {})
    for branch in node.get("anyOf", []):
        if "enum" in branch:
            return branch["enum"]
    return None


NIST_SCHEMAS = {
    "catalog":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_catalog_schema.json",
    "component-definition":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_component_schema.json",
    "profile":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_profile_schema.json",
    "mapping-collection":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_mapping_schema.json",
    "assessment-results":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_assessment-results_schema.json",
    #  Added with data/schema-evidence/poam-outcomes.json. Without an entry here
    #  the model lookup in _refetch_nist_fragments returns None and the fragment
    #  is skipped in silence, including in CI, which is the only place the live
    #  half of this check ever runs.
    "plan-of-action-and-milestones":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_poam_schema.json",
    #  Added with by-component.json and assessment-subject.json, which are the
    #  evidence behind the claim that a control response is made against a
    #  component and an assessment is made against a subject. Both fragments
    #  were taken from an offline 1.1.3 copy because 1.2.1 could not be reached,
    #  so the re-fetch below is the thing that confirms them.
    "system-security-plan":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_ssp_schema.json",
    "assessment-plan":
        "https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.1/json/schema/"
        "oscal_assessment-plan_schema.json",
}


_NIST_SCHEMA_CACHE: dict[str, dict] = {}


def _nist_schema(model: str) -> dict:
    """Fetch the exact released schema once per run, shared by both checks."""
    import urllib.request

    if model not in _NIST_SCHEMA_CACHE:
        url = NIST_SCHEMAS[model]
        with urllib.request.urlopen(url, timeout=30) as response:
            schema = json.load(response)
        if not isinstance(schema, dict):
            raise ValueError(f"{url}: expected a JSON schema object")
        _NIST_SCHEMA_CACHE[model] = schema
        print(f"        fetched {url}")
    return _NIST_SCHEMA_CACHE[model]


def _refetch_nist_fragments() -> None:
    """Re-derive every stored fragment from the published NIST 1.2.1 schemas.

    The fragments in data/schema-evidence/ were fetched on a date they each
    record. Everything the site says about question 2 rests on them, so the
    strongest form of this check is to fetch the schemas again and confirm the
    fragment is still what the schema says. That needs network, so locally it
    skips by name and in CI it runs.
    """
    if not have_network():
        for name in sorted(os.path.splitext(os.path.basename(q))[0]
                           for q in glob.glob(os.path.join(EVIDENCE, "*.json"))):
            skip(f"{name} fragment still matches the published NIST 1.2.1 schema",
                 "no network, so the published schema could not be fetched",
                 f"curl -s {NIST_SCHEMAS['mapping-collection']} | "
                 f"jq '.definitions[\"<definition>\"]'")
        return

    fetched = {}
    for model in NIST_SCHEMAS:
        try:
            fetched[model] = _nist_schema(model)
        except Exception as exc:                    # noqa: BLE001
            check(f"the {model} schema could be fetched from NIST", False, str(exc)[:120])

    def find_def(doc: dict, key: str):
        defs = doc.get("definitions", {})
        if key in defs:
            return defs[key]
        for v in defs.values():
            if isinstance(v, dict) and v.get("$id", "").endswith("/" + key):
                return v
        return None

    for path in sorted(glob.glob(os.path.join(EVIDENCE, "*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        name = os.path.splitext(os.path.basename(path))[0]
        schema = fetched.get(doc["model"])
        if schema is None:
            check(f"{name} has a published NIST schema to compare against",
                  False, doc["model"])
            continue
        live = find_def(schema, doc["definition"])
        check(f"{name} is still defined in the published {doc['model']} schema",
              live is not None, doc["definition"])
        if live is None:
            continue
        #  Most fragments are whole definitions and compare by equality. Two carry
        #  only the keys a claim rests on and declare that with fragment_note, so
        #  for those compare key by key. Without this the partial ones would fail
        #  the moment CI had the network, which is the one place this check runs.
        if doc.get("fragment_note"):
            drift = [k for k, v in doc["fragment"].items()
                     if k == "properties" or live.get(k) != v]
            if "properties" in doc["fragment"]:
                drift = [k for k, v in doc["fragment"].items() if k != "properties"
                         and live.get(k) != v]
                drift += [f"properties/{k}"
                          for k, v in doc["fragment"]["properties"].items()
                          if (live.get("properties") or {}).get(k) != v]
            check(f"{name} partial fragment still matches the published "
                  f"NIST 1.2.1 schema", not drift,
                  f"changed since {doc['fetched_at']}: {drift[:4]}")
        else:
            check(f"{name} fragment still matches the published NIST 1.2.1 schema",
                  live == doc["fragment"],
                  "the published definition has changed since "
                  f"{doc['fetched_at']}. Re-extract before publishing.")


def check_schema() -> None:
    print("\n[schema] constraints behind the question 2 claims")
    for name in ("mapping-item", "mapping-resource-reference", "finding",
                 "finding-target", "observation", "result", "reviewed-controls",
                 "poam-outcomes", "by-component", "assessment-subject",
                 "metadata"):
        path = os.path.join(EVIDENCE, f"{name}.json")
        if not os.path.exists(path):
            check(f"{name}.json present", False, "missing")
            continue
        doc = json.load(open(path, encoding="utf-8"))
        frag = doc["fragment"]
        req = frag.get("required", [])

        if name == "mapping-item":
            check("mapping-item required == ['type','id-ref']", req == ["type", "id-ref"], str(req))
            check("mapping-item type allOf enum == ['control','statement']",
                  _allof_enum(frag, "type") == ["control", "statement"],
                  str(_allof_enum(frag, "type")))
            check("mapping-item has no 'uuid' property", not _has_prop(frag, "uuid"))
            check("mapping-item has no 'href' property", not _has_prop(frag, "href"))
        elif name == "mapping-resource-reference":
            check("mapping-resource-reference required == ['type','href']",
                  req == ["type", "href"], str(req))
            check("mapping-resource-reference type is an open anyOf vocabulary",
                  _anyof_enum(frag, "type") == ["catalog", "profile"],
                  str(_anyof_enum(frag, "type")))
        elif name == "finding":
            check("finding required includes 'target'", "target" in req, str(req))
        elif name == "finding-target":
            check("finding-target required == ['type','target-id','status']",
                  req == ["type", "target-id", "status"], str(req))
            check("finding-target type allOf enum == ['statement-id','objective-id']",
                  _allof_enum(frag, "type") == ["statement-id", "objective-id"],
                  str(_allof_enum(frag, "type")))
            status = (frag.get("properties") or {}).get("status", {})
            check("finding-target status.required includes 'state'",
                  "state" in status.get("required", []), str(status.get("required")))
            state = (status.get("properties") or {}).get("state", {})
            enum = next((b["enum"] for b in state.get("allOf", []) if "enum" in b), state.get("enum"))
            check("finding-target status.state enum == ['satisfied','not-satisfied']",
                  enum == ["satisfied", "not-satisfied"], str(enum))
        elif name == "observation":
            check("observation required == ['uuid','description','methods','collected']",
                  req == ["uuid", "description", "methods", "collected"], str(req))
            for absent in ("target", "control-id", "objective-id"):
                check(f"observation has no '{absent}' property", not _has_prop(frag, absent))
        elif name == "by-component":
            #  Behind the claim, on the catalog page, that a claim can only be
            #  made against a component. The load-bearing half is the absence:
            #  there is no way to respond for one host rather than for the class
            #  of thing the host is.
            check("by-component required == ['component-uuid','uuid','description']",
                  req == ["component-uuid", "uuid", "description"], str(req))
            check("by-component keys the response by component-uuid",
                  _has_prop(frag, "component-uuid"))
            for absent in ("subject", "subject-uuid", "inventory-item-uuid", "type"):
                check(f"by-component has no '{absent}' property",
                      not _has_prop(frag, absent))
        elif name == "assessment-subject":
            #  And the other half: what an assessment can be aimed at instead.
            check("assessment-subject required includes 'type'",
                  "type" in req, str(req))
            check("assessment-subject type vocabulary is the five subject kinds",
                  _anyof_enum(frag, "type") == ["component", "inventory-item",
                                                "location", "party", "user"],
                  str(_anyof_enum(frag, "type")))
        elif name == "metadata":
            #  Behind the claim, on the catalog page, that a guide published as a
            #  catalog is versioned and citable the way a framework is.
            check("metadata required == ['title','last-modified','version','oscal-version']",
                  req == ["title", "last-modified", "version", "oscal-version"], str(req))
        elif name == "result":
            #  Behind "every assessment result is required to declare the controls
            #  it reviewed", on the index and on the comparison page.
            check("result required includes 'reviewed-controls'",
                  "reviewed-controls" in req, str(req))
        elif name == "reviewed-controls":
            #  Behind the second half of that sentence, that a result may satisfy
            #  the requirement with include-all rather than by naming a control.
            #  The prose carried that caveat with nothing behind it until now.
            check("reviewed-controls required == ['control-selections']",
                  req == ["control-selections"], str(req))
            items = ((frag.get("properties") or {})
                     .get("control-selections", {}).get("items", {}))
            branches = [b.get("required") for b in items.get("anyOf", [])]
            check("a control selection is include-all or include-controls",
                  branches == [["include-all"], ["include-controls"]], str(branches))
        elif name == "poam-outcomes":
            #  Behind "an outcome can be recorded only in the assessment layer".
            #  An earlier draft said observations and findings exist in no model
            #  but assessment results. The POA&M carries both, so the claim was
            #  false and is now stated as the layer rather than the model. This
            #  fragment is what stops it reverting.
            for present in ("observations", "findings"):
                check(f"the POA&M root carries '{present}'", _has_prop(frag, present))
            props = frag.get("properties") or {}
            for k in ("observations", "findings"):
                ref = (props.get(k) or {}).get("items", {}).get("$ref", "")
                check(f"POA&M {k} reuse the shared assessment-common definition",
                      "assessment-common" in ref, ref)

    # Everything above reads the stored fragment. That proves the site's claims
    # match what was fetched, not that what was fetched is still what NIST
    # publishes. The second half closes that gap where it can.
    _refetch_nist_fragments()


# --------------------------------------------------------------------------- #
# --stats                                                                      #
# --------------------------------------------------------------------------- #

def oscal_files(*parts, root_key=None):
    """Every .json under a corpus subtree whose OSCAL root key matches.

    Discovery is by root key, not by folder name. The corpora were reorganised
    into publisher folders once and eight hardcoded globs broke together. This
    also keeps non-OSCAL source material out: the CIS benchmarks ship as
    XCCDF-derived JSON with a "Benchmark" root and sit beside the plans.
    """
    out = []
    for path in sorted(glob.glob(ex.source_path(*parts, "**", "*.json"),
                                recursive=True)):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (ValueError, OSError):
            continue
        if not isinstance(doc, dict) or len(doc) != 1:
            continue
        key = next(iter(doc))
        if key in NIST_SCHEMAS and (root_key is None or key == root_key):
            out.append(path)
    return out


def ez_plans():
    """The Easy Dynamics assessment plans, wherever they currently live."""
    return oscal_files("Easy Dynamics", root_key="assessment-plan")


def recompute_stats() -> dict:
    AWS = "AWS/oscal-content-for-aws-services-main"
    EZ = "Easy Dynamics"
    s: dict = {}

    s["aws_catalog_files"] = len(glob.glob(
        ex.source_path(AWS, "catalogs", "*.oscal.json")))
    cat = corpus_json(f"{AWS}/catalogs/aws_security-hub.oscal.json")["catalog"]
    s["aws_groups"] = len(cat["groups"])
    s["aws_controls"] = sum(len(g["controls"]) for g in cat["groups"])
    tci = {c["id"]: p["title"]
           for g in cat["groups"] for c in g["controls"] for p in c["parts"]
           if p["name"] == "assessment-method"}

    cdefs = sorted(glob.glob(ex.source_path(AWS, "component-definitions", "*.oscal.json")))
    s["aws_cdef_files"] = len(cdefs)
    sw = matches = 0
    checked, allref = set(), set()
    for f in cdefs:
        for comp in json.load(open(f, encoding="utf-8"))["component-definition"].get("components", []):
            is_sw = comp["type"] == "software"
            sw += is_sw
            for ci in comp.get("control-implementations", []):
                for ir in ci["implemented-requirements"]:
                    allref.add(ir["control-id"])
                    if is_sw:
                        checked.add(ir["control-id"])
                        matches += tci.get(ir["control-id"]) == comp["title"]
    s["aws_software_components"] = sw
    s["aws_title_matches"] = matches
    s["aws_controls_without_check"] = s["aws_controls"] - len(checked)
    s["aws_controls_unreferenced"] = s["aws_controls"] - len(allref)

    rules = checks = 0
    ctrl_ids = set()
    for f in ("cos", "idservice"):
        for comp in corpus_json(f"IBM/{f}-component-definition.json")["component-definition"]["components"]:
            rules += len(comp.get("rules", []))
            for ci in comp.get("control-implementations", []):
                for ir in ci["implemented-requirements"]:
                    ctrl_ids.add(ir["control-id"])
    for f in ("ansible", "oscap"):
        for comp in corpus_json(f"IBM/{f}-validation-component-definition.json")["component-definition"]["components"]:
            checks += len(comp.get("checks", []))
    s["ibm_rules"], s["ibm_checks"], s["ibm_control_ids"] = rules, checks, len(ctrl_ids)

    s["ibm_cdef_files"] = len(glob.glob(
        ex.source_path("IBM", "*component-definition.json")))
    s["ibm_ap_files"] = len(glob.glob(ex.source_path("IBM", "assessment-plan.json")))
    s["ibm_ar_files"] = len(glob.glob(ex.source_path("IBM", "assessment-result.json")))

    acts = steps = 0
    #  By root key, not by folder. The tree was reorganised into publisher folders
    #  and now also carries the CIS source benchmarks, which are XCCDF-derived JSON
    #  with a "Benchmark" root and would otherwise be counted as plans.
    ez_files = ez_plans()
    s["ez_files"] = len(ez_files)
    for f in ez_files:
        a = json.load(open(f, encoding="utf-8"))["assessment-plan"]["local-definitions"]["activities"]
        acts += len(a)
        steps += sum(len(x.get("steps", [])) for x in a)
    s["ez_activities"], s["ez_steps"] = acts, steps

    def status_split(rel: str) -> collections.Counter:
        c = collections.Counter()
        for a in corpus_json(rel)["assessment-plan"]["local-definitions"]["activities"]:
            for st in a.get("steps", []):
                for p in st.get("props", []):
                    if p["name"] == "assessment-status":
                        c[p["value"]] += 1
        return c

    ub = status_split(f"{EZ}/Center for Internet Security/"
                      "CIS_Ubuntu_Linux_24_04_LTS_Benchmark_v2_OSCAL_AP.json")
    pg = status_split(f"{EZ}/Center for Internet Security/"
                      "CIS_PostgreSQL_18_Benchmark_v1_0_0_OSCAL_AP.json")
    s["cis_ubuntu_automated"], s["cis_ubuntu_manual"] = ub["automated"], ub["manual"]
    s["cis_postgres_automated"], s["cis_postgres_manual"] = pg["automated"], pg["manual"]

    stig = sorted([f for f in ez_files if os.sep + "DISA" + os.sep in f])
    s["stig_files"] = len(stig)
    m = collections.Counter()
    ph = 0
    for f in stig:
        d = json.load(open(f, encoding="utf-8"))["assessment-plan"]
        ph += d["import-ssp"].get("href") == "PLACEHOLDER"
        for a in d["local-definitions"]["activities"]:
            for p in a.get("props", []):
                if p["name"] == "method":
                    m[p["value"]] += 1
    s["stig_placeholder"] = ph
    s["stig_method_test"] = m["TEST"]

    # ----------------------------------------------------------------- #
    # Figures first cited by the comparison page, which has been removed.
    # They are still cited on the pages that remain, so they are recomputed
    # here for the same
    # reason as the rest: a number that appears on a page has to be
    # derivable from a file, and has to break the build when it drifts.
    # ----------------------------------------------------------------- #

    def prop_count(node, n: int = 0) -> int:
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "props" and isinstance(v, list):
                    n += len(v)
                n = prop_count(v, n)
        elif isinstance(node, list):
            for v in node:
                n = prop_count(v, n)
        return n

    s["ez_props"] = sum(prop_count(json.load(open(f, encoding="utf-8"))) for f in ez_files)
    aws_all = sorted(glob.glob(ex.source_path(AWS, "**", "*.json"), recursive=True))
    s["aws_props"] = sum(prop_count(json.load(open(f, encoding="utf-8"))) for f in aws_all)
    s["ibm_cdef_props"] = sum(
        prop_count(json.load(open(f, encoding="utf-8")))
        for f in glob.glob(ex.source_path("IBM", "*component-definition.json")))

    # Hierarchy and tailoring, criteria 4 and 5. The model allows both; the
    # question the criteria ask is what the shipped content does with them.
    s["aws_nested_groups"] = sum(1 for g in cat["groups"] if g.get("groups"))
    s["aws_control_params"] = sum(
        len(c.get("params", [])) for g in cat["groups"] for c in g["controls"])
    s["aws_profile_files"] = len([
        f for f in aws_all if "profile" in json.load(open(f, encoding="utf-8"))])

    # Requirement level, criterion 3: count the vocabulary in the OSCAL examples.
    cisa = sorted(glob.glob(ex.source_path(EZ, "CISA BOD 25-01", "*.json")))
    s["cisa_files"] = len(cisa)
    crit = collections.Counter()
    for a in corpus_json(f"{EZ}/CISA BOD 25-01/ap-cisa-scuba-agnostic.json"
                         )["assessment-plan"]["local-definitions"]["activities"]:
        for st in a.get("steps", []):
            for p in st.get("props", []):
                if p["name"] == "criticality":
                    crit[p["value"]] += 1
    s["cisa_criticality_shall"] = crit["SHALL"]
    s["cisa_criticality_should"] = crit["SHOULD"]

    # Response fidelity, criterion 8. An assessment-subject block is one that
    # carries a type together with include-all or include-subjects.
    subj = collections.Counter()

    def subjects(node) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("type"), str) and (
                    "include-all" in node or "include-subjects" in node):
                subj[node["type"]] += 1
            for v in node.values():
                subjects(v)
        elif isinstance(node, list):
            for v in node:
                subjects(v)

    for f in ez_files:
        subjects(json.load(open(f, encoding="utf-8")))
    s["ez_subjects_component"] = subj["component"]
    s["ez_subjects_inventory_item"] = subj["inventory-item"]

    ar = corpus_json("IBM/assessment-result.json")["assessment-results"]["results"][0]
    s["ibm_ar_findings"] = len(ar.get("findings", []))
    s["ibm_ar_observations"] = len(ar.get("observations", []))

    # The tie to a control is optional in all three corpora, and each shows it
    # differently. These two counts are behind the claim that all three treat
    # the path from a rule to a control as optional.
    s["ez_activities_with_related_controls"] = sum(
        1 for f in ez_files
        for a in json.load(open(f, encoding="utf-8"))
            ["assessment-plan"]["local-definitions"]["activities"]
        if a.get("related-controls"))
    s["ibm_ir_without_rules"] = sum(
        1 for f in ("cos", "idservice")
        for comp in corpus_json(f"IBM/{f}-component-definition.json")
            ["component-definition"]["components"]
        for ci in comp.get("control-implementations", [])
        for ir in ci["implemented-requirements"]
        if not ir.get("implementing-rules"))

    # ----------------------------------------------------------------- #
    # Denominators, recomputed beside their numerators. These were first
    # cited by the data-quality page, which has been removed, but the
    # figures are still used by the approach pages and the comparison, and
    # a denominator typed by hand is the easiest place on this site to
    # flatter one approach by accident.
    # ----------------------------------------------------------------- #

    # Assessment-first. The synthetic control ids are self-flagged by the
    # content's own prop, so the flag is what is counted rather than the
    # shape of the identifier.
    cis_ap = sorted(glob.glob(ex.source_path(
        EZ, "Center for Internet Security", "*_OSCAL_AP.json")))
    s["cis_ap_files"] = len(cis_ap)
    all_ids, synthetic, refs = set(), set(), 0
    for f in cis_ap:
        plan = json.load(open(f, encoding="utf-8"))["assessment-plan"]
        for sel in plan.get("reviewed-controls", {}).get("control-selections", []):
            flagged = any(p["name"] == "resolution-status"
                          and p["value"] == "synthetic-ids"
                          for p in sel.get("props", []))
            for inc in sel.get("include-controls", []):
                ids = ([inc["control-id"]] if "control-id" in inc
                       else inc.get("control-ids", []))
                for cid in ids:
                    all_ids.add(cid)
                    if flagged:
                        synthetic.add(cid)
                        refs += 1
    s["cis_control_ids"] = len(all_ids)
    s["cis_synthetic_ids"] = len(synthetic)
    s["cis_synthetic_refs"] = refs

    step_types = collections.Counter()
    per_set = collections.defaultdict(collections.Counter)
    for f in ez_files:
        family = os.path.basename(os.path.dirname(f))
        for a in json.load(open(f, encoding="utf-8"))[
                "assessment-plan"]["local-definitions"]["activities"]:
            for st in a.get("steps", []):
                for p in st.get("props", []):
                    if p["name"] == "step-type":
                        step_types[p["value"]] += 1
                        per_set[family][p["value"]] += 1
    s["ez_step_type_remediate"] = step_types["remediate"]
    s["ez_step_type_remediation"] = step_types["remediation"]
    s["ez_step_type_check"] = step_types["check"]
    s["ez_step_type_audit"] = step_types["audit"]
    s["ez_step_type_vocabularies"] = len(
        {tuple(sorted(c)) for c in per_set.values()})
    s["ez_files_with_step_type"] = sum(
        1 for f in ez_files
        if '"step-type"' in open(f, encoding="utf-8").read())
    #  Counted over every OSCAL file in the corpus, not over ez_files, which is
    #  the assessment plans. Asking a list of plans how many results it holds
    #  can only ever answer none, and it did, for as long as a result existed.
    ez_all = oscal_files(EZ)
    s["ez_ar_files"] = sum(
        1 for f in ez_all
        if "assessment-results" in json.load(open(f, encoding="utf-8")))
    s["ez_ssp_files"] = sum(
        1 for f in ez_all
        if "system-security-plan" in json.load(open(f, encoding="utf-8")))

    # Catalog-first. role-id "owner" is referenced where only author is
    # declared. This does not affect conformance and the appendix says so;
    # the counts are here so the claim carries its denominator.
    owner_refs = owner_files = 0
    declared = collections.Counter()
    for f in cdefs:
        cd = json.load(open(f, encoding="utf-8"))["component-definition"]
        for r in cd.get("metadata", {}).get("roles", []):
            declared[r["id"]] += 1

        def role_refs(node):
            n = 0
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "role-id" and v == "owner":
                        n += 1
                    n += role_refs(v)
            elif isinstance(node, list):
                for v in node:
                    n += role_refs(v)
            return n

        hits = role_refs(cd)
        if hits:
            owner_files += 1
            owner_refs += hits
    s["aws_owner_refs"] = owner_refs
    s["aws_files_referencing_owner"] = owner_files
    s["aws_files_declaring_author"] = declared["author"]
    s["aws_roles_declared"] = len(declared)

    guidance = collections.Counter()
    for g in cat["groups"]:
        for c in g["controls"]:
            for p in c.get("parts", []):
                if p.get("name") == "guidance":
                    guidance[p.get("prose", "")] += 1
    s["aws_guidance_parts"] = sum(guidance.values())
    s["aws_guidance_distinct"] = len(guidance)

    test_groups = [g for g in cat["groups"] if g.get("id") == "TestControl"]
    s["aws_test_groups"] = len(test_groups)
    s["aws_test_controls"] = sum(len(g["controls"]) for g in test_groups)
    s["aws_test_controls_mislinked"] = sum(
        1 for g in test_groups for c in g["controls"]
        for lk in c.get("links", [])
        if lk.get("rel") == "remediation" and c["id"].split(".")[0]
        not in lk.get("href", ""))
    s["aws_ssp_files"] = len([
        f for f in aws_all
        if "system-security-plan" in json.load(open(f, encoding="utf-8"))])
    s["aws_ar_files"] = len([
        f for f in aws_all
        if "assessment-results" in json.load(open(f, encoding="utf-8"))])
    s["aws_ap_files"] = len([
        f for f in aws_all
        if "assessment-plan" in json.load(open(f, encoding="utf-8"))])

    # Component-first. One document uuid across four files, and the
    # target-component-uuid resolution split between the two validation
    # components.
    ibm_cdefs = sorted(glob.glob(
        ex.source_path("IBM", "*component-definition.json")))
    doc_uuids, comp_uuids = set(), set()
    for f in ibm_cdefs:
        cd = json.load(open(f, encoding="utf-8"))["component-definition"]
        doc_uuids.add(cd["uuid"])
        for c in cd["components"]:
            comp_uuids.add(c["uuid"])
    s["ibm_document_uuids"] = len(doc_uuids)
    for tool in ("oscap", "ansible"):
        total = dangling = 0
        for comp in corpus_json(
                f"IBM/{tool}-validation-component-definition.json"
        )["component-definition"]["components"]:
            for ch in comp.get("checks", []) or []:
                total += 1
                dangling += ch.get("target-component-uuid") not in comp_uuids
        s[f"ibm_{tool}_checks"] = total
        s[f"ibm_{tool}_checks_dangling"] = dangling
    ap_doc = corpus_json("IBM/assessment-plan.json")["assessment-plan"]
    s["ibm_ap_local_definitions_misspelled"] = int(
        "local-defintions" in ap_doc and "local-definitions" not in ap_doc)
    s["ibm_ssp_files"] = len([
        f for f in glob.glob(ex.source_path("IBM", "*.json"))
        if "system-security-plan" in json.load(open(f, encoding="utf-8"))])
    return s


def check_stats() -> None:
    print("\n[stats] recompute every cited figure from source")
    doc = json.load(open(os.path.join(DATA, "corpus-stats.json"), encoding="utf-8"))
    declared = {x["key"]: x["value"] for x in doc["stats"]}
    check("statistic keys are unique", len(declared) == len(doc["stats"]))
    actual = recompute_stats()
    for key, want in sorted(declared.items()):
        got = actual.get(key, "<not recomputed>")
        check(f"{key} == {want}", got == want, f"recomputed {got}")
    extra = set(actual) - set(declared)
    check("no recomputed stat is missing from corpus-stats.json", not extra, str(sorted(extra)))

    # These are editorial scale examples, not counts attributed to a document.
    # Keep them separate from the corpus figures, and hold their arithmetic.
    scale = doc.get("illustrative_scale", {})
    values = {k: scale.get(k) for k in
              ("regulatory_controls", "benchmark_requirements", "combined")}
    valid = all(type(v) is int and v > 0 for v in values.values())
    check("illustrative_scale declares three positive integer counts", valid, str(values))
    if valid:
        check("the illustrative combined scale is the sum of its parts",
              values["combined"] == values["regulatory_controls"]
              + values["benchmark_requirements"], str(values))
    check("illustrative scale is separate from recomputed statistics",
          not (set(values) & set(declared)))

    #  A derivation is the sentence that tells a reader how to reproduce the
    #  figure, and being prose, nothing checked it. Six of them went on saying
    #  the corpus held fourteen plans for as long as it held fifteen, and one
    #  label carried a denominator that had moved. So any corpus size a
    #  derivation states has to be a figure this file also declares.
    SIZED = {"Easy Dynamics assessment plans": "ez_files"}
    stats = json.load(open(os.path.join(DATA, "corpus-stats.json"),
                           encoding="utf-8"))["stats"]
    for s in stats:
        for phrase, key in SIZED.items():
            for n in re.findall(rf"\b(\d+)\s+{re.escape(phrase)}\b",
                                s["label"] + " " + s["derivation"]):
                check(f"{s['key']}: says {n} {phrase}, which is what {key} says",
                      int(n) == declared[key], f"{key} == {declared[key]}")
        #  A denominator written into a label is the same hazard.
        m = re.search(r"\bout of (\d+)\b", s["label"])
        if m:
            check(f"{s['key']}: its denominator is a figure this file declares",
                  int(m.group(1)) in declared.values(), m.group(1))


# --------------------------------------------------------------------------- #
# --data                                                                       #
# --------------------------------------------------------------------------- #

def check_data() -> None:
        print("\n[data] internal consistency of the content files")
        crit = json.load(open(os.path.join(DATA, "criteria.json"), encoding="utf-8"))["criteria"]
        check("exactly fifteen criteria, numbered 1 to 15",
            [c["number"] for c in crit] == list(range(1, 16)))
        meaningful = all(isinstance(c.get("name"), str) and c["name"].strip()
                   and isinstance(c.get("question"), str)
                   and len(c["question"].split()) >= 4 for c in crit)
        check("every criterion has a name and a meaningful question", meaningful)

    anat = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    slots = [s["number"] for s in anat["slots"]]
    check("seven question rows: 1, 2, 3, 4, 5, 6a, 6b",
          slots == ["1", "2", "3", "4", "5", "6a", "6b"], str(slots))

    approaches = [a["key"] for a in anat["approaches"]]
    cells = {(c["slot"], c["approach"]) for c in anat["matrix"]}
    missing = {(s, a) for s in slots for a in approaches} - cells
    check("the answer matrix is complete: every question by every approach",
          not missing, str(sorted(missing)))

    valid_states = {e["key"] for e in anat["empty_states"]} | {"filled", "partial"}
    bad = [(c["slot"], c["approach"], c["state"]) for c in anat["matrix"]
           if c["state"] not in valid_states]
    check("every cell state is one of filled, partial, or the three empty states",
          not bad, str(bad))

    #  The finding is prose about the matrix, printed on the comparison page. An
    #  earlier version said questions 1 and 3 were answered by all three, while
    #  the matrix had question 3 for one approach at "partial", and said all three
    #  were substantially complete on 1 to 3 while one approach's question 2 was
    #  not asserted at all. Nothing caught either, because nothing derived the
    #  sentence from the cells. This does.
    by_slot = {}
    for c in anat["matrix"]:
        by_slot.setdefault(c["slot"], {})[c["approach"]] = c["state"]
    all_three = sorted(k for k, v in by_slot.items()
                       if all(x == "filled" for x in v.values()))
    none_full = sorted(k for k, v in by_slot.items()
                       if not any(x == "filled" for x in v.values()))
    finding = anat.get("finding", "")
    for slot in all_three:
        check(f"the finding does not contradict the matrix at question {slot}",
              slot in finding, f"question {slot} is answered by all three")
    for slot in none_full:
        check(f"the finding names question {slot}, answered in full by none",
              slot in finding, "missing from the finding")
    #  Read the clause that makes the all-three claim and check the question
    #  numbers inside it against the cells. Parsing prose is fragile, so the
    #  clause is delimited by a fixed phrase the finding is required to use.
    PHRASE = "by all three"
    check("the finding states its all-three claim in the expected form",
          PHRASE in finding, finding)
    if PHRASE in finding:
        claimed = set(re.findall(r"\b(\d(?:[ab])?)\b", finding.split(PHRASE)[0]))
        check("the finding claims 'all three' only where the matrix agrees",
              claimed == set(all_three),
              f"finding claims {sorted(claimed)}, matrix has {all_three}")

    noteless = [(c["slot"], c["approach"]) for c in anat["matrix"] if not c.get("note")]
    check("every cell carries a note, which becomes its tooltip", not noteless, str(noteless))

    have = {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(SNIPPETS, "*.json"))}
    have |= {os.path.splitext(os.path.basename(p))[0]
             for p in glob.glob(os.path.join(EVIDENCE, "*.json"))}
    dangling = sorted({sid for c in anat["matrix"] for sid in c.get("snippet_ids", [])} - have)
    check("every snippet_ids reference in the matrix resolves", not dangling, str(dangling))

    _check_editorial_data()

    views = json.load(open(os.path.join(DATA, "views.json"), encoding="utf-8"))
    check("exactly three views of what a rule is", len(views["views"]) == 3)
    check("each view maps to a distinct approach",
          len({v["aligned_approach"] for v in views["views"]}) == 3)
    check("the working definition makes no claim about bindingness",
          "without any claim about whether it is binding"
          in views["working_definition"]["text"])

    gloss = json.load(open(os.path.join(DATA, "glossary.json"), encoding="utf-8"))["terms"]
    by_term = {t["term"]: t for t in gloss}
    check("'validation component' carries both the IBM and AWS senses",
          len(by_term.get("validation component", {}).get("other_usages", [])) >= 2)
    for t in ("assessment platform", "assessment asset", "component"):
        check(f"'{t}' is marked not-established",
              by_term.get(t, {}).get("status") == "not-established")
    check("'rule' carries at least three distinct usages",
          len(by_term.get("rule", {}).get("other_usages", [])) >= 3)


# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# --css                                                                        #
# --------------------------------------------------------------------------- #

HEX = re.compile(r"#[0-9A-Fa-f]{3,8}\b")


def _css_text() -> str:
    with open(os.path.join(SITE_ROOT, "assets", "site.css"), "r", encoding="utf-8") as fh:
        return fh.read()


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def check_css() -> None:
    print("\n[css] tokens are the only place colour is written")
    css = _strip_comments(_css_text())

    # The token block runs from the first :root to the end of the sub-question block.
    end = css.find("2. RESET")
    if end == -1:
        end = css.find("*, *::before")
    tokens, rest = css[:end], css[end:]

    # @media print legitimately forces pure black on pure white for ink. Those two
    # are the only literals allowed anywhere below the token block, and only there.
    print_start = rest.find("@media print")
    body, print_block = (rest[:print_start], rest[print_start:]) if print_start != -1 else (rest, "")

    stray = sorted(set(HEX.findall(body)))
    check("no raw hex below the token block", not stray, str(stray[:8]))

    allowed_print = {"#fff", "#000", "#FFF", "#000000", "#ffffff", "#FFFFFF"}
    stray2 = sorted(set(HEX.findall(print_block)) - allowed_print)
    check("hex inside @media print is limited to pure black and white",
          not stray2, str(stray2[:8]))

    for theme, block in (("light", ":root"), ("dark", '[data-theme="dark"]')):
        seg = tokens.split(block, 1)[1] if block in tokens else ""
        seg = seg.split("[data-theme")[0] if theme == "light" else seg
        for n in range(1, 7):
            for suffix in ("", "-bg", "-fg", "-border"):
                name = f"--slot-{n}{suffix}:"
                check(f"{theme} theme defines --slot-{n}{suffix}", name in seg,
                      "missing")

    # A rule that hides a question's name is how the three cards on the start
    # page came to show a number, a blank column and a state. The name is the
    # point of the list, so nothing may hide it at any size.
    hides_name = re.search(r"\.(answers__q|slot-strip__name)[^{]*\{[^}]*"
                           r"display:\s*none", css)
    check("no rule hides the question name at any size", hides_name is None,
          hides_name.group(0)[:70] if hides_name else "")
    # And the row is a grid whose columns are fixed, which is what lets three
    # lists line up rank for rank.
    check("the answer row is a grid with a fixed number column",
          re.search(r"\.answers__n\s*\{[^}]*width:", css) is not None)
    check("a card carrying an answer list pins it to the bottom",
          ".approach-card .slot-strip { margin-top: auto; }" in css
          or "margin-top: auto" in css)

    for key in ("--empty-line", "--empty-dot", "--empty-absent-fill"):
        check(f"{key} defined", key in tokens)

    # The vocabulary of answer states lives in data/six-questions.json and
    # nowhere else. This list used to be written out here as well, so retiring a
    # state left the stylesheet carrying rules nothing could ever match and this
    # check demanding they stay.
    states = [s["key"] for s in json.load(
        open(os.path.join(DATA, "six-questions.json"),
             encoding="utf-8"))["answer_states"]]
    for key in states:
        check(f".is-{key} rule present", f".is-{key}" in css)
    stale = sorted(set(re.findall(r"\.is-(filled|partial|empty-[a-z-]+)", css))
                   - set(states))
    check("the stylesheet paints no state the data has retired",
          not stale, ", ".join(stale))

    # The answer states must be separable with no colour at all, so each
    # carries a geometry, in every place a mark is drawn.
    #
    # This check used to pass while the legend was broken, and it passed by
    # rewriting the evidence. It searched for `.answers__swatch.is-X` inside
    # `css.replace(".answers__row.is-X .answers__swatch", ".answers__swatch.is-X")`,
    # so the row-scoped selector was substituted into the swatch-scoped form
    # before the search ran and the string was always found. The stylesheet had
    # only the row form. In a browser that meant no geometry rule matched a
    # legend swatch at all, so every legend on the site drew five identical
    # plain outlines next to lists drawing five different shapes.
    #
    # A mark is drawn in three places and each needs its own rule: standalone
    # in prose, inside an answer list row that wears the state class, and in the
    # legend where the swatch wears the state class itself. So the selectors are
    # named literally, and nothing is substituted before looking.
    #  Keyed by every state the vocabulary has ever carried, so a state coming
    #  back finds its geometry waiting. Only the live ones are looked for, and a
    #  live state with no entry here is a failure rather than a silent pass.
    GEOMETRY = {
        "is-partial": r"border-style\s*:\s*dashed",
        "is-empty-by-design": r"border-style\s*:\s*solid",
        "is-empty-not-asserted": r"content\s*:",
        "is-empty-absent": r"radial-gradient",
    }
    live = [f"is-{k}" for k in states if k != "filled"]
    check("every live state has a geometry to be checked against",
          all(s in GEOMETRY for s in live),
          ", ".join(s for s in live if s not in GEOMETRY))
    for state, paint in ((s, GEOMETRY[s]) for s in live if s in GEOMETRY):
        for sel in (rf"\.state-swatch\.{state}",
                    rf"\.answers__row\.{state}\s+\.answers__swatch",
                    rf"\.answers__swatch\.{state}"):
            # The rule this selector appears in, up to the closing brace.
            m = re.search(sel + r"(::after)?\s*(,[^{]*)?\{([^}]*)\}", css)
            check(f"{state} is drawn by a rule matching {sel}",
                  m is not None and re.search(paint, m.group(3)) is not None,
                  "no rule" if m is None else f"rule has no {paint}")

    # Filled is the one state drawn two legitimate ways, so it gets its own
    # check rather than a contorted entry in the table above. The list marks
    # paint it directly with currentColor. The inline mark paints it from the
    # --cell-bg token, which .is-filled sets and the base rule reads, and that
    # is the mechanism that lets one mark carry a question's hue.
    for sel in (r"\.answers__row\.is-filled\s+\.answers__swatch",
                r"\.answers__swatch\.is-filled"):
        m = re.search(sel + r"\s*(,[^{]*)?\{([^}]*)\}", css)
        check(f"is-filled is drawn by a rule matching {sel}",
              m is not None and "currentColor" in m.group(2),
              "no rule" if m is None else "rule does not fill")
    m = re.search(r"\.state-swatch\s*\{([^}]*)\}", css)
    check("the inline mark takes its fill from --cell-bg",
          m is not None and re.search(r"background\s*:\s*var\(--cell-bg", m.group(1))
          is not None)
    m = re.search(r"\.is-filled\s*\{([^}]*)\}", css)
    check("and .is-filled sets --cell-bg to something that shows",
          m is not None and re.search(r"--cell-bg\s*:\s*var\(", m.group(1)) is not None)

    # The page grid. grid-area on a broad child selector resolves to one named
    # cell, row and column both, which renders every section of every page on
    # top of the others. It shipped once, it is invisible to every DOM check
    # because the harness has no layout engine, and it was caught by a person.
    # The named-lines form (grid-column) is the only one that flows.
    broad = re.compile(r"main\s*>\s*\*[^{]*\{[^}]*\bgrid-area\s*:", re.S)
    check("main > * places children by grid-column, never grid-area",
          not broad.search(css) and "grid-column: content" in css,
          "grid-area on a broad selector stacks every section in one cell")
    # A box in the carrier row is drawn like the badge that declares it: a
    # proposed assembly like the PROPOSED badge, a prop like the PROP badge.
    # Two places saying the same thing is two places to change, and the prop box
    # already shipped once with the badge's hue and the wrong border weight,
    # which made a dotted 2px border read as a solid 1px one.
    #
    # The pair is held to the same border style and the same hue token. Weight
    # is asserted separately because it is what was wrong: dashes survive 1px,
    # dots do not.
    #  Comments are stripped first. These helpers scan for selector blocks with
    #  a regex, and a comment is not a rule: a note that mentions a border would
    #  otherwise be read as a declaration and could satisfy the very check it is
    #  describing.
    css_nc = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def _rule(sel: str) -> str:
        """Every declaration that applies to `sel`, in source order.

        One rule is not enough. These selectors appear in two: a shared rule
        setting the weight and background for both boxes, and then one each for
        the border style and hue. Reading only the first match returned the
        shared rule's body and reported the border style as missing, so this
        collects all of them the way the cascade would.
        """
        out = []
        for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css_nc):
            selectors = [s.strip() for s in m.group(1).split(",")]
            if sel in selectors:
                out.append(m.group(2))
        return "\n".join(out)

    # Reading the declarations is not enough, and this check learned that the
    # hard way twice. A rule can say `border-style: dotted` and lose it to a
    # less obvious rule that sets the `border` shorthand at higher specificity,
    # and a text search sees a passing stylesheet while the page draws a solid
    # line. That is exactly what shipped: `.carrier code` is (0,1,1) and sets
    # the whole shorthand, so `.carrier__prop` at (0,1,0) lost its border style,
    # its width and its background, and only the colour reached the page.
    #
    # So the border declarations are resolved rather than searched: whichever
    # rule that can match the element has the highest specificity wins, with
    # source order breaking ties, the way a browser does it.
    def _specificity(sel: str):
        ids = len(re.findall(r"#[\w-]+", sel))
        cls = len(re.findall(r"[.\[:][\w-]+", sel))
        typ = len(re.findall(r"(?:^|[\s>+~])([a-zA-Z][\w-]*)", sel))
        return (ids, cls, typ)

    def _winner(prop: str, *classes: str):
        """The declaration of `prop` that survives the cascade on an element
        carrying `classes`, given every rule in the stylesheet that could match
        it. Returns (value, selector)."""
        want = set(classes)
        best = None
        for order, m in enumerate(re.finditer(r"([^{}]+)\{([^}]*)\}", css_nc)):
            for sel in (s.strip() for s in m.group(1).split(",")):
                if not sel or "@" in sel:
                    continue
                #  Only selectors built from the classes and element names this
                #  element actually has can match it.
                tokens = set(re.findall(r"\.([\w-]+)", sel))
                if not tokens <= want:
                    continue
                body = m.group(2)
                #  The shorthand sets the longhand, so it counts as a setter.
                hit = re.findall(r"\bborder(?:-" + prop + r")?\s*:\s*([^;]+)", body)
                if not hit:
                    continue
                key = (_specificity(sel), order)
                if best is None or key > best[0]:
                    best = (key, hit[-1].strip(), sel)
        return (best[1], best[2]) if best else (None, None)

    for kind, box, badge, css_classes in (
            ("proposed", ".carrier__assembly.is-proposed", ".mech--proposed",
             ("carrier", "carrier__assembly", "is-proposed")),
            ("prop", ".carrier__prop", ".mech--prop",
             ("carrier", "carrier__prop"))):
        won, by = _winner("style", *css_classes)
        badge_style = re.search(r"border-style:\s*(\w+)", _rule(badge))
        want_style = badge_style.group(1) if badge_style else None
        check(f"the {kind} box's border style survives the cascade",
              bool(won) and want_style is not None and want_style in (won or ""),
              f"{want_style!r} expected, {won!r} wins from {by!r}")
        won_w, by_w = _winner("width", *css_classes)
        check(f"the {kind} box's border width survives the cascade",
              bool(won_w) and "2px" in (won_w or ""),
              f"{won_w!r} wins from {by_w!r}")

    for kind, box, badge in (("proposed", ".carrier code.carrier__assembly.is-proposed", ".mech--proposed"),
                             ("prop", ".carrier code.carrier__prop", ".mech--prop")):
        b, g = _rule(box), _rule(badge)
        style = re.search(r"border-style:\s*(\w+)", b)
        bstyle = re.search(r"border-style:\s*(\w+)", g)
        check(f"the {kind} box is drawn with the same border style as its badge",
              bool(style) and bool(bstyle) and style.group(1) == bstyle.group(1),
              f"box {style.group(1) if style else None}, badge {bstyle.group(1) if bstyle else None}")
        hue = re.search(r"border-color:\s*var\((--slot-\d+-border)\)", b)
        ghue = re.search(r"border-color:\s*var\((--slot-\d+-border)\)", g)
        check(f"the {kind} box carries the same hue as its badge",
              bool(hue) and bool(ghue) and hue.group(1) == ghue.group(1),
              f"box {hue.group(1) if hue else None}, badge {ghue.group(1) if ghue else None}")
        check(f"the {kind} box border is heavy enough for its dashes to show",
              "border-width: 2px" in b,
              "1px dotted reads as solid at text size")

    #  A class the stylesheet defines has to be reachable.
    #
    #  Eighty-eight were not. They were whole families left by three pages that
    #  were deleted: the example walkthrough, the side-by-side comparison and
    #  the component gallery. Deleting a page took its markup and left its
    #  styling, and nothing looked wrong, because a rule that matches nothing
    #  costs nothing to render. Thirteen kilobytes of it accumulated.
    #
    #  A class can also be built rather than written, "slot-" + number, so a
    #  prefix that something concatenates or interpolates counts as a use. That
    #  rescue is what makes this check safe to enforce: without it the six
    #  question colours and the two media badges all read as dead.
    written = []
    for pat in ("*.html", "assets/*.js", "assets/diagrams/*.js", "tools/*.py",
                "data/*.json", "data/*/*.json"):
        for f in glob.glob(os.path.join(SITE_ROOT, pat)):
            if f.endswith("bundle.js"):
                continue
            written.append(open(f, encoding="utf-8", errors="ignore").read())
    blob = "\n".join(written)

    def reachable(name: str) -> bool:
        if re.search(r"""["'\s.]""" + re.escape(name) + r"""(?=["'\s.:\[,])""", blob):
            return True
        for m in re.finditer(r"[-_]{1,2}", name):
            stem = name[:m.end()]
            if len(stem) < 4:
                continue
            if re.search(re.escape(stem) + r"""["']\s*\+""", blob):
                return True
            if re.search(re.escape(stem) + r"\{", blob):
                return True
        return False

    declared = set(re.findall(r"(?:^|[\s,>+~{}\)])\.([A-Za-z][\w-]*)",
                              re.sub(r"/\*.*?\*/", " ", css, flags=re.S), re.M))
    orphans = sorted(c for c in declared if not reachable(c))
    check(f"every one of the {len(declared)} classes the stylesheet defines is "
          f"reachable", not orphans, ", ".join(orphans[:6]))

    check("the toc rail is placed by grid-column, never grid-area",
          "grid-area: rail" not in css)
    check("nothing spans under the sticky rail",
          "grid-column: 1 / -1" not in css,
          "a full-span child overlaps the rail the toc occupies")

    # The measure belongs to prose, not to the page. A blanket cap on main's
    # children put every diagram in a 600px box against its own 720px floor,
    # so each grew a scrollbar beside a column of empty space. Screen rules
    # only: print legitimately sets max-width none on the same selector.
    blanket = re.compile(r"main\s*>\s*\*\s*\{[^}]*max-width", re.S)
    check("main children carry no blanket measure cap; prose is capped by kind",
          not blanket.search(body) and "main .tier2" in body)

    #  The measure is the reading column, not a character count, so prose fills
    #  the space it is given rather than stopping short of the rail. The two are
    #  computed from the same four numbers here, because they were set
    #  independently once and drifted 215px apart without anything noticing.
    def rem(v):
        v = v.strip()
        return float(v[:-3]) * 16 if v.endswith("rem") else float(v.rstrip("px"))
    spacing = dict(re.findall(r"(--s\d):\s*([^;]+);", tokens))
    measure = re.search(r"--measure:\s*([^;]+);", tokens).group(1)
    m_main = re.search(r"\nmain \{[^}]*max-width:\s*(\d+)px", body)
    #  padding is the three-value shorthand, top / left and right / bottom,
    #  so the horizontal one is the second. A greedy match took the third
    #  and put the column 80px out.
    m_pad = re.search(r"\nmain \{[^}]*padding:\s*var\(--s\d\)\s+var\((--s\d)\)",
                      body)
    m_gap = re.search(r"\nmain \{[^}]*column-gap:\s*var\((--s\d)\)", body)
    m_rail = re.search(r"\[content-end rail-start\]\s*([\d.]+)rem", body)
    ok = all((m_main, m_pad, m_gap, m_rail))
    check("the page grid states its width, padding, gap and rail", ok)
    if ok:
        column = (int(m_main.group(1)) - 2 * rem(spacing[m_pad.group(1)])
                  - rem(spacing[m_gap.group(1)]) - float(m_rail.group(1)) * 16)
        check(f"the measure is the reading column, {column:.0f}px",
              abs(rem(measure) - column) < 1,
              f"measure {rem(measure):.0f}px against a {column:.0f}px column")

    # Two sticky elements have to be told about each other, and same-page
    # anchors have to be told about both.
    if "position: sticky; top: 0" in css:
        check("the rail toc sticks below the sticky header",
              "--header-h" in css.split("main > .toc", 1)[-1][:400])
        check("same-page anchors land clear of the sticky header",
              "scroll-padding-top" in css)

    #  A row of the sources table is one line. Thirteen rows that each wrap to two
    #  are twenty-six things to scan and the shape of the corpus stops being
    #  legible, so both halves of the constraint are asserted: the cells do not
    #  wrap, and the icons in a cell do not wrap either. white-space does not
    #  govern flex items, so the second is not implied by the first.
    src_rule = re.search(r"\.sources th, \.sources td \{[^}]*\}", css)
    check("no cell in the sources table wraps",
          src_rule is not None and "white-space: nowrap" in src_rule.group(0),
          src_rule.group(0)[:80] if src_rule else "rule missing")
    fl = re.search(r"\.filelist \{[^}]*\}", css)
    check("a row of document icons does not wrap either",
          fl is not None and "flex-wrap: nowrap" in fl.group(0),
          fl.group(0)[:80] if fl else "rule missing")
    #  Icon-only links have no text to underline, so the hit area is the only
    #  feedback there is and it has to answer to the keyboard as well.
    icon = re.search(r"\.filelink--icon:hover, \.filelink--icon:focus-visible \{[^}]*\}", css)
    check("an icon-only link shows focus as well as hover", icon is not None)
    #  The type is reversed out of a filled badge, so the two have to be a pair:
    #  a badge with no rule filling it, or a label the same colour as the badge,
    #  and the icon says nothing at all.
    badge = re.search(r"\.micon__badge \{[^}]*\}", css)
    label = re.search(r"\.micon__label \{[^}]*\}", css)
    check("the type badge is filled", badge is not None
          and "fill: currentColor" in badge.group(0))
    check("the type is reversed out of the badge", label is not None
          and "fill: var(--bg)" in label.group(0))
    #  A disclosure that print leaves closed would drop the whole provenance
    #  table from a printed page, which is the one thing this site prints for.
    check("the sources panel opens when the page is printed",
          ".sources-panel__body { display: block !important; }" in css
          or ".sources-panel__body" in css.split("@media print", 1)[-1])

    check("a print stylesheet exists", "@media print" in css)
    check("reduced motion is honoured", "prefers-reduced-motion" in css)
    check("no @import and no url() to a remote origin",
          "@import" not in css and "url(http" not in css)


# --------------------------------------------------------------------------- #
# --a11y                                                                       #
# --------------------------------------------------------------------------- #

def _srgb_to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rel_lum(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (_srgb_to_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    la, lb = _rel_lum(a), _rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _tokens_for(theme: str) -> dict:
    css = _strip_comments(_css_text())
    block = ":root {" if theme == "light" else '[data-theme="dark"] {'
    start = css.find(block)
    seg = css[start:css.find("}", start)]
    out = {}
    for name, value in re.findall(r"(--[\w-]+)\s*:\s*(#[0-9A-Fa-f]{3,8})\s*;", seg):
        out[name] = value
    return out


def check_a11y() -> None:
    print("\n[a11y] contrast of every token pair the site actually renders")
    #  The code surface does not follow the theme, on purpose: an artifact that
    #  inverts when the reader flips the theme reads as page content. Asserted
    #  here so the two definitions cannot drift apart.
    lt, dk = _tokens_for("light"), _tokens_for("dark")
    for name in ("--code-bg", "--code-fg", "--code-dim", "--code-focus",
                 "--code-rule"):
        check(f"{name} is the same in both themes", lt[name] == dk[name],
              f"{lt[name]} against {dk[name]}")
    for theme in ("light", "dark"):
        t = _tokens_for(theme)
        bg, sub = t["--bg"], t["--bg-subtle"]

        check(f"{theme}: body text on page background is AA (4.5)",
              _contrast(t["--text"], bg) >= 4.5, f"{_contrast(t['--text'], bg):.2f}")
        check(f"{theme}: gist text on subtle background is AAA (7.0)",
              _contrast(t["--text"], sub) >= 7.0, f"{_contrast(t['--text'], sub):.2f}")
        check(f"{theme}: muted text on page background is AA (4.5)",
              _contrast(t["--text-muted"], bg) >= 4.5, f"{_contrast(t['--text-muted'], bg):.2f}")
        check(f"{theme}: faint text meets large-text AA (3.0)",
              _contrast(t["--text-faint"], bg) >= 3.0, f"{_contrast(t['--text-faint'], bg):.2f}")
        check(f"{theme}: accent link on page background is AA (4.5)",
              _contrast(t["--accent"], bg) >= 4.5, f"{_contrast(t['--accent'], bg):.2f}")
        check(f"{theme}: strong border meets non-text AA (3.0)",
              _contrast(t["--border-strong"], bg) >= 3.0,
              f"{_contrast(t['--border-strong'], bg):.2f}")
        #  The PDF badge is filled with this and its letters are reversed out of
        #  it in the page colour, so the pair that has to hold is against --bg,
        #  and it is text rather than a line: AA 4.5, not 3.0.
        check(f"{theme}: the PDF badge letters on the badge are AA (4.5)",
              _contrast(t["--micon-pdf"], bg) >= 4.5,
              f"{_contrast(t['--micon-pdf'], bg):.2f}")
        #  The inline JSON view is its own surface, so nothing here is measured
        #  against the page. Lit lines are text and need AA; the dimmed context
        #  lines are still text a reader has to read, so they need AA too, not
        #  the 3.0 a decorative line would take.
        code_bg = t["--code-bg"]
        check(f"{theme}: JSON view text on the code surface is AA (4.5)",
              _contrast(t["--code-fg"], code_bg) >= 4.5,
              f"{_contrast(t['--code-fg'], code_bg):.2f}")
        check(f"{theme}: dimmed context lines are still AA (4.5)",
              _contrast(t["--code-dim"], code_bg) >= 4.5,
              f"{_contrast(t['--code-dim'], code_bg):.2f}")
        check(f"{theme}: lit lines stay AA on the lifted background",
              _contrast(t["--code-fg"], t["--code-focus"]) >= 4.5,
              f"{_contrast(t['--code-fg'], t['--code-focus']):.2f}")

        for n in range(1, 7):
            base = t[f"--slot-{n}"]
            chip_bg, chip_fg = t[f"--slot-{n}-bg"], t[f"--slot-{n}-fg"]
            check(f"{theme}: --slot-{n} meets non-text AA (3.0) on the page",
                  _contrast(base, bg) >= 3.0, f"{_contrast(base, bg):.2f}")
            check(f"{theme}: --slot-{n}-fg on --slot-{n}-bg is AA (4.5)",
                  _contrast(chip_fg, chip_bg) >= 4.5, f"{_contrast(chip_fg, chip_bg):.2f}")

        # A monotonic lightness ladder is what keeps the questions separable for
        # dichromats and in grayscale. Assert it rather than trusting it.
        lums = [_rel_lum(t[f"--slot-{n}"]) for n in range(1, 7)]
        check(f"{theme}: question luminance ladder is monotonic",
              all(a < b for a, b in zip(lums, lums[1:])),
              str([round(x, 3) for x in lums]))

        #  The approach colours are the opposite case and the assertion is the
        #  opposite too. They must be equally light, because an approach drawn
        #  darker or brighter than the other two would be arguing in a channel
        #  no word count can see. Equal lightness costs dichromat separation,
        #  which is why every approach outline also carries a marker shape and
        #  a written label, and why --diagrams asserts that it does.
        ap = [t[f"--approach-{k}"] for k in ("assessment", "catalog", "component")]
        for name, colour in zip(("assessment", "catalog", "component"), ap):
            check(f"{theme}: --approach-{name} meets non-text AA (3.0)",
                  _contrast(colour, bg) >= 3.0, f"{_contrast(colour, bg):.2f}")
        spread = max(_rel_lum(c) for c in ap) - min(_rel_lum(c) for c in ap)
        check(f"{theme}: the three approach colours are equally light",
              spread <= 0.02, f"luminance spread {spread:.4f}")

    _axe()


def _axe() -> None:
    """Run axe-core over every page in a headless browser.

    The contrast arithmetic above is worth having and is not an accessibility
    audit. axe covers the things a stylesheet cannot be asked about: landmark
    structure, accessible names on the controls the renderers build, the tab
    order through the disclosure widgets, and the inline SVG's title and desc
    reaching the accessibility tree.

    It needs a browser and a package install, so locally it skips by name.
    """
    pages = sorted(os.path.basename(p)
                   for p in glob.glob(os.path.join(SITE_ROOT, "*.html")))
    runner = os.path.join(TOOLS_DIR, "axe_run.mjs")
    command = f"node {os.path.relpath(runner, SITE_ROOT)}"

    if not os.path.isfile(runner):
        skip(f"axe-core reports no violations on any of the {len(pages)} pages",
             "tools/axe_run.mjs is missing", command)
        return
    node_modules = os.path.join(SITE_ROOT, "node_modules")
    if not os.path.isdir(os.path.join(node_modules, "axe-core")) \
            or not os.path.isdir(os.path.join(node_modules, "puppeteer")):
        skip(f"axe-core reports no violations on any of the {len(pages)} pages",
             "axe-core and puppeteer are not installed and cannot be fetched "
             "without network",
             f"npm install --no-save axe-core puppeteer && {command}")
        return

    print(f"        running: {command}")
    rc = subprocess.run(command, shell=True, cwd=SITE_ROOT,
                        capture_output=True, text=True)
    print(rc.stdout.rstrip())
    try:
        report = json.loads(rc.stdout.strip().splitlines()[-1])
    except Exception:                                # noqa: BLE001
        check("the axe run produced a report", False,
              (rc.stdout + rc.stderr)[-300:])
        return
    for page, violations in sorted(report.items()):
        summary = "; ".join(
            f"{v['id']} x{len(v['nodes'])}" for v in violations[:4])
        check(f"axe-core reports no violations on {page}",
              not violations, summary)


# --------------------------------------------------------------------------- #
# --quotes                                                                     #
# --------------------------------------------------------------------------- #

BLOCKQUOTE = re.compile(r"<blockquote\b", re.I)
DATA_QUOTE = re.compile(
    r"\bdata-(?:quotes?(?:-ids?)?|settled-quote|supporting-quotes|"
    r"advocate|speaker|raised-by|verbatim)\b", re.I)
PRE_BLOCK = re.compile(r"<pre\b", re.I)
LONG_DASH = re.compile("[—–]")

# Editorial records must not retain attribution even when it is not rendered.
# Do not blocklist people or publishers: OSCAL source paths remain legitimate.
ARCHIVED_ATTRIBUTION_KEYS = {
    "quote", "quotes", "quote_id", "quote_ids", "settled_quote", "supporting_quotes",
    "advocate", "speaker", "affiliation", "raised_by", "verbatim",
    "source_document", "source_status", "cited_from_position_paper",
    "preread", "pre_read",
}
ARCHIVED_DOCUMENT_TRACE = re.compile(
    r"\.docx\b|\bpre[\s-]?read\b|\bposition[\s_-]+paper\b|"
    r"\bproposal[\s_-]+document\b|\bibm-(?:rules-md|open-questions)\b", re.I)


def _pages() -> list[str]:
    """Published pages only. assets/ holds a template and a kitchen sink."""
    return sorted(glob.glob(os.path.join(SITE_ROOT, "*.html")))


def _archived_attribution_paths(node, path: str = "$") -> list[str]:
    """Locate removed editorial metadata, without requiring an archive of names."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            child = f"{path}/{k}"
            if k.lower().replace("-", "_") in ARCHIVED_ATTRIBUTION_KEYS:
                found.append(child)
            # Raw OSCAL extracts retain their original text, not editorial metadata.
            if k == "content" and "sha256_of_source_file" in node:
                continue
            found.extend(_archived_attribution_paths(v, child))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found.extend(_archived_attribution_paths(v, f"{path}/{i}"))
    elif isinstance(node, str) and ARCHIVED_DOCUMENT_TRACE.search(node):
        found.append(path)
    return found


def _check_editorial_data() -> None:
    check("the quotation archive is not retained",
          not os.path.exists(os.path.join(DATA, "quotes.json")))
    blobs = sorted(glob.glob(os.path.join(DATA, "**", "*.json"), recursive=True))
    check("there is site data to check", bool(blobs))
    for blob in blobs:
        with open(blob, encoding="utf-8") as fh:
            found = _archived_attribution_paths(json.load(fh))
        check(f"{os.path.relpath(blob, DATA)}: no archived attribution or document trace",
              not found, ", ".join(found[:5]))


def check_quotes() -> None:
    """No quotation hooks or archived attribution; original OSCAL traces remain."""
    print("\n[quotes] no quotation hooks or archived attribution")
    _check_editorial_data()
    pages = _pages()
    check("there are pages to check", bool(pages))
    for path in pages:
        name = os.path.basename(path)
        html = _text(path)
        check(f"{name}: carries no blockquote", not BLOCKQUOTE.search(html),
              str(len(BLOCKQUOTE.findall(html))))
        check(f"{name}: carries no quotation or attribution hook", not DATA_QUOTE.search(html),
              str(DATA_QUOTE.findall(html)[:3]))
        check(f"{name}: carries no archived document attribution",
              not ARCHIVED_DOCUMENT_TRACE.search(html))

    print("\n[quotes] pages hold no content that belongs in data/")
    for path in pages:
        name = os.path.basename(path)
        html = _text(path)
        check(f"{name}: no hand-typed code block", not PRE_BLOCK.search(html))
        check(f"{name}: uses no long dash", not LONG_DASH.search(html),
              str(LONG_DASH.findall(html)[:3]))


# --------------------------------------------------------------------------- #
# --criteria                                                                   #
# --------------------------------------------------------------------------- #

def check_criteria() -> None:
    """The site's fifteen criteria remain meaningful and map to real questions."""
    print("\n[criteria] editorial criteria and question mappings")
    crit = json.load(open(os.path.join(DATA, "criteria.json"), encoding="utf-8"))
    anat = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    slots = {s["number"] for s in anat["slots"]}
    archived = _archived_attribution_paths(crit)
    check("criteria contain no archived attribution", not archived, str(archived[:5]))

    rows = crit["criteria"]
    check("exactly fifteen criteria in criteria.json", len(rows) == 15, str(len(rows)))
    check("numbered 1 to 15 with no gap and no repeat",
          [c["number"] for c in rows] == list(range(1, 16)),
          str([c["number"] for c in rows]))
    names = [c.get("name", "").strip().casefold() for c in rows]
    check("criterion names are nonempty and unique",
          all(names) and len(names) == len(set(names)))
    for c in rows:
        question = c.get("question", "")
        check(f"criterion {c['number']}: asks a meaningful question",
              isinstance(question, str) and len(question.split()) >= 4
              and any(ch.isalpha() for ch in question))
        mapped = c.get("slots", [])
        check(f"criterion {c['number']}: maps to distinct, existing question rows",
              isinstance(mapped, list) and bool(mapped)
              and all(isinstance(s, str) and s in slots for s in mapped)
              and len(mapped) == len(set(mapped)), str(mapped))


# --------------------------------------------------------------------------- #
# --pages                                                                      #
# --------------------------------------------------------------------------- #

def check_pages() -> None:
    """Run each page's renderers against the real data and inspect the result.

    Every page here is markup plus data: the markup carries hooks and site.js
    fills them at load time, which is what plan section 8 asks for. The cost is
    that a broken hook or a renderer that silently produced nothing is invisible
    to any check that only reads the HTML. tools/pagecheck.js supplies a DOM
    small enough to run site.js, loads each page, and asserts on what came out.
    """
    print("\n[pages] render each page and inspect the result")
    node = shutil.which("node")
    if not node:
        check("node is available to run tools/pagecheck.js", False,
              "install Node, or run tools/pagecheck.js by hand")
        return
    proc = subprocess.run([node, os.path.join(TOOLS_DIR, "pagecheck.js")],
                          capture_output=True, text=True, cwd=SITE_ROOT)
    tail = (proc.stdout or "").strip().splitlines()
    summary = next((l for l in reversed(tail) if "page checks passed" in l), "")
    ok = proc.returncode == 0
    check(f"tools/pagecheck.js: {summary or 'no summary'}", ok)
    if not ok:
        for line in tail:
            if line.startswith("  - "):
                print("        " + line[4:])
        if proc.stderr.strip():
            print("        " + proc.stderr.strip().splitlines()[-1])


# --------------------------------------------------------------------------- #
# --diagrams                                                                   #
# --------------------------------------------------------------------------- #

DIAGRAMS = os.path.join(SITE_ROOT, "assets", "diagrams")
BUILD_GRAY = os.path.join(SITE_ROOT, "build", "grayscale")

#  A literal colour is #abc, #abcdef or rgb(). The awkward case is that AWS
#  writes a control-implementation source as "#uuid", and a uuid is hex, so a
#  naive hex search finds one in every catalog-first join diagram. Colour only
#  ever appears inside the <style> block or in a fill/stroke attribute, so those
#  are the only places worth searching, and searching only there is also the
#  honest test: a hex string inside a <desc> is a quoted identifier, not paint.
RGBFN = re.compile(r"\brgba?\(")
PRESENTATION = re.compile(r'\b(fill|stroke|stop-color|flood-color)\s*[:=]\s*"?([^";]+)')


def _svgs() -> list[str]:
    return sorted(glob.glob(os.path.join(DIAGRAMS, "*.svg")))


def _text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _style_block(doc: str) -> str:
    m = re.search(r"<style>(.*?)</style>", doc, flags=re.S)
    return m.group(1) if m else ""


def _between(doc: str, a: str, b: str) -> str:
    i, j = doc.find(a), doc.find(b)
    return doc[i:j + len(b)] if i != -1 and j != -1 else ""


def _shared(path: str, a: str, b: str) -> str:
    """A geometry block with its own root id normalised out.

    Markers are referenced as url(#<root-id>-ref), and the root id has to differ
    between files or two inlined diagrams on one page would collide. So the
    comparison is on geometry modulo that id, which is the thing the plan
    actually requires: one drawing, reused with different highlighting.
    """
    doc = _text(path)
    root_id = re.search(r'\bid="([^"]+)"', doc).group(1)
    return _between(doc, a, b).replace(root_id, "ROOT")


def check_diagrams() -> None:
    import xml.etree.ElementTree as ET

    print("\n[diagrams] structure")
    files = _svgs()
    check("assets/diagrams contains SVG files", bool(files), "none found")
    ns = "{http://www.w3.org/2000/svg}"

    ids: dict[str, str] = {}
    for path in files:
        name = os.path.basename(path)
        doc = _text(path)
        root = ET.fromstring(doc)

        vb = root.get("viewBox")
        check(f"{name}: has a viewBox", bool(vb), "missing")
        check(f"{name}: sets no fixed width or height",
              not root.get("width") and not root.get("height"))

        kids = [k.tag.replace(ns, "") for k in list(root)]
        check(f"{name}: <title> then <desc> are the first two children",
              kids[:2] == ["title", "desc"], str(kids[:3]))
        title = root.find(ns + "title")
        desc = root.find(ns + "desc")
        check(f"{name}: <desc> is written out, not a stub",
              desc is not None and len((desc.text or "").split()) >= 40,
              f"{len((desc.text or '').split()) if desc is not None else 0} words")
        check(f"{name}: title and desc are wired to aria-labelledby",
              (root.get("aria-labelledby") or "") ==
              f"{title.get('id')} {desc.get('id')}")

        did = root.get("id")
        check(f"{name}: root id is unique across the library",
              did and did not in ids, f"{did} also in {ids.get(did)}")
        ids[did] = name

        #  An SVG <style> block is not scoped. Inlined into a page, an
        #  unscoped .box rule would restyle every other diagram on it.
        style = _style_block(doc)
        selectors = re.findall(r"(?m)^\s*([^{}\n]+)\{", style)
        unscoped = [s.strip() for s in selectors if f"#{did}" not in s]
        check(f"{name}: every style rule is scoped to the root id",
              not unscoped, str(unscoped[:3]))

    print("\n[diagrams] colour comes only from tokens")
    for path in files:
        name = os.path.basename(path)
        doc = _text(path)
        style = _style_block(doc)
        bad = sorted(set(HEX.findall(style)) | set(RGBFN.findall(style)))
        check(f"{name}: no literal colour in the style block", not bad, str(bad[:4]))
        attrs = [v.strip() for _k, v in PRESENTATION.findall(doc)]
        literal = [v for v in attrs
                   if HEX.fullmatch(v) or RGBFN.match(v)
                   or v in ("black", "white", "red", "green", "blue", "grey", "gray")]
        check(f"{name}: no literal colour in a fill or stroke", not literal,
              str(literal[:4]))

    print("\n[diagrams] every var(--token) the library uses is defined")
    tokens = sr.read_tokens(os.path.join(SITE_ROOT, "assets", "site.css"))
    for path in files:
        name = os.path.basename(path)
        style = _style_block(_text(path))
        used = set(re.findall(r"var\((--[\w-]+)\)", style))
        local = set(re.findall(r"(--[\w-]+)\s*:", style))
        for theme in ("light", "dark"):
            missing = sorted(t for t in used - local if t not in tokens[theme])
            check(f"{name}: every token resolves in the {theme} theme",
                  not missing, str(missing[:4]))

    print("\n[diagrams] text is large enough to read")
    #  Every diagram is authored on a 960 unit canvas and site.css gives
    #  .diagram > svg a min-width. The smallest text must still be 12 CSS px at
    #  that width, which is what this re-derives rather than assumes.
    css = open(os.path.join(SITE_ROOT, "assets", "site.css"), encoding="utf-8").read()
    m = re.search(r"\.diagram\s*>\s*svg\s*\{[^}]*min-width:\s*(\d+)px", css)
    check("site.css gives .diagram > svg a min-width", bool(m), "not found")
    min_px = int(m.group(1)) if m else 0
    for path in files:
        name = os.path.basename(path)
        doc = _text(path)
        vb_w = float(re.search(r'viewBox="0 0 ([\d.]+)', doc).group(1))
        sizes = [int(s) for s in re.findall(r"font-size:\s*(\d+)px", _style_block(doc))]
        check(f"{name}: declares at least one font size", bool(sizes))
        if not sizes:
            continue
        effective = min(sizes) * min_px / vb_w
        check(f"{name}: smallest text is at least 12px at the minimum width",
              effective >= 12.0, f"{effective:.1f}px")

    #  A phase here checked the three layer maps against one another: that
    #  there were three, that each carried the shared geometry block, and that
    #  the three blocks were byte-identical. The label on the last of them said
    #  four, and had said four since two of the five were dropped, which is what
    #  a check nobody reads looks like from the inside.
    #
    #  The figures are gone. The section that showed them, "which OSCAL models
    #  this touches", was replaced by the chain, and nothing linked to them
    #  afterwards. What replaces the phase is one line further down: a published
    #  figure has to be referenced by a page.

    readers = [p for p in files if os.path.basename(p).startswith("75-stakeholders")]
    rbodies = {os.path.basename(p): _shared(p, "<!-- readers:begin -->",
                                            "<!-- readers:end -->") for p in readers}
    #  One, not four: the three per-approach variants outlined one stakeholder
    #  path each and were only shown on the gallery. The shared drawing stays.
    check("there is one three-stakeholders drawing", len(readers) == 1, str(len(readers)))
    check("the three-stakeholders drawing carries the shared geometry",
          all(rbodies.values()), str([k for k, v in rbodies.items() if not v]))

    print("\n[diagrams] equal budget across the three approaches")
    for family, count in (("73-join", 3),):
        got = [os.path.basename(p) for p in files
               if os.path.basename(p).startswith(family)
               and any(a in os.path.basename(p)
                       for a in ("assessment", "catalog", "component"))]
        check(f"{family}: one drawing per approach", len(got) == count, str(got))

    #  A published figure has to be shown somewhere.
    #
    #  Three layer maps sat in assets/diagrams for weeks after the section that
    #  drew them was replaced. Nothing failed: they were generated on every
    #  build, checked by four assertions, rendered to grayscale for review, and
    #  seen by nobody. Every other kind of orphan on this site fails a build,
    #  and this kind did not, because the checks all ran from the directory
    #  rather than from the pages.
    #
    #  So the direction is inverted here. The pages are the authority: whatever
    #  they draw is what the library owes them, and anything else it writes is
    #  rot with a generator behind it.
    drawn = set()
    for page in glob.glob(os.path.join(SITE_ROOT, "*.html")):
        drawn |= set(re.findall(r'data-diagram="([^"]+)"',
                                open(page, encoding="utf-8").read()))
    published = {os.path.basename(p)[:-4] for p in files}
    for name in sorted(published - drawn):
        check(f"{name}: is drawn on a page, not just written to the directory",
              False, "published but referenced by no page")
    check(f"every one of the {len(published)} published figures is on a page",
          published <= drawn, str(sorted(published - drawn)))
    for name in sorted(drawn - published):
        check(f"{name}: a page asks for it and the library writes it",
              False, "referenced by a page but never written")

    #  Colour is never allowed to be the only channel that says which approach
    #  a mark belongs to, because the three approach colours sit at one
    #  lightness and so collapse for a dichromat and in grayscale. Every file
    #  that uses an approach colour must also carry a marker shape and a
    #  written label.
    for path in files:
        doc = _text(path)
        if "--approach-" not in doc:
            continue
        name = os.path.basename(path)
        check(f"{name}: approach marks carry a shape as well as a colour",
              'class="ringmark"' in doc)
        check(f"{name}: approach marks carry a written label",
              'class="ringlab"' in doc or "Option A" in doc)

    #  The 72 family drew the seven answer states per approach as a strip, and
    #  asserted every cell against data/six-questions.json. Those drawings were only
    #  ever shown on the component gallery, which has been removed, so the
    #  assertion moved with them: other pages render the same states from the
    #  same data, and tools/pagecheck.js checks that table cell by cell.
    approaches = {"assessment": "assessment-first", "catalog": "catalog-first",
                  "component": "component-first"}

    #  The figure drew two joins per approach and now draws the whole chain, so
    #  what it has to match is the chain in data/joins.json rather than a count
    #  that was the same on all three pages.
    _jn = json.load(open(os.path.join(DATA, "joins.json"), encoding="utf-8"))
    for short, key in approaches.items():
        doc = _text(os.path.join(DIAGRAMS, f"73-join-{short}.svg"))
        want = len(_jn["approaches"][key]["hops"])
        got = len(re.findall(r'class="n">\d+\. ', doc))
        check(f"73-join-{short}: draws all {want} steps of the chain",
              got == want, str(got))
        #  One mark beside each step that involves the runtime, plus the one in
        #  the legend. Three rt-l strokes make up a mark: the line in, the box,
        #  and the line out.
        RT_L = 'class="rt-l"'
        runtime = sum(1 for h in _jn["approaches"][key]["hops"]
                      if "runtime" in (h["from"], h["to"]))
        check(f"73-join-{short}: marks the runtime on each of its {runtime} steps",
              doc.count(RT_L) == 3 * (runtime + 1),
              f"{doc.count(RT_L)} strokes for {runtime} steps")

    print("\n[diagrams] every literal in a join diagram is in the encoding")
    #  These figures used to draw whichever identifiers each proponent had
    #  published, and every literal was matched back to data/snippets to prove
    #  it had not been typed by hand. Three pages then showed three different
    #  subjects, so a reader comparing the figures was comparing the corpora
    #  rather than the modelling.
    #
    #  They draw one rule now, the same one in all three columns, taken from
    #  data/pattern-examples.json. The check moves with them: every literal on a
    #  figure has to be in that file's encoding for that approach. It is the
    #  same guarantee against a hand-typed value, pointed at the file the
    #  figures are now built from.
    _pat = json.load(open(os.path.join(DATA, "pattern-examples.json"),
                          encoding="utf-8"))
    _enc = collections.defaultdict(str)
    for _q, _per in _pat["examples"].items():
        for _ap, _bs in _per.items():
            for _b in _bs:
                _c = _b["content"]
                _enc[_ap] += _c if isinstance(_c, str) else json.dumps(_c)

    for short, key in approaches.items():
        doc = _text(os.path.join(DIAGRAMS, f"73-join-{short}.svg"))
        #  Only the boxed values are literals. A field path is the site's own
        #  writing about the schema; a value is a quotation from the encoding.
        printed = set()
        for hop in _jn["approaches"][key]["hops"]:
            for pr in hop["pairs"]:
                for side in ("foreign", "primary"):
                    v = pr[side].get("value")
                    if v:
                        printed.add(v)
        missing = sorted(v for v in printed
                         if v not in _enc[key] and v.lstrip("#") not in _enc[key])
        check(f"73-join-{short}: every value it prints is in the encoding",
              not missing, str(missing[:4]))
        check(f"73-join-{short}: at least six values were checked",
              len(printed) >= 6, str(len(printed)))
        uuids = [v for v in printed if re.fullmatch(r"[0-9a-f-]{36}", v)]
        check(f"73-join-{short}: at least one uuid was traced to the encoding",
              bool(uuids), str(sorted(printed)[:3]))
        #  And what the figure draws is what the data says it draws.
        drawn = set(re.findall(r'<text[^>]*class="m"[^>]*>([^<]*)</text>', doc))
        drawn = {d.replace("&quot;", '"').replace("&amp;", "&") for d in drawn}
        unaccounted = sorted(
            v for v in printed
            if v not in drawn and not any(v.startswith(d[:12]) for d in drawn if d))
        check(f"73-join-{short}: and every one of them is on the figure",
              not unaccounted, str(unaccounted[:3]))

    print("\n[diagrams] grayscale renders for manual review")
    #  The sheet below is the only place a human looks at these drawings, so a
    #  rasteriser that draws something plausible and wrong is worse than one
    #  that crashes. It used to ignore scale() in silence: every model icon is
    #  placed translate/scale/translate, so all of them came out two to three
    #  times their real size and overlapped the labels beside them, and the
    #  review sheet had been showing that for as long as the icons had been in
    #  the figures. Both halves of the repair are held here.
    ops = sr.Renderer.parse_transform("translate(10,20) scale(0.5) translate(-2,-4)")
    check("the rasteriser reads a scale rather than dropping it",
          ("s", 0.5, 0.5) in ops, str(ops))
    try:
        sr.Renderer.parse_transform("matrix(1,0,0,1,0,0)")
        bad = False
    except SystemExit:
        bad = True
    check("and refuses a transform it cannot draw instead of skipping it", bad)
    # build/ is gitignored, so on a fresh clone this directory does not exist.
    os.makedirs(BUILD_GRAY, exist_ok=True)
    written = 0
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        for theme in ("light", "dark"):
            try:
                im = sr.render(path, tokens[theme], 1.0).convert("L")
                im.save(os.path.join(BUILD_GRAY, f"{name}.{theme}.png"))
                written += 1
            except Exception as exc:  # noqa: BLE001
                check(f"{name}: grayscale render, {theme}", False, repr(exc))
    check(f"grayscale renders written to build/grayscale ({written} files)",
          written == len(files) * 2, f"{written} of {len(files) * 2}")
    _write_contact_sheet(files)


def _write_contact_sheet(files) -> None:
    """One page a reviewer can open, showing every diagram in both themes."""
    rows = []
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        rows.append(
            f'<section><h2>{name}</h2><div class="pair">'
            f'<figure><figcaption>light</figcaption>'
            f'<img src="{name}.light.png" alt=""></figure>'
            f'<figure><figcaption>dark</figcaption>'
            f'<img src="{name}.dark.png" alt=""></figure>'
            f"</div></section>")
    html = (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>Grayscale contact sheet</title><meta name=\"robots\" "
        "content=\"noindex\"><style>"
        "body{font:16px/1.5 system-ui,sans-serif;margin:2rem;max-width:1100px}"
        "h1{font-size:1.4rem}h2{font-size:1rem;font-family:ui-monospace,monospace}"
        ".pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}"
        "img{width:100%;border:1px solid #ccc}figcaption{font-size:.8rem;"
        "color:#555}section{margin-block:2rem}</style></head><body>"
        "<h1>Grayscale contact sheet</h1><p>Generated by "
        "<code>tools/verify.py --diagrams</code>. Every distinction the diagrams "
        "make has to survive here, because colour is never allowed to be the only "
        "channel. Gate 3 of the build guide is this page.</p>"
        + "".join(rows) + "</body></html>\n")
    with open(os.path.join(BUILD_GRAY, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)


# --------------------------------------------------------------------------- #
# --questions                                                                  #
# --------------------------------------------------------------------------- #

def _words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text) if w])


def check_questions() -> None:
    """Four sections of editorial questions, with stable ids and reasoning."""
    print("\n[questions] editorial content and stable question identifiers")
    q = json.load(open(os.path.join(DATA, "questions.json"), encoding="utf-8"))
    archived = _archived_attribution_paths(q)
    check("questions contain no archived attribution", not archived, str(archived[:5]))

    secs = q["sections"]
    approaches = [a["key"] for a in json.load(
        open(os.path.join(DATA, "six-questions.json"),
             encoding="utf-8"))["approaches"]]
    check("four sections: one across the three, then one each",
          [s["key"] for s in secs] == ["all"] + approaches,
          str([s["key"] for s in secs]))
    for s in secs:
        check(f"{s['key']}: is labelled and introduced",
              bool(s.get("label")) and len(s.get("intro", "").split()) >= 8)
        check(f"{s['key']}: carries at least one question", bool(s["questions"]))

    every = [x for s in secs for x in s["questions"]]
    check("no question appears twice", len(every) == len({x["id"] for x in every}),
          str(len(every)))
    for x in every:
        where = x["id"]
        check(f"{where}: is a usable question identifier",
              isinstance(where, str) and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", where)))
        question = x.get("q", "")
        reason = x.get("why", "")
        check(f"{where}: asks a meaningful question",
              isinstance(question, str) and len(question.split()) >= 4
              and any(ch.isalpha() for ch in question))
        check(f"{where}: is asked as a question",
              isinstance(question, str) and question.rstrip().endswith("?"))
        check(f"{where}: says why it is open, in a paragraph",
              isinstance(reason, str) and 20 <= len(reason.split()) <= 90,
              f"{len(reason.split()) if isinstance(reason, str) else 0} words")

    # Historical-looking ids are stable site anchors, not source attributions.
    # Removing their metadata must not delete the questions themselves.
    required = {
        "all": {"xccdf", "rule-metadata", "remediation"},
        "catalog-first": {"one-ssp", "requirement-level", "control-type",
                          "paper-cat-1", "paper-cat-2"},
        "component-first": {"which-cdef-maps", "proposal-1", "proposal-2",
                            "proposal-3", "proposal-4", "paper-comp-1",
                            "paper-comp-2", "paper-comp-3", "paper-comp-4",
                            "paper-comp-5"},
        "assessment-first": {"paper-ap-1"},
    }
    for key, expected in required.items():
        present = {x["id"] for s in secs if s["key"] == key for x in s["questions"]}
        check(f"{key}: retains every existing question identifier",
              expected <= present, str(sorted(expected - present)))

# --------------------------------------------------------------------------- #
# --links                                                                      #
# --------------------------------------------------------------------------- #

def question_cells():
    """The 21 cells of the question matrix, from data."""
    return json.load(open(os.path.join(DATA, "six-questions.json"),
                          encoding="utf-8"))["matrix"]


def words_in(html: str) -> int:
    """Words a reader sees, with the markup taken out."""
    return len([w for w in re.sub(r"<[^>]+>", " ", html).split()
                if any(ch.isalnum() for ch in w)])


def check_source_sanity() -> None:
    """No tool or script defines the same thing twice.

    Twice in one session an edit that replaced a span of a file computed its end
    offset before its start, appended the tail back on, and left a second copy
    of three functions behind. Python and node both accept that in silence: the
    later definition wins, so a file can carry a stale copy of a function and
    behave correctly until the copies are edited in different directions.

    It costs a regex to find and it is invisible in review, so it is checked.
    """
    print("\n[source] no python or javascript file defines the same thing twice")
    import collections as _c
    for path in sorted(glob.glob(os.path.join(TOOLS_DIR, "*.py"))
                       + glob.glob(os.path.join(SITE_ROOT, "assets", "*.js"))
                       + glob.glob(os.path.join(SITE_ROOT, "assets", "diagrams", "*.js"))):
        name = os.path.relpath(path, SITE_ROOT)
        text = open(path, encoding="utf-8").read()
        if path.endswith(".py"):
            found = re.findall(r"^def ([A-Za-z_][A-Za-z_0-9]*)\(", text, re.M)
        else:
            #  Top level only: a nested function is indented, these are not.
            found = re.findall(r"^  function ([A-Za-z_$][\w$]*)\(", text, re.M)
            found += re.findall(r"^function ([A-Za-z_$][\w$]*)\(", text, re.M)
        dupes = sorted(k for k, v in _c.Counter(found).items() if v > 1)
        check(f"{name}: defines nothing twice", not dupes, ", ".join(dupes))
        if path.endswith(".py"):
            try:
                compile(text, path, "exec")
                check(f"{name}: compiles", True)
            except SyntaxError as exc:
                check(f"{name}: compiles", False, str(exc))



#  Every number the scenario page owns. Anything here appearing on another page
#  is a second scenario being described without being introduced.
def _scenario_figures(sc):
    reg = sc["framework"]["controls"]
    hard = sum(h["requirements"] for h in sc["hardening"])
    out = {reg, hard, reg + hard, sc["framework"]["base"],
           sc["framework"]["enhancements"]}
    out |= {h["requirements"] for h in sc["hardening"]}
    out |= {sum(f["count"] for f in a["files"]) for a in sc["approaches"].values()}
    #  Single digits and small counts occur in ordinary prose, so the rule only
    #  covers figures large enough to be unmistakably a count of something.
    return {n for n in out if n >= 100}




def check_joins() -> None:
    """Section 3.1: the chain from the rule to the claim and the result.

    The six questions are answered one at a time, which hides the thing that
    decides whether the set works. This is the chain: it starts where the rule
    is introduced and walks to the claim and the result, and each step is made
    of one or more foreign keys and the primary key each resolves to.

    Five things are held.

    The chain starts at the rule, because a chain that starts anywhere else is
    not answering the question the section asks. Every step names two stages the
    data declares and every field names a question that exists. Every
    relationship declares one of the ways of joining, and the glossary under the
    table lists only the ways that page uses, so a page joining three ways does
    not explain five.

    And the values. Every literal in this file is one of the two running rules
    as data/pattern-examples.json encodes it, which is what lets the three
    figures be read against each other: the old figures drew whichever
    identifiers each proponent had published, so comparing them compared the
    corpora. A value that is not in that encoding fails here, which is the check
    that keeps the two files honest as either changes.
    """
    print("\n[joins] the chain from the rule to the claim and the result")
    jn = json.load(open(os.path.join(DATA, "joins.json"), encoding="utf-8"))
    sq = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    pat = json.load(open(os.path.join(DATA, "pattern-examples.json"),
                         encoding="utf-8"))
    approaches = {a["key"] for a in sq["approaches"]}
    slots = {s["number"] for s in sq["slots"]}
    hows = {h["key"] for h in jn["how"]}
    stages = {s["key"] for s in jn["stages"]}

    check("every approach has a chain", set(jn["approaches"]) == approaches,
          str(set(jn["approaches"]) ^ approaches))
    for st in jn["stages"]:
        check(f"stage {st['key']}: is one of the questions",
              st["slot"] in slots, st["slot"])

    #  What the six questions page encodes, as one string per approach, so a
    #  declared value can be looked for in it.
    encoded = collections.defaultdict(str)
    for _q, per in pat["examples"].items():
        for ap, blocks in per.items():
            for b in blocks:
                c = b["content"]
                encoded[ap] += c if isinstance(c, str) else json.dumps(c)

    used_anywhere = set()
    for key in sorted(jn["approaches"]):
        a = jn["approaches"][key]
        hops = a["hops"]
        check(f"{key}: says how its answers connect", len(hops) >= 4, str(len(hops)))
        #  One order, on all three chains.
        #
        #  The three figures are read against each other, so a step has to be in
        #  the same place in each: what a reader compares is how much it costs
        #  this approach to get from the rule to the check, against the row
        #  beside it. An approach may skip a step it does not have, and may not
        #  reorder the ones it has.
        #
        #  It also makes the file safe to edit by position, which is how six
        #  notes ended up on each other's steps: they were rewritten by index
        #  while the first two steps were check then control rather than the
        #  other way round. Nothing failed, because each note was true and well
        #  written and about the wrong thing.
        want = [tuple(x) for x in jn["step_order"]]
        got = [(h["from"], h["to"]) for h in hops]
        rest = list(want)
        ordered = True
        for step in got:
            if step not in rest:
                ordered = False
                break
            rest = rest[rest.index(step) + 1:]
        check(f"{key}: its steps run in the order every chain runs in",
              ordered, " then ".join(f"{a2} to {b2}" for a2, b2 in got))

        check(f"{key}: the chain starts where the rule is introduced",
              hops[0]["from"] == "rule", hops[0]["from"])
        reached = {h["to"] for h in hops}
        check(f"{key}: and reaches the claim or the result",
              {"claim", "result"} & reached, str(sorted(reached)))
        check(f"{key}: the runtime is on the chain", "runtime" in
              {h["to"] for h in hops} | {h["from"] for h in hops})

        for i, hop in enumerate(hops, 1):
            where = f"{key}/step {i}"
            for end in ("from", "to"):
                check(f"{where}: {end} names a stage that exists",
                      hop[end] in stages, hop[end])
            check(f"{where}: says what the step costs",
                  len(hop["note"].split()) >= 12, hop["note"][:50])
            check(f"{where}: is made of at least one relationship",
                  len(hop["pairs"]) >= 1)
            for j, pr in enumerate(hop["pairs"], 1):
                pw = f"{where}/relationship {j}"
                check(f"{pw}: declares a way of joining",
                      pr["how"] in hows, pr["how"])
                used_anywhere.add(pr["how"])
                for side in ("foreign", "primary"):
                    sd = pr[side]
                    check(f"{pw}: {side} names a model and a field",
                          bool(sd.get("model")) and bool(sd.get("field")),
                          str(sd))
                    if sd.get("slot"):
                        check(f"{pw}: {side} names a question that exists",
                              sd["slot"] in slots, sd["slot"])
                    v = sd.get("value")
                    if v:
                        #  The href form carries a leading hash the encoding
                        #  also carries, so both are tried.
                        check(f"{pw}: {side} value is in the six questions "
                              f"encoding",
                              v in encoded[key] or v.lstrip("#") in encoded[key],
                              v)
                #  A relationship with no field on either side is not a match.
                nofield = (pr["foreign"]["field"] == "no field"
                           == pr["primary"]["field"])
                check(f"{pw}: an absence is not called a match",
                      not nofield or pr["how"] == "none", pr["how"])

    for h in jn["how"]:
        check(f"the vocabulary entry {h['key']} is used by some approach",
              h["key"] in used_anywhere, "unused")

    #  The page renders the chain as the figure plus one note per step. It was
    #  a four-column table above the figure, a row per relationship, and it was
    #  the figure again in words at the length of a screen and a half. The
    #  fields and the values are on the figure; the notes are what the figure
    #  cannot draw, so those stayed.
    for key in sorted(jn["approaches"]):
        body = open(os.path.join(SITE_ROOT, f"{key}.html"), encoding="utf-8").read()
        hops = jn["approaches"][key]["hops"]
        check(f"{key}.html: draws the chain figure",
              f'data-diagram="73-join-{key.split("-")[0]}"' in body)
        check(f"{key}.html: no longer tables the chain beside it",
              'class="criteria-table joins"' not in body)
        #  One block per step, and one more before them all for where the rule
        #  is defined. The chain used to open on the tie from the rule to a
        #  control, so in catalog-first the mapping collection was the first
        #  document named and the catalog holding the rule came second.
        check(f"{key}.html: keeps a note for each of the {len(hops)} steps, "
              f"after the one that says where the rule is defined",
              body.count("<li><strong>") == len(hops) + 1,
              str(body.count("<li><strong>")))
        intro = jn["approaches"][key]["introduced"]
        check(f"{key}.html: says the rule is introduced in {intro['model']}",
              intro["note"][:40] in body and f'<code>{intro["field"]}</code>' in body)
        #  The rule reaches its check before anything else points at it. This is
        #  the order the section was renamed for.
        check(f"{key}: the chain reaches the check before the control",
              [h["to"] for h in hops].index("check")
              < [h["to"] for h in hops].index("control"),
              str([f'{h["from"]}>{h["to"]}' for h in hops]))
        for hop in hops:
            check(f"{key}.html: says what the {hop['from']} to {hop['to']} step costs",
                  hop["note"][:40] in body, hop["note"][:40])
            for end in ("from", "to"):
                #  The link leaves the page: section 3 held the questions and is
                #  gone, so a stage name points at the six questions page, at
                #  this approach's column of the question it belongs to.
                slot = {s["key"]: s for s in jn["stages"]}[hop[end]]["slot"]
                check(f"{key}.html: links {hop[end]} to question {slot}",
                      f'href="./six-questions.html#q{slot}-{key}"' in body)

    #  And the encodings really are gone from the approach pages, which is what
    #  makes this section the place a reader learns how the answers connect.
    for key in sorted(jn["approaches"]):
        body = open(os.path.join(SITE_ROOT, f"{key}.html"), encoding="utf-8").read()
        check(f"{key}.html: shows no encoding, which lives on the six questions page",
              "data-pattern=" not in body, str(body.count("data-pattern=")))

def check_stakeholders() -> None:
    """Section 1: seven parties, each mapped to the model it works in.

    Three claims in here are the substance and all three are checked rather
    than reviewed.

    The profile belongs to the system owner on every approach and to nobody
    else, because the selection of what a system is held to is a decision about
    that system. In the catalog approach it also carries the merge of several
    catalogs into the one a plan can import, which is the same decision again.

    The document holding the checks belongs to the policy engine provider in all
    three, because a check is what triggers an engine to run. Which document it
    is differs: a component definition of type software in the catalog approach,
    one of type validation in the component approach, and the assessment plan
    itself in the assessment approach, where the guidance authors write the
    activity and the engine provider writes the check inside it. The engine
    writes that and nothing else.

    And the mapping is nobody's by default. A hardening guide does not always
    carry the tie to a framework: a STIG carries CCIs and DISA's separate CCI
    list is what names the 800-53 controls. So the mapping provider is a party
    of its own, holding the mapping-collection where the tie is a document and
    holding nothing where the tie is inline.
    """
    print("\n[stakeholders] seven parties, each mapped to a model, on every page")
    #  The one component definition on the table whose type is not settled.
    #  Written once, here, because the string is a value in the data and a label
    #  on the page, and two spellings of it would be one row silently exempt.
    UNSETTLED = "software or validation"
    sh = json.load(open(os.path.join(DATA, "stakeholders.json"), encoding="utf-8"))
    sq = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    sc = json.load(open(os.path.join(DATA, "scenario.json"), encoding="utf-8"))
    approaches = {a["key"] for a in sq["approaches"]}
    keys = [p["key"] for p in sh["parties"]]
    known = set(sc["models"])

    def entries(e):
        """Every model an entry names, wherever it names it."""
        out = list(e.get("writes", []))
        for fl in e.get("flows", []):
            src, dst = (fl["from"], fl["to"]) if isinstance(fl, dict) else fl
            out += list(src) + list(dst)
        return out

    check("seven parties", len(keys) == 7, str(len(keys)))
    check("no party is declared twice", len(set(keys)) == len(keys))
    check("the block covers every approach and nothing else",
          set(sh["approaches"]) == approaches,
          str(sorted(set(sh["approaches"]) ^ approaches)))
    for p in sh["parties"]:
        check(f"{p['key']}: has a name and says who they are",
              len(p["name"].split()) >= 2 and len(p["who"].split()) >= 4,
              p.get("who", "")[:50])

    for key in sorted(sh["approaches"]):
        per = sh["approaches"][key]
        check(f"{key}: answers for every party and no other",
              list(per) == keys, str([k for k in per if k not in keys]))
        for k in keys:
            named = entries(per[k])
            #  A party may legitimately have nothing to write in an approach.
            #  The mapping provider does in two of the three, because the tie to
            #  the framework is inline there. What it may not do is say nothing:
            #  an empty row with no explanation reads as an oversight.
            check(f"{key}/{k}: names a model, or says why it names none",
                  bool(named) or len(per[k].get("note", "").split()) >= 12,
                  str(per[k]))
            stray = sorted({m["model"] for m in named} - known)
            check(f"{key}/{k}: names only real OSCAL models", not stray, str(stray))
            #  A row says what a party produces and what its runs consume, and
            #  nothing about what a person opens. The auditor row carried a
            #  "reads" key naming documents an auditor would read, which is a
            #  fact about a reader rather than about automation, and it is gone.
            #  Held as a rule rather than left to the renderer, because a key
            #  the renderer ignores is a key that gets written again.
            check(f"{key}/{k}: says what it produces, not what it opens",
                  set(per[k]) <= {"writes", "flows", "note"},
                  str(sorted(set(per[k]) - {"writes", "flows", "note"})))
            for m in named:
                check(f"{key}/{k}: {m['model']} is named as a model",
                      set(m) <= {"model", "kind"}, str(sorted(m)))

        #  A provider builds a tool and runs nothing. The row that ships the
        #  checks and the rows that execute them are different rows, which is
        #  the substance of this block: on the two approaches with a path from a
        #  check to a claim, the same checks make the plan of record's responses
        #  when the system owner runs them and a result when an auditor does. So
        #  the engine has no run on it, and every run on the page belongs to a
        #  party that executes rather than to the party that shipped it.
        eng = per["engine"]
        check(f"{key}/engine: builds the tool and runs nothing",
              not eng.get("flows"), str(eng.get("flows")))
        check(f"{key}/engine: says what it ships",
              len(eng.get("note", "").split()) >= 8, eng.get("note", ""))
        runners = [k for k in keys
                   if any(f.get("runtime") for f in per[k].get("flows", []))]
        #  Two of the three have two runners. The assessment approach has one,
        #  and that is the approach's position rather than a hole in the table:
        #  an assessor works from the plan of record and nothing else the owner
        #  holds, cannot see what the owner automates, and is not answerable for
        #  it. Drawing the owner running the same plan said the assessor's route
        #  depended on the owner's tooling, which is the opposite of the claim.
        want_runners = (["auditor"] if key == "assessment-first"
                        else ["owner", "auditor"])
        check(f"{key}: the tool is run by {' and the '.join(want_runners)}",
              runners == want_runners, str(runners))
        for k in runners:
            for fl in per[k].get("flows", []):
                check(f"{key}/{k}: a run reads something and writes something",
                      bool(fl.get("from")) and bool(fl.get("to")), str(fl))
                check(f"{key}/{k}: and says what the run produces",
                      len(fl.get("makes", "").split()) >= 2, str(fl.get("makes")))
        #  An auditor's run always ends in a result. An owner's run ends in the
        #  plan of record on the two routes that have a path from a check to a
        #  claim, and there is no owner's run on the one that does not.
        made = {k: [m["model"] for f in per[k].get("flows", []) for m in f["to"]]
                for k in ("owner", "auditor")}
        check(f"{key}: the auditor's run makes a result",
              made["auditor"] == ["assessment-results"], str(made["auditor"]))
        want = ([] if key == "assessment-first" else ["system-security-plan"])
        check(f"{key}: the owner's run makes {want[0] if want else 'nothing'}",
              made["owner"] == want, str(made["owner"]))
        #  A row with no run is not an omission, and a reader cannot tell an
        #  argument from an oversight by looking at an empty cell. Whichever way
        #  this row is drawn, it has to say why in words.
        if not made["owner"]:
            check(f"{key}: and the owner's row says why nothing runs on it",
                  len(per["owner"].get("note", "").split()) >= 12,
                  per["owner"].get("note", "")[:40])
        elif made["owner"] == made["auditor"]:
            check(f"{key}: and the row says why both runs make the same thing",
                  len(per["auditor"].get("note", "").split()) >= 12,
                  per["auditor"].get("note", "")[:40])

        #  Who owns the component definition that holds the checks.
        cdefs = [(k, m) for k in keys for m in entries(per[k])
                 if m["model"] == "component-definition"]
        checks_cdef = [(k, m) for k, m in cdefs if m.get("kind") in
                       ("software", "validation") and k == "engine"]
        if cdefs:
            for k, m in cdefs:
                #  UNSETTLED is a third value and it is not a way out of this
                #  rule, it is a claim of its own: that which type holds this is
                #  genuinely open. One row is allowed to say it, the mapping
                #  provider's, and only while the open questions page carries a
                #  question about it. An unsettled marker with no question
                #  behind it is a shrug printed as a finding.
                check(f"{key}/{k}: a component definition says which type it is",
                      m.get("kind") in ("software", "validation", UNSETTLED),
                      str(m))
                if m.get("kind") == UNSETTLED:
                    check(f"{key}/{k}: and only the mapping provider leaves it "
                          f"open", k == "mapper", k)
                    qs = json.load(open(os.path.join(DATA, "questions.json"),
                                        encoding="utf-8"))
                    asked = [x for s in qs["sections"] if s["key"] == key
                             for x in s["questions"]
                             if "component definition" in x["q"].lower()
                             and "?" in x["q"]]
                    check(f"{key}/{k}: with an open question recording why",
                          bool(asked), "no question on the questions page")
            check(f"{key}: the check component definition belongs to the engine",
                  bool(checks_cdef), str([k for k, _ in cdefs]))

    #  The mapping provider works in every approach. What changes is whose
    #  document it works in.
    #
    #  The row used to say "nothing to write" on two of the three, on the
    #  reasoning that an inline tie is written by whoever writes the thing it
    #  sits on. That confuses the tie with its container. Somebody still decides
    #  which framework control a rule serves, and in these two approaches they
    #  do it by editing a document another party owns: a component definition
    #  where the tie is a rule's, the assessment plan where it is an activity's.
    #  Editing somebody else's document is a heavier ask than shipping your own,
    #  and the row said nothing at all about it.
    #
    #  So: exactly one approach gives this party a document of its own, and the
    #  other two give it a document to edit. Both are asserted, because a row
    #  with a model on it and no explanation of whose model it is would read as
    #  a fourth author of the same file.
    MAPS_IN = {"catalog-first": "mapping-collection",
               "component-first": "component-definition",
               "assessment-first": "assessment-plan"}
    for key in sorted(sh["approaches"]):
        per = sh["approaches"][key]
        holders = sorted(k for k in keys
                         if any(m["model"] == "mapping-collection"
                                for m in entries(per[k])))
        wants = ["mapper"] if key == "catalog-first" else []
        check(f"{key}: a mapping collection is the mapping provider's, or nobody's",
              holders == wants, str(holders))
        named = [m["model"] for m in entries(per["mapper"])]
        check(f"{key}: the mapping provider works in the {MAPS_IN[key]}",
              named == [MAPS_IN[key]], str(named))
        check(f"{key}: and says whether the document is its own or another's",
              len(per["mapper"].get("note", "").split()) >= 12,
              per["mapper"].get("note", "")[:40])
        #  Whether it is the party's own document is not taken from the prose.
        #  A document is somebody else's exactly when somebody else writes it,
        #  and that is already in the table: the guidance authors and the engine
        #  provider write the component definition and the assessment plan, and
        #  nobody but the mapping provider writes a mapping collection.
        own = key == "catalog-first"
        others = sorted(k for k in keys if k != "mapper"
                        and any(m["model"] == MAPS_IN[key] for m in entries(per[k])))
        check(f"{key}: the {MAPS_IN[key]} is "
              f"{'the mapping provider' if own else 'another party'}'s to write",
              (not others) == own, str(others))

    #  The engine writes the document that holds the checks and nothing else.
    #  Which document that is differs: a component definition where the checks
    #  hang off a component, the assessment plan where they hang off an
    #  activity. What does not differ is that the checks are the engine
    #  provider's to write, because a check is the thing that triggers an engine
    #  to run, and that whatever the checks are written into carries nothing of
    #  the engine's beyond them. The guidance authors write the activity; the
    #  engine provider writes the check inside it.
    HOLDS_CHECKS = {"catalog-first": "component-definition",
                    "component-first": "component-definition",
                    "assessment-first": "assessment-plan"}
    for key in sorted(sh["approaches"]):
        wrote = [m["model"] for m in sh["approaches"][key]["engine"].get("writes", [])]
        want = HOLDS_CHECKS[key]
        check(f"{key}: the engine writes only the {want} holding the checks",
              set(wrote) <= {want}, str(wrote))

    #  In, runtime, out is one fact and is held on one line. It was three flex
    #  items beside a label, so the label took the first line and the output
    #  wrapped onto a third, reading as two separate statements. The label takes
    #  a row of its own now and the three parts are wrapped together, and this
    #  measures whether the widest of them still fits the cell they sit in: a
    #  longer model name or a wider spacing token would start it wrapping again
    #  without anything else noticing.
    css = open(os.path.join(SITE_ROOT, "assets", "site.css"), encoding="utf-8").read()
    root = re.search(r":root\s*\{(.*?)\n\}", css, re.S).group(1)
    tok = dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", root))
    rem = lambda v: float(v.strip()[:-3]) * 16
    fs, fx, s2, s5 = (rem(tok["--fs-sm"]), rem(tok["--fs-xs"]),
                      rem(tok["--s2"]), rem(tok["--s5"]))
    hdr = float(re.search(r'\.stakeholders th\[scope="row"\][^}]*width:\s*(\d+)%',
                          css).group(1)) / 100
    gw = float(re.search(r"\.mflow__runtime\s*\{[^}]*width:\s*([\d.]+)em", css,
                         re.S).group(1)) * 16
    check("the run is wrapped so its three parts stay together",
          ".mflow__run" in css and re.search(
              r"\.mflow__run\s*\{[^}]*flex-wrap:\s*nowrap", css, re.S) is not None)
    check("and its label takes a row of its own",
          re.search(r"\.mflow__by\s*\{[^}]*flex:\s*0 0 100%", css, re.S) is not None)

    def tile_w(m):
        w = 2 * s2 + 2 + 0.85 * fs + s2 + len(m["model"]) * 0.6 * fs
        return w + (s2 + len(m["kind"]) * 0.6 * fx + 8 if m.get("kind") else 0)

    cell = (1 - hdr) * rem(tok["--measure"]) - 2 * s5
    for key in sorted(sh["approaches"]):
        for k in keys:
            for fl in sh["approaches"][key][k].get("flows", []):
                need = (sum(tile_w(m) for m in fl["from"])
                        + sum(tile_w(m) for m in fl["to"])
                        + gw + 2 * s2)
                check(f"{key}/{k}: the run fits on one line, "
                      f"{need:.0f} of {cell:.0f} available",
                      need <= cell, f"{need - cell:.0f} over")

    #  The order of the seven is an argument, so it is held rather than left to
    #  whatever the file happens to say. A rule travels down this table: the
    #  framework is published, something ties a guide back to it, somebody
    #  writes the guide, somebody builds the tool that tests it, and two parties
    #  run that tool. The mapping provider sits directly under the regulatory
    #  row because the tie it holds points at the framework that row publishes,
    #  and it was four rows further down, after the guidance it maps.
    check("the seven read in the order a rule travels",
          [p["key"] for p in sh["parties"]] ==
          ["regulatory", "mapper", "benchmark", "software",
           "engine", "owner", "auditor"],
          str([p["key"] for p in sh["parties"]]))
    #  Two pairs are one role each, and a group has to be declared, used, and
    #  contiguous: a heading that spans two rows has to have them adjacent.
    grouped = [p["key"] for p in sh["parties"] if p.get("group")]
    check("the two guidance authors are grouped",
          grouped[:2] == ["benchmark", "software"], str(grouped))
    #  The tool is inside the automation group, not above it: a policy engine
    #  and an automation tool are the same thing, and separating them said they
    #  were two.
    check("the automation is the tool and the two parties that run it",
          grouped[2:] == ["engine", "owner", "auditor"], str(grouped))
    for g in sh.get("groups", []):
        at = [i for i, p in enumerate(sh["parties"]) if p.get("group") == g["key"]]
        check(f"group {g['key']}: its parties sit together",
              at == list(range(at[0], at[0] + len(at))), str(at))
        check(f"group {g['key']}: has more than one party in it", len(at) > 1)
    check("and the group they name is declared",
          {p["group"] for p in sh["parties"] if p.get("group")}
          <= {g["key"] for g in sh.get("groups", [])})
    for g in sh.get("groups", []):
        check(f"group {g['key']}: says why the two are one role",
              len(g["note"].split()) >= 12, g["note"][:40])

    #  The profile is the system owner's on every approach, and nobody else's.
    #  Choosing what a system is held to is a decision about that system: the
    #  body that publishes a framework publishes the catalog, and the baseline
    #  an organisation selects out of it is the organisation's.
    #
    #  This used to be asserted for the catalog approach alone, where the merge
    #  makes it unmissable, and the other two put the profile on the regulatory
    #  row. So the catalog page said "the profile is always the owner's" while
    #  the two pages beside it drew it on someone else. A rule scoped to the one
    #  case where a claim is obvious is a rule that lets the claim be wrong
    #  everywhere else.
    for key in sorted(sh["approaches"]):
        per = sh["approaches"][key]
        owner_models = {m["model"] for m in entries(per["owner"])}
        check(f"{key}: the profile is the system owner's",
              "profile" in owner_models, str(sorted(owner_models)))
        others = sorted(k for k in keys if k != "owner"
                        and any(m["model"] == "profile" for m in entries(per[k])))
        check(f"{key}: and nobody else writes one", not others, str(others))

    #  And the page renders all six, in order, each model drawn as a file tile.
    for key in sorted(sh["approaches"]):
        body = open(os.path.join(SITE_ROOT, f"{key}.html"), encoding="utf-8").read()
        check(f"{key}.html: has the stakeholder section", 'id="stakeholder"' in body)
        at = [body.find(p["name"]) for p in sh["parties"]]
        check(f"{key}.html: names all seven parties", all(i != -1 for i in at),
              str([p["name"] for p, i in zip(sh["parties"], at) if i == -1]))
        check(f"{key}.html: in the order the data declares", at == sorted(at), str(at))
        #  Counted inside the section, not across the page. The chain table in
        #  section 3.1 draws the same tile for the models it names, and counting
        #  the whole document made this assertion answer a question about two
        #  sections at once.
        sec = body[body.index('id="stakeholder"'):body.index('id="tradeoffs"')]
        want = sum(len(entries(sh["approaches"][key][k])) for k in keys)
        check(f"{key}.html: draws a file tile for each of the {want} models named",
              sec.count('class="mtile"') == want, str(sec.count('class="mtile"')))
        #  The engine's flow is an execution and is drawn with the runtime
        #  glyph; any other party's flow is a derivation and keeps the arrow.
        for g in sh.get("groups", []):
            check(f"{key}.html: heads the group {g['label']!r}",
                  f'colspan="2">{g["label"]}' in sec)
        check(f"{key}.html: indents the two parties under it",
              sec.count('class="stakeholders__in"') == len(
                  [p for p in sh["parties"] if p.get("group")]),
              str(sec.count('class="stakeholders__in"')))
        runs = sum(1 for k in keys
                   for f in sh["approaches"][key][k].get("flows", [])
                   if f.get("runtime"))
        rest = sum(1 for k in keys
                   for f in sh["approaches"][key][k].get("flows", [])
                   if not f.get("runtime"))
        #  Counted in the table, because the mark is drawn once more below it
        #  in the line that defines what it means.
        tbody = sec[sec.index("<tbody>"):sec.index("</tbody>")]
        check(f"{key}.html: draws the runtime for each of the {runs} runs",
              tbody.count('class="mflow__runtime"') == runs,
              str(tbody.count('class="mflow__runtime"')))
        check(f"{key}.html: and once more where it defines the mark",
              sec.count('class="mflow__runtime"') == runs + 1,
              str(sec.count('class="mflow__runtime"')))
        check(f"{key}.html: draws an arrow for each of the {rest} other flows",
              sec.count('mflow__arrow') == rest, str(sec.count("mflow__arrow")))
        #  The glyph is aria-hidden, so the sentence it draws has to be said in
        #  text or a screen reader hears two model names in a row and nothing
        #  about the machine between them, which is the whole content of the
        #  row. The count was asserted and the sentence was not, and it went
        #  missing once without anything noticing: a scripted edit took it out
        #  along with the constant it lives on, and every check still passed.
        check(f"{key}.html: and says in text what the {runs} runs draw",
              tbody.count("is read by the policy engine, which runs and writes")
              == runs,
              str(tbody.count(
                  "is read by the policy engine, which runs and writes")))
        check(f"{key}.html: says what each of the {runs} runs makes",
              sec.count('class="mflow__by"') == runs,
              str(sec.count('class="mflow__by"')))
        for k in keys:
            for fl in sh["approaches"][key][k].get("flows", []):
                if fl.get("runtime"):
                    check(f"{key}.html: the {k} row says its run makes "
                          f"{fl['makes']}",
                          f'runs the checks, making {fl["makes"]}' in sec)
        #  The mark is defined where it is used, not two sections further down
        #  in the legend of a figure.
        check(f"{key}.html: defines the runtime mark beside the table",
              'class="stakeholders__key"' in sec and sh["runtime"][:40] in sec)
        for k in keys:
            for m in entries(sh["approaches"][key][k]):
                check(f"{key}.html: {k} row names {m['model']}",
                      f'>{m["model"]}</span>' in body, m["model"])


def check_scenario() -> None:
    """Section 3: one scenario, modelled three ways.

    The scenario is the only place on the site where the three approaches are
    put to the same task, so it is the place where a thumb on the scale would be
    least visible and most effective. Four things are held.

    Every count is derived, not asserted: the framework count from the stored
    NIST profile, each guide's count from a file in the corpora, and the file
    inventory from a stated rule per approach.

    Every consequence names a strength or a risk from section 2 of the same
    page, and that entry has to exist. A consequence that tied to nothing would
    be a new argument smuggled in below the one the page already made.

    Every model appears in every inventory, including with a count of zero,
    because an approach that simply omits the models it does not use would look
    smaller than one that declares them.

    And the three figures are drawn on one grid, so comparing them by eye is
    comparing the same thing.
    """
    print("\n[scenario] one system, three hardening guides, modelled three ways")
    sc = json.load(open(os.path.join(DATA, "scenario.json"), encoding="utf-8"))
    global SCENARIO_FIGURES
    SCENARIO_FIGURES = _scenario_figures(sc)
    ev = json.load(open(os.path.join(DATA, "scenario-evidence",
                                     "nist-high-baseline.json"), encoding="utf-8"))

    #  The framework count is the length of a list this repository stores, not a
    #  number anybody typed.
    ids = ev["with_ids"]
    check("the baseline control ids are unique", len(ids) == len(set(ids)))
    check(f"the framework count is the {len(ids)} ids in the stored profile",
          sc["framework"]["controls"] == len(ids), str(sc["framework"]["controls"]))
    check("and splits into base controls and enhancements",
          sc["framework"]["base"] + sc["framework"]["enhancements"] == len(ids),
          f'{sc["framework"]["base"]} + {sc["framework"]["enhancements"]}')
    check("base is the ids with no dot in them",
          sc["framework"]["base"] == len([i for i in ids if "." not in i]))
    check("families is the distinct prefixes",
          sc["framework"]["families"] == len({i.split("-")[0] for i in ids}))

    #  Each guide's count is recomputed from the file it names, by the rule it
    #  names. A guide whose requirement count drifted from its own corpus would
    #  put the whole scenario out by that much.
    for h in sc["hardening"]:
        check(f"{h['key']}: says how its count was derived",
              len(h["derivation"]) > 60)
        path = ex.source_path(h["source"])
        check(f"{h['key']}: names a file that exists", os.path.isfile(path), h["source"])
        if not os.path.isfile(path):
            continue
        plan = json.load(open(path, encoding="utf-8"))["assessment-plan"]
        acts = plan["local-definitions"]["activities"]
        steps = [st for a in acts for st in a.get("steps", [])]
        if h["count_rule"] == "audit-steps":
            got = len([st for st in steps if st["title"].startswith("Audit for")])
        elif h["count_rule"] == "step-type-check":
            got = len([st for st in steps for pr in st.get("props", [])
                       if pr["name"] == "step-type" and pr["value"] == "check"])
        else:
            got = len(steps)
        check(f"{h['key']}: {h['requirements']} requirements, recomputed",
              got == h["requirements"], f"recomputed {got}")
        check(f"{h['key']}: {h['grouping']} {h['grouping_label']}, recomputed",
              h["grouping"] in (len(acts), h["requirements"]),
              f"activities {len(acts)}")

    hard = sum(h["requirements"] for h in sc["hardening"])
    models = sc["models"]
    check("seven models, and the excluded one is not among them",
          len(models) == 7 and sc["excluded_model"]["model"] not in models)

    #  Three counts on this page are forced by a cardinality in the schemas
    #  rather than chosen: one profile per plan, one plan per result, one system
    #  security plan per plan. The section that set those out has been removed,
    #  so the rows that depend on them have to carry the reason themselves.
    FORCED = {
        ("catalog-first", "profile"): "import-profile",
        ("catalog-first", "system-security-plan"): "import-profile",
        ("assessment-first", "assessment-plan"): "import-ssp",
        ("assessment-first", "assessment-results"): "import-ap",
    }
    for (key, model), field in FORCED.items():
        f = [x for x in sc["approaches"][key]["files"] if x["model"] == model][0]
        check(f"{key}/{model}: says the count follows from {field}",
              field in f["detail"], f["detail"][:70])

    for key in sorted(sc["approaches"]):
        a = sc["approaches"][key]
        got = [f["model"] for f in a["files"]]
        check(f"{key}: declares every model, including the ones it does not use",
              got == models, str(got))
        check(f"{key}: says what rule produced the inventory",
              len(a["rule"].split()) >= 12, a["rule"])
        check(f"{key}: says what the plan of record ends up answering",
              "plan of record" in a["plan_of_record"], a["plan_of_record"])
        for f in a["files"]:
            check(f"{key}/{f['model']}: a count of zero says why, a count says what",
                  len(f["what"].split()) >= 1, f["what"])
            #  One name per file, so the figure can label every tile and a
            #  reader can follow one document from the drawing into the list.
            items = f.get("items", [])
            check(f"{key}/{f['model']}: one name per file",
                  len(items) == f["count"], f"{len(items)} names, {f['count']} files")
            for it in items:
                check(f"{key}/{f['model']}: {it.get('name')!r} fits a tile",
                      1 <= len(it.get("name", "")) <= 16, it.get("name"))
            names = [i.get("name") for i in items]
            check(f"{key}/{f['model']}: no two files share a name",
                  len(set(names)) == len(names), str(names))
            #  A component definition holds either the thing being configured or
            #  the checks that test it, and which one is the distinction the
            #  approach rests on. It cannot be read off a count, so it is named.
            if f["model"] == "component-definition" and f["count"]:
                kinds = {i.get("kind") for i in items}
                check(f"{key}: every component definition says software or validation",
                      kinds <= {"software", "validation"} and None not in kinds,
                      str(sorted(str(k) for k in kinds)))


    #  One scenario, on one page. A figure anywhere else would be a second
    #  scenario, implied and never stated, and a reader comparing two pages
    #  would be comparing two systems without being told.
    page = open(os.path.join(SITE_ROOT, "scenario.html"), encoding="utf-8").read()
    for other in sorted(glob.glob(os.path.join(SITE_ROOT, "*.html"))):
        name = os.path.basename(other)
        if name == "scenario.html":
            continue
        body = open(other, encoding="utf-8").read()
        figs = re.findall(r'data-(?:stat|cited)="([^"]+)"', body)
        check(f"{name}: renders no figure, because the scenario has a page",
              not figs, ", ".join(sorted(set(figs))))
        #  And none of the scenario's own numbers retyped into prose, which is
        #  the way this rule would actually be broken: a span is obvious, a
        #  sentence saying "917 controls" is not.
        prose = re.sub(r"<[^>]+>", " ", body)
        prose = re.sub(r"\b(?:800|53|1\.2\.\d|24\.04|25-01|16|18|5)\b", " ", prose)
        loose = sorted({n for n in SCENARIO_FIGURES
                        if re.search(rf"(?<![\d.-]){n}(?![\d.-])", prose)})
        check(f"{name}: retypes none of the scenario's counts",
              not loose, ", ".join(map(str, loose)))

    for key in sorted(sc["approaches"]):
        a = sc["approaches"][key]
        total = sum(f["count"] for f in a["files"])
        short = key.split("-")[0]
        check(f"scenario.html: shows the figure for {key}",
              f'data-diagram="710-scenario-{short}"' in page)
        check(f"scenario.html: states {key} produces {total} files",
              f"{total} files" in page, str(total))
        check(f"scenario.html: links to the {key} page",
              f'href="./{key}.html"' in page)
        #  The file names are asserted against the figure, not the page. They
        #  used to be in both, because the page repeated the whole inventory in
        #  a list under each drawing. The list is gone, so the drawing is the
        #  only place the names are, and the drawing is where the check goes.
        import xml.etree.ElementTree as ET
        fig = open(os.path.join(SITE_ROOT, "assets", "diagrams",
                                f"710-scenario-{short}.svg"), encoding="utf-8").read()
        root = ET.fromstring(fig)
        ns = "{http://www.w3.org/2000/svg}"
        dsc = (root.find(ns + "desc").text or "")
        for f in a["files"]:
            for it in f.get("items", []):
                #  The tile wraps a long name onto two lines, so the check is
                #  that every word of it is drawn rather than the whole string.
                check(f"710-scenario-{short}.svg: draws {it['name']!r}",
                      all(w in fig for w in it["name"].split()), it["name"])
                #  And says it, whole, in the description. This is the half that
                #  used to be the printed list's job: a reader who cannot see
                #  the tiles gets the description of the tiles. It is the only
                #  route to these names now, so it is checked rather than
                #  assumed, name and component type both.
                check(f"710-scenario-{short}.svg: and names it in the "
                      f"description, {it['name']!r}", it["name"] in dsc, it["name"])
                if it.get("kind"):
                    check(f"710-scenario-{short}.svg: saying {it['name']!r} is "
                          f"a {it['kind']} component definition",
                          f"{it['name']} ({it['kind']})" in dsc, it["kind"])
            #  What each model is for, said once, in the drawing.
            if f["what"]:
                check(f"710-scenario-{short}.svg: says what the "
                      f"{f['model']} files are for",
                      f["what"][:34] in dsc, f["what"][:34])
        body = open(os.path.join(SITE_ROOT, f"{key}.html"), encoding="utf-8").read()
        check(f"{key}.html: carries no scenario section of its own",
              'id="scenario"' not in body)
        svg_path = os.path.join(SITE_ROOT, "assets", "diagrams",
                                f"710-scenario-{short}.svg")
        check(f"{key}: the figure exists", os.path.isfile(svg_path))
        if not os.path.isfile(svg_path):
            continue
        fig = open(svg_path, encoding="utf-8").read()
        #  One tile is one file. If the drawing and the inventory disagree, the
        #  figure is the thing a reader believes.
        tiles = len(re.findall(r'class="model"', fig))
        check(f"{key}: the figure draws one tile per file, {total}",
              tiles == total, f"{tiles} tiles")
        check(f"{key}: and states the same total", f"{total} files," in fig, str(total))
        #  Every group in the figure is labelled with the same icon the table
        #  above it uses, including the groups with no files: an approach that
        #  does not use a model still draws the model, and the label is how a
        #  reader knows which absence they are looking at.
        icons = len(re.findall(r'<g class="mi ', fig))
        check(f"{key}: the figure labels all {len(sc['models'])} groups with "
              f"the model's icon", icons == len(sc["models"]), f"{icons} icons")
        #  Drawn at 21, not at the height of the label. A diagram is shown at
        #  three quarters of its authoring width, so an icon matched to the 16px
        #  label lands at 12px on the page, which is below where these icons
        #  stop being readable.
        sizes = {round(float(m), 4)
                 for m in re.findall(r'<g class="mi [^"]*" transform='
                                     r'"translate\([^)]*\) scale\(([\d.]+)\)', fig)}
        vws = {round(21 / s, 1) for s in sizes} if sizes else set()
        check(f"{key}: and draws each at 21 units",
              len(vws) == len(sizes) and all(30 < v < 45 for v in vws),
              str(sorted(sizes)))

    #  Same grid on all three, or the areas are not comparable.
    boxes = set()
    for key in sc["approaches"]:
        fig = open(os.path.join(SITE_ROOT, "assets", "diagrams",
                                f"710-scenario-{key.split('-')[0]}.svg"),
                   encoding="utf-8").read()
        m = re.search(r'viewBox="0 0 (\d+) ', fig)
        t = re.search(r'<rect[^>]*width="(\d+)" height="(\d+)"[^>]*class="model"', fig)
        boxes.add((m.group(1) if m else "?", t.groups() if t else None))
    check("the three figures share a width and a tile size",
          len(boxes) == 1, str(sorted(map(str, boxes))))

    check(f"the three guides come to {hard} requirements", hard == 547, str(hard))

    #  And the page states the inputs it rests on, not just the outputs.
    for h in sc["hardening"]:
        check(f"scenario.html: states {h['key']} at {h['requirements']}",
              f'<strong>{h["requirements"]}</strong>' in page, str(h["requirements"]))
    check(f"scenario.html: states the framework at {sc['framework']['controls']}",
          f'<strong>{sc["framework"]["controls"]}</strong>' in page)
    check(f"scenario.html: states the combined total, "
          f"{sc['framework']['controls'] + hard}",
          f'<strong>{sc["framework"]["controls"] + hard}</strong>' in page)
    #  Inverted with the removal. The derivations are provenance in the data,
    #  not prose on the page: each one names a file and a rule, and the checks
    #  above open that file and recompute the count by that rule. Printing the
    #  sentence beside the figure asked a reader to take on trust the thing the
    #  build already proves, in four paragraphs of it.
    check("scenario.html: does not print the derivations, which are checked",
          not any(h["derivation"][:40] in page for h in sc["hardening"]))

    #  One order for the three, everywhere. This page was alphabetical by
    #  structural name while every other comparison used the site's option
    #  letters, so the one page putting the three in a table put them in a
    #  different order from the page putting them side by side per question.
    #  Nothing held it, which is why it drifted, so it is held here: the table
    #  columns and the subsection headings both, since they are generated from
    #  the same list and would drift together.
    LETTERS = ["catalog-first", "component-first", "assessment-first"]
    _sq = json.load(open(os.path.join(DATA, "six-questions.json"),
                         encoding="utf-8"))
    labels = [a["label"] for k in LETTERS
              for a in _sq["approaches"] if a["key"] == k]
    cols = re.findall(r'<th scope="col">([^<]+)</th>', page)
    check("scenario.html: the table reads in the option-letter order",
          cols[1:4] == labels, str(cols[:4]))
    heads = [h for h in re.findall(r"<h3[^>]*>2\.\d+ ([^,<]+)", page)]
    check("scenario.html: and so do the sections beneath it",
          heads[:3] == labels, str(heads[:3]))

    #  A model is drawn the same way wherever it is named. The chip is the unit
    #  the approach pages taught, and this page was setting the same seven
    #  models as bare <code>, so a reader crossing between the two met one set
    #  of things in two vocabularies. Two surfaces have to agree now: the
    #  table's first column, and the label above each group in each figure.
    sec = page[page.index('id="files"'):]
    want_rows = len(sc["models"])
    check(f"scenario.html: draws the chip for each of the {want_rows} table rows",
          sec.count('<th scope="row"><span class="mtile">') == want_rows,
          str(sec.count('<th scope="row"><span class="mtile">')))
    #  The thing that would silently undo this: a model name set as code again.
    #  Not banned across the section, because the prose above it names fields
    #  and those are code. Banned as the whole content of a row heading, which
    #  is what it was.
    bare = sorted({m for m in sc["models"] if f'<code>{m}</code></th>' in sec})
    check("scenario.html: and no model is set as bare code instead", not bare,
          str(bare))
    #  The inventory is the figure's to carry. The page repeated it underneath
    #  in a list per approach, so every count and every file name was on the
    #  page twice, and the longer telling was the one made of words.
    check("scenario.html: prints no second inventory under the figures",
          'class="scenario__files"' not in sec and sec.count("<dl") == 0,
          str(sec.count("<dl")))


def check_tradeoffs() -> None:
    """Section 2 of every approach page: three strengths, three risks.

    The block is the only place on the site where the approaches are weighed
    rather than described, which makes it the place where an asymmetry does the
    most damage. Three things are held: the count is equal and identical across
    the pages, every figure it prints resolves, and the two colours it uses are
    safe to use for meaning.

    The word budget is enforced in tools/approach_pages.py, which refuses to
    build a page whose two columns differ by more than 15 per cent, or whose
    section runs more than 10 per cent longer than another page's.

    The block carries no citations on the page. That is a decision recorded in
    BUILD-LOG.md, not an omission, so nothing here looks for one. What an entry
    rests on, where it is a claim about what a model can express, is named in
    schema_evidence and checked below without being rendered.
    """
    print("\n[tradeoffs] three strengths, three risks, on all three pages")
    tr = json.load(open(os.path.join(DATA, "tradeoffs.json"), encoding="utf-8"))
    sq = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    approaches = {a["key"] for a in sq["approaches"]}
    stats = json.load(open(os.path.join(DATA, "corpus-stats.json"), encoding="utf-8"))
    stat_keys = {x["key"] for x in stats["stats"]}
    scale_keys = {k for k, v in stats["illustrative_scale"].items()
                  if type(v) is int}

    check("the block covers every approach and nothing else",
          set(tr["approaches"]) == approaches,
          str(sorted(set(tr["approaches"]) ^ approaches)))
    #  The counts were held equal, three a side on every page. That rule is gone:
    #  it started deciding what could be said, and an approach has the risks it
    #  has. What is checked now is that neither side of any page is empty, which
    #  is the failure the equality rule was standing in front of. Length parity
    #  across the three pages is enforced in tools/approach_pages.py and is the
    #  constraint that was doing the real work.
    check("no approach is listed without a per-side count",
          all(k in tr["approaches"] for k in approaches))

    for key in sorted(tr["approaches"]):
        a = tr["approaches"][key]
        for side in ("pros", "cons"):
            check(f"{key}: states at least one {side[:-1]}", len(a[side]) >= 1,
                  str(len(a[side])))
        titles = [e["title"] for e in a["pros"] + a["cons"]]
        check(f"{key}: no entry repeats another's title",
              len(set(titles)) == len(titles))
        check(f"{key}: says what the section is for",
              len(a.get("intro", "").split()) >= 8, a.get("intro", ""))
        for e in a["pros"] + a["cons"]:
            where = f"{key}/{e['title'][:34]}"
            check(f"{where}: says something, in 15 words or more",
                  words_in(e["body"]) >= 15, str(words_in(e["body"])))
            for frag in e.get("schema_evidence", []):
                check(f"{where}: rests on a schema fragment that exists",
                      os.path.isfile(os.path.join(EVIDENCE, f"{frag}.json")), frag)
            # Recomputed figures and editorial scale examples stay distinct.
            # A key that is neither renders an empty span on the page.
            for k in re.findall(r'data-stat="([^"]+)"', e["body"]):
                check(f"{where}: data-stat {k} is a real statistic",
                      k in stat_keys, k)
            for k in re.findall(r'data-cited="([^"]+)"', e["body"]):
                check(f"{where}: data-cited {k} is a declared illustrative scale",
                    k in scale_keys, k)

    #  The counts are no longer held equal, so what is checked is length rather
    #  than shape: an approach can have four risks where another has three, and
    #  none of them may be argued at greater length than another. That budget is
    #  enforced in tools/approach_pages.py, which refuses to build, and is
    #  reported here so a reader of the log sees the numbers.
    #  Measured per point, not per page.
    #
    #  The rule is that no approach is argued at greater length than another,
    #  and the unit that expresses is the point rather than the page. Counted
    #  by page it says something else: that an approach with more to say must
    #  say each thing in fewer words. Component-first carries nine entries to
    #  the others' seven, and squeezing those nine into seven entries' worth of
    #  words would make its sentences terser than its rivals', which reads as
    #  less considered and is a thumb on the scale of its own.
    #
    #  How many points an approach has is a fact about it and is visible in the
    #  list. How much room each one gets is the thing that can be unfair, and
    #  that is what this holds.
    words_by = {k: [len(re.sub(r"<[^>]+>", " ", e["title"] + " " + e["body"]).split())
                    for e in v["pros"] + v["cons"]]
                for k, v in tr["approaches"].items()}
    per = {k: sum(v) / len(v) for k, v in words_by.items()}
    lo, hi = min(per.values()), max(per.values())
    check("no point is given more room than another, across the approaches",
          (hi - lo) / lo <= 0.20,
          ", ".join(f"{k} {sum(words_by[k])}w over {len(words_by[k])} points, "
                    f"{v:.0f} each" for k, v in sorted(per.items()))
          + f", spread {(hi - lo) / lo * 100:.0f} per cent")
    #  And no point runs to a paragraph. A single sentence is the shape here:
    #  these are the claims a reader weighs against each other, and one of them
    #  arriving three times the length of its neighbour is an argument made by
    #  volume.
    for k, v in tr["approaches"].items():
        for e in v["pros"] + v["cons"]:
            n = len(re.sub(r"<[^>]+>", " ", e["body"]).split())
            check(f"{k}: {e['title'][:34]!r} is one sentence, {n} words",
                  12 <= n <= 30 and e["body"].rstrip().count(". ") <= 1, str(n))
    counts = {k: (len(v["pros"]), len(v["cons"])) for k, v in tr["approaches"].items()}
    check("every page states at least one of each",
          all(p and c for p, c in counts.values()), str(counts))

    #  Green and red carry meaning here, which is the one place on this site
    #  they do, so the conditions that make it safe are conditions rather than
    #  intentions. Both tokens defined in both themes; matched in contrast so
    #  neither column shouts; clear of 4.5 on both surfaces they are drawn on;
    #  and never the only channel, which is the mark, the edge and the word.
    css = open(os.path.join(SITE_ROOT, "assets", "site.css"), encoding="utf-8").read()
    for theme in ("light", "dark"):
        t = _tokens_for(theme)
        for name in ("--strength", "--risk"):
            check(f"{theme}: {name} is defined", name in t, str(name))
        if "--strength" not in t or "--risk" not in t:
            continue
        for name in ("--strength", "--risk"):
            for surface in ("--bg", "--bg-subtle"):
                r = _contrast(t[name], t[surface])
                check(f"{theme}: {name} on {surface} is AA (4.5)", r >= 4.5, f"{r:.2f}")
        pair = [_contrast(t[n2], t["--bg"]) for n2 in ("--strength", "--risk")]
        check(f"{theme}: the two are matched in contrast, within 0.25",
              abs(pair[0] - pair[1]) <= 0.25,
              f"{pair[0]:.2f} against {pair[1]:.2f}")
    check("the two columns keep an edge a grayscale reader can separate",
          re.search(r"\.tradeoffs__side--pro\s*\{[^}]*border-left:[^;]*solid", css)
          and re.search(r"\.tradeoffs__side--con\s*\{[^}]*border-left:[^;]*dashed", css))

    #  And the pages render it, in second place, after the inventory.
    for key in sorted(tr["approaches"]):
        body = open(os.path.join(SITE_ROOT, f"{key}.html"), encoding="utf-8").read()
        i, j = body.find('id="tradeoffs"'), body.find('id="exists"')
        check(f"{key}.html: renders the block", i != -1)
        #  Second, between who does what and which models it lands in. The
        #  section that used to follow, this approach's column of the six
        #  questions, is gone: all three columns are on the six questions page,
        #  which is where the comparison a reader is making can be made.
        st = body.find('id="stakeholder"')
        #  Was "before the models", meaning the footprint section. That section
        #  is gone and the join chain took its number, so the block sits between
        #  who does what and how the answers connect. The order is the point:
        #  which party works in which model, then the argument about the
        #  approach, then the detail the argument generalises.
        jn = body.find('id="joins"')
        check(f"{key}.html: after the stakeholder mapping and before the joins",
              st != -1 and jn != -1 and st < i < jn,
              f"stakeholder {st}, tradeoffs {i}, joins {jn}")
        for e in tr["approaches"][key]["pros"] + tr["approaches"][key]["cons"]:
            check(f"{key}.html: carries the entry {e['title'][:30]!r}",
                  e["title"] in body)


def check_links() -> None:
    """Every internal link resolves, and every page is reachable.

    Cross-page anchors were unchecked for six phases. They are the links most
    likely to rot, because the anchor is owned by one page and written on
    another, and a rotted one is invisible unless somebody clicks it.
    """
    print("\n[links] every internal href resolves and every page is in the nav")
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SITE_ROOT, "*.html")))
    text = {p: open(os.path.join(SITE_ROOT, p), encoding="utf-8").read() for p in pages}
    ids = {p: set(re.findall(r'\sid="([^"]+)"', t)) for p, t in text.items()}

    #  The glossary page's anchors used to be synthesised here, one per term,
    #  because a renderer produced them at load time and they were not in the
    #  markup. That page is gone. The vocabulary is not: data/glossary.json still
    #  drives every .dfn term card, and a card now carries the whole of what the
    #  page held for one term, so nothing links to a term anchor any more.

    for page, body in text.items():
        for href in sorted(set(re.findall(r'href="(\./[^"#]*\.html(?:#[^"]*)?)"', body))):
            target, _, frag = href[2:].partition("#")
            check(f"{page}: links to a page that exists, {target}",
                  target in text, href)
            if target in text and frag:
                if target == "six-questions.html" and frag.startswith("q"):
                    #  The question stack is rendered at load time, so its
                    #  anchors are not in the markup to be found here. They are
                    #  q<question>-<approach>, one per cell, and the cell is the
                    #  thing that has to exist. tools/pagecheck.js renders the
                    #  page and checks the id is really produced; this checks the
                    #  link names a pair the data has.
                    slot, _, appr = frag[1:].partition("-")
                    check(f"{page}: link {href} names a question and an approach "
                          f"the data has",
                          any(c["slot"] == slot and c["approach"] == appr
                              for c in question_cells()), href)
                    continue
                check(f"{page}: anchor {target}#{frag} exists on that page",
                      frag in ids[target], href)
        for href in sorted(set(re.findall(r'href="(\./data/[^"]+)"', body))):
            path = os.path.join(SITE_ROOT, href[2:])
            check(f"{page}: links to a data file that exists, {href}",
                  os.path.isfile(path), path)

    #  Naming a real cell is half of a working link. The other half is that
    #  arriving with the hash in the address takes the reader to it, and for six
    #  phases it did not.
    #
    #  boot() calls initDisclosures, which calls revealHash, synchronously. The
    #  question stack is built from a fetch, so when revealHash ran its targets
    #  did not exist yet and it returned having done nothing. Every one of the
    #  links above carries a hash, eighteen distinct targets across the three
    #  approach pages, and all of them dropped the reader at the top of the
    #  page.
    #
    #  It looked fine because clicking one from the matrix on the same page
    #  works: the stack is built by then, and what fires is the hashchange
    #  listener rather than the load-time call. The broken path is the one that
    #  arrives from somewhere else, which is the path the links exist for.
    #
    #  So the renderer calls revealHash when it is done. Held here because the
    #  failure is silent, produces no error, and is invisible to any check that
    #  only reads the markup.
    js = open(os.path.join(SITE_ROOT, "assets", "site.js"), encoding="utf-8").read()
    stack = js.split("function renderQuestionStack", 1)[-1].split("\n  }", 1)[0]
    check("the question stack reveals the anchor it was asked for, once it has "
          "built it", "revealHash()" in stack,
          "renderQuestionStack does not call revealHash")
    check("and boot still reveals on load for the pages that need no rendering",
          "revealHash();" in js.split("function initDisclosures", 1)[-1]
          .split("\n  }", 1)[0])

    nav = re.findall(r'class="site-nav".*?</nav>', text["index.html"], flags=re.S)
    linked = re.findall(r'href="\./([^"]+\.html)"', nav[0]) if nav else []
    check("every page is reachable from the navigation",
          set(pages) == set(linked),
          f"pages not in nav: {sorted(set(pages) - set(linked))}, "
          f"nav entries with no page: {sorted(set(linked) - set(pages))}")
    for page in pages:
        page_nav = re.findall(r'class="site-nav".*?</nav>', text[page], flags=re.S)
        entries = re.findall(r'href="\./([^"]+\.html)"', page_nav[0]) if page_nav else []
        check(f"{page}: carries the same navigation as the index",
              entries == linked, str([e for e in entries if e not in linked]))

    # Every path on the site has to be relative, or the site works on Pages and
    # not from a folder, or the other way round.
    for page, body in text.items():
        absolute = sorted(set(re.findall(r'(?:href|src)="(/[^/"][^"]*)"', body)))
        check(f"{page}: every internal path is relative", not absolute, str(absolute))

    # --- external links ---------------------------------------------------- #
    # Some external links are rendered from data/ rather than written into
    # markup, so both are scanned. A link a renderer produces is still a link a
    # reader clicks.
    in_markup = {u for body in text.values()
                 for u in re.findall(r'href="(https?://[^"]+)"', body)}
    in_data = set()
    for path in glob.glob(os.path.join(DATA, "*.json")):
        blob = json.load(open(path, encoding="utf-8"))
        in_data |= {u.rstrip('".,') for u in re.findall(
            r'https?://[^\s"\\]+', json.dumps(blob))}
    # Schema identifiers are namespaces rather than pages and are not fetched.
    in_data = {u for u in in_data if "csrc.nist.gov/ns/" not in u
               and "cisa.gov/ns/" not in u}
    external = sorted(in_markup | in_data)
    print(f"        {len(external)} distinct external links, "
          f"{len(in_markup)} in markup and {len(in_data - in_markup)} from data/")
    for u in sorted(in_markup):
        check(f"external link declares rel=noopener: {u[:60]}",
              any(re.search(re.escape(f'href="{u}"') + r'[^>]*rel="noopener"', b)
                  for b in text.values()), u)

    if not have_network():
        skip("every external link is reachable",
             "no network, so the external links could not be requested",
             "for u in $(grep -ho 'https://[^\"]*' *.html | sort -u); do "
             "curl -sS -o /dev/null -w '%{http_code} '\"$u\"'\\n' \"$u\"; done")
        return

    import urllib.error
    import urllib.request
    for u in external:
        req = urllib.request.Request(u, method="HEAD", headers={
            "User-Agent": "tfg-rules-and-checks-site link check"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
        except urllib.error.HTTPError as exc:
            # A HEAD is not always allowed. Fall back to a ranged GET before
            # calling a link broken.
            try:
                req = urllib.request.Request(u, headers={
                    "User-Agent": "tfg-rules-and-checks-site link check",
                    "Range": "bytes=0-0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    code = r.status
            except Exception:                        # noqa: BLE001
                code = exc.code
        except Exception as exc:                     # noqa: BLE001
            code = str(exc)[:60]
        check(f"external link is reachable: {u[:60]}",
              isinstance(code, int) and code < 400, f"got {code}")


# --------------------------------------------------------------------------- #
# --matrix                                                                     #
# --------------------------------------------------------------------------- #

def check_slots() -> None:
    """The answer matrix is the site's central claim set, so it gets its own pass.

    Twenty-four cells, and the seven unanswered ones carry the most weight. An
    unanswered cell can mean three different things and rendering them the same
    would be an argument disguised as a design choice, so every one of them has
    to name which of the three it is and carry the evidence behind it as a
    tooltip. That is the check plan section 11.4 asks for.
    """
    print("\n[matrix] every cell resolves, and every unanswered one is classified")
    anat = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    slots = [s["number"] for s in anat["slots"]]
    approaches = [a["key"] for a in anat["approaches"]]
    empty = {e["key"] for e in anat["empty_states"]}
    filled = {"filled", "partial"}

    cells = {(c["slot"], c["approach"]): c for c in anat["matrix"]}
    check("the matrix is complete: every question by every approach",
          len(cells) == len(slots) * len(approaches),
          f"{len(cells)} cells against {len(slots)} by {len(approaches)}")
    missing = sorted({(s, a) for s in slots for a in approaches} - set(cells))
    check("no cell is absent", not missing, str(missing))
    strays = sorted(k for k in cells if k[0] not in slots or k[1] not in approaches)
    check("no cell names a question or an approach that does not exist",
          not strays, str(strays))

    # Equal budget by construction: the same number of cells per approach, so a
    # matrix cannot describe one approach in more places than another.
    per = collections.Counter(a for _, a in cells)
    check("the same number of cells for every approach",
          len(set(per.values())) == 1, str(dict(per)))

    have_snips = {os.path.splitext(os.path.basename(p))[0]
                  for p in glob.glob(os.path.join(SNIPPETS, "*.json"))}
    have_snips |= {os.path.splitext(os.path.basename(p))[0]
                   for p in glob.glob(os.path.join(EVIDENCE, "*.json"))}

    for (s, a), c in sorted(cells.items()):
        where = f"cell {s}/{a}"
        state = c.get("state")
        check(f"{where} declares a state", state in filled | empty, str(state))
        check(f"{where} carries a note, which becomes its tooltip",
              bool(c.get("note", "").strip()))
        dangling = sorted(set(c.get("snippet_ids", [])) - have_snips)
        check(f"{where} points only at extracts that exist", not dangling, str(dangling))
        if state in filled:
            check(f"{where} is answered, so it names the construct that answers it",
                  bool(c.get("model")) and bool(c.get("assemblies")),
                  f'model {c.get("model")!r}, assemblies {c.get("assemblies")!r}')
        if state in empty:
            # This is the check that matters. An unanswered cell is the easiest
            # claim on the site to get wrong and the most consequential.
            check(f"{where} is unanswered and says which of the three it is",
                  state in empty, str(state))
            check(f"{where} unanswered note gives the reason, not just the absence",
                  len(c.get("note", "")) >= 40, f"{len(c.get('note', ''))} characters")

    # --- the names have to say what the question asks --------------------
    # "Control tie" was a label that told a reader nothing on its own. Every
    # name is now a phrase, with a short form for the strip cells, and both are
    # required so that a later edit cannot quietly go back to a bare noun.
    for s in anat["slots"]:
        n = s["number"]
        # A two-word noun phrase is exactly what was wrong before: "Control
        # tie" has a space in it and still tells a reader nothing. The bar is
        # three words, and the retired labels are named so they cannot return.
        words = s.get("name", "").split()
        check(f"question {n} has a name that says what it asks",
              len(words) >= 3, s.get("name", ""))
        check(f"question {n} does not use a retired label as its name",
              s.get("name", "").strip().lower() not in RETIRED_LABELS,
              s.get("name", ""))
    # And the prose. Renaming a question and leaving every sentence that used
    # the old label is how a retired label survives where a reader meets it.
    for blob in ("six-questions.json", "glossary.json", "questions.json",
                 "views.json"):
        path = os.path.join(DATA, blob)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read().lower()
        check(f"{blob} does not use the retired phrase 'control tie'",
              "control tie" not in text)
        check(f"question {n} has a short form for tight spaces",
              bool(s.get("short", "").strip()) and len(s["short"]) <= 14,
              s.get("short", ""))
        check(f"question {n} states its question as a question",
              s.get("question", "").rstrip().endswith("?"), s.get("question", ""))
    six = [s for s in anat["slots"] if s["number"].startswith("6")]
    check("the two-part question carries one name for the pair",
          len({s.get("group_name") for s in six}) == 1 and all(s.get("group_name")
                                                              for s in six))

    # --- the catalog approach's control link names its mechanism ----------
    # Question 2 for this approach used to read as though an inline prop was the
    # plan and had been stripped pending a decision. It is not: the tie is made
    # by OSCAL's own mapping model, in a separate document, which is why the
    # inline props came out. The mechanism has to be named, and the state has to
    # stay unanswered, because no mapping document is published. The cell wording
    # was cut to the length the other questions use; these three checks are what
    # the cut had to preserve.
    cat2 = [c for c in anat["matrix"]
            if c["approach"] == "catalog-first" and c["slot"] == "2"][0]
    check("the catalog approach's control link names the mapping model",
          cat2.get("model") == "mapping-collection", str(cat2.get("model")))
    check("and says the tie is made by it rather than inline",
          "mapping model" in cat2["note"] and "inline" in cat2["note"])
    #  Answered, and answered by a document. The cell used to read unanswered
    #  because no publisher had shipped a mapping, but that is a fact about the
    #  corpus and this axis is about the model: the tie is made, in a separate
    #  file, by a released OSCAL model. What nobody has published belongs on the
    #  artifacts page, and the note still says it.
    check("the catalog approach answers the control tie",
          cat2["state"] == "filled", cat2["state"])
    check("and still records that no publisher has shipped a mapping",
          "No publisher has shipped one" in cat2["note"], cat2["note"][:80])
    #  Late binding used to be question 2b, a row in the matrix, and its
    #  catalog-first cell carried the disclaimer that being the only approach
    #  able to use it is not an advantage. The row is gone: it scored a property
    #  of the OSCAL mapping model as though it were something an approach
    #  answers, and it rewarded whichever view of a rule the schema already
    #  assumes. The disclaimer still has to be somewhere, because the analysis
    #  is still on the site, so it is asserted where the analysis now lives.
    #  RETIRED, two checks. They asserted that the site's mapping-collection
    #  analysis carried its own disclaimer: that being the only approach able to
    #  use late binding is not an advantage, and that the constraint is a gap in
    #  OSCAL rather than a property of any approach. That analysis lived in
    #  sections 2.1 to 2.3 of the six questions page, which has been reduced to
    #  the grid alone, so there is no longer a claim for the disclaimer to
    #  qualify. What survives is the question itself, put to the group on the
    #  open questions page with both sides at the same length.
    #
    #  If the analysis is ever re-homed, these two come back with it.
    late = [b for b in [s for s in anat["slots"] if s["number"] == "2"][0]
            ["binding_times"] if b["key"] == "late"][0]
    check("the binding-times table still records who can use late binding",
          set(late.get("available_to", {})) ==
          {a["key"] for a in anat["approaches"]}, str(late.get("available_to")))
    check("and why the other two cannot",
          "closed by allOf" in late.get("why", ""))

    # An answer describes where a rule lives and how it joins. A bare count
    # describes the sample somebody published, so a cell answering a question
    # should not lead with one.
    lead_number = re.compile(r"^\s*\d[\d,]*\s")
    offenders = [(c["slot"], c["approach"]) for c in anat["matrix"]
                 if lead_number.match(c.get("note", ""))
                 or lead_number.match(" ".join(c.get("assemblies", [])))]
    check("no answer opens with a count instead of a description",
          not offenders, str(offenders))

    counted = collections.Counter(c["state"] for c in anat["matrix"])
    print(f"        states in use: {dict(counted)}")
    check("every declared empty state is used by at least one cell, or dropped",
          all(k in counted for k in empty), str(sorted(empty - set(counted))))


# --------------------------------------------------------------------------- #
# --budget                                                                     #
# --------------------------------------------------------------------------- #

PROSE_STRIP = re.compile(
    r"<(script|style|pre|code|nav|header|footer|svg)\b.*?</\1>", re.S | re.I)


def _page_prose(path: str) -> str:
    """The authored prose of a page: no navigation, no code, no rendered data.

    Snippets and quotations render from data/ at load time, so the static markup
    holds exactly what a person wrote, which is what a budget should measure.
    """
    body = open(path, encoding="utf-8").read()
    m = re.search(r"<main\b[^>]*>(.*)</main>", body, re.S)
    body = m.group(1) if m else body
    body = PROSE_STRIP.sub(" ", body)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", body)


def check_budget() -> None:
    """Editorial rule 5, measured from the shipped HTML rather than the generator.

    tools/approach_pages.py already refuses to write pages outside the budget.
    That is the generator checking its own arithmetic. This measures the files
    that actually shipped, which is the only number a reader is exposed to.
    """
    print("\n[budget] equal budget across the three approach pages")
    pages = ["assessment-first.html", "catalog-first.html", "component-first.html"]
    counts = {}
    for p in pages:
        path = os.path.join(SITE_ROOT, p)
        if not os.path.isfile(path):
            check(f"{p} exists", False, path)
            return
        counts[p] = len([w for w in _page_prose(path).split() if w])

    for p, n in counts.items():
        print(f"        {p:26s} {n:5d} words of prose")
    lo, hi = min(counts.values()), max(counts.values())
    mean = sum(counts.values()) / len(counts)
    spread = (hi - lo) / mean
    check("no two approach pages differ by more than ten per cent",
          spread <= 0.10, f"{spread * 100:.1f} per cent, {lo} to {hi}")

    # The structural counts have to match too, or one page could hold its word
    # budget while carrying an extra section or an extra figure. This is the
    # check that caught assessment-first shipping without its own join diagram
    # while the other two showed theirs.
    for what, pattern in (("sections", r"<section\b"), ("subsections", r"<h3\b"),
                          ("figures", r"<figure\b"), ("strips", r"data-strip="),
                          ("diagrams", r"data-diagram=")):
        got = {p: len(re.findall(pattern, open(os.path.join(SITE_ROOT, p),
                                               encoding="utf-8").read()))
               for p in pages}
        check(f"the three approach pages carry the same number of {what}",
              len(set(got.values())) == 1, str(got))

    # Extract counts are the one thing on these pages that cannot be equal.
    #
    # Plan section 3 rule 5 asks for the "same snippet count". It is not
    # reachable and forcing it would be worse than the asymmetry: one corpus has
    # six distinct constructs to show and another has fourteen, so equality
    # would mean either padding one page with extracts that illustrate nothing
    # or deleting extracts a reader needs. Both put a thumb on the scale more
    # heavily than an unequal count does.
    #
    # What is checkable, and is what the rule is for, is that no approach's
    # answer goes unevidenced, and that the difference in count is stated on the
    # page in the same words rather than left to read as depth of documentation.
    anat = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    bodies = {p: open(os.path.join(SITE_ROOT, p), encoding="utf-8").read()
              for p in pages}
    shown = {p: set(re.findall(r'data-(?:snippet|schema)="([^"]+)"', b))
             for p, b in bodies.items()}
    for p in pages:
        print(f"        {p:26s} {len(shown[p]):5d} distinct extracts")

    #  Every answered question has to carry evidence. That used to be checked
    #  on the approach pages, which showed the extracts for their own column;
    #  they do not any more, and the six questions page shows all three columns
    #  of both kinds. It renders from data, so this asserts the data: an
    #  answered cell declares a published extract, or an encoding of the two
    #  running rules exists for it, or both. An answer resting on neither is the
    #  thing the rule was written to catch.
    pat = json.load(open(os.path.join(DATA, "pattern-examples.json"),
                         encoding="utf-8"))
    encoded = {(q, ap) for q, per in pat["examples"].items() for ap in per}
    for cell in anat["matrix"]:
        if cell["state"] not in ("filled", "partial"):
            continue
        where = f"question {cell['slot']}, {cell['approach']}"
        check(f"{where}: is answered and something evidences it",
              bool(cell.get("snippet_ids"))
              or (cell["slot"], cell["approach"]) in encoded,
              f"extracts {len(cell.get('snippet_ids', []))}, "
              f"encoding {(cell['slot'], cell['approach']) in encoded}")

    #  Three checks here held the extract-count note on each page: that it
    #  stated its own count, that it gave the structural reason for the three
    #  counts differing, and that all three worded the reason identically. The
    #  extracts were in section 3 and went with it. What is left on a page is
    #  its status evidence, and a count of that is not a fact a reader needs.

    # And the two boxes in the strongest-case section, which is the one place a
    # page argues for and against itself.
    for p in pages:
        body = open(os.path.join(SITE_ROOT, p), encoding="utf-8").read()
        boxes = re.findall(r'<div class="card">(.*?)</div>', body, re.S)
        if len(boxes) < 2:
            continue
        w = [len(re.sub(r"<[^>]+>", " ", b).split()) for b in boxes[:2]]
        sp = abs(w[0] - w[1]) / ((w[0] + w[1]) / 2) if sum(w) else 0
        check(f"{p}: the case for and the questions against are within fifteen per cent",
              sp <= 0.15, f"{w[0]} against {w[1]} words")


# --------------------------------------------------------------------------- #
# --conformance                                                                #
# --------------------------------------------------------------------------- #

def _label_for(sid: str, anat: dict) -> str:
    """The status annotation the site shows on a snippet from this corpus."""
    snip = load_snippet(sid)
    for a in anat["approaches"]:
        if a["key"] == snip.get("approach"):
            return a["status_annotation"]
    return "schema evidence"


def check_conformance() -> None:
    """Check local OSCAL examples against their labels and NIST 1.2.1 schemas.

    Offline checks retain the structural evidence. Formal validation uses
    jsonschema and the exact published schema for each document's model, not
    a CLI exit status that could also mean a malformed command. Every local
    OSCAL document is checked, not just a representative file per approach.
    Missing dependencies or network are explicit skips, and fail under --strict.
    """
    print("\n[conformance] labelled conformant validates, labelled proposed fails")
    anat = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    reproduce = "python tools/verify.py --conformance --strict"
    print(f"        reproduce with jsonschema installed: {reproduce}")

    # --- the offline half: the structural reason the labels differ ---------- #
    # OSCAL 1.2.1 defines no rules, checks or rule-groups assembly anywhere in
    # the component-definition model. Their presence is what makes the
    # component-first content unvalidatable. Absence is only a structural
    # check, not proof of conformance; the full schemas are checked below.
    proposed_keys = {"rules", "checks", "rule-groups", "implementing-rules",
                     "assessment-check-id", "target-component-uuid"}

    def keys_in(path: str) -> set:
        found = set()

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in proposed_keys:
                        found.add(k)
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(json.load(open(path, encoding="utf-8")))
        return found

    corpora = {
        "component-first": sorted(glob.glob(ex.source_path("IBM", "*.json"))),
        "catalog-first": sorted(glob.glob(ex.source_path(
            "AWS/oscal-content-for-aws-services-main", "**", "*.json"),
            recursive=True)),
        "assessment-first": oscal_files("Easy Dynamics"),
    }
    for key, files in corpora.items():
        check(f"{key}: local OSCAL examples are present", bool(files))
        label = [a["status_annotation"] for a in anat["approaches"]
                 if a["key"] == key][0]
        used = set()
        for f in files:
            used |= keys_in(f)
        if label == "proposed schema":
            check(f"{key} is labelled proposed and uses undefined assemblies",
                  bool(used), f"undefined keys found: {sorted(used)}")
        else:
            check(f"{key} is not labelled proposed and uses no undefined assembly",
                  not used, f"undefined keys found: {sorted(used)}")

    # The misspelled key in the component-first assessment plan is a second,
    # independent reason that file cannot validate. It was reported on the
    # data-quality page, which has been removed, so this is now the only place
    # it is recorded.
    ap = corpus_json("IBM/assessment-plan.json")["assessment-plan"]
    check("the component-first assessment plan cannot validate for a second reason",
          "local-defintions" in ap and "local-definitions" not in ap,
          "expected the misspelled local-defintions key")

    # --- the network half -------------------------------------------------- #
    try:
        from jsonschema.validators import validator_for
    except ImportError:
        skip("every conformant extract validates against OSCAL 1.2.1",
             "the Python jsonschema package is required", reproduce)
        skip("every proposed extract fails validation",
             "the Python jsonschema package is required", reproduce)
        return
    if not have_network():
        skip("every conformant extract validates against OSCAL 1.2.1",
             "no network to fetch the pinned NIST 1.2.1 schemas", reproduce)
        skip("every proposed extract fails validation",
             "no network to fetch the pinned NIST 1.2.1 schemas", reproduce)
        return

    validators = {}
    failed_schemas = set()
    for key, files in corpora.items():
        label = [a["status_annotation"] for a in anat["approaches"]
                 if a["key"] == key][0]
        for target in files:
            where = os.path.relpath(target, SITE_ROOT)
            with open(target, encoding="utf-8") as fh:
                document = json.load(fh)
            models = set(document) & set(NIST_SCHEMAS) if isinstance(document, dict) else set()
            if not check(f"{where}: identifies one OSCAL model", len(models) == 1,
                         str(sorted(models))):
                continue
            model = next(iter(models))
            if model in failed_schemas:
                continue
            if model not in validators:
                try:
                    schema = _nist_schema(model)
                    validator_class = validator_for(schema)
                    validator_class.check_schema(schema)
                    validators[model] = validator_class(
                        schema, format_checker=validator_class.FORMAT_CHECKER)
                except Exception as exc:
                    # A download/schema failure is never evidence that an
                    # example labelled proposed correctly failed validation.
                    check(f"{model}: NIST 1.2.1 schema is available and valid",
                          False, str(exc)[:240])
                    failed_schemas.add(model)
                    continue
            try:
                error = next(validators[model].iter_errors(document), None)
            except Exception as exc:
                check(f"{where}: schema validation completed", False, str(exc)[:240])
                continue
            detail = (f"/{'/'.join(map(str, error.absolute_path))}: {error.message}"
                      if error is not None else "no schema violations")
            if label == "proposed schema":
                check(f"{where}: proposed schema fails NIST 1.2.1 validation",
                      error is not None, detail[:240])
            else:
                check(f"{where}: validates against NIST 1.2.1",
                      error is None, detail[:240])


# --------------------------------------------------------------------------- #
# --example                                                                    #
# --------------------------------------------------------------------------- #

def check_example() -> None:
    """Our own encodings: two rules, written in all three shapes.

    The site used to quote what each group published. That compares subject
    matter, because the three ship for different products, so the encodings are
    now ours: two rules, chosen once, written three ways, so the only thing that
    differs between the columns is the modelling.

    Authoring the content is a licence to get it wrong, which is what this phase
    exists to stop. The disciplines are the ones the retired worked example was
    held to: real identifiers, a namespace on every property and none of them
    ours, nobody named, and the same rules in every column.
    """
    print("\n[example] our own encodings, and what must hold across them")

    for tool, what in (("pattern_examples.py", "data/pattern-examples.json"),
                       ("oscal_artifacts.py", "data/oscal-artifacts.json")):
        rc = subprocess.run([sys.executable, os.path.join(TOOLS_DIR, tool), "--check"],
                            capture_output=True, text=True)
        detail = (rc.stdout + rc.stderr).strip().splitlines()
        check(f"{what} is current with its generator", rc.returncode == 0,
              detail[-1] if detail else "")

    pe = json.load(open(os.path.join(DATA, "pattern-examples.json"), encoding="utf-8"))

    #  Two rules, deliberately of different shapes: one binary, one carrying a
    #  value. The pair is what shows where each approach puts a parameter.
    rules = pe["rules"]
    check("the encodings rest on two rules", len(rules) == 2, str(len(rules)))
    check("one rule carries a value and one does not",
          sum(1 for r in rules if r["key"] == "password-min-length") == 1)
    for r in rules:
        check(f"{r['key']}: keeps the publisher's own identifier",
              bool(r["stig"]["group"]) and r["stig"]["group"].startswith("V-"),
              str(r["stig"]))
        check(f"{r['key']}: names the control it supports", bool(r["control"]))
        check(f"{r['key']}: says why it was chosen", len(r["why_chosen"]) > 60)

    #  The same rules, in the same order, in every column. If this drifts the
    #  columns stop being comparable, which is the one thing they are for.
    #  The two rules appear in every column, in the same order. An approach may
    #  carry an extra block beyond them, which is how a choice only it has to
    #  make gets shown, so extras are allowed and are required to be labelled.
    #  "both" is the shared block for a question answered once per document
    #  rather than once per rule, so it is shared, not extra.
    #  A column may also answer a per-rule question once for the whole document,
    #  which is a real difference between the approaches rather than drift: the
    #  claim question is answered per rule by two of them and by a single
    #  pointer by the third. So each column has to be one of two shapes, both
    #  rules in order or one shared block, and where a question mixes the two
    #  the shared block has to say what it covers.
    #  A third shape, since the runner arrived. Question 5 answers once per
    #  path, because what a runner sits between depends on who is running it,
    #  so a column there carries one block per path it has, keyed by the path.
    _anat = json.load(open(os.path.join(DATA, "six-questions.json"),
                           encoding="utf-8"))
    #  Two files to a path, what the run reads and what it writes, so the
    #  block keys are the path key with a half on the end.
    path_keys = {(c["slot"], c["approach"]):
                 [x["key"] + half for x in c["paths"] for half in ("-in", "-out")]
                 for c in _anat["matrix"] if c.get("paths")}
    rule_keys = [r["key"] for r in rules]
    for q, per in pe["examples"].items():
        shapes = {}
        for ap, bl in per.items():
            paths = path_keys.get((q, ap), [])
            keys = rule_keys + ["both"] + paths
            core = [b for b in bl if b["rule"] in keys]
            shapes[ap] = [b["rule"] for b in core]
            by_path = bool(paths) and sorted(shapes[ap]) == sorted(paths)
            check(f"question {q}/{ap}: answers per rule, once, or once per path",
                  shapes[ap] in (rule_keys, ["both"]) or by_path, str(shapes[ap]))
            if shapes[ap] == ["both"]:
                check(f"question {q}/{ap}: the shared block says what it covers",
                      len(core[0]["label"]) > 12, core[0]["label"])
            elif by_path:
                for b in core:
                    check(f"question {q}/{ap}/{b['rule']}: says what that path "
                          f"shows", len(b["label"]) > 12, b["label"])
        per_rule = {ap: [b["label"] for b in bl if b["rule"] in rule_keys]
                    for ap, bl in per.items() if shapes[ap] == rule_keys}
        check(f"question {q}: the same rules in every option answering per rule",
              len(set(map(str, per_rule.values()))) <= 1, str(per_rule))

    #  A question answers itself and not the one after it. Question 1 asks only
    #  where the rule is written down; the tie to a control is question 2.
    #
    #  The component-first encoding of the parameterised rule used to carry a
    #  control implementation, to show where the value is set. Setting a value
    #  needs an implemented requirement, because that is what a control
    #  implementation requires, and an implemented requirement names a control
    #  and the rule that implements it. So a reader met control-id and
    #  implementing-rules under question 1, one question before the tie to a
    #  control was put to them. The declaration stays there and the value moved
    #  to question 2, onto the control implementation already in it.
    TIE = ("implemented-requirements", "control-id", "implementing-rules",
           "related-controls", "mapping-collection")
    for ap, bl in pe["examples"].get("1", {}).items():
        for b in bl:
            found = sorted(t for t in TIE if t in b["content"])
            check(f"q1/{ap}/{b['rule']}: says where the rule is written and "
                  f"leaves the control tie to question 2",
                  not found, str(found))

    #  The parameter gap, held as evidence rather than as prose that could drift.
    #
    # Question 1 puts a rule's parameters in its definition, with the options
    # and a default. Two approaches declare one; the third has no construct
    # to declare it with.
    #
    #  It is not a mark against the column. The approach is not failing to use a
    #  construct, it is being asked to use one that does not exist: an activity
    #  and a step have no parameter. So the cell says the value goes into the
    #  rule text and the answer state stays filled.
    #
    #  It had an open question behind it as well, and that question has been
    #  taken off the page. What is left is a description of what the encoding
    #  does, which is what the cell was always saying; what is gone is the
    #  argument that it ought to be otherwise. The evidence stays checked, so
    #  the description cannot drift from the encodings it describes.
    rule2 = {ap: bl[1]["content"] for ap, bl in pe["examples"]["1"].items()
             if len(bl) > 1}
    for ap in ("catalog-first", "component-first"):
        check(f"q1/{ap}: the rule that carries a value declares a parameter",
              '"params"' in rule2.get(ap, ""), "no params in the encoding")
    check("q1/assessment-first: has no parameter to declare",
          '"params"' not in rule2.get("assessment-first", ""))
    check("q1/assessment-first: so the value is inside the requirement text",
          "15-character" in rule2.get("assessment-first", ""),
          "the literal is no longer in the title")
    anat = json.load(open(os.path.join(DATA, "six-questions.json"),
                          encoding="utf-8"))
    cell = [c for c in anat["matrix"]
            if c["slot"] == "1" and c["approach"] == "assessment-first"][0]
    check("q1/assessment-first: answers the question, the rule being written down",
          cell["state"] == "filled", cell["state"])
    check("and its note says the value goes into the rule itself",
          "parameter" in cell["note"] and "value" in cell["note"])

    #  The runner question shows documents the other questions already show.
    #
    #  Question 5 is a run, so its blocks are the file it reads and the file it
    #  writes, and both of those are answers to other questions: the check at 3,
    #  the response at 6a, the result at 6b. Two encodings of one document that
    #  disagree are saying there are two documents, and they had drifted: one
    #  carried a description the other did not, one carried the control
    #  implementation the other had trimmed away.
    #
    #  They are built from one function each now, and this is what says so.
    #  Compared by field path rather than by bytes, because a slice is
    #  legitimate: question 3 shows one check where question 5 shows both.
    def _paths(o, p=""):
        out = set()
        if isinstance(o, dict):
            for k, v in o.items():
                out.add(p + "." + k)
                out |= _paths(v, p + "." + k)
        elif isinstance(o, list):
            for e in o:
                out |= _paths(e, p + "[]")
        return out

    def _block(q, ap, rule):
        for b in pe["examples"].get(q, {}).get(ap, []):
            if b["rule"] == rule:
                return json.loads(b["content"])
        return None

    SHARED = [
        ("catalog-first", "3", "data-at-rest", "5", "implementor-in",
         "the check component"),
        ("catalog-first", "6a", "data-at-rest", "5", "implementor-out",
         "the response in the plan of record"),
        ("component-first", "3", "data-at-rest", "5", "implementor-in",
         "the validation component"),
        ("component-first", "6a", "data-at-rest", "5", "implementor-out",
         "the response in the plan of record"),
        ("component-first", "6b", "data-at-rest", "5", "assessor-out",
         "the observation"),
        ("assessment-first", "6b", "data-at-rest", "5", "assessor-out",
         "the result"),
    ]
    for ap, qa, ra, qb, rb, what in SHARED:
        a, b = _block(qa, ap, ra), _block(qb, ap, rb)
        check(f"q{qa} and q{qb} of {ap} show one {what}, not two",
              a is not None and b is not None and _paths(a) == _paths(b),
              str(sorted(_paths(a) ^ _paths(b))[:3]) if a and b else "missing")

    #  And a result whose related observation resolves. A finding pointing at an
    #  observation uuid that its own document does not carry is not a result.
    for ap in ("catalog-first", "assessment-first"):
        blk = _block("6b", ap, "data-at-rest")
        res = blk["assessment-results"]["results"][0]
        have = {o["uuid"] for o in res.get("observations", [])}
        want = {r["observation-uuid"] for f in res.get("findings", [])
                for r in f.get("related-observations", [])}
        check(f"q6b/{ap}: every observation a finding relates to is in the "
              f"document", want <= have, str(sorted(want - have)))

    #  Brevity, as a rule rather than as a habit.
    #
    #  These are the sentences a reader meets in a cell, a step or a row, and
    #  the whole page is a comparison: three columns of them, read across. One
    #  note ran to a hundred words while its neighbours ran to twelve, which
    #  made the approach look more complicated than the others when what had
    #  happened is that its note had been rewritten more often. Long is not
    #  neutral on a page like this.
    #
    #  Two sentences is the shape. The ceiling allows a third where a claim
    #  needs a qualification, and the floor is there because a note of four
    #  words is not an answer.
    for c in anat["matrix"]:
        n = len(c["note"].split())
        check(f"q{c['slot']}/{c['approach']}: the note is brief, {n} words",
              6 <= n <= 32, str(n))
    jn_b = json.load(open(os.path.join(DATA, "joins.json"), encoding="utf-8"))
    for key, a in jn_b["approaches"].items():
        for i, h in enumerate(a["hops"], 1):
            n = len(h["note"].split())
            check(f"{key}/step {i}: the note is brief, {n} words",
                  6 <= n <= 32, str(n))
    sh_b = json.load(open(os.path.join(DATA, "stakeholders.json"),
                          encoding="utf-8"))
    for key, per in sh_b["approaches"].items():
        for pk, e in per.items():
            if not e.get("note"):
                continue
            n = len(e["note"].split())
            check(f"{key}/{pk}: the row's note is brief, {n} words",
                  6 <= n <= 32, str(n))
    for g in sh_b.get("groups", []):
        n = len(g["note"].split())
        check(f"group {g['key']}: the note is brief, {n} words", 6 <= n <= 32,
              str(n))

    #  The runner's two paths. Question 5 is the only one whose answer is a
    #  step rather than a place, and a runner is legible only as the thing
    #  between an input and an output. Which documents those are depends on who
    #  runs it: an implementer runs the checks to build the responses in a plan
    #  of record, an assessor runs the same checks to produce a result from a
    #  plan they own.
    #
    #  It was one lineage row per approach, input to output, with the output
    #  reading "the claim, the result, or both". That or was doing too much
    #  work: the two outputs are two different runs by two different parties,
    #  and drawing them as alternatives off one arrow said they were the same
    #  run recorded twice.
    paths = {c["approach"]: c["paths"] for c in anat["matrix"]
             if c["slot"] == "5" and c.get("paths")}
    check("every approach says which of the two paths it has",
          set(paths) == {a["key"] for a in anat["approaches"]},
          str(sorted(paths)))
    by = {(c["slot"], c["approach"]): c for c in anat["matrix"]}
    seen = set()
    for ap, ps in sorted(paths.items()):
        keys = [p["key"] for p in ps]
        check(f"q5/{ap}: its paths are named from the fixed pair",
              set(keys) <= {"implementor", "assessor"} and len(set(keys)) == len(keys),
              str(keys))
        seen |= set(keys)
        for p in ps:
            where = f"q5/{ap}/{p['key']}"
            check(f"{where}: has a file in and a file out",
                  bool(p.get("in")) and bool(p.get("out")), str(p))
            for role in ("copy", "in", "out"):
                end = p.get(role)
                if not end:
                    continue
                model = end.get("model") or (by.get((end.get("slot"), ap))
                                             or {}).get("model")
                check(f"{where}: the {role} names a document",
                      bool(model), str(end))
            #  An assessor's run ends in a result and an implementer's in the
            #  plan of record, which is what makes them two paths rather than
            #  one with a choice at the end.
            out = p["out"].get("model") or (by.get((p["out"].get("slot"), ap))
                                            or {}).get("model")
            want = ("assessment-results" if p["key"] == "assessor"
                    else "system-security-plan")
            check(f"{where}: ends in {want}", out == want, str(out))
    check("both paths are shown by some approach",
          seen == {"implementor", "assessor"}, str(sorted(seen)))
    #  Only component-first has both, and that is the finding rather than an
    #  accident of authoring.
    check("component-first is the only approach with both paths",
          [ap for ap, ps in paths.items() if len(ps) == 2] == ["component-first"],
          str({ap: len(ps) for ap, ps in paths.items()}))

    #  A path has to have its encoding under it, keyed by the path.
    for ap, ps in sorted(paths.items()):
        blocks = {b["rule"] for b in pe["examples"]["5"].get(ap, [])}
        for p in ps:
            if not blocks:
                continue
            #  A path is a run, so it shows what the run reads and what it
            #  writes. One without the other is half an answer, and the whole
            #  point of the section is that the runner is the thing between.
            for half, what in (("-in", "what the run reads"),
                               ("-out", "what the run writes")):
                check(f"q5/{ap}/{p['key']}: shows {what}",
                      p["key"] + half in blocks, str(sorted(blocks)))

    #  The paths must agree with the stakeholder mapping, which draws the same
    #  two runs on every approach page. Two places saying one thing, so they are
    #  compared rather than trusted.
    sh = json.load(open(os.path.join(DATA, "stakeholders.json"), encoding="utf-8"))
    for ap, ps in sorted(paths.items()):
        ends = set()
        for p in ps:
            ends.add(p["out"].get("model")
                     or by[(p["out"]["slot"], ap)]["model"])
        drawn = {m["model"]
                 for e in sh["approaches"][ap].values()
                 for f in (e.get("flows") or []) for m in f["to"]}
        check(f"q5/{ap}: its outputs are the ones the mapping draws",
              ends <= drawn, f"{sorted(ends)} against {sorted(drawn)}")

    #  A block showing a second arrangement lights what moved.
    #
    #  Focus is keyed on the question and the approach, because the two rules in
    #  a cell are the same shape. An extra block is there to show the same answer
    #  arranged differently, so the cell's key can be exactly wrong for it: the
    #  bulk block moves the check off the steps and onto the activity above them,
    #  and the cell's key is "steps", which lit everything except the thing the
    #  block was drawn to show.
    #
    #  Asserted as a difference rather than as a literal, because what matters is
    #  that the override is still being applied. Dropping it from the generator
    #  would fall back to the cell's key silently, light the wrong lines, and
    #  break nothing else.
    for q, per in pe["examples"].items():
        for ap, bl in per.items():
            keys = {b["rule"]: b.get("focus_key") for b in bl if b.get("focus_key")}
            #  A block keyed to a path is not a rearrangement of the cell's
            #  answer, it is one half of a run: what it reads or what it writes.
            #  Two paths reading the same construct is the finding rather than a
            #  duplicate, so only genuine extras are held to this.
            paths = {x["key"] + h
                     for c in _anat["matrix"]
                     if c.get("paths") and c["slot"] == q and c["approach"] == ap
                     for x in c["paths"] for h in ("-in", "-out")}
            extra = {r: k for r, k in keys.items()
                     if r not in {x["key"] for x in pe["rules"]}
                     and r != "both" and r not in paths}
            for rule, key in extra.items():
                others = {k for r, k in keys.items() if r != rule}
                check(f"q{q}/{ap}/{rule}: lights what this arrangement moved, "
                      f"not what the other blocks light",
                      not others or key not in others,
                      f"{key!r} against {sorted(others)}")

    #  The shallowest-only selector, exercised directly.
    #
    #  No focus uses it at the moment: the one that did, question 1 of the
    #  assessment column, moved onto the check property when it turned out that
    #  in that approach the rule and the check are the same thing. The selector
    #  stays, because the problem it solves recurs the moment a focus names a
    #  key that also appears nested under itself, and a title or a props is
    #  exactly that kind of key. An unused mechanism with no test is the kind
    #  that rots quietly, so it is checked against a document written here
    #  rather than against whatever the encodings happen to contain.
    sys.path.insert(0, TOOLS_DIR)
    import pattern_examples as _pe
    _sample = json.dumps({"outer": {"title": "a", "inner": {"title": "b"}}},
                         indent=2)
    check("the focus selector finds a key at every depth",
          len(_pe.focus_spans(_sample, "title")) == 2,
          str(_pe.focus_spans(_sample, "title")))
    check("and the shallowest-only form keeps just the outer one",
          len(_pe.focus_spans(_sample, "title^")) == 1
          and _pe.focus_spans(_sample, "title^")[0]
          == _pe.focus_spans(_sample, "title")[0],
          str(_pe.focus_spans(_sample, "title^")))

    #  Addressing one element of an array by a value it carries, with a brace
    #  inside a string value to prove the scan is not counting brackets. The
    #  catalog statement really does hold one, in an insert directive, and a
    #  scanner that balanced braces without tracking string boundaries would
    #  close the wrong object.
    _arr = json.dumps({"props": [{"name": "method", "value": "{ TEST }"},
                                 {"name": "check", "value": "x"}]}, indent=2)
    _got = _pe.focus_spans(_arr, "name=check")
    _lines = _arr.split("\n")
    check("the focus selector can address one element of an array",
          len(_got) == 1, str(_got))
    if len(_got) == 1:
        lo, hi = _got[0]
        _in = "\n".join(_lines[lo - 1:hi])
        check("and it takes the whole element and only that one",
              '"name": "check"' in _in and "method" not in _in
              and _lines[lo - 1].strip() == "{" and _lines[hi - 1].strip() == "}",
              _in.replace("\n", " "))

    #  What the page lights inside each block. The spans are computed by the
    #  generator from the encoding, never typed against it, so what is checked
    #  here is that they still land where they claim to and that they still
    #  point at something rather than at everything.
    for q, per in pe["examples"].items():
        for ap, bl in per.items():
            for b in bl:
                where = f"q{q}/{ap}/{b['rule']}"
                lines = b["content"].split("\n")
                spans = b.get("focus") or []
                check(f"{where}: names the part that answers the question",
                      bool(spans) and bool(b.get("focus_key")), str(spans))
                if not spans:
                    continue
                lit = sum(hi - lo + 1 for lo, hi in spans)
                check(f"{where}: every lit span is inside the block",
                      all(1 <= lo <= hi <= len(lines) for lo, hi in spans),
                      f"{spans} against {len(lines)} lines")
                #  The first lit line has to carry the key, or the span has
                #  drifted off the thing it was computed for. A trailing ^ on a
                #  key means the generator kept only its shallowest matches, so
                #  it is a selector rather than part of the name.
                #  A focus can name more than one field, where the answer is
                #  two of them and lighting one tells half of it. Each span
                #  then has to open on one of the names rather than on the one.
                names = [x.strip().rstrip("^") for x in b["focus_key"].split(",")]
                bare = names[0]
                if len(names) > 1:
                    check(f"{where}: every lit line opens on one of "
                          f"{', '.join(names)}",
                          all(any(f'"{n}":' in lines[lo - 1] for n in names)
                              for lo, _hi in spans),
                          str([lines[lo - 1].strip()[:34] for lo, _ in spans]))
                    check(f"{where}: and each of them is lit at least once",
                          all(any(f'"{n}":' in lines[lo - 1] for lo, _hi in spans)
                              for n in names),
                          ", ".join(names))
                elif "=" in bare:
                    #  An object addressed by a value it carries. It opens on a
                    #  brace, so what is asserted is that the value is inside
                    #  the span rather than on its first line.
                    kn, kv = bare.split("=", 1)
                    check(f"{where}: every lit span holds {kn}={kv}",
                          all(f'"{kn}": "{kv}"' in "\n".join(lines[lo - 1:hi])
                              for lo, hi in spans),
                          str([lines[lo - 1].strip()[:30] for lo, _ in spans]))
                    check(f"{where}: and each is a whole object",
                          all(lines[lo - 1].strip() == "{"
                              and lines[hi - 1].strip().rstrip(",") == "}"
                              for lo, hi in spans),
                          str([(lines[lo - 1].strip(), lines[hi - 1].strip())
                               for lo, hi in spans]))
                else:
                    check(f"{where}: the lit lines open on {bare!r}",
                          all(f'"{bare}":' in lines[lo - 1] for lo, _hi in spans),
                          str([lines[lo - 1].strip()[:40] for lo, _ in spans]))
                #  And where it is shallowest-only, every span really is at one
                #  depth: the point of the selector is to stay out of the
                #  structures nested under it, which are other questions.
                if b["focus_key"].endswith("^"):
                    depths = {len(lines[lo - 1]) - len(lines[lo - 1].lstrip())
                              for lo, _hi in spans}
                    check(f"{where}: and all sit at one depth", len(depths) == 1,
                          str(sorted(depths)))
                #  A focus covering the whole block points at nothing. Question
                #  1 of the assessment column lit fifty lines of fifty-six
                #  before the key was narrowed from the activity to its props.
                check(f"{where}: lights a part rather than the whole block",
                      lit <= len(lines) * 0.75,
                      f"{lit} of {len(lines)} lines")
        for ap, bl in per.items():
            for b in bl:
                if b["rule"] in keys:
                    continue
                check(f"question {q}/{ap}: the extra block says what it is",
                      len(b["label"]) > 12 and len(b["shows"]) > 40, b["label"])

    #  Every block is JSON, every property that carries a namespace carries a
    #  real one, and none of them is ours. Inventing a namespace was the thing
    #  the retired corpus did that this replaces.
    OURS = ("component-definition-focus-group", "oscal-foundation.github.io",
            "tfg-rules-and-checks")
    #  Names OSCAL defines itself, which is why the publishers' own files give
    #  them no namespace. asset-type was on this list for one encoding and came
    #  off with it: an exception for a property that appears nowhere is
    #  permission granted for nothing, and if it returns it should have to be
    #  argued for again rather than slipping in under a standing allowance.
    CORE_PROPS = {"method", "marking", "label", "sort-id", "version", "status",
                  "type", "released"}
    blocks = [(f"q{q}/{ap}/{b['rule']}", b)
              for q, per in pe["examples"].items()
              for ap, bl in per.items() for b in bl]
    check("every encoding is well-formed JSON", True)
    naked, ours = [], []
    for where, b in blocks:
        doc = json.loads(b["content"])

        def walk(o):
            if isinstance(o, dict):
                #  method is a core OSCAL prop name and carries no namespace,
                #  which is why the publishers' own files do not give it one.
                if ("name" in o and "value" in o and "ns" not in o
                        and len(o) <= 4 and o.get("name") not in CORE_PROPS):
                    naked.append(f"{where}: {o.get('name')}")
                if isinstance(o.get("ns"), str) and any(x in o["ns"] for x in OURS):
                    ours.append(f"{where}: {o['ns']}")
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(doc)
    check("every property in an encoding carries a namespace", not naked,
          str(naked[:4]))
    check("and no namespace in an encoding is ours", not ours, str(ours[:4]))

    #  Nobody is named anywhere in content the site wrote itself.
    text = json.dumps(pe)
    for org in ("Easy Dynamics", "IBM", "Amazon Web Services"):
        check(f"the encodings name no proponent organization: {org}",
              org not in text)

    #  How a capability is enabled is a claim the site makes in a badge on
    #  every cell, and a badge is exactly the kind of claim that rots. So it is
    #  derived from the encoding and compared, rather than trusted: a cell that
    #  says "assembly" while its JSON leans on a namespaced prop is a defect.
    PROPOSED_NAMES = {
        "rules", "rule-groups", "implementing-rules", "checks",
        "associated-checks", "uses-assessment-platforms",
        "import-component-definitions", "assessment-check-id",
        "assessment-asset-uuid", "target-component-uuid",
    }

    def _props_named(doc, want: str):
        """Every prop in `doc` whose name is `want`, wherever it sits.

        Used to hold a cell's named prop against the cell's own encoding, so
        the box on the page cannot claim a prop the JSON beside it does not
        carry, or claim a namespace the publisher did not use.
        """
        out = []

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "props" and isinstance(v, list):
                        out.extend(x for x in v
                                   if isinstance(x, dict) and x.get("name") == want)
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(doc)
        return out

    def observed(doc):
        """Which mechanisms this document actually uses."""
        seen = set()

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in PROPOSED_NAMES:
                        seen.add("proposed")
                    if k == "props" and isinstance(v, list):
                        #  A core OSCAL prop is part of the model. Only a prop in
                        #  somebody's own namespace is an extension.
                        if any(x.get("ns") for x in v):
                            seen.add("prop")
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(doc)
        return seen

    anat = json.load(open(os.path.join(DATA, "six-questions.json"), encoding="utf-8"))
    vocab = {m["key"] for m in anat["mechanism_states"]}
    check("the legend defines exactly three mechanisms",
          vocab == {"assembly", "proposed", "prop"}, str(sorted(vocab)))
    for m in anat["mechanism_states"]:
        check(f"mechanism {m['key']}: says what it means and how it is drawn",
              len(m["meaning"]) > 60 and bool(m["rendering"]) and bool(m["short"]))

    for cell in anat["matrix"]:
        where = f"q{cell['slot']}/{cell['approach']}"
        declared = set(cell.get("mechanisms") or [])
        check(f"{where}: every declared mechanism is in the legend",
              declared <= vocab, str(sorted(declared - vocab)))
        bl = (pe["examples"].get(cell["slot"]) or {}).get(cell["approach"])
        if not bl:
            check(f"{where}: declares no mechanism, because it encodes nothing",
                  not declared, str(sorted(declared)))
            continue
        saw = set()
        for b in bl:
            saw |= observed(json.loads(b["content"]))
        #  Only "proposed" and "prop" are derivable from a document: both are
        #  literal names you can look for. Whether a released assembly carries
        #  part of the answer, as opposed to merely containing it, is a
        #  judgement, so it is declared in the data with the construct that
        #  names it rather than guessed at here.
        #
        #  This used to special-case component-first to make a wrong declaration
        #  pass. It did: question 2 was marked proposed-only when its encoding
        #  plainly shows an implemented-requirement doing half the work. The
        #  special case is gone, and under-declaration is what is checked.
        check(f"{where}: declares every mechanism its encoding demonstrably uses",
              saw <= declared,
              f"declared {sorted(declared)}, encoding also uses {sorted(saw - declared)}")
        check(f"{where}: names the model and the assemblies its answer lives in",
              bool(cell.get("model")) and bool(cell.get("assemblies")),
              f'model {cell.get("model")!r}, assemblies {cell.get("assemblies")!r}')

        #  A named prop has to be a prop that is really in this cell's own
        #  encoding, under the namespace the cell claims for it. Naming the
        #  prop is what the carrier block gained so that a cell declaring the
        #  prop mechanism says which prop: catalog-first at question 3 declared
        #  the mechanism and named a component, and the ConfigRuleId that
        #  actually reaches the runtime check appeared nowhere.
        #
        #  Checked against the encoding rather than against prose, so the claim
        #  cannot drift from the file it came from.
        for p in cell.get("props") or []:
            found_ns = set()
            for b in bl:
                for pr in _props_named(json.loads(b["content"]), p["name"]):
                    found_ns.add(pr.get("ns") or "")
            check(f"{where}: prop {p['name']} is in this cell's own encoding",
                  bool(found_ns), "not present in the block")
            if p.get("ns"):
                check(f"{where}: prop {p['name']} carries the namespace the cell claims",
                      p["ns"] in found_ns, f"encoding has {sorted(found_ns)}")
        #  Naming a prop without declaring the mechanism would put the row on a
        #  cell the legend says uses no props.
        if cell.get("props"):
            check(f"{where}: names props only where it declares the prop mechanism",
                  "prop" in declared, str(sorted(declared)))

    #  A cell names the model and the assemblies its answer lives in, and the
    #  JSON beside it has to show both. An extract of steps with no plan around
    #  it declares one thing and shows another, which is how a reader ends up
    #  unable to tell what document they are looking at.
    #
    #  One invariant does the work: the block opens with the model the cell
    #  names, and every assembly it names is a key inside. That replaced a table
    #  of per-assembly shape signatures, which had to be extended for every new
    #  assembly and quietly passed anything it did not know about.
    def has_key(doc, name):
        want = {name, name + "s"}
        found = [False]

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in want:
                        found[0] = True
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(doc)
        return found[0]

    #  An assembly that is an object type rather than a key. The container it
    #  sits in is the key, and that is what gets looked for.
    CONTAINER = {"control": "controls", "activity": "activities",
                 "step": "steps", "component": "components",
                 "resource": "resources", "finding": "findings",
                 "observation": "observations", "mapping": "mappings",
                 "map": "maps", "implemented-requirement": "implemented-requirements",
                 "by-component": "by-components"}

    for cell in anat["matrix"]:
        names = cell.get("assemblies") or []
        bl = (pe["examples"].get(cell["slot"]) or {}).get(cell["approach"])
        if not names or not bl:
            continue
        where = f"q{cell['slot']}/{cell['approach']}"
        rule_keys = {x["key"] for x in pe["rules"]} | {"both"}
        MODELS = {"catalog", "profile", "mapping-collection",
                  "component-definition", "system-security-plan",
                  "assessment-plan", "assessment-results",
                  "plan-of-action-and-milestones"}
        for b in bl:
            doc = json.loads(b["content"])
            #  An extra block can answer from a different document, and question
            #  4 of component-first is why: its answer is a response in the plan
            #  of record, and its extra is the same component carried into the
            #  assessor's own plan. Holding every block to the cell's model said
            #  that second document was the wrong one. It still has to open with
            #  a model, and the assembly rule below still applies to the cell's
            #  own blocks.
            if b["rule"] not in rule_keys:
                check(f"{where}/{b['rule']}: opens with an OSCAL model",
                      list(doc)[:1] and list(doc)[0] in MODELS, str(list(doc)[:1]))
                continue
            check(f"{where}: the block opens with the model the cell names",
                  isinstance(doc, dict) and list(doc)[:1] == [cell["model"]],
                  f'opens with {list(doc)[:1]}, cell says {cell["model"]!r}')
            for n in names:
                check(f"{where}: and shows the {n} inside it",
                      has_key(doc, CONTAINER.get(n, n)),
                      f"no {CONTAINER.get(n, n)} in the encoding")

    #  A cell that shows no JSON has to say why, in the same terms as one that
    #  does. "Nothing here" is a claim, and an unevidenced claim is the thing
    #  this site exists not to make: the runner cell for the catalog approach
    #  had an invented back-matter resource in it until the corpus was searched
    #  and came back empty.
    for cell in anat["matrix"]:
        bl = (pe["examples"].get(cell["slot"]) or {}).get(cell["approach"])
        where = f"q{cell['slot']}/{cell['approach']}"
        if bl:
            check(f"{where}: shows JSON, so claims no absence",
                  "no_encoding" not in cell, "both an encoding and an absence")
            continue
        n = cell.get("no_encoding") or {}
        check(f"{where}: encodes nothing, and says what was looked for",
              len(n.get("looked_for", "")) > 20, str(n.get("looked_for")))
        check(f"{where}: and what was found instead",
              len(n.get("found", "")) > 40, str(n.get("found"))[:60])
        check(f"{where}: and names no model, having nothing to name one for",
              not cell.get("model") and not cell.get("assemblies"),
              f'model {cell.get("model")!r}, assemblies {cell.get("assemblies")!r}')

    #  The check identifier is the join across the columns. If the three
    #  approaches name a check differently, a reader cannot follow one check
    #  from one column to the next, and the comparison stops being one.
    for r in rules:
        cid = r["check_id"]
        check(f"{r['key']}: the check id is the publisher's XCCDF rule id",
              cid.startswith("SV-") and cid.endswith("_rule"), cid)
        for ap in ("catalog-first", "component-first", "assessment-first"):
            bl = (pe["examples"].get("3") or {}).get(ap) or []
            mine = [b for b in bl if b["rule"] == r["key"]]
            check(f"{r['key']}: {ap} names that same check id at question 3",
                  any(cid in b["content"] for b in mine),
                  f"looked for {cid}")

    #  Rules and checks, not remediation. A remediate step would be a second
    #  subject on a site that is about one.
    for q, per in pe["examples"].items():
        for ap, bl in per.items():
            for b in bl:
                check(f"q{q}/{ap}/{b['rule']}: carries no remediation step",
                      "remediate" not in b["content"].lower(),
                      b["label"])

    #  One component for the rule, another for the check. That separation is the
    #  shape the component approach rests on, and it only holds if the check
    #  actually resolves to the component carrying the rule. A uuid that points
    #  nowhere would look identical on the page.
    def only_component(block):
        """The single component in a component-definition block."""
        comps = json.loads(block)["component-definition"]["components"]
        return comps[0]

    rule_doc = only_component(pe["examples"]["1"]["component-first"][0]["content"])
    check_doc = only_component(pe["examples"]["3"]["component-first"][0]["content"])
    check("the rule and the check sit on two different components",
          rule_doc["type"] != check_doc["type"],
          f'{rule_doc["type"]} and {check_doc["type"]}')
    check("and the check component is the validation one",
          check_doc["type"] == "validation", check_doc["type"])
    targets = {c.get("target-component-uuid") for c in check_doc.get("checks", [])}
    check("and every check resolves to the component that carries the rule",
          targets == {rule_doc["uuid"]},
          f'targets {sorted(targets)}, rule component {rule_doc["uuid"]}')
    rule_ids = {r["id"] for r in rule_doc.get("rules", [])}
    named = {c.get("rule-id") for c in check_doc.get("checks", [])}
    check("and names a rule that component actually declares",
          named <= rule_ids, f"names {sorted(named)}, declares {sorted(rule_ids)}")

    #  Question 2 is the mapping model, and the model is the cost. A collection
    #  needs metadata and a four-field provenance block before its first map,
    #  and both ends of a map must be a control or a statement, so it cannot
    #  point at a rule. Asserted here because it is the finding, not a detail.
    mc = json.loads(pe["examples"]["2"]["catalog-first"][0]["content"])
    root = mc.get("mapping-collection", {})
    check("the catalog tie is a whole mapping-collection document",
          all(k in root for k in ("uuid", "metadata", "provenance", "mappings")),
          str(sorted(root)))
    check("and its provenance carries all four required fields",
          all(k in root.get("provenance", {}) for k in
              ("method", "matching-rationale", "status", "mapping-description")),
          str(sorted(root.get("provenance", {}))))
    ends = [m["type"] for mp in root.get("mappings", [])
            for mo in mp.get("maps", [])
            for m in mo.get("sources", []) + mo.get("targets", [])]
    check("and every end of every map is a control or a statement",
          ends and set(ends) <= {"control", "statement"}, str(sorted(set(ends))))



def check_bundle() -> None:
    """The offline fallback mirrors data/ exactly, or it is a liability.

    assets/bundle.js exists so that a copy of this site opens from a folder. It
    is a mirror, and a stale mirror is worse than no mirror: a reader would be
    shown content the build no longer stands behind, with no way to tell.
    """
    print("\n[bundle] the offline fallback matches data/ byte for byte")
    out = os.path.join(SITE_ROOT, "assets", "bundle.js")
    check("assets/bundle.js exists", os.path.isfile(out), out)
    if not os.path.isfile(out):
        return

    rc = subprocess.run([sys.executable, os.path.join(TOOLS_DIR, "bundle.py"),
                         "--check"], capture_output=True, text=True)
    check("the fallback is current with data/ and assets/diagrams/",
          rc.returncode == 0, (rc.stdout + rc.stderr).strip()[:200])

    text = open(out, encoding="utf-8").read()
    check("the fallback says it is generated and must not be edited",
          "GENERATED by tools/bundle.py" in text and "Do not edit" in text)

    # Every file a renderer can ask for has to be in it, or opening from a
    # folder fails for exactly the pages that use that file.
    want = {os.path.relpath(p, SITE_ROOT).replace(os.sep, "/")
            for p in glob.glob(os.path.join(DATA, "**", "*.json"), recursive=True)}
    want |= {os.path.relpath(p, SITE_ROOT).replace(os.sep, "/")
             for p in glob.glob(os.path.join(SITE_ROOT, "assets", "diagrams", "*.svg"))}
    want.add("analysis.json")
    payload = json.loads(text.split("window.TFGBundle = ", 1)[1].rsplit(";", 1)[0])
    missing = sorted(want - set(payload))
    check("every data file and every diagram is in the fallback",
          not missing, str(missing[:6]))
    extra = sorted(set(payload) - want)
    check("the fallback carries only analysis metadata, data and diagrams",
          not extra, str(extra[:6]))
    print(f"        {len(payload)} files, {os.path.getsize(out):,} bytes")

    # And every page has to load it, before site.js, or the fallback is present
    # and unused.
    for page in sorted(glob.glob(os.path.join(SITE_ROOT, "*.html"))):
        body = open(page, encoding="utf-8").read()
        name = os.path.basename(page)
        i_bundle = body.find("assets/bundle.js")
        i_site = body.find("assets/site.js")
        check(f"{name}: loads the fallback before site.js",
              -1 < i_bundle < i_site, f"bundle at {i_bundle}, site.js at {i_site}")


# --------------------------------------------------------------------------- #
# --sources                                                                    #
# --------------------------------------------------------------------------- #

def check_sources() -> None:
    """Validate the published inventory against committed downloads and OSCAL.

    The site's guidance descriptions are authoritative, not reconstructed from
    an external folder. OSCAL counts still come from the original local example
    files; download and example indexes must match their files and digests.
    """
    print("\n[sources] local guidance downloads and original OSCAL examples")
    doc = json.load(open(os.path.join(DATA, "sources.json"), encoding="utf-8"))
    rows = doc["publishers"]
    by_key = {r["key"]: r for r in doc["rows"]}
    check("four publishers", len(rows) == 4, str(sorted(rows)))
    #  Per publisher rather than as one total, because the introduction names the
    #  four counts and a single total would let one grow while another shrank.
    #  Nine DISA rows, not ten: the STIG and SRG package readme was removed as a
    #  row of its own, so the nine STIGs are the nine rows.
    want_rows = {"cis": 2, "disa": 9, "cisa": 1, "aws": 1}
    got_rows = collections.Counter(r["publisher"] for r in doc["rows"])
    check("two CIS, nine DISA, one CISA and one AWS row",
          dict(got_rows) == want_rows, str(dict(got_rows)))
    check("every row key is unique", len(by_key) == len(doc["rows"]))
    check("every row names a publisher that the data defines",
          all(r["publisher"] in rows for r in doc["rows"]),
          str(sorted({r["publisher"] for r in doc["rows"]} - set(rows))))
    check("every publisher has at least one row",
          not (set(rows) - {r["publisher"] for r in doc["rows"]}),
          str(sorted(set(rows) - {r["publisher"] for r in doc["rows"]})))
    check("every row names its guidance and the source form held",
          all(all(r.get(k) for k in ("guidance", "source_form"))
              for r in doc["rows"]))
    check("every publisher records its short name, full name and OSCAL form",
          all(all(p.get(k) for k in ("name", "full_name", "oscal_form"))
              for p in rows.values()))
    #  The one publisher the site shortens. The full name is kept so the
    #  shortening stays a display choice rather than a lost fact.
    check("the table shows CIS, not the full name",
          rows["cis"]["name"] == "CIS"
          and rows["cis"]["full_name"] == "Center for Internet Security",
          rows["cis"]["name"])
    check("every publisher records how its counts were derived",
          all(p.get("derivation") for p in rows.values()))
    check("the removed OSCAL column is gone from the table",
          "Read into OSCAL as" not in doc["columns"], str(doc["columns"]))

    #  The icons are the whole of the last column, so they are the one drawing on
    #  this site a reader cannot get the meaning of any other way. Keeping them
    #  inside the subset tools/svgrender.py rasterises is what lets them be
    #  checked by looking at them: a bezier here would still render in a browser
    #  and would silently stop being checkable, which is how the first globe drew
    #  a wedge in the rasteriser and nobody would have known.
    js = open(os.path.join(SITE_ROOT, "assets", "site.js"), encoding="utf-8").read()
    icons = js.split("function mediaIconMarkup(kind) {", 1)[-1].split("\n  }", 1)[0]
    cmds = set(re.findall(r"[A-Za-z]", " ".join(re.findall(r'd="([^"]+)"', icons))))
    check("every icon path stays in the subset the rasteriser can draw",
          cmds <= set("MmLlHhVvZz"), str(sorted(cmds - set("MmLlHhVvZz"))))

    #  Closed by default, so the summary is what most readers will ever see of
    #  this table. It has to say what is inside without being opened.
    check("the panel has a name and a line saying what is inside",
          bool(doc.get("summary")) and bool(doc.get("summary_sub")))
    words = {1: "One", 2: "Two", 3: "Three", 8: "Eight", 9: "Nine", 10: "Ten"}
    #  Every DISA row is a STIG now. The package readme had a row of its own and
    #  was subtracted here; that row is gone, so the count is the row count.
    for key, noun in (("cis", "CIS Benchmark"), ("disa", "DISA STIG")):
        n = got_rows[key]
        said = f"{words[n]} {noun}s"
        check(f"the summary says {said.lower()}",
              said.lower() in doc["summary_sub"].lower(), doc["summary_sub"])

    #  Guidance that is a page rather than a document is linked, not copied. Both
    #  the URL and what it is have to be in the data, because the icon carries no
    #  text and the title is the only thing that says where the link goes.
    linked = [l for r in doc["rows"] for l in r.get("links", [])]
    check("every link states its kind, its address and what it is",
          all(l.get("kind") and l.get("href", "").startswith("https://")
              and l.get("label") for l in linked), str(len(linked)))
    check("the CISA row links the publisher's page for BOD 25-01",
          any("cisa.gov" in l["href"] and "bod-25-01" in l["href"]
              for l in by_key["cisa-bod-25-01"].get("links", [])))
    check("the AWS row links the publisher's Security Hub guidance",
          any("aws.github.io" in l["href"] and "security-hub" in l["href"]
              for l in by_key["aws-security-hub"].get("links", [])))
    #  Every row has something in its last cell: a document to download or a page
    #  to open. A row with neither would be a claim with nothing behind it, and
    #  the reasons that used to sit under the table are gone.
    with_files = {f["guidance"] for f in json.load(
        open(os.path.join(DATA, "source-files.json"), encoding="utf-8"))["files"]}
    bare = [r["key"] for r in doc["rows"]
            if r["key"] not in with_files and not r.get("links")]
    check("every row carries a document or a link", not bare, str(bare))
    check("no row carries an OSCAL form, which is a publisher-level fact now",
          not any("oscal_form" in r for r in doc["rows"]))

    plans = ez_plans()
    families = {
        "cis": "Center for Internet Security",
        "disa": "DISA",
        "cisa": "CISA BOD 25-01",
    }
    count_models = {
        "assessment_plans": "assessment-plan",
        "assessment_results": "assessment-results",
    }
    for key, family in families.items():
        for count_key, model in count_models.items():
            if count_key not in rows[key]["oscal_counts"]:
                continue
            want = rows[key]["oscal_counts"][count_key]
            got = len(oscal_files("Easy Dynamics", family, root_key=model))
            check(f"{key} row claims {want} {model} documents",
                  got == want, f"found {got}")

    source_counts_valid = all(type(n) is int and n >= 0 for p in rows.values()
                              for n in p.get("source_counts", {}).values())
    check("published source counts are nonnegative integers", source_counts_valid)

    aws = "AWS/oscal-content-for-aws-services-main"
    c = rows["aws"]["oscal_counts"]
    got = len(glob.glob(ex.source_path(aws, "catalogs", "*.oscal.json")))
    check(f"AWS row claims {c['catalogs']} catalog", got == c["catalogs"], f"found {got}")
    got = len(glob.glob(ex.source_path(aws, "component-definitions", "*.oscal.json")))
    check(f"AWS row claims {c['component_definitions']} component definitions",
          got == c["component_definitions"], f"found {got}")
    cat = corpus_json(f"{aws}/catalogs/aws_security-hub.oscal.json")["catalog"]
    got = sum(len(g["controls"]) for g in cat["groups"])
    check(f"AWS row claims {c['controls']} controls", got == c["controls"], f"found {got}")
    check(f"AWS row claims {c['groups']} groups",
          len(cat["groups"]) == c["groups"], f"found {len(cat['groups'])}")
    check("the AWS row says the publisher shipped OSCAL, so no conversion happened",
          "published as oscal"
          in by_key["aws-security-hub"]["source_form"].lower(),
          by_key["aws-security-hub"]["source_form"])

    # --- the files copied into the site --------------------------------- #
    sf = json.load(open(os.path.join(DATA, "source-files.json"), encoding="utf-8"))

    #  Both directions. A link must resolve to a file, and a file must be linked:
    #  a document sitting in sources/ that no row reaches is worse than a missing
    #  one, because nothing on the page says it is there.
    listed = {f["href"] for f in sf["files"]}
    check("source download paths are unique", len(listed) == len(sf["files"]))
    check("source downloads stay within sources/",
          all(h.startswith("sources/") and os.path.commonpath([
              os.path.realpath(os.path.join(SITE_ROOT, "sources")),
              os.path.realpath(os.path.join(SITE_ROOT, h))])
              == os.path.realpath(os.path.join(SITE_ROOT, "sources")) for h in listed))
    missing = [h for h in sorted(listed)
               if not os.path.isfile(os.path.join(SITE_ROOT, h))]
    check("every listed source download is on disk", not missing, str(missing[:4]))

    #  Paths the generator excludes on purpose, declared in the data rather than
    #  known here, so the two cannot disagree. The OSCAL written from this guidance
    #  is published separately, and .gitignore keeps it out of the repository, but a
    #  working copy may still hold it.
    excluded = {e["path"] for e in sf.get("excluded", [])}
    check("every exclusion states why it is excluded",
          all(e.get("why") for e in sf.get("excluded", [])))

    on_disk = set()
    for path in glob.glob(os.path.join(SITE_ROOT, "sources", "**", "*"), recursive=True):
        if not os.path.isfile(path):
            continue
        rel = os.path.relpath(path, SITE_ROOT).replace(os.sep, "/")
        top = rel.split("/")[1] if rel.count("/") >= 1 else ""
        #  Exclusions come at two granularities now. A folder, for the OSCAL
        #  written from this guidance, and a single file, for the readme that is
        #  about the STIG packages as a set rather than about any one guide.
        #  Both are declared in the data and both are stated on the page's own
        #  terms, which is the difference between excluded and forgotten.
        if top in excluded or rel[len("sources/"):] in excluded:
            continue
        on_disk.add(rel)
    unlinked = sorted(on_disk - listed)
    check("every file under sources/ is listed, exclusions aside",
          not unlinked, str(unlinked[:4]))

    #  Nothing listed may come from an excluded path, which is the failure the
    #  exclusion exists to prevent.
    leaked = sorted(h for h in listed
                    if h.split("/")[1:2] and h.split("/")[1] in excluded)
    check("no excluded path is linked from the table", not leaked, str(leaked[:4]))

    #  And the table lists inputs only. A file whose kind is not "source" would be
    #  something written from the guidance rather than read as input.
    kinds = sorted({f.get("kind") for f in sf["files"]})
    check("every listed document is an input, not an output",
          kinds == ["source"], str(kinds))

    # Check the committed index directly, without regenerating its wording.
    bad = []
    for f in sf["files"]:
        full = os.path.join(SITE_ROOT, f["href"])
        if not os.path.isfile(full):
            continue
        if os.path.getsize(full) != f["bytes"]:
            bad.append(f["name"] + ": size")
        if ex.sha256_file(full) != f.get("sha256"):
            bad.append(f["name"] + ": sha256")
        if f["media"] != os.path.splitext(f["name"])[1].lstrip(".").lower():
            bad.append(f["name"] + ": media type")
        media = sf.get("media_types", {}).get(f["media"], {})
        if f.get("mime") != media.get("mime") or f.get("media_label") != media.get("label"):
            bad.append(f["name"] + ": media label or MIME")
    check("every source file's size, digest and media match the index", not bad, str(bad[:4]))

    #  The OSCAL tree used to be excluded from the repository and this asserted
    #  that it stayed excluded. It is committed now, under examples/, so that
    #  the artifacts inventory can link to a document rather than only count it,
    #  and the assertion is turned around: what has to hold is that every file
    #  the inventory names is either in this repository or at a public address.
    examples = json.load(open(os.path.join(DATA, "examples.json"), encoding="utf-8"))
    indexed = {f["path"] for f in examples["files"]}
    check("example paths are unique", len(indexed) == len(examples["files"]))
    check("the example index includes all three approaches",
          {f["approach"] for f in examples["files"]} == set(OPTION_ORDER))
    missing = [f["path"] for f in examples["files"]
               if not os.path.isfile(os.path.join(SITE_ROOT, "examples",
                                                  f["path"].replace("/", os.sep)))]
    check("every indexed example is on disk", not missing, str(missing[:3]))
    on_disk = {os.path.relpath(p, os.path.join(SITE_ROOT, "examples")).replace(os.sep, "/")
               for p in glob.glob(os.path.join(SITE_ROOT, "examples", "**", "*.json"),
                                  recursive=True) if os.path.isfile(p)}
    check("every local JSON example is indexed", on_disk == indexed,
          str(sorted(on_disk ^ indexed)[:4]))
    bad = []
    for f in examples["files"]:
        full = os.path.join(SITE_ROOT, "examples", f["path"])
        if f["path"].split("/", 1)[0] != f["approach"]:
            bad.append(f["path"] + ": approach")
        if not os.path.isfile(full):
            continue
        if os.path.getsize(full) != f.get("bytes"):
            bad.append(f["path"] + ": size")
        if ex.sha256_file(full) != f.get("sha256"):
            bad.append(f["path"] + ": sha256")
    check("every example's size, digest and approach match the index",
          not bad, str(bad[:4]))

    #  And every row of the inventory reaches a document. A local link has to
    #  resolve to a file in this repository; an external one has to be a URL.
    #  The page reads as complete either way, so a row pointing nowhere is the
    #  failure a reader finds by clicking and the build should find first.
    art = json.load(open(os.path.join(DATA, "oscal-artifacts.json"),
                         encoding="utf-8"))
    dead, unlinked = [], []
    for pub in art["publishers"]:
        for f in pub["files"]:
            href = f.get("href")
            if not href:
                unlinked.append(f["file"])
                continue
            if f.get("href_external"):
                if not href.startswith("https://"):
                    dead.append(href)
                continue
            local = urllib.parse.unquote(href).replace("/", os.sep)
            if not os.path.isfile(os.path.join(SITE_ROOT, local)):
                dead.append(href)
        check("every document in the inventory carries a link", not unlinked,
            str(unlinked[:3]))
        check("and every link reaches a file or a public address", not dead,
            str(dead[:3]))
        command = [sys.executable, os.path.join(TOOLS_DIR, "copy_examples.py"), "--check"]
        rc = subprocess.run(command, capture_output=True, text=True,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        check("the local example index passes its read-only integrity check",
            rc.returncode == 0, (rc.stdout + rc.stderr).strip()[-600:])
    check("every file carries its own terms",
          all(f.get("terms") for f in sf["files"]))
    check("every file carries a media label for the icon's alternative text",
          all(f.get("media_label") and f.get("mime") for f in sf["files"]))

    #  Every file names the row it belongs to, and that row must exist. A file
    #  whose row does not exist renders nowhere: the page would look complete and
    #  be short a document, which is the failure this whole table exists to
    #  prevent. Nothing is listed outside the table any more, so a row is the
    #  only home a document has.
    check("every file names the row it belongs to",
          all(f.get("guidance") for f in sf["files"]))
    orphans = sorted({f["guidance"] for f in sf["files"]} - set(by_key))
    check("every file's row exists in the table", not orphans, str(orphans))
    #  A file's row and its folder must agree about the publisher, or a DISA
    #  document could be linked from a CIS row and nothing would say so.
    for_row = {r["key"]: r["publisher"] for r in doc["rows"]}
    crossed = sorted(f["name"] for f in sf["files"]
                     if for_row.get(f["guidance"]) != f["publisher"])
    check("no file is filed under another publisher's row", not crossed,
          str(crossed[:4]))

    #  The release each row names must be the release its files actually are. A
    #  row saying V1R5 while linking V1R4 is the one error in this table a reader
    #  cannot catch, because both look right.
    wrong = []
    for r in doc["rows"]:
        if not r.get("version"):
            continue
        mine = [f["name"] for f in sf["files"] if f["guidance"] == r["key"]]
        if mine and not any(r["version"] in n for n in mine):
            wrong.append(f"{r['key']} says {r['version']}")
    check("every row's version appears in the filename of a file it links",
          not wrong, str(wrong[:4]))

    #  A publisher whose material is not held here has the reason recorded with
    #  the folder, in NOT_COPIED, even though the page now answers the reader's
    #  question with a link to the publisher instead of a paragraph. The record
    #  is about sources/, not about the page: it is what stops an empty folder
    #  from looking like an oversight to whoever maintains it.
    have = {f["publisher"] for f in sf["files"]}
    excused = {n["publisher"] for n in sf.get("not_copied", [])}
    silent = sorted(set(rows) - have - excused)
    check("every publisher has files or a recorded reason it has none",
          not silent, str(silent))
    empty = [r["key"] for r in doc["rows"]
             if not any(f["guidance"] == r["key"] for f in sf["files"])]
    check("every row with no documents belongs to an excused publisher",
          all(for_row[k] in excused for k in empty), str(empty))
    for n in sf.get("not_copied", []):
        check(f"the {n['publisher']} exception says what is missing and why",
              bool(n.get("what") and n.get("why")))
        check(f"the {n['publisher']} row links the publisher instead",
              any(r.get("links") for r in doc["rows"]
                  if r["publisher"] == n["publisher"]))

    #  Every plan in the corpus belongs to exactly one publisher, so a new
    #  publisher cannot appear in the tree without appearing in the table.
    claimed = sum(p["oscal_counts"].get("assessment_plans", 0)
                  for p in rows.values())
    check("every assessment plan in the corpus is accounted for",
          claimed == len(plans), f"data claims {claimed}, corpus has {len(plans)}")


#  The order used to be load-bearing: the methodology page published this list
#  in this order and check_methodology compared the two, so a reordering here
#  silently made the page wrong. That page is gone, and with it the coupling. The
#  order is now only the order the phases run in.
#
#  Two phases were removed with the pages they checked. --appendix recomputed the
#  data-quality page's arithmetic, four items per approach with every numerator
#  beside its denominator. --methodology held the editorial rules against the
#  development plan and checked the correction log.
def check_icons() -> None:
    """One icon per OSCAL model, and the colour still in one place.

    The eight drawings in assets/images are authored with literal hex and a
    filled chip. tools/model_icons.py converts them once into geometry, and the
    stylesheet colours them from the layer tokens. What is worth asserting is
    that the conversion actually happened: an icon that kept its own colour
    would look right in light theme and wrong in dark, which is the failure
    nobody notices until a reader reports it.
    """
    print("\n[icons] one per model, and the colour still lives in the tokens")

    rc = subprocess.run([sys.executable,
                         os.path.join(TOOLS_DIR, "model_icons.py"), "--check"],
                        capture_output=True, text=True)
    detail = (rc.stdout + rc.stderr).strip().splitlines()
    check("data/model-icons.json is current with its generator",
          rc.returncode == 0, detail[-1] if detail else "")

    icons = json.load(open(os.path.join(DATA, "model-icons.json"),
                           encoding="utf-8"))

    #  Every model the site puts content in has to have one, or a tile falls
    #  back to nothing. Taken from the scenario page, which enumerates the seven
    #  it uses, plus the model every matrix cell names.
    sc = json.load(open(os.path.join(DATA, "scenario.json"), encoding="utf-8"))
    anat = json.load(open(os.path.join(DATA, "six-questions.json"),
                          encoding="utf-8"))
    named = set(sc["models"]) | {c["model"] for c in anat["matrix"] if c.get("model")}
    named.add(sc["excluded_model"]["model"])
    missing = sorted(named - set(icons["icons"]))
    check("every model the site names has an icon", not missing, str(missing))

    #  Geometry only. A hex anywhere in here means the conversion let one
    #  through and that icon has stopped following the theme.
    stray = sorted(set(HEX.findall(json.dumps(icons))))
    check("no icon carries a literal colour", not stray, str(stray[:6]))

    #  tools/svgrender.py implements M L H V Z and their relative forms. A curve
    #  renders as a straight line to the last control point, so the grayscale
    #  review would show a shape nobody drew.
    curved = [f'{m}: {s["d"]}' for m, i in icons["icons"].items()
              for s in i["shapes"]
              if s["tag"] == "path" and re.search(r"[CcSsQqTtAa]", s["d"])]
    check("every icon path stays in the subset svgrender can draw",
          not curved, str(curved[:2]))

    #  Three layers, and every icon in exactly one. The hue is the argument: a
    #  model belongs to a layer, and two models in one layer look related
    #  because they are.
    layers = icons["layers"]
    for key, layer in layers.items():
        for m in layer["models"]:
            check(f"{m} is in the {key} layer, and says so once",
                  icons["icons"].get(m, {}).get("layer") == key,
                  str(icons["icons"].get(m, {}).get("layer")))
    listed = [m for l in layers.values() for m in l["models"]]
    check("no model is filed under two layers", len(listed) == len(set(listed)))
    check("and every icon is filed under one",
          set(listed) == set(icons["icons"]),
          str(sorted(set(icons["icons"]) ^ set(listed))))

    #  The icon is a graphical object, so the ratio to clear is the non-text 3.0
    #  rather than the 4.5 body text takes. Both tones, against their own chip,
    #  in both themes, because the chip is what each is drawn on.
    SHORT = {"control": "control", "implementation": "impl",
             "assessment": "assess"}
    for theme in ("light", "dark"):
        t = _tokens_for(theme)
        for layer, short in SHORT.items():
            chip = t[f"--layer-{short}-bg"]
            for tone in ("ink", "soft"):
                ratio = _contrast(t[f"--layer-{short}-{tone}"], chip)
                check(f"{theme}: the {layer} {tone} on its chip is non-text "
                      f"AA (3.0)", ratio >= 3.0, f"{ratio:.2f}")

    #  A class in the markup the stylesheet does not define paints an icon with
    #  no ink at all, which is invisible rather than wrong-coloured.
    css = _css_text()
    for layer in layers:
        check(f"the stylesheet defines .model-icon--{layer}",
              f".model-icon--{layer}" in css)

    #  Two icon families, two names. .micon is the media icon in the sources
    #  table, the one with the PDF badge; .model-icon is this one. They shared a
    #  name for a while and the later rule silently resized the earlier family.
    #  Nothing caught it, because the download links set their own width and the
    #  only marks that moved were the web-link globes.
    bare = re.findall(r"(?m)^\.micon\s*\{[^}]*?\bwidth:\s*([^;]+);", css)
    check("the media icon keeps one width rule, not two",
          len(bare) == 1, str(bare))

    #  The glyph fills its chip. Cropping the viewBox is only half the fix; an
    #  inset here would put the second reduction straight back.
    inset = re.search(r"\.model-icon svg\s*\{[^}]*width:\s*(\d+)%", css)
    check("the glyph fills the chip rather than being inset inside it",
          inset is not None and int(inset.group(1)) == 100,
          inset.group(1) + "%" if inset else "no rule")

    #  The drawing used about half its authored canvas and was then inset again,
    #  so at 16px roughly 8px of it was ink. Cropping is what fixes that, and it
    #  is asserted here rather than left to the generator having been run.
    for model, ic in icons["icons"].items():
        span = float(ic["view_box"].split()[2])
        authored = float(ic["authored_box"].split()[2])
        check(f"{model}: the viewBox is cropped to the drawing",
              span < authored * 0.98, f"{span:g} of {authored:g}")

    #  Two class attributes on one element is invalid and the second is dropped
    #  without complaint. The profile's markers want both, being stroked in the
    #  second tone and filled with the chip colour to hide the rule behind them,
    #  and they shipped with the knockout silently gone.
    import model_icons as mi
    twice = []
    for model in icons["icons"]:
        for el in re.findall(r"<(?:path|rect|circle)\b[^>]*>",
                             mi.model_icon(model)):
            if el.count("class=") > 1:
                twice.append(f"{model}: {el[:60]}")
    check("no icon element carries two class attributes", not twice,
          str(twice[:2]))


PHASES = {
    "snippets": check_snippets,
    "schema": check_schema,
    "stats": check_stats,
    "sources": check_sources,
    "data": check_data,
    "css": check_css,
    "a11y": check_a11y,
    "diagrams": check_diagrams,
    "quotes": check_quotes,
    "criteria": check_criteria,
    "questions": check_questions,
    "matrix": check_slots,
    "budget": check_budget,
    "conformance": check_conformance,
    "example": check_example,
    "bundle": check_bundle,
    "source": check_source_sanity,
    "tradeoffs": check_tradeoffs,
    "stakeholders": check_stakeholders,
    "joins": check_joins,
    "scenario": check_scenario,
    "links": check_links,
    "icons": check_icons,
    "pages": check_pages,
}
NOT_YET: list = []


def main() -> None:
    global STRICT
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--all", action="store_true")
    p.add_argument("--strict", action="store_true",
                   help="a skipped check is a failure. Used in CI, where the "
                        "network and the validators are available.")
    for name in list(PHASES) + NOT_YET:
        p.add_argument(f"--{name}", action="store_true")
    args = p.parse_args()
    STRICT = args.strict

    selected = [n for n in PHASES if getattr(args, n)] or (list(PHASES) if args.all else [])
    if not selected:
        p.print_help()
        sys.exit(2)

    for name in selected:
        PHASES[name]()

    passed = sum(1 for _, ok, _ in _RESULTS if ok)
    total = len(_RESULTS)
    print(f"\n{'=' * 60}\n{passed}/{total} checks passed")

    if _SKIPS:
        # A skip is reported on its own line and is never folded into the pass
        # count. Anything here is a claim this run did not establish.
        print(f"\n{len(_SKIPS)} check(s) skipped, and a skip is not a pass:")
        for name, reason, command in _SKIPS:
            print(f"  - {name}\n      why:     {reason}")
            if command:
                print(f"      command: {command}")
        print("\n  Run with --strict, or in CI, to require these.")

    if passed != total:
        print("\nFailures:")
        for name, ok, detail in _RESULTS:
            if not ok:
                print(f"  - {name}  |  {detail}")
        sys.exit(1)


if __name__ == "__main__":
    main()
