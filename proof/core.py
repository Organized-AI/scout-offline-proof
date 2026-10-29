"""Readiness checks, evidence, and a fail-closed offline workflow supervisor."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import queue
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .suites import HARNESS_CASES, catalog, evaluate_structured, load_suite, parse_json, prepare_task, summary

ROOT = Path(__file__).resolve().parents[1]
SANDBOX = "/usr/bin/sandbox-exec"
POLICY = "(version 1)(allow default)(deny network*)"
STAGES = [("preflight", "Check local setup"), ("manifest", "Fingerprint the inputs"),
          ("isolation", "Block and test network access"), ("workflow", "Run acceptance tasks"),
          ("quality", "Verify outputs and contracts")]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_corpus(directory):
    directory = Path(directory).expanduser().resolve()
    files = sorted(p for p in directory.glob("*") if p.suffix.lower() in {".md", ".txt"} and p.is_file())
    if not files:
        raise ValueError("No UTF-8 .md or .txt documents found in this folder.")
    if len(files) > 100 or sum(p.stat().st_size for p in files) > 2_000_000:
        raise ValueError("This release supports at most 100 documents / 2 MB of text.")
    return [{"source": p.name, "text": p.read_text(encoding="utf-8"), "sha256": digest(p)} for p in files]


def terms(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def retrieve(question, corpus, limit=2):
    """Deterministic term-overlap retrieval; no embedding service or hidden download."""
    stop = {"a", "the", "is", "of", "to", "in", "for", "it", "what", "does", "which", "how"}
    query = set(terms(question)) - stop
    ranked = sorted(corpus, key=lambda d: (-len(query & set(terms(d["text"]))), d["source"]))
    return [{"source": d["source"], "text": d["text"][:7000]} for d in ranked[:limit]]


def parse_answer(output):
    output = re.sub(r"<think>.*?</think>", "", output, flags=re.S).strip()
    if "</think>" in output:
        output = output.split("</think>")[-1].strip()
    if output.startswith("```"):
        output = re.sub(r"^```(?:json)?\s*|\s*```$", "", output).strip()
    value = parse_json(output)
    if not isinstance(value, dict) or not isinstance(value.get("answer"), str):
        raise ValueError("Expected a JSON object with an answer string.")
    if set(value) != {"answer", "source", "quote"}:
        raise ValueError("Expected exactly answer, source, and quote fields.")
    return value


def normalize(text):
    return " ".join(terms(text))


def evaluate(task, output, retrieved):
    if task.get("kind", "grounded_qa") != "grounded_qa":
        return evaluate_structured(task, output)
    checks = []
    parsed = None
    try:
        parsed = parse_answer(output)
        checks.append({"label": "Structured response", "passed": True})
        if not task["answerable"]:
            passed = parsed == {"answer": "NOT_FOUND", "source": None, "quote": None}
            checks.append({"label": "Abstains when the documents do not answer", "passed": passed})
        else:
            source = next((d for d in retrieved if d["source"] == parsed["source"]), None)
            quote = parsed.get("quote")
            cited = source is not None and source["source"] == task["source"]
            exact_quote = cited and isinstance(quote, str) and len(quote.strip()) >= 12 and quote in source["text"]
            checks.extend([
                {"label": "Cites the expected retrieved document", "passed": cited},
                {"label": "Quotation exists verbatim in that document", "passed": bool(exact_quote)},
                {"label": "Answer contains the expected fact", "passed": all(normalize(s) in normalize(parsed["answer"]) for s in task["expected"])},
                {"label": "Quotation supports the expected fact", "passed": isinstance(quote, str) and all(normalize(s) in normalize(quote) for s in task["expected"])},
            ])
    except (ValueError, TypeError, KeyError) as exc:
        checks.append({"label": "Structured response", "passed": False, "detail": str(exc)})
    return {"passed": all(c["passed"] for c in checks), "parsed": parsed, "checks": checks}


def machine():
    result = {"host": socket.gethostname(), "os": platform.platform(), "architecture": platform.machine()}
    if platform.system() == "Darwin":
        for field, key in [("memory_bytes", "hw.memsize"), ("chip", "machdep.cpu.brand_string")]:
            v = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True).stdout.strip()
            result[field] = int(v) if v.isdigit() else v
    return result


def discover():
    models = []
    for base in [Path("/Volumes/A1/stash/models/mlx"), ROOT / ".proof/models"]:
        if base.exists():
            for p in sorted(base.iterdir()):
                if p.is_dir() and (p / "config.json").is_file():
                    if re.search(r"embed|rerank|whisper|tts|guard|clef|kev|jev|ocr|vl-|vlm|tars|privacy", p.name, re.I):
                        continue
                    models.append({"name": p.name, "path": str(p), "bytes": sum(f.stat().st_size for f in p.glob("*.safetensors"))})
    # Prefer the small, non-thinking instruct model; list alternatives by file size.
    models.sort(key=lambda m: ("Qwen3-4B-Instruct-2507" not in m["name"], m["bytes"]))
    candidates = [Path(sys.executable), ROOT / ".venv/bin/python"]
    candidates += sorted((Path.home() / ".nvme-stash/venvs").glob("*/bin/python"))
    runtime = str(Path(sys.executable))
    for p in candidates:
        if p.exists():
            r = subprocess.run([str(p), "-c", "import importlib.util; print(bool(importlib.util.find_spec('mlx_lm')))"], capture_output=True, text=True, timeout=10)
            if r.stdout.strip() == "True":
                runtime = str(p)
                break
    return {"machine": machine(), "models": models, "suites": catalog(),
            "defaults": {"model": models[0]["path"] if models else "", "python": runtime,
                         "documents": str(ROOT / "data/fieldkit"), "mode": "mlx",
                         "suite": "fieldkit-qa", "harness_case": "valid"}}


def model_files(model):
    files = [p for p in model.iterdir() if p.is_file() and not p.name.startswith(".")
             and (p.suffix in {".json", ".safetensors", ".jinja", ".txt", ".model"})]
    return sorted(files)


def preflight(config):
    checks = []
    def add(label, passed, detail, remedy=""):
        checks.append({"label": label, "passed": bool(passed), "detail": detail, "remedy": remedy if not passed else ""})
    add("OS network sandbox", platform.system() == "Darwin" and Path(SANDBOX).is_file(),
        "macOS sandbox-exec with a network-deny policy", "Run this release on macOS with sandbox-exec available.")
    python = Path(config["python"]).expanduser().absolute()
    add("Python interpreter", python.is_file() and os.access(python, os.X_OK), str(python), "Choose an executable Python 3.10+ interpreter.")
    suite = None
    try:
        suite = load_suite(config.get("suite", "fieldkit-qa"))
        add("Task suite", True, f"{suite['name']} · {len(suite['tasks'])} tasks")
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        add("Task suite", False, str(exc), "Choose a bundled suite or a valid local suite JSON file. See README for its format.")
    add("Harness scenario", config.get("harness_case", "valid") in HARNESS_CASES,
        config.get("harness_case", "valid"), "Choose valid, wrong-answer, or malformed-json.")
    try:
        if suite and any(t["kind"] == "grounded_qa" for t in suite["tasks"]):
            docs = read_corpus(config["documents"])
            add("Local documents", True, f"{len(docs)} UTF-8 documents; no remote sources")
        elif suite:
            add("Task inputs", True, "Text inputs are bundled in the suite; no document directory is required.")
    except (OSError, ValueError) as exc:
        add("Local documents", False, str(exc), "Select a folder containing readable .md or .txt documents.")
    if config["mode"] == "mlx":
        model = Path(config["model"]).expanduser().resolve()
        exists = model.is_dir()
        add("Local model folder", exists, str(model), "Connect the A1 drive or select an existing local MLX model folder.")
        for name, ok, remedy in [
            ("Model configuration", (model / "config.json").is_file(), "Restore config.json from the same model revision."),
            ("Tokenizer", any((model / f).is_file() for f in ["tokenizer.json", "tokenizer.model"]), "Restore tokenizer.json or tokenizer.model before running offline."),
        ]:
            add(name, ok, "Found locally" if ok else "Required file is missing", remedy)
        weights = list(model.glob("*.safetensors")) if exists else []
        ok = bool(weights) and all(p.stat().st_size > 0 for p in weights)
        index = model / "model.safetensors.index.json"
        if index.exists():
            try:
                shards = set(json.loads(index.read_text())["weight_map"].values())
                ok = ok and bool(shards) and all((model / s).is_file() and (model / s).resolve().is_relative_to(model) for s in shards)
            except (OSError, ValueError, KeyError, TypeError):
                ok = False
        add("Model weights", ok, f"{sum(p.stat().st_size for p in weights) / 1e9:.2f} GB on disk", "Restore all nonempty safetensors shards referenced by the model index.")
        if python.is_file():
            try:
                r = subprocess.run([str(python), "-c", "import sys,importlib.util; print(sys.version_info >= (3,10) and bool(importlib.util.find_spec('mlx_lm')))"], capture_output=True, text=True, timeout=15)
                add("MLX language-model runtime", r.returncode == 0 and r.stdout.strip() == "True", str(python), "Use a Python 3.10+ environment with mlx-lm installed. Setup happens before the offline run.")
            except (OSError, subprocess.TimeoutExpired) as exc:
                add("MLX language-model runtime", False, str(exc), "Choose a working MLX Python environment.")
        memory = machine().get("memory_bytes", 0)
        if isinstance(memory, int) and memory:
            add("Model size budget", sum(p.stat().st_size for p in weights) < memory * .7,
                "Weights must use less than 70% of physical RAM; runtime overhead is additional.", "Choose a smaller model; this is a conservative size check, not a peak-memory measurement.")
    return checks


def run(config, publish=lambda r: None, timeout=300):
    """The coordinator is online; the actual workflow runs entirely in a denied subprocess."""
    config = {"suite": "fieldkit-qa", "harness_case": "valid", **config, "mode": config.get("mode", "mlx")}
    if config["mode"] not in {"mlx", "harness"}:
        raise ValueError("Unknown runtime mode")
    report = {"schema_version": 2, "id": str(uuid.uuid4()), "started_at": now(), "status": "running",
              "mode": config["mode"], "config": config, "machine": machine(), "checks": [], "answers": [],
              "network": {}, "inputs": {}, "stages": [{"id": k, "label": label, "status": "pending"} for k, label in STAGES],
              "limitations": ["Network denial covers the runner process and its descendants, not the entire Mac or the dashboard.",
                "Passing a configured task suite does not certify general model accuracy or agent safety.",
                "Fact checks and exact quotations do not validate every possible extra claim in an answer.",
                "Tool-call outputs are checked against contracts; proposed tools are not executed.",
                "Input hashes identify this run's local files; this is not a signed third-party attestation."]}
    started = time.monotonic()
    current = "preflight"
    proc = None
    reader = None
    def emit():
        report["elapsed_s"] = round(time.monotonic() - started, 2)
        publish(json.loads(json.dumps(report)))
    def stage(name, status):
        nonlocal current
        current = name
        for s in report["stages"]:
            if s["id"] == name:
                s["status"] = status
        emit()
    try:
        stage("preflight", "running")
        report["checks"] = preflight(config)
        if not all(c["passed"] for c in report["checks"]):
            raise ValueError("Setup needs attention. Resolve the failed checks, then run again.")
        suite = load_suite(config["suite"])
        report["suite"] = summary(suite)
        report["generation"] = {"max_tokens": suite["max_tokens"], "temperature": 0, "seed": 0}
        stage("preflight", "passed")
        stage("manifest", "running")
        tasks = suite["tasks"]
        needs_corpus = any(t["kind"] == "grounded_qa" for t in tasks)
        corpus = read_corpus(config["documents"]) if needs_corpus else []
        prepared = [prepare_task(t, retrieve(t["question"], corpus, suite["retrieval_limit"]) if t["kind"] == "grounded_qa" else [], config["mode"]) for t in tasks]
        report["inputs"] = {"documents": [{k: d[k] for k in ["source", "sha256"]} for d in corpus],
                            "suite_files": suite["files"],
                            "task_bank_sha256": hashlib.sha256(json.dumps(tasks, sort_keys=True).encode()).hexdigest(),
                            "application": {p.name: digest(p) for p in sorted((ROOT / "proof").glob("*.py"))}, "model_files": []}
        fingerprints = []
        if config["mode"] == "mlx":
            model = Path(config["model"]).expanduser().resolve()
            for p in model_files(model):
                stat = p.stat()
                report["inputs"]["model_files"].append({"file": p.name, "bytes": stat.st_size, "sha256": digest(p)})
                fingerprints.append((p, stat.st_size, stat.st_mtime_ns))
        stage("manifest", "passed")
        stage("isolation", "running")
        with socket.socket() as witness:
            witness.bind(("127.0.0.1", 0))
            witness.listen(8)
            port = witness.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                report["network"]["witness_reachable_before_sandbox"] = True
            payload = {"model": str(Path(config["model"]).expanduser().resolve()) if config["model"] else "",
                       "mode": config["mode"], "witness_port": port, "tasks": prepared,
                       "max_tokens": suite["max_tokens"], "harness_case": config["harness_case"]}
            env = {k: os.environ[k] for k in ["PATH", "HOME", "TMPDIR", "LANG"] if k in os.environ}
            env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1")
            command = [SANDBOX, "-p", POLICY, str(Path(config["python"]).expanduser().absolute()), "-u", "-m", "proof.runner"]
            report["network"]["policy"] = POLICY
            report["network"]["policy_sha256"] = hashlib.sha256(POLICY.encode()).hexdigest()
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, start_new_session=True)
            proc.stdin.write(json.dumps(payload))
            proc.stdin.close()
            lines = queue.Queue()
            def read_lines():
                try:
                    for line in proc.stdout:
                        lines.put(line)
                finally:
                    lines.put(None)
            reader = threading.Thread(target=read_lines, daemon=True)
            reader.start()
            done = False
            tail = []
            while True:
                if time.monotonic() - started > timeout:
                    raise TimeoutError(f"Workflow exceeded its {timeout}-second limit. Try a smaller model.")
                try:
                    line = lines.get(timeout=.25)
                except queue.Empty:
                    continue
                if line is None:
                    break
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict) or "event" not in event:
                        raise ValueError()
                except ValueError:
                    tail.append(line.strip()[:500]); tail = tail[-5:]
                    continue
                kind = event["event"]
                if kind == "network":
                    report["network"].update(event["evidence"])
                    if not event["evidence"]["enforced"]:
                        raise ValueError("Network enforcement probes failed. Inference was refused.")
                    stage("isolation", "passed")
                    stage("workflow", "running")
                elif kind == "loaded":
                    report["runtime"] = event
                    emit()
                elif kind == "answer":
                    if event["id"] in {a["id"] for a in report["answers"]}:
                        raise ValueError("Runner returned a duplicate task result.")
                    task = next(t for t in tasks if t["id"] == event["id"])
                    docs = next(t["documents"] for t in prepared if t["id"] == event["id"])
                    report["answers"].append({"id": task["id"], "kind": task["kind"], "suite_id": task["suite_id"],
                                              "question": task["question"], "input": task.get("input"),
                                              "expected": task["expected"], "raw": event["output"],
                                              "seconds": event["seconds"], "retrieved_sources": [d["source"] for d in docs],
                                              **evaluate(task, event["output"], docs)})
                    emit()
                elif kind == "error":
                    raise ValueError(event["message"])
                elif kind == "done":
                    done = True
            code = proc.wait(timeout=5)
            if code or not done or len(report["answers"]) != len(tasks) or not report["network"].get("enforced"):
                raise ValueError(f"Runner did not finish a complete enforced workflow (exit {code}). " + " ".join(tail))
        if any(p.stat().st_size != size or p.stat().st_mtime_ns != mtime for p, size, mtime in fingerprints):
            raise ValueError("Model files changed during the run; the evidence is invalid. Run again with stable files.")
        if any(digest(f["path"]) != f["sha256"] for f in suite["files"]):
            raise ValueError("Task suite changed during the run; run again with stable inputs.")
        if needs_corpus and read_corpus(config["documents"]) != corpus:
            raise ValueError("Documents changed during the run; run again with stable inputs.")
        stage("workflow", "passed")
        stage("quality", "running")
        quality = all(a["passed"] for a in report["answers"])
        stage("quality", "passed" if quality else "failed")
        report["status"] = ("verified" if config["mode"] == "mlx" else "harness_passed") if quality else "failed"
        if not quality:
            report["error"] = "The workflow completed offline, but one or more answers failed the quality checks."
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        stage(current, "failed")
    finally:
        if proc is not None and proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
        if reader is not None:
            reader.join(timeout=3)
        if proc is not None:
            if proc.stdout:
                proc.stdout.close()
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
        report["finished_at"] = now()
        emit()
    return report
