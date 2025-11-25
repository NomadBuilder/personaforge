"""Vendor detection algorithms for identifying synthetic identity vendors."""

from typing import Dict, List, Optional
from collections import Counter
import re


def detect_vendor_type(domain: str, enrichment_data: Dict) -> Optional[str]:
    """
    Detect vendor type based on domain name and enrichment data.
    
    Returns:
        'synthetic_identity', 'deepfake', 'impersonation', or None
    """
    domain_lower = domain.lower()
    
    # Keywords for synthetic identity vendors
    synthetic_keywords = [
        'identity', 'id', 'persona', 'profile', 'fake', 'synthetic',
        'document', 'passport', 'license', 'ssn', 'credit'
    ]
    
    # Keywords for deepfake vendors
    deepfake_keywords = [
        'deepfake', 'face-swap', 'voice-clone', 'impersonate',
        'clone', 'replica', 'fake-video', 'ai-face'
    ]
    
    # Keywords for impersonation services
    impersonation_keywords = [
        'impersonate', 'pretend', 'roleplay', 'character',
        'profile-pack', 'identity-kit'
    ]
    
    # Check domain name
    synthetic_score = sum(1 for kw in synthetic_keywords if kw in domain_lower)
    deepfake_score = sum(1 for kw in deepfake_keywords if kw in domain_lower)
    impersonation_score = sum(1 for kw in impersonation_keywords if kw in domain_lower)
    
    # Check page content (if available)
    if enrichment_data.get('cms') == 'WordPress':
        # WordPress sites often have more content to analyze
        pass
    
    # Determine vendor type
    if deepfake_score > 0:
        return 'deepfake'
    elif impersonation_score > 0:
        return 'impersonation'
    elif synthetic_score > 0:
        return 'synthetic_identity'
    
    return None


def extract_vendor_name(domain: str, enrichment_data: Dict) -> Optional[str]:
    """
    Extract vendor name from domain or enrichment data.
    
    Returns:
        Vendor name or None
    """
    # Try to extract from domain (remove TLD)
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        # Use second-level domain as potential vendor name
        potential_name = domain_parts[-2]
        
        # Clean up common prefixes/suffixes
        potential_name = re.sub(r'^(www|shop|store|buy|get)', '', potential_name)
        potential_name = re.sub(r'(shop|store|site|web)$', '', potential_name)
        
        if len(potential_name) > 2:
            return potential_name.capitalize()
    
    # Try WHOIS data
    if enrichment_data.get('whois_data'):
        whois = enrichment_data['whois_data']
        if isinstance(whois, dict):
            # Look for organization name
            org = whois.get('org') or whois.get('organization')
            if org:
                return org
    
    return None


def calculate_vendor_risk_score(domain: str, enrichment_data: Dict) -> int:
    """
    Calculate risk score for a vendor domain (0-100).
    
    Higher score = higher risk of being a synthetic identity vendor.
    
    Also checks if domain is likely a vendor site vs. just mentioned in discussions.
    """
    score = 0
    domain_lower = domain.lower()
    
    # Strong vendor indicators in domain name
    strong_vendor_keywords = [
        'fakeid', 'fake-id', 'fakeidvendor', 'fakeidshop', 'fakeidstore',
        'deepfake', 'deep-fake', 'deepfakeservice', 'face-swap', 'voice-clone',
        'syntheticid', 'synthetic-id', 'personakit', 'persona-kit', 'identitypack',
        'fakedocs', 'fake-docs', 'fakedocuments', 'fake-documents',
        'kycbypass', 'kyc-bypass', 'fakekyc', 'fake-kyc'
    ]
    
    # Medium vendor indicators
    medium_vendor_keywords = [
        'fake', 'synthetic', 'clone', 'impersonate', 'persona', 'identity',
        'document', 'passport', 'license', 'ssn', 'credit'
    ]
    
    # Check for strong indicators (likely actual vendor site)
    for keyword in strong_vendor_keywords:
        if keyword in domain_lower:
            score += 25  # Strong indicator
    
    # Check for medium indicators
    for keyword in medium_vendor_keywords:
        if keyword in domain_lower:
            score += 10
    
    # Content analysis indicators (if available)
    content_analysis = enrichment_data.get('content_analysis', {})
    if content_analysis:
        vendor_keywords = content_analysis.get('vendor_keywords', [])
        if vendor_keywords:
            score += 20  # Found vendor keywords on the site itself
        pricing = content_analysis.get('pricing_indicators', [])
        if pricing:
            score += 15  # Has pricing (likely selling something)
    
    # Payment processor indicators (crypto = higher risk)
    payment = enrichment_data.get('payment_processor') or ''
    if payment:
        payment_lower = payment.lower()
        if any(crypto in payment_lower for crypto in ['crypto', 'bitcoin', 'btc', 'eth', 'ethereum', 'monero', 'xmr']):
            score += 20  # Crypto payment = higher risk
        elif any(legit in payment_lower for legit in ['stripe', 'paypal', 'square']):
            score -= 5  # Legitimate payment = slightly lower risk
    
    # Hosting provider indicators (offshore = higher risk)
    isp = enrichment_data.get('isp') or ''
    host = enrichment_data.get('host_name') or ''
    hosting_info = (isp + ' ' + host).lower()
    if hosting_info:
        if any(indicator in hosting_info for indicator in ['offshore', 'bulletproof', 'anonymous', 'bulletproof']):
            score += 20
        elif any(legit in hosting_info for legit in ['cloudflare', 'amazon', 'google', 'microsoft', 'aws']):
            score -= 5  # Legitimate hosting = slightly lower risk
    
    # Registrar indicators
    registrar = enrichment_data.get('registrar') or ''
    if registrar:
        registrar_lower = registrar.lower()
        if any(indicator in registrar_lower for indicator in ['privacy', 'anonymous', 'offshore', 'bulletproof']):
            score += 15
        elif any(legit in registrar_lower for legit in ['godaddy', 'namecheap', 'google', 'cloudflare']):
            score -= 3  # Legitimate registrar = slightly lower risk
    
    # Domain age (new domains = higher risk, but not definitive)
    creation_date = enrichment_data.get('creation_date')
    if creation_date:
        try:
            from datetime import datetime
            if isinstance(creation_date, str):
                # Try to parse date
                pass  # TODO: Calculate age
        except:
            pass
    
    # Negative indicators (likely NOT a vendor site)
    # Common legitimate sites that might be mentioned in discussions
    legitimate_sites = [
        'reddit.com', 'youtube.com', 'twitter.com', 'facebook.com', 'instagram.com',
        'linkedin.com', 'github.com', 'stackoverflow.com', 'wikipedia.org',
        'news', 'blog', 'article', 'report', 'study', 'research', 'gov', 'edu',
        'bloomberg', 'reuters', 'cnn', 'bbc', 'nytimes', 'washingtonpost',
        'coinbase', 'binance', 'ethereum', 'bitcoin.org'
    ]
    
    for legit in legitimate_sites:
        if legit in domain_lower:
            score -= 30  # Strong negative indicator - likely just mentioned in discussion
            break
    
    return max(0, min(score, 100))  # Clamp between 0-100


def is_likely_vendor_site(domain: str, enrichment_data: Dict, min_risk_score: int = 40) -> bool:
    """
    Determine if a domain is likely an actual vendor site (not just mentioned).
    
    Returns:
        True if likely a vendor site, False if just mentioned in discussions
    """
    risk_score = calculate_vendor_risk_score(domain, enrichment_data)
    
    # High risk score = likely vendor site
    if risk_score >= min_risk_score:
        return True
    
    # Check for strong vendor indicators in domain
    domain_lower = domain.lower()
    strong_indicators = [
        'fakeid', 'deepfake', 'syntheticid', 'personakit', 'fakedocs',
        'kycbypass', 'fakeidvendor', 'deepfakeservice'
    ]
    
    if any(indicator in domain_lower for indicator in strong_indicators):
        return True
    
    # Check content analysis
    content_analysis = enrichment_data.get('content_analysis', {})
    if content_analysis.get('vendor_keywords'):
        return True
    
    return False

