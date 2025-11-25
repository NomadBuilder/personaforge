"""
Dark web enrichment via Tor (OPTIONAL - Use with caution).

⚠️ WARNING: Dark web access has legal and ethical risks.
- Consult legal counsel before using
- Implement strict content filtering
- Only extract metadata, never store illegal content
- Use dedicated infrastructure (not public cloud)
- Document all compliance procedures

This module is provided for research purposes only.
"""

import requests
import socket
import re
from typing import Dict, Optional, List
from src.utils.config import Config
from src.utils.logger import logger

# Try to import Tor libraries
try:
    import socks  # PySocks
    try:
        from stem import Signal
        from stem.control import Controller
        TOR_AVAILABLE = True
        STEM_AVAILABLE = True
    except ImportError:
        # PySocks available but stem not - can still use SOCKS proxy
        TOR_AVAILABLE = True
        STEM_AVAILABLE = False
        logger.info("PySocks available but stem not - basic Tor support only")
except ImportError:
    TOR_AVAILABLE = False
    STEM_AVAILABLE = False
    socks = None
    logger.warning("Tor libraries not available. Install with: pip install PySocks stem")


# Illegal content keywords to filter
ILLEGAL_CONTENT_KEYWORDS = [
    # Add specific illegal content indicators here
    # This is a placeholder - implement proper filtering
]

# Known illegal marketplace patterns
ILLEGAL_MARKETPLACE_PATTERNS = [
    # Add patterns for known illegal marketplaces
    # This is a placeholder
]


def setup_tor_proxy(proxy_host: str = "127.0.0.1", proxy_port: int = 9050):
    """
    Setup Tor SOCKS proxy for requests.
    
    Requires Tor to be running locally on proxy_port.
    """
    if not TOR_AVAILABLE or socks is None:
        raise ImportError("Tor libraries not available. Install: pip install PySocks")
    
    socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port)
    socket.socket = socks.socksocket
    logger.info(f"Tor proxy configured: {proxy_host}:{proxy_port}")


def check_content_safety(content: str) -> bool:
    """
    Check if content is safe to process (no illegal material).
    
    This is a basic filter - implement comprehensive filtering in production.
    
    Returns:
        True if content appears safe, False if potentially illegal
    """
    content_lower = content.lower()
    
    # Check for illegal content keywords
    for keyword in ILLEGAL_CONTENT_KEYWORDS:
        if keyword in content_lower:
            logger.warning(f"Potentially illegal content detected: {keyword}")
            return False
    
    # Additional checks can be added here
    # - ML model for content classification
    # - Image/video analysis (if needed)
    # - Pattern matching for illegal marketplaces
    
    return True


def extract_metadata_only(content: str) -> Dict:
    """
    Extract only safe metadata from content.
    
    Never stores full content, only extracts:
    - Domain information
    - Service descriptions (if public)
    - Contact methods (if public)
    - Pricing (if public)
    - No images, videos, or illegal content
    """
    result = {
        "service_keywords": [],
        "pricing_info": [],
        "contact_methods": [],
        "vendor_description": None
    }
    
    # Only extract safe, public information
    # Extract email addresses (public contact)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, content)
    if emails:
        result["contact_methods"] = emails[:3]  # Limit to 3
    
    # Extract pricing (if public)
    pricing_patterns = [
        r'\$[\d,]+',
        r'[\d,]+\s*btc',
        r'[\d,]+\s*eth',
    ]
    for pattern in pricing_patterns:
        matches = re.findall(pattern, content)
        if matches:
            result["pricing_info"].extend(matches[:5])
    
    # Extract service keywords (vendor-related only)
    vendor_keywords = [
        "synthetic identity", "deepfake", "voice clone",
        "identity kit", "persona pack"
    ]
    for keyword in vendor_keywords:
        if keyword in content.lower():
            result["service_keywords"].append(keyword)
    
    return result


def access_onion_site(onion_url: str, use_tor: bool = True) -> Optional[Dict]:
    """
    Access .onion site via Tor and extract safe metadata only.
    
    ⚠️ WARNING: Use with extreme caution. Only extracts metadata.
    
    Args:
        onion_url: .onion URL to access
        use_tor: Whether to use Tor proxy (default: True)
    
    Returns:
        Dictionary with extracted metadata, or None if unsafe/error
    """
    if not onion_url.endswith(".onion"):
        logger.error("URL must be a .onion address")
        return None
    
    if use_tor and not TOR_AVAILABLE:
        logger.error("Tor not available - cannot access .onion sites")
        return None
    
    try:
        # Setup Tor proxy if needed
        if use_tor:
            setup_tor_proxy()
        
        # Access site
        full_url = f"http://{onion_url}" if not onion_url.startswith("http") else onion_url
        logger.info(f"Accessing .onion site: {onion_url}")
        
        response = requests.get(
            full_url,
            timeout=30,  # Tor is slow
            allow_redirects=True
        )
        
        if response.status_code != 200:
            logger.warning(f"Failed to access {onion_url}: {response.status_code}")
            return None
        
        content = response.text
        
        # Check content safety
        if not check_content_safety(content):
            logger.warning(f"Unsafe content detected for {onion_url} - skipping")
            return None
        
        # Extract metadata only (never store full content)
        metadata = extract_metadata_only(content)
        metadata["onion_url"] = onion_url
        metadata["accessed_via_tor"] = use_tor
        
        logger.info(f"Successfully extracted metadata from {onion_url}")
        return metadata
        
    except Exception as e:
        logger.error(f"Error accessing {onion_url}: {e}")
        return None


def enrich_domain_with_darkweb(domain: str) -> Dict:
    """
    Attempt to find .onion mirror for a domain and enrich it.
    
    This is experimental - many domains don't have .onion mirrors.
    
    Returns:
        Dictionary with dark web metadata if found
    """
    result = {
        "darkweb_available": False,
        "onion_urls": [],
        "darkweb_metadata": {}
    }
    
    # Try common .onion patterns
    # Note: This is speculative - actual .onion addresses are not predictable
    potential_onions = [
        f"{domain.replace('.', '')}.onion",
        f"www{domain.replace('.', '')}.onion",
    ]
    
    for onion_url in potential_onions:
        try:
            metadata = access_onion_site(onion_url)
            if metadata:
                result["darkweb_available"] = True
                result["onion_urls"].append(onion_url)
                result["darkweb_metadata"] = metadata
                break
        except Exception as e:
            logger.debug(f"Failed to access {onion_url}: {e}")
            continue
    
    return result


# Configuration check
def is_darkweb_enabled() -> bool:
    """Check if dark web access is enabled in configuration."""
    return Config.DARKWEB_ENABLED if hasattr(Config, 'DARKWEB_ENABLED') else False

