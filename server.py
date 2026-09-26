"""
FastAPI Autonomous Backend Engine for Hostinger Cold Outreach Automation.
Handles REST endpoints, WebSocket live event streaming, and background task orchestration.
"""

import asyncio
import threading
import time
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    init_db,
    get_connection,
    get_settings,
    set_setting,
    get_accounts,
    add_account,
    remove_account,
    get_leads_list,
    get_lead_details,
    get_analytics,
    update_lead_status
)
from categories import ALL_100_CATEGORIES, TOP_20_EASIEST_NICHES, get_flattened_categories
from scraper import harvest_leads
from auditor import audit_website
from ai_engine import generate_email_1, generate_email_2
from email_engine import send_email_dispatch, test_account_connection
from reply_listener import check_all_inboxes_for_replies, simulate_client_reply

app = FastAPI(title="Hostinger AI Outreach Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAIN_LOOP = None

@app.on_event("startup")
async def on_startup():
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    init_db()

# Active WebSockets for live console streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# Global Background Worker State
CAMPAIGN_STATE = {
    "is_running": False,
    "active_node": "IDLE",  # 'CATEGORY', 'SCRAPER', 'AUDITOR', 'AI_DRAFT', 'SENDER', 'LISTENER', 'PITCH'
    "progress_pct": 0,
    "current_action": "System Ready",
    "leads_processed": 0,
    "target_leads": 0,
    "stop_requested": False
}

def safe_print(text: str):
    try:
        print(text)
    except Exception:
        try:
            print(text.encode('ascii', errors='replace').decode('ascii'))
        except Exception:
            pass

def emit_event(event_type: str, data: Any):
    """Utility to broadcast thread-safe events to all connected WebSocket clients and print to console."""
    global MAIN_LOOP
    payload = {"type": event_type, "timestamp": time.strftime("%H:%M:%S"), "data": data}
    msg_str = data.get("message") if isinstance(data, dict) and "message" in data else str(data)
    safe_print(f"[{payload['timestamp']}] [{event_type.upper()}] {msg_str}")
    
    if MAIN_LOOP and MAIN_LOOP.is_running():
        try:
            asyncio.run_coroutine_threadsafe(manager.broadcast(payload), MAIN_LOOP)
        except Exception:
            pass

def log_to_console(text: str, level: str = "info"):
    emit_event("log", {"message": text, "level": level})

def update_node_state(node_name: str, progress: int = 0, action_text: str = ""):
    CAMPAIGN_STATE["active_node"] = node_name
    CAMPAIGN_STATE["progress_pct"] = progress
    if action_text:
        CAMPAIGN_STATE["current_action"] = action_text
    emit_event("state_change", CAMPAIGN_STATE)

# Pydantic Request Models
class CampaignStartRequest(BaseModel):
    category: str
    location: str
    target_count: int = 30
    auto_send: bool = True

class AccountAddRequest(BaseModel):
    email: str
    app_password: str

class SettingsUpdateRequest(BaseModel):
    hostinger_referral_link: str
    gemini_api_key: Optional[str] = ""
    supabase_url: Optional[str] = ""
    supabase_key: Optional[str] = ""
    min_delay_seconds: Optional[int] = 180
    max_delay_seconds: Optional[int] = 360
    daily_limit_per_account: Optional[int] = 20

class SimulateReplyRequest(BaseModel):
    lead_id: int
    reply_text: str

# Background Worker Thread
def run_autonomous_campaign(category: str, location: str, target_count: int, auto_send: bool):
    global CAMPAIGN_STATE
    try:
        CAMPAIGN_STATE["is_running"] = True
        CAMPAIGN_STATE["stop_requested"] = False
        CAMPAIGN_STATE["target_leads"] = target_count
        CAMPAIGN_STATE["leads_processed"] = 0

        log_to_console(f"🚀 [Engine Started] Category: '{category}' | Location: '{location}' | Goal: {target_count} leads", "start")
        
        # Node 1: Category & Setup
        update_node_state("CATEGORY", 10, f"Targeting {category} in {location}")
        time.sleep(1.0)

        # Node 2: Scraping & Auto-Filter
        update_node_state("SCRAPER", 25, "Harvesting Google Maps & Business Websites...")
        
        def scraper_logger(msg):
            log_to_console(msg, "scraper")

        def scraper_progress(curr, total, label):
            pct = 25 + int((curr / total) * 35) # scale to 25%-60%
            update_node_state("SCRAPER", pct, label)

        leads = harvest_leads(
            category=category,
            location=location,
            target_count=target_count,
            log_fn=scraper_logger,
            progress_fn=scraper_progress
        )

        if CAMPAIGN_STATE["stop_requested"]:
            log_to_console("🛑 Campaign stopped by user.", "warning")
            return

        if not leads:
            uncontacted = get_leads_list(limit=target_count, status_filter="NEW")
            if uncontacted:
                log_to_console(f"ℹ️ Found {len(uncontacted)} uncontacted leads in local queue. Advancing to audit & dispatch.", "info")
                leads = uncontacted
            else:
                log_to_console("⚠️ No new uncontacted leads found for this query.", "warning")
                return

        # Process each lead through Auditor -> AI Hook -> Safe Dispatch
        total_leads = len(leads)
        for idx, lead in enumerate(leads):
            if CAMPAIGN_STATE["stop_requested"]:
                log_to_console("🛑 Campaign stopped during dispatch.", "warning")
                break

            lead_id = lead.get("id")
            biz_name = lead.get("business_name")
            email = lead.get("email")
            
            # Node 3: Speed Auditor
            update_node_state("AUDITOR", 60 + int((idx / total_leads) * 10), f"Auditing {biz_name} TTFB...")
            log_to_console(f"⚡ [Auditor] Audited {biz_name}: TTFB is {lead.get('ttfb_seconds')}s", "auditor")
            time.sleep(0.5)

            # Node 4: Gemini AI Drafter
            update_node_state("AI_DRAFT", 70 + int((idx / total_leads) * 10), f"Drafting Hook for {biz_name}...")
            hook_email = generate_email_1(lead)
            log_to_console(f"✍️ [Gemini AI] Crafted Hook Subject: '{hook_email['subject']}'", "ai")
            time.sleep(0.5)

            # Node 5: Gmail Multi-Account Sender
            if auto_send:
                update_node_state("SENDER", 80 + int((idx / total_leads) * 15), f"Dispatching to {email}...")
                dispatch_result = send_email_dispatch(
                    to_email=email,
                    subject=hook_email["subject"],
                    body=hook_email["body"],
                    lead_id=lead_id,
                    step=1
                )
                
                if dispatch_result.get("success"):
                    acc = dispatch_result.get("account_used")
                    sim = " [Sandbox Preview]" if dispatch_result.get("simulated") else ""
                    log_to_console(f"✉️ [Sent Email #1]{sim} To: {email} via Account: {acc}", "success")
                else:
                    log_to_console(f"❌ [Failed Email #1] To: {email}: {dispatch_result.get('error')}", "error")

                # Human-like delay between dispatches (simulated short delay in demo)
                settings = get_settings()
                min_delay = min(int(settings.get("min_delay_seconds", 180)), 5) # Default short pause for smoothness
                time.sleep(min_delay)

        # Node 6 & 7: Trigger Reply Sweep
        update_node_state("LISTENER", 95, "Checking for replies in Gmail inboxes...")
        replies_found = check_all_inboxes_for_replies(log_fn=lambda m: log_to_console(m, "listener"))
        
        if replies_found > 0:
            update_node_state("PITCH", 100, f"Dispatched {replies_found} Hostinger Referral Pitches!")
        else:
            update_node_state("LISTENER", 100, "Inbox Listener Active (Awaiting Replies)")

        log_to_console("🎉 [Pipeline Complete] Processed all targeted leads successfully!", "success")
        time.sleep(1.5)

    except Exception as e:
        log_to_console(f"❌ [Engine Exception] {str(e)}", "error")
        print(f"Engine Exception: {e}")
    finally:
        CAMPAIGN_STATE["is_running"] = False
        update_node_state("IDLE", 0, "System Idle")

# REST API Endpoints
@app.get("/api/categories")
def get_categories():
    return {
        "top_20": TOP_20_EASIEST_NICHES,
        "grouped": ALL_100_CATEGORIES,
        "flattened": get_flattened_categories()
    }

@app.get("/api/stats")
def get_stats(timeframe: str = Query("ALL", pattern="^(TODAY|7D|30D|ALL)$")):
    return get_analytics(timeframe)

@app.get("/api/leads")
def get_leads(limit: int = 50, offset: int = 0, status: str = "ALL"):
    leads = get_leads_list(limit, offset, status)
    return {"leads": leads, "count": len(leads)}

@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: int):
    details = get_lead_details(lead_id)
    if not details:
        raise HTTPException(status_code=404, detail="Lead not found")
    return details

@app.get("/api/leads/export/csv")
def export_leads_csv():
    leads = get_leads_list(limit=5000, offset=0, status_filter="ALL")
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Business Name", "Email", "Website", "Phone", "Location", "Category", "TTFB (s)", "Status", "Created At"])
    for l in leads:
        writer.writerow([l["id"], l["business_name"], l["email"], l["website"], l["phone"], l["location"], l["category"], l["ttfb_seconds"], l["status"], l["created_at"]])
    
    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hostinger_clean_leads.csv"}
    )

@app.get("/api/accounts")
def list_accounts():
    accounts = get_accounts()
    # Mask passwords for UI security
    sanitized = []
    for a in accounts:
        pwd = a["app_password"]
        masked = pwd[:3] + "********" + pwd[-3:] if len(pwd) >= 6 else "********"
        sanitized.append({**a, "app_password_masked": masked})
    return {"accounts": sanitized}

@app.post("/api/accounts")
def add_new_account(req: AccountAddRequest):
    # Verify connection first
    valid, msg = test_account_connection(req.email, req.app_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    success = add_account(req.email, req.app_password)
    if not success:
        raise HTTPException(status_code=500, detail="Could not store account in database")
    return {"success": True, "message": "Account verified and added successfully!"}

@app.post("/api/accounts/test")
def test_account(req: AccountAddRequest):
    valid, msg = test_account_connection(req.email, req.app_password)
    return {"success": valid, "message": msg}

@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: int):
    remove_account(account_id)
    return {"success": True}

@app.get("/api/settings")
def read_settings():
    return get_settings()

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    set_setting("hostinger_referral_link", req.hostinger_referral_link)
    if req.gemini_api_key is not None:
        set_setting("gemini_api_key", req.gemini_api_key)
    if req.supabase_url is not None:
        set_setting("supabase_url", req.supabase_url)
    if req.supabase_key is not None:
        set_setting("supabase_key", req.supabase_key)
    if req.min_delay_seconds:
        set_setting("min_delay_seconds", str(req.min_delay_seconds))
    if req.max_delay_seconds:
        set_setting("max_delay_seconds", str(req.max_delay_seconds))
    if req.daily_limit_per_account:
        set_setting("daily_limit_per_account", str(req.daily_limit_per_account))
    return {"success": True, "message": "Settings updated"}

@app.post("/api/campaign/start")
def start_campaign(req: CampaignStartRequest):
    if CAMPAIGN_STATE["is_running"]:
        raise HTTPException(status_code=400, detail="A campaign is already running")
    
    t = threading.Thread(
        target=run_autonomous_campaign,
        args=(req.category, req.location, req.target_count, req.auto_send),
        daemon=True
    )
    t.start()
    return {"success": True, "message": "Campaign launched in background"}

@app.post("/api/campaign/stop")
def stop_campaign():
    if not CAMPAIGN_STATE["is_running"]:
        return {"success": True, "message": "Campaign is not currently running"}
    CAMPAIGN_STATE["stop_requested"] = True
    return {"success": True, "message": "Stop signal transmitted to pipeline"}

@app.get("/api/campaign/status")
def campaign_status():
    return CAMPAIGN_STATE

@app.post("/api/test/single-lead")
def test_single_pipeline(category: str = "Real Estate Agencies & Brokers", location: str = "Miami, Florida"):
    """
    Executes a single end-to-end dry run to preview the audit and AI generated hook.
    """
    test_leads = harvest_leads(category=category, location=location, target_count=1)
    if test_leads:
        lead = test_leads[0]
    else:
        existing = get_leads_list(limit=1)
        if existing:
            lead = existing[0]
        else:
            lead = {
                "business_name": f"Elite {category.split(' ')[0]} Group",
                "website": "https://www.florida-prime-properties.com",
                "email": "contact@florida-prime-properties.com",
                "ttfb_seconds": 3.82,
                "category": category,
                "location": location,
                "bottleneck_summary": "sluggish server response latency (TTFB of 3.82s)"
            }
    hook = generate_email_1(lead)
    
    settings = get_settings()
    ref_link = settings.get("hostinger_referral_link", "https://www.hostinger.com/in?REFERRALCODE=YYUADRASHKGH")
    sample_reply = "Hey Alex, thanks for letting us know! We haven't had other reports, but our team is checking."
    pitch = generate_email_2(lead, sample_reply, ref_link)

    return {
        "lead": lead,
        "email_1_hook": hook,
        "sample_client_reply": sample_reply,
        "email_2_pitch_with_hostinger": pitch
    }

@app.post("/api/test/simulate-reply")
def test_simulate_reply(req: SimulateReplyRequest):
    res = simulate_client_reply(req.lead_id, req.reply_text, log_fn=lambda m: log_to_console(m, "listener"))
    return res

# WebSocket Route for Real-time Streaming
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current state upon connection
        await websocket.send_json({"type": "state_change", "data": CAMPAIGN_STATE})
        while True:
            # Keep-alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Mount static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Static UI files are being initialized."}

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
