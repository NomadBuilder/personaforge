"""CMS and tech stack detection module."""

import requests
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Import Config with fallback
try:
    from src.utils.config import Config
except ImportError:
    class Config:
        API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "10"))

# Try to import Wappalyzer
try:
    from Wappalyzer import Wappalyzer, WebPage
    WAPPALYZER_AVAILABLE = True
except ImportError:
    try:
        from wappalyzer import Wappalyzer, WebPage
        WAPPALYZER_AVAILABLE = True
    except ImportError:
        WAPPALYZER_AVAILABLE = False


def detect_cms(domain: str) -> Optional[str]:
    """Detect CMS used by a domain."""
    # Try Wappalyzer first
    if WAPPALYZER_AVAILABLE:
        try:
            wappalyzer = Wappalyzer.latest()
            webpage = WebPage.new_from_url(f"http://{domain}")
            technologies = wappalyzer.analyze(webpage)
            
            # Look for CMS in detected technologies
            cms_keywords = ["wordpress", "drupal", "joomla", "shopify", "wix", "squarespace"]
            for tech in technologies:
                tech_lower = tech.lower()
                for keyword in cms_keywords:
                    if keyword in tech_lower:
                        return tech
        except Exception as e:
            print(f"Wappalyzer detection failed: {e}")
    
    # Fallback: HTTP header analysis
    try:
        url = f"http://{domain}" if not domain.startswith("http") else domain
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS, allow_redirects=True)
        headers = response.headers
        
        # Check X-Powered-By header
        if "X-Powered-By" in headers:
            powered_by = headers["X-Powered-By"].lower()
            if "wordpress" in powered_by:
                return "WordPress"
            elif "drupal" in powered_by:
                return "Drupal"
        
        # Check for CMS-specific paths/headers
        content = response.text.lower()
        if "wp-content" in content or "wp-includes" in content:
            return "WordPress"
        elif "drupal" in content:
            return "Drupal"
        elif "joomla" in content:
            return "Joomla"
            
    except Exception as e:
        print(f"CMS detection failed for {domain}: {e}")
    
    return None

