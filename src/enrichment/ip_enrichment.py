"""IP geolocation and hosting provider enrichment."""

import requests
import time
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Import Config with fallback
try:
    from src.utils.config import Config
    from src.utils.rate_limiter import check_rate_limit, record_api_request, wait_if_needed
except ImportError:
    class Config:
        IPLOCATE_API_KEY = os.getenv("IPLOCATE_API_KEY", "")
        API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
    
    def check_rate_limit(api_name): return True
    def record_api_request(api_name): pass
    def wait_if_needed(api_name, max_wait=5.0): return True


def enrich_ip_location(ip_address: str) -> Dict:
    """Enrich IP address with location and hosting provider data."""
    result = {
        "ip_address": ip_address,
        "host_name": None,
        "asn": None,
        "isp": None,
        "country": None,
        "city": None
    }
    
    if not ip_address:
        return result
    
    # Try IPLocate.io first (free, no key needed for basic)
    try:
        if wait_if_needed("iplocate.io", max_wait=2.0):
            url = "https://www.iplocate.io/api/lookup/" + ip_address
            if Config.IPLOCATE_API_KEY:
                url += f"?apikey={Config.IPLOCATE_API_KEY}"
            
            response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
            record_api_request("iplocate.io")
            if response.status_code == 200:
                data = response.json()
                result["host_name"] = data.get("org") or data.get("asn", {}).get("name")
                result["asn"] = data.get("asn", {}).get("asn")
                result["isp"] = data.get("org")
                result["country"] = data.get("country")
                result["city"] = data.get("city")
                return result
    except Exception as e:
        print(f"IPLocate.io lookup failed: {e}")
    
    # Fallback to ip-api.com (free, 45 requests/minute)
    try:
        if wait_if_needed("ip-api.com", max_wait=2.0):
            url = f"http://ip-api.com/json/{ip_address}"
            response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
            record_api_request("ip-api.com")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result["host_name"] = data.get("org")
                    result["asn"] = data.get("as")
                    result["isp"] = data.get("isp")
                    result["country"] = data.get("country")
                    result["city"] = data.get("city")
    except Exception as e:
        print(f"ip-api.com lookup failed: {e}")
    
    return result

