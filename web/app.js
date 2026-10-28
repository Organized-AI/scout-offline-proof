const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
let state,
  mode = "mlx",
  selectedAnswer = 0,
  checked = [],
  busy = false;
const stages = [
  [
    "preflight",
    "Check local setup",
    "Model, tokenizer, runtime, and documents",
  ],
  [
    "manifest",
    "Fingerprint the inputs",
    "SHA-256 hashes of the files used in this run",
  ],
  [
    "isolation",
    "Block and test network access",
    "OS policy + live connection-denial probes",
  ],
  [
    "workflow",
    "Run document questions",
    "Retrieve sources and generate local answers",
  ],
  [
    "quality",
    "Verify answers and sources",
    "Expected facts, exact quotations, and abstention",
  ],
];
const titles = {
  running: "Proof in progress",
  verified: "Verified offline",
  failed: "Proof needs attention",
  harness_passed: "Harness passed · no model",
};

function config() {
  return {
    model: $("model-path").value,
    python: $("python-path").value,
    documents: state.info.defaults.documents,
    mode,
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
  if (!response.ok) throw new Error(result.error || "Request failed");
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
function render() {
  const r = state.report,
    active = state.active || busy;
  $("connection").textContent = "Connected locally";
  $("machine-name").textContent = state.info.machine.host;
  $("machine-spec").textContent =
    `${state.info.machine.chip || state.info.machine.architecture} · ${Math.round((state.info.machine.memory_bytes || 0) / 1073741824)} GB RAM`;
  document.querySelector(".status-strip").className =
    "status-strip " + (r?.status || "");
  $("result-title").textContent = r ? titles[r.status] : "No proof run yet";
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
    `${r?.answers?.length ? r.answers.filter((a) => a.passed).length : "—"} <span>/ 3</span>`;
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
  ])
    $(id).disabled = active;
  $("run").innerHTML = active
    ? "Running proof… <span>◌</span>"
    : mode === "harness"
      ? "Run harness check <span>↗</span>"
      : "Run offline proof <span>↗</span>";
  $("stages").innerHTML = stages
    .map(([id, label, description], i) => {
      const status = r?.stages?.find((s) => s.id === id)?.status || "pending";
      return `<div class="stage ${status}"><span class="stage-icon">${status === "passed" ? "✓" : status === "failed" ? "!" : String(i + 1).padStart(2, "0")}</span><div><strong>${label}</strong><p>${description}</p></div><span class="stage-state">${status === "pending" ? "" : status}</span></div>`;
    })
    .join("");
  renderChecks(active && r?.checks?.length ? r.checks : checked);
  if (active) alertMessage("");
  else if (r?.error) alertMessage(r.error);
  $("evidence-label").textContent = r
    ? r.mode === "harness"
      ? "HARNESS · NO INFERENCE"
      : r.status === "running"
        ? "COLLECTING EVIDENCE"
        : "RECORDED EVIDENCE"
    : "WAITING FOR A RUN";
  const answers = r?.answers || [];
  if (answers.length) {
    selectedAnswer = Math.min(selectedAnswer, answers.length - 1);
    const a = answers[selectedAnswer],
      p = a.parsed;
    $("evidence-content").innerHTML =
      `<div class="evidence-layout"><div class="answer-list">${answers.map((answer, i) => `<button class="answer-card ${answer.passed ? "" : "failed"} ${i === selectedAnswer ? "selected" : ""}" data-answer="${i}" aria-pressed="${i === selectedAnswer}"><span class="answer-icon">${answer.passed ? "✓" : "!"}</span><div><strong>${esc(answer.question)}</strong><small>${answer.passed ? "PASSED" : "FAILED"} · ${answer.seconds.toFixed(2)} s</small></div></button>`).join("")}</div><div class="answer-detail"><span class="eyebrow muted">${p?.answer === "NOT_FOUND" ? "CORRECT ABSTENTION" : "MODEL RESPONSE"}</span><h3>${esc(p?.answer === "NOT_FOUND" ? "Not found in the supplied documents." : p?.answer || "Response could not be validated")}</h3>${p?.source ? `<span class="source-tag">↳ ${esc(p.source)}</span><blockquote>${esc(p.quote)}</blockquote>` : ""}${a.checks.map((c) => `<div class="answer-check ${c.passed ? "" : "bad"}">${c.passed ? "✓" : "✕"} ${esc(c.label)}</div>`).join("")}<details><summary>Inspect raw response <span>+</span></summary><pre>${esc(a.raw)}</pre></details></div></div>${networkHTML(r)}`;
    document.querySelectorAll("[data-answer]").forEach(
      (b) =>
        (b.onclick = () => {
          selectedAnswer = Number(b.dataset.answer);
          render();
        }),
    );
  } else if (r) {
    $("evidence-content").innerHTML =
      `<div class="empty-evidence"><span class="empty-icon">${r.status === "failed" ? "!" : "⌕"}</span><div><strong>${r.status === "failed" ? "Setup stopped this run before answers were produced." : "Waiting for the model to finish the first question."}</strong><p>${r.status === "failed" ? "Review the diagnostics above. Failed runs are evidence too; export the report to inspect the checks." : "The runner checks network isolation before loading any model weights."}</p></div></div>${networkHTML(r)}`;
  }
  $("history").innerHTML = state.history.length
    ? state.history
        .slice(0, 3)
        .map(
          (h) =>
            `<div class="history-row"><span>${esc(new Date(h.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }))}</span><b>${esc(titles[h.status] || h.status)}</b><span>${h.elapsed_s?.toFixed(1)}s</span></div>`,
        )
        .join("")
    : "<span>No saved runs on this machine.</span>";
}
function networkHTML(r) {
  if (!r.network?.probes) return "";
  return `<div class="network-evidence"><span class="eyebrow muted">NETWORK DENIAL · LIVE PROBES</span><div class="probe-grid">${r.network.probes.map((p) => `<div class="probe ${p.denied ? "" : "bad"}"><span>${esc(p.label)}</span><code>${p.denied ? "DENIED" : "NOT DENIED"} · errno ${p.errno}</code></div>`).join("")}</div><p class="network-footnote">The local witness was reachable before sandboxing: ${r.network.witness_reachable_before_sandbox ? "yes" : "not proven"}. Only OS permission errors count as denied; a timeout or refused connection does not.</p></div>`;
}
async function poll() {
  try {
    const response = await fetch("/api/state");
    if (!response.ok) throw Error("Dashboard unavailable");
    const next = await response.json();
    const changed = JSON.stringify(next) !== JSON.stringify(state);
    state = next;
    if (changed) render();
  } catch (error) {
    $("connection").textContent = "Connection lost";
    alertMessage(
      "The local server is unavailable. Restart it and refresh this page.",
    );
  }
}
async function check() {
  if (!state) return;
  $("check").disabled = true;
  alertMessage("");
  try {
    const response = await request("/api/preflight", config());
    checked = response.checks;
    renderChecks(checked);
  } catch (e) {
    alertMessage(e.message);
  } finally {
    $("check").disabled = false;
  }
}
function setMode(value) {
  mode = value;
  checked = [];
  for (const m of ["mlx", "harness"]) {
    $("mode-" + m).classList.toggle("active", mode === m);
    $("mode-" + m).setAttribute("aria-pressed", String(mode === m));
  }
  $("mode-note").textContent =
    mode === "mlx"
      ? "Real inference. Your model stays on this machine."
      : "Tests orchestration with fixed answers. Never earns “Verified offline.”";
  $("mode-note").classList.toggle("warning", mode === "harness");
  render();
  check();
}
$("mode-mlx").onclick = () => setMode("mlx");
$("mode-harness").onclick = () => setMode("harness");
$("model-select").onchange = () => {
  if ($("model-select").value) {
    $("model-path").value = $("model-select").value;
    check();
  } else {
    $("advanced").open = true;
    $("model-path").focus();
  }
};
$("model-path").onchange = check;
$("python-path").onchange = check;
$("check").onclick = check;
$("run").onclick = async () => {
  alertMessage("");
  busy = true;
  selectedAnswer = 0;
  render();
  try {
    await request("/api/run", config());
    await poll();
  } catch (e) {
    alertMessage(e.message);
  } finally {
    busy = false;
    render();
  }
};
$("export").onclick = () => {
  window.location.href = "/api/report";
};
async function init() {
  await poll();
  if (!state) return;
  $("model-select").innerHTML =
    state.info.models
      .map(
        (m) =>
          `<option value="${esc(m.path)}">${esc(m.name)} · ${(m.bytes / 1e9).toFixed(1)} GB</option>`,
      )
      .join("") + '<option value="">Enter a different local path…</option>';
  $("model-path").value = state.info.defaults.model;
  $("python-path").value = state.info.defaults.python;
  if (!state.info.models.length) $("advanced").open = true;
  await check();
  setInterval(poll, 1000);
}
init();
