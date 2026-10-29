import copy
import json
import platform
import sys
import tempfile
import unittest
from pathlib import Path

from proof.core import ROOT, evaluate, preflight, read_corpus, retrieve, run
from proof.runner import harness_answer, messages
from proof.suites import load_suite, prepare_task, validate_suite


class SuiteTests(unittest.TestCase):
    def setUp(self):
        self.suite = load_suite("all")
        self.corpus = read_corpus(ROOT / "data/fieldkit")

    def test_all_fixtures_and_fault_scenarios_are_scored(self):
        self.assertEqual(len(self.suite["tasks"]), 10)
        for task in self.suite["tasks"]:
            docs = retrieve(task["question"], self.corpus) if task["kind"] == "grounded_qa" else []
            for case in ["valid", "wrong-answer", "malformed-json"]:
                with self.subTest(task=task["id"], case=case):
                    result = evaluate(task, harness_answer(task, case), docs)
                    self.assertEqual(result["passed"], case == "valid", result)

    def test_model_protocol_never_contains_grading_values_or_fixtures(self):
        for original in self.suite["tasks"]:
            task = {**original, "fixture": {"hidden": "FIXTURE_SENTINEL"}, "expected": "GRADING_SENTINEL"}
            if "tools" in task:
                task["tools"] = [{**t, "expected": "GRADING_SENTINEL"} for t in task["tools"]]
            payload = prepare_task(task, [], "mlx")
            self.assertNotIn("expected", payload)
            self.assertNotIn("fixture", payload)
            prompt = json.dumps(messages(payload))
            self.assertNotIn("GRADING_SENTINEL", prompt)
            self.assertNotIn("FIXTURE_SENTINEL", prompt)
            self.assertIn("fixture", prepare_task(task, [], "harness"))

    def test_strict_json_types_keys_and_values(self):
        task = load_suite("extraction")["tasks"][0]
        correct = task["expected"]
        mutations = [
            {**correct, "sensor_count": "12"}, {**correct, "sensor_count": 12.0},
            {**correct, "verified": 1}, {**correct, "extra": True},
            {"bundle_id": "FK-204", "sensor_count": 12}, {**correct, "sensor_count": 13},
        ]
        for value in mutations:
            self.assertFalse(evaluate(task, json.dumps(value), [])["passed"], value)
        for raw in ['[]', 'null', 'true', 'NaN', '{"bundle_id":"x","bundle_id":"FK-204","sensor_count":12,"verified":true}',
                    '```json\n' + json.dumps(correct) + '\n```', json.dumps(correct) + ' extra']:
            self.assertFalse(evaluate(task, raw, [])["passed"], raw)

    def test_null_is_distinct_from_missing_or_empty(self):
        task = load_suite("extraction")["tasks"][1]
        for value in ["null", "", "Jordan"]:
            self.assertFalse(evaluate(task, json.dumps({**task["expected"], "owner": value}), [])["passed"])

    def test_tool_names_and_arguments_are_both_enforced(self):
        task = load_suite("tool-routing")["tasks"][1]
        bad = [
            {"tool": "upload_files", "arguments": {}},
            {"tool": "verify_checksum", "arguments": {"file": "other.zip", "algorithm": "SHA-256"}},
            {"tool": "verify_checksum", "arguments": {"file": "field-bundle-204.zip", "algorithm": "SHA-256", "shell": "rm -rf /"}},
            {"tool": "verify_checksum", "arguments": {"file": 204, "algorithm": "SHA-256"}},
            {"tool": "verify_checksum", "arguments": None},
        ]
        for output in bad:
            self.assertFalse(evaluate(task, json.dumps(output), [])["passed"], output)

    def test_invalid_suites_fail_validation(self):
        original = load_suite("extraction")
        variants = []
        for key, value in [("schema_version", 2), ("tasks", []), ("max_tokens", 1000000), ("max_tokens", True), ("retrieval_limit", 0)]:
            variants.append({**copy.deepcopy(original), key: value})
        duplicate = copy.deepcopy(original)
        duplicate["tasks"][1]["id"] = duplicate["tasks"][0]["id"]
        variants.append(duplicate)
        for key, value in [("kind", "python_eval"), ("fields", {"x": "object"}), ("expected", {}), ("fixture", None)]:
            malformed = copy.deepcopy(original)
            malformed["tasks"][0][key] = value
            variants.append(malformed)
        for suite in variants:
            with self.assertRaises(ValueError):
                validate_suite(suite)

    def test_custom_suite_path_and_size_limit(self):
        with self.assertRaisesRegex(ValueError, "Choose a suite"):
            load_suite("")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "custom.json"
            suite = load_suite("extraction")
            suite["id"] = "my-suite"
            path.write_text(json.dumps(suite))
            loaded = load_suite(str(path))
            self.assertEqual(loaded["id"], "my-suite")
            self.assertEqual(loaded["files"][0]["path"], str(path.resolve()))
            path.write_text(" " * 512001)
            with self.assertRaisesRegex(ValueError, "512 KB"):
                load_suite(str(path))


@unittest.skipUnless(platform.system() == "Darwin", "Real OS sandbox requires macOS")
class SuiteIntegrationTests(unittest.TestCase):
    def config(self, **kwargs):
        return {"mode": "harness", "python": sys.executable, "model": "", "documents": str(ROOT / "data/fieldkit"), "suite": "all", **kwargs}

    def test_all_suites_under_real_network_denial_and_negative_cases(self):
        for case in ["valid", "wrong-answer", "malformed-json"]:
            with self.subTest(case=case):
                report = run(self.config(harness_case=case))
                self.assertEqual(report["status"], "harness_passed" if case == "valid" else "failed", report.get("error"))
                self.assertEqual(len(report["answers"]), 10)
                self.assertEqual(report["suite"]["task_count"], 10)
                self.assertEqual(sum(a["passed"] for a in report["answers"]), 10 if case == "valid" else 0)
                self.assertTrue(report["network"]["enforced"])
                self.assertEqual(len(report["inputs"]["suite_files"]), 3)

    def test_inline_tasks_do_not_require_document_directory(self):
        report = run(self.config(suite="extraction", documents="/nonexistent/documents"))
        self.assertEqual(report["status"], "harness_passed", report.get("error"))
        self.assertEqual(report["inputs"]["documents"], [])

    def test_missing_custom_suite_is_actionable_and_fails_closed(self):
        config = self.config(suite="/nonexistent/custom-suite.json")
        checks = preflight(config)
        bad = next(c for c in checks if c["label"] == "Task suite")
        self.assertFalse(bad["passed"])
        self.assertIn("JSON", bad["remedy"])
        report = run(config)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["answers"], [])
        self.assertEqual(report["network"], {})

    def test_editing_suite_during_run_invalidates_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "custom.json"
            path.write_text(json.dumps(load_suite("extraction")))
            def edit(report):
                if any(s["id"] == "workflow" and s["status"] == "running" for s in report["stages"]):
                    path.write_text(path.read_text() + " ")
            report = run(self.config(suite=str(path)), publish=edit)
            self.assertEqual(report["status"], "failed")
            self.assertIn("suite changed", report["error"])


if __name__ == "__main__":
    unittest.main()
