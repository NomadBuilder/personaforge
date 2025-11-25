"""WHOIS and DNS enrichment module."""

import whois
import dns.resolver
from typing import Dict
from datetime import datetime


def enrich_whois(domain: str) -> Dict:
    """Enrich domain with WHOIS data."""
    result = {
        "registrar": None,
        "creation_date": None,
        "whois_data": {}
    }
    
    try:
        w = whois.whois(domain)
        
        if w:
            result["registrar"] = w.registrar if hasattr(w, 'registrar') else None
            
            # Handle creation date (can be a list or single date)
            if hasattr(w, 'creation_date'):
                creation_date = w.creation_date
                if isinstance(creation_date, list) and creation_date:
                    creation_date = creation_date[0]
                if isinstance(creation_date, datetime):
                    result["creation_date"] = creation_date.date()
                elif creation_date:
                    result["creation_date"] = creation_date
            
            # Store raw WHOIS data
            result["whois_data"] = {
                "expiration_date": str(w.expiration_date) if hasattr(w, 'expiration_date') else None,
                "updated_date": str(w.updated_date) if hasattr(w, 'updated_date') else None,
                "name_servers": w.name_servers if hasattr(w, 'name_servers') else None,
                "status": w.status if hasattr(w, 'status') else None,
            }
    except Exception as e:
        print(f"WHOIS lookup failed for {domain}: {e}")
    
    return result


def enrich_dns(domain: str) -> Dict:
    """Enrich domain with DNS records."""
    result = {
        "dns_records": {},
        "ip_address": None,
        "cdn": None
    }
    
    try:
        # A record (IPv4)
        try:
            a_records = dns.resolver.resolve(domain, 'A')
            ip_addresses = [str(ip) for ip in a_records]
            result["dns_records"]["A"] = ip_addresses
            result["ip_address"] = ip_addresses[0] if ip_addresses else None
        except Exception:
            pass
        
        # AAAA record (IPv6)
        try:
            aaaa_records = dns.resolver.resolve(domain, 'AAAA')
            result["dns_records"]["AAAA"] = [str(ip) for ip in aaaa_records]
        except Exception:
            pass
        
        # MX records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            result["dns_records"]["MX"] = [str(mx) for mx in mx_records]
        except Exception:
            pass
        
        # NS records
        try:
            ns_records = dns.resolver.resolve(domain, 'NS')
            result["dns_records"]["NS"] = [str(ns) for ns in ns_records]
        except Exception:
            pass
        
        # Detect CDN from nameservers
        if result["dns_records"].get("NS"):
            ns_list = result["dns_records"]["NS"]
            cdn_indicators = {
                "cloudflare": "Cloudflare",
                "fastly": "Fastly",
                "amazonaws": "Amazon CloudFront",
                "akamai": "Akamai",
                "maxcdn": "MaxCDN",
                "keycdn": "KeyCDN"
            }
            for ns in ns_list:
                ns_lower = ns.lower()
                for indicator, cdn_name in cdn_indicators.items():
                    if indicator in ns_lower:
                        result["cdn"] = cdn_name
                        break
                if result["cdn"]:
                    break
                    
    except Exception as e:
        print(f"DNS lookup failed for {domain}: {e}")
    
    return result

