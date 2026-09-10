"""Isolated source-map/cache tests: temporary fixtures and mocked network only."""

from copy import deepcopy
import contextlib
import glob
import io
import json
import os
from pathlib import Path
import runpy
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import source_inputs as sources

PINNED = sources.source_metadata()
REVISION = "4a1779ffb556c4ab8fb3dad94a19d4d198116803"
REPOSITORY = "awslabs/oscal-content-for-aws-services"
PUBLIC_BASE = f"https://github.com/{REPOSITORY}/blob/{REVISION}/"
ARCHIVE_ROOT = "oscal-content-for-aws-services-" + REVISION


class SourceInputsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.lock = deepcopy(PINNED)
        self.ibm, self.easy, self.aws = self.lock["sources"]
        self.ibm["expected_files"] = 1
        self.easy["expected_files"] = 2
        rows = []
        for entry, names in ((self.ibm, ["sample.json"]),
                             (self.easy, ["sample.json", "nested space/other.json"])):
            for name in names:
                raw = b'{"test": "original bytes"}\n'
                self.write(entry["directory"] + "/" + name, raw)
                size, digest = sources._fingerprint(raw)
                rows.append({"approach": entry["approach"],
                             "path": entry["approach"] + "/" + name,
                             "sha256": digest, "bytes": size})
        self.write("data/examples.json", json.dumps({"files": rows}).encode())
        self.members = [
            (ARCHIVE_ROOT + "/", tarfile.DIRTYPE, b""),
            (ARCHIVE_ROOT + "/catalogs/", tarfile.DIRTYPE, b""),
            (ARCHIVE_ROOT + "/catalogs/example.json", tarfile.REGTYPE, b'{"catalog": {}}\n'),
            (ARCHIVE_ROOT + "/profiles/profile.json", tarfile.REGTYPE, b'{"profile": {}}\n'),
            (ARCHIVE_ROOT + "/LICENSE", tarfile.REGTYPE, b"License fixture\n"),
            (ARCHIVE_ROOT + "/NOTICE", tarfile.REGTYPE, b"Notice fixture\n"),
            (ARCHIVE_ROOT + "/README.md", tarfile.REGTYPE, b"Do not extract\n"),
        ]
        self.raw = self.make_archive()
        self.aws["archive_bytes"], self.aws["archive_sha256"] = sources._fingerprint(self.raw)
        self.aws["json_files"] = 2
        self.network = self.enterContext(patch.object(
            sources, "urlopen", side_effect=AssertionError("Unexpected network access")))
        self.enterContext(patch.object(sources, "ROOT", self.root))
        self.enterContext(patch.object(sources, "_LOCK", sources._validate_lock(self.lock)))
        sources.clear_cache()
        self.addCleanup(sources.clear_cache)

    def write(self, relative, raw):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def make_archive(self, members=None):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            for name, kind, raw in self.members if members is None else members:
                info = tarfile.TarInfo(name)
                info.type = kind
                if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                    info.linkname = "../../outside.json"
                info.size = len(raw) if kind == tarfile.REGTYPE else 0
                archive.addfile(info, io.BytesIO(raw) if kind == tarfile.REGTYPE else None)
        return buffer.getvalue()

    def fetch(self, raw=None):
        self.network.side_effect = lambda *_args, **_kwargs: io.BytesIO(self.raw if raw is None else raw)
        try:
            sources.prepare(fetch=True)
        finally:
            self.network.side_effect = AssertionError("Unexpected network access")

    def cache_root(self):
        return self.root / self.aws["directory"]

    def assert_no_cache(self):
        self.assertFalse((self.root / ".cache").exists())

    def test_published_lock_has_exact_source_identities(self):
        ibm, easy, aws = PINNED["sources"]
        self.assertEqual(PINNED["version"], 1)
        self.assertEqual((ibm["key"], ibm["prefix"], ibm["directory"], ibm["expected_files"]),
                         ("ibm", "IBM", "examples/component-first", 6))
        self.assertEqual((easy["key"], easy["prefix"], easy["directory"], easy["expected_files"]),
                         ("easy-dynamics", "Easy Dynamics", "examples/assessment-first", 19))
        self.assertEqual(aws["prefix"], "AWS/oscal-content-for-aws-services-main")
        self.assertEqual(aws["directory"], f".cache/oscal-sources/aws/{REVISION}")
        self.assertEqual(aws["repository"], REPOSITORY)
        self.assertEqual(aws["revision"], REVISION)
        self.assertEqual(aws["url"], f"https://codeload.github.com/{REPOSITORY}/tar.gz/{REVISION}")
        self.assertEqual(aws["archive_sha256"], "f309b59344560b88a699c5908fbc70c51c7a0e8e0339d901b1285b9c8d804a18")
        self.assertEqual(len(aws["archive_sha256"]), 64)
        self.assertEqual((aws["archive_bytes"], aws["json_files"]), (379596, 231))
        self.assertEqual(aws["file_base"], PUBLIC_BASE)

    def test_mapping_supports_joined_split_directory_and_glob_paths(self):
        self.assertEqual(sources.source_path("IBM"), str(self.root / self.ibm["directory"]))
        self.assertEqual(sources.source_path("Easy Dynamics", "nested space/other.json"),
                         sources.source_path("Easy Dynamics/nested space", "other.json"))
        pattern = sources.source_path("Easy Dynamics", "**", "*.json")
        self.assertTrue(Path(pattern).is_absolute())
        self.assertEqual(len(glob.glob(pattern, recursive=True)), 2)
        self.assertEqual(sources.source_path("IBM", "absent*.json"),
                         str(self.root / self.ibm["directory"] / "absent*.json"))
        self.network.assert_not_called()

    def test_unknown_absolute_traversal_and_glob_prefix_rejected(self):
        cases = [(), ("Unknown",), ("IBMadjacent",), ("I*", "*.json"), ("AWS",),
                 ("/IBM",), ("IBM", "/tmp/file"), ("IBM/../sample.json",),
                 ("IBM", "..", "sample.json"), ("IBM", "**/../*.json"),
                 ("IBM", "./sample.json"), ("IBM", "C:/sample.json"),
                 ("IBM", "a\\b"), ("IBM", ""), ("IBM//sample.json",),
                 ("IBM", "sample.json\x00"), ("IBM", "sample.json\n")]
        for parts in cases:
            with self.subTest(parts=parts), self.assertRaises(sources.SourceInputError):
                sources.source_path(*parts)
        self.network.assert_not_called()

    def test_missing_requested_file_rejected(self):
        with self.assertRaisesRegex(sources.SourceInputError, "Missing source path"):
            sources.source_path("IBM", "missing.json")

    def test_environment_cannot_supply_local_or_public_sources(self):
        with patch.dict(os.environ, {"TFG_CORPORA": str(self.root / "unread-external-corpus")}):
            self.assertEqual(sources.source_path("IBM/sample.json"),
                             str(self.root / self.ibm["directory"] / "sample.json"))
            with self.assertRaisesRegex(sources.SourceInputError, sources.FETCH_COMMAND):
                sources.source_path(self.aws["prefix"])
            (self.root / self.ibm["directory"] / "sample.json").unlink()
            sources.clear_cache()
            with self.assertRaisesRegex(sources.SourceInputError, "missing="):
                sources.source_path("IBM")
        self.network.assert_not_called()

    def test_metadata_is_independent_and_has_no_io(self):
        with patch.object(Path, "read_text", side_effect=AssertionError("Unexpected I/O")), \
                patch.object(Path, "is_symlink", side_effect=AssertionError("Unexpected I/O")):
            snapshot = sources.source_metadata()
            snapshot["sources"][0]["prefix"] = "changed"
            self.assertEqual(sources.source_metadata()["sources"][0]["prefix"], "IBM")
            self.assertEqual(sources.public_file_base("catalog-first"), PUBLIC_BASE)
        self.network.assert_not_called()
        self.assert_no_cache()

    def test_non_public_or_unknown_browser_base_rejected(self):
        for approach in ("assessment-first", "component-first", "unknown"):
            with self.subTest(approach=approach), self.assertRaises(sources.SourceInputError):
                sources.public_file_base(approach)

    def test_import_reads_only_lock_and_never_fetches_or_verifies_sources(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Import fetched")) as network, \
                patch.object(Path, "read_bytes", side_effect=AssertionError("Import read a source")):
            module = runpy.run_path(sources.__file__)
            self.assertEqual(module["source_metadata"](), PINNED)
        network.assert_not_called()
        self.assert_no_cache()

    def test_local_corruption_rejected_without_rewriting_index(self):
        original_index = (self.root / "data/examples.json").read_bytes()
        self.write(self.ibm["directory"] + "/sample.json", b"corrupt")
        with self.assertRaisesRegex(sources.SourceInputError, "integrity mismatch"):
            sources.prepare(fetch=True)
        self.assertEqual((self.root / "data/examples.json").read_bytes(), original_index)
        self.assertEqual((self.root / self.ibm["directory"] / "sample.json").read_bytes(), b"corrupt")
        self.network.assert_not_called()

    def test_local_missing_file_rejected(self):
        (self.root / self.easy["directory"] / "sample.json").unlink()
        with self.assertRaisesRegex(sources.SourceInputError, "missing=.*sample.json"):
            sources.source_path("Easy Dynamics")

    def test_local_extra_json_rejected(self):
        self.write(self.ibm["directory"] + "/extra.json", b"{}")
        with self.assertRaisesRegex(sources.SourceInputError, "extra=.*extra.json"):
            sources.source_path("IBM")

    def test_local_index_count_and_fingerprints_are_validated(self):
        path = self.root / "data/examples.json"
        original = json.loads(path.read_text())
        for defect in ("missing", "duplicate", "sha256", "bytes", "path"):
            with self.subTest(defect=defect):
                index = deepcopy(original)
                if defect == "missing":
                    index["files"].pop(0)
                elif defect == "duplicate":
                    index["files"].append(deepcopy(index["files"][0]))
                else:
                    index["files"][0][defect] = {"sha256": "bad", "bytes": -1,
                                                   "path": "component-first/../escape.json"}[defect]
                path.write_text(json.dumps(index))
                sources.clear_cache()
                with self.assertRaises(sources.SourceInputError):
                    sources.source_path("IBM")

    def test_local_symlinks_rejected(self):
        outside = self.write("outside.json", b"{}")
        target = self.root / self.ibm["directory"] / "sample.json"
        target.unlink()
        target.symlink_to(outside)
        with self.assertRaisesRegex(sources.SourceInputError, "Unsafe source entry"):
            sources.source_path("IBM", "*.json")

    def test_clear_cache_forces_revalidation(self):
        sources.source_path("IBM")
        self.write(self.ibm["directory"] + "/sample.json", b"changed")
        sources.source_path("IBM")  # Integrity is intentionally cached per invocation.
        sources.clear_cache()
        with self.assertRaisesRegex(sources.SourceInputError, "integrity mismatch"):
            sources.source_path("IBM")

    def test_prepare_always_rechecks_local_integrity(self):
        sources.source_path("IBM")
        self.write(self.ibm["directory"] + "/sample.json", b"changed")
        with self.assertRaisesRegex(sources.SourceInputError, "integrity mismatch"):
            sources.prepare()

    def test_missing_cache_error_names_exact_fetch_command_without_network(self):
        with self.assertRaisesRegex(sources.SourceInputError, sources.FETCH_COMMAND):
            sources.prepare()
        self.network.assert_not_called()
        self.assert_no_cache()

    def test_explicit_fetch_retains_archive_and_only_allowed_original_files(self):
        self.fetch()
        self.network.assert_called_once_with(self.aws["url"], timeout=60)
        expected = {name.split("/", 1)[1]: raw for name, kind, raw in self.members
                    if kind == tarfile.REGTYPE and not name.endswith("README.md")}
        expected[sources.ARCHIVE] = self.raw
        actual = {p.relative_to(self.cache_root()).as_posix(): p.read_bytes()
                  for p in self.cache_root().rglob("*") if p.is_file()}
        self.assertEqual(actual, expected)
        sources.clear_cache()
        sources.prepare()  # Retained, authenticated archive is the offline authority.
        sources.prepare(fetch=True)  # A valid cache does not download again.
        self.assertEqual(self.network.call_count, 1)
        self.assertEqual(sources.source_path("AWS", "oscal-content-for-aws-services-main", "catalogs"),
                         str(self.cache_root() / "catalogs"))

    def test_bad_download_digest_prevents_tar_open_and_any_cache_write(self):
        bad = bytearray(self.raw)
        bad[-1] ^= 1
        with patch.object(tarfile, "open", side_effect=AssertionError("Tar opened before digest check")):
            with self.assertRaisesRegex(sources.SourceInputError, "SHA-256 mismatch"):
                self.fetch(bytes(bad))
        self.assert_no_cache()

    def test_bad_download_size_prevents_cache_write(self):
        for raw in (self.raw[:-1], self.raw + b"extra"):
            with self.subTest(size=len(raw)), self.assertRaisesRegex(sources.SourceInputError, "SHA-256 mismatch"):
                self.fetch(raw)
        self.assert_no_cache()

    def test_network_failure_is_actionable_and_does_not_write_cache(self):
        self.network.side_effect = OSError("fixture network unavailable")
        with self.assertRaisesRegex(sources.SourceInputError, sources.FETCH_COMMAND):
            sources.prepare(fetch=True)
        self.assert_no_cache()

    def test_traversal_absolute_unexpected_root_links_and_special_tar_entries_rejected(self):
        invalid = [("../escape.json", tarfile.REGTYPE, b"{}"),
                   ("/escape.json", tarfile.REGTYPE, b"{}"),
                   (ARCHIVE_ROOT + "/../../escape.json", tarfile.REGTYPE, b"{}"),
                   ("wrong-root/extra.json", tarfile.REGTYPE, b"{}"),
                   (ARCHIVE_ROOT + "/link", tarfile.SYMTYPE, b""),
                   (ARCHIVE_ROOT + "/hard", tarfile.LNKTYPE, b""),
                   (ARCHIVE_ROOT + "/pipe", tarfile.FIFOTYPE, b""),
                   (ARCHIVE_ROOT + "/a\\b.json", tarfile.REGTYPE, b"{}"),
                   (ARCHIVE_ROOT + "/C:/b.json", tarfile.REGTYPE, b"{}")]
        for member in invalid:
            with self.subTest(member=member):
                raw = self.make_archive(self.members + [member])
                lock = deepcopy(self.lock)
                lock["sources"][2]["archive_bytes"], lock["sources"][2]["archive_sha256"] = sources._fingerprint(raw)
                with patch.object(sources, "_LOCK", sources._validate_lock(lock)):
                    with self.assertRaises(sources.SourceInputError):
                        self.fetch(raw)
                self.assert_no_cache()
        self.assertFalse((self.root / "escape.json").exists())

    def test_duplicate_archive_member_rejected(self):
        duplicates = [self.members[2], (ARCHIVE_ROOT + "/catalogs", tarfile.DIRTYPE, b"")]
        for member in duplicates:
            with self.subTest(member=member):
                raw = self.make_archive(self.members + [member])
                sources._LOCK["sources"][2]["archive_bytes"], sources._LOCK["sources"][2]["archive_sha256"] = sources._fingerprint(raw)
                with self.assertRaisesRegex(sources.SourceInputError, "Duplicate archive"):
                    self.fetch(raw)
        self.assert_no_cache()

    def test_license_and_notice_are_optional(self):
        raw = self.make_archive([m for m in self.members if not m[0].endswith(("LICENSE", "NOTICE"))])
        sources._LOCK["sources"][2]["archive_bytes"], sources._LOCK["sources"][2]["archive_sha256"] = sources._fingerprint(raw)
        self.fetch(raw)
        sources.prepare()
        self.assertFalse((self.cache_root() / "LICENSE").exists())
        self.assertFalse((self.cache_root() / "NOTICE").exists())

    def test_archive_json_count_checked_before_extraction(self):
        sources._LOCK["sources"][2]["json_files"] = 3
        with self.assertRaisesRegex(sources.SourceInputError, "JSON count mismatch"):
            self.fetch()
        self.assert_no_cache()

    def test_cache_tampered_json_rejected_even_with_same_file_size(self):
        self.fetch()
        self.write(self.aws["directory"] + "/catalogs/example.json", b'{"catalog": []}\n')
        with self.assertRaisesRegex(sources.SourceInputError, "integrity mismatch"):
            sources.prepare()

    def test_cache_missing_json_rejected(self):
        self.fetch()
        (self.cache_root() / "catalogs/example.json").unlink()
        with self.assertRaisesRegex(sources.SourceInputError, "missing=.*example.json"):
            sources.prepare()

    def test_cache_extra_json_and_non_json_rejected(self):
        self.fetch()
        for name in ("extra.json", "invented-hashes.txt"):
            with self.subTest(name=name):
                extra = self.write(self.aws["directory"] + "/" + name, b"{}")
                with self.assertRaisesRegex(sources.SourceInputError, "extra="):
                    sources.prepare()
                extra.unlink()

    def test_cache_license_tampering_rejected(self):
        self.fetch()
        (self.cache_root() / "LICENSE").write_bytes(b"changed")
        with self.assertRaisesRegex(sources.SourceInputError, "integrity mismatch"):
            sources.prepare()

    def test_cache_archive_missing_or_corrupt_rejected(self):
        self.fetch()
        path = self.cache_root() / sources.ARCHIVE
        path.write_bytes(b"untrusted archive")
        with self.assertRaisesRegex(sources.SourceInputError, "SHA-256 mismatch"):
            sources.prepare()
        path.unlink()
        with self.assertRaisesRegex(sources.SourceInputError, sources.FETCH_COMMAND):
            sources.prepare()

    def test_cache_symlink_and_symlinked_cache_parent_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / ".cache").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(sources.SourceInputError, "Symlink source path"):
            sources.prepare(fetch=True)
        self.network.assert_not_called()
        self.assertEqual(list(outside.iterdir()), [])
        (self.root / ".cache").unlink()
        self.fetch()
        (self.cache_root() / "alias").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(sources.SourceInputError, "Unsafe source entry"):
            sources.prepare()

    def test_explicit_fetch_repairs_only_cache_and_preserves_examples_and_index(self):
        committed = {p: p.read_bytes() for p in self.root.rglob("*.json")}
        self.fetch()
        self.write(self.aws["directory"] + "/catalogs/example.json", b"corrupt")
        self.write(self.aws["directory"] + "/extra.txt", b"extra")
        self.fetch()
        sources.prepare()
        self.assertFalse((self.cache_root() / "extra.txt").exists())
        self.assertEqual({p: p.read_bytes() for p in committed}, committed)
        self.assertEqual(self.network.call_count, 2)

    def test_failed_fetch_does_not_replace_existing_cache(self):
        self.fetch()
        changed = self.write(self.aws["directory"] + "/catalogs/example.json", b"corrupt")
        with self.assertRaisesRegex(sources.SourceInputError, "SHA-256 mismatch"):
            self.fetch(b"invalid download")
        self.assertEqual(changed.read_bytes(), b"corrupt")
        self.assertEqual((self.cache_root() / sources.ARCHIVE).read_bytes(), self.raw)

    def test_staging_failure_preserves_existing_cache_and_cleans_staging_directory(self):
        self.fetch()
        changed = self.write(self.aws["directory"] + "/catalogs/example.json", b"corrupt")
        # Both archive paths are safe individually but cannot coexist on disk.
        raw = self.make_archive(self.members + [
            (ARCHIVE_ROOT + "/catalogs/example.json/child.json", tarfile.REGTYPE, b"{}")])
        sources._LOCK["sources"][2]["archive_bytes"], sources._LOCK["sources"][2]["archive_sha256"] = sources._fingerprint(raw)
        sources._LOCK["sources"][2]["json_files"] = 3
        with self.assertRaisesRegex(sources.SourceInputError, "Fetch failed"):
            self.fetch(raw)
        self.assertEqual(changed.read_bytes(), b"corrupt")
        self.assertEqual(list(self.cache_root().parent.iterdir()), [self.cache_root()])

    def test_lock_rejects_unpinned_urls_hashes_repository_and_escaping_directory(self):
        cases = [("revision", "main"), ("revision", "a" * 39),
                 ("archive_sha256", "f" * 63), ("archive_sha256", "z" * 64),
                 ("url", self.aws["url"].replace("https:", "http:")),
                 ("url", self.aws["url"].replace(REVISION, "b" * 40)),
                 ("url", self.aws["url"] + "?redirect=elsewhere"),
                 ("url", "https://codeload.github.com.evil.invalid/archive"),
                 ("repository", "other/repository"), ("file_base", PUBLIC_BASE.replace(REVISION, "main")),
                 ("directory", "/tmp/outside"), ("directory", ".cache/../examples/component-first"),
                 ("directory", "examples/component-first"), ("directory", ".cache/unapproved"),
                 ("archive_bytes", True), ("json_files", 0)]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                lock = deepcopy(self.lock)
                lock["sources"][2][field] = value
                with self.assertRaises(sources.SourceInputError):
                    sources._validate_lock(lock)
        self.network.assert_not_called()
        self.assert_no_cache()

    def test_lock_rejects_invalid_schema_duplicates_and_local_escapes(self):
        locks = [None, {}, {"version": 2, "sources": []}, {"version": True, "sources": []}]
        for field, value in (("directory", "../elsewhere"), ("directory", "sources/ibm"),
                             ("prefix", "/IBM"), ("key", "../ibm"), ("expected_files", False)):
            lock = deepcopy(self.lock)
            lock["sources"][0][field] = value
            locks.append(lock)
        duplicate = deepcopy(self.lock)
        duplicate["sources"].append(deepcopy(duplicate["sources"][0]))
        locks.append(duplicate)
        overlap = deepcopy(self.lock)
        overlap["sources"][0]["prefix"] = "AWS"
        locks.append(overlap)
        for lock in locks:
            with self.subTest(lock=lock), self.assertRaises(sources.SourceInputError):
                sources._validate_lock(lock)

    def test_cli_defaults_to_offline_check_and_fetch_is_explicit(self):
        for args in ([], ["--check"]):
            with self.subTest(args=args), patch.object(sources, "prepare") as prepare:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(sources.main(args), 0)
                prepare.assert_called_once_with(fetch=False)
        with patch.object(sources, "prepare") as prepare, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sources.main(["--fetch"]), 0)
            prepare.assert_called_once_with(fetch=True)
        with contextlib.redirect_stderr(io.StringIO()) as error:
            with self.assertRaises(SystemExit) as raised:
                sources.main(["--check"])
        self.assertEqual(raised.exception.code, 1)
        self.assertIn(sources.FETCH_COMMAND, error.getvalue())
        self.network.assert_not_called()


if __name__ == "__main__":
    unittest.main()