"""
Clearnet mirror detection and analysis.

Many dark web vendors operate clearnet mirrors or use clearnet services:
- Clearnet versions of dark web sites (.com instead of .onion)
- Telegram channels (public, accessible via clearnet)
- Paste sites (pastebin, etc.) for listings
- Public forums discussing vendors
- Social media profiles linking to services
- Public marketplaces that also operate on dark web

This is MUCH safer than direct dark web access - all clearnet, no Tor needed.
"""

import requests
import re
from typing import Dict, List, Optional
from src.utils.config import Config
from src.utils.logger import logger


def find_clearnet_mirrors(domain: str) -> List[str]:
    """
    Find potential clearnet mirrors of a domain.
    
    Many dark web sites have clearnet mirrors with similar names.
    
    Returns:
        List of potential mirror domains
    """
    mirrors = []
    
    # Common patterns for clearnet mirrors
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        base_name = domain_parts[-2]  # Second-level domain
        
        # Try common TLDs
        common_tlds = ['com', 'net', 'org', 'io', 'co', 'xyz']
        for tld in common_tlds:
            mirror = f"{base_name}.{tld}"
            if mirror != domain:
                mirrors.append(mirror)
        
        # Try with common prefixes/suffixes
        prefixes = ['www', 'shop', 'store', 'market', 'mirror']
        suffixes = ['shop', 'store', 'market', 'mirror']
        
        for prefix in prefixes:
            mirrors.append(f"{prefix}.{base_name}.com")
        for suffix in suffixes:
            mirrors.append(f"{base_name}{suffix}.com")
    
    return mirrors


def check_clearnet_mirror(mirror_domain: str) -> Optional[Dict]:
    """
    Check if a clearnet mirror exists and extract metadata.
    
    Returns:
        Dictionary with mirror information if found, None otherwise
    """
    try:
        url = f"http://{mirror_domain}" if not mirror_domain.startswith("http") else mirror_domain
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check if it's actually a mirror (similar content/indicators)
            mirror_indicators = [
                "mirror", "clearnet", "alternative", "backup",
                "same service", "also available"
            ]
            
            is_mirror = any(indicator in content for indicator in mirror_indicators)
            
            return {
                "mirror_domain": mirror_domain,
                "exists": True,
                "is_mirror": is_mirror,
                "status_code": response.status_code,
                "content_length": len(content)
            }
    except Exception as e:
        logger.debug(f"Failed to check mirror {mirror_domain}: {e}")
        return None
    
    return None


def find_telegram_channels(domain: str, content: str = None) -> List[str]:
    """
    Find Telegram channels mentioned on a domain.
    
    Many vendors use public Telegram channels for communication.
    These are accessible via clearnet (telegram.org, t.me).
    
    Returns:
        List of Telegram channel usernames
    """
    channels = []
    
    # If content provided, extract from it
    if content:
        # Telegram link patterns
        telegram_patterns = [
            r't\.me/([a-z0-9_]+)',
            r'telegram\.org/([a-z0-9_]+)',
            r'@([a-z0-9_]+).*telegram',
            r'telegram[:\s]+@?([a-z0-9_]+)',
        ]
        
        for pattern in telegram_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            channels.extend([f"@{m}" if not m.startswith("@") else m for m in matches])
    
    # Also try to fetch domain content if not provided
    else:
        try:
            url = f"http://{domain}" if not domain.startswith("http") else domain
            response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
            if response.status_code == 200:
                return find_telegram_channels(domain, response.text)
        except:
            pass
    
    # Remove duplicates and return
    return list(set(channels))


def find_paste_sites(domain: str) -> List[Dict]:
    """
    Search paste sites (pastebin, etc.) for vendor listings.
    
    Many vendors post listings on paste sites with clearnet access.
    
    Returns:
        List of paste site URLs with vendor content
    """
    pastes = []
    
    # Extract domain name for search
    domain_name = domain.split('.')[0] if '.' in domain else domain
    
    # Try Pastebin search (if they have public search - check ToS)
    # Note: Pastebin's public search may have ToS restrictions
    # This is a placeholder - implement if ToS allows
    
    # Alternative: Check if domain mentions pastebin links
    try:
        url = f"http://{domain}" if not domain.startswith("http") else domain
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            content = response.text
            
            # Find pastebin links in content
            pastebin_pattern = r'pastebin\.com/([a-zA-Z0-9]+)'
            matches = re.findall(pastebin_pattern, content)
            for paste_id in matches:
                pastes.append({
                    "site": "pastebin.com",
                    "url": f"https://pastebin.com/{paste_id}",
                    "found_on": domain
                })
    except:
        pass
    
    return pastes


def analyze_public_forum_mentions(domain: str) -> Dict:
    """
    Search public forums for mentions of the domain/vendor.
    
    Many forums discuss dark web vendors on clearnet.
    
    Returns:
        Dictionary with forum mentions
    """
    mentions = {
        "reddit": [],
        "other_forums": []
    }
    
    # Reddit search (via public API)
    try:
        # Reddit search API (public, no auth needed for basic search)
        search_url = f"https://www.reddit.com/search.json?q={domain}&limit=10"
        response = requests.get(
            search_url,
            headers={"User-Agent": "PersonaForge/1.0"},
            timeout=Config.API_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "children" in data["data"]:
                for post in data["data"]["children"]:
                    post_data = post.get("data", {})
                    mentions["reddit"].append({
                        "title": post_data.get("title"),
                        "url": post_data.get("url"),
                        "subreddit": post_data.get("subreddit"),
                        "score": post_data.get("score", 0)
                    })
    except Exception as e:
        logger.debug(f"Reddit search failed: {e}")
    
    return mentions


def enrich_with_clearnet_mirrors(domain: str) -> Dict:
    """
    Comprehensive clearnet mirror enrichment.
    
    Finds and analyzes clearnet mirrors, Telegram channels, forum mentions.
    All accessible via normal web - no Tor needed!
    
    Returns:
        Dictionary with clearnet mirror intelligence
    """
    result = {
        "clearnet_mirrors": [],
        "telegram_channels": [],
        "forum_mentions": {},
        "paste_sites": [],
        "social_media": {}
    }
    
    # Find potential mirrors
    potential_mirrors = find_clearnet_mirrors(domain)
    
    # Check each mirror
    for mirror in potential_mirrors[:10]:  # Limit to 10 to avoid too many requests
        mirror_info = check_clearnet_mirror(mirror)
        if mirror_info and mirror_info.get("exists"):
            result["clearnet_mirrors"].append(mirror_info)
    
    # Get website content once for multiple extractions
    website_content = None
    try:
        url = f"http://{domain}" if not domain.startswith("http") else domain
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            website_content = response.text
    except:
        pass
    
    # Find Telegram channels
    if website_content:
        telegram_channels = find_telegram_channels(domain, website_content)
        result["telegram_channels"] = telegram_channels
    
    # Find social media profiles
    try:
        from .social_media import enrich_social_media
        social_data = enrich_social_media(domain)
        result["social_media"] = social_data
    except ImportError:
        pass
    
    # Search public forums
    forum_mentions = analyze_public_forum_mentions(domain)
    result["forum_mentions"] = forum_mentions
    
    # Search paste sites
    paste_sites = find_paste_sites(domain)
    result["paste_sites"] = paste_sites
    
    return result

