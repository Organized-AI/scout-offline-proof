# Draft submission — Scout Offline Proof

Track: Antler Agents. Status: draft; team details, public repository URL, and Loom URL still need to be supplied before submission. Nothing is submitted automatically.

## Write-up

Downloading a model is easy. Knowing whether an entire AI workflow will still work without internet access is harder. Missing tokenizers, runtime dependencies, and unsupported answers can turn a promising local setup into a failed field demo.

Scout Offline Proof is a local verification tool for people who need dependable AI on their own hardware. It inspects a model and runtime, fingerprints the input files, and executes a document-answering workflow inside a macOS subprocess whose network access is denied by the operating system. Live connection probes verify that denial before inference begins.

The workflow retrieves local documents, generates answers with an MLX model, and checks expected facts, exact source quotations, and abstention when the answer is absent. A dashboard shows progress and failures; an exported report contains the actual outputs, checks, timings, runtime versions, and input hashes. A separate harness mode tests the plumbing without claiming a real model proof.

Built as an independent companion to A1 Scout, this first release demonstrates one narrow workflow with synthetic documents. Its purpose is to replace assumptions about offline readiness with inspectable evidence. Future versions can support user-defined acceptance tests and compare model revisions before deployment.

## Submission checklist

- [ ] Publicly viewable repository URL
- [ ] 3–5 minute Loom demo showing actual inference
- [ ] Team roster and contact details
- [ ] Confirm treatment of existing model weights/dependencies with organizers
- [ ] Submit before October 29, 2026, 5 PM Central

The local application needs no deployment URL: run instructions and the recorded demonstration reproduce the workflow on compatible hardware.
