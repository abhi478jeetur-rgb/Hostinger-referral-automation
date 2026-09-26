"""
Multi-Gmail Round-Robin Rotator & Smart Drip SMTP Sender.
Rotates across unlimited connected Gmail accounts to maintain pristine sender reputation,
respects daily safety limits (15-20/day/account), and tracks thread IDs.
"""

import smtplib
import ssl
import time
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple

from database import (
    get_accounts,
    log_email_sent,
    update_lead_status,
    get_settings,
    get_connection
)

def test_account_connection(email: str, app_password: str) -> Tuple[bool, str]:
    """
    Validates Google App Password by connecting to smtp.gmail.com over SSL.
    """
    clean_pwd = app_password.replace(" ", "").strip()
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=10) as server:
            server.login(email.strip(), clean_pwd)
        return True, "Connection successful! Ready to send."
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your 16-character App Password (not your normal Gmail password)."
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_next_available_account() -> Optional[Dict[str, Any]]:
    """
    Selects the next active Gmail account that hasn't reached its daily limit.
    Uses round-robin based on least recently used.
    """
    settings = get_settings()
    daily_limit = int(settings.get("daily_limit_per_account", 20))

    accounts = get_accounts()
    active_accounts = [a for a in accounts if a["is_active"] and a["daily_sent_count"] < daily_limit]
    
    if not active_accounts:
        return None

    # Pick account with lowest daily_sent_count or oldest last_used_at
    active_accounts.sort(key=lambda a: (a["daily_sent_count"], a["last_used_at"] or ""))
    return active_accounts[0]

def send_email_dispatch(
    to_email: str,
    subject: str,
    body: str,
    lead_id: int,
    step: int = 1,
    in_reply_to_msg_id: Optional[str] = None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dispatches email using the next available Gmail in the rotation pool.
    """
    account = get_next_available_account()
    
    # If no live Gmail configured yet, operate in simulated preview mode so user can inspect workflow
    if not account:
        simulated_account = "sandbox-preview@hostinger-agent.local"
        sim_msg_id = f"<{uuid.uuid4()}@mail.gmail.com>"
        sim_thread_id = thread_id or f"thread_{uuid.uuid4().hex[:12]}"
        
        log_email_sent(lead_id, simulated_account, step, sim_msg_id, sim_thread_id, subject, body)
        new_status = "SENT_1" if step == 1 else "SENT_2"
        update_lead_status(lead_id, new_status)
        
        return {
            "success": True,
            "simulated": True,
            "account_used": simulated_account,
            "message_id": sim_msg_id,
            "thread_id": sim_thread_id,
            "notice": "Sent in Sandbox Mode (Add a Gmail account in Settings to send live emails)"
        }

    from_email = account["email"]
    app_pwd = account["app_password"].replace(" ", "").strip()

    msg = MIMEMultipart()
    msg["From"] = f"Alex <{from_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg_id = f"<{uuid.uuid4()}@{from_email.split('@')[1]}>"
    msg["Message-ID"] = msg_id

    if in_reply_to_msg_id:
        msg["In-Reply-To"] = in_reply_to_msg_id
        msg["References"] = in_reply_to_msg_id

    assigned_thread_id = thread_id or f"th_{uuid.uuid4().hex[:12]}"
    msg["Thread-Topic"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=15) as server:
            server.login(from_email, app_pwd)
            server.send_message(msg)

        log_email_sent(lead_id, from_email, step, msg_id, assigned_thread_id, subject, body)
        new_status = "SENT_1" if step == 1 else "SENT_2"
        update_lead_status(lead_id, new_status)

        return {
            "success": True,
            "simulated": False,
            "account_used": from_email,
            "message_id": msg_id,
            "thread_id": assigned_thread_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "account_used": from_email
        }
