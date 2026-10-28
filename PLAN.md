# Scout Offline Proof — build plan

Build date: October 28, 2026. Target: AITX / MLOps Agents track.

## Product

Prove that a local document-answering workflow works when its inference process cannot access the network. A model file alone is not proof of readiness.

The first release is a standalone, local companion to A1 Scout. It reads model files without changing them and does not require Scout's private Worker, credentials, or code. All application code and synthetic demo documents are written for this build. Existing model weights and dependencies are external assets, listed separately. Hackathon eligibility of any pre-existing assets remains an organizer question.

## Deliverables and order

1. Standard-library Python CLI and preflight checks: model files, interpreter, runtime, document corpus, memory advisory, and macOS network sandbox availability.
2. A subprocess runner under an OS network-deny policy. Verify a reachable local witness is denied inside the runner, plus IPv4, IPv6, and UDP denial probes. No Wi-Fi or system firewall changes.
3. Deterministic lexical retrieval, local MLX inference, exact quotation and source validation, expected-fact checks, and an unanswerable question. Runs use no hosted APIs or downloaded assets.
4. A local dashboard: inspect setup, run workflow, inspect stages and answer evidence, export JSON, and show failed-run diagnostics. A clearly labeled harness mode tests orchestration without pretending to be a model run.
5. Inspect available machines, read the A1 model stash over SSH, and run the proof on a machine with sufficient resources.
6. README, architecture, dataset provenance, demo script, and a draft submission description.

## Acceptance criteria

- An absent model or tokenizer fails with actionable diagnostics before inference.
- A runtime without functioning OS enforcement cannot produce a verified result.
- Only a real model run with all checks passing is marked verified.
- Unsupported answers, invented citations, incorrect expected facts, and failed abstention fail quality checks.
- Reports include file hashes, machine/runtime identity, network probes, actual outputs, checks, timings, and limitations.
- Live progress and exported reports agree; concurrent runs are refused; subprocesses time out cleanly.
- Backend serves loopback only, validates mutation requests, and never returns credentials.
- Automated tests cover failure paths and report semantics; browser QA covers the working UI.

## Scope limits

One machine per run, MLX text models, UTF-8 Markdown/text documents, one document-Q&A workflow. No model downloads during proof, model training, cloud deployment, autonomous dependency installation, or native Mac UI in this release. An OS-denied connection is evidence for the subprocess and its descendants, not a claim that the entire machine is air-gapped. Passing this small task bank is not a general model-quality guarantee.

## Build outcome

- Standalone Python engine, CLI, dashboard, synthetic task bank, and documentation implemented.
- Verified the A1 host's SSH access and persisted the local alias `a1-m1`.
- M1 internal storage had approximately 116 MB free and refused a project copy. No cleanup or changes to its existing Scout installation were performed.
- Copied the existing Qwen3-1.7B-4bit model from the A1 into this checkout's ignored `.proof/models` directory. Installed a separate local MLX virtual environment; no model was downloaded from a cloud service.
- Actual inference ran on the local M4 Mac mini with 16 GB RAM. First run: 12.21 seconds, 3/3 tasks passed, all four OS-denial probes passed. A subsequent dashboard run completed in 5.51 seconds with the same pass results. These are observed run timings, not promised performance.
- The native Mac app and Scout's private Worker remain independent. This local companion needs neither service to run.
