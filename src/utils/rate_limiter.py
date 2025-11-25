"""Rate limiting utilities to respect API quotas."""

import time
from typing import Dict, Optional
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    """
    Simple rate limiter to track and enforce API rate limits.
    
    Tracks requests per API and respects limits per time window.
    """
    
    def __init__(self):
        # Track requests per API: {api_name: deque of timestamps}
        self._requests = defaultdict(lambda: deque())
        self._locks = defaultdict(Lock)
        self._limits = {
            "ip-api.com": (45, 60),  # 45/minute
            "iplocate.io": (1000, 86400),  # 1000/day
            "builtwith": (10, 86400),  # 10/day (free tier)
            "shodan": (100, 2592000),  # 100/month (free tier)
            "crtsh": (10, 60),  # Conservative limit
            "urlhaus": (10, 60),  # Conservative limit
            "openai": (50, 60),  # 50/minute (reasonable limit)
            "reddit": (10, 60),  # Conservative limit
            "duckduckgo": (20, 60),  # Conservative limit
            "telegram": (5, 60),  # Very conservative
            "serpapi": (30, 86400),  # 30/day = ~900/month (conservative for 1000/month limit)
            "youtube": (20, 60),  # Conservative
        }
    
    def can_make_request(self, api_name: str) -> bool:
        """
        Check if we can make a request to the API.
        
        Args:
            api_name: Name of the API
            
        Returns:
            True if request can be made, False if rate limited
        """
        if api_name not in self._limits:
            return True  # No limit configured, allow request
        
        limit, window_seconds = self._limits[api_name]
        now = time.time()
        
        with self._locks[api_name]:
            # Remove old requests outside the time window
            requests = self._requests[api_name]
            while requests and (now - requests[0]) > window_seconds:
                requests.popleft()
            
            # Check if we're at the limit
            if len(requests) >= limit:
                return False
            
            return True
    
    def record_request(self, api_name: str):
        """
        Record that a request was made to the API.
        
        Args:
            api_name: Name of the API
        """
        if api_name not in self._limits:
            return
        
        now = time.time()
        
        with self._locks[api_name]:
            self._requests[api_name].append(now)
    
    def get_remaining_requests(self, api_name: str) -> Optional[int]:
        """
        Get remaining requests in current time window.
        
        Args:
            api_name: Name of the API
            
        Returns:
            Number of remaining requests, or None if no limit
        """
        if api_name not in self._limits:
            return None
        
        limit, window_seconds = self._limits[api_name]
        now = time.time()
        
        with self._locks[api_name]:
            # Remove old requests
            requests = self._requests[api_name]
            while requests and (now - requests[0]) > window_seconds:
                requests.popleft()
            
            return max(0, limit - len(requests))
    
    def wait_if_needed(self, api_name: str, max_wait: float = 5.0) -> bool:
        """
        Wait if needed to avoid rate limiting.
        
        Args:
            api_name: Name of the API
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if can proceed, False if rate limited even after wait
        """
        if self.can_make_request(api_name):
            return True
        
        # Wait a bit and check again
        wait_time = min(max_wait, 1.0)  # Wait at most 1 second
        time.sleep(wait_time)
        
        return self.can_make_request(api_name)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def check_rate_limit(api_name: str) -> bool:
    """Check if request can be made to API."""
    return _rate_limiter.can_make_request(api_name)


def record_api_request(api_name: str):
    """Record that an API request was made."""
    _rate_limiter.record_request(api_name)


def get_api_remaining(api_name: str) -> Optional[int]:
    """Get remaining API requests."""
    return _rate_limiter.get_remaining_requests(api_name)

