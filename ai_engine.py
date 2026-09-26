"""
Gemini AI Prompt Engine for Autonomous 2-Step Soft Pitch Funnel.
Powered by Google Gemini 2.0 Flash / 1.5 Flash REST API with high-converting psychology copy fallback.

Strategy:
  1. Email #1: "The Concerned Prospective Customer" (Zero sales pitch, high curiosity, 40%+ open rate)
  2. Email #2: "The Peer Solution & Hostinger Soft Pitch" (Delivered ONLY upon reply, natural affiliate link placement)
"""

import os
import random
import requests
from typing import Dict, Any, Optional
from database import get_settings

SYSTEM_PROMPT = """
You are a master conversion copywriter specializing in natural, high-trust consumer-to-business communications.
Your sole job is writing organic, empathetic, non-salesy emails in pure, fluent English.

CRITICAL INSTRUCTIONS:
- LANGUAGE: ALWAYS write 100% in English. Never use any other language or non-English characters.
- IDENTITY: You are an everyday customer/visitor who genuinely tried to use the business's website from a smartphone or laptop.
- ZERO MARKETING JARGON: Never say "digital marketing", "SEO audit", "web agency", "synergy", or "pitch".
- NO SPAM TRIGGERS: Never say "guaranteed", "buy now", "limited offer", "exclusive deal", or "click here".
- FORMAT: Clean plain text only. No markdown asterisks (**bold**), no HTML, no brackets, no placeholders.
- LENGTH: 3 to 5 concise, natural sentences with normal paragraph spacing.
"""

# Rotating natural sender aliases for believable peer communication
SENDER_NAMES = ["Alex", "Sam", "Chris", "Jordan", "Taylor", "Morgan", "Ryan"]

def call_gemini_api(prompt_text: str) -> Optional[str]:
    """Direct REST call to Gemini 2.0 Flash / 1.5 Flash."""
    settings = get_settings()
    api_key = settings.get("gemini_api_key", "").strip() or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None

    models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt_text}"}]}
            ],
            "generationConfig": {
                "temperature": 0.65,
                "maxOutputTokens": 450
            }
        }
        try:
            res = requests.post(url, json=payload, timeout=8.0)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            continue
    return None

def generate_email_1(lead: Dict[str, Any]) -> Dict[str, str]:
    """
    Step 1: The 'Concerned Prospect' Hook
    Triggers the business owner's fear of losing paying customers without raising sales resistance.
    """
    biz_name = lead.get("business_name", "Team")
    website = lead.get("website", "")
    ttfb = round(float(lead.get("ttfb_seconds", 3.4)), 1)
    sender = random.choice(SENDER_NAMES)

    prompt = f"""
STRICT REQUIREMENT: Output MUST be 100% in English only.

Write Email #1 from an interested visitor to {biz_name} ({website}).

Context:
- You were trying to look up their services / details on {website} today from your mobile phone.
- The website had noticeable lag, taking around {ttfb} seconds to respond, and you noticed a delay before anything rendered.
- You wanted to let them know politely in case their contact form or customer inquiries are being affected.

Copywriting Rules:
- Subject Line: 3-6 words, ultra-casual, curiosity-driven (e.g., "Quick question regarding {biz_name}", "Trouble loading {website} earlier today", "Quick note regarding your website loading").
- Body: 
  * Greet them warmly (e.g., "Hi {biz_name} team,").
  * State simply that you were checking out their website from mobile earlier today.
  * Mention politely that the page took roughly {ttfb}s to load and lagged before opening.
  * Ask if this was just temporary server maintenance on their end or if others have reported loading issues.
  * Sign off naturally with "{sender}".
- STRICT: NO mention of hosting companies, NO sales pitch, NO links.

Output format strictly:
SUBJECT: <subject line>
BODY:
<plain text email body>
"""
    ai_text = call_gemini_api(prompt)
    if ai_text and "SUBJECT:" in ai_text and "BODY:" in ai_text:
        parts = ai_text.split("BODY:")
        subject = parts[0].replace("SUBJECT:", "").strip()
        body = parts[1].strip()
        return {"subject": subject, "body": body}

    # Deterministic high-converting copywriting fallback
    subject_options = [
        f"Quick question regarding {biz_name} website",
        f"Trouble loading {website} earlier today",
        f"Quick note about {biz_name} site response"
    ]
    subject = random.choice(subject_options)
    body = (
        f"Hi {biz_name} Team,\n\n"
        f"I was trying to check out your services on your website ({website}) from my phone earlier today, "
        f"but the page took nearly {ttfb} seconds to load and froze for a moment.\n\n"
        f"Just wanted to ask if this was an issue on my end, or if your web server was undergoing maintenance today?\n\n"
        f"Best regards,\n{sender}"
    )
    return {"subject": subject, "body": body}

def generate_email_2(lead: Dict[str, Any], client_reply_text: str, referral_link: str) -> Dict[str, str]:
    """
    Step 2: The 'Peer Recommendation' Solution
    Sent ONLY after the client replies. Injects the Hostinger referral link naturally as friendly peer advice.
    """
    biz_name = lead.get("business_name", "Team")
    website = lead.get("website", "")
    sender = random.choice(SENDER_NAMES)

    prompt = f"""
STRICT REQUIREMENT: Output MUST be 100% in English only.

Write Email #2 responding to {biz_name}'s reply.

Context:
- Business: {biz_name}
- Their reply to our initial note: "{client_reply_text}"
- Hostinger Referral Link to naturally embed: {referral_link}

Copywriting Strategy:
1. Thank them politely for the prompt reply and say the site seems to be responding better now.
2. Share a brief personal experience: mention your own team had the exact same sluggish response time and high server latency last year until migrating to Hostinger's LiteSpeed cloud infrastructure.
3. Drop the Hostinger referral link casually as a helpful peer recommendation:
   "In case your web team or developer ever looks into upgrading your hosting, here's a direct discount link: {referral_link} — no pressure at all, just wanted to pass it along because it made a night-and-day difference for our speeds!"
4. Sign off warmly with "{sender}".

Output format strictly:
SUBJECT: Re: Quick question regarding {biz_name} website
BODY:
<plain text email body>
"""
    ai_text = call_gemini_api(prompt)
    if ai_text and "SUBJECT:" in ai_text and "BODY:" in ai_text:
        parts = ai_text.split("BODY:")
        subject = parts[0].replace("SUBJECT:", "").strip()
        body = parts[1].strip()
        return {"subject": subject, "body": body}

    # Deterministic high-converting copywriting fallback
    subject = f"Re: Quick question regarding {biz_name} website"
    body = (
        f"Hi {biz_name} Team,\n\n"
        f"Thanks for getting back to me so quickly! Glad to hear it — it does seem to be opening much better now.\n\n"
        f"We actually dealt with the exact same server lag and TTFB delays on our own web projects last year. "
        f"Our site speed improved drastically after we switched to Hostinger's LiteSpeed infrastructure.\n\n"
        f"If your developer or team ever looks into optimizing your hosting, here is a direct discount link: {referral_link}\n\n"
        f"No pressure at all, just thought I'd share what worked wonders for our load times! Wishing you all the best.\n\n"
        f"Best regards,\n{sender}"
    )
    return {"subject": subject, "body": body}
