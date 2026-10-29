import copy
import platform
import sys
import unittest
from unittest.mock import patch

from proof.core import ROOT, evaluate, read_corpus, retrieve, run
from proof.runner import harness_answer
from proof.suites import load_suite, prepare_task, replay_tasks


class ReplayCaseTests(unittest.TestCase):
    def test_known_decisions_cover_each_validator(self):
        tasks = replay_tasks(load_suite("all")["tasks"])
        self.assertEqual(len(tasks), 63)
        self.assertEqual(len({t["id"] for t in tasks}), 63)
        self.assertEqual(sum(t["expected_accept"] for t in tasks), 10)
        corpus = read_corpus(ROOT / "data/fieldkit")
        for task in tasks:
            with self.subTest(case=task["id"]):
                docs = retrieve(task["question"], corpus) if task["kind"] == "grounded_qa" else []
                output = harness_answer(prepare_task(task, docs, "harness"), "failure-replay")
                self.assertEqual(evaluate(task, output, docs)["passed"], task["expected_accept"])
                model_payload = prepare_task(task, docs, "mlx")
                self.assertNotIn("fixture_output", model_payload)
                self.assertNotIn("expected_accept", model_payload)

    def test_wrong_tool_case_can_satisfy_schema_and_still_fail_choice(self):
        task = next(t for t in replay_tasks(load_suite("tool-routing")["tasks"]) if t["id"] == "bundle-check::wrong-tool")
        result = evaluate(task, task["fixture_output"], [])
        self.assertTrue(next(c["passed"] for c in result["checks"] if c["label"] == "Tool is allowed"))
        self.assertTrue(next(c["passed"] for c in result["checks"] if c["label"] == "Arguments match the tool contract"))
        self.assertFalse(result["passed"])

    def test_replay_does_not_mutate_the_configured_fixtures(self):
        tasks = load_suite("all")["tasks"]
        original = copy.deepcopy(tasks)
        replay_tasks(tasks)
        self.assertEqual(tasks, original)


@unittest.skipUnless(platform.system() == "Darwin", "Real OS sandbox requires macOS")
class ReplayIntegrationTests(unittest.TestCase):
    def config(self, suite="tool-routing"):
        return {"mode": "harness", "python": sys.executable, "model": "", "documents": str(ROOT / "data/fieldkit"),
                "suite": suite, "harness_case": "failure-replay"}

    def test_agent_replay_has_four_valid_and_twenty_eight_invalid_cases(self):
        report = run(self.config())
        self.assertEqual(report["status"], "harness_passed", report.get("error"))
        self.assertEqual(report["suite"]["task_count"], 4)
        self.assertEqual(report["harness"], {"case_count": 32, "checked": 32, "matched": 32,
                         "valid_cases": 4, "valid_accepted": 4, "invalid_cases": 28, "invalid_rejected": 28,
                         "false_accepts": 0, "false_rejects": 0})
        self.assertTrue(report["network"]["enforced"])
        self.assertTrue(all(a["passed"] for a in report["answers"]))
        self.assertEqual(sum(a["validator_accepted"] for a in report["answers"]), 4)

    def test_a_broken_evaluator_cannot_pass_replay(self):
        for accepted, field, count in [(True, "false_accepts", 53), (False, "false_rejects", 10)]:
            with self.subTest(accepted=accepted):
                verdict = {"passed": accepted, "parsed": None, "checks": [{"label": "Deliberately broken evaluator", "passed": accepted}]}
                with patch("proof.core.evaluate", side_effect=lambda *_: copy.deepcopy(verdict)):
                    report = run(self.config("all"))
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["harness"][field], count)
                self.assertIn("evaluator", report["error"])


if __name__ == "__main__":
    unittest.main()
