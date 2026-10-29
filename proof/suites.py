"""Declarative acceptance suites. No executable validators or remote resources."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILTINS = ("fieldkit-qa", "extraction", "tool-routing")
KINDS = {"grounded_qa", "json_exact", "tool_call"}
HARNESS_CASES = {"valid", "wrong-answer", "malformed-json", "failure-replay"}
TYPES = {"string", "integer", "number", "boolean", "null"}


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _text(value, limit=12000):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}", value)


def matches_type(value, spec):
    checks = {
        "string": isinstance(value, str),
        "integer": type(value) is int,
        "number": type(value) is int or (type(value) is float and math.isfinite(value)),
        "boolean": type(value) is bool,
        "null": value is None,
    }
    return any(checks.get(t, False) for t in spec.split("|"))


def _validate_fields(fields, label):
    _require(isinstance(fields, dict) and len(fields) <= 30, f"{label}: expected an object of field names and types.")
    for name, spec in fields.items():
        _require(_identifier(name), f"{label}: invalid field name.")
        _require(isinstance(spec, str) and set(spec.split("|")) <= TYPES,
                 f"{label}.{name}: use string, integer, number, boolean, null, or a union such as string|null.")


def fields_match(value, fields):
    return (isinstance(value, dict) and set(value) == set(fields)
            and all(matches_type(value[k], spec) for k, spec in fields.items()))


def exact_equal(a, b):
    """JSON equality without Python's True == 1 or 1 == 1.0 coercion."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(exact_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact_equal(x, y) for x, y in zip(a, b))
    return a == b


def parse_json(output):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"Invalid JSON constant: {value}")
    return json.loads(output, object_pairs_hook=unique, parse_constant=invalid)


def validate_suite(suite):
    _require(isinstance(suite, dict) and suite.get("schema_version") == 1, "Suite must be an object with schema_version: 1.")
    _require(_identifier(suite.get("id")) and _text(suite.get("name"), 160), "Suite needs an id and name.")
    _require(_text(suite.get("description"), 2000), "Suite needs a description.")
    tasks = suite.get("tasks")
    _require(isinstance(tasks, list) and 1 <= len(tasks) <= 50, "A suite must contain 1–50 tasks.")
    for key, default, low, high in [("max_tokens", 200, 32, 1024), ("retrieval_limit", 2, 1, 5)]:
        value = suite.setdefault(key, default)
        _require(type(value) is int and low <= value <= high, f"{key} must be an integer from {low} to {high}.")
    ids = set()
    for task in tasks:
        _require(isinstance(task, dict), "Each task must be an object.")
        name = task.get("id")
        _require(_identifier(name) and name not in ids, "Task IDs must be valid and unique.")
        ids.add(name)
        kind = task.get("kind")
        _require(kind in KINDS, f"{name}: kind must be grounded_qa, json_exact, or tool_call.")
        _require(_text(task.get("question"), 4000), f"{name}: a question or instruction is required.")
        _require(isinstance(task.get("fixture"), dict), f"{name}: provide an explicit JSON fixture for harness checks.")
        if kind == "grounded_qa":
            _require(type(task.get("answerable")) is bool, f"{name}: answerable must be a boolean.")
            expected = task.get("expected")
            _require(isinstance(expected, list) and all(_text(s, 300) for s in expected), f"{name}: expected must be a list of facts.")
            if task["answerable"]:
                source = task.get("source")
                _require(bool(expected) and _text(source, 200) and Path(source).name == source,
                         f"{name}: answerable tasks need expected facts and a source filename.")
            else:
                _require(not expected and task.get("source") is None, f"{name}: unanswerable tasks use expected: [] and source: null.")
        else:
            _require(_text(task.get("input")), f"{name}: provide input text.")
            if kind == "json_exact":
                _validate_fields(task.get("fields"), name)
                _require(bool(task["fields"]) and fields_match(task.get("expected"), task["fields"]),
                         f"{name}: expected must exactly match the declared fields and types.")
            else:
                tools = task.get("tools")
                _require(isinstance(tools, list) and 1 <= len(tools) <= 12, f"{name}: provide 1–12 tool contracts.")
                names = set()
                for tool in tools:
                    _require(isinstance(tool, dict) and _identifier(tool.get("name")) and tool["name"] not in names,
                             f"{name}: tool names must be valid and unique.")
                    names.add(tool["name"])
                    _require(_text(tool.get("description"), 2000), f"{name}: describe each tool.")
                    _validate_fields(tool.get("arguments"), tool["name"])
                expected = task.get("expected")
                _require(isinstance(expected, dict) and set(expected) == {"tool", "arguments"}, f"{name}: expected needs tool and arguments.")
                tool = next((t for t in tools if t["name"] == expected["tool"]), None)
                _require(tool is not None and fields_match(expected["arguments"], tool["arguments"]),
                         f"{name}: expected call must match an allowed tool contract.")
    return suite


def load_suite(spec="fieldkit-qa"):
    _require(_text(spec, 4096), "Choose a suite or enter the path to a local suite JSON file.")
    if spec == "all":
        suites = [load_suite(name) for name in BUILTINS]
        suite = {"schema_version": 1, "id": "all", "name": "All acceptance suites",
                 "description": "Grounded answers, structured extraction, and tool selection. Includes abstention and unsupported-action checks.",
                 "max_tokens": max(s["max_tokens"] for s in suites), "retrieval_limit": 2,
                 "tasks": [{**t, "id": f"{s['id']}.{t['id']}"} for s in suites for t in s["tasks"]],
                 "files": [f for s in suites for f in s["files"]]}
        return validate_suite(suite)
    path = ROOT / "data/suites" / f"{spec}.json" if spec in BUILTINS else Path(spec).expanduser().resolve()
    with path.open("rb") as f:
        raw = f.read(512001)
    _require(len(raw) <= 512000, "Suite file must be no larger than 512 KB.")
    suite = validate_suite(parse_json(raw.decode("utf-8")))
    suite["files"] = [{"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}]
    for task in suite["tasks"]:
        task["suite_id"] = suite["id"]
    return suite


def summary(suite):
    return {k: suite[k] for k in ["id", "name", "description", "max_tokens", "retrieval_limit"]} | {
        "task_count": len(suite["tasks"]), "kinds": sorted({t["kind"] for t in suite["tasks"]})}


def catalog():
    return [summary(load_suite(name)) for name in (*BUILTINS, "all")]


def prepare_task(task, documents, mode):
    """Explicit allowlist keeps grading targets and fixtures out of model payloads."""
    result = {k: task[k] for k in ["id", "kind", "question", "input", "fields", "tools"] if k in task}
    if "tools" in result:
        result["tools"] = [{k: tool[k] for k in ["name", "description", "arguments"]} for tool in task["tools"]]
    result["documents"] = documents
    if mode == "harness":
        result["fixture"] = task["fixture"]
        if "fixture_output" in task:
            result["fixture_output"] = task["fixture_output"]
    return result


def replay_tasks(tasks):
    """Known accept/reject cases, authored independently of validator decisions."""
    cases = []
    for task in tasks:
        fixture = task["fixture"]
        def add(slug, label, value, accepted=False, raw=False):
            cases.append({**task, "id": task["id"] + "::" + slug, "base_task_id": task["id"],
                          "case_label": label, "expected_accept": accepted,
                          "fixture_output": value if raw else json.dumps(value)})
        add("valid", "Valid response", fixture, accepted=True)
        add("malformed", "Malformed JSON", '{"broken":', raw=True)
        if task["kind"] == "grounded_qa":
            wrong = {**fixture, "answer": "UNSUPPORTED_FIXTURE_ANSWER"}
            add("wrong-fact", "Wrong fact" if task["answerable"] else "Invented answer instead of abstention", wrong)
            if task["answerable"]:
                add("wrong-source", "Invented source", {**fixture, "source": "__nonexistent_source__.md"})
                add("invented-quote", "Fabricated supporting quote", {**fixture, "quote": "This invented quotation is not present in the supplied source."})
        elif task["kind"] == "json_exact":
            key = next(iter(task["fields"]))
            missing = {k: v for k, v in fixture.items() if k != key}
            add("missing-field", "Missing required field", missing)
            add("wrong-type", "Wrong JSON type", {**fixture, key: []})
            add("wrong-value", "Incorrect extracted value", {**fixture, key: _different(fixture.get(key))})
            extra = _unused("unexpected_field", task["fields"])
            add("extra-field", "Unexpected output field", {**fixture, extra: True})
        else:
            names = [t["name"] for t in task["tools"]]
            add("unknown-tool", "Invented or unsupported tool", {"tool": _unused("upload_files", names), "arguments": {}})
            tool = next((t for t in task["tools"] if t["name"] == fixture.get("tool")), None)
            arguments = fixture.get("arguments")
            if tool and isinstance(arguments, dict):
                if tool["arguments"]:
                    key = next(iter(tool["arguments"]))
                    add("missing-argument", "Missing required argument", {**fixture, "arguments": {k: v for k, v in arguments.items() if k != key}})
                    add("wrong-type", "Wrong argument type", {**fixture, "arguments": {**arguments, key: []}})
                    add("wrong-value", "Incorrect argument value", {**fixture, "arguments": {**arguments, key: _different(arguments.get(key))}})
                extra = _unused("unexpected_argument", tool["arguments"])
                add("extra-argument", "Unexpected tool argument", {**fixture, "arguments": {**arguments, extra: True}})
            other = next((t for t in task["tools"] if t["name"] != fixture.get("tool")), None)
            if other:
                values = {"string": "fixture", "integer": 0, "number": 0.0, "boolean": False, "null": None}
                args = {k: values[v.split("|")[0]] for k, v in other["arguments"].items()}
                add("wrong-tool", "Allowed tool, wrong choice", {"tool": other["name"], "arguments": args})
    return cases


def _unused(name, existing):
    while name in existing:
        name += "_"
    return name


def _different(value):
    if type(value) is bool:
        return not value
    if type(value) in {int, float}:
        return value + 1
    if isinstance(value, str):
        return value + "_INCORRECT"
    return "INCORRECT_FIXTURE"


def replay_summary(answers, count):
    valid = [a for a in answers if a["expected_accept"]]
    invalid = [a for a in answers if not a["expected_accept"]]
    return {"case_count": count, "checked": len(answers), "matched": sum(a["passed"] for a in answers),
            "valid_cases": len(valid), "valid_accepted": sum(a["validator_accepted"] for a in valid),
            "invalid_cases": len(invalid), "invalid_rejected": sum(not a["validator_accepted"] for a in invalid),
            "false_accepts": sum(a["validator_accepted"] for a in invalid),
            "false_rejects": sum(not a["validator_accepted"] for a in valid)}


def evaluate_structured(task, output):
    checks = []
    parsed = None
    try:
        parsed = parse_json(output)
        checks.append({"label": "Strict JSON response", "passed": isinstance(parsed, dict)})
        if task["kind"] == "json_exact":
            checks.append({"label": "Exact field names and JSON types", "passed": fields_match(parsed, task["fields"])})
            for key, expected in task["expected"].items():
                checks.append({"label": f"Correct value: {key}", "passed": isinstance(parsed, dict) and key in parsed and exact_equal(parsed[key], expected)})
        else:
            shape = isinstance(parsed, dict) and set(parsed) == {"tool", "arguments"}
            checks.append({"label": "Exactly tool and arguments fields", "passed": shape})
            tool = next((t for t in task["tools"] if shape and t["name"] == parsed["tool"]), None)
            checks.append({"label": "Tool is allowed", "passed": tool is not None})
            checks.append({"label": "Arguments match the tool contract", "passed": tool is not None and fields_match(parsed["arguments"], tool["arguments"])})
            checks.append({"label": "Correct tool and exact arguments", "passed": exact_equal(parsed, task["expected"])})
    except (ValueError, TypeError) as exc:
        checks.append({"label": "Strict JSON response", "passed": False, "detail": str(exc)})
    return {"passed": all(c["passed"] for c in checks), "parsed": parsed, "checks": checks}
