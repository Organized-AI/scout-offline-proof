# Three-minute Loom walkthrough

## Before recording

- Start `python3 -m proof serve` and open the dashboard.
- Keep the selected model local and the correct Python interpreter configured.
- Run the real workflow once to confirm this machine works. This is a functional rehearsal, not a substitute for the recorded run.
- Never show secret configuration or unrelated client data. Everything in this corpus is synthetic.

## 0:00–0:30 — the problem

“I keep local models on an external drive. But a file being downloaded doesn't tell me whether its tokenizer, runtime, and full workflow can actually run offline. Scout Offline Proof tests that claim.”

Show the model, machine, and bundled documents.

## 0:30–1:00 — show a real failure

Open the advanced settings and change the model path to an explicitly nonexistent folder, such as `/nonexistent/offline-proof-demo-model`. Run the proof. Show the failed model/tokenizer/weights checks and remediation. No actual file needs to be removed.

Restore the existing model using the model dropdown.

## 1:00–2:15 — run the real proof

Click **Local model**, then **Run offline proof**. Explain the five stages while they progress. The runner probes a live local witness before loading the model. The OS blocks TCP and UDP connections from inside that process.

“The dashboard remains online. The inference subprocess has network access denied. Those are separate claims.”

Show the actual results. If a quality check fails, show the failure honestly and diagnose it; do not substitute a harness result.

## 2:15–3:00 — inspect the evidence

Open a passing answer and its supporting quotation. Open the unknown-price question and show abstention. Show the four denied network probes, then export the JSON report with file hashes, actual output, and runtime versions.

“This is a small, reproducible workflow proof, not a promise that every model response is correct. Next, teams can supply their own tasks and gate model updates on the workflows they actually need.”
