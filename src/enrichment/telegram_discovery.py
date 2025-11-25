"""
Telegram channel discovery for persona kit vendors.

Uses headless browser (Playwright) to scrape Telegram channels.
No API keys needed - uses Telegram's public web interface.

100% legal - metadata only, no illegal content.
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from src.utils.config import Config
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter()

# Try to import Playwright for headless browser
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install")

# Keywords for finding persona kit vendors
VENDOR_KEYWORDS = [
    "deepfake",
    "synthetic identity",
    "fake id",
    "persona kit",
    "KYC bypass",
    "voice clone",
    "fake documents",
    "identity pack"
]


def search_telegram_with_browser(keywords: List[str] = None, limit: int = 20) -> List[Dict]:
    """
    Search Telegram channels using headless browser.
    
    Uses Playwright to scrape Telegram's web interface.
    """
    if keywords is None:
        keywords = VENDOR_KEYWORDS[:5]
    
    channels = []
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available - using basic scraping")
        return search_telegram_basic(keywords, limit)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for keyword in keywords:
                try:
                    if not rate_limiter.can_make_request("telegram"):
                        continue
                    
                    # Search Telegram channels directory
                    # Try multiple Telegram channel directory sites
                    search_urls = [
                        f"https://telegramchannels.me/search?q={keyword.replace(' ', '+')}",
                        f"https://tlgrm.ru/channels?q={keyword.replace(' ', '+')}",
                    ]
                    
                    for url in search_urls:
                        try:
                            page.goto(url, wait_until="networkidle", timeout=30000)
                            page.wait_for_timeout(2000)  # Wait for JS to load
                            
                            # Extract channel links
                            channel_links = page.query_selector_all('a[href*="t.me/"]')
                            
                            for link in channel_links[:limit]:
                                href = link.get_attribute('href')
                                text = link.inner_text()
                                
                                if href:
                                    match = re.search(r't\.me/([a-zA-Z0-9_]+)', href)
                                    if match:
                                        username = match.group(1)
                                        if username and username not in ['s', 'joinchat', 'share']:
                                            channels.append({
                                                "name": text or username,
                                                "username": username,
                                                "url": f"https://t.me/{username}",
                                                "keyword": keyword
                                            })
                        except Exception as e:
                            logger.debug(f"Telegram search failed for {url}: {e}")
                            continue
                    
                    rate_limiter.record_request("telegram")
                    
                except Exception as e:
                    logger.debug(f"Telegram browser search failed for '{keyword}': {e}")
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Telegram browser discovery failed: {e}")
        return search_telegram_basic(keywords, limit)
    
    # Remove duplicates
    seen = set()
    unique_channels = []
    for ch in channels:
        key = ch.get('username')
        if key and key not in seen:
            seen.add(key)
            unique_channels.append(ch)
    
    return unique_channels[:limit]


def search_telegram_basic(keywords: List[str] = None, limit: int = 20) -> List[Dict]:
    """Basic Telegram search using requests + BeautifulSoup."""
    if keywords is None:
        keywords = VENDOR_KEYWORDS[:3]
    
    channels = []
    
    for keyword in keywords:
        try:
            if not rate_limiter.can_make_request("telegram"):
                continue
            
            # Try telegram channel directory sites
            url = f"https://telegramchannels.me/search?q={keyword.replace(' ', '+')}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=Config.API_TIMEOUT_SECONDS)
            rate_limiter.record_request("telegram")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find channel links
                links = soup.find_all('a', href=re.compile(r't\.me/'))
                
                for link in links[:limit]:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    match = re.search(r't\.me/([a-zA-Z0-9_]+)', href)
                    if match:
                        username = match.group(1)
                        if username and username not in ['s', 'joinchat']:
                            channels.append({
                                "name": text or username,
                                "username": username,
                                "url": f"https://t.me/{username}",
                                "keyword": keyword
                            })
        except Exception as e:
            logger.debug(f"Basic Telegram search failed: {e}")
    
    return channels


def extract_domains_from_telegram_channels(channels: List[Dict]) -> List[str]:
    """
    Visit Telegram channel pages and extract domains from descriptions.
    
    Uses headless browser to get channel metadata.
    """
    domains = set()
    
    if not PLAYWRIGHT_AVAILABLE:
        return list(domains)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for channel in channels[:10]:  # Limit to avoid too many requests
                try:
                    if not rate_limiter.can_make_request("telegram"):
                        continue
                    
                    channel_url = channel.get('url', '')
                    if not channel_url:
                        continue
                    
                    # Visit channel page
                    page.goto(channel_url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(2000)
                    
                    # Get page content
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract description text
                    description = soup.get_text()
                    
                    # Find domains in description
                    domain_pattern = r'(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z]{2,}\.?)+)'
                    found = re.findall(domain_pattern, description, re.IGNORECASE)
                    
                    for domain in found:
                        domain = domain.lower()
                        if 't.me' not in domain and 'telegram.org' not in domain:
                            domains.add(domain)
                    
                    rate_limiter.record_request("telegram")
                    
                except Exception as e:
                    logger.debug(f"Error visiting Telegram channel: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Error extracting domains from Telegram: {e}")
    
    return list(domains)


def discover_telegram_vendors(limit: int = 30) -> Dict:
    """
    Discover persona kit vendors from Telegram channels.
    
    Returns:
        Dictionary with channels and extracted domains
    """
    result = {
        "channels": [],
        "domains": []
    }
    
    try:
        # Search for channels
        channels = search_telegram_with_browser(limit=limit)
        result["channels"] = channels
        
        # Extract domains from channel pages
        if channels:
            domains = extract_domains_from_telegram_channels(channels)
            result["domains"] = domains
        
        logger.info(f"Telegram discovery: {len(channels)} channels, {len(result['domains'])} domains")
        
    except Exception as e:
        logger.error(f"Telegram discovery failed: {e}")
    
    return result
