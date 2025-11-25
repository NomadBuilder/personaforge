"""Input validation utilities."""

import re
from typing import Tuple, Optional


def sanitize_input(value: str) -> str:
    """Sanitize user input."""
    if not value:
        return ""
    return value.strip()


def validate_domain(domain: str) -> Tuple[bool, Optional[str]]:
    """Validate domain name format."""
    if not domain:
        return False, "Domain is required"
    
    domain = domain.strip().lower()
    
    # Remove protocol if present
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = domain.split('/')[0].split('?')[0].split('#')[0].rstrip('/')
    
    # Basic domain validation
    domain_pattern = r'^([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
    if not re.match(domain_pattern, domain):
        return False, "Invalid domain format"
    
    if len(domain) > 253:
        return False, "Domain too long"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate URL format."""
    if not url:
        return False, "URL is required"
    
    url = url.strip()
    
    # Basic URL validation
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        return False, "Invalid URL format"
    
    return True, None

