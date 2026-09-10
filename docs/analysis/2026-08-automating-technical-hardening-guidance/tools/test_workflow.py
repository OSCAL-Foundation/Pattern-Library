"""Verification workflow contracts; no network, source cache or commits required."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github/workflows/verify-2026-08-hardening-guidance.yml"
# BaseLoader preserves GitHub's `on` key rather than treating it as a YAML 1.1 boolean.
TEXT = WORKFLOW.read_text(encoding="utf-8")
CONFIG = yaml.load(TEXT, Loader=yaml.BaseLoader)
GENERATORS = (
    "extract", "pattern_examples", "copy_examples", "oscal_artifacts",
    "sources_files", "diagrams", "approach_pages", "scenario_page", "bundle",
)
OUTPUTS = (
    "data", "assets/diagrams", "assets/bundle.js", "assessment-first.html",
    "catalog-first.html", "component-first.html", "scenario.html",
)


def steps(job):
    return CONFIG["jobs"][job]["steps"]


def command_step(job, command):
    matches = [step for step in steps(job) if step.get("run") == command]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one {command!r} step in {job}")
    return matches[0]


def generation_step():
    return next(step for step in steps("offline")
                if "python tools/extract.py" in step.get("run", ""))


class WorkflowTests(unittest.TestCase):
    def test_push_pr_manual_and_scheduled_checks_remain(self):
        self.assertEqual(set(CONFIG["on"]), {"push", "pull_request", "workflow_dispatch", "schedule"})
        for event in ("push", "pull_request"):
            self.assertIn(str(WORKFLOW.relative_to(ROOT)), CONFIG["on"][event]["paths"])

    def test_checkout_is_only_the_current_repository(self):
        for job in CONFIG["jobs"]:
            with self.subTest(job=job):
                checkout = [step for step in steps(job)
                            if step.get("uses", "").startswith("actions/checkout@")]
                self.assertEqual(len(checkout), 1)
                self.assertEqual(checkout[0]["with"], {"path": "site"})

    def test_no_external_corpus_variables_or_secrets(self):
        self.assertNotIn("TFG_CORPORA", TEXT)
        self.assertNotIn("${{ vars.", TEXT)
        self.assertNotIn("${{ secrets.", TEXT)
        self.assertEqual(CONFIG["permissions"], {"contents": "read"})
        self.assertEqual(set(CONFIG["env"]), {"SITE"})

    def test_all_regression_suites_run_before_source_preparation(self):
        for job in ("offline", "strict"):
            with self.subTest(job=job):
                tests = next(step for step in steps(job)
                             if "unittest discover" in step.get("run", ""))
                for suite in ("test_verify", "test_source_inputs", "test_workflow"):
                    self.assertIn(f"tools/{suite}.py", tests["run"])
                self.assertIn("-p 'test_*.py'", tests["run"])
                self.assertNotIn("if", tests)
                prepare = command_step(job, "python tools/source_inputs.py --fetch")
                self.assertLess(steps(job).index(tests), steps(job).index(prepare))
                command_step(job, "node tools/bannercheck.js")

    def test_locked_source_check_precedes_every_full_pass(self):
        for job, flag in (("offline", "--offline"), ("strict", "--strict")):
            with self.subTest(job=job):
                prepare = command_step(job, "python tools/source_inputs.py --fetch")
                validate = command_step(job, "python tools/source_inputs.py --check")
                full = command_step(job, f"python tools/verify.py --all {flag}")
                self.assertLess(steps(job).index(prepare), steps(job).index(validate))
                self.assertLess(steps(job).index(validate), steps(job).index(full))
                for step in (prepare, validate, full):
                    self.assertNotIn("if", step)
                    self.assertEqual(step["working-directory"], "${{ env.SITE }}")

    def test_rendering_and_reextraction_checks_remain(self):
        for job in ("offline", "strict"):
            structural = command_step(job,
                "python tools/verify.py --data --css --quotes --bundle --source --pages --offline")
            self.assertNotIn("if", structural)
        command_step("offline", "python tools/verify.py --snippets --offline")

    def test_required_checks_do_not_suppress_failures(self):
        for job in ("offline", "strict"):
            self.assertNotIn("continue-on-error", CONFIG["jobs"][job])
            for step in steps(job):
                with self.subTest(job=job, step=step.get("name", step.get("uses"))):
                    self.assertNotIn("continue-on-error", step)
                    self.assertNotIn("|| true", step.get("run", ""))
                    self.assertNotIn("set +e", step.get("run", ""))

    def test_independent_accessibility_audit_enforces_strict_results(self):
        audit = command_step("strict", "python tools/verify.py --a11y --strict")
        self.assertEqual(audit["if"], "${{ !cancelled() && steps.browser_deps.outcome == 'success' }}")
        install = next(step for step in steps("strict") if step.get("id") == "browser_deps")
        self.assertIn("axe-core puppeteer", install["run"])
        full = command_step("strict", "python tools/verify.py --all --strict")
        self.assertLess(steps("strict").index(install), steps("strict").index(full))
        self.assertLess(steps("strict").index(full), steps("strict").index(audit))

    def test_generated_content_check_covers_every_output_and_generator(self):
        step = generation_step()
        self.assertEqual(step["shell"], "bash")
        self.assertIn("set -euo pipefail", step["run"])
        positions = [step["run"].index(f"python tools/{name}.py") for name in GENERATORS]
        self.assertEqual(positions, sorted(positions))
        for output in OUTPUTS:
            self.assertIn(output, step["run"])
        self.assertIn("git status --porcelain --untracked-files=all", step["run"])

    def test_analysis_commands_use_the_analysis_directory(self):
        for job in ("offline", "strict"):
            for step in steps(job):
                if "tools/" in step.get("run", ""):
                    self.assertEqual(step["working-directory"], "${{ env.SITE }}")

    def run_generation_check(self, changes="", fail_generator=""):
        # Execute the real workflow shell with stubbed generators/Git. No real
        # checkout, source download, index update or commit is performed.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python = root / "python"
            python.write_text(
                '#!/bin/sh\nif [ "$1" = "${FAIL_GENERATOR:-}" ]; then exit 9; fi\nexit 0\n')
            git = root / "git"
            git.write_text(
                '#!/bin/sh\ncase "$1" in\n'
                '  status) printf "%s" "${TEST_CHANGES:-}" ;;\n'
                '  diff) echo diff-called ;;\n'
                '  *) exit 7 ;;\nesac\n')
            python.chmod(0o755)
            git.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                       TEST_CHANGES=changes, FAIL_GENERATOR=fail_generator)
            return subprocess.run(["bash", "-e", "-o", "pipefail", "-c", generation_step()["run"]],
                                  cwd=root, env=env, capture_output=True, text=True, check=False)

    def test_unchanged_generation_passes(self):
        result = self.run_generation_check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_modified_deleted_staged_and_untracked_outputs_fail(self):
        for change in (" M data/provenance.json", " D scenario.html",
                       "A  data/new.json", "?? data/new.json"):
            with self.subTest(change=change):
                result = self.run_generation_check(changes=change)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(change, result.stdout)
                self.assertIn("::error::Generated files differ", result.stdout)

    def test_generator_failure_stops_before_diff(self):
        result = self.run_generation_check(fail_generator="tools/diagrams.py")
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertNotIn("diff-called", result.stdout)


if __name__ == "__main__":
    unittest.main()