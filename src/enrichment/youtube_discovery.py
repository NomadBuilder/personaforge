"""
YouTube discovery for deepfake and persona kit vendors.

Uses headless browser (Playwright) to scrape YouTube search results.
No API keys needed.

100% legal - public data only.
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

# Keywords for finding deepfake/persona vendors
# More specific terms that vendors actually use
SEARCH_KEYWORDS = [
    "fake id for sale",
    "fake documents online",
    "deepfake service buy",
    "synthetic identity kit",
    "fake passport generator",
    "fake driver license maker",
    "ai voice clone service",
    "fake kyc documents",
    "deepfake video call service",
    "synthetic identity marketplace",
    "fake id vendor review",
    "persona kit download",
    "fake documents vendor",
    "deepfake face swap service"
]


def search_youtube_with_browser(keywords: List[str] = None, limit: int = 20) -> List[Dict]:
    """
    Search YouTube using headless browser.
    
    Uses Playwright to scrape YouTube search results.
    """
    if keywords is None:
        keywords = SEARCH_KEYWORDS[:5]
    
    results = []
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available - using basic scraping")
        return search_youtube_basic(keywords, limit)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for keyword in keywords:
                try:
                    if not rate_limiter.can_make_request("youtube"):
                        continue
                    
                    # Search YouTube
                    url = f"https://www.youtube.com/results?search_query={keyword.replace(' ', '+')}"
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(3000)  # Wait for videos to load
                    
                    # Scroll to load more results
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    
                    # Extract video links - YouTube uses various selectors
                    video_links = page.query_selector_all('a[href*="/watch?v="]')
                    logger.debug(f"Found {len(video_links)} video links for keyword: {keyword}")
                    
                    seen_ids = set()
                    for link in video_links[:limit * 3]:  # Get more to filter duplicates
                        try:
                            href = link.get_attribute('href')
                            if not href:
                                continue
                            
                            # Get title - try multiple methods
                            title = ""
                            try:
                                title_elem = link.query_selector('#video-title')
                                if title_elem:
                                    title = title_elem.get_attribute('title') or title_elem.inner_text()
                                else:
                                    title = link.get_attribute('title') or link.inner_text()
                            except:
                                title = link.inner_text()
                            
                            # Extract video ID
                            video_id_match = re.search(r'v=([a-zA-Z0-9_-]{11})', href)
                            if video_id_match:
                                video_id = video_id_match.group(1)
                                if video_id and video_id not in seen_ids and len(video_id) == 11:
                                    seen_ids.add(video_id)
                                    full_url = f"https://www.youtube.com{href}" if href.startswith('/') else href
                                    results.append({
                                        "title": title[:200] if title else "",
                                        "video_id": video_id,
                                        "url": full_url,
                                        "keyword": keyword
                                    })
                        except Exception as e:
                            logger.debug(f"Error extracting video link: {e}")
                            continue
                    
                    rate_limiter.record_request("youtube")
                    
                except Exception as e:
                    logger.debug(f"YouTube browser search failed for '{keyword}': {e}")
            
            browser.close()
            
    except Exception as e:
        logger.error(f"YouTube browser discovery failed: {e}")
        return search_youtube_basic(keywords, limit)
    
    return results[:limit]


def search_youtube_basic(keywords: List[str] = None, limit: int = 20) -> List[Dict]:
    """Basic YouTube search using requests."""
    if keywords is None:
        keywords = SEARCH_KEYWORDS[:3]
    
    results = []
    
    for keyword in keywords:
        try:
            if not rate_limiter.can_make_request("youtube"):
                continue
            
            url = f"https://www.youtube.com/results?search_query={keyword.replace(' ', '+')}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=Config.API_TIMEOUT_SECONDS)
            rate_limiter.record_request("youtube")
            
            if response.status_code == 200:
                # YouTube embeds data in script tags - extract video IDs
                video_id_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
                video_ids = re.findall(video_id_pattern, response.text)
                
                for vid_id in list(set(video_ids))[:limit]:
                    results.append({
                        "title": "",
                        "video_id": vid_id,
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "keyword": keyword
                    })
        except Exception as e:
            logger.debug(f"Basic YouTube search failed: {e}")
    
    return results


def extract_domains_from_youtube_videos(videos: List[Dict]) -> List[str]:
    """
    Visit YouTube video pages and extract domains from descriptions.
    
    Uses headless browser to get video descriptions.
    """
    domains = set()
    
    if not PLAYWRIGHT_AVAILABLE:
        return list(domains)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for video in videos[:15]:  # Limit to avoid too many requests
                try:
                    if not rate_limiter.can_make_request("youtube"):
                        continue
                    
                    video_url = video.get('url', '')
                    if not video_url:
                        continue
                    
                    # Visit video page
                    page.goto(video_url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(2000)
                    
                    # Get description - ONLY the video description, not entire page
                    description = ""
                    try:
                        # Try to get ONLY the video description text
                        desc_selectors = [
                            '#description-text',
                            'ytd-expander #content',
                            '#description yt-formatted-string',
                            '#description'
                        ]
                        
                        for selector in desc_selectors:
                            elem = page.query_selector(selector)
                            if elem:
                                description = elem.inner_text()
                                if description and len(description) > 20:  # Make sure we got actual text
                                    break
                        
                        # If we didn't get description, skip this video (don't scrape entire page)
                        if not description or len(description) < 20:
                            logger.debug(f"No description found for video {video.get('video_id')}")
                            continue
                            
                    except Exception as e:
                        logger.debug(f"Error getting description: {e}")
                        continue  # Skip this video if we can't get description
                    
                    # Extract domains - only from description text, not page source
                    # Use stricter pattern: must look like a real domain
                    domain_pattern = r'(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z]{2,}|[a-z]{2,}\.[a-z]{2,}))'
                    found = re.findall(domain_pattern, description, re.IGNORECASE)
                    
                    for domain in found:
                        domain = domain.lower()
                        if not any(skip in domain for skip in ['youtube.com', 'youtu.be', 'google.com', 'goo.gl']):
                            domains.add(domain)
                    
                    rate_limiter.record_request("youtube")
                    
                except Exception as e:
                    logger.debug(f"Error visiting YouTube video: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Error extracting domains from YouTube: {e}")
    
    return list(domains)


def discover_youtube_vendors(limit: int = 30) -> Dict:
    """
    Discover persona kit vendors from YouTube.
    
    Returns:
        Dictionary with videos and extracted domains
    """
    result = {
        "videos": [],
        "domains": []
    }
    
    try:
        # Search for videos
        videos = search_youtube_with_browser(limit=limit)
        result["videos"] = videos
        
        # Extract domains from video descriptions
        if videos:
            domains = extract_domains_from_youtube_videos(videos)
            result["domains"] = domains
        
        logger.info(f"YouTube discovery: {len(videos)} videos, {len(result['domains'])} domains")
        
    except Exception as e:
        logger.error(f"YouTube discovery failed: {e}")
    
    return result
