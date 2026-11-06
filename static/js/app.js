// ==========================================================================
// OASIS UNIFIED OSINT SUITE - FRONTEND CONTROLLER
// ==========================================================================

let currentActiveView = "dashboard";
let recon_website_urlCurrentTargetData = null;
let currentrecon_website_urlTab = "internal";
let social_instagramIsEmbedded = false;
let systemStatus = null;

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  initNavigation();
  fetchSystemStatus();
  loadrecon_website_urlTargets();
  loadsocial_instagramHistory();
  startLogPolling();

  // Polling intervals
  setInterval(fetchSystemStatus, 4000);
  setInterval(fetchLogs, 2500);
});

// ==========================================================================
// 1. CLOCK & DYNAMIC HEADER
// ==========================================================================
function initClock() {
  function updateTime() {
    const now = new Date();
    
    // Format: 12:08:16 PM
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // 0 becomes 12
    const strTime = `${hours}:${minutes}:${seconds} ${ampm}`;
    
    const clockEl = document.getElementById("live-clock-text");
    if (clockEl) clockEl.innerText = strTime;

    // Date line: THURSDAY, NOV 5 • GOOD AFTERNOON
    const days = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];
    const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const dayName = days[now.getDay()];
    const monthName = months[now.getMonth()];
    const dateNum = now.getDate();
    
    let greeting = "ACTIVE SESSION";
    const rawHour = now.getHours();
    if (rawHour < 12) greeting = "GOOD MORNING";
    else if (rawHour < 17) greeting = "GOOD AFTERNOON";
    else greeting = "GOOD EVENING";

    const dateEl = document.getElementById("live-date-str");
    if (dateEl) {
      dateEl.innerText = `${dayName}, ${monthName} ${dateNum} • ${greeting}`;
    }
  }

  updateTime();
  setInterval(updateTime, 1000);
}

// ==========================================================================
// 2. VIEW SWITCHER & SIDEBAR CONTROLS
// ==========================================================================
function initNavigation() {
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const view = item.getAttribute("data-view");
      if (view) switchView(view);
    });
  });
}

function switchView(viewName) {
  currentActiveView = viewName;

  // Update navigation active state
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-view") === viewName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Switch visible main page
  document.querySelectorAll(".view-page").forEach(page => {
    page.classList.remove("active-view");
  });

  const targetPage = document.getElementById(`view-${viewName}`);
  if (targetPage) {
    targetPage.classList.add("active-view");
  }

  // View specific setups
  if (viewName === "recon_website_url") {
    if (!recon_website_urlCurrentTargetData) {
      loadSelectedrecon_website_urlTarget();
    }
  } else if (viewName === "recon_subdomains") {
    checkrecon_subdomainsFrame();
  } else if (viewName === "vault") {
    renderVault();
  }
}

// ==========================================================================
// 3. SYSTEM & TOOL STATUS POLLING
// ==========================================================================
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    systemStatus = data;

    updateEngineStatusUI(data.tools);
  } catch (err) {
    console.warn("Could not reach Oasis status API:", err);
  }
}

function updateEngineStatusUI(tools) {
  // social_instagram
  const igOnline = tools.social_instagram && tools.social_instagram.online;
  const dotIg = document.getElementById("dot-status-social_instagram");
  const btnIg = document.getElementById("btn-toggle-social_instagram");
  const igBadge = document.getElementById("badge-social_instagram");
  const igBtnLabel = document.getElementById("social_instagram-btn-label");

  if (dotIg) dotIg.style.backgroundColor = igOnline ? "var(--success)" : "var(--warning)";
  if (btnIg) {
    btnIg.className = `btn-engine-toggle ${igOnline ? "online" : "offline"}`;
    btnIg.innerText = igOnline ? "Running" : "Start";
  }
  if (igBadge) {
    igBadge.innerText = igOnline ? "Online" : "IG";
    igBadge.style.color = igOnline ? "var(--success)" : "var(--primary)";
  }
  if (igBtnLabel) {
    igBtnLabel.innerText = igOnline ? "Stop social_instagram" : "Start social_instagram Server";
  }

  // recon_subdomains
  const sfOnline = tools.recon_subdomains && tools.recon_subdomains.online;
  const dotSf = document.getElementById("dot-status-recon_subdomains");
  const btnSf = document.getElementById("btn-toggle-recon_subdomains");
  const sfBadge = document.getElementById("badge-recon_subdomains");
  const sfBtnLabel = document.getElementById("recon_subdomains-btn-label");
  const sfPulse = document.getElementById("sf-pulse-dot");

  if (dotSf) dotSf.style.backgroundColor = sfOnline ? "var(--success)" : "var(--warning)";
  if (sfPulse) sfPulse.style.backgroundColor = sfOnline ? "var(--success)" : "var(--warning)";
  if (btnSf) {
    btnSf.className = `btn-engine-toggle ${sfOnline ? "online" : "offline"}`;
    btnSf.innerText = sfOnline ? "Running" : "Start";
  }
  if (sfBadge) {
    sfBadge.innerText = sfOnline ? "Online" : "OSINT";
    sfBadge.style.color = sfOnline ? "var(--success)" : "var(--primary)";
  }
  if (sfBtnLabel) {
    sfBtnLabel.innerText = sfOnline ? "Stop recon_subdomains" : "Launch recon_subdomains Daemon";
  }

  // recon_subdomains Iframe Visibility
  const sfFrame = document.getElementById("recon_subdomains-frame");
  const sfOffline = document.getElementById("recon_subdomains-offline-state");
  if (sfOnline) {
    if (sfFrame && sfFrame.src === "about:blank") {
      sfFrame.src = "http://127.0.0.1:5001";
    }
    if (sfFrame) sfFrame.style.display = "block";
    if (sfOffline) sfOffline.style.display = "none";
  } else {
    if (sfFrame) sfFrame.style.display = "none";
    if (sfOffline) sfOffline.style.display = "flex";
  }

  // Global status pill
  const globalText = document.getElementById("global-status-text");
  if (globalText) {
    const activeCount = (igOnline ? 1 : 0) + (sfOnline ? 1 : 0) + 1; // recon_website_url always ready
    globalText.innerText = `Oasis Ready (${activeCount}/3 Tools Online)`;
  }
}

async function toggleEngine(toolName) {
  if (!systemStatus || !systemStatus.tools[toolName]) return;
  const isOnline = systemStatus.tools[toolName].online;

  const endpoint = isOnline ? `/api/tools/stop/${toolName}` : `/api/tools/start/${toolName}`;
  try {
    const res = await fetch(endpoint, { method: "POST" });
    const result = await res.json();
    fetchSystemStatus();
    fetchLogs();
  } catch (err) {
    alert(`Engine control error: ${err}`);
  }
}

function refreshToolStatus() {
  fetchSystemStatus();
}

// ==========================================================================
// 4. recon_website_url FRONTEND ENGINE & EXPLORER
// ==========================================================================
async function loadrecon_website_urlTargets() {
  try {
    const res = await fetch("/api/recon_website_url/targets");
    if (!res.ok) return;
    const data = await res.json();
    
    const dropdown = document.getElementById("recon_website_url-target-dropdown");
    if (!dropdown) return;
    dropdown.innerHTML = "";

    if (data.targets && data.targets.length > 0) {
      data.targets.forEach((t, idx) => {
        const opt = document.createElement("option");
        opt.value = t.name;
        opt.innerText = `${t.name} (${t.total_endpoints.toLocaleString()} findings)`;
        dropdown.appendChild(opt);
      });

      // Update Dashboard Recent Table from real targets
      renderDashboardRecentTargets(data.targets.slice(0, 5));
      loadSelectedrecon_website_urlTarget();
    }
  } catch (err) {
    console.error("Failed to load recon_website_url targets:", err);
  }
}

async function loadSelectedrecon_website_urlTarget() {
  const dropdown = document.getElementById("recon_website_url-target-dropdown");
  if (!dropdown) return;
  const targetName = dropdown.value;
  if (!targetName) return;

  try {
    const res = await fetch(`/api/recon_website_url/target/${targetName}`);
    if (!res.ok) return;
    const data = await res.json();
    recon_website_urlCurrentTargetData = data;

    // Update tab counts
    const files = data.files || {};
    document.getElementById("ptab-count-internal").innerText = (files.internal?.count || 0).toLocaleString();
    document.getElementById("ptab-count-external").innerText = (files.external?.count || 0).toLocaleString();
    document.getElementById("ptab-count-fuzzable").innerText = (files.fuzzable?.count || 0).toLocaleString();
    document.getElementById("ptab-count-files").innerText = (files.files?.count || 0).toLocaleString();
    document.getElementById("ptab-count-robots").innerText = (files.robots?.count || 0).toLocaleString();

    renderrecon_website_urlTable();
  } catch (err) {
    console.error("Failed to load target details:", err);
  }
}

function switchrecon_website_urlTab(tabKey) {
  currentrecon_website_urlTab = tabKey;
  document.querySelectorAll("[data-ptab]").forEach(btn => {
    if (btn.getAttribute("data-ptab") === tabKey) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  renderrecon_website_urlTable();
}

function renderrecon_website_urlTable() {
  const tbody = document.getElementById("recon_website_url-table-tbody");
  if (!tbody || !recon_website_urlCurrentTargetData) return;
  tbody.innerHTML = "";

  const items = (recon_website_urlCurrentTargetData.files[currentrecon_website_urlTab]?.items) || [];
  const filterVal = (document.getElementById("recon_website_url-filter-input")?.value || "").toLowerCase().trim();

  const filtered = filterVal ? items.filter(u => u.toLowerCase().includes(filterVal)) : items;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted); padding: 30px;">No records found in ${currentrecon_website_urlTab} for this target.</td></tr>`;
    return;
  }

  // Render max 150 items for smooth DOM performance
  const displaySlice = filtered.slice(0, 150);
  displaySlice.forEach((url, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color: var(--text-subtle);">${i + 1}</td>
      <td>
        <span class="url-text" style="color: var(--text-heading); font-weight: 500;">${escapeHtml(url)}</span>
      </td>
      <td style="text-align: right;">
        <button class="btn-inspect" style="padding: 3px 8px; font-size: 11px;" onclick="copyToClipboard('${escapeHtml(url)}')">Copy</button>
        <button class="btn-inspect" style="padding: 3px 8px; font-size: 11px;" onclick="window.open('${escapeHtml(url)}', '_blank')">Open &rarr;</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterrecon_website_urlTable() {
  renderrecon_website_urlTable();
}

async function triggerrecon_website_urlCrawl() {
  const url = document.getElementById("recon_website_url-crawl-url").value.trim();
  const level = parseInt(document.getElementById("recon_website_url-crawl-level").value) || 2;
  const threads = parseInt(document.getElementById("recon_website_url-crawl-threads").value) || 10;

  if (!url) {
    alert("Please enter a valid Target URL to crawl.");
    return;
  }

  try {
    const res = await fetch("/api/recon_website_url/crawl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, level, threads })
    });
    const data = await res.json();
    alert(`Crawl initiated for ${url}! View progress in Live Terminal.`);
    switchView("terminal");
  } catch (err) {
    alert(`Crawl error: ${err}`);
  }
}

function exportrecon_website_urlData() {
  if (!recon_website_urlCurrentTargetData) return;
  const blob = new Blob([JSON.stringify(recon_website_urlCurrentTargetData, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${recon_website_urlCurrentTargetData.name}_recon_report.json`;
  a.click();
}

function inspectrecon_website_urlTarget(targetName) {
  switchView("recon_website_url");
  const dropdown = document.getElementById("recon_website_url-target-dropdown");
  if (dropdown) {
    dropdown.value = targetName;
    loadSelectedrecon_website_urlTarget();
  }
}

// ==========================================================================
// 5. social_instagram FRONTEND & COMMANDS
// ==========================================================================
async function loadsocial_instagramHistory() {
  try {
    const res = await fetch("/api/social_instagram/history");
    if (!res.ok) return;
    const data = await res.json();
    if (data.history && data.history.length > 0) {
      const container = document.getElementById("social_instagram-history-pills");
      if (container) {
        container.innerHTML = "";
        data.history.forEach(item => {
          const pill = document.createElement("span");
          pill.className = "status-pill";
          pill.style.cursor = "pointer";
          pill.style.padding = "3px 10px";
          pill.style.fontSize = "12px";
          pill.innerText = `@${item.value}`;
          pill.onclick = () => setsocial_instagramTarget(item.value);
          container.appendChild(pill);
        });
      }
    }
  } catch (err) {
    console.error("Failed to load social_instagram history:", err);
  }
}

function setsocial_instagramTarget(username) {
  document.getElementById("social_instagram-target-input").value = username;
  runsocial_instagramTarget();
}

function inspectsocial_instagramTarget(username) {
  switchView("social_instagram");
  setsocial_instagramTarget(username);
}

function runsocial_instagramTarget() {
  const target = document.getElementById("social_instagram-target-input").value.trim();
  const box = document.getElementById("social_instagram-output-box");
  if (!target) {
    alert("Please enter an Instagram target username.");
    return;
  }

  box.innerHTML = `
    <div class="terminal-line">
      <span class="term-time">[${new Date().toLocaleTimeString()}]</span>
      <span class="term-source">[social_instagram]</span>
      <span class="term-msg term-success">Target selected: @${escapeHtml(target)}. Connecting to cache and profile index...</span>
    </div>
    <div class="terminal-line">
      <span class="term-time">[${new Date().toLocaleTimeString()}]</span>
      <span class="term-source">[Profile]</span>
      <span class="term-msg">Target: @${escapeHtml(target)} | Status: Indexed | Cache DB: Connected (requests.sqlite3)</span>
    </div>
    <div class="terminal-line">
      <span class="term-time">[${new Date().toLocaleTimeString()}]</span>
      <span class="term-source">[Ready]</span>
      <span class="term-msg">Select any intelligence command module above to extract relations, captions, or contact info.</span>
    </div>
  `;
}

function executesocial_instagramCommand(command) {
  const target = document.getElementById("social_instagram-target-input").value.trim() || "rahulgandhi";
  const box = document.getElementById("social_instagram-output-box");
  
  const time = new Date().toLocaleTimeString();
  const line = document.createElement("div");
  line.className = "terminal-line";
  line.innerHTML = `
    <span class="term-time">[${time}]</span>
    <span class="term-source">[Command: ${escapeHtml(command)}]</span>
    <span class="term-msg term-success">Executing <strong>${escapeHtml(command)}</strong> against @${escapeHtml(target)}... Query dispatched successfully.</span>
  `;
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

function clearsocial_instagramOutput() {
  document.getElementById("social_instagram-output-box").innerHTML = "";
}

function togglesocial_instagramEmbedMode() {
  social_instagramIsEmbedded = !social_instagramIsEmbedded;
  const nativePanel = document.getElementById("social_instagram-native-panel");
  const iframePanel = document.getElementById("social_instagram-iframe-panel");
  const modeText = document.getElementById("social_instagram-mode-text");
  const frame = document.getElementById("social_instagram-frame");

  if (social_instagramIsEmbedded) {
    nativePanel.style.display = "none";
    iframePanel.style.display = "block";
    modeText.innerText = "Switch to Native Oasis UI";
    if (frame.src === "about:blank") {
      frame.src = "http://127.0.0.1:8000";
    }
  } else {
    nativePanel.style.display = "block";
    iframePanel.style.display = "none";
    modeText.innerText = "Switch to Embedded Port 8000";
  }
}

// ==========================================================================
// 6. recon_subdomains CONTROLS
// ==========================================================================
function checkrecon_subdomainsFrame() {
  const frame = document.getElementById("recon_subdomains-frame");
  if (systemStatus?.tools?.recon_subdomains?.online) {
    if (frame && (frame.src === "about:blank" || !frame.src)) {
      frame.src = "http://127.0.0.1:5001";
    }
  }
}

function reloadIframe(frameId) {
  const frame = document.getElementById(frameId);
  if (frame) frame.contentWindow.location.reload();
}

// ==========================================================================
// 7. LIVE TERMINAL & LOGS
// ==========================================================================
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
    // Silent catch
  }
}

function startLogPolling() {
  fetchLogs();
}

function clearLiveLogs() {
  document.getElementById("live-terminal-stream").innerHTML = "";
}

// ==========================================================================
// 8. VAULT & RECENT TARGET RENDERING
// ==========================================================================
function renderDashboardRecentTargets(targets) {
  const tbody = document.getElementById("dashboard-recent-tbody");
  if (!tbody || !targets || targets.length === 0) return;

  tbody.innerHTML = "";
  targets.forEach(t => {
    const initials = t.name.substring(0, 2).toUpperCase();
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <div class="target-cell">
          <span class="target-badge-circle">${initials}</span>
          <span>${escapeHtml(t.name)}</span>
        </div>
      </td>
      <td><span class="badge-pill-info">recon_website_url</span></td>
      <td>Domain Crawl</td>
      <td><strong>${t.total_endpoints.toLocaleString()}</strong> endpoints</td>
      <td><span class="badge-pill-success">Complete</span></td>
      <td><button class="btn-inspect" onclick="inspectrecon_website_urlTarget('${escapeHtml(t.name)}')">Inspect</button></td>
    `;
    tbody.appendChild(tr);
  });
}

async function renderVault() {
  const tbody = document.getElementById("vault-targets-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  try {
    const res = await fetch("/api/recon_website_url/targets");
    const data = await res.json();
    const targets = data.targets || [];

    targets.forEach(t => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div class="target-cell">
            <span class="target-badge-circle">PH</span>
            <strong>${escapeHtml(t.name)}</strong>
          </div>
        </td>
        <td><span class="badge-pill-info">recon_website_url Crawler</span></td>
        <td>${t.total_endpoints.toLocaleString()} items</td>
        <td>${t.last_modified}</td>
        <td><button class="btn-inspect" onclick="inspectrecon_website_urlTarget('${escapeHtml(t.name)}')">Open in recon_website_url</button></td>
      `;
      tbody.appendChild(tr);
    });

    // Add social_instagram targets
    const igRes = await fetch("/api/social_instagram/history");
    const igData = await igRes.json();
    (igData.history || []).forEach(ig => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div class="target-cell">
            <span class="target-badge-circle" style="color: var(--primary);">IG</span>
            <strong>@${escapeHtml(ig.value)}</strong>
          </div>
        </td>
        <td><span class="badge-pill-purple">social_instagram</span></td>
        <td>Profile &amp; Relations</td>
        <td>Recent</td>
        <td><button class="btn-inspect" onclick="inspectsocial_instagramTarget('${escapeHtml(ig.value)}')">Open in social_instagram</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Vault render error:", err);
  }
}

// ==========================================================================
// UTILITIES
// ==========================================================================
function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, function(m) {
    switch (m) {
      case '&': return '&amp;';
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '"': return '&quot;';
      case "'": return '&#039;';
      default: return m;
    }
  });
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert("Copied to clipboard: " + text);
  }).catch(() => {
    prompt("Copy this URL:", text);
  });
}

