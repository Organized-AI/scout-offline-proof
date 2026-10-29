# Scout Offline Proof

**Tagline:** Measure the result. Record the conditions.

**Track:** Antler — Agents / agent tooling

**Repository:** https://github.com/Organized-AI/scout-offline-proof

**Demo video:** [Add Loom URL]

**Team:** [Add team name, members, and contact]

## Submission write-up

Our goal is measurable agent outcomes across online and offline execution. Define success once, verify the actual result, and record the time, resources, and conditions required to achieve it.

Scout Offline Proof is the evaluation foundation for that goal, built as an independent companion to A1 Scout. It checks a local MLX setup, fingerprints inputs, and runs ten synthetic acceptance tasks under macOS network denial. Four live probes verify enforcement before inference.

The suites cover grounded document Q&A, typed extraction, and agent tool selection. For tool selection, the local model acts as a decision model: propose an allowed action, ask for missing information, or decline an unsupported request. The evaluator checks those proposals; tools are not yet executed. Teams can define custom JSON suites.

A separate Harness check replays known valid and invalid decisions to test the evaluator. The agent suite verifies 32 cases and reports false accepts and false rejects. Only real model inference can earn “Verified offline.” The dashboard exposes failures and exports outputs, checks, timings, runtime versions, and file hashes.

In a measured run, Qwen3 4B loaded from A1 passed all ten tasks in 20.8 seconds on an M4 Mac mini, with all four denial probes passing.

Next comes a complete local workflow and a shared outcome contract for comparing online and offline runs. Both will be evaluated against the same requirements, with completion, quality, latency, and cost reported separately. We plan to tune prompts, skills, retrieval, tools, and model choice using fixed criteria and held-out cases. Online comparisons and automated tuning remain planned; current results do not establish frontier parity.

## Short pitch

Scout Offline Proof tests local answers, extraction, and tool decisions under OS-enforced network denial and exports inspectable evidence. It is the first step toward measuring complete workflow outcomes against a shared standard online and offline, then improving configurations based on verified results.

## Why this fits the hackathon

The [Antler Agents track and judging rubric](https://common-scooter-829.notion.site/AITX-MLOps-World-Community-Hackathon-Austin-Tech-Week-4021e636288e81e08278fd9a977d7639) emphasize agent tooling that performs useful work, a complete functioning system, technical depth, usability, and performance. This project demonstrates a working evaluation pipeline, real OS enforcement, deliberately failing cases, and measured local inference. Tool selection extends the proof to agent decisions. The proposed next milestone connects those components into a complete local workflow; subsequent reference comparisons would measure whether configuration changes improve its results.

## Before submitting

- [ ] Add the team roster and contact details.
- [ ] Record the 3–5 minute Loom using `DEMO.md`, then add its URL.
- [ ] Make the repository publicly viewable if submitting it; it is currently private.
- [ ] Confirm treatment of existing model weights and third-party dependencies with the organizers.
- [ ] Submit before October 29, 2026, 5:00 PM Central using the event form.

Nothing has been submitted. The app runs locally; the repository instructions and recorded demo explain how to reproduce it on compatible hardware.
