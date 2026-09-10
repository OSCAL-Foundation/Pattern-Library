"""Regression tests for the verifier; no external corpus or network required."""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import extract
import verify
from schema_validation import schema_validator


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.results = verify._RESULTS
        self.skips = verify._SKIPS
        verify._RESULTS = []
        verify._SKIPS = []

    def tearDown(self):
        verify._RESULTS = self.results
        verify._SKIPS = self.skips

    def run_checks(self, *checks):
        with contextlib.redirect_stdout(io.StringIO()):
            for check in checks:
                check()
        return [(name, detail) for name, ok, detail in verify._RESULTS if not ok]

    def test_all_python_sources_compile(self):
        for source in Path(__file__).parent.glob("*.py"):
            with self.subTest(source=source.name):
                compile(source.read_text(), str(source), "exec")

    def test_source_path_uses_repository_examples_not_environment(self):
        with patch.dict(os.environ, {"TFG_CORPORA": "/tmp/test-corpus"}):
            self.assertEqual(extract.source_path("IBM", "*.json"),
                             str(Path(verify.SITE_ROOT) / "examples/component-first/*.json"))

    def test_extraction_reads_declared_json_pointer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.json").write_text('{"rule": "value"}')
            json_entry = {"id": "sample", "source": "sample.json", "pointer": "/rule"}
            with patch.object(extract, "source_path", return_value=str(root / "sample.json")):
                self.assertEqual(extract.extract_one(json_entry)["content"], '"value"')

    def test_manifest_and_committed_snippets_are_oscal_json_only(self):
        entries = extract.load_manifest()["snippets"]
        self.assertEqual(len(entries), 32)
        self.assertTrue(all(e.get("language", "json") == "json"
                            and e["source"].endswith(".json") for e in entries))
        self.assertEqual({e["id"] for e in entries},
                         {p.stem for p in Path(verify.SNIPPETS).glob("*.json")})
        for path in Path(verify.SNIPPETS).glob("*.json"):
            record = json.loads(path.read_text())
            self.assertEqual(record["language"], "json")
            self.assertTrue(record["source"].endswith(".json"))
            json.loads(record["content"])

    def test_offline_never_probes_network(self):
        with patch.object(verify, "OFFLINE", True), patch("urllib.request.urlopen") as request:
            self.assertFalse(verify.have_network())
            request.assert_not_called()

    def test_strict_skip_is_a_failure(self):
        with patch.object(verify, "STRICT", True), contextlib.redirect_stdout(io.StringIO()):
            verify.skip("missing source", "not available")
        self.assertEqual(verify._RESULTS[0][1], False)
        self.assertEqual(verify._SKIPS, [])

    def test_pinned_schema_urls_use_release_assets(self):
        for url in verify.NIST_SCHEMAS.values():
            self.assertTrue(url.startswith(
                "https://github.com/usnistgov/OSCAL/releases/download/v1.2.1/"))

    def test_background_attribution_is_absent(self):
        self.assertEqual(self.run_checks(verify.check_quotes), [])

    def test_banner_tokens_and_layout_contract(self):
        self.assertEqual(self.run_checks(verify.check_css), [])

    def test_revised_prose_keeps_matrix_and_stakeholder_contracts(self):
        self.assertEqual(self.run_checks(verify.check_slots, verify.check_stakeholders,
                                         verify.check_tradeoffs), [])

    def test_editorial_checks_need_no_external_files_even_in_strict_mode(self):
        with patch.object(verify, "STRICT", True), patch.object(
                extract, "source_path", side_effect=AssertionError("unexpected external source lookup")):
            self.assertEqual(self.run_checks(verify.check_quotes, verify.check_criteria,
                                             verify.check_questions), [])
        self.assertEqual(verify._SKIPS, [])

    def test_background_attribution_is_rejected_in_editorial_data(self):
        node = {"sections": [{"verbatim": "background", "source_document": "draft"}]}
        self.assertEqual(verify.editorial_reference_paths(node),
                         ["$/sections/0/verbatim", "$/sections/0/source_document"])
        self.assertEqual(verify.editorial_reference_paths(
            {"snippet_ids": ["aws-acm2-control"], "id": "paper-cat-1"}), [])

    def test_bundle_contains_only_current_sources(self):
        import bundle

        payload = bundle.collect()
        stored = Path(bundle.OUT).read_text().split("window.TFGBundle = ", 1)[1]
        self.assertEqual(json.loads(stored.rsplit(";", 1)[0]), payload)
        self.assertEqual(len(payload["data/provenance.json"]["snippets"]), 32)

    def test_provenance_and_public_file_links_match_the_source_lock(self):
        import source_inputs

        with open(Path(verify.DATA) / "provenance.json", encoding="utf-8") as stream:
            provenance = json.load(stream)
        self.assertEqual(provenance["source_lock"], "tools/source-lock.json")
        self.assertEqual(provenance["source_inputs"], source_inputs.source_metadata())
        base = source_inputs.public_file_base("catalog-first")
        with open(Path(verify.DATA) / "examples.json", encoding="utf-8") as stream:
            self.assertEqual(json.load(stream)["link_only"]["catalog-first"], base)
        with open(Path(verify.DATA) / "oscal-artifacts.json", encoding="utf-8") as stream:
            publishers = json.load(stream)["publishers"]
        aws = next(p for p in publishers if p["key"] == "catalog-first")
        self.assertTrue(aws["files"])
        self.assertTrue(all(f["href_external"] and f["href"].startswith(base)
                            for f in aws["files"]))

    def test_question_validation_covers_every_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(verify.DATA)
            # Preserve dependencies; mutate only the first question in memory.
            original = json.loads((source / "six-questions.json").read_text())
            original["slots"][0]["question"] = "Not a question"
            (Path(directory) / "six-questions.json").write_text(json.dumps(original))
            with patch.object(verify, "DATA", directory):
                failures = self.run_checks(verify.check_slots)
            self.assertTrue(any("question 1 states its question" in name for name, _ in failures))

    def test_unicode_schema_patterns_are_not_removed(self):
        schema = {"$schema": "http://json-schema.org/draft-07/schema#",
                  "type": "string", "pattern": r"^(\p{L}|_)(\p{L}|\p{N}|[.\-_])*$"}
        validator = schema_validator(schema)
        self.assertTrue(validator.is_valid("étiquette_1"))
        self.assertFalse(validator.is_valid("1-invalid"))
        self.assertFalse(validator.is_valid("invalid token"))
        self.assertIn(r"\p{L}", schema["pattern"])

    def test_schema_required_and_format_checks_remain_enabled(self):
        validator = schema_validator({"type": "object", "required": ["timestamp"],
                                      "properties": {"timestamp": {"type": "string", "format": "date-time"}}})
        self.assertFalse(validator.is_valid({}))
        self.assertFalse(validator.is_valid({"timestamp": "not-a-date"}))
        self.assertTrue(validator.is_valid({"timestamp": "2026-09-09T00:00:00Z"}))

    def test_subject_evidence_matches_the_pinned_schema_contract(self):
        with patch.object(verify, "OFFLINE", True):
            self.assertEqual(self.run_checks(verify.check_schema), [])

    def test_namespace_identifiers_are_not_treated_as_web_pages(self):
        namespace = "https://example.invalid/ns/oscal"
        link = "https://example.invalid/document"
        document = {"props": [{"ns": namespace}], "links": [{"href": link}]}
        self.assertEqual(verify.namespace_urls(document), {namespace})
        self.assertEqual(verify.namespace_urls({"content": json.dumps(document)}), {namespace})
        self.assertEqual(verify.namespace_urls({"href": namespace}), set())


if __name__ == "__main__":
    unittest.main()