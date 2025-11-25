"""Threat intelligence enrichment (optional, free sources)."""

import requests
from typing import Dict, Optional
from src.utils.config import Config
from src.utils.rate_limiter import check_rate_limit, record_api_request, wait_if_needed


def enrich_with_crtsh(domain: str) -> Dict:
    """
    Enrich domain with Certificate Transparency data from crt.sh.
    
    Returns:
        Dictionary with certificate information
    """
    result = {
        "certificates": [],
        "subdomains": []
    }
    
    try:
        if not wait_if_needed("crtsh", max_wait=1.0):
            return result
        
        url = f"https://crt.sh/?q={domain}&output=json"
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
        record_api_request("crtsh")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Extract unique subdomains
                subdomains = set()
                for cert in data:
                    name_value = cert.get("name_value", "")
                    if name_value:
                        # Parse name_value (can be multiple lines)
                        for name in name_value.split("\n"):
                            name = name.strip().lower()
                            if name and name != domain:
                                # Remove wildcard prefix
                                if name.startswith("*."):
                                    name = name[2:]
                                subdomains.add(name)
                
                result["subdomains"] = sorted(list(subdomains))
                result["certificates"] = data[:10]  # Limit to 10 certs
    except Exception as e:
        print(f"crt.sh lookup failed for {domain}: {e}")
    
    return result


def enrich_with_urlhaus(domain: str) -> Dict:
    """
    Check domain against URLhaus malware database (abuse.ch).
    
    Returns:
        Dictionary with threat intelligence data
    """
    result = {
        "is_malicious": False,
        "threat_type": None,
        "first_seen": None
    }
    
    try:
        if not wait_if_needed("urlhaus", max_wait=1.0):
            return result
        
        url = f"https://urlhaus-api.abuse.ch/v1/host/{domain}/"
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
        record_api_request("urlhaus")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("query_status") == "ok":
                result["is_malicious"] = data.get("threat", {}).get("threat_type") is not None
                if result["is_malicious"]:
                    result["threat_type"] = data.get("threat", {}).get("threat_type")
                    result["first_seen"] = data.get("firstseen")
    except Exception as e:
        print(f"URLhaus lookup failed for {domain}: {e}")
    
    return result

