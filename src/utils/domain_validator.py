"""
Domain validation utilities to filter out false positives.
"""

import re
import socket
from typing import List, Set

# Common valid TLDs (not exhaustive, but covers most)
VALID_TLDS = {
    'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
    'io', 'co', 'ai', 'app', 'dev', 'tech', 'online',
    'xyz', 'info', 'biz', 'me', 'tv', 'cc', 'ws',
    'uk', 'us', 'ca', 'au', 'de', 'fr', 'jp', 'cn',
    'ru', 'in', 'br', 'mx', 'es', 'it', 'nl', 'se',
    'no', 'dk', 'fi', 'pl', 'cz', 'gr', 'ie', 'pt',
    'be', 'ch', 'at', 'nz', 'sg', 'hk', 'kr', 'tw',
    'th', 'vn', 'ph', 'id', 'my', 'ae', 'sa', 'il',
    'tr', 'za', 'eg', 'ng', 'ke', 'gh', 'ma', 'tn',
    'ro', 'hu', 'bg', 'hr', 'sk', 'si', 'lt', 'lv',
    'ee', 'is', 'ie', 'lu', 'mt', 'cy', 'li', 'mc',
    'ad', 'sm', 'va', 'by', 'ua', 'kz', 'ge', 'am',
    'az', 'md', 'al', 'mk', 'rs', 'ba', 'me', 'xk',
    'club', 'site', 'website', 'store', 'shop', 'blog',
    'online', 'news', 'media', 'email', 'cloud', 'host'
}


def is_valid_domain(domain: str) -> bool:
    """
    Validate if a string is a real domain name.
    
    Checks:
    - Has valid format (contains dot, proper length)
    - Has valid TLD
    - Not a file extension
    - Not JavaScript/CSS code
    - Not an IP address
    """
    if not domain or not isinstance(domain, str):
        return False
    
    domain = domain.lower().strip()
    
    # Remove common prefixes
    domain = domain.replace('www.', '').replace('http://', '').replace('https://', '')
    domain = domain.split('/')[0].split('?')[0].split('#')[0]  # Remove paths and fragments
    
    # Basic format checks
    if '.' not in domain:
        return False
    
    if len(domain) < 4 or len(domain) > 253:  # Max domain length
        return False
    
    # Check for invalid patterns
    invalid_patterns = [
        r'\.(jpg|jpeg|png|gif|pdf|txt|zip|rar|exe|dll|css|js|json|xml|asp|php|html|svg|ico|woff|ttf|eot)$',
        r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$',  # IP addresses
        r'^localhost',
        r'^127\.',
        r'^192\.168\.',
        r'^10\.',
        r'^172\.(1[6-9]|2[0-9]|3[01])\.',  # Private IP ranges
        r'\.create$',  # JavaScript methods
        r'\.prototype\.',  # JavaScript
        r'\.style\.',  # CSS/JS
        r'\.push$',  # JavaScript methods
        r'\.tolowercase$',  # JavaScript methods
        r'object\.',  # JavaScript
        r'^meta\.',  # HTML meta
        r'^img\.',  # HTML tags
        r'^button\.',  # CSS classes
        r'\.tp\.',  # Internal YouTube paths
        r'\.yt\.',  # YouTube internal
        r'\.vflset',  # YouTube internal
        r'contributors',  # File names
        r'manifest\.',  # Web manifests
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, domain, re.IGNORECASE):
            return False
    
    # Check TLD
    parts = domain.split('.')
    if len(parts) < 2:
        return False
    
    tld = parts[-1].lower()
    
    # Check if TLD is valid (at least 2 chars and known TLD or looks valid)
    if len(tld) < 2:
        return False
    
    # If it's a known TLD, great
    if tld in VALID_TLDS:
        return True
    
    # If it's 2-4 chars and looks like a TLD, accept it (covers country codes and new TLDs)
    if 2 <= len(tld) <= 4 and tld.isalpha():
        return True
    
    # If it's a multi-part TLD (like co.uk), check the last two parts
    if len(parts) >= 3:
        last_two = '.'.join(parts[-2:])
        if last_two in VALID_TLDS or (parts[-2].isalpha() and parts[-1].isalpha() and 2 <= len(parts[-1]) <= 4):
            return True
    
    return False


def validate_domains(domains: List[str]) -> Set[str]:
    """
    Filter a list of domains to only include valid ones.
    
    Returns:
        Set of valid domain names
    """
    valid = set()
    
    for domain in domains:
        if is_valid_domain(domain):
            # Clean the domain
            clean = domain.lower().strip()
            clean = clean.replace('www.', '').replace('http://', '').replace('https://', '')
            clean = clean.split('/')[0].split('?')[0].split('#')[0]
            
            if clean and '.' in clean:
                valid.add(clean)
    
    return valid


def can_resolve_domain(domain: str, timeout: float = 2.0) -> bool:
    """
    Check if a domain can be resolved via DNS.
    
    This is optional validation - some domains might be valid but not resolve.
    """
    try:
        socket.gethostbyname(domain)
        return True
    except (socket.gaierror, socket.timeout, OSError):
        return False

