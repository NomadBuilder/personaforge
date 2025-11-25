"""
Clearnet marketplace discovery for persona kit vendors.

Uses headless browser (Playwright) to scrape marketplaces.
No API keys needed.

100% legal - only public listings and metadata.
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from src.utils.config import Config
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter()

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install")

# Keywords for finding persona kit services
MARKETPLACE_KEYWORDS = [
    "deepfake service",
    "fake id",
    "synthetic identity",
    "persona kit",
    "KYC bypass",
    "fake documents",
    "voice clone"
]


def search_fiverr_with_browser(keywords: List[str] = None, limit: int = 20) -> List[Dict]:
    """Search Fiverr using headless browser."""
    if keywords is None:
        keywords = MARKETPLACE_KEYWORDS[:3]
    
    results = []
    
    if not PLAYWRIGHT_AVAILABLE:
        return search_fiverr_basic(keywords, limit)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for keyword in keywords:
                try:
                    if not rate_limiter.can_make_request("fiverr"):
                        continue
                    
                    url = f"https://www.fiverr.com/search/gigs?query={keyword.replace(' ', '+')}"
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(3000)  # Wait for results to load
                    
                    # Extract gig links
                    gig_links = page.query_selector_all('a[href*="/gigs/"]')
                    
                    for link in gig_links[:limit]:
                        href = link.get_attribute('href')
                        title = link.get_attribute('title') or link.inner_text()
                        
                        if href and title:
                            results.append({
                                "marketplace": "fiverr",
                                "keyword": keyword,
                                "title": title[:200],
                                "url": f"https://www.fiverr.com{href}" if href.startswith('/') else href
                            })
                    
                    rate_limiter.record_request("fiverr")
                    
                except Exception as e:
                    logger.debug(f"Fiverr browser search failed for '{keyword}': {e}")
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Fiverr browser discovery failed: {e}")
        return search_fiverr_basic(keywords, limit)
    
    return results


def search_fiverr_basic(keywords: List[str] = None, limit: int = 20) -> List[Dict]:
    """Basic Fiverr search using requests."""
    if keywords is None:
        keywords = MARKETPLACE_KEYWORDS[:2]
    
    results = []
    
    for keyword in keywords:
        try:
            if not rate_limiter.can_make_request("fiverr"):
                continue
            
            url = f"https://www.fiverr.com/search/gigs?query={keyword.replace(' ', '+')}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=Config.API_TIMEOUT_SECONDS)
            rate_limiter.record_request("fiverr")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=re.compile(r'/gigs/'))
                
                for link in links[:limit]:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    if href:
                        results.append({
                            "marketplace": "fiverr",
                            "keyword": keyword,
                            "title": title,
                            "url": f"https://www.fiverr.com{href}" if href.startswith('/') else href
                        })
        except Exception as e:
            logger.debug(f"Basic Fiverr search failed: {e}")
    
    return results


def extract_domains_from_marketplace_listings(listings: List[Dict]) -> List[str]:
    """Extract domains from marketplace listings using headless browser."""
    domains = set()
    
    if not PLAYWRIGHT_AVAILABLE:
        return list(domains)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for listing in listings[:10]:  # Limit to avoid too many requests
                try:
                    if not rate_limiter.can_make_request("marketplace"):
                        continue
                    
                    url = listing.get('url', '')
                    if not url:
                        continue
                    
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(2000)
                    
                    # Get page content
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()
                    
                    # Find domains
                    domain_pattern = r'(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z]{2,}\.?)+)'
                    found = re.findall(domain_pattern, text, re.IGNORECASE)
                    
                    # Filter out marketplace domains
                    for domain in found:
                        domain = domain.lower()
                        if not any(skip in domain for skip in ['fiverr.com', 'upwork.com', 'etsy.com', 'gumroad.com', 'shopify.com']):
                            domains.add(domain)
                    
                    rate_limiter.record_request("marketplace")
                    
                except Exception as e:
                    logger.debug(f"Error visiting marketplace listing: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Error extracting domains from marketplace: {e}")
    
    return list(domains)


def search_clearnet_marketplaces(keywords: List[str] = None, limit: int = 30) -> Dict:
    """
    Search multiple clearnet marketplaces for persona kit vendors.
    
    Returns:
        Dictionary with marketplace results and domains
    """
    result = {
        "fiverr": [],
        "domains": set()
    }
    
    try:
        fiverr_results = search_fiverr_with_browser(keywords, limit=limit)
        result["fiverr"] = fiverr_results
        
        # Extract domains from listings
        if fiverr_results:
            domains = extract_domains_from_marketplace_listings(fiverr_results)
            result["domains"] = list(domains)
        
        logger.info(f"Marketplace discovery: {len(fiverr_results)} Fiverr listings, {len(result['domains'])} domains")
        
    except Exception as e:
        logger.error(f"Marketplace discovery failed: {e}")
    
    return result
