"""
Active vendor discovery from public sources.

This module actively searches for synthetic identity vendors from:
- AI-powered discovery (OpenAI to find data sources and vendors)
- Public Telegram channels
- Public forums and marketplaces
- Certificate Transparency (crt.sh) keyword searches
- Public paste sites
- Search engine results
- Public social media mentions

All sources are publicly accessible - no dark web access needed.
"""

import requests
import re
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.utils.config import Config
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter

# Initialize rate limiter
rate_limiter = RateLimiter()

# Try to import OpenAI for AI-powered discovery
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


# Keywords that indicate synthetic identity vendors
# More specific terms that vendors actually use
VENDOR_KEYWORDS = [
    "fake id for sale",
    "fake documents online",
    "deepfake service",
    "synthetic identity kit",
    "persona pack buy",
    "fake passport generator",
    "fake driver license maker",
    "identity pack download",
    "synthetic id vendor",
    "fake documents vendor",
    "deepfake video call",
    "ai voice clone service",
    "fake kyc documents",
    "synthetic identity marketplace",
    "fake id vendor",
    "persona kit for sale",
    "fake documents service",
    "deepfake face swap",
    "ai identity generator",
    "fake id maker online",
    "fake ssn",
    "credit profile",
    "bank account",
    "verification service",
    "identity verification bypass",
    "fake utility bill",
    "proof of address",
    "kyc bypass"
]


def discover_from_crtsh(keywords: List[str] = None, limit: int = 50) -> List[str]:
    """
    Discover domains from Certificate Transparency logs using keywords.
    
    Searches crt.sh for domains with suspicious keywords in their certificates.
    
    Returns:
        List of discovered domain names
    """
    if keywords is None:
        keywords = ["deepfake", "synthetic", "identity", "persona", "fake"]
    
    discovered_domains = set()
    
    for keyword in keywords[:3]:  # Limit to avoid too many requests
        try:
            if not rate_limiter.can_make_request("crtsh"):
                continue
            
            # Search crt.sh for domains with keyword
            url = f"https://crt.sh/?q=%25{keyword}%25&output=json"
            response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
            rate_limiter.record_request("crtsh")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for cert in data[:limit]:
                        name_value = cert.get("name_value", "")
                        if name_value:
                            for name in name_value.split("\n"):
                                name = name.strip().lower()
                                # Remove wildcards and clean
                                if name.startswith("*."):
                                    name = name[2:]
                                # Extract root domain
                                if "." in name and len(name) > 4:
                                    parts = name.split(".")
                                    if len(parts) >= 2:
                                        root_domain = ".".join(parts[-2:])
                                        # Filter out common/legitimate domains
                                        if (root_domain and 
                                            not root_domain.startswith("*") and
                                            len(root_domain) > 4 and
                                            not any(skip in root_domain for skip in 
                                                   ['google.com', 'microsoft.com', 'amazon.com', 
                                                    'cloudflare.com', 'github.com', 'example.com'])):
                                            discovered_domains.add(root_domain)
        except Exception as e:
            logger.debug(f"crt.sh discovery failed for keyword '{keyword}': {e}")
    
    return list(discovered_domains)


def discover_from_paste_sites(limit: int = 20) -> List[str]:
    """
    Search public paste sites for vendor domains.
    
    Checks pastebin.com, paste.ee, and other public paste sites.
    
    Returns:
        List of discovered domain names
    """
    discovered_domains = set()
    
    # Common paste site APIs (public access)
    paste_sites = [
        {
            "name": "pastebin",
            "search_url": "https://pastebin.com/archive",
            "api_url": None  # Pastebin requires API key for search
        }
    ]
    
    # For now, we'll use a simpler approach - search for known patterns
    # In production, you'd use paste site APIs or scrape public listings
    
    return list(discovered_domains)


def discover_from_telegram_public_channels(limit: int = 30) -> List[str]:
    """
    Discover domains from public Telegram channels.
    
    Uses Telegram's public web interface to search for channels mentioning
    synthetic identity keywords, then extracts domains from messages.
    
    Note: This uses public web interface only - no API key needed.
    
    Returns:
        List of discovered domain names
    """
    discovered_domains = set()
    
    # Telegram public channel search (via web)
    # Note: Telegram web interface can be scraped, but rate-limited
    search_terms = ["synthetic identity", "fake id", "persona kit", "deepfake"]
    
    for term in search_terms[:3]:  # Limit searches
        try:
            if not rate_limiter.can_make_request("telegram"):
                continue
            
            # Search Telegram public channels via web
            # This is a simplified version - in production you'd use Telegram API
            # or scrape public channel listings
            url = f"https://t.me/s/{term.replace(' ', '_')}"
            # Note: Actual implementation would need to parse Telegram web pages
            # or use Telegram Bot API for public channels
            
        except Exception as e:
            logger.debug(f"Telegram discovery failed: {e}")
    
    return list(discovered_domains)


def discover_from_reddit(limit: int = 20) -> List[str]:
    """
    Search Reddit for vendor mentions (public subreddits only).
    
    Uses Reddit's public JSON API and web scraping to find posts mentioning
    synthetic identity keywords.
    
    Returns:
        List of discovered domain names
    """
    discovered_domains = set()
    
    # More specific search terms targeting actual vendors
    search_terms = [
        "fake id for sale",
        "fake documents online",
        "deepfake service buy",
        "synthetic identity kit",
        "fake passport generator",
        "fake driver license maker",
        "ai voice clone service",
        "fake kyc documents",
        "synthetic identity marketplace",
        "fake id vendor review"
    ]
    
    for term in search_terms[:3]:  # Limit to avoid rate limits
        try:
            if not rate_limiter.can_make_request("reddit"):
                continue
            
            # Reddit JSON API (no auth needed for public data)
            url = f"https://www.reddit.com/search.json?q={term}&limit={limit}&sort=relevance"
            headers = {"User-Agent": "PersonaForge/1.0 (OSINT Research Tool)"}
            response = requests.get(url, headers=headers, timeout=Config.API_TIMEOUT_SECONDS)
            rate_limiter.record_request("reddit")
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                
                for post in posts:
                    post_data = post.get("data", {})
                    # Extract domains from title, selftext, and URL
                    text = f"{post_data.get('title', '')} {post_data.get('selftext', '')} {post_data.get('url', '')}"
                    
                    # Find domains in text
                    domain_pattern = r'(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z]{2,}\.?)+)'
                    domains = re.findall(domain_pattern, text, re.IGNORECASE)
                    
                    for domain in domains:
                        domain = domain.lower().strip()
                        # Filter out common/legitimate domains
                        skip_domains = [
                            'reddit.com', 'imgur.com', 'youtube.com', 'twitter.com', 'x.com',
                            'facebook.com', 'instagram.com', 'tiktok.com', 'discord.com',
                            'google.com', 'amazon.com', 'microsoft.com', 'apple.com',
                            'github.com', 'stackoverflow.com', 'wikipedia.org',
                            # News sites (just mentioned, not vendors)
                            'cnn.com', 'bloomberg.com', 'reuters.com', 'bbc.com', 'nytimes.com',
                            'washingtonpost.com', 'fortune.com', 'nasdaq.com', 'wsj.com',
                            'theguardian.com', 'usnews.com', 'news', 'gov', 'edu', 'org'
                        ]
                        if domain and len(domain) > 4 and not any(skip in domain for skip in skip_domains):
                            discovered_domains.add(domain)
        except Exception as e:
            logger.debug(f"Reddit discovery failed: {e}")
    
    return list(discovered_domains)


def discover_from_search_engines(keywords: List[str] = None, limit: int = 50) -> List[str]:
    """
    Discover domains using search engine results.
    
    Uses DuckDuckGo web scraping (no API key needed) to search for vendor keywords
    and extract domains from results.
    
    Returns:
        List of discovered domain names
    """
    if keywords is None:
        keywords = ["deepfake service", "synthetic identity vendor", "fake id for sale", "persona kit"]
    
    discovered_domains = set()
    
    try:
        from bs4 import BeautifulSoup
        BEAUTIFULSOUP_AVAILABLE = True
    except ImportError:
        BEAUTIFULSOUP_AVAILABLE = False
    
    for keyword in keywords[:5]:  # More searches
        try:
            if not rate_limiter.can_make_request("duckduckgo"):
                continue
            
            # DuckDuckGo HTML search (no API key needed)
            url = f"https://html.duckduckgo.com/html/?q={keyword.replace(' ', '+')}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=Config.API_TIMEOUT_SECONDS)
            rate_limiter.record_request("duckduckgo")
            
            if response.status_code == 200:
                if BEAUTIFULSOUP_AVAILABLE:
                    # Parse HTML properly
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find result links
                    result_links = soup.find_all('a', class_=re.compile('result|link'))
                    
                    for link in result_links[:limit]:
                        href = link.get('href', '')
                        if href:
                            # Extract domain from URL
                            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', href)
                            if domain_match:
                                domain = domain_match.group(1).lower().strip()
                                # Filter out search engine domains
                                if domain and not any(skip in domain for skip in 
                                                     ['duckduckgo.com', 'google.com', 'bing.com', 'yahoo.com',
                                                      'wikipedia.org', 'youtube.com', 'reddit.com']):
                                    discovered_domains.add(domain)
                else:
                    # Fallback: regex extraction
                    domain_pattern = r'https?://(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:[a-z]{2,}\.?)+)'
                    domains = re.findall(domain_pattern, response.text, re.IGNORECASE)
                    
                    for domain in domains[:limit]:
                        domain = domain.lower().strip()
                        if domain and not any(skip in domain for skip in 
                                             ['duckduckgo.com', 'google.com', 'bing.com', 'yahoo.com']):
                            discovered_domains.add(domain)
        except Exception as e:
            logger.debug(f"Search engine discovery failed for '{keyword}': {e}")
    
    return list(discovered_domains)


def discover_from_urlhaus(limit: int = 50) -> List[str]:
    """
    Discover domains from URLhaus malware database.
    
    URLhaus tracks malicious domains - some may be synthetic identity vendors.
    
    Returns:
        List of discovered domain names
    """
    discovered_domains = set()
    
    try:
        if not rate_limiter.can_make_request("urlhaus"):
            return list(discovered_domains)
        
        # Get recent malicious domains
        url = "https://urlhaus-api.abuse.ch/v1/payloads/recent/"
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS)
        rate_limiter.record_request("urlhaus")
        
        if response.status_code == 200:
            data = response.json()
            payloads = data.get("payloads", [])[:limit]
            
            for payload in payloads:
                url_data = payload.get("urlhaus_reference", "")
                # Extract domain from URL
                if url_data:
                    domain_match = re.search(r'https?://([^/]+)', url_data)
                    if domain_match:
                        domain = domain_match.group(1).lower()
                        if domain:
                            discovered_domains.add(domain)
    except Exception as e:
        logger.debug(f"URLhaus discovery failed: {e}")
    
    return list(discovered_domains)


def discover_with_ai(limit: int = 30) -> List[str]:
    """
    Use AI to intelligently discover vendor domains and data sources.
    
    Asks AI to:
    1. Find known data sources for synthetic identity vendors
    2. Generate search queries to find vendors
    3. Identify vendor domains from descriptions
    
    Returns:
        List of discovered domain names
    """
    discovered_domains = set()
    
    if not OPENAI_AVAILABLE or not Config.OPENAI_API_KEY:
        logger.debug("OpenAI not available - skipping AI discovery")
        return list(discovered_domains)
    
    try:
        if not rate_limiter.can_make_request("openai"):
            return list(discovered_domains)
        
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Ask AI to find data sources and vendor domains
        prompt = """You are an OSINT researcher tracking synthetic identity vendors and deepfake services.

Find me:
1. Known public data sources where these vendors operate (forums, marketplaces, Telegram channels, websites)
2. Specific domain names or patterns associated with synthetic identity vendors
3. Search queries I should use to find more vendors

Focus on publicly accessible sources only. Return a JSON list of domains and data sources.

Format:
{
  "domains": ["example1.com", "example2.com"],
  "data_sources": ["forum-url.com", "marketplace-url.com"],
  "search_queries": ["synthetic identity for sale", "fake id vendor"]
}"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for discovery
            messages=[
                {"role": "system", "content": "You are an OSINT researcher. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        rate_limiter.record_request("openai")
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            
            # Extract domains
            domains = data.get("domains", [])
            for domain in domains:
                if isinstance(domain, str) and "." in domain:
                    # Clean domain
                    domain = domain.lower().strip()
                    domain = domain.replace("http://", "").replace("https://", "").replace("www.", "")
                    domain = domain.split("/")[0].split("?")[0]
                    if domain and len(domain) > 3:
                        discovered_domains.add(domain)
            
            # Use search queries to find more
            queries = data.get("search_queries", [])
            for query in queries[:3]:  # Limit queries
                try:
                    # Use search engine with AI-generated query
                    search_results = discover_from_search_engines(keywords=[query], limit=10)
                    discovered_domains.update(search_results)
                except:
                    pass
        
        logger.info(f"AI discovery found {len(discovered_domains)} domains")
        
    except Exception as e:
        logger.error(f"AI discovery failed: {e}")
    
    return list(discovered_domains)


def ask_ai_for_data_sources() -> Dict:
    """
    Ask AI to identify data sources for finding synthetic identity vendors.
    
    Returns:
        Dictionary with data sources, search strategies, and keywords
    """
    if not OPENAI_AVAILABLE or not Config.OPENAI_API_KEY:
        return {
            "sources": [],
            "search_strategies": [],
            "keywords": VENDOR_KEYWORDS
        }
    
    try:
        if not rate_limiter.can_make_request("openai"):
            return {"sources": [], "search_strategies": [], "keywords": VENDOR_KEYWORDS}
        
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        prompt = """As an OSINT researcher, identify the best public data sources to find synthetic identity vendors and deepfake services.

Consider:
- Public forums where vendors advertise
- Marketplaces (clearnet and darknet mirrors)
- Telegram channels (public ones)
- Paste sites where vendors post
- Social media platforms
- Certificate Transparency logs
- Threat intelligence databases

Return JSON with:
{
  "data_sources": [
    {"name": "source name", "url": "url", "description": "how to use it"},
    ...
  ],
  "search_strategies": ["strategy 1", "strategy 2"],
  "keywords": ["keyword1", "keyword2"]
}"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an OSINT expert. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        
        rate_limiter.record_request("openai")
        
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        
    except Exception as e:
        logger.error(f"AI data source discovery failed: {e}")
    
    return {
        "sources": [],
        "search_strategies": [],
        "keywords": VENDOR_KEYWORDS
    }


def discover_all_sources(limit_per_source: int = 20) -> Dict[str, List[str]]:
    """
    Discover vendors from all available public sources.
    
    Returns:
        Dictionary with source names as keys and lists of domains as values
    """
    results = {
        "crtsh": [],
        "reddit": [],
        "search_engines": [],
        "urlhaus": [],
        "paste_sites": [],
        "telegram": []
    }
    
    logger.info("🔍 Starting vendor discovery from public OSINT sources...")
    
    # AI-powered discovery (if available)
    ai_domains = []
    if OPENAI_AVAILABLE and Config.OPENAI_API_KEY:
        try:
            ai_domains = discover_with_ai(limit=limit_per_source)
            results["ai_discovery"] = ai_domains
            logger.info(f"  ✓ AI Discovery: {len(ai_domains)} domains")
        except Exception as e:
            logger.error(f"  ✗ AI discovery failed: {e}")
    else:
        logger.info("  ⚠ AI discovery not available (no OpenAI API key)")
    
    # Telegram channels (metadata only)
    try:
        from .telegram_discovery import discover_telegram_vendors
        telegram_data = discover_telegram_vendors(limit=limit_per_source)
        results["telegram"] = telegram_data.get("domains", [])
        logger.info(f"  ✓ Telegram: {len(results['telegram'])} domains")
    except Exception as e:
        logger.error(f"  ✗ Telegram discovery failed: {e}")
    
    # YouTube channels (SerpAPI if available, else Playwright scraping)
    try:
        from src.enrichment.serpapi_discovery import search_youtube_with_serpapi
        
        if Config.SERPAPI_API_KEY:
            # Use SerpAPI (more reliable)
            youtube_result = search_youtube_with_serpapi(limit=limit_per_source)
            results["youtube"] = youtube_result.get("domains", [])
            logger.info(f"  ✓ YouTube (SerpAPI): {len(results['youtube'])} domains")
        else:
            # Fallback to Playwright scraping
            from .youtube_discovery import discover_youtube_vendors
            youtube_data = discover_youtube_vendors(limit=limit_per_source)
            results["youtube"] = youtube_data.get("domains", [])
            logger.info(f"  ✓ YouTube (scraping): {len(results['youtube'])} domains")
    except Exception as e:
        logger.error(f"  ✗ YouTube discovery failed: {e}")
    
    # Clearnet marketplaces
    try:
        from .marketplace_discovery import search_clearnet_marketplaces
        marketplace_data = search_clearnet_marketplaces(limit=limit_per_source)
        results["marketplaces"] = marketplace_data.get("domains", [])
        logger.info(f"  ✓ Marketplaces: {len(results['marketplaces'])} domains")
    except Exception as e:
        logger.error(f"  ✗ Marketplace discovery failed: {e}")
    
    # Certificate Transparency
    try:
        results["crtsh"] = discover_from_crtsh(limit=limit_per_source)
        logger.info(f"  ✓ crt.sh: {len(results['crtsh'])} domains")
    except Exception as e:
        logger.error(f"  ✗ crt.sh discovery failed: {e}")
    
    # Reddit
    try:
        results["reddit"] = discover_from_reddit(limit=limit_per_source)
        logger.info(f"  ✓ Reddit: {len(results['reddit'])} domains")
    except Exception as e:
        logger.error(f"  ✗ Reddit discovery failed: {e}")
    
    # Search engines (SerpAPI if available, else DuckDuckGo scraping)
    try:
        from src.enrichment.serpapi_discovery import search_with_serpapi
        
        if Config.SERPAPI_API_KEY:
            # Use SerpAPI (more reliable)
            results["search_engines"] = search_with_serpapi(limit=limit_per_source)
            logger.info(f"  ✓ Search engines (SerpAPI): {len(results['search_engines'])} domains")
        else:
            # Fallback to scraping
            results["search_engines"] = discover_from_search_engines(limit=limit_per_source)
            logger.info(f"  ✓ Search engines (scraping): {len(results['search_engines'])} domains")
    except Exception as e:
        logger.error(f"  ✗ Search engine discovery failed: {e}")
    
    # URLhaus
    try:
        results["urlhaus"] = discover_from_urlhaus(limit=limit_per_source)
        logger.info(f"  ✓ URLhaus: {len(results['urlhaus'])} domains")
    except Exception as e:
        logger.error(f"  ✗ URLhaus discovery failed: {e}")
    
    # Telegram is now handled above in the new discovery section
    # Old telegram discovery removed - using new telegram_discovery module
    
    # Paste sites (limited - requires API keys)
    try:
        results["paste_sites"] = discover_from_paste_sites(limit=limit_per_source)
        logger.info(f"  ✓ Paste sites: {len(results['paste_sites'])} domains")
    except Exception as e:
        logger.error(f"  ✗ Paste site discovery failed: {e}")
    
    # Combine all results
    all_domains = set()
    for domains in results.values():
        all_domains.update(domains)
    
    # Filter out false positives using proper domain validation
    from src.utils.domain_validator import validate_domains
    valid_domains = validate_domains(list(all_domains))
    
    logger.info(f"🎯 Total unique domains discovered: {len(all_domains)} (filtered to {len(valid_domains)} valid)")
    
    # Update results with filtered domains
    filtered_results = {}
    for source, domains in results.items():
        filtered = [d for d in domains if d in valid_domains]
        if filtered:
            filtered_results[source] = filtered
    
    return filtered_results


if __name__ == "__main__":
    # Test discovery
    results = discover_all_sources(limit_per_source=10)
    print("\n📊 Discovery Results:")
    for source, domains in results.items():
        print(f"  {source}: {len(domains)} domains")
        if domains:
            print(f"    Examples: {', '.join(domains[:3])}")

