"""
Social media intelligence (public profiles only).

Many vendors use public social media profiles:
- Twitter/X accounts
- Instagram profiles
- Public Telegram channels
- Public Discord servers

All accessible via clearnet - no special access needed.
"""

import requests
import re
from typing import Dict, List, Optional
from src.utils.config import Config
from src.utils.logger import logger


def find_twitter_profiles(domain: str, content: str = None) -> List[str]:
    """
    Find Twitter/X profiles mentioned on a domain.
    
    Returns:
        List of Twitter usernames
    """
    profiles = []
    
    if not content:
        try:
            url = f"http://{domain}" if not domain.startswith("http") else domain
            response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
            if response.status_code == 200:
                content = response.text
        except:
            return profiles
    
    if content:
        # Twitter link patterns
        twitter_patterns = [
            r'twitter\.com/([a-z0-9_]+)',
            r'x\.com/([a-z0-9_]+)',
            r'@([a-z0-9_]+).*twitter',
            r'twitter[:\s]+@?([a-z0-9_]+)',
        ]
        
        for pattern in twitter_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            profiles.extend([f"@{m}" if not m.startswith("@") else m for m in matches])
    
    return list(set(profiles))


def find_instagram_profiles(domain: str, content: str = None) -> List[str]:
    """
    Find Instagram profiles mentioned on a domain.
    
    Returns:
        List of Instagram usernames
    """
    profiles = []
    
    if not content:
        try:
            url = f"http://{domain}" if not domain.startswith("http") else domain
            response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
            if response.status_code == 200:
                content = response.text
        except:
            return profiles
    
    if content:
        # Instagram link patterns
        instagram_patterns = [
            r'instagram\.com/([a-z0-9_.]+)',
            r'@([a-z0-9_.]+).*instagram',
            r'instagram[:\s]+@?([a-z0-9_.]+)',
        ]
        
        for pattern in instagram_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            profiles.extend([f"@{m}" if not m.startswith("@") else m for m in matches])
    
    return list(set(profiles))


def find_discord_servers(domain: str, content: str = None) -> List[str]:
    """
    Find Discord server invites mentioned on a domain.
    
    Returns:
        List of Discord invite codes
    """
    invites = []
    
    if not content:
        try:
            url = f"http://{domain}" if not domain.startswith("http") else domain
            response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
            if response.status_code == 200:
                content = response.text
        except:
            return invites
    
    if content:
        # Discord invite patterns
        discord_patterns = [
            r'discord\.gg/([a-z0-9]+)',
            r'discord\.com/invite/([a-z0-9]+)',
            r'discord[:\s]+([a-z0-9]+)',
        ]
        
        for pattern in discord_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            invites.extend(matches)
    
    return list(set(invites))


def enrich_social_media(domain: str) -> Dict:
    """
    Find all social media profiles associated with a domain.
    
    Returns:
        Dictionary with social media intelligence
    """
    result = {
        "twitter": [],
        "instagram": [],
        "telegram": [],
        "discord": [],
        "other": []
    }
    
    try:
        url = f"http://{domain}" if not domain.startswith("http") else domain
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            content = response.text
            
            # Find all social media profiles
            result["twitter"] = find_twitter_profiles(domain, content)
            result["instagram"] = find_instagram_profiles(domain, content)
            result["discord"] = find_discord_servers(domain, content)
            
            # Telegram (from clearnet_mirrors, but also check here)
            from .clearnet_mirrors import find_telegram_channels
            result["telegram"] = find_telegram_channels(domain, content)
            
    except Exception as e:
        logger.debug(f"Social media enrichment failed for {domain}: {e}")
    
    return result

