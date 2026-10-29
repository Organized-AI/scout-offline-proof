# Scout Offline Proof — build plan

Build date: October 28, 2026. Target: AITX / MLOps Agents track.

## Product

Measure whether agent workflows achieve their declared outcomes under recorded execution conditions, whether online or offline. Use that evidence to compare model and harness configurations, make useful workflows portable to local hardware, and improve their results over time.

The working prototype provides the evaluation foundation: local MLX inference, configurable acceptance tasks, evaluator failure replay, and evidence reports. Full multistep tool execution, online reference capture, baseline comparison, and automated harness optimization are planned capabilities, not implemented claims.

The first release is a standalone, local companion to A1 Scout. It reads model files without changing them and does not require Scout's private Worker, credentials, or code. All application code and synthetic demo documents are written for this build. Existing model weights and dependencies are external assets, listed separately. Hackathon eligibility of any pre-existing assets remains an organizer question.

## Deliverables and order

1. Standard-library Python CLI and preflight checks: model files, interpreter, runtime, document corpus, memory advisory, and macOS network sandbox availability.
2. A subprocess runner under an OS network-deny policy. Verify a reachable local witness is denied inside the runner, plus IPv4, IPv6, and UDP denial probes. No Wi-Fi or system firewall changes.
3. Deterministic lexical retrieval, local MLX inference, exact quotation and source validation, expected-fact checks, and an unanswerable question. Runs use no hosted APIs or downloaded assets.
4. A local dashboard: inspect setup, run workflow, inspect stages and answer evidence, export JSON, and show failed-run diagnostics. A clearly labeled harness mode tests orchestration without pretending to be a model run.
5. Inspect available machines, read the A1 model stash over SSH, and run the proof on a machine with sufficient resources.
6. README, architecture, dataset provenance, demo script, and a draft submission description.

## Current release acceptance criteria

- An absent model or tokenizer fails with actionable diagnostics before inference.
- A runtime without functioning OS enforcement cannot produce a **Verified offline** result.
- Only a real model run with all checks passing earns the current **Verified offline** label.
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

## Outcome measurement across online and offline execution

**Define success once. Verify the result. Record the conditions and resources used to achieve it.**

The primary measurement unit is a logical workflow request with a declared outcome. A verified outcome plays the role of a conversion in a measurement plan. Network access, model, harness configuration, hardware, and available tools are dimensions of the run. A frontier model is another measured configuration; its output is not the definition of success.

This is the measurement design for the next implementation. Today's report records task outputs and checks, timings, file hashes, runtime versions, machine information, and network-denial evidence. It does not yet record completed multistep artifacts, actual tool execution, online comparisons, spend, peak memory, or human interventions.

### Outcome contract

Before comparing configurations, version the following for each workflow:

- The requested result, required final artifacts or external effects, and evidence that establishes delivery.
- Acceptance criteria for artifact correctness, source support, tool effects, and required behavior; critical criteria are gates, not points that can be averaged away.
- The input snapshot, data freshness requirements, permitted capabilities, and resource limits.
- Whether a case tests completed work or a boundary behavior such as clarification or refusal.
- The evaluation cohort, development/held-out split, attempt policy, and primary metric denominators.

Keep three observations separate: whether execution finished, whether the requested work was delivered, and whether behavior met the acceptance criteria. Correctly asking for a missing filename can pass a clarification test while the bundle-verification request remains unresolved. Likewise, refusing an unavailable upload may be correct behavior, but a queued or refused upload is not a completed upload. The current ten-task acceptance score includes such boundary tests and is not an end-to-end completion rate.

### Measurement record

| Dimension | Record | Interpretation |
| --- | --- | --- |
| Identity | Workflow/case revision, logical request ID, run ID, attempt ID, configuration ID | Link retries to one request and compare equivalent cases. |
| Evidence origin | Measured model run, evaluator fixture, or estimate; native/imported provenance and original report identity | Keep real execution, evaluator self-tests, and predictions distinguishable throughout the interface and exports. |
| Delivery | Completed, needs clarification, unsupported, blocked, failed, or unknown; required artifact/effect evidence | Count completion only when the declared result is verified. A missing result stays unresolved. |
| Acceptance | Pass/fail/undetermined for each criterion, evaluator revision, relevant source/tool evidence | Report artifact quality and appropriate boundary behavior separately from delivery. |
| Execution conditions | Compute location, configured network policy, observed network evidence, tools, source snapshots, model/harness versions | Local compute and offline execution are separate dimensions. A local model can run with networking enabled. |
| Efficiency | End-to-end time, attempt and tool counts, human interventions, observed tokens/memory, cost and accounting scope | Missing measurements remain unknown. Label estimates and their assumptions. |

For mixed or fallback runs, record conditions per step and retain the overall sequence. A run that used an online service before switching to local execution cannot be labeled entirely offline. Continue enforcing network denial for steps declared forced offline. Environment evidence complements the outcome verdict; neither substitutes for the other.

### Metrics and denominators

- **Verified completion rate:** unique requests with the required result verified / all requests assigned to the completion cohort. Keep blocked, timed-out, failed, and unresolved requests in the denominator. Declare any eligibility exclusions before running and report them. Report clarification/refusal test acceptance separately.
- **Acceptance by criterion:** passing cases / assigned cases for each applicable criterion, with failures and undetermined results visible. Preserve sample counts and critical failures alongside aggregate scores.
- **Time to verified completion:** elapsed time from the first attempt to the accepted result, including retries. Report unresolved/time-limited runs and success rate alongside latency; separately record waiting and active time when available.
- **Cost per verified completion:** total recorded cost for all attempts in the cohort, including failed attempts and retries / unique verified completions. With no verified completions, the ratio is undefined. Incomplete cost coverage cannot be presented as a complete cost figure. Local hardware and energy estimates must be labeled separately from measured API spend; no API bill does not imply zero total cost.
- **Operational burden:** attempts and tool calls per request, recovery rate on declared failure cases, and human intervention rate. Record both request-level and attempt-level results so retries cannot inflate success counts.

Stage outcomes provide diagnostic context for these metrics. Readiness, isolation, generation, and validation events help locate a failure; stage progress alone does not establish the user's outcome. Avoid a single blended score that can hide failed delivery behind low cost or fast execution.

### Fair comparisons and improvement claims

Use paired workflow cases, the same input snapshots and acceptance criteria, declared budgets, and versioned model/harness/tool configurations. Evaluate online references with the same outcome checks as local candidates. Record data or capability differences that prevent a like-for-like comparison.

Repeat trials, record cold/warm conditions, and interleave or randomize comparable runs where practical. Show sample sizes and uncertainty alongside observed differences. A controlled configuration change can support attributing improvement to that change; a before/after score with several changes does not isolate their individual effects. Keep the evaluation rubric frozen and reserve held-out cases for promotion decisions.

The first comparison view should show completion, acceptance, latency, resource use, and conditions side by side. Unknown measurements remain visible. No online reference has been selected or benchmarked yet.

### Bench interface direction

Use the user's A1 Bench screenshots from October 29 as the visual reference: charcoal surfaces, yellow selection and action accents, IBM Plex typography, compact pills, job cards, a configuration panel, a dense comparison table, and individual acceptance checks. Preserve the working companion's existing Scout styling while adapting the information hierarchy to outcome measurement.

The main product question is: **Which configuration delivers the requested outcome, under which conditions, and what does it take?**

| Bench pattern | Measurement dashboard application |
| --- | --- |
| Job cards | Select the workflow or task suite. Display task count and real-run count with distinct labels. Start with the three implemented suites; complete workflow cards follow actual execution support. |
| Measured / Simulate navigation | Distinguish real model results, evaluator checks, and any future estimates. The current Harness check is an evaluator check. A simulation is a separate future capability. |
| Parts, machine, and scenario controls | Select model/harness configuration, hardware, input cohort, budgets, and execution policy. Record the exact selected configuration with the run. |
| Comparison table | Compare equivalent workflow revisions using verified completions, acceptance results, sample counts, end-to-end time, measured resources, and cost coverage. Include model/harness identity, compute location, and observed network conditions. |
| Test checklist | Open the criteria that passed, failed, or remained unmeasured. Link each result to the input, actual output, expected requirement, and relevant evidence. |
| Stack / execution diagram | Inspect the stages and actual tool sequence for a selected run, including failures, retries, clarification, and fallback boundaries when implemented. |

The drill-down path is **workflow → configuration comparison → individual run → stage/task checks → source, tool result, or final artifact**. Comparisons should show both outcome and efficiency rather than hiding tradeoffs in a single score. The screenshots' weighted model scores are design references, not an adopted definition of workflow completion. Keep fixtures and estimates out of measured rankings; keep missing values visible as unmeasured rather than zero.

Current implementation remains the local task dashboard with per-task evidence and stage status. The comparison view, expanded stage drill-down, complete workflow accounting, and online execution controls described here are planned. Do not copy screenshot metrics into run evidence.

## Workflow portability and continuous improvement

### Product promise and terminology

**Apply the same outcome standard to a workflow online and offline, then use the evidence to improve either configuration.** Portability requires making the necessary dependencies available locally; successful completion is established by the outcome contract above.

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

Report completion and quality alongside latency distributions, memory, model/token/tool budgets, and cost where observed, using the denominators defined above. Compare paired cases and repeat trials to expose variability. Predeclare the acceptable quality gap and resource limits for each workflow. A claim of comparable performance names the workflow, test-set revision, reference version, hardware, sample size, and observed uncertainty. The present ten synthetic tasks do not establish frontier parity.

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
| 1. Execute and measure one portable workflow | A versioned outcome contract and bounded agent loop with local document lookup and checksum tools, state, budgets, and validated actions | Real final artifact and tool results under OS network denial; delivery distinguished from correct clarification/refusal; missing-input and tool-failure cases |
| 2. Compare online and offline configurations | Versioned reference-report import and paired outcome comparison, with completion, quality, time, and resource accounting | The same acceptance criteria, request/attempt identities, provenance, equivalent input/task revisions, and visible capability or measurement gaps |
| 3. Tune configurations | Versioned prompt/skill/retrieval/model configurations with development and held-out evaluations | Candidate changes improve selected workflows without degrading required behavior |
| 4. Train only where justified | Optional adapter/weight fine-tuning on verified training examples | Improvement persists on held-out cases, resource costs are recorded, and rollback remains available |

For the hackathon, demonstrate the implemented offline checks and evaluator replay, then show this roadmap as the next step. Do not present the reference capture, automatic fallback, training, or frontier-comparison loop as already working.
