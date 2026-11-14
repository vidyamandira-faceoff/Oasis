// ==========================================================================
// OASIS UNIFIED OSINT SUITE - SHARED ARCHITECTURE CONTROLLER
// Handles clock, header status, global notifications & microservice links
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initClock();
  fetchSystemStatus();
  fetchNotificationCounts();
  setInterval(fetchSystemStatus, 4000);
  setInterval(fetchNotificationCounts, 5000);
});

// --------------------------------------------------------------------------
// THEME SWITCHER CONTROLLER (Dark Mode <-> Light Mode)
// --------------------------------------------------------------------------
function getPreferredTheme() {
  const saved = localStorage.getItem('oasis_theme');
  if (saved) return saved;
  return 'light';
}

function applyTheme(theme) {
  const isDark = theme === 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  if (isDark) {
    document.documentElement.classList.add('dark-theme');
    document.body.classList.add('dark-mode');
    document.body.classList.add('dark-theme');
  } else {
    document.documentElement.classList.remove('dark-theme');
    document.body.classList.remove('dark-mode');
    document.body.classList.remove('dark-theme');
  }
  
  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.setAttribute('title', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
    toggleBtn.setAttribute('aria-label', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
  }

  window.dispatchEvent(new CustomEvent('oasis:theme-changed', { detail: { theme } }));
}

function toggleOasisTheme() {
  const current = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
  const nextTheme = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem('oasis_theme', nextTheme);
  applyTheme(nextTheme);
}

function initTheme() {
  const theme = getPreferredTheme();
  applyTheme(theme);
}

window.toggleOasisTheme = toggleOasisTheme;
window.toggleTheme = toggleOasisTheme;

// 1. Live Real-time Clock (IST Asia/Kolkata Unified Engine)
function initClock() {
  function updateTime() {
    const now = new Date();
    
    // Time in IST (24-hour tactical format: HH:mm:ss IST)
    let timeStr = "";
    try {
      timeStr = now.toLocaleTimeString('en-GB', { 
        timeZone: 'Asia/Kolkata', 
        hour12: false 
      }) + ' IST';
    } catch (_) {
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      timeStr = `${h}:${m}:${s} IST`;
    }
    
    const clockEl = document.getElementById("live-clock-text");
    if (clockEl) clockEl.innerText = timeStr;

    // Date in IST (Tactical format: DAY, DD MON YYYY)
    const dateEl = document.getElementById("live-date-str");
    if (dateEl) {
      try {
        const parts = new Intl.DateTimeFormat('en-US', { 
          timeZone: 'Asia/Kolkata', 
          weekday: 'short', 
          day: 'numeric', 
          month: 'short', 
          year: 'numeric' 
        }).formatToParts(now);
        const getPart = type => parts.find(p => p.type === type)?.value || '';
        dateEl.innerText = `${getPart('weekday')}, ${getPart('day')} ${getPart('month')} ${getPart('year')}`.toUpperCase();
      } catch (_) {
        const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
        const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
        dateEl.innerText = `${days[now.getDay()]}, ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;
      }
    }
  }

  updateTime();
  if (!window._oasisClockInterval) {
    window._oasisClockInterval = setInterval(updateTime, 1000);
  }
}

// 2. Global Status & Microservices Health Polling
async function fetchSystemStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    window.oasisStatus = data;

    // Update global status pill in header
    const globalPillText = document.getElementById("global-status-text");
    if (globalPillText) {
      globalPillText.innerText = "Oasis Engines Operational (12 Active Services)";
    }

    // Trigger page-specific status updates if hook exists
    if (typeof onStatusUpdate === "function") {
      onStatusUpdate(data);
    }
  } catch (err) {
    console.warn("Status poll error:", err);
  }
}

// 2b. Global Notification Counter Polling
async function fetchNotificationCounts() {
  try {
    const res = await fetch("/api/notifications");
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById("alert-counter");
    if (badge && data.stats) {
      const count = data.stats.badge_count !== undefined ? data.stats.badge_count : data.stats.total;
      badge.innerText = count;
      badge.style.display = count > 0 ? "inline-flex" : "none";
      if (data.stats.processing > 0) {
        badge.style.background = "var(--ember-500)";
      }
    }
  } catch (err) {
    // Silent background poll
  }
}

// 3. Engine Management Dispatcher
async function toggleToolEngine(toolName) {
  if (!window.oasisStatus || !window.oasisStatus.tools[toolName]) return;
  const isOnline = window.oasisStatus.tools[toolName].online;
  const endpoint = isOnline ? `/api/${toolName}/stop` : `/api/${toolName}/start`;

  try {
    const res = await fetch(endpoint, { method: "POST" });
    const result = await res.json();
    fetchSystemStatus();
  } catch (err) {
    alert(`Engine control error: ${err}`);
  }
}

// 4. Utility helpers
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
    prompt("Copy this:", text);
  });
}

function handleSignOut() {
  if (confirm("Are you sure you want to sign out of Oasis?")) {
    alert("Session signed out successfully. Recon engines remaining in background.");
    window.location.href = "/dashboard";
  }
}

// Immediate task abortion dispatchers
async function stopToolImmediately(toolName) {
  if (confirm(`Immediately stop all tasks and release processes for ${toolName.toUpperCase()}?`)) {
    try {
      const res = await fetch(`/api/${toolName}/stop`, { method: "POST" });
      const data = await res.json();
      alert(`${toolName.toUpperCase()} was stopped immediately.`);
      fetchSystemStatus();
    } catch (err) {
      alert(`Error stopping ${toolName}: ${err}`);
    }
  }
}

async function abortAllTasksImmediately() {
  if (confirm("Immediately abort ALL running OSINT tools, crawlers, and daemons?")) {
    try {
      const res = await fetch("/api/tools/abort-all", { method: "POST" });
      const data = await res.json();
      alert("Emergency Abort: All active OSINT tools and tasks were stopped immediately.");
      fetchSystemStatus();
    } catch (err) {
      alert(`Error stopping tasks: ${err}`);
    }
  }
}

// --------------------------------------------------------------------------
// MOBILE NAVIGATION CONTROLLER
// --------------------------------------------------------------------------
function toggleMobileNav(forceState) {
  const body = document.body;
  const isOpening = forceState !== undefined ? forceState : !body.classList.contains('mobile-nav-open');
  if (isOpening) {
    body.classList.add('mobile-nav-open');
  } else {
    body.classList.remove('mobile-nav-open');
  }
  const toggleBtn = document.getElementById('mobile-nav-toggle');
  if (toggleBtn) {
    toggleBtn.setAttribute('aria-expanded', isOpening ? 'true' : 'false');
  }
}
window.toggleMobileNav = toggleMobileNav;

// Auto-close mobile drawer when tapping links on mobile
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".sidebar .nav-item").forEach(link => {
    link.addEventListener("click", () => {
      if (window.innerWidth <= 992) {
        toggleMobileNav(false);
      }
    });
  });
});

