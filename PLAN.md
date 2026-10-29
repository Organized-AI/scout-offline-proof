# Scout Offline Proof — build plan

Build date: October 28, 2026. Target: AITX / MLOps Agents track.

## Product

Make useful online agent workflows portable to local hardware, verify what completes under enforced network denial, and improve local performance against measured reference runs from frontier models with their harnesses.

The working prototype provides the evaluation foundation: local MLX inference, configurable acceptance tasks, evaluator failure replay, and evidence reports. Full multistep tool execution, online reference capture, baseline comparison, and automated harness optimization are planned capabilities, not implemented claims.

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

The current release supports one machine per run, MLX text models, UTF-8 Markdown/text documents, and declarative task suites. No model downloads during proof, model training, cloud deployment, autonomous dependency installation, or native Mac UI are implemented. Tool selections are validated without executing the proposed calls. An OS-denied connection is evidence for the subprocess and its descendants, not a claim that the entire machine is air-gapped. Passing these task suites is not a general model-quality guarantee.

## Build outcome

- Standalone Python engine, CLI, dashboard, synthetic task bank, and documentation implemented.
- Verified the A1 host's SSH access and persisted the local alias `a1-m1`.
- M1 internal storage had approximately 116 MB free and refused a project copy. No cleanup or changes to its existing Scout installation were performed.
- Copied the existing Qwen3-1.7B-4bit model from the A1 into this checkout's ignored `.proof/models` directory. Installed a separate local MLX virtual environment; no model was downloaded from a cloud service.
- Actual inference ran on the local M4 Mac mini with 16 GB RAM. First run: 12.21 seconds, 3/3 tasks passed, all four OS-denial probes passed. A subsequent dashboard run completed in 5.51 seconds with the same pass results. These are observed run timings, not promised performance.
- The native Mac app and Scout's private Worker remain independent. This local companion needs neither service to run.

## October 29 expansion

- Added three configurable suites: grounded Q&A (3 tasks), structured extraction (3), and agent tool selection (4). Custom JSON files supply tasks, expectations, fixtures, token budgets, and retrieval limits.
- Added wrong-answer and malformed-JSON fixture scenarios to verify that the evaluator rejects faults. Harness runs remain distinct from real model runs.
- Matched the original Scout visual language: charcoal and yellow, compact cards, pill controls, and locally served IBM Plex fonts. Added a light theme and persisted browser settings.
- A1 is now mounted directly on the M4 Mac at `/Volumes/A1`. Qwen3-4B-Instruct-2507-4bit passed all ten tasks in 21.77 seconds with four OS-denial probes passing. Timings describe this observed run only.
- Agent tool selection was prioritized because the [Antler Agents track and event rubric](https://common-scooter-829.notion.site/AITX-MLOps-World-Community-Hackathon-Austin-Tech-Week-4021e636288e81e08278fd9a977d7639) emphasize useful agent tooling, complete working systems, technical depth, and performance. This is a product choice based on the rubric, not a claim of organizer endorsement.
- Added failure replay: 32 agent-decision cases (4 accept / 28 reject), or 63 cases across all suites. Reports distinguish evaluator correctness from model accuracy. Tests inject always-accept and always-reject evaluators to confirm that both defects fail replay.
- The local model's tool-selection role is explicitly described as the decision model in the submission and Loom narrative; proposed actions remain unexecuted.

## Workflow portability and continuous improvement

### Product promise and terminology

**Take a workflow that works online, make its dependencies available locally, then measure and improve the offline result.**

An agent harness is the execution system around a model: instructions, skills, context assembly, retrieval, available tools, action validation, state, retries, stopping rules, and budgets. Optimizing that harness is distinct from fine-tuning model weights. Both can improve a local system; neither establishes parity without measurement.

The existing **Harness check** is an evaluator self-test. Its fixed fixtures test whether acceptance criteria detect mistakes. It does not learn, train a model, or execute a full agent workflow. Real inference mode measures actual model behavior on the configured tasks. These remain separate from the planned agent execution harness.

### First workflow to port

Use a bounded field-report intake workflow that builds on the current suites:

1. Read an intake request and a local handbook.
2. Extract the bundle identifier, file name, checksum algorithm, and missing information.
3. Ask for clarification if a required input is absent; otherwise select an allowed local integrity check.
4. Execute that check against a synthetic local bundle and compare the actual checksum with the expected checksum.
5. Produce a report containing the result and supporting source evidence.

Completion requires the final report **and actual tool evidence**. A plausible tool-call JSON object alone does not complete the workflow. This is a proposed first integration; the current implementation evaluates steps independently and does not execute step 4.

### Portable workflow contract

Record the original online workflow's source and version, then map its dependencies. Package transferable prompts, skills, tools, and data locally so they do not need to be fetched during execution. Replace required hosted capabilities with local equivalents where feasible, and preserve any unresolved dependency in the readiness result.

Each workflow package should declare:

- Input and output schemas, required artifacts, acceptance criteria, and valid stopping states.
- Required capabilities and their online and offline implementations: for example, document search over a frozen corpus and a local checksum tool.
- Versioned skills, prompts, model/tokenizer/runtime dependencies, tool versions, source snapshots, and hardware requirements.
- Execution limits: tokens, context, tool calls, retries, elapsed time, and memory.
- A data freshness policy and explicit treatment of unavailable capabilities.
- Development cases and a separate held-out evaluation set, identified by stable IDs and hashes.

Online-only steps must be visible in readiness checks. A cached corpus may support a dated research answer; it cannot establish a current web fact. An external write may be recorded as pending for later synchronization, but must not count as completed offline. An unavailable required capability produces a blocked or incomplete result. Reference traces can test adapters and evaluators; replaying recorded outputs does not prove that the local agent completed the work.

### Reference and comparison protocol

Treat the reference as a **model plus harness plus tools plus data**, with recorded versions, configuration, and budgets. Capture task inputs, observable outputs, tool calls/results, final artifacts, and measured resource use from authorized online runs. No provider or frontier baseline has been selected or run yet.

Evaluate the reference outputs too: they are comparison evidence, not automatic ground truth. Use the same input snapshots and task outcomes for a controlled comparison. If an online system uses live data unavailable locally, report the capability/data difference separately rather than presenting it as a pure model comparison.

For full workflows, score completion, artifact correctness, source support, invalid actions, appropriate clarification/abstention, and recovery from tool failures. Allow multiple valid execution paths; matching a reference's exact tool sequence is not the objective. The current exact tool-call tests remain useful component tests.

Report quality alongside latency distributions, memory, model/token/tool budgets, and online spend where observed. Compare paired cases and repeat trials to expose variability. Predeclare the acceptable quality gap and resource limits for each workflow. A claim of comparable performance names the workflow, test-set revision, reference version, hardware, sample size, and observed uncertainty. The present ten synthetic tasks do not establish frontier parity.

### Tuning and promotion loop

1. Freeze a baseline, evaluation rubric, and held-out cases. Validate the evaluator with failure replay.
2. Run the local candidate on development cases and classify failures: missing assets, retrieval, instructions, decision errors, tool adapters, or runtime/resource limits.
3. Version a focused candidate change to prompts, skills, context selection, retrieval, tool contracts, retries, or model/quantization choice. Record every changed dimension.
4. Re-run development cases. Use held-out cases at promotion checkpoints, not as a repeatedly exposed optimization target. Repeatedly inspected holdouts must eventually be replaced.
5. Promote only if the candidate meets the predefined quality/resource gates without critical regressions. Keep a prior known-good configuration for rollback.
6. Consider weight fine-tuning on curated, independently checked training examples if harness changes leave a persistent capability gap. Keep training examples and reference outputs from held-out cases out of tuning inputs.

Improvement should change the system's behavior, not weaken the acceptance tests to raise its score. Any justified rubric change creates a new evaluation version and requires re-evaluating both the reference and local candidates.

### Decision model and routing

The local decision model chooses allowed actions, asks for missing information, or stops when requirements cannot be met. The future runtime validates those proposals and executes permitted local tools, recording their outcomes.

Execution mode is explicit: online, forced offline, or a configured fallback mode. Forced-offline runs retain OS network denial even if the Mac is connected. Falling back should occur at a validated checkpoint with compatible state and tool contracts; network loss alone does not make an online workflow portable. If a required dependency is unavailable, the runtime must report the gap rather than silently inventing a result.

### Next implementation milestones

| Milestone | Deliverable | Evidence required |
| --- | --- | --- |
| 1. Execute one portable workflow | A bounded agent loop with local document lookup and checksum tools, state, budgets, and validated actions | Real final artifact and tool results under OS network denial; missing-input and tool-failure cases |
| 2. Compare with an online reference | Versioned reference-report import and paired outcome comparison | Provenance, equivalent input/task revisions, and separately labeled capability differences |
| 3. Tune configurations | Versioned prompt/skill/retrieval/model configurations with development and held-out evaluations | Candidate changes improve selected workflows without degrading required behavior |
| 4. Train only where justified | Optional adapter/weight fine-tuning on verified training examples | Improvement persists on held-out cases, resource costs are recorded, and rollback remains available |

For the hackathon, demonstrate the implemented offline checks and evaluator replay, then show this roadmap as the next step. Do not present the reference capture, automatic fallback, training, or frontier-comparison loop as already working.
