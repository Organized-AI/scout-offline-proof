import errno
import json
import platform
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from proof.core import ROOT, evaluate, parse_answer, preflight, read_corpus, retrieve, run
from proof.runner import harness_answer, network_evidence
from proof.suites import load_suite


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.corpus = read_corpus(ROOT / "data/fieldkit")
        self.tasks = load_suite("fieldkit-qa")["tasks"]

    def check(self, task, output):
        return evaluate(task, json.dumps(output), retrieve(task["question"], self.corpus))

    def test_correct_facts_have_exact_source_evidence(self):
        for task in self.tasks:
            result = evaluate(task, harness_answer(task), retrieve(task["question"], self.corpus))
            self.assertTrue(result["passed"], result)

    def test_invented_quotation_fails(self):
        output = json.loads(harness_answer(self.tasks[0]))
        output["quote"] = "The answer is 72 hours according to a made-up policy."
        self.assertFalse(self.check(self.tasks[0], output)["passed"])

    def test_correct_fact_with_wrong_document_fails(self):
        output = json.loads(harness_answer(self.tasks[0]))
        output["source"] = "02-integrity.md"
        self.assertFalse(self.check(self.tasks[0], output)["passed"])

    def test_wrong_fact_with_real_quote_fails(self):
        output = json.loads(harness_answer(self.tasks[0]))
        output["answer"] = "24 hours"
        self.assertFalse(self.check(self.tasks[0], output)["passed"])

    def test_irrelevant_quote_cannot_support_correct_answer(self):
        output = json.loads(harness_answer(self.tasks[0]))
        output["quote"] = "FieldKit is a fictional field-research team used only for this demonstration."
        self.assertFalse(self.check(self.tasks[0], output)["passed"])

    def test_unanswerable_question_requires_exact_abstention(self):
        task = self.tasks[-1]
        for output in [{"answer": "$20", "source": None, "quote": None},
                       {"answer": "NOT_FOUND", "source": "03-operations.md", "quote": None}]:
            self.assertFalse(self.check(task, output)["passed"])

    def test_extra_or_trailing_json_rejected(self):
        for text in ['{"answer":"x","source":null,"quote":null,"extra":true}',
                     '{"answer":"x","source":null,"quote":null} {"answer":"second"}']:
            with self.assertRaises(ValueError):
                parse_answer(text)

    def test_gold_answers_are_not_sent_to_runner(self):
        # The runner protocol is task ID, question and retrieved documents, never expected facts.
        from proof.runner import messages
        task = {"id": "test", "question": "How long?", "documents": self.corpus[:1]}
        prompt = messages(task)
        self.assertEqual(len(prompt), 2)
        self.assertIn("SOURCE: 01-retention.md", prompt[1]["content"])
        self.assertNotIn('"expected"', prompt[1]["content"])


class ReadinessTests(unittest.TestCase):
    def config(self, model):
        return {"model": str(model), "python": sys.executable, "documents": str(ROOT / "data/fieldkit"), "mode": "mlx"}

    def test_missing_model_is_actionable(self):
        checks = preflight(self.config("/nonexistent/scout-model"))
        bad = next(c for c in checks if c["label"] == "Local model folder")
        self.assertFalse(bad["passed"])
        self.assertIn("Connect", bad["remedy"])

    def test_missing_tokenizer_and_shard_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "config.json").write_text("{}")
            (p / "model.safetensors").write_bytes(b"not-real-weights")
            (p / "model.safetensors.index.json").write_text(json.dumps({"weight_map": {"w": "missing-shard.safetensors"}}))
            checks = preflight(self.config(p))
            self.assertFalse(next(c for c in checks if c["label"] == "Tokenizer")["passed"])
            self.assertFalse(next(c for c in checks if c["label"] == "Model weights")["passed"])

    def test_missing_documents_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                read_corpus(tmp)

    def test_connection_refused_is_not_network_isolation(self):
        with patch("proof.runner.socket.socket") as fake:
            fake.return_value.__enter__.return_value.connect.side_effect = OSError(errno.ECONNREFUSED, "Connection refused")
            evidence = network_evidence(12345)
        self.assertFalse(evidence["enforced"])

    def test_timeouts_are_not_network_isolation(self):
        with patch("proof.runner.socket.socket") as fake:
            fake.return_value.__enter__.return_value.connect.side_effect = socket.timeout("timed out")
            self.assertFalse(network_evidence(12345)["enforced"])

    def test_only_permission_denial_counts(self):
        with patch("proof.runner.socket.socket") as fake:
            fake.return_value.__enter__.return_value.connect.side_effect = PermissionError(errno.EPERM, "Operation not permitted")
            self.assertTrue(network_evidence(12345)["enforced"])


@unittest.skipUnless(platform.system() == "Darwin", "Real OS sandbox test requires macOS")
class SupervisorTests(unittest.TestCase):
    def config(self):
        return {"model": "", "python": sys.executable, "documents": str(ROOT / "data/fieldkit"), "mode": "harness"}

    def test_real_sandbox_and_harness_never_claim_model_proof(self):
        report = run(self.config())
        self.assertEqual(report["status"], "harness_passed", report.get("error"))
        self.assertTrue(report["network"]["witness_reachable_before_sandbox"])
        self.assertTrue(report["network"]["enforced"])
        self.assertEqual(len(report["network"]["probes"]), 4)
        self.assertEqual(len(report["answers"]), 3)
        self.assertTrue(all(s["status"] == "passed" for s in report["stages"]))

    def test_unsupported_os_fails_closed(self):
        with patch("proof.core.platform.system", return_value="Unsupported"):
            report = run(self.config())
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["answers"], [])

    def test_changed_corpus_cannot_pass_fixed_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in (ROOT / "data/fieldkit").glob("*.md"):
                (Path(tmp) / path.name).write_text(path.read_text().replace("72 hours", "24 hours"))
            config = {**self.config(), "documents": tmp}
            report = run(config)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["answers"][0]["passed"])
        self.assertTrue(report["network"]["enforced"])

    def test_timeout_is_a_failure(self):
        report = run(self.config(), timeout=0)
        self.assertEqual(report["status"], "failed")
        self.assertIn("limit", report["error"])


if __name__ == "__main__":
    unittest.main()
