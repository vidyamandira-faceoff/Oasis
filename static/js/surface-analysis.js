(function () {
  const page = document.querySelector(".surface-page");
  if (!page) return;
  const moduleName = page.dataset.module;
  const form = document.getElementById("surface-form");
  const resultBox = document.getElementById("surface-results");
  const status = document.getElementById("surface-status");
  const button = form.querySelector("button[type=submit]");
  const defaults = {
    level: Number(page.dataset.defaultLevel || 2),
    threads: Number(page.dataset.defaultThreads || 6)
  };
  document.getElementById("surface-level").value = String(defaults.level);
  document.getElementById("surface-threads").value = String(defaults.threads);
  document.getElementById("surface-keys").checked = moduleName === "website-url";
  document.getElementById("surface-dns").checked = moduleName === "subdomains";

  function renderJob(job) {
    status.textContent = job.status === "completed" ? "Analysis complete" : job.status;
    status.className = `status-chip ${job.status === "completed" ? "status-success" : ""}`;
    if (job.status === "failed") {
      resultBox.innerHTML = `<div class="results-empty"><div class="empty-icon">!</div><h3>Analysis could not be completed</h3><p>${escapeHtml(job.error || "The analysis process reported an error.")}</p></div>`;
      return;
    }
    if (job.status !== "completed") {
      resultBox.innerHTML = `<div class="results-empty"><div class="empty-icon">◌</div><h3>Analysis in progress</h3><p>Collecting public observations for ${escapeHtml(job.target)}. This panel updates automatically.</p></div>`;
      return;
    }
    const summary = Object.entries(job.summary || {}).filter(([, value]) => value > 0).slice(0, 8);
    resultBox.innerHTML = `<div class="result-summary">${summary.length ? summary.map(([key, value]) => `<div class="result-stat"><strong>${value.toLocaleString()}</strong><span>${escapeHtml(key.replaceAll("_", " "))}</span></div>`).join("") : '<div class="result-stat"><strong>0</strong><span>observations</span></div>'}</div><div class="result-log">${(job.logs || []).map(escapeHtml).join("\n") || "No execution log was returned."}</div>`;
  }
  async function poll(jobId) {
    const response = await fetch(`/api/surface/jobs/${jobId}`);
    if (!response.ok) throw new Error("Unable to read analysis status.");
    const job = await response.json();
    renderJob(job);
    if (job.status === "queued" || job.status === "running") setTimeout(() => poll(jobId), 1500);
    else button.disabled = false;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    button.firstElementChild.textContent = "Starting…";
    status.textContent = "Queued";
    const payload = {
      target: document.getElementById("surface-target").value,
      level: Number(document.getElementById("surface-level").value),
      threads: Number(document.getElementById("surface-threads").value),
      keys: document.getElementById("surface-keys").checked,
      dns: document.getElementById("surface-dns").checked,
      wayback: document.getElementById("surface-wayback").checked,
      only_urls: document.getElementById("surface-urls").checked
    };
    try {
      const response = await fetch(`/api/surface/${moduleName}/run`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
      const job = await response.json();
      if (!response.ok) throw new Error(job.detail || "Unable to start analysis.");
      renderJob(job);
      await poll(job.id);
    } catch (error) {
      button.disabled = false;
      button.firstElementChild.textContent = "Start analysis";
      resultBox.innerHTML = `<div class="results-empty"><div class="empty-icon">!</div><h3>Request rejected</h3><p>${escapeHtml(error.message)}</p></div>`;
    } finally {
      button.firstElementChild.textContent = "Start analysis";
    }
  });
  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[char]));
  }
}());
