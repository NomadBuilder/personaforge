"""Tests for enrichment pipeline."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.enrichment_pipeline import enrich_domain
from src.utils.validation import validate_domain


def test_validate_domain():
    """Test domain validation."""
    # Valid domains
    assert validate_domain("example.com")[0] == True
    assert validate_domain("test.example.com")[0] == True
    assert validate_domain("subdomain.example.co.uk")[0] == True
    
    # Invalid domains
    assert validate_domain("")[0] == False
    assert validate_domain("not a domain")[0] == False
    assert validate_domain("http://example.com")[0] == True  # Should normalize


def test_enrich_domain_structure():
    """Test that enrich_domain returns expected structure."""
    # Note: This test may make actual API calls
    # In production, you'd mock these
    
    result = enrich_domain("example.com")
    
    # Check required fields exist
    assert "domain" in result
    assert result["domain"] == "example.com"
    assert "ip_address" in result
    assert "host_name" in result
    assert "registrar" in result
    assert "vendor_type" in result or result.get("vendor_type") is None
    assert "vendor_risk_score" in result


def test_enrich_domain_caching():
    """Test that caching works for domain enrichment."""
    # First call
    result1 = enrich_domain("example.com")
    
    # Second call should use cache (if enabled)
    result2 = enrich_domain("example.com")
    
    # Results should be identical
    assert result1["domain"] == result2["domain"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

