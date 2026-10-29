// Read-only exploration of task definitions and recorded run evidence.
const proofExplorer = (() => {
  const $ = (id) => document.getElementById(id);
  const esc = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const json = (value) => `<pre>${esc(JSON.stringify(value, null, 2))}</pre>`;
  const family = {
    grounded_qa: {
      name: "Grounded Q&A",
      purpose:
        "Can this model use local knowledge and support its answers with evidence?",
      relevance:
        "An offline workflow needs usable local sources and a clear response when those sources cannot answer the question.",
      tuning:
        "Document coverage, retrieval, context selection, and grounding instructions.",
    },
    json_exact: {
      name: "Extraction",
      purpose:
        "Can this model turn source text into the exact data a workflow needs?",
      relevance:
        "Subsequent steps depend on correct values and types. Missing information must stay missing, and instructions inside source data must not rewrite the task.",
      tuning:
        "Output schemas, extraction instructions, examples, and handling of missing or untrusted information.",
    },
    tool_call: {
      name: "Tool selection",
      purpose:
        "Can the decision model choose an available action with the right arguments?",
      relevance:
        "A portable agent must respect the tools available in its environment, ask for required information, and recognize unsupported requests. These proposals are checked; the tools are not executed.",
      tuning:
        "Tool descriptions, argument contracts, clarification rules, and model choice.",
    },
  };
  const stageGuide = {
    preflight: {
      purpose: "Establish that the selected setup is ready to run locally.",
      steps: [
        "Validate the suite and its required local inputs.",
        "Check the Python interpreter and macOS network-sandbox availability.",
        "For model runs, check configuration, tokenizer, weight files, MLX availability, and the model size budget.",
      ],
      meaning:
        "A pass establishes readiness. A failure points to a missing asset, invalid suite, or runtime issue before model quality is assessed. The weight-size check is not a measurement of peak memory.",
    },
    manifest: {
      purpose:
        "Identify the exact inputs behind this measurement so configurations can be compared.",
      steps: [
        "Record SHA-256 hashes of the suite, local documents, application source, and model files used.",
        "Prepare Q&A context using local keyword retrieval; keep grading answers out of the model payload.",
        "Check suite/corpus contents and model file size/timestamps again after execution to detect changes.",
      ],
      meaning:
        "The fingerprint identifies this run's files. Detected input changes invalidate the evidence. The report is a local record, not a signed attestation.",
    },
    isolation: {
      purpose:
        "Establish that inference can proceed with its network access denied by the OS.",
      steps: [
        "Confirm a local TCP witness is reachable before sandboxing.",
        "Launch the runner under a network-deny policy.",
        "Require OS permission errors from the witness, external IPv4 TCP, IPv6 loopback TCP, and external IPv4 UDP probes before loading the model.",
      ],
      meaning:
        "Only permission-denied errors count. Timeouts or connection refusals do not prove enforcement. The restriction covers the runner and descendants; the dashboard and the rest of the Mac can remain online.",
    },
    workflow: {
      purpose:
        "Produce a response for every selected task within the run limits.",
      steps: [
        "In Local model mode, load the model once and generate each task's output with greedy decoding and the suite's token budget.",
        "In Harness check mode, replay prepared responses without model inference.",
        "Record outputs and timings; require every expected result and stable inputs before completing this stage.",
      ],
      meaning:
        "A pass means execution completed. Output correctness is judged separately. Tasks are independent component checks, and proposed tool calls are not executed.",
    },
    quality: {
      purpose:
        "Decide whether the observed outputs satisfy the declared acceptance criteria.",
      steps: [
        "Check facts, source quotations, and abstention for Q&A.",
        "Check exact fields, JSON types, values, tool names, and arguments for structured tasks.",
        "Evaluate outputs as they arrive, then aggregate their verdicts. In failure replay, compare the evaluator's accept/reject decision with the expected verdict.",
      ],
      meaning:
        "Only a real model run passing all required stages earns Verified offline. A correct clarification or refusal can pass a behavior test while the requested work remains unfinished. Harness success measures the evaluator, not model accuracy.",
    },
  };
  let suite = null,
    report = null,
    selectedKind = null,
    inspectAnswer;
  let stageDefinitions = [];

  function facts(rows) {
    return `<dl class="drill-facts">${rows.map(([key, value]) => `<div><dt>${esc(key)}</dt><dd>${esc(value ?? "Not recorded")}</dd></div>`).join("")}</dl>`;
  }
  function list(items) {
    return `<ul class="drill-list">${items.map((value) => `<li>${esc(value)}</li>`).join("")}</ul>`;
  }
  function checksFor(task) {
    if (task.kind === "grounded_qa")
      return task.answerable
        ? [
            "Exactly answer, source, and quote fields; answer is a string.",
            "Cite the expected document from the retrieved context.",
            "Supply a quotation that exists verbatim in that source.",
            "Include the expected facts in both the answer and quotation.",
          ]
        : [
            "Return NOT_FOUND with source and quote both null.",
            "Do not infer an answer missing from the supplied documents.",
          ];
    if (task.kind === "json_exact")
      return [
        "Return a bare JSON object with exactly the declared fields and types.",
        "Match each expected value; preserve null where specified.",
        "Extra fields, duplicate keys, Markdown fences, or trailing prose fail.",
      ];
    return [
      "Return exactly tool and arguments in a bare JSON object.",
      "Choose an allowed tool with all and only its required arguments, using the declared types.",
      "Match the expected action and exact argument values for this request.",
    ];
  }
  function taskMeaning(task) {
    if (task.kind === "tool_call") {
      if (task.expected.tool === "request_clarification")
        return "Correct clarification is the expected behavior. The underlying request still needs information before work can finish.";
      if (task.expected.tool === "no_action")
        return "Correctly declining this action passes the behavior check. It does not mean the requested external action was completed.";
      return "This verifies the proposed action and its arguments. Actual tool execution and its result are outside this task.";
    }
    if (task.kind === "grounded_qa" && !task.answerable)
      return "Correct abstention is the expected result when local evidence is unavailable.";
    if (task.kind === "json_exact")
      return "The output must represent the input record accurately. Extracting a claim such as verified=true does not independently verify the real-world event.";
    return "The answer must be supported by the selected local sources. These checks do not validate every possible extra claim.";
  }
  function taskHTML(task) {
    const expected =
      task.kind === "grounded_qa"
        ? task.answerable
          ? facts([
              ["Answer must include", task.expected.join("; ")],
              ["Expected source", task.source],
              [
                "Supporting quote",
                "Verbatim text from the retrieved source containing the expected facts",
              ],
            ])
          : json({ answer: "NOT_FOUND", source: null, quote: null })
        : json(task.expected);
    return `<details class="task-disclosure" data-task-id="${esc(task.id)}">
      <summary><strong>${esc(task.id.split(".").pop().replaceAll("-", " "))}</strong><span aria-hidden="true">+</span></summary>
      <div class="drill-body">
        <p class="small-label">TASK INSTRUCTION</p><p class="drill-text">${esc(task.question)}</p>
        ${task.input ? `<p class="small-label">INPUT DATA</p><p class="task-input">${esc(task.input)}</p>` : ""}
        <p class="small-label">REQUIRED RESULT · ACCEPTANCE DEFINITION</p>${expected}
        ${task.fields ? `<details><summary>Field types <span aria-hidden="true">+</span></summary>${json(task.fields)}</details>` : ""}
        ${task.tools ? `<details><summary>Allowed tool contracts · ${task.tools.length} <span aria-hidden="true">+</span></summary>${json(task.tools)}</details>` : ""}
        <p class="small-label">WHAT THE EVALUATOR CHECKS</p>${list(checksFor(task))}
        <p class="drill-note">${esc(taskMeaning(task))}</p>
        <button type="button" class="button" data-task-result="${esc(task.id)}" hidden></button>
      </div>
    </details>`;
  }
  function renderFamily() {
    const root = $("suite-explorer"),
      info = family[selectedKind];
    root.hidden = !info;
    $("suite-kinds")
      .querySelectorAll("button")
      .forEach((button) => {
        button.setAttribute(
          "aria-expanded",
          String(button.dataset.kind === selectedKind),
        );
      });
    if (!info) return;
    const opened = new Set(
      [...root.querySelectorAll("details[data-task-id][open]")].map(
        (d) => d.dataset.taskId,
      ),
    );
    const tasks = suite?.tasks?.filter((t) => t.kind === selectedKind);
    root.innerHTML = `<div class="drill-heading"><div><span class="eyebrow">EXPLORE TASK FAMILY</span><h3 id="suite-explorer-title">${esc(info.name)}</h3></div><button type="button" class="button drill-close" data-close-family aria-label="Close task family details">Close ×</button></div>
      <p class="drill-lead">${esc(info.purpose)}</p><p class="drill-text">${esc(info.relevance)}</p>
      <p class="small-label">${tasks ? `${tasks.length} ${tasks.length === 1 ? "TASK" : "TASKS"} · SELECT ONE TO INSPECT` : "LOADING TASK DEFINITIONS"}</p>
      ${tasks ? tasks.map(taskHTML).join("") : '<p class="hint">The selected suite is being checked. Its task definitions will appear here.</p>'}
      <p class="drill-note"><strong>Tuning focus:</strong> ${esc(info.tuning)}</p>
      <p class="hint">These are acceptance requirements, not measured results. Expected values stay out of real-model prompts.</p>`;
    root.querySelectorAll("details[data-task-id]").forEach((d) => {
      d.open = opened.has(d.dataset.taskId);
    });
    updateResultLinks();
  }
  function sameDefinition() {
    return (
      suite?.id === report?.suite?.id &&
      suite?.files?.length &&
      suite.files.length === report?.inputs?.suite_files?.length &&
      suite.files.every((f) =>
        report.inputs.suite_files.some(
          (old) => old.path === f.path && old.sha256 === f.sha256,
        ),
      )
    );
  }
  function updateResultLinks() {
    const matches = sameDefinition();
    $("suite-explorer")
      .querySelectorAll("[data-task-result]")
      .forEach((button) => {
        const index = matches
          ? (report.answers || []).findIndex(
              (a) => (a.base_task_id || a.id) === button.dataset.taskResult,
            )
          : -1;
        button.hidden = index < 0;
        button.dataset.inspectAnswer = index;
        button.textContent =
          report?.mode === "harness"
            ? "View latest recorded fixture response ↓"
            : "View latest recorded model response ↓";
      });
  }
  function setSuite(value) {
    if (suite?.id !== value?.id) selectedKind = null;
    suite = value;
    if (!suite?.kinds?.includes(selectedKind)) selectedKind = null;
    $("suite-kinds").innerHTML = (suite?.kinds || [])
      .map(
        (kind) =>
          `<button type="button" class="chip suite-kind" id="explore-${esc(kind)}" data-kind="${esc(kind)}" aria-expanded="${kind === selectedKind}" aria-controls="suite-explorer">${esc(family[kind]?.name || kind)} <span aria-hidden="true">↗</span></button>`,
      )
      .join("");
    $("suite-explore-hint").hidden = !suite?.kinds?.length;
    renderFamily();
  }
  function answerLinks(r) {
    return `<div class="drill-results">${(r.answers || []).map((a, index) => `<button type="button" class="drill-result ${a.passed ? "" : "bad"}" data-inspect-answer="${index}"><span>${esc(a.case_label ? `${a.base_task_id.split(".").pop()} · ${a.case_label}` : a.id.split(".").pop().replaceAll("-", " "))}</span><strong>${r.harness ? (a.passed ? "Matched" : "Mismatch") : a.passed ? "Passed" : "Failed"} ↗</strong></button>`).join("")}</div>`;
  }
  function stageEvidence(id) {
    const r = report;
    if (!r)
      return '<p class="hint">No recorded run yet. Run a suite to collect this evidence.</p>';
    const status = r.stages?.find((s) => s.id === id)?.status || "pending";
    const heading = `<p class="small-label">RECORDED EVIDENCE · ${esc(status)}</p>`;
    const error =
      status === "failed" && r.error
        ? `<p class="drill-error">${esc(r.error)}</p>`
        : "";
    let content = "",
      raw;
    if (id === "preflight") {
      content = (r.checks || [])
        .map(
          (c) =>
            `<div class="drill-check ${c.passed ? "" : "bad"}"><strong>${c.passed ? "✓" : "!"} ${esc(c.label)}</strong><p>${esc(c.detail)}${c.remedy ? ` ${esc(c.remedy)}` : ""}</p></div>`,
        )
        .join("");
      raw = r.checks?.length ? r.checks : null;
    } else if (id === "manifest" && Object.keys(r.inputs || {}).length) {
      content = facts([
        ["Document fingerprints", r.inputs.documents?.length ?? 0],
        ["Suite files", r.inputs.suite_files?.length ?? 0],
        ["Application files", Object.keys(r.inputs.application || {}).length],
        ["Model files", r.inputs.model_files?.length ?? 0],
      ]);
      raw = r.inputs;
    } else if (id === "isolation" && Object.keys(r.network || {}).length) {
      content = facts([
        [
          "Enforcement",
          r.network.enforced === true
            ? "All probes denied"
            : r.network.enforced === false
              ? "Not proven"
              : "Awaiting probes",
        ],
        [
          "Witness reachable before sandbox",
          r.network.witness_reachable_before_sandbox === true
            ? "Yes"
            : "Not proven",
        ],
      ]);
      content += (r.network.probes || [])
        .map(
          (p) =>
            `<div class="drill-check ${p.denied ? "" : "bad"}"><strong>${esc(p.label)}</strong><p>${p.denied ? "Permission denied" : "Denial not proven"} · errno ${esc(p.errno)}</p></div>`,
        )
        .join("");
      raw = r.network;
    } else if (id === "workflow" && (r.runtime || r.answers?.length)) {
      content = facts([
        [
          "Execution",
          r.mode === "harness"
            ? "Prepared fixtures · no model"
            : "Real model inference",
        ],
        [
          "Outputs returned",
          `${r.answers?.length || 0} / ${r.harness?.case_count ?? r.suite?.task_count ?? "unknown"}`,
        ],
        [
          "Load time",
          r.runtime?.load_seconds == null
            ? null
            : `${r.runtime.load_seconds} s`,
        ],
        [
          "Generation budget",
          r.generation ? `${r.generation.max_tokens} tokens per task` : null,
        ],
        ["Whole-run elapsed", r.elapsed_s == null ? null : `${r.elapsed_s} s`],
      ]);
      content += answerLinks(r);
      raw = { runtime: r.runtime, generation: r.generation };
    } else if (id === "quality" && r.answers?.length) {
      const passed = r.answers.filter((a) => a.passed).length;
      content = facts([
        [
          r.harness
            ? "Evaluator verdicts matched"
            : r.mode === "harness"
              ? "Fixture acceptance"
              : "Task acceptance",
          `${passed} / ${r.answers.length} evaluated`,
        ],
        ["Expected total", r.harness?.case_count ?? r.suite?.task_count],
        [
          "Measure",
          r.harness
            ? "Evaluator correctness"
            : r.mode === "harness"
              ? "Prepared responses; no model inference"
              : "Component-task acceptance; not end-to-end delivery",
        ],
      ]);
      if (r.harness)
        content += facts([
          ["Valid accepted", r.harness.valid_accepted],
          ["Invalid rejected", r.harness.invalid_rejected],
          ["False accepts", r.harness.false_accepts],
          ["False rejects", r.harness.false_rejects],
        ]);
      content += answerLinks(r);
    }
    return (
      heading +
      error +
      (content ||
        '<p class="hint">No evidence recorded for this stage yet.</p>') +
      (raw
        ? `<details data-evidence-json><summary>Inspect recorded fields <span aria-hidden="true">+</span></summary>${json(raw)}</details>`
        : "")
    );
  }
  function updateStageEvidence(id) {
    const target = $("stage-evidence-" + id);
    const content = stageEvidence(id);
    if (target.dataset.rendered === content) return;
    const wasOpen = target.querySelector("[data-evidence-json]")?.open;
    const focused = target.contains(document.activeElement)
      ? document.activeElement
      : null;
    const answerIndex = focused?.dataset.inspectAnswer;
    const rawFocused =
      focused?.parentElement?.hasAttribute("data-evidence-json");
    target.innerHTML = content;
    target.dataset.rendered = content;
    const raw = target.querySelector("[data-evidence-json]");
    if (raw && wasOpen) raw.open = true;
    if (answerIndex != null)
      target
        .querySelector(`[data-inspect-answer="${answerIndex}"]`)
        ?.focus({ preventScroll: true });
    else if (rawFocused)
      raw?.querySelector("summary")?.focus({ preventScroll: true });
  }
  function updateReport(value) {
    report = value;
    $("stage-context").textContent = report
      ? `Latest recorded run: ${report.suite?.name || "Setup stopped before suite validation"} · ${report.mode === "harness" ? "Harness check" : "Local model"} · ${new Date(report.started_at).toLocaleString()} · ${report.id.slice(0, 8)}. Stage status belongs to this run.`
      : "Explore each stage before running. Recorded evidence will appear after a run starts.";
    for (const [id] of stageDefinitions) {
      const item = $("stage-" + id),
        status = report?.stages?.find((s) => s.id === id)?.status || "pending";
      item.dataset.status = status;
      item.querySelector(".stage").className = "stage " + status;
      item.querySelector(".stage-state").textContent = status;
      item.querySelector(".stage-icon").textContent =
        status === "passed"
          ? "✓"
          : status === "failed"
            ? "!"
            : item.dataset.number;
      if (item.open) updateStageEvidence(id);
    }
    updateResultLinks();
  }
  function init(definitions, onInspectAnswer) {
    inspectAnswer = onInspectAnswer;
    stageDefinitions = definitions;
    $("suite-kinds").onclick = (event) => {
      const button = event.target.closest("[data-kind]");
      if (!button) return;
      selectedKind =
        selectedKind === button.dataset.kind ? null : button.dataset.kind;
      renderFamily();
    };
    $("suite-explorer").onclick = (event) => {
      if (event.target.closest("[data-close-family]")) {
        const previous = selectedKind;
        selectedKind = null;
        renderFamily();
        $("explore-" + previous)?.focus();
      }
      const button = event.target.closest("[data-inspect-answer]");
      if (button) inspectAnswer(Number(button.dataset.inspectAnswer));
    };
    $("stages").innerHTML = definitions
      .map(([id, label, description], index) => {
        const guide = stageGuide[id],
          number = String(index + 1).padStart(2, "0");
        return `<details class="stage-disclosure" id="stage-${id}" data-number="${number}">
        <summary class="stage pending"><span class="stage-icon" aria-hidden="true">${number}</span><div class="stage-title"><strong>${esc(label)}</strong><p>${esc(description)}</p></div><span class="stage-state">pending</span><span class="stage-expand" aria-hidden="true">+</span></summary>
        <div class="stage-detail"><p class="drill-lead">${esc(guide.purpose)}</p><p class="small-label">WHAT HAPPENS</p>${list(guide.steps)}<p class="small-label">WHAT THE RESULT MEANS</p><p class="drill-text">${esc(guide.meaning)}</p><div id="stage-evidence-${id}" class="stage-evidence"></div></div>
      </details>`;
      })
      .join("");
    for (const [id] of definitions)
      $("stage-" + id).ontoggle = () => {
        if ($("stage-" + id).open) updateStageEvidence(id);
      };
    $("stages").onclick = (event) => {
      const button = event.target.closest("[data-inspect-answer]");
      if (button) inspectAnswer(Number(button.dataset.inspectAnswer));
    };
  }
  return { init, setSuite, updateReport };
})();
