#!/usr/bin/env python3
"""
extract.py: build data/snippets/ and data/provenance.json from tools/manifest.yaml.

Nothing on the site is hand-typed. Every code block the reader sees is produced
here, from a source file in the corpora, at a declared JSON pointer.

Usage:
    python tools/extract.py                 write into data/
    python tools/extract.py --out /tmp/x    write elsewhere (used by verify.py)
    python tools/extract.py --quiet         suppress the summary table

Dependencies: Python 3.8+, PyYAML.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys

import source_inputs

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required:  pip install pyyaml")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(TOOLS_DIR)
MANIFEST = os.path.join(TOOLS_DIR, "manifest.yaml")

TRUNCATION_MARKER = " [truncated]"
ELISION_MARKER = "..."


class ExtractionError(Exception):
    """Raised when a snippet cannot be produced exactly as declared."""


# --------------------------------------------------------------------------- #
# RFC 6901 JSON pointer                                                        #
# --------------------------------------------------------------------------- #

def _unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def resolve_pointer(doc, pointer: str, where: str):
    """Resolve an RFC 6901 pointer. '$' means the whole document."""
    if pointer in ("$", "", "/"):
        return doc
    if not pointer.startswith("/"):
        raise ExtractionError(f"{where}: pointer must start with '/' or be '$', got {pointer!r}")

    node = doc
    walked = ""
    for raw in pointer.split("/")[1:]:
        token = _unescape(raw)
        walked += "/" + raw
        if isinstance(node, dict):
            if token not in node:
                keys = ", ".join(sorted(node.keys())[:12])
                raise ExtractionError(
                    f"{where}: no key {token!r} at {walked}. Available: {keys}"
                )
            node = node[token]
        elif isinstance(node, list):
            if not token.lstrip("-").isdigit():
                raise ExtractionError(f"{where}: non-integer index {token!r} at {walked}")
            idx = int(token)
            if idx < 0 or idx >= len(node):
                raise ExtractionError(
                    f"{where}: index {idx} out of range at {walked} (len {len(node)})"
                )
            node = node[idx]
        else:
            raise ExtractionError(
                f"{where}: cannot descend into {type(node).__name__} at {walked}"
            )
    return node


def elide(node, pointer: str, where: str):
    """Replace the value at a relative pointer with the elision marker."""
    parent_ptr, _, last = pointer.rstrip("/").rpartition("/")
    parent = resolve_pointer(node, parent_ptr or "$", where)
    key = _unescape(last)
    if isinstance(parent, dict):
        if key not in parent:
            raise ExtractionError(f"{where}: trim target {pointer!r} not present")
        parent[key] = ELISION_MARKER
    elif isinstance(parent, list):
        parent[int(key)] = ELISION_MARKER
    else:
        raise ExtractionError(f"{where}: trim target {pointer!r} has no container")


def slice_section(text: str, heading: str, where: str) -> str:
    """Return one Markdown section, from its heading to the next of the same
    or a higher level.

    The whole section is returned including its heading, because a section cut
    short is an undeclared trim and the site does not make those. The heading
    is matched exactly, so a source whose wording changes fails the build here
    rather than shipping a silently different quotation.
    """
    lines = text.split("\n")
    start = level = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        hashes = len(stripped) - len(stripped.lstrip("#"))
        if stripped[hashes:].strip() == heading:
            start, level = i, hashes
            break
    if start is None:
        found = [ln.strip() for ln in lines if ln.strip().startswith("#")]
        raise ExtractionError(
            f"{where}: no heading exactly {heading!r}. Headings present: {found}")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].strip()
        if not stripped.startswith("#"):
            continue
        if len(stripped) - len(stripped.lstrip("#")) <= level:
            end = j
            break
    return "\n".join(lines[start:end]).strip("\n")


def truncate_prose(node, limit: int):
    """Recursively cut any string longer than limit, marking the cut explicitly."""
    if isinstance(node, dict):
        return {k: truncate_prose(v, limit) for k, v in node.items()}
    if isinstance(node, list):
        return [truncate_prose(v, limit) for v in node]
    if isinstance(node, str) and len(node) > limit:
        return node[:limit].rstrip() + TRUNCATION_MARKER
    return node


# --------------------------------------------------------------------------- #
# Extraction                                                                   #
# --------------------------------------------------------------------------- #

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(path: str = MANIFEST) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    if "snippets" not in manifest:
        raise ExtractionError("manifest has no 'snippets' key")
    seen = set()
    for entry in manifest["snippets"]:
        sid = entry.get("id")
        if not sid:
            raise ExtractionError(f"manifest entry without an id: {entry!r}")
        if sid in seen:
            raise ExtractionError(f"duplicate snippet id {sid!r}")
        seen.add(sid)
    return manifest


def source_path(*parts: str) -> str:
    """Resolve original source names using the repository's verified source map."""
    return source_inputs.source_path(*parts)


def extract_one(entry: dict) -> dict:
    sid = entry["id"]
    src_rel = entry["source"]
    src_abs = source_path(src_rel)
    if not os.path.isfile(src_abs):
        raise ExtractionError(f"{sid}: source not found: {src_abs}")

    language = entry.get("language", "json")
    pointer = entry.get("pointer", "$")

    if language in ("markdown", "text"):
        if pointer != "$":
            raise ExtractionError(f"{sid}: non-JSON sources must use pointer '$'")
        with open(src_abs, "r", encoding="utf-8") as fh:
            content = fh.read().rstrip("\n")
        if entry.get("section"):
            content = slice_section(content, entry["section"], sid)
    else:
        with open(src_abs, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        node = resolve_pointer(doc, pointer, sid)
        node = json.loads(json.dumps(node))  # deep copy, so trims never touch source
        for trim_ptr in entry.get("trim", []) or []:
            elide(node, trim_ptr, sid)
        if entry.get("max_prose"):
            node = truncate_prose(node, int(entry["max_prose"]))
        content = json.dumps(node, indent=2, ensure_ascii=False)

    return {
        "id": sid,
        "slot": str(entry.get("slot", "meta")),
        "approach": entry.get("approach", "schema"),
        "title": entry.get("title", sid),
        "source": src_rel,
        "pointer": pointer,
        # A Markdown section is part of the address, so it is displayed with the
        # pointer rather than left implicit.
        "section": entry.get("section"),
        "language": language,
        "content": content,
        "sha256_of_source_file": sha256_file(src_abs),
        "extracted_at": _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }


def run(out_dir: str, quiet: bool = False) -> int:
    manifest = load_manifest()
    source_inputs.prepare()

    snippet_dir = os.path.join(out_dir, "snippets")
    os.makedirs(snippet_dir, exist_ok=True)

    rows, provenance, failures = [], [], []

    for entry in manifest["snippets"]:
        sid = entry["id"]
        try:
            record = extract_one(entry)
        except ExtractionError as exc:
            failures.append(str(exc))
            rows.append((sid, entry.get("slot", "?"), entry.get("approach", "?"), 0, "NO"))
            continue

        # Keep the previous extraction time when nothing about the extract has
        # changed. Without this the generator is not idempotent, and a generator
        # that rewrites itself on every run cannot be checked by regenerating and
        # diffing, which is how a hand-edited generated file gets caught.
        out_path = os.path.join(snippet_dir, f"{sid}.json")
        if os.path.isfile(out_path):
            try:
                with open(out_path, "r", encoding="utf-8") as fh:
                    previous = json.load(fh)
            except (OSError, ValueError):
                previous = None
            if previous is not None:
                same = all(previous.get(k) == record.get(k) for k in record
                           if k != "extracted_at")
                if same and previous.get("extracted_at"):
                    record["extracted_at"] = previous["extracted_at"]

        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

        provenance.append(
            {
                "id": record["id"],
                "slot": record["slot"],
                "approach": record["approach"],
                "title": record["title"],
                "source": record["source"],
                "pointer": record["pointer"],
                "language": record["language"],
                "bytes": len(record["content"].encode("utf-8")),
                "sha256_of_source_file": record["sha256_of_source_file"],
                "sha256_of_content": sha256_text(record["content"]),
                "extracted_at": record["extracted_at"],
            }
        )
        rows.append(
            (sid, record["slot"], record["approach"], len(record["content"].encode("utf-8")), "yes")
        )

    if failures:
        for msg in failures:
            print(f"FAIL  {msg}", file=sys.stderr)
        raise ExtractionError(
            f"{len(failures)} snippet(s) did not resolve. "
            "Fix the manifest. Placeholders are never emitted."
        )

    prov_path = os.path.join(out_dir, "provenance.json")
    record = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "source_lock": "tools/source-lock.json",
        "source_inputs": source_inputs.source_metadata(),
        "snippet_count": len(provenance),
        "snippets": provenance,
    }
    # Same reasoning as above. The build time only moves when something extracted
    # actually changed, so this file is a statement about the content rather than
    # about when the command was last typed.
    if os.path.isfile(prov_path):
        try:
            with open(prov_path, "r", encoding="utf-8") as fh:
                previous = json.load(fh)
        except (OSError, ValueError):
            previous = None
        if previous is not None and all(
                previous.get(k) == record[k] for k in record if k != "generated_at"):
            record["generated_at"] = previous.get("generated_at", record["generated_at"])

    with open(prov_path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    if not quiet:
        w = max(len(r[0]) for r in rows) + 2
        print(f"{'id':<{w}}{'slot':<7}{'approach':<20}{'bytes':>8}  resolved")
        print("-" * (w + 47))
        for sid, slot, approach, size, ok in sorted(rows):
            print(f"{sid:<{w}}{slot:<7}{approach:<20}{size:>8}  {ok}")
        print("-" * (w + 47))
        by_approach = {}
        for _, _, approach, _, _ in rows:
            by_approach[approach] = by_approach.get(approach, 0) + 1
        summary = ", ".join(f"{k} {v}" for k, v in sorted(by_approach.items()))
        print(f"{len(rows)} snippets resolved ({summary})")

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.join(SITE_ROOT, "data"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    try:
        run(args.out, quiet=args.quiet)
    except (ExtractionError, source_inputs.SourceInputError) as exc:
        sys.exit(f"\nEXTRACTION FAILED: {exc}")


if __name__ == "__main__":
    main()
