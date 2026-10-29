# Loom script — Scout Offline Proof

**Video title:** Scout Offline Proof: testing local AI beyond Wi-Fi

**Target length:** 4:00–4:30

**Format:** Screen recording with optional face camera. Narration below is ready to read; screen actions are separate.

## Set up before recording

1. Start `python3 -m proof serve` from this repository and open http://127.0.0.1:8741.
2. Keep A1 connected. Select **All acceptance suites**, **Local model**, and **Qwen3-4B-Instruct-2507-4bit · A1**. Under Local paths, use this project's `.venv/bin/python` and bundled `data/fieldkit` documents.
3. Rehearse a real run once. Confirm the actual result; do not assume it will always pass or take the same time. The measured reference run passed 10/10 in 20.84 seconds.
4. Use a browser window around 1440 × 1000, the dark theme, and readable zoom. Start at the top of the dashboard. Keep the downloaded report and `data/suites/extraction.json` ready to show near the end.
5. Use the synthetic bundled data throughout. Close unrelated tabs and notifications. The JSON report includes local paths and machine names; select the relevant sections when showing it.

## 0:00–0:30 — The problem

**On screen:** Show the A1 device briefly if convenient, then the dashboard and selected local model.

**Say:**

“I keep local AI models on this A1 drive. But having a model downloaded doesn't tell me whether it can actually do useful work without internet access. The tokenizer might be missing, the runtime might fail, or the model might give an answer that looks convincing but is wrong.

I built Scout Offline Proof to test the whole workflow and keep evidence of what happened.”

## 0:30–1:00 — What the tool tests

**On screen:** Open the task-suite dropdown. Point out the three suites and leave **All acceptance suites** selected.

**Say:**

“There are ten tasks across three suites. Document Q&A checks answers against local sources. Structured extraction checks fields, values, and JSON types. In the third suite, Qwen acts as a decision model. It chooses an allowed tool and its arguments, asks for missing information, or declines an unsupported action.

These are small, synthetic acceptance tests. You can supply your own tasks for the work your team actually needs.”

## 1:00–1:35 — Show that the evaluator catches failures

**On screen:** Select **Agent tool selection**, click **Harness check**, and choose **Failure replay · accept/reject checks**. Click **Run harness check**. Show **32/32 cases verified**, **4/4 valid accepted**, **28/28 invalid rejected**, and zero false accepts/rejects. Select a **Missing required argument** case to inspect its expected rejection.

**Say:**

“How do I know the evaluator works? Harness mode replays prepared decisions without loading a model. These include valid calls, invented tools, missing arguments, and a valid tool chosen for the wrong request.

Here it accepted four valid responses and rejected 28 invalid ones. All 32 judgments matched the expected verdict. A bad response that is correctly rejected is a successful harness check. This tests the evaluator; the next run tests the model itself.”

## 1:35–2:10 — Run real inference

**On screen:** Select **All acceptance suites**, switch to **Local model**, and click **Run offline proof**. Keep the run stages visible while it executes.

**Say:**

“Now this is the real Qwen model, loaded directly from A1 and running on this Mac.

The tool checks the setup and hashes the inputs. It then starts the inference process under an operating-system policy that denies network access. Four live connection probes have to confirm that restriction before the model is loaded.

The model runs each task, and a separate evaluator checks the outputs. Expected answers are not included in the model's prompts.”

**Timing:** The reference run took about 21 seconds. If your live run takes longer, let it finish; do not substitute the fixture results.

## 2:10–3:10 — Explain the actual results

**On screen:** Show the total and category scores. In Run evidence, open the retention answer; then select **missing value** and **unsupported action**. Open **Expected output** where useful.

**Say, if the live run passes:**

“This run passed all ten tasks. The category scores show where those results came from.

For this document question, the answer is 72 hours. The evaluator checks the expected fact, the source filename, and whether the supporting quotation really appears in that source. There's also a question the documents cannot answer, where the model must abstain.

In extraction, an absent owner stays null instead of becoming a made-up name. The suite also tests whether an instruction hidden in the input changes the extracted record.

For the unsupported upload request, the model selects no action instead of inventing a tool. These tool calls are checked against contracts; this demo does not execute the proposed actions.”

**If a live task fails, use instead:** “The run completed, but this task failed its acceptance check. Here is the actual output and the expected result. This is the kind of problem the tool is designed to expose before deployment.” Then continue with the evidence.

## 3:10–3:40 — Define the offline claim

**On screen:** Scroll to the four network probes.

**Say:**

“All four network probes were denied. The local test endpoint was reachable before sandboxing, so a missing internet connection alone can't explain the result.

The restriction applies to the inference process and its descendants. My dashboard and the rest of the Mac remain online. The evidence is that these particular tasks completed with that process's network access blocked—not that the entire computer is air-gapped or every future answer will be correct.”

## 3:40–4:15 — Evidence, configuration, and value

**On screen:** Click **Export report**. Show the suite name, an answer with its checks, and the file hashes. Briefly show `data/suites/extraction.json` or expand **Configure your own tasks**.

**Say:**

“The report keeps the actual outputs, expected values, checks, timings, runtime versions, and input hashes. That gives us something concrete to inspect when a setup or model changes.

To adapt this, copy a suite JSON file and change the inputs and acceptance criteria. The same harness can check your fixtures before you run them against a real model.

Scout Offline Proof is agent tooling for developers who need dependable local AI. It turns ‘the model is on the drive’ into a much more useful question: can this setup finish the work, with evidence we can inspect?”

## Recording notes

- Describe the score and timing that actually appear in your recording.
- Keep “harness” and “real model” labels visible when switching modes.
- The report is an unsigned local record, not independent certification.
- Do not call this a fully autonomous agent or claim that its proposed tools were executed.
- If you need to shorten the video, omit the custom-file preview and show only one extraction example.
