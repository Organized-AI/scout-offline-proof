# Scout Offline Proof

**Tagline:** Downloaded isn't the same as ready.

**Track:** Antler — Agents / agent tooling

**Repository:** https://github.com/Organized-AI/scout-offline-proof

**Demo video:** [Add Loom URL]

**Team:** [Add team name, members, and contact]

## Submission write-up

Agent workflows are becoming useful online, but unreliable connectivity can put their tools and data out of reach. Our goal is to make suitable workflows portable: prepare local dependencies, complete the work offline, and measure quality against an online reference.

Scout Offline Proof is the evaluation foundation for that goal, built as an independent companion to A1 Scout. It checks a local MLX setup, fingerprints inputs, and runs ten synthetic acceptance tasks under macOS network denial. Four live probes verify enforcement before inference.

The suites cover grounded document Q&A, typed extraction, and agent tool selection. For tool selection, the local model acts as a decision model: propose an allowed action, ask for missing information, or decline an unsupported request. The evaluator checks those proposals; tools are not yet executed. Teams can define custom JSON suites.

A separate Harness check replays known valid and invalid decisions to test the evaluator. The agent suite verifies 32 cases and reports false accepts and false rejects. Only real model inference can earn “Verified offline.” The dashboard exposes failures and exports outputs, checks, timings, runtime versions, and file hashes.

In a measured run, Qwen3 4B loaded from A1 passed all ten tasks in 20.8 seconds on an M4 Mac mini, with all four denial probes passing.

Next comes one complete local workflow, then paired evaluation against a versioned reference using a frontier model and its harness. We plan to tune prompts, skills, retrieval, tools, and model choice while keeping acceptance criteria fixed and testing held-out cases. Weight fine-tuning may follow. No frontier comparison has been run; these narrow results establish neither general agent reliability nor parity.

## Short pitch

Scout Offline Proof provides the evaluation foundation for taking online agent workflows offline. It tests local answers, extraction, and tool decisions under OS-enforced network denial and exports inspectable evidence. The roadmap is complete local execution, then measured improvement against online references.

## Why this fits the hackathon

The [Antler Agents track and judging rubric](https://common-scooter-829.notion.site/AITX-MLOps-World-Community-Hackathon-Austin-Tech-Week-4021e636288e81e08278fd9a977d7639) emphasize agent tooling that performs useful work, a complete functioning system, technical depth, usability, and performance. This project demonstrates a working evaluation pipeline, real OS enforcement, deliberately failing cases, and measured local inference. Tool selection extends the proof to agent decisions. The proposed next milestone connects those components into a complete local workflow; subsequent reference comparisons would measure whether configuration changes improve its results.

## Before submitting

- [ ] Add the team roster and contact details.
- [ ] Record the 3–5 minute Loom using `DEMO.md`, then add its URL.
- [ ] Make the repository publicly viewable if submitting it; it is currently private.
- [ ] Confirm treatment of existing model weights and third-party dependencies with the organizers.
- [ ] Submit before October 29, 2026, 5:00 PM Central using the event form.

Nothing has been submitted. The app runs locally; the repository instructions and recorded demo explain how to reproduce it on compatible hardware.
