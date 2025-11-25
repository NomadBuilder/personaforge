"""Tests for utility functions."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.rate_limiter import RateLimiter, check_rate_limit, record_api_request
from src.utils.cache import get_cached, set_cached, clear_cache


def test_rate_limiter():
    """Test rate limiter functionality."""
    limiter = RateLimiter()
    
    # Should allow requests initially
    assert limiter.can_make_request("ip-api.com") == True
    
    # Record some requests
    for _ in range(10):
        limiter.record_request("ip-api.com")
    
    # Should still allow (under 45 limit)
    assert limiter.can_make_request("ip-api.com") == True


def test_cache():
    """Test caching functionality."""
    # Clear cache first
    clear_cache()
    
    # Set cache
    test_data = {"domain": "example.com", "ip": "1.2.3.4"}
    set_cached("domain", "example.com", test_data, ttl_hours=1)
    
    # Get cache
    cached = get_cached("domain", "example.com")
    assert cached is not None
    assert cached["domain"] == "example.com"
    
    # Test cache miss
    cached = get_cached("domain", "nonexistent.com")
    assert cached is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

