"""Public content analysis for vendor detection (legitimate sources only)."""

import requests
import re
from typing import Dict, List, Optional
from src.utils.config import Config


def analyze_public_website(domain: str) -> Dict:
    """
    Analyze public website content for vendor indicators.
    
    Only analyzes publicly accessible content - no dark web, no private content.
    
    Returns:
        Dictionary with vendor indicators found in public content
    """
    result = {
        "vendor_keywords": [],
        "service_descriptions": [],
        "pricing_indicators": [],
        "contact_methods": [],
        "platform_mentions": []
    }
    
    try:
        url = f"http://{domain}" if not domain.startswith("http") else domain
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS, allow_redirects=True)
        
        if response.status_code != 200:
            return result
        
        content = response.text.lower()
        
        # Vendor type keywords (public indicators)
        vendor_keywords = {
            "synthetic_identity": [
                "synthetic identity", "fake id", "identity kit", "persona pack",
                "fake documents", "synthetic id", "identity bundle"
            ],
            "deepfake": [
                "deepfake", "face swap", "voice clone", "ai impersonation",
                "video deepfake", "voice deepfake", "face swap service"
            ],
            "impersonation": [
                "impersonation", "roleplay", "character pack", "profile kit",
                "fake profile", "synthetic persona"
            ]
        }
        
        # Check for vendor keywords
        for vendor_type, keywords in vendor_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    result["vendor_keywords"].append({
                        "type": vendor_type,
                        "keyword": keyword,
                        "context": _extract_context(content, keyword)
                    })
        
        # Extract pricing information (if public)
        pricing_patterns = [
            r'\$[\d,]+',  # USD
            r'€[\d,]+',   # EUR
            r'£[\d,]+',   # GBP
            r'[\d,]+\s*btc',  # Bitcoin
            r'[\d,]+\s*eth',  # Ethereum
        ]
        
        for pattern in pricing_patterns:
            matches = re.findall(pattern, content)
            if matches:
                result["pricing_indicators"].extend(matches[:5])  # Limit to 5
        
        # Extract contact methods (public only)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        if emails:
            result["contact_methods"].extend(emails[:3])  # Limit to 3
        
        # Telegram mentions
        telegram_patterns = [
            r'telegram[:\s]+@?([a-z0-9_]+)',
            r't\.me/([a-z0-9_]+)',
            r'@([a-z0-9_]+).*telegram'
        ]
        
        for pattern in telegram_patterns:
            matches = re.findall(pattern, content)
            if matches:
                result["contact_methods"].extend([f"@{m}" for m in matches[:3]])
        
        # Platform mentions
        platforms = ["telegram", "discord", "whatsapp", "signal", "wickr"]
        for platform in platforms:
            if platform in content:
                result["platform_mentions"].append(platform)
        
        # Extract service descriptions (simple pattern matching)
        service_patterns = [
            r'we (?:offer|provide|sell|create).{0,200}',
            r'our (?:service|product|kit|pack).{0,200}',
        ]
        
        for pattern in service_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                result["service_descriptions"].extend([m.strip()[:200] for m in matches[:3]])
        
    except Exception as e:
        print(f"Public content analysis failed for {domain}: {e}")
    
    return result


def _extract_context(text: str, keyword: str, context_length: int = 100) -> str:
    """Extract context around a keyword."""
    index = text.find(keyword)
    if index == -1:
        return ""
    
    start = max(0, index - context_length)
    end = min(len(text), index + len(keyword) + context_length)
    
    context = text[start:end]
    # Clean up context
    context = re.sub(r'\s+', ' ', context)
    return context.strip()


def analyze_public_telegram_channel(channel_username: str) -> Dict:
    """
    Analyze public Telegram channel (if accessible via API).
    
    Note: Requires Telegram API access or public channel scraping (if ToS allows).
    This is a placeholder for legitimate Telegram monitoring.
    
    Returns:
        Dictionary with channel analysis
    """
    result = {
        "channel_name": channel_username,
        "post_count": 0,
        "vendor_mentions": [],
        "service_descriptions": []
    }
    
    # TODO: Implement if Telegram API access is available
    # Or use legitimate Telegram monitoring services
    
    return result

