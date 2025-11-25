"""
Search engine discovery using SerpAPI (recommended over scraping).

SerpAPI provides reliable, structured search results without:
- CAPTCHA challenges
- IP blocking
- Breaking when sites change structure
- Legal concerns

Free tier: 100 searches/month
Paid: $50/month for 5,000 searches
"""

import re
from typing import List, Dict, Optional
from src.utils.config import Config
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter()

# Try to import SerpAPI
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    logger.warning("SerpAPI not available. Install with: pip install google-search-results")
    GoogleSearch = None


def search_with_serpapi(keywords: List[str] = None, limit: int = 50) -> List[str]:
    """
    Search Google using SerpAPI and extract domains.
    
    Much more reliable than scraping - handles CAPTCHAs, proxies, etc.
    
    Returns:
        List of discovered domain names
    """
    if not SERPAPI_AVAILABLE or not Config.SERPAPI_API_KEY:
        logger.debug("SerpAPI not available - skipping")
        return []
    
    if keywords is None:
        keywords = [
            "fake id for sale",
            "deepfake service",
            "synthetic identity kit",
            "fake documents online",
            "persona kit for sale"
        ]
    
    discovered_domains = set()
    
    for keyword in keywords[:5]:  # Limit to avoid hitting API limits
        try:
            if not rate_limiter.can_make_request("serpapi"):
                logger.debug(f"Rate limit hit for SerpAPI, skipping: {keyword}")
                continue
            
            params = {
                "q": keyword,
                "api_key": Config.SERPAPI_API_KEY,
                "num": 50,  # Results per page
                "hl": "en",
                "gl": "us"
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            rate_limiter.record_request("serpapi")
            
            # Extract domains from organic results
            organic_results = results.get("organic_results", [])
            
            for result in organic_results[:limit]:
                link = result.get("link", "")
                if link:
                    # Extract domain from URL
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', link)
                    if domain_match:
                        domain = domain_match.group(1).lower()
                        # Filter out common sites
                        if not any(skip in domain for skip in [
                            'google.com', 'youtube.com', 'reddit.com', 'facebook.com',
                            'twitter.com', 'instagram.com', 'linkedin.com', 'wikipedia.org'
                        ]):
                            discovered_domains.add(domain)
            
            # Also check "People Also Ask" and related searches
            related_searches = results.get("related_searches", [])
            for related in related_searches:
                query = related.get("query", "")
                if query:
                    # Could do additional searches, but limit to avoid API costs
                    pass
            
            logger.debug(f"SerpAPI search for '{keyword}': {len(organic_results)} results")
            
        except Exception as e:
            logger.error(f"SerpAPI search failed for '{keyword}': {e}")
            continue
    
    return list(discovered_domains)


def search_youtube_with_serpapi(keywords: List[str] = None, limit: int = 20) -> Dict:
    """
    Search YouTube using SerpAPI and extract domains from video descriptions.
    
    Returns:
        Dictionary with videos and extracted domains
    """
    if not SERPAPI_AVAILABLE or not Config.SERPAPI_API_KEY:
        logger.debug("SerpAPI not available - skipping YouTube search")
        return {"videos": [], "domains": []}
    
    if keywords is None:
        keywords = [
            "fake id for sale",
            "deepfake service",
            "synthetic identity kit"
        ]
    
    videos = []
    domains = set()
    
    for keyword in keywords[:3]:  # Limit to avoid API costs
        try:
            if not rate_limiter.can_make_request("serpapi"):
                continue
            
            params = {
                "search_query": keyword,  # YouTube engine uses search_query, not q
                "api_key": Config.SERPAPI_API_KEY,
                "engine": "youtube",
                "num": 20
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            rate_limiter.record_request("serpapi")
            
            video_results = results.get("video_results", [])
            
            for video in video_results[:limit]:
                video_id = video.get("video_id") or video.get("id")
                title = video.get("title", "")
                link = video.get("link", "") or video.get("url", "")
                # Try multiple fields for description
                description = (
                    video.get("description", "") or 
                    video.get("snippet", "") or 
                    video.get("about_this_result", {}).get("snippet", "") or
                    ""
                )
                
                if video_id:
                    videos.append({
                        "video_id": video_id,
                        "title": title,
                        "url": link,
                        "description": description
                    })
                    
                    # Extract domains from description
                    if description:
                        domain_pattern = r'(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z]{2,}\.?)+)'
                        found = re.findall(domain_pattern, description, re.IGNORECASE)
                        
                        for domain in found:
                            domain = domain.lower()
                            if not any(skip in domain for skip in [
                                'youtube.com', 'youtu.be', 'google.com', 'goo.gl'
                            ]):
                                domains.add(domain)
            
            logger.debug(f"SerpAPI YouTube search for '{keyword}': {len(video_results)} videos")
            
        except Exception as e:
            logger.error(f"SerpAPI YouTube search failed for '{keyword}': {e}")
            continue
    
    return {
        "videos": videos,
        "domains": list(domains)
    }

