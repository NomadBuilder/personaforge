"""Main enrichment pipeline that orchestrates all enrichment steps."""

from typing import Dict
from .whois_enrichment import enrich_whois, enrich_dns
from .ip_enrichment import enrich_ip_location
from .cms_enrichment import detect_cms
from .payment_detection import detect_payment_processors
from .vendor_detection import detect_vendor_type, extract_vendor_name, calculate_vendor_risk_score

# Optional threat intelligence
try:
    from .threat_intel import enrich_with_crtsh, enrich_with_urlhaus
    THREAT_INTEL_AVAILABLE = True
except ImportError:
    THREAT_INTEL_AVAILABLE = False
    def enrich_with_crtsh(domain): return {}
    def enrich_with_urlhaus(domain): return {}

# Public content analysis (legitimate sources only)
try:
    from .content_analysis import analyze_public_website
    CONTENT_ANALYSIS_AVAILABLE = True
except ImportError:
    CONTENT_ANALYSIS_AVAILABLE = False
    def analyze_public_website(domain): return {}

# Clearnet mirror detection (much safer than dark web!)
try:
    from .clearnet_mirrors import enrich_with_clearnet_mirrors
    CLEARNET_MIRRORS_AVAILABLE = True
except ImportError:
    CLEARNET_MIRRORS_AVAILABLE = False
    def enrich_with_clearnet_mirrors(domain): return {}

# Dark web access (OPTIONAL - Use with extreme caution)
try:
    from .darkweb_enrichment import enrich_domain_with_darkweb, is_darkweb_enabled, TOR_AVAILABLE
    from src.utils.config import Config
    DARKWEB_AVAILABLE = TOR_AVAILABLE and (Config.DARKWEB_ENABLED if hasattr(Config, 'DARKWEB_ENABLED') else False)
except ImportError:
    DARKWEB_AVAILABLE = False
    TOR_AVAILABLE = False
    def enrich_domain_with_darkweb(domain): return {}
    def is_darkweb_enabled(): return False

# Import caching
try:
    from src.utils.cache import get_cached, set_cached
    from src.utils.config import Config
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    def get_cached(*args, **kwargs): return None
    def set_cached(*args, **kwargs): pass


def enrich_domain(domain: str) -> Dict:
    """
    Enrich a domain with all available data sources.
    
    Args:
        domain: Domain name to enrich
        
    Returns:
        Dictionary containing all enrichment data
    """
    # Check cache first
    if CACHE_AVAILABLE:
        cached_data = get_cached("domain", domain)
        if cached_data:
            print(f"Cache hit for domain: {domain}")
            return cached_data
    
    print(f"Enriching domain: {domain}")
    
    result = {
        "domain": domain,
        "ip_address": None,
        "ip_addresses": [],
        "ipv6_addresses": [],
        "host_name": None,
        "asn": None,
        "isp": None,
        "cdn": None,
        "cms": None,
        "payment_processor": None,
        "registrar": None,
        "creation_date": None,
        "expiration_date": None,
        "updated_date": None,
        "name_servers": [],
        "mx_records": [],
        "whois_status": None,
        "whois_data": {},
        "dns_records": {},
        "subdomains": [],
        "threat_intel": {},
        "content_analysis": {},
        "clearnet_mirrors": {}
    }
    
    # Step 1: WHOIS enrichment
    print(f"  → WHOIS lookup...")
    whois_data = enrich_whois(domain)
    result.update(whois_data)
    
    # Extract additional WHOIS fields
    if whois_data.get("whois_data"):
        whois_info = whois_data["whois_data"]
        if whois_info.get("expiration_date"):
            result["expiration_date"] = str(whois_info["expiration_date"])
        if whois_info.get("updated_date"):
            result["updated_date"] = str(whois_info["updated_date"])
        if whois_info.get("name_servers"):
            result["name_servers"] = whois_info["name_servers"] if isinstance(whois_info["name_servers"], list) else [whois_info["name_servers"]]
        if whois_info.get("status"):
            status_list = whois_info["status"] if isinstance(whois_info["status"], list) else [whois_info["status"]]
            result["whois_status"] = ", ".join(str(s) for s in status_list) if status_list else None
    
    # Step 2: DNS enrichment
    print(f"  → DNS lookup...")
    dns_data = enrich_dns(domain)
    result.update(dns_data)
    
    # Extract all IPs and DNS records
    if dns_data.get("dns_records"):
        dns_recs = dns_data["dns_records"]
        if dns_recs.get("A"):
            result["ip_addresses"] = dns_recs["A"]
            result["ip_address"] = dns_recs["A"][0] if dns_recs["A"] else None
        if dns_recs.get("AAAA"):
            result["ipv6_addresses"] = dns_recs["AAAA"]
        if dns_recs.get("MX"):
            result["mx_records"] = dns_recs["MX"]
        if dns_recs.get("NS"):
            if not result.get("name_servers"):
                result["name_servers"] = dns_recs["NS"]
    
    # Step 3: IP location enrichment
    if result.get("ip_address"):
        print(f"  → IP location lookup...")
        ip_data = enrich_ip_location(result["ip_address"])
        result["host_name"] = ip_data.get("host_name")
        result["asn"] = ip_data.get("asn")
        result["isp"] = ip_data.get("isp")
    
    # Step 4: CMS detection
    print(f"  → CMS detection...")
    cms = detect_cms(domain)
    if cms:
        result["cms"] = cms
    
    # Step 5: Payment processor detection
    print(f"  → Payment processor detection...")
    processors = detect_payment_processors(domain)
    if processors:
        result["payment_processor"] = ", ".join(processors)
    
    # Step 6: Vendor detection
    print(f"  → Vendor detection...")
    vendor_type = detect_vendor_type(domain, result)
    if vendor_type:
        result["vendor_type"] = vendor_type
    
    vendor_name = extract_vendor_name(domain, result)
    if vendor_name:
        result["vendor_name"] = vendor_name
    
    risk_score = calculate_vendor_risk_score(domain, result)
    result["vendor_risk_score"] = risk_score
    
    # Step 7: Threat intelligence (optional)
    if THREAT_INTEL_AVAILABLE:
        print(f"  → Threat intelligence lookup...")
        crtsh_data = enrich_with_crtsh(domain)
        if crtsh_data.get("subdomains"):
            result["subdomains"] = crtsh_data["subdomains"]
        
        urlhaus_data = enrich_with_urlhaus(domain)
        if urlhaus_data:
            result["threat_intel"] = urlhaus_data
    
    # Step 8: Public content analysis (legitimate sources only)
    if CONTENT_ANALYSIS_AVAILABLE:
        print(f"  → Public content analysis...")
        content_data = analyze_public_website(domain)
        if content_data:
            result["content_analysis"] = content_data
    
    # Step 8b: Clearnet mirror detection (much safer than dark web!)
    if CLEARNET_MIRRORS_AVAILABLE:
        print(f"  → Clearnet mirror detection...")
        mirror_data = enrich_with_clearnet_mirrors(domain)
        if mirror_data:
            result["clearnet_mirrors"] = mirror_data
    
    # Step 9: Dark web access (OPTIONAL - Use with extreme caution)
    # ⚠️ WARNING: Only enabled if DARKWEB_ENABLED=true and Tor is configured
    if DARKWEB_AVAILABLE and is_darkweb_enabled():
        print(f"  → Dark web lookup (experimental - use with caution)...")
        try:
            darkweb_data = enrich_domain_with_darkweb(domain)
            if darkweb_data.get("darkweb_available"):
                result["darkweb"] = darkweb_data
        except Exception as e:
            print(f"Dark web enrichment failed: {e}")
            # Don't fail entire enrichment if dark web fails
    
    # Cache the result
    if CACHE_AVAILABLE:
        set_cached("domain", domain, result)
    
    print(f"  ✅ Enrichment complete for {domain}")
    return result

