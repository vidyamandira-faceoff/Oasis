// ==========================================================================
// TERMINAL MICROSERVICE FRONTEND JAVASCRIPT
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  fetchLogs();
  setInterval(fetchLogs, 2000);
});

async function fetchLogs() {
  try {
    const res = await fetch("/api/terminal/logs");
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById("live-terminal-stream");
    if (!container) return;

    if (data.logs && data.logs.length > 0) {
      container.innerHTML = "";
      data.logs.forEach(log => {
        const div = document.createElement("div");
        div.className = "terminal-line";
        let lvlClass = "";
        if (log.level === "success") lvlClass = "term-success";
        else if (log.level === "warning") lvlClass = "term-warning";
        else if (log.level === "error") lvlClass = "term-error";

        div.innerHTML = `
          <span class="term-time">[${log.timestamp}]</span>
          <span class="term-source">[${escapeHtml(log.source)}]</span>
          <span class="term-msg ${lvlClass}">${escapeHtml(log.message)}</span>
        `;
        container.appendChild(div);
      });
      container.scrollTop = container.scrollHeight;
    }
  } catch (err) {
    // Silent
  }
}

async function clearTerminalLogs() {
  await fetch("/api/terminal/clear", { method: "POST" });
  document.getElementById("live-terminal-stream").innerHTML = "";
}

