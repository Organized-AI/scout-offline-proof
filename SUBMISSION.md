# Scout Offline Proof

**Tagline:** Downloaded isn't the same as ready.

**Track:** Antler — Agents / agent tooling

**Repository:** https://github.com/Organized-AI/scout-offline-proof

**Demo video:** [Add Loom URL]

**Team:** [Add team name, members, and contact]

## Submission write-up

Local AI is only useful if it can finish the work when connectivity disappears. A downloaded model does not tell you whether its runtime, tokenizer, and outputs are ready for a real workflow.

Scout Offline Proof turns that uncertainty into inspectable evidence. It checks a local MLX setup, fingerprints its inputs, and runs acceptance tasks inside a macOS process whose network access is denied by the operating system. Four live probes verify the restriction before inference begins.

The tool includes ten synthetic tasks across three suites: grounded document Q&A, structured extraction, and agent tool selection. In the third suite, the local model acts as a decision model: choosing a tool, requesting clarification, or declining an unsupported action. Deterministic checks validate its proposed decisions without executing them. Teams can supply their own JSON suites to test the workflows they need.

A separate harness replays known good and bad decisions to test the evaluator itself. The agent suite verifies 32 accept/reject cases and reports false accepts and false rejects. Only actual model inference can earn “Verified offline.” The dashboard exposes individual failures, category scores, timings, and an exportable report containing outputs, checks, runtime versions, and file hashes.

In a measured run, Qwen3 4B loaded directly from the A1 drive passed all ten tasks in 20.8 seconds on an M4 Mac mini, with all four network-denial probes passing. These are narrow acceptance results, not a general accuracy guarantee.

Built as an independent companion to A1 Scout, the tool helps developers check local AI and agent workflows before taking them into environments with unreliable connectivity.

## Short pitch

Scout Offline Proof checks whether a local AI workflow actually works with its network access blocked. It tests grounded answers, structured extraction, and tool selection, then exports the evidence—so teams can verify readiness before relying on a model offline.

## Why this fits the hackathon

The [Antler Agents track and judging rubric](https://common-scooter-829.notion.site/AITX-MLOps-World-Community-Hackathon-Austin-Tech-Week-4021e636288e81e08278fd9a977d7639) emphasize agent tooling that performs useful work, a complete functioning system, technical depth, usability, and performance. This project demonstrates a working evaluation pipeline, real OS enforcement, deliberately failing cases, and measured local inference. Tool selection extends the proof to agent decisions while keeping the claims precise.

## Before submitting

- [ ] Add the team roster and contact details.
- [ ] Record the 3–5 minute Loom using `DEMO.md`, then add its URL.
- [ ] Make the repository publicly viewable if submitting it; it is currently private.
- [ ] Confirm treatment of existing model weights and third-party dependencies with the organizers.
- [ ] Submit before October 29, 2026, 5:00 PM Central using the event form.

Nothing has been submitted. The app runs locally; the repository instructions and recorded demo explain how to reproduce it on compatible hardware.
