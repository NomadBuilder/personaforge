"""Caching utilities to avoid redundant API calls."""

import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta
from functools import wraps
from src.utils.config import Config

# Simple in-memory cache (can be replaced with Redis later)
_cache = {}
_cache_ttl = {}  # TTL for each cache entry


def get_cache_key(entity_type: str, value: str) -> str:
    """Generate a cache key for an entity."""
    key_string = f"{entity_type}:{value.lower().strip()}"
    return hashlib.md5(key_string.encode()).hexdigest()


def get_cached(entity_type: str, value: str, ttl_hours: int = None) -> Optional[Dict]:
    """
    Get cached enrichment data.
    
    Args:
        entity_type: Type of entity
        value: Entity value
        ttl_hours: Time-to-live in hours (uses Config if None)
    
    Returns:
        Cached data if available and not expired, else None
    """
    if not Config.CACHE_ENABLED:
        return None
    
    ttl_hours = ttl_hours or Config.CACHE_TTL_HOURS
    cache_key = get_cache_key(entity_type, value)
    
    if cache_key in _cache:
        # Check if cache entry is still valid
        if cache_key in _cache_ttl:
            ttl = _cache_ttl[cache_key]
            if datetime.now() < ttl:
                return _cache[cache_key]
            else:
                # Cache expired, remove it
                del _cache[cache_key]
                del _cache_ttl[cache_key]
        else:
            # No TTL, return cached data
            return _cache[cache_key]
    
    return None


def set_cached(entity_type: str, value: str, data: Dict, ttl_hours: int = None):
    """
    Cache enrichment data.
    
    Args:
        entity_type: Type of entity
        value: Entity value
        data: Data to cache
        ttl_hours: Time-to-live in hours (uses Config if None)
    """
    if not Config.CACHE_ENABLED:
        return
    
    ttl_hours = ttl_hours or Config.CACHE_TTL_HOURS
    cache_key = get_cache_key(entity_type, value)
    _cache[cache_key] = data
    _cache_ttl[cache_key] = datetime.now() + timedelta(hours=ttl_hours)


def clear_cache(entity_type: Optional[str] = None):
    """Clear cache entries, optionally filtered by entity type."""
    if entity_type:
        # Clear only entries for this entity type (requires checking keys)
        # For simplicity, clear all for now
        _cache.clear()
        _cache_ttl.clear()
    else:
        # Clear all cache
        _cache.clear()
        _cache_ttl.clear()


def get_cache_stats() -> Dict:
    """Get cache statistics."""
    if not Config.CACHE_ENABLED:
        return {"enabled": False}
    
    valid_entries = sum(1 for key in _cache if key in _cache_ttl and datetime.now() < _cache_ttl[key])
    expired_entries = len(_cache) - valid_entries
    
    return {
        "enabled": True,
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries
    }


def cached(ttl_hours: int = None):
    """
    Decorator to cache function results.
    
    Usage:
        @cached(ttl_hours=24)
        def enrich_domain(domain: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # For enrichment functions, first arg is usually the value
            if args:
                value = args[0]
                entity_type = func.__name__.replace("enrich_", "")
                
                # Check cache
                cached_data = get_cached(entity_type, value, ttl_hours)
                if cached_data is not None:
                    return cached_data
                
                # Call function and cache result
                result = func(*args, **kwargs)
                
                # Cache if enrichment was successful
                if result and not result.get("errors"):
                    set_cached(entity_type, value, result, ttl_hours)
                
                return result
            else:
                # No args, can't cache
                return func(*args, **kwargs)
        return wrapper
    return decorator

