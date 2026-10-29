const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const pretty = (value) => JSON.stringify(value, null, 2);
const kindNames = {
  grounded_qa: "Grounded Q&A",
  json_exact: "Extraction",
  tool_call: "Tool selection",
};
const titles = {
  running: "Proof in progress",
  verified: "Verified offline",
  failed: "Proof needs attention",
  harness_passed: "Harness passed · no model",
};
const stages = [
  ["preflight", "Check local setup", "Suite, inputs, model, and runtime"],
  ["manifest", "Fingerprint the inputs", "SHA-256 hashes of the files used"],
  [
    "isolation",
    "Block and test network access",
    "OS policy + four connection-denial probes",
  ],
  [
    "workflow",
    "Run acceptance tasks",
    "Generate outputs from the selected suite",
  ],
  [
    "quality",
    "Verify outputs and contracts",
    "Facts, JSON types, tool names, and arguments",
  ],
];
let state,
  mode = "mlx",
  selectedAnswer = 0,
  checked = [],
  busy = false,
  suiteInfo = null,
  checkSequence = 0;
const openDetails = new Set();
function saved(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}
function save(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {}
}
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $("theme").textContent = theme === "dark" ? "Light" : "Dark";
  save("scout-proof-theme", theme);
}
applyTheme(saved("scout-proof-theme", "dark"));
$("theme").onclick = () =>
  applyTheme(
    document.documentElement.dataset.theme === "dark" ? "light" : "dark",
  );
function config() {
  return {
    model: $("model-path").value,
    python: $("python-path").value,
    documents: $("documents-path").value,
    mode,
    suite: $("suite-select").value || $("suite-path").value,
    harness_case: $("harness-case").value,
  };
}
function alertMessage(message) {
  $("alert").textContent = message || "";
  $("alert").hidden = !message;
}
async function request(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Scout-Token": state.token,
    },
    body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) throw Error(result.error || "Request failed");
  return result;
}
function renderChecks(checks) {
  $("checks").innerHTML = checks
    .map(
      (c) =>
        `<div class="check-row ${c.passed ? "" : "bad"}"><span>${c.passed ? "✓" : "!"}</span><div><strong>${esc(c.label)}</strong>${!c.passed ? `<p>${esc(c.detail)} ${esc(c.remedy)}</p>` : ""}</div></div>`,
    )
    .join("");
}
function renderSuite() {
  const s = suiteInfo;
  $("custom-suite").hidden = $("suite-select").value !== "";
  $("task-count").textContent = s ? `${s.task_count} tasks` : "Not validated";
  $("suite-description").textContent =
    s?.description ||
    "Choose a suite or enter a local JSON file, then check setup.";
  $("suite-kinds").innerHTML = (s?.kinds || [])
    .map((k) => `<span class="chip">${esc(kindNames[k] || k)}</span>`)
    .join("");
}
function renderMode() {
  for (const m of ["mlx", "harness"]) {
    $("mode-" + m).classList.toggle("active", mode === m);
    $("mode-" + m).setAttribute("aria-pressed", String(mode === m));
  }
  $("harness-options").hidden = mode !== "harness";
  $("mode-note").textContent =
    mode === "mlx"
      ? "Real inference. Only a passing model run earns “Verified offline.”"
      : "Fixed fixtures test the evaluator. No language model runs.";
  $("mode-note").classList.toggle("warning", mode === "harness");
}
function expectedFailure(r) {
  return (
    r?.mode === "harness" &&
    r.config?.harness_case &&
    ["wrong-answer", "malformed-json"].includes(r.config.harness_case) &&
    r.stages?.some((s) => s.id === "quality" && s.status === "failed")
  );
}
function title(r) {
  if (r?.harness && r.status !== "running")
    return r.status === "harness_passed"
      ? "Evaluator checks passed"
      : "Evaluator check failed";
  return expectedFailure(r)
    ? "Fixture errors detected"
    : titles[r?.status] || "No proof run yet";
}
function render() {
  if (!state) return;
  const r = state.report,
    active = state.active || busy;
  $("connection").textContent = "Connected locally";
  $("machine-name").textContent = state.info.machine.host;
  $("machine-spec").textContent =
    `${state.info.machine.chip || state.info.machine.architecture} · ${Math.round((state.info.machine.memory_bytes || 0) / 1073741824)} GB RAM`;
  document.querySelector(".status-strip").className =
    "status-strip " + (r?.status || "");
  $("result-title").textContent = title(r);
  $("result-suite").textContent = r
    ? r.suite?.name || "Grounded document Q&A · previous run"
    : "";
  $("result-symbol").textContent =
    r?.status === "verified"
      ? "✓"
      : r?.status === "failed"
        ? "!"
        : r?.status === "running"
          ? "◌"
          : "○";
  $("network-value").textContent = r?.network?.enforced
    ? "Access denied"
    : r?.network?.enforced === false
      ? "Not enforced"
      : "Awaiting test";
  $("score-value").innerHTML =
    `${r ? (r.answers || []).filter((a) => a.passed).length : "—"} <span>/ ${r ? (r.harness?.case_count ?? r.suite?.task_count ?? (r.answers?.length || "—")) : "—"}</span>`;
  $("score-label").textContent = r?.harness ? "CASES VERIFIED" : "TASKS PASSED";
  $("time-value").textContent = r
    ? `${r.elapsed_s?.toFixed(1) || "0.0"} s`
    : "—";
  $("export").disabled = !r || active;
  for (const id of [
    "run",
    "check",
    "mode-mlx",
    "mode-harness",
    "model-select",
    "model-path",
    "python-path",
    "documents-path",
    "suite-select",
    "suite-path",
    "harness-case",
  ])
    $(id).disabled = active;
  $("run").textContent = active
    ? "Running proof…"
    : mode === "harness"
      ? "Run harness check ↗"
      : "Run offline proof ↗";
  $("stages").innerHTML = stages
    .map(([id, label, description], i) => {
      const status = r?.stages?.find((s) => s.id === id)?.status || "pending";
      return `<div class="stage ${status}"><span class="stage-icon">${status === "passed" ? "✓" : status === "failed" ? "!" : String(i + 1).padStart(2, "0")}</span><div><strong>${label}</strong><p>${description}</p></div><span class="stage-state">${status === "pending" ? "" : status}</span></div>`;
    })
    .join("");
  renderChecks(active && r?.checks?.length ? r.checks : checked);
  if (active) alertMessage("");
  else if (r?.error)
    alertMessage(
      expectedFailure(r)
        ? "The evaluator rejected the deliberately broken fixtures. These are harness results, not model results."
        : r.error,
    );
  else alertMessage("");
  $("evidence-label").textContent = !r
    ? "WAITING FOR A RUN"
    : r.mode === "harness"
      ? "HARNESS · NO INFERENCE"
      : r.status === "running"
        ? "COLLECTING EVIDENCE"
        : "MODEL EVIDENCE";
  const model = r?.config?.model?.split("/").filter(Boolean).pop();
  $("report-meta").textContent = r
    ? `${r.suite?.name || "Original Q&A suite"} · ${r.mode === "harness" ? `Fixtures: ${r.config?.harness_case || "valid"}` : model || "Local model"} · ${new Date(r.started_at).toLocaleString()}`
    : "";
  $("harness-summary").hidden = !r?.harness;
  if (r?.harness) {
    const h = r.harness;
    $("harness-summary").innerHTML =
      `<p class="hint">Evaluator self-test · ${r.suite.task_count} tasks, ${h.case_count} fixture cases. A case passes when the evaluator makes the expected accept/reject decision. This is not model accuracy.</p><div class="category-results"><div class="category-result">Valid accepted<b>${h.valid_accepted}/${h.valid_cases}</b></div><div class="category-result">Invalid rejected<b>${h.invalid_rejected}/${h.invalid_cases}</b></div><div class="category-result ${h.false_accepts ? "bad" : ""}">False accepts<b>${h.false_accepts}</b></div><div class="category-result ${h.false_rejects ? "bad" : ""}">False rejects<b>${h.false_rejects}</b></div></div>`;
  }
  const answers = r?.answers || [],
    categories = {};
  for (const a of answers) {
    const k = a.kind || "grounded_qa";
    categories[k] ??= { passed: 0, total: 0 };
    categories[k].total++;
    if (a.passed) categories[k].passed++;
  }
  $("category-results").innerHTML = Object.entries(categories)
    .map(
      ([k, v]) =>
        `<div class="category-result ${v.passed === v.total ? "" : "bad"}">${esc(kindNames[k] || k)}<b>${v.passed}/${v.total}</b></div>`,
    )
    .join("");
  if (answers.length) {
    selectedAnswer = Math.min(selectedAnswer, answers.length - 1);
    const a = answers[selectedAnswer],
      p = a.parsed,
      qa = !a.kind || a.kind === "grounded_qa";
    const response = qa
      ? `<h3>${esc(p?.answer === "NOT_FOUND" ? "Not found in the supplied documents." : p?.answer || "Response could not be validated")}</h3>${p?.source ? `<span class="source-tag">↳ ${esc(p.source)}</span><blockquote>${esc(p.quote)}</blockquote>` : ""}`
      : `<pre>${esc(p == null ? "Response could not be parsed." : pretty(p))}</pre>`;
    const verdict = r.harness
      ? `<div class="case-verdict ${a.passed ? "" : "bad"}"><strong>${a.passed ? "Expected decision matched" : "Evaluator decision mismatch"}</strong><span>Expected: ${a.expected_accept ? "accept" : "reject"} · Evaluator: ${a.validator_accepted ? "accepted" : "rejected"}</span></div>`
      : "";
    const detailsKey = `${r.id}:${a.id}`;
    $("evidence-content").innerHTML =
      `<div class="evidence-layout"><div class="answer-list">${answers.map((answer, i) => `<button class="answer-card ${answer.passed ? "" : "failed"} ${i === selectedAnswer ? "selected" : ""}" data-answer="${i}" aria-pressed="${i === selectedAnswer}"><span class="answer-icon">${answer.passed ? "✓" : "!"}</span><div><strong>${esc(answer.case_label ? `${answer.base_task_id.split(".").pop().replaceAll("-", " ")} · ${answer.case_label}` : answer.kind && answer.kind !== "grounded_qa" ? answer.id.split(".").pop().replaceAll("-", " ") : answer.question)}</strong><small>${answer.case_label ? (answer.passed ? (answer.expected_accept ? "ACCEPTED AS EXPECTED" : "REJECTED AS EXPECTED") : "MISMATCH") : answer.passed ? "PASSED" : "FAILED"} · ${esc(kindNames[answer.kind] || "Grounded Q&A")} · ${answer.seconds.toFixed(2)} s</small></div></button>`).join("")}</div><div class="answer-detail"><span class="eyebrow">${r.mode === "harness" ? "FIXTURE RESPONSE" : "MODEL RESPONSE"}</span>${verdict}${response}${a.input ? `<details><summary>Task input <span>+</span></summary><p class="task-input">${esc(a.question)}\n\n${esc(a.input)}</p></details>` : ""}${a.checks.map((c) => `<div class="answer-check ${c.passed ? "" : "bad"}">${c.passed ? "✓" : "✕"} ${esc(c.label)}${c.detail ? `: ${esc(c.detail)}` : ""}</div>`).join("")}${!qa ? `<details><summary>${r.harness ? "Reference correct output" : "Expected output"} <span>+</span></summary><pre>${esc(pretty(a.expected))}</pre></details>` : ""}<details id="raw-response" ${openDetails.has(detailsKey) ? "open" : ""}><summary>Inspect raw response <span>+</span></summary><pre>${esc(a.raw)}</pre></details></div></div>${networkHTML(r)}`;
    document.querySelectorAll("[data-answer]").forEach(
      (b) =>
        (b.onclick = () => {
          selectedAnswer = Number(b.dataset.answer);
          render();
        }),
    );
    $("raw-response").ontoggle = () =>
      $("raw-response").open
        ? openDetails.add(detailsKey)
        : openDetails.delete(detailsKey);
  } else if (r) {
    $("evidence-content").innerHTML =
      `<div class="empty-evidence"><strong>${r.status === "failed" ? "Setup stopped this run before outputs were produced." : "Waiting for the first task result."}</strong><p>${r.status === "failed" ? "Review the setup checks and export the report for details." : "The runner proves network denial before loading the model."}</p></div>${networkHTML(r)}`;
  }
  $("history").innerHTML = state.history.length
    ? state.history
        .slice(0, 5)
        .map(
          (h) =>
            `<div class="history-row"><span>${esc(new Date(h.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }))}</span><b>${esc(titles[h.status] || h.status)}<small>${esc(h.suite?.name || "Original Q&A suite")}</small></b><span>${h.elapsed_s?.toFixed(1)}s</span></div>`,
        )
        .join("")
    : "No saved runs on this machine.";
}
function networkHTML(r) {
  if (!r.network?.probes) return "";
  return `<div class="network-evidence"><span class="eyebrow">NETWORK DENIAL · LIVE PROBES</span><div class="probe-grid">${r.network.probes.map((p) => `<div class="probe ${p.denied ? "" : "bad"}"><span>${esc(p.label)}</span><code>${p.denied ? "DENIED" : "NOT DENIED"} · errno ${p.errno}</code></div>`).join("")}</div><p class="network-footnote">Local witness reachable before sandboxing: ${r.network.witness_reachable_before_sandbox ? "yes" : "not proven"}. Only OS permission errors count as denial.</p></div>`;
}
async function poll() {
  try {
    const response = await fetch("/api/state");
    if (!response.ok) throw Error("Unavailable");
    const next = await response.json();
    const changed = pretty(next) !== pretty(state);
    state = next;
    if (changed) render();
  } catch {
    $("connection").textContent = "Connection lost";
    alertMessage(
      "The local server is unavailable. Restart it and refresh this page.",
    );
  }
}
async function check() {
  if (!state) return;
  const sequence = ++checkSequence,
    settings = config();
  save("scout-proof-settings", settings);
  $("check").disabled = true;
  alertMessage("");
  try {
    const response = await request("/api/preflight", settings);
    if (sequence !== checkSequence) return;
    checked = response.checks;
    suiteInfo = response.suite;
    renderChecks(checked);
    renderSuite();
  } catch (e) {
    if (sequence === checkSequence) alertMessage(e.message);
  } finally {
    if (sequence === checkSequence) $("check").disabled = state.active || busy;
  }
}
function setMode(value) {
  mode = value;
  renderMode();
  render();
  check();
}
$("mode-mlx").onclick = () => setMode("mlx");
$("mode-harness").onclick = () => {
  $("harness-case").value = "failure-replay";
  setMode("harness");
};
$("suite-select").onchange = () => {
  suiteInfo =
    state.info.suites.find((s) => s.id === $("suite-select").value) || null;
  renderSuite();
  check();
};
$("model-select").onchange = () => {
  if ($("model-select").value) {
    $("model-path").value = $("model-select").value;
    check();
  } else {
    $("advanced").open = true;
    $("model-path").focus();
  }
};
for (const id of [
  "suite-path",
  "harness-case",
  "model-path",
  "python-path",
  "documents-path",
])
  $(id).onchange = check;
$("check").onclick = check;
$("run").onclick = async () => {
  alertMessage("");
  busy = true;
  selectedAnswer = 0;
  let error = "";
  render();
  try {
    await request("/api/run", config());
    await poll();
  } catch (e) {
    error = e.message;
  } finally {
    busy = false;
    render();
    if (error) alertMessage(error);
  }
};
$("export").onclick = () => {
  window.location.href = "/api/report";
};
async function init() {
  await poll();
  if (!state) return;
  const settings = {
    ...state.info.defaults,
    suite: "all",
    ...saved("scout-proof-settings", {}),
  };
  $("model-select").innerHTML =
    state.info.models
      .map(
        (m) =>
          `<option value="${esc(m.path)}">${esc(m.name)} · ${(m.bytes / 1e9).toFixed(1)} GB · ${m.path.startsWith("/Volumes/A1/") ? "A1" : "Mac"}</option>`,
      )
      .join("") + '<option value="">Enter a different local path…</option>';
  $("suite-select").innerHTML =
    state.info.suites
      .map(
        (s) =>
          `<option value="${esc(s.id)}">${esc(s.name)} · ${s.task_count} tasks</option>`,
      )
      .join("") + '<option value="">Custom JSON file…</option>';
  for (const [id, key] of [
    ["model-path", "model"],
    ["python-path", "python"],
    ["documents-path", "documents"],
    ["harness-case", "harness_case"],
  ])
    $(id).value = settings[key];
  $("model-select").value = state.info.models.some(
    (m) => m.path === settings.model,
  )
    ? settings.model
    : "";
  $("suite-select").value = state.info.suites.some(
    (s) => s.id === settings.suite,
  )
    ? settings.suite
    : "";
  $("suite-path").value = $("suite-select").value ? "" : settings.suite;
  suiteInfo = state.info.suites.find((s) => s.id === settings.suite) || null;
  mode = settings.mode === "harness" ? "harness" : "mlx";
  renderMode();
  renderSuite();
  render();
  await check();
  setInterval(poll, 1000);
}
init();
