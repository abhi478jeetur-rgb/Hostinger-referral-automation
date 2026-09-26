"""
Gemini AI Prompt Engine for Autonomous 2-Step Soft Pitch Funnel.
Uses Google Gemini 2.0 Flash / 1.5 Flash via clean REST API, with intelligent copywriting fallback.
Generates:
  1. Email #1: "The Concerned Customer Hook" (High open rate, polite, genuine customer voice).
  2. Email #2: "The Casual Solution & Hostinger Recommendation" (Contextual reply with referral link).
"""

import os
import requests
from typing import Dict, Any, Optional
from database import get_settings

SYSTEM_PROMPT = """
You are an expert cold email conversion copywriter operating on behalf of an interested user/customer.
Your objective is to craft authentic, natural, non-salesy emails to business owners based on technical issues on their website.
Follow these guidelines strictly:
- ALWAYS write ONLY in English. Never use any other language, script, or character set — not Hindi, not Spanish, not French, nothing. English only.
- NEVER sound like a marketer, agency, or sales rep.
- Sound like an everyday prospective customer who wanted to use their services or read their site.
- Be concise (3-5 short sentences maximum).
- Plain text only (no HTML, no brackets, no markdown formatting).
- Do NOT include any greeting or sign-off in a non-English language.
"""

def call_gemini_api(prompt_text: str) -> Optional[str]:
    """Direct REST call to Gemini 2.0 Flash / 1.5 Flash."""
    settings = get_settings()
    api_key = settings.get("gemini_api_key", "").strip() or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None

    # Try Gemini 2.0 Flash first, fallback to 1.5 Flash
    models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt_text}"}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 400
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
    Step 1: The "Concerned User" Hook
    Mentions realistic loading lag & TTFB based on live audit.
    """
    biz_name = lead.get("business_name", "Team")
    website = lead.get("website", "")
    ttfb = lead.get("ttfb_seconds", 3.8)
    bottleneck = lead.get("bottleneck_summary", f"taking around {ttfb}s to load")

    prompt = f"""
IMPORTANT: Write ONLY in English. Do not use any other language under any circumstances.

Write Email 1 following this exact strategy:
- Target Business: {biz_name}
- Target Website: {website}
- Detected Issue: {bottleneck} (TTFB latency: {ttfb}s)

Instructions:
1. Subject line: Short, curiosity-driven (e.g. "Quick question about {biz_name}", or "Trouble loading {website} today").
2. Body: You were trying to check their site/services today, but it was sluggish/lagging. Ask politely if this is on your end or if their server is having maintenance.
3. Tone: Casual, helpful, everyday customer. NO hard pitch, NO mention of hosting or buying anything.
4. Output format:
SUBJECT: <subject here>
BODY:
<body here>
"""
    ai_text = call_gemini_api(prompt)
    if ai_text and "SUBJECT:" in ai_text and "BODY:" in ai_text:
        parts = ai_text.split("BODY:")
        subject = parts[0].replace("SUBJECT:", "").strip()
        body = parts[1].strip()
        return {"subject": subject, "body": body}

    # High-converting deterministic fallback
    subject = f"Quick question about {biz_name} site loading"
    body = (
        f"Hi {biz_name} Team,\n\n"
        f"I was trying to check out your services on your website ({website}) earlier today, "
        f"but the page took nearly {ttfb} seconds to respond and timed out once on mobile.\n\n"
        f"Just wanted to check if this is an issue on my end or if your server is having maintenance today?\n\n"
        f"Best regards,\nAlex"
    )
    return {"subject": subject, "body": body}

def generate_email_2(lead: Dict[str, Any], client_reply_text: str, referral_link: str) -> Dict[str, str]:
    """
    Step 2: The "Casual Recommendation" upon receiving their reply.
    Naturally injects the Hostinger referral link as a peer tip.
    """
    biz_name = lead.get("business_name", "Team")
    website = lead.get("website", "")

    prompt = f"""
IMPORTANT: Write ONLY in English. Do not use any other language under any circumstances.

Write Email 2 (Follow-up response to the client's reply):
- Business: {biz_name}
- Client's Reply Message: "{client_reply_text}"
- Hostinger Referral Link: {referral_link}

Instructions:
1. Thank them for getting back to you.
2. Mention the site seemed to work fine after refreshing a couple of times.
3. Mention you experienced similar server latency on your own web projects until you moved to Hostinger's LiteSpeed infrastructure.
4. Casually drop the discount link without being pushy: "In case your team is looking to upgrade or optimize hosting, here is a discount link: {referral_link}. No pressure at all, just thought it might help!"
5. Output format:
SUBJECT: Re: Quick question about {biz_name} site loading
BODY:
<body here>
"""
    ai_text = call_gemini_api(prompt)
    if ai_text and "SUBJECT:" in ai_text and "BODY:" in ai_text:
        parts = ai_text.split("BODY:")
        subject = parts[0].replace("SUBJECT:", "").strip()
        body = parts[1].strip()
        return {"subject": subject, "body": body}

    # High-converting deterministic fallback
    subject = f"Re: Quick question about {biz_name} site loading"
    body = (
        f"Hi {biz_name} Team,\n\n"
        f"Thanks for getting back to me so quickly! The site did load fine after a couple of refreshes.\n\n"
        f"We actually had very similar TTFB and server response lag on our own client sites before switching over to Hostinger. "
        f"Their LiteSpeed servers made a huge difference in loading speed for us.\n\n"
        f"If your web developer or team ever looks into optimizing hosting, here is a direct discount link: {referral_link}\n\n"
        f"No pressure at all, just thought I'd share it in case it saves you some headache! Wishing you all the best.\n\n"
        f"Best regards,\nAlex"
    )
    return {"subject": subject, "body": body}
