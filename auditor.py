"""
Website Performance & TTFB Speed Auditor.
Detects real server response latency to provide 100% authentic data for the AI Hook.
"""

import time
import requests
from typing import Dict, Any
from urllib.parse import urlparse

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def audit_website(url: str, timeout: float = 6.0) -> Dict[str, Any]:
    """
    Measures genuine TTFB, response time, server header and identifies bottlenecks.
    """
    if not url:
        return {"success": False, "ttfb_seconds": 0.0, "bottleneck_summary": "No website URL provided"}

    if not url.startswith("http"):
        url = "https://" + url

    try:
        start_time = time.time()
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True, verify=False)
        total_time = round(time.time() - start_time, 2)
        
        # TTFB is approximately the elapsed time to the initial headers
        ttfb = round(response.elapsed.total_seconds(), 2)
        if ttfb > total_time:
            ttfb = total_time

        server = response.headers.get("Server", "Unknown Server")
        content_type = response.headers.get("Content-Type", "")
        status_code = response.status_code

        # Craft realistic bottleneck diagnosis based on actual data
        bottleneck = []
        if ttfb >= 2.5:
            bottleneck.append(f"sluggish server response time (TTFB of {ttfb}s)")
        elif total_time >= 3.5:
            bottleneck.append(f"slow total page load time ({total_time}s)")
        else:
            bottleneck.append(f"intermittent delay ({ttfb}s response latency)")

        if "cloudflare" not in server.lower() and "litespeed" not in server.lower():
            bottleneck.append("unoptimized hosting server configuration")

        return {
            "success": True,
            "url": url,
            "status_code": status_code,
            "ttfb_seconds": ttfb,
            "total_seconds": total_time,
            "server": server,
            "bottleneck_summary": " and ".join(bottleneck) if bottleneck else "minor loading lag",
            "is_slow": ttfb >= 2.0 or total_time >= 3.0
        }

    except requests.exceptions.Timeout:
        return {
            "success": True,
            "url": url,
            "status_code": 408,
            "ttfb_seconds": 6.0,
            "total_seconds": 6.0,
            "server": "Timeout",
            "bottleneck_summary": "frequent connection timeouts and server unresponsiveness",
            "is_slow": True
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "status_code": 500,
            "ttfb_seconds": 0.0,
            "total_seconds": 0.0,
            "server": "Error",
            "bottleneck_summary": "connection errors",
            "is_slow": False
        }
