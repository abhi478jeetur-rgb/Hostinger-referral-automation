"""
Autonomous 24/7 Inbox Reply Listener & Hostinger Referral Pitch Engine.
Monitors IMAP inboxes of configured Gmail accounts, detects incoming replies,
and triggers Gemini AI to craft and dispatch the contextual recommendation (Email #2).
"""

import imaplib
import email
from email.header import decode_header
import time
from typing import List, Dict, Any, Optional, Callable

from database import (
    get_accounts,
    get_connection,
    log_reply_received,
    update_lead_status,
    get_settings,
    get_lead_details
)
from ai_engine import generate_email_2
from email_engine import send_email_dispatch

def decode_mime_words(s: str) -> str:
    """Decodes MIME encoded header strings into readable text."""
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    result = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            result.append(fragment.decode(encoding or "utf-8", errors="ignore"))
        else:
            result.append(str(fragment))
    return "".join(result)

def check_account_for_replies(account: Dict[str, Any], log_fn: Optional[Callable[[str], None]] = None) -> int:
    """
    Checks the IMAP inbox of a single Gmail account for new replies matching our sent leads.
    """
    email_address = account["email"]
    app_pwd = account["app_password"].replace(" ", "").strip()
    replies_processed = 0

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=6)
        mail.login(email_address, app_pwd)
        mail.select("inbox")

        # Search for UNSEEN (unread) messages
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            mail.logout()
            return 0

        email_ids = messages[0].split()
        if log_fn:
            log_fn(f"📬 [{email_address}] Found {len(email_ids)} new unread emails. Checking for client replies...")

        conn = get_connection()
        cursor = conn.cursor()

        for e_id in email_ids[-10:]: # Check last 10 unread
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    from_header = decode_mime_words(msg.get("From", ""))
                    subject = decode_mime_words(msg.get("Subject", ""))
                    in_reply_to = msg.get("In-Reply-To", "")

                    # Extract sender email
                    sender_email = ""
                    if "<" in from_header and ">" in from_header:
                        sender_email = from_header.split("<")[1].split(">")[0].strip().lower()
                    else:
                        sender_email = from_header.strip().lower()

                    # Match lead in database: status should be 'SENT_1'
                    cursor.execute("""
                    SELECT * FROM leads WHERE (email = ? OR ? LIKE '%' || email || '%') AND status = 'SENT_1'
                    """, (sender_email, from_header))
                    lead = cursor.fetchone()

                    if lead:
                        lead_dict = dict(lead)
                        lead_id = lead_dict["id"]
                        
                        # Extract body text
                        reply_body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    reply_body = payload.decode("utf-8", errors="ignore")
                                    break
                        else:
                            reply_body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                        if log_fn:
                            log_fn(f"🎉 Matched Reply from '{lead_dict['business_name']}' ({sender_email})!")

                        # 1. Update status to REPLIED
                        update_lead_status(lead_id, "REPLIED")

                        # 2. Generate Email 2 with Hostinger Referral Link
                        settings = get_settings()
                        ref_link = settings.get("hostinger_referral_link", "https://www.hostinger.com/in?REFERRALCODE=YYUADRASHKGH")
                        pitch_email = generate_email_2(lead_dict, reply_body[:500], ref_link)

                        # 3. Log reply
                        log_reply_received(lead_id, reply_body[:1000], pitch_email["body"])

                        # 4. Dispatch Email 2 (pitch) into the same thread
                        dispatch_res = send_email_dispatch(
                            to_email=lead_dict["email"],
                            subject=pitch_email["subject"],
                            body=pitch_email["body"],
                            lead_id=lead_id,
                            step=2,
                            in_reply_to_msg_id=in_reply_to or msg.get("Message-ID")
                        )

                        if log_fn:
                            log_fn(f"🚀 Contextual Hostinger Pitch (Email #2) sent to {lead_dict['business_name']}!")

                        replies_processed += 1
                        
                        # Mark email as read in Gmail
                        mail.store(e_id, '+FLAGS', '\\Seen')

        conn.close()
        mail.logout()
    except Exception as e:
        if log_fn:
            log_fn(f"⚠️ Inbox check skipped for {email_address}: {e}")

    return replies_processed

def check_all_inboxes_for_replies(log_fn: Optional[Callable[[str], None]] = None) -> int:
    """Runs a sweep across all active connected Gmail accounts."""
    accounts = get_accounts()
    total = 0
    for acc in accounts:
        if acc["is_active"]:
            total += check_account_for_replies(acc, log_fn=log_fn)
    return total

def simulate_client_reply(lead_id: int, sample_reply_text: str, log_fn: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """
    Simulates an incoming client reply so the user can test the autonomous reply & Hostinger pitch workflow live!
    """
    lead = get_lead_details(lead_id)
    if not lead:
        return {"success": False, "error": "Lead not found"}

    if log_fn:
        log_fn(f"📩 Incoming reply simulated from '{lead['business_name']}': '{sample_reply_text}'")

    update_lead_status(lead_id, "REPLIED")

    settings = get_settings()
    ref_link = settings.get("hostinger_referral_link", "https://www.hostinger.com/in?REFERRALCODE=YYUADRASHKGH")
    pitch_email = generate_email_2(lead, sample_reply_text, ref_link)

    log_reply_received(lead_id, sample_reply_text, pitch_email["body"])

    dispatch_res = send_email_dispatch(
        to_email=lead["email"],
        subject=pitch_email["subject"],
        body=pitch_email["body"],
        lead_id=lead_id,
        step=2
    )

    if log_fn:
        log_fn(f"✅ Autonomous Hostinger Pitch (Email #2) Dispatched successfully with referral link!")

    return {
        "success": True,
        "pitch_subject": pitch_email["subject"],
        "pitch_body": pitch_email["body"],
        "dispatch_info": dispatch_res
    }
