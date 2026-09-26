/**
 * Main Application Logic for Hostinger Client Acquisition Engine
 */

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  loadCategories();
  loadAnalytics("ALL");
  loadLeads();
  loadAccounts();
  loadSettings();
  initEventListeners();
});

// 1. Tab Switching (Sidebar Navigation)
function initTabs() {
  const tabs = document.querySelectorAll(".nav-item[data-tab]");
  const pageTitles = {
    "tab-canvas": "Workflow Canvas",
    "tab-analytics": "Analytics & ROI",
    "tab-leads": "Leads & Threads",
    "tab-settings": "Settings"
  };

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) targetPane.classList.add("active");

      // Update page title
      const titleEl = document.getElementById("page-title");
      if (titleEl) titleEl.textContent = pageTitles[tab.dataset.tab] || "Dashboard";

      // Auto refresh data on tab click
      if (tab.dataset.tab === "tab-analytics") loadAnalytics();
      if (tab.dataset.tab === "tab-leads") loadLeads();
      if (tab.dataset.tab === "tab-settings") {
        loadAccounts();
        loadSettings();
      }
    });
  });
}

// 2. Load 100 Categories into Select Dropdown
async function loadCategories() {
  const select = document.getElementById("campaign-category-select");
  if (!select) return;

  try {
    const res = await fetch("/api/categories");
    const data = await res.json();
    
    select.innerHTML = "";
    
    // Grouped rendering
    for (const [groupTitle, cats] of Object.entries(data.grouped)) {
      const optGroup = document.createElement("optgroup");
      optGroup.label = groupTitle;
      
      cats.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        if (c === "Real Estate Agencies & Brokers") opt.selected = true;
        optGroup.appendChild(opt);
      });
      select.appendChild(optGroup);
    }
  } catch (e) {
    console.error("Could not load categories", e);
  }
}

// 3. Analytics Loading
async function loadAnalytics(timeframe = "ALL") {
  try {
    const res = await fetch(`/api/stats?timeframe=${timeframe}`);
    const data = await res.json();

    document.getElementById("stat-total-leads").textContent = data.total_leads_collected || 0;
    document.getElementById("stat-emails-sent-1").textContent = data.emails_sent_step_1 || 0;
    document.getElementById("stat-replies-received").textContent = data.replies_received || 0;
    document.getElementById("stat-pitches-sent").textContent = data.emails_sent_step_2 || 0;
    document.getElementById("stat-reply-rate-sub").textContent = `Reply Rate: ${data.reply_rate_percent}%`;

    // Funnel bars
    document.getElementById("funnel-step-1").textContent = data.total_leads_collected || 0;
    document.getElementById("funnel-step-2").textContent = data.emails_sent_step_1 || 0;
    document.getElementById("funnel-step-3").textContent = data.replies_received || 0;
    document.getElementById("funnel-step-4").textContent = data.emails_sent_step_2 || 0;

    // Node Badges on Canvas
    const bScraped = document.getElementById("badge-scraped-count");
    const bDraft = document.getElementById("badge-draft-count");
    const bSent = document.getElementById("badge-sent-count");
    const bRep = document.getElementById("badge-replies-count");
    const bPitch = document.getElementById("badge-pitch-count");

    if (bScraped) bScraped.textContent = `${data.total_leads_collected} Leads`;
    if (bDraft) bDraft.textContent = `${data.emails_sent_step_1} Hooks`;
    if (bSent) bSent.textContent = `${data.emails_sent_step_1} Sent`;
    if (bRep) bRep.textContent = `${data.replies_received} Replies`;
    if (bPitch) bPitch.textContent = `${data.emails_sent_step_2} Pitches`;

  } catch (e) {
    console.error("Error loading stats", e);
  }
}

// 4. Leads Loading & Rendering
async function loadLeads(status = "ALL") {
  const tbody = document.getElementById("leads-tbody");
  if (!tbody) return;

  try {
    const res = await fetch(`/api/leads?limit=100&status=${status}`);
    const data = await res.json();
    const leads = data.leads;

    if (!leads || leads.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4">No leads found in database.</td></tr>`;
      return;
    }

    tbody.innerHTML = leads.map(l => {
      const statusPill = `<span class="pill ${l.status.toLowerCase()}">${l.status}</span>`;
      const ttfbBadge = l.ttfb_seconds ? `${l.ttfb_seconds}s` : "Pending";
      return `
        <tr>
          <td>#${l.id}</td>
          <td><strong>${escapeHtml(l.business_name)}</strong></td>
          <td><code>${escapeHtml(l.email)}</code></td>
          <td><a href="${l.website}" target="_blank" class="text-cyan">${escapeHtml(l.website.substring(0, 30))}</a></td>
          <td>${escapeHtml(l.category)}</td>
          <td><span class="text-amber">${ttfbBadge}</span></td>
          <td>${statusPill}</td>
          <td>
            <button class="btn-tiny" onclick="viewLeadThread(${l.id})">
              <i class="fa-solid fa-eye"></i> View Thread
            </button>
            ${l.status === 'SENT_1' ? `
            <button class="btn-tiny" onclick="simulateReplyPrompt(${l.id})" title="Simulate client reply & trigger referral pitch">
              <i class="fa-solid fa-reply"></i> Test Reply
            </button>` : ''}
          </td>
        </tr>
      `;
    }).join("");
  } catch (e) {
    console.error("Could not load leads", e);
  }
}

// 5. Gmail Accounts Management
async function loadAccounts() {
  const container = document.getElementById("connected-accounts-list");
  if (!container) return;

  try {
    const res = await fetch("/api/accounts");
    const data = await res.json();
    const accounts = data.accounts;

    if (!accounts || accounts.length === 0) {
      container.innerHTML = `
        <div class="text-dim text-center py-3">
          <i class="fa-solid fa-inbox"></i> No Gmail accounts connected yet. The engine will run in Safe Sandbox Mode.
        </div>`;
      return;
    }

    container.innerHTML = accounts.map(a => `
      <div class="account-item-card">
        <div class="acc-info">
          <div class="acc-avatar"><i class="fa-solid fa-envelope"></i></div>
          <div>
            <div class="acc-email">${escapeHtml(a.email)}</div>
            <div class="acc-quota">Sent Today: <strong>${a.daily_sent_count}/20</strong> | Password: ${a.app_password_masked}</div>
          </div>
        </div>
        <div class="acc-actions">
          <span class="pill ${a.is_active ? 'sent_2' : 'new'}">${a.is_active ? 'Active' : 'Paused'}</span>
          <button class="btn-tiny btn-rose" onclick="deleteAccount(${a.id})"><i class="fa-solid fa-trash"></i></button>
        </div>
      </div>
    `).join("");
  } catch (e) {
    console.error("Error loading accounts", e);
  }
}

async function deleteAccount(accId) {
  if (!confirm("Are you sure you want to remove this Gmail account from the rotation pool?")) return;
  try {
    await fetch(`/api/accounts/${accId}`, { method: "DELETE" });
    loadAccounts();
  } catch (e) {
    alert("Error deleting account");
  }
}

// 6. Settings Management
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const settings = await res.json();

    if (settings.hostinger_referral_link) {
      document.getElementById("setting-ref-link").value = settings.hostinger_referral_link;
      // Also update header badge
      const codeMatch = settings.hostinger_referral_link.match(/REFERRALCODE=([A-Z0-9]+)/);
      if (codeMatch) {
        document.getElementById("sidebar-ref-code").textContent = codeMatch[1];
      }
    }
    if (settings.gemini_api_key) {
      document.getElementById("setting-gemini-key").value = settings.gemini_api_key;
    }
    if (settings.supabase_url) {
      document.getElementById("setting-supabase-url").value = settings.supabase_url;
    }
    if (settings.supabase_key) {
      document.getElementById("setting-supabase-key").value = settings.supabase_key;
    }
    if (settings.min_delay_seconds) {
      document.getElementById("setting-min-delay").value = settings.min_delay_seconds;
    }
    if (settings.daily_limit_per_account) {
      document.getElementById("setting-daily-limit").value = settings.daily_limit_per_account;
    }
  } catch (e) {
    console.error("Error loading settings", e);
  }
}

// 7. Event Listeners Setup
function initEventListeners() {
  // Launch Campaign Button
  const btnLaunch = document.getElementById("btn-canvas-start");
  const btnTopStart = document.getElementById("btn-start-top");
  const btnStop = document.getElementById("btn-canvas-stop");

  const launchHandler = async () => {
    const cat = document.getElementById("campaign-category-select").value || "Real Estate Agencies & Brokers";
    const loc = document.getElementById("campaign-location-input").value || "Miami, Florida";
    const count = parseInt(document.getElementById("campaign-target-count").value || "30");

    try {
      const res = await fetch("/api/campaign/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: cat, location: loc, target_count: count, auto_send: true })
      });
      const data = await res.json();
      if (!res.ok) alert(data.detail || "Error starting campaign");
    } catch (e) {
      alert("Network error starting campaign");
    }
  };

  if (btnLaunch) btnLaunch.addEventListener("click", launchHandler);
  if (btnTopStart) btnTopStart.addEventListener("click", () => {
    document.querySelector('.tab-btn[data-tab="tab-canvas"]').click();
    launchHandler();
  });

  if (btnStop) {
    btnStop.addEventListener("click", async () => {
      await fetch("/api/campaign/stop", { method: "POST" });
    });
  }

  // Quick Test 1 Lead
  const btnQuickTest = document.getElementById("btn-quick-test");
  if (btnQuickTest) {
    btnQuickTest.addEventListener("click", async () => {
      const cat = document.getElementById("campaign-category-select").value || "Real Estate Agencies & Brokers";
      const loc = document.getElementById("campaign-location-input").value || "Miami, Florida";

      const modal = document.getElementById("modal-test-overlay");
      const modalBody = document.getElementById("modal-test-body");
      modal.classList.add("open");
      modalBody.innerHTML = `<div class="text-center py-4"><i class="fa-solid fa-spinner fa-spin fa-2x text-cyan"></i><p class="mt-2">Harvesting 1 lead & generating AI Cold Hook preview...</p></div>`;

      try {
        const res = await fetch(`/api/test/single-lead?category=${encodeURIComponent(cat)}&location=${encodeURIComponent(loc)}`, { method: "POST" });
        const data = await res.json();

        modalBody.innerHTML = `
          <div class="lead-preview-box">
            <h4><i class="fa-solid fa-building text-cyan"></i> ${escapeHtml(data.lead.business_name)}</h4>
            <p><strong>Website:</strong> <a href="${data.lead.website}" target="_blank" class="text-cyan">${data.lead.website}</a> | <strong>Email:</strong> <code>${data.lead.email}</code></p>
            <p><strong>Audited TTFB Latency:</strong> <span class="text-amber">${data.lead.ttfb_seconds} seconds</span></p>
            
            <div class="thread-item mt-3">
              <div class="thread-meta"><span>STEP 1: CONCERNED CLIENT HOOK</span></div>
              <div class="thread-subject">Subject: ${escapeHtml(data.email_1_hook.subject)}</div>
              <div class="thread-body">${escapeHtml(data.email_1_hook.body)}</div>
            </div>

            <div class="thread-item reply mt-2">
              <div class="thread-meta"><span>INCOMING CLIENT REPLY (SIMULATED)</span></div>
              <div class="thread-body">"${escapeHtml(data.sample_client_reply)}"</div>
            </div>

            <div class="thread-item pitch mt-2">
              <div class="thread-meta"><span class="text-emerald">STEP 2: HOSTINGER REFERRAL RECOMMENDATION</span></div>
              <div class="thread-subject">Subject: ${escapeHtml(data.email_2_pitch_with_hostinger.subject)}</div>
              <div class="thread-body">${escapeHtml(data.email_2_pitch_with_hostinger.body)}</div>
            </div>
          </div>
        `;
        loadAnalytics();
        loadLeads();
      } catch (e) {
        modalBody.innerHTML = `<p class="text-rose">Error executing test dry-run.</p>`;
      }
    });
  }

  // Modal Close buttons
  const btnCloseTest = document.getElementById("btn-close-test-modal");
  if (btnCloseTest) btnCloseTest.addEventListener("click", () => document.getElementById("modal-test-overlay").classList.remove("open"));

  const btnCloseThread = document.getElementById("btn-close-thread-modal");
  if (btnCloseThread) btnCloseThread.addEventListener("click", () => document.getElementById("modal-thread-overlay").classList.remove("open"));

  // Add Account Form
  const btnAddAcc = document.getElementById("btn-add-account");
  if (btnAddAcc) {
    btnAddAcc.addEventListener("click", async () => {
      const email = document.getElementById("input-acc-email").value.trim();
      const pwd = document.getElementById("input-acc-pwd").value.trim();
      if (!email || !pwd) {
        alert("Please enter both Gmail address and 16-character App Password.");
        return;
      }

      btnAddAcc.disabled = true;
      btnAddAcc.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Verifying...`;

      try {
        const res = await fetch("/api/accounts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, app_password: pwd })
        });
        const data = await res.json();
        if (res.ok) {
          alert("Gmail Account connected successfully!");
          document.getElementById("input-acc-email").value = "";
          document.getElementById("input-acc-pwd").value = "";
          loadAccounts();
        } else {
          alert(data.detail || "Authentication failed. Check your App Password.");
        }
      } catch (e) {
        alert("Network error connecting account.");
      } finally {
        btnAddAcc.disabled = false;
        btnAddAcc.innerHTML = `<i class="fa-solid fa-plus"></i> Connect Account`;
      }
    });
  }

  // Save Settings Form
  const settingsForm = document.getElementById("settings-form");
  if (settingsForm) {
    settingsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        hostinger_referral_link: document.getElementById("setting-ref-link").value.trim(),
        gemini_api_key: document.getElementById("setting-gemini-key").value.trim(),
        supabase_url: document.getElementById("setting-supabase-url").value.trim(),
        supabase_key: document.getElementById("setting-supabase-key").value.trim(),
        min_delay_seconds: parseInt(document.getElementById("setting-min-delay").value || "180"),
        daily_limit_per_account: parseInt(document.getElementById("setting-daily-limit").value || "20")
      };

      try {
        const res = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          alert("Configuration saved successfully!");
          loadSettings();
        }
      } catch (e) {
        alert("Error saving settings");
      }
    });
  }

  // Timeframe selector buttons
  const tfBtns = document.querySelectorAll(".tf-btn");
  tfBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tfBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadAnalytics(btn.dataset.tf);
    });
  });

  // Leads Status Filter
  const statusFilter = document.getElementById("leads-status-filter");
  if (statusFilter) {
    statusFilter.addEventListener("change", (e) => loadLeads(e.target.value));
  }

  // Export CSV
  const btnExport = document.getElementById("btn-export-csv");
  if (btnExport) {
    btnExport.addEventListener("click", () => {
      window.location.href = "/api/leads/export/csv";
    });
  }
}

// 8. Lead Thread Inspector
async function viewLeadThread(leadId) {
  const modal = document.getElementById("modal-thread-overlay");
  const modalBody = document.getElementById("modal-thread-body");
  modal.classList.add("open");
  modalBody.innerHTML = `<div class="text-center py-3"><i class="fa-solid fa-spinner fa-spin"></i> Loading conversation history...</div>`;

  try {
    const res = await fetch(`/api/leads/${leadId}`);
    const lead = await res.json();

    let html = `
      <div class="mb-3">
        <h4>${escapeHtml(lead.business_name)}</h4>
        <p class="text-muted">Target: ${escapeHtml(lead.email)} | Website: ${escapeHtml(lead.website)}</p>
      </div>
    `;

    if (lead.logs && lead.logs.length > 0) {
      lead.logs.forEach(log => {
        const isPitch = log.step === 2;
        html += `
          <div class="thread-item ${isPitch ? 'pitch' : ''}">
            <div class="thread-meta">
              <span>${isPitch ? 'STEP 2: HOSTINGER PITCH' : 'STEP 1: CONCERNED HOOK'} | Sent via: ${log.account_used}</span>
              <span>${log.sent_at}</span>
            </div>
            <div class="thread-subject">Subject: ${escapeHtml(log.subject)}</div>
            <div class="thread-body">${escapeHtml(log.body)}</div>
          </div>
        `;
      });
    }

    if (lead.replies && lead.replies.length > 0) {
      lead.replies.forEach(rep => {
        html += `
          <div class="thread-item reply">
            <div class="thread-meta">
              <span>CLIENT REPLY RECEIVED</span>
              <span>${rep.replied_at}</span>
            </div>
            <div class="thread-body">"${escapeHtml(rep.raw_reply_text)}"</div>
          </div>
        `;
      });
    }

    if ((!lead.logs || lead.logs.length === 0) && (!lead.replies || lead.replies.length === 0)) {
      html += `<p class="text-dim">No emails sent to this lead yet.</p>`;
    }

    modalBody.innerHTML = html;
  } catch (e) {
    modalBody.innerHTML = `<p class="text-rose">Error loading thread.</p>`;
  }
}

// 9. Simulate Reply Prompt
async function simulateReplyPrompt(leadId) {
  const replyText = prompt("Enter a simulated response from the client (e.g. 'Hey, thanks for letting us know! What issues did you face?'):", "Thanks for letting us know! We haven't noticed any slowdowns, but our tech team is checking.");
  if (!replyText) return;

  try {
    const res = await fetch("/api/test/simulate-reply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lead_id: leadId, reply_text: replyText })
    });
    const data = await res.json();
    if (res.ok) {
      alert("Autonomous Pitch triggered! Hostinger referral link dispatched into the thread.");
      loadLeads();
      loadAnalytics();
      viewLeadThread(leadId);
    } else {
      alert(data.detail || "Error simulating reply");
    }
  } catch (e) {
    alert("Network error simulating reply");
  }
}
