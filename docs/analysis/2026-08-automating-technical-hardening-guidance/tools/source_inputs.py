"""Locked, stdlib-only source inputs; no environment overrides or implicit fetches.

Run ``python tools/source_inputs.py --fetch`` from the analysis directory once,
then ``--check`` works offline. The lock is read once at import; metadata has no
I/O. Successful integrity checks are memoized until clear_cache() or prepare().
Committed examples and their index are never written by this module.
"""

import argparse
from copy import deepcopy
from functools import lru_cache
from glob import has_magic
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ".source-archive.tar.gz"
FETCH_COMMAND = "python tools/source_inputs.py --fetch"


class SourceInputError(RuntimeError):
    """Invalid mapping, missing input, unsafe path, or failed integrity check."""


def _require(condition, message):
    if not condition:
        raise SourceInputError(message)


def _relative(value, patterns=False):
    _require(isinstance(value, str) and bool(value), "Source path must be nonempty text")
    parts = value.split("/")
    _require(not any(p in ("", ".", "..") for p in parts)
             and not any(c in value for c in "\\:\x00")
             and not any(ord(c) < 32 for c in value)
             and (patterns or not has_magic(value)), f"Unsafe source path: {value!r}")
    return parts


def _validate_lock(data):
    _require(isinstance(data, dict) and set(data) == {"version", "sources"}
             and type(data["version"]) is int and data["version"] == 1
             and isinstance(data["sources"], list) and data["sources"], "Invalid source lock version/schema")
    common = {"key", "approach", "prefix", "directory"}
    public = {"repository", "revision", "url", "archive_sha256", "archive_bytes", "json_files", "file_base"}
    for source in data["sources"]:
        _require(isinstance(source, dict), "Invalid source lock entry")
        remote = "repository" in source
        _require(set(source) == common | (public if remote else {"expected_files"}), "Invalid source lock fields")
        for field in common | (public - {"archive_bytes", "json_files"} if remote else set()):
            _require(isinstance(source[field], str), f"Invalid lock field: {field}")
        for field in ("key", "approach"):
            _require(re.fullmatch(r"[a-z][a-z0-9-]*", source[field]), f"Invalid {field}")
        _relative(source["prefix"])
        _relative(source["directory"])
        for field in (("archive_bytes", "json_files") if remote else ("expected_files",)):
            _require(type(source[field]) is int and source[field] > 0, f"Invalid {field}")
        if remote:
            repo, revision = source["repository"], source["revision"]
            _require(repo == "awslabs/oscal-content-for-aws-services", "Unapproved public repository")
            _require(re.fullmatch(r"[0-9a-f]{40}", revision), "Revision must be a full commit SHA")
            _require(re.fullmatch(r"[0-9a-f]{64}", source["archive_sha256"]), "Invalid archive SHA-256")
            _require(source["url"] == f"https://codeload.github.com/{repo}/tar.gz/{revision}", "Archive URL must match pinned official codeload URL")
            _require(source["file_base"] == f"https://github.com/{repo}/blob/{revision}/", "Public file URL must match revision")
            directory = f".cache/oscal-sources/{source['key']}/{revision}"
        else:
            directory = f"examples/{source['approach']}"
        _require(source["directory"] == directory, f"Invalid source directory: {source['directory']}")
    for field in common:
        values = [s[field] for s in data["sources"]]
        _require(len(values) == len(set(values)), f"Duplicate source {field}")
    prefixes = [s["prefix"] for s in data["sources"]]
    _require(not any(a.startswith(b + "/") for a in prefixes for b in prefixes if a != b), "Overlapping source prefixes")
    return deepcopy(data)


_LOCK = _validate_lock(json.loads((ROOT / "tools/source-lock.json").read_text(encoding="utf-8")))


def source_metadata() -> dict:
    """Return an independent version/sources snapshot, without paths outside ROOT or I/O."""
    return deepcopy(_LOCK)


def public_file_base(approach: str) -> str:
    """Return the pinned browser URL; non-public/unknown approaches are errors."""
    for source in _LOCK["sources"]:
        if source["approach"] == approach and "file_base" in source:
            return source["file_base"]
    raise SourceInputError(f"No public file URL for approach: {approach!r}")


def _path(relative):
    # Reject every symlink component, including the cache root, before any I/O
    # below it. Canonical relative paths cannot move outside the analysis root.
    path = ROOT
    for part in _relative(relative, patterns=True):
        path = path / part
        _require(not path.is_symlink(), f"Symlink source path refused: {path}")
    return path


def _fingerprint(raw):
    return len(raw), hashlib.sha256(raw).hexdigest()


def _inventory(root, json_only=False):
    _require(root.is_dir(), f"Missing source directory: {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        _require(not path.is_symlink() and (path.is_dir() or path.is_file()), f"Unsafe source entry: {path}")
        if path.is_file() and (not json_only or path.suffix == ".json"):
            result[path.relative_to(root).as_posix()] = _fingerprint(path.read_bytes())
    return result


def _compare(actual, expected):
    missing, extra = sorted(expected.keys() - actual.keys()), sorted(actual.keys() - expected.keys())
    _require(not missing and not extra, f"Source inventory mismatch; missing={missing}; extra={extra}")
    changed = [name for name in expected if actual[name] != expected[name]]
    _require(not changed, f"Source integrity mismatch (size/SHA-256): {changed}")


def _local_expected(source):
    index = json.loads(_path("data/examples.json").read_text(encoding="utf-8"))
    _require(isinstance(index, dict) and isinstance(index.get("files"), list), "Invalid committed example index")
    expected = {}
    for row in index["files"]:
        _require(isinstance(row, dict), "Invalid example index entry")
        if row.get("approach") != source["approach"]:
            continue
        parts = _relative(row.get("path"))
        _require(parts[0] == source["approach"] and len(parts) > 1
                 and parts[-1].endswith(".json"), "Example index path/approach mismatch")
        name = "/".join(parts[1:])
        digest, size = row.get("sha256"), row.get("bytes")
        _require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                 and type(size) is int and size >= 0 and name not in expected, "Invalid/duplicate example index fingerprint")
        expected[name] = (size, digest)
    _require(len(expected) == source["expected_files"], f"Committed example index count mismatch: {source['key']}")
    return expected


def _archive_files(source, raw):
    # Authenticate the complete retained archive BEFORE even opening the tar.
    _require(_fingerprint(raw) == (source["archive_bytes"], source["archive_sha256"]), "Archive size/SHA-256 mismatch")
    root = source["repository"].split("/")[1] + "-" + source["revision"]
    files, seen, expanded = {}, set(), 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive:
            parts = _relative(member.name.removesuffix("/"))
            _require(parts[0] == root, f"Unexpected archive root: {member.name}")
            _require(member.isdir() or member.isfile(), f"Archive link/special entry refused: {member.name}")
            canonical = "/".join(parts)
            _require(canonical not in seen, f"Duplicate archive entry: {member.name}")
            seen.add(canonical)
            expanded += member.size
            _require(len(seen) <= 10000 and expanded <= 128 * 1024 * 1024, "Archive exceeds safety limits")
            if member.isdir():
                continue
            _require(len(parts) > 1, "Archive root must be a directory")
            name = "/".join(parts[1:])
            if name.endswith(".json") or name in {"LICENSE", "NOTICE"}:
                stream = archive.extractfile(member)
                if stream is None:
                    raise SourceInputError(f"Unreadable archive entry: {name}")
                with stream:
                    files[name] = stream.read()
    _require(sum(name.endswith(".json") for name in files) == source["json_files"], "Archive JSON count mismatch")
    return files


@lru_cache(maxsize=None)
def _verified_source(key):
    source = next(s for s in _LOCK["sources"] if s["key"] == key)
    remote = "repository" in source
    try:
        root = _path(source["directory"])
        if remote:
            archive = _path(source["directory"] + "/" + ARCHIVE)
            _require(archive.is_file() and archive.stat().st_size == source["archive_bytes"], "Missing archive or archive size/SHA-256 mismatch")
            raw = archive.read_bytes()
            expected = {name: _fingerprint(value) for name, value in _archive_files(source, raw).items()}
            expected[ARCHIVE] = _fingerprint(raw)
        else:
            expected = _local_expected(source)
        _compare(_inventory(root, json_only=not remote), expected)
        return root
    except (OSError, ValueError, tarfile.TarError, SourceInputError) as error:
        remedy = (f"Run `{FETCH_COMMAND}` from the analysis directory."
                  if remote else "Restore the committed examples/index; do not regenerate the index to accept changes.")
        raise SourceInputError(f"{key}: {error}. {remedy}") from error


def clear_cache() -> None:
    """Forget successful integrity checks, not the import-time lock snapshot."""
    _verified_source.cache_clear()


def source_path(*parts: str) -> str:
    """Resolve a legacy prefix plus existing path or glob; never fetch or fall back."""
    query = "/".join("/".join(_relative(part, patterns=True)) for part in parts)
    for source in _LOCK["sources"]:
        prefix = source["prefix"]
        if query == prefix or query.startswith(prefix + "/"):
            tail = query[len(prefix):]
            _verified_source(source["key"])
            path = _path(source["directory"] + tail)
            _require(has_magic(tail) or path.is_file() or path.is_dir(), f"Missing source path: {query}")
            return str(path)
    raise SourceInputError(f"Unknown source prefix: {query!r}")


def _fetch(source):
    root = _path(source["directory"])
    try:
        with urlopen(source["url"], timeout=60) as response:
            raw = response.read(source["archive_bytes"] + 1)
        files = _archive_files(source, raw)
        # No cache writes until digest AND all archive member checks pass.
        root.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".staging-", dir=root.parent) as temporary:
            stage = Path(temporary) / "source"
            stage.mkdir()
            for name, value in files.items():
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(value)
            (stage / ARCHIVE).write_bytes(raw)
            expected = {name: _fingerprint(value) for name, value in files.items()}
            expected[ARCHIVE] = _fingerprint(raw)
            _compare(_inventory(stage), expected)
            _path(source["directory"])  # Recheck before replacing only this cache.
            if root.is_dir():
                shutil.rmtree(root)
            elif root.exists():
                root.unlink()
            stage.replace(root)
    except (OSError, ValueError, tarfile.TarError) as error:
        raise SourceInputError(f"Fetch failed for {source['key']}: {error}. Retry `{FETCH_COMMAND}`.") from error


def prepare(fetch: bool = False) -> None:
    """Always recheck every input; explicit fetch may populate/repair only public cache."""
    clear_cache()
    for source in sorted(_LOCK["sources"], key=lambda s: "repository" in s):
        try:
            _verified_source(source["key"])
        except SourceInputError:
            if not fetch or "repository" not in source:
                raise
            _fetch(source)
            _verified_source(source["key"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Verify inputs offline (default)")
    mode.add_argument("--fetch", action="store_true", help="Fetch/repair the pinned public cache, then verify")
    args = parser.parse_args(argv)
    try:
        prepare(fetch=args.fetch)
    except SourceInputError as error:
        parser.exit(1, f"Source inputs: {error}\n")
    print("Source inputs verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())