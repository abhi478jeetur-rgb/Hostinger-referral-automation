/**
 * Canvas Engine & WebSocket Event Handler for Hostinger Autonomous Outreach
 */

class CanvasOrchestrator {
  constructor() {
    this.nodes = [
      "CATEGORY",
      "SCRAPER",
      "AUDITOR",
      "AI_DRAFT",
      "SENDER",
      "LISTENER",
      "PITCH"
    ];
    this.activeNode = "IDLE";
    this.ws = null;
    this.reconnectInterval = 3000;
    this.initWebSocket();
    this.initClearTerminal();
  }

  initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:8000";
    const wsUrl = `${protocol}//${host}/ws/logs`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.appendLog("Connected to Autonomous Engine Stream via WebSocket", "start");
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === "log") {
            const data = payload.data;
            this.appendLog(data.message, data.level, payload.timestamp);
          } else if (payload.type === "state_change") {
            this.handleStateChange(payload.data);
          }
        } catch (e) {
          console.error("WS Parse error", e);
        }
      };

      this.ws.onclose = () => {
        setTimeout(() => this.initWebSocket(), this.reconnectInterval);
      };

      this.ws.onerror = (err) => {
        console.warn("WS error:", err);
      };
    } catch (e) {
      console.warn("WebSocket could not be established immediately:", e);
    }
  }

  handleStateChange(state) {
    const activeNodeName = state.active_node;
    const progress = state.progress_pct || 0;
    const actionText = state.current_action || "";

    // Update Progress Bar
    const bar = document.getElementById("progress-bar-fill");
    const pct = document.getElementById("progress-percentage-val");
    const statusText = document.getElementById("progress-status-text");

    if (bar) bar.style.width = `${progress}%`;
    if (pct) pct.textContent = `${progress}%`;
    if (statusText && actionText) statusText.textContent = actionText;

    // Update Header Status Badge
    const headerStatus = document.getElementById("system-status-badge");
    const headerText = document.getElementById("system-status-text");
    if (headerStatus && headerText) {
      if (state.is_running) {
        headerStatus.className = "badge status-badge active";
        headerText.textContent = `Active (${activeNodeName})`;
      } else {
        headerStatus.className = "badge status-badge idle";
        headerText.textContent = "System Idle";
      }
    }

    // Update Canvas Node Classes
    const activeIndex = this.nodes.indexOf(activeNodeName);

    this.nodes.forEach((nodeName, idx) => {
      const el = document.getElementById(`node-${nodeName}`);
      if (!el) return;

      el.classList.remove("active", "complete");

      if (nodeName === activeNodeName) {
        el.classList.add("active");
      } else if (activeIndex > -1 && idx < activeIndex) {
        el.classList.add("complete");
      }
    });

    // Update button states
    const btnLaunch = document.getElementById("btn-canvas-start");
    const btnStop = document.getElementById("btn-canvas-stop");
    if (btnLaunch && btnStop) {
      btnLaunch.disabled = state.is_running;
      btnStop.disabled = !state.is_running;
    }
  }

  appendLog(message, level = "info", timestamp = null) {
    const terminal = document.getElementById("terminal-logs");
    if (!terminal) return;

    const timeStr = timestamp || new Date().toTimeString().split(" ")[0];
    const line = document.createElement("div");
    line.className = `log-line ${level}`;

    const tagNames = {
      info: "[INFO]",
      scraper: "[SCRAPER]",
      auditor: "[AUDITOR]",
      ai: "[GEMINI AI]",
      success: "[SUCCESS]",
      error: "[ERROR]",
      warning: "[WARNING]",
      start: "[SYSTEM]"
    };

    line.innerHTML = `
      <span class="log-time">[${timeStr}]</span>
      <span class="log-tag">${tagNames[level] || "[LOG]"}</span>
      <span class="log-text">${escapeHtml(message)}</span>
    `;

    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }

  initClearTerminal() {
    const btn = document.getElementById("btn-clear-terminal");
    if (btn) {
      btn.addEventListener("click", () => {
        const terminal = document.getElementById("terminal-logs");
        if (terminal) terminal.innerHTML = "";
      });
    }
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

document.addEventListener("DOMContentLoaded", () => {
  window.canvasOrchestrator = new CanvasOrchestrator();
});
